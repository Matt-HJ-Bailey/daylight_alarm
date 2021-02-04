import rpi_ws281x as ws
import random
import time
import os

from collections import defaultdict
from pyowm.owm import OWM

from led_animations import dither_fade


WEATHER_ANIMATIONS = defaultdict(lambda: sunrise_animation)


def main(strip):
    print(f"Good morning! Waking up at {time.time()}")
    owm = OWM(WEATHER_API_KEY)

    mgr = owm.weather_manager()
    observation = mgr.weather_at_place(
        "Oxford,GB"
    )  # the observation object is a box containing a weather object
    weather = observation.weather.status
    print(f"The current weather is {weather}")

    start_time = time.time()
    strip.begin()
    dither_fade(
        strip, ws.Color(0, 1, 1), leds_to_switch=None, dither_time=RUNTIME * 0.5
    )
    WEATHER_ANIMATIONS[weather](strip, RUNTIME)
    time.sleep(10 * 60)
    WEATHER_ANIMATIONS[weather](strip, RUNTIME, reverse=True)
    dither_fade(
        strip, ws.Color(0, 0, 0), leds_to_switch=None, dither_time=RUNTIME * 0.5
    )
    end_time = time.time()
    print(
        f"I hope you're awake! Closing down at {time.time()}. We spent {(end_time - start_time) // 60} minutes."
    )


def read_api_keys(filename):
    """
    Read api keys from a filename for usage in this program.

    The file should have keys in the format 'name=api key', each on a new line. Don't add that file to git!

    :param filename: the filename of the file containing api keys
    :return: a dictionary keyed by api name, with api keys as values.
    """
    key_dict = {}
    with open(filename) as fi:
        for line in fi:
            key, val = [item.strip() for item in line.split("=")]
            key_dict[key] = val
    return key_dict


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    WEATHER_API_KEY = read_api_keys("./.apikey")["openweathermap"]
    NUM_LEDS = 150
    LED_PIN = 18
    RUNTIME = 20 * 60
    strip = ws.PixelStrip(NUM_LEDS, LED_PIN)
    try:
        main(strip)
    except KeyboardInterrupt:
        for pixel in range(strip.numPixels()):
            strip.setPixelColor(pixel, ws.Color(0, 0, 0))
        strip.show()
        raise KeyboardInterrupt
