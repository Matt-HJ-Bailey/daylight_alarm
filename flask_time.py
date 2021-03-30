#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 27 18:01:27 2020

@author: matthew-bailey
"""

import schedule
import time
from collections import defaultdict
import datetime
from threading import Thread
import sys

try:
    import rpi_ws281x as ws
except ImportError:
    import ws_stub as ws

from pyowm.owm import OWM

from flask import Flask, render_template, flash, redirect

from config import Config
from timeform import TimeForm
from led_animations import sunrise_animation, alternate_colors
from lightarray import display_image

CONFIG = Config()

WEATHER_ANIMATIONS = defaultdict(lambda: sunrise_animation)
WEATHER_ANIMATIONS["Clear"] = lambda strip, runtime, reverse: display_image(
    strip=strip, image_filename="sunrise.jpg", runtime=runtime, reverse=reverse
)
WEATHER_ANIMATIONS["Rain"] = lambda strip, runtime, reverse: display_image(
    strip=strip, image_filename="rain.jpg", runtime=runtime, reverse=reverse
)

WEATHER_ANIMATIONS["Snow"] = lambda strip, runtime, reverse: display_image(
    strip=strip, image_filename="snow.jpg", runtime=runtime, reverse=reverse
)
WEATHER_ANIMATIONS["Thunderstorm"] = lambda strip, runtime, reverse: display_image(
    strip=strip, image_filename="thunderstorm.jpg", runtime=runtime, reverse=reverse
)
WEATHER_ANIMATIONS["Drizzle"] = lambda strip, runtime, reverse: display_image(
    strip=strip, image_filename="drizzle.jpeg", runtime=runtime, reverse=reverse
)

WEATHER_ANIMATIONS["Clouds"] = lambda strip, runtime, reverse: display_image(
    strip=strip, image_filename="clouds.jpeg", runtime=runtime, reverse=reverse
)

NUM_LEDS = 150
LED_PIN = 18
RUNTIME = 20 * 60
STRIP = ws.PixelStrip(NUM_LEDS, LED_PIN)

app = Flask(__name__)
app.config.from_object(CONFIG)


def get_weather(location: str = "Oxford,GB") -> str:
    """
    Get the weather from OpenWeatherMap

    :param location: an owm location string to get weather data for

    :return: the simple weather status
    """
    try:
        owm = OWM(CONFIG.WEATHER_API_KEY)

        mgr = owm.weather_manager()
        observation = mgr.weather_at_place(
            "Oxford,GB"
        )  # the observation object is a box containing a weather object
        return observation.weather.status
    except Exception as ex:
        print(f"Failed to get the weather: {ex}", file=sys.stderr)
        return None


def turn_lights_on(strip: ws.PixelStrip, runtime: float = RUNTIME):
    print(f"Turning the lights on over {runtime}s")
    start_time = time.time()
    weather = get_weather()
    print("The weather is", weather)
    WEATHER_ANIMATIONS[weather](strip, runtime=runtime, reverse=False)
    print(f"Animation done, took {time.time() - start_time}")


def turn_lights_off(strip: ws.PixelStrip, runtime: float = RUNTIME):
    print(f"Turning the lights off over {runtime}s")
    weather = get_weather()
    WEATHER_ANIMATIONS[weather](strip, runtime, reverse=True)
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, ws.Color(0, 0, 0))
    strip.show()


@app.route("/", methods=["GET", "POST"])
def change_time():
    """
    Set the regular time that the lights will come on.
    This is taken from a web page with two boxes, containing hours.data and minutes.data

    We write the times to a file to make sure that we keep them across running sessions.
    """
    form = TimeForm()
    if form.validate_on_submit():

        # Clear the schedule.
        schedule.clear()
        on_time = datetime.time(hour=form.hours.data, minute=form.minutes.data)
        # We can't meaningfully add times and time offsets without
        # dates getting involved... argh!
        off_time = (
            datetime.datetime.combine(datetime.date.today(), on_time)
            + datetime.timedelta(seconds=RUNTIME)
        ).time()

        with open("./times.txt", "w") as fi:
            fi.write(on_time.strftime("%H:%M:%S") + "\n")
            fi.write(off_time.strftime("%H:%M:%S") + "\n")
        schedule.every().day.at(on_time.strftime("%H:%M:%S")).do(turn_lights_on, STRIP)
        schedule.every().day.at(off_time.strftime("%H:%M:%S")).do(
            turn_lights_off, STRIP
        )
        for i in range(STRIP.numPixels()):
            STRIP.setPixelColor(i, ws.Color(0, 0, 0))
        STRIP.show()
        flash(f"The lights will come on at {on_time.strftime('%H:%M:%S')}")
        print(f"The lights will come on at {on_time.strftime('%H:%M:%S')}")
        return redirect("/")
    return render_template("timesetter.html", title="Light Time", form=form)


def check_schedule(sleep_time: int = 10):
    while True:
        schedule.run_pending()
        time.sleep(sleep_time)


if __name__ == "__main__":
    STRIP.begin()

    with open("./times.txt", "r") as fi:
        schedule.every().day.at(fi.readline().strip()).do(turn_lights_on, STRIP)
        schedule.every().day.at(fi.readline().strip()).do(turn_lights_off, STRIP)

    thread = Thread(target=check_schedule, args=[60])
    thread.start()

    app.run(host="0.0.0.0")
