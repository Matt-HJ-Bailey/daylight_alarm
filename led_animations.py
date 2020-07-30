"""
A set of animations for a WS2812b strip, taken from
https://tutorials-raspberrypi.com/connect-control-raspberry-pi-ws2812-rgb-led-strips/
"""

import rpi_ws281x as ws
import random
import time


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
