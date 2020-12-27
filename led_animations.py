"""
A set of animations for a WS2812b strip, taken from
https://tutorials-raspberrypi.com/connect-control-raspberry-pi-ws2812-rgb-led-strips/
"""
try:
    import rpi_ws281x as ws
except ImportError:
    import ws_stub as ws
    
import random
import time

import pandas as pd
from PIL import Image
import numpy as np
from lightarray import LightArray

from typing import Optional, Iterable

def display_image(strip: ws.PixelStrip,
                  image_filename:str):
    image = Image.open(image_filename)
    light_pos = pd.read_csv("./light_coordinates.csv")
    light_arr= np.vstack([light_pos["X"].to_numpy() / light_pos["X"].max(),
                          light_pos["Y"].to_numpy() / light_pos["Y"].max()]).T
    la = LightArray(light_arr)
    la.image_to_strip(strip=strip, im=image, ids=light_pos["ID"])
    
def alternate_colors(strip: ws.PixelStrip,
                     colors:Optional[Iterable[ws.Color]]=None):
    """
    Show a set of colours along the strip.
    
    :param strip: the strip to show the colors on
    :param colors: a list of colors to show
    """
    if colors is None:
        colors = [ws.Color(255, 0, 0),
                  ws.Color(0, 255, 0),
                  ws.Color(0, 0, 255)]
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, colors[i % len(colors)])
    strip.show()

def get_rainbow_color(pos: int) -> ws.Color:
    """
    Generate rainbow colors across 0-255 positions.
    :param pos: a position between 0 and 255
    
    :return: a rainbow color for each position
    """
    if pos < 85:
        return ws.Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return ws.Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return ws.Color(0, pos * 3, 255 - pos * 3)


def color_wipe(strip: ws.PixelStrip, color: ws.Color, wait_ms: float = 50.0):
    """
    Wipe color across display a pixel at a time.
    
    :param strip: the strip to animate
    :param color: the color to set each pixel to
    :param wait_ms: the time between animating each pixel, in milliseconds
    """
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)


def theater_chase(
    strip: ws.PixelStrip, color: ws.Color, wait_ms: float = 50.0, iterations: int = 10
):
    """
    Movie theater light style chaser animation.
    
    :param strip: the strip to animate
    :param color: the color to set each pixel to
    :param wait_ms: the time between animating each pixel, in milliseconds
    :param iterations: the number of times this animation will play
    """
    for j in range(iterations):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, color)
            strip.show()
            time.sleep(wait_ms / 1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, 0)


def rainbow(strip: ws.PixelStrip, wait_ms: float = 20.0, iterations: int = 1):
    """
    Draw rainbow that fades across all pixels at once.
    
    :param strip: the strip to animate
    :param wait_ms: the time between each fading step
    :param iterations: the number of times to play this animation
    """
    for j in range(256 * iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, get_rainbow_color((i + j) & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)


def rainbow_cycle(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256 * iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(
                i, get_rainbow_color((int(i * 256 / strip.numPixels()) + j) & 255)
            )
        strip.show()
        time.sleep(wait_ms / 1000.0)


def theater_chase_rainbow(strip, wait_ms=50):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, get_rainbow_color((i + j) % 255))
            strip.show()
            time.sleep(wait_ms / 1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, 0)


def dither_fade(
    strip: ws.PixelStrip, new_color: ws.Color, leds_to_switch=None, dither_time=1
):
    # Dither in to a new color by randomly switching group_size
    # at a time.

    start_time = time.time()
    if leds_to_switch is None:
        leds_to_switch = [i for i in range(strip.numPixels())]
    random.shuffle(leds_to_switch)

    num_leds = len(leds_to_switch)
    # As a rough rule of thumb, it takes 0.005 seconds to switch an LED and render an
    # update. Calculate the group size dynamically to fit into our time budget.

    min_update_time = 0.005
    switches_in_time = int(round(dither_time / min_update_time))
    batch_size = int(round((strip.numPixels() / switches_in_time) + 0.5))
    if batch_size != 1:
        num_batches = int(round((strip.numPixels() / batch_size)))
        batch_size = int(round((strip.numPixels() / num_batches)))

    while leds_to_switch:
        these_leds = [leds_to_switch.pop() for _ in range(batch_size) if leds_to_switch]
        for this_led in these_leds:
            strip.setPixelColor(this_led, new_color)
        time.sleep(dither_time / (batch_size * num_leds))
        strip.show()

    # Sometimes we go too fast with the switching, as
    # the batching approximation is horrible. If we
    # do, just chill here before moving on
    end_time = time.time()
    time_diff = end_time - start_time
    if time_diff < dither_time:
        time.sleep(dither_time - time_diff)


def sunrise_animation(strip, total_time=3600, reverse=False):
    steps = 256
    dither_time = total_time / 2
    brightening_time = total_time - dither_time

    for step in range(steps):
        frac = step / steps
        if reverse:
            frac = 1.0 - frac
        SKYBLUE = ws.Color(
            max(int(135 * frac), 1), max(int(206 * frac), 1), max(int(235 * frac), 1)
        )
        SUNRISE = ws.Color(
            max(int(255 * frac), 1), max(int(191 * frac), 1), max(int(39 * frac), 1)
        )
        sunrise_width = int(strip.numPixels() * 0.1)
        sunrise_start = int(frac * strip.numPixels())
        sunrise_end = sunrise_start + sunrise_width
        sky_pixels = [i for i in range(strip.numPixels())]
        for pixel in range(sunrise_start, sunrise_end):
            if pixel in sky_pixels:
                sky_pixels.remove(pixel)
            strip.setPixelColor(pixel, SUNRISE)
        t_1 = time.time()
        dither_fade(strip, SKYBLUE, sky_pixels, (brightening_time - 1) / steps)
        t_2 = time.time()
        time_diff = t_2 - t_1
        if time_diff < brightening_time / steps:
            time.sleep((brightening_time / steps) - time_diff)
            
if __name__ == "__main__":
    NUM_LEDS = 150
    LED_PIN = 18
    STRIP = ws.PixelStrip(NUM_LEDS, LED_PIN)
    STRIP.begin()
    theater_chase_rainbow(STRIP)
