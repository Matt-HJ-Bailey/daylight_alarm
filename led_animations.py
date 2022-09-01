"""
A set of animations for a WS2812b strip, taken from
https://tutorials-raspberrypi.com/connect-control-raspberry-pi-ws2812-rgb-led-strips/
"""

from abc import ABC, abstractmethod
from collections import deque
import copy
import random
import time
from typing import Optional, Iterable, Union

import pandas as pd
from PIL import Image
import numpy as np

try:
    import rpi_ws281x as ws
except ImportError:
    import ws_stub as ws


class Frame:
    """
    Single frame to display on the image
    """

    def __init__(
        self, strip: ws.PixelStrip, colors: Optional[Iterable[ws.Color]] = None
    ):
        """
        Initialise this frame as a strip and associated colour array.

        Will pad the colours array to be the correct length if too small.
        If too large, excess data are ignored.
        Parameters
        ----------
        strip
            The strip to display on
        colours
            24-bit RGB colours to display. If just one colour, will repeat across the array.
        """
        self.strip = strip
        try:
            iter(colors)
            self.colors = np.asarray(colors, dtype=int)
        except TypeError:
            self.colors = np.array(
                [colors for _ in range(self.strip.getNumPixels())], dtype=int
            )

    def show(self):
        for i in range(self.strip.getNumPixels()):
            if i < len(self.colors):
                self.strip.setPixelColor(i, self.colors[i % len(self.colors)])
        self.strip.show()


class Animation(ABC):
    def __init__(self, strip):
        self.strip = strip
        self.frame_number = 0

    def __iter__(self):
        self.frame_number = 0
        return self

    @abstractmethod
    def __next__(self):
        self.frame_number += 1
        return

    def play(self, delay: float = 33.0 / 1000):
        """
        Play this animation on the strip

        Parameters
        ----------
        delay
            Time to wait between frames in ms
        """
        time_now = time.time()
        for frame in self:
            frame.show()
            time_after = time.time()
            dt = time_after - time_now
            # print(f"Showing F{self.frame_number} with dt={dt}")
            time.sleep(delay - dt)
            time_now = time.time()


class AlternateColors(Animation):
    """
    Show a set of alternating colours along the strip.

    Parameters
    ----------
    strip
        The strip to show the colors on
    colors
        a list of colors to show, can be None in which case R, G, B is used.
    """

    def __init__(self, strip: ws.PixelStrip, colors: Optional[np.ndarray] = None):
        super().__init__(strip)
        if colors is not None:
            self.color_arr = colors
        else:
            self.color_arr = np.array(
                [ws.Color(255, 0, 0), ws.Color(0, 255, 0), ws.Color(0, 0, 255)]
            )

    def __next__(self):
        super().__next__()
        return Frame(
            self.strip,
            [
                self.color_arr[(i + self.frame_number) % len(self.color_arr)]
                for i in range(self.strip.getNumPixels())
            ],
        )


class RainbowColors(Animation):
    """
    Generate rainbow colors across the strip.
    """

    def __init__(self, strip):
        super().__init__(strip)

    def __next__(self):
        colors = deque([0 for _ in range(self.strip.getNumPixels())])
        for i in range(self.strip.getNumPixels()):
            if i < 85:
                colors[i] = ws.Color(i * 3, 255 - i * 3, 0)
            elif i < 170:
                colors[i] = ws.Color(255 - (i - 85) * 3, 0, (i - 85) * 3)
            else:
                colors[i] = ws.Color((i - 170) * 3, 255 - (i - 170) * 3, 0)
        colors.rotate(self.frame_number)
        super().__next__()
        return Frame(self.strip, colors)


class ColorWipe(Animation):
    def __init__(self, strip: ws.PixelStrip, color: ws.Color):
        super().__init__(strip)
        self.color = color

    def __next__(self):
        if self.frame_number >= self.strip.getNumPixels():
            raise StopIteration
        colors = [ws.Color(0, 0, 0) for _ in range(self.strip.getNumPixels())]
        for i in range(self.frame_number):
            colors[i] = self.color
        super().__next__()
        return Frame(self.strip, colors)


class TheatreChase(Animation):
    """
    Movie theatre style light cahse animation
    """

    def __init__(self, strip: ws.PixelStrip, color: ws.Color, max_iterations: int = 10):
        super().__init__(strip)
        self.max_iterations = max_iterations
        self.color = color

    def __next__(self):
        if self.frame_number >= self.max_iterations:
            raise StopIteration
        colors = [ws.Color(0, 0, 0) for _ in range(self.strip.getNumPixels())]
        for i in range(len(colors), 3):
            colors[(i + self.frame_number) % len(colors)] = self.color
        super().__next__()
        return Frame(self.strip, colors)


class DitherFade(Animation):
    """
    Fade between two images by randomly swapping pixels.
    """

    def __init__(
        self,
        strip: ws.PixelStrip,
        old_frame: Frame,
        new_frame: Frame,
        batch_size: int = 16,
    ):
        super().__init__(strip)
        self.current_frame = copy.deepcopy(old_frame)
        self.new_frame = new_frame
        self.batch_size = batch_size
        rng = np.random.default_rng()
        self.remaining_pixels = [i for i in range(self.strip.getNumPixels())]
        rng.shuffle(self.remaining_pixels)

    def __next__(self):
        if not self.remaining_pixels:
            raise StopIteration

        for _ in range(self.batch_size):
            try:
                idx = self.remaining_pixels.pop()
            except IndexError:
                break
            self.current_frame.colors[idx] = self.new_frame.colors[idx]
        super().__next__()
        return self.current_frame


class LerpFade(Animation):
    """
    Linearly fade between two images by interpolating pixels
    """

    def __init__(
        self, strip: ws.PixelStrip, old_frame: Frame, new_frame: Frame, steps=255
    ):
        super().__init__(strip)
        self.old_frame = old_frame
        self.new_frame = new_frame
        self.delta = (new_frame.colors - old_frame.colors).astype(float) / steps
        self.steps = steps

    def __next__(self):
        if self.frame_number >= self.steps:
            raise StopIteration

        current_colors = self.old_frame.colors + (
            self.delta * self.frame_number
        ).astype(int)
        super().__next__()
        return Frame(self.strip, current_colors)


class DitherLerpFade(Animation):
    """
    Fade between two images by interpolating pixels and dithering each step
    """

    def __init__(
        self,
        strip: ws.PixelStrip,
        old_frame: Frame,
        new_frame: Frame,
        batch_size=16,
        steps=255,
    ):
        super().__init__(strip)
        self.delta = (new_frame.colors - old_frame.colors).astype(float) / steps
        self.steps = steps
        self.batch_size = batch_size
        self.remaining_pixels = self.get_random_pixels()
        self.lerp_step = 0
        self.old_frame = copy.deepcopy(old_frame)
        self.current_frame = copy.deepcopy(old_frame)
        self.next_frame = self.get_next_lerp_frame()

    def get_random_pixels(self, seed: Optional[int] = None) -> Iterable[int]:
        """
        Get a set of pixels in a random order

        Parameters
        ----------
        seed
            Seed for the random number generator

        Returns
        -------
            list of pixel ids in a random order
        """
        rng = np.random.default_rng(seed=seed)
        remaining_pixels = [i for i in range(self.strip.getNumPixels())]
        rng.shuffle(remaining_pixels)
        return remaining_pixels

    def get_next_lerp_frame(self):
        """
        Get the next linearly interpolated frame
        """
        self.lerp_step += 1
        return Frame(
            self.strip,
            self.old_frame.colors + (self.delta * self.lerp_step).astype(int),
        )

    def __next__(self):
        if not self.remaining_pixels:
            self.current_frame = self.next_frame
            self.next_frame = self.get_next_lerp_frame()
            self.remaining_pixels = self.get_random_pixels()

        for _ in range(self.batch_size):
            try:
                idx = self.remaining_pixels.pop()
            except IndexError:
                break
            self.current_frame.colors[idx] = self.next_frame.colors[idx]
        super().__next__()
        return self.current_frame


class SunriseAnimation(Animation):
    def __init__(self, strip, reverse=False, steps: int = 256):
        super().__init__(strip)
        self.reverse = False
        self.steps = steps

    def __next__(self):
        sunrise_width = int(self.strip.getNumPixels() * 0.1)
        sunrise_start = (self.frame_number / steps) * self.strip.getNumPixels()


def sunrise_animation(strip, total_time=3600, reverse=False):
    steps = 256
    dither_time = total_time / 2
    brightening_time = total_time - dither_time

    for step in range(steps):
        frac = step / steps
        if reverse:
            frac = 1.0 - frac
        skyblue = ws.Color(
            max(int(135 * frac), 1), max(int(206 * frac), 1), max(int(235 * frac), 1)
        )
        sunrise = ws.Color(
            max(int(255 * frac), 1), max(int(191 * frac), 1), max(int(39 * frac), 1)
        )
        sunrise_width = int(strip.numPixels() * 0.1)
        sunrise_start = int(frac * strip.numPixels())
        sunrise_end = sunrise_start + sunrise_width
        sky_pixels = [i for i in range(strip.numPixels())]
        for pixel in range(sunrise_start, sunrise_end):
            if pixel in sky_pixels:
                sky_pixels.remove(pixel)
            strip.setPixelColor(pixel, sunrise)
        t_1 = time.time()
        dither_fade(strip, skyblue, sky_pixels, (brightening_time - 1) / steps)
        t_2 = time.time()
        time_diff = t_2 - t_1
        if time_diff < brightening_time / steps:
            time.sleep((brightening_time / steps) - time_diff)
    if reverse:
        for pixel in range(strip.numPixels()):
            strip.setPixelColor(pixel, 0)


if __name__ == "__main__":
    NUM_LEDS = 150
    LED_PIN = 18
    STRIP = ws.PixelStrip(NUM_LEDS, LED_PIN)
    STRIP.begin()
    anim = DitherLerpFade(
        STRIP,
        Frame(STRIP, ws.Color(0, 0, 0)),
        Frame(STRIP, ws.Color(255, 255, 255)),
        steps=16,
    )
    anim.play(delay=0.1)
