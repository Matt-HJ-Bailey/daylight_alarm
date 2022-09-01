#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 27 20:43:44 2020

@author: matthew-bailey
"""

import logging
import os
import pickle as pkl
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
import scipy.spatial
from sklearn.cluster import KMeans

from led_animations import dither_fade

logger = logging.getLogger(__name__)

try:
    import rpi_ws281x as ws

    IS_STUB_WS = False
except ImportError as ex:
    logger.warning(f"Using stub rpi_ws821x: {ex}")
    import ws_stub as ws

    IS_STUB_WS = True


def gamma_adjust(colors: np.array, exponent: float = 2.2):
    """
    Taken in an RGB numpy array and adjust it with a gamma curve.

    Parameters
    ----------
    colors
        An RGB array in range [0, 255)
    exponent
        The gamma value, should be about 2.2 for sRGB
    """
    return 255.0 * (np.asarray(colors) / 255.0) ** exponent


class LightArray:
    def __init__(self, position_data, image_filename):
        """
        Calculate the KD Tree for these pixels, to find which regions are closest
        to each pixel and no others
        """
        assert position_data.shape[1] == 2, "Pixel positions must be a 2D array"
        position_data = np.asarray(position_data, dtype=float)
        # Normalise the position data before using it further
        position_data[:, 0] /= np.max(position_data[:, 0])
        position_data[:, 1] /= np.max(position_data[:, 1])

        self.kdtree = scipy.spatial.cKDTree(
            position_data, compact_nodes=True, copy_data=True
        )

        image = Image.open(image_filename)
        self.colors = self._image_to_colors(image)

    def _image_to_colors(self, image):
        """
        Take in an image and figure out what colours the pixels in this array should be.
        Each pixel takes the colour of the most significant cluster of pixel colours
        in the region closest to it.

        Parameters
        ----------
        im
            The image to sample
        Returns
        -------
        colors
            Nx3 RGB array of colour data
        """
        pixel_positions = np.array(
            [
                [x / image.width, y / image.height]
                for x in range(image.width)
                for y in range(image.height)
            ]
        )
        _, regions = self.kdtree.query(pixel_positions)
        color_data = np.array(image.getdata())
        ret_colors = np.zeros([self.kdtree.data.shape[0], 3], dtype=int)
        for region in range(min(regions), max(regions)):
            colors_in_region = color_data[regions == region]
            kmeans = KMeans(n_clusters=1, random_state=0).fit(colors_in_region)
            ret_colors[region, :] = [int(item) for item in kmeans.cluster_centers_[0]]
        return ret_colors

    def image_to_strip(self, strip, ids):
        """
        Display a given image on a strip.

        Parameters
        ----------
        strip
            The LED strip to draw on
        im
            The image to show
        ids
            The index array linking the colours to the pixel addresses
        """
        for i in range(self.colors.shape[0]):
            this_color = ws.Color(
                int(self.colors[i, 0]), int(self.colors[i, 1]), int(self.colors[i, 2])
            )
            strip.setPixelColor(int(ids[i]), this_color)
        strip.show()
        return strip

    def blend_image_to_strip(self, strip, ids, runtime=60, reverse=False):
        """
        Slowly display the image on the strip with increasing brightness.

        Parameters
        ---------
        strip
            The LED strip to show
        im
            The image to show
        ids
            The indices of the pixels to change
        runtime
            how long the display should take
        reverse
            Should this go dark->light or light->dark
        """

        NUM_STEPS = 256
        TIME_PER_STEP = runtime / NUM_STEPS

        if reverse:
            # Remember that range doesn't include the end point.
            steps = range(NUM_STEPS - 1, -1, -1)
        else:
            steps = range(NUM_STEPS)

        for step in steps:
            color_arr = [ws.Color(0, 0, 0) for _ in range(strip.numPixels())]
            interp_colors = self.colors * (step / NUM_STEPS) ** 2.3
            for i in range(self.colors.shape[0] - 1, 0, -1):
                color_arr[int(ids[i])] = ws.Color(
                    *[int(round(item)) for item in interp_colors[i, :]]
                )
            dither_fade(strip, color_arr, dither_time=TIME_PER_STEP)


def display_image(
    strip: ws.PixelStrip, image_filename: str, runtime: float, reverse: bool
):
    """
    Display a given image on the strip.

    Uses a cached pickle file as this is expensive on the Raspberry Pi.
    Parameters
    ---------
    strip
        The LED strip to show.
        Coordinates of lights should be available in light_coordinates.csv
    image_filename
        The name of the image to show
    runtime
        The length of time for this animation to show
    reverse
        Should we go from dark->bright(False) or bright->dark (True)
    """
    _pkl_name = os.path.join("./pkl/", os.path.splitext(image_filename)[0] + ".pkl")

    light_pos = pd.read_csv("./light_coordinates.csv")
    if os.path.exists(_pkl_name):
        logger.info(f"Using pickled {_pkl_name}")
        with open(_pkl_name, "rb") as fi:
            la = pkl.load(fi)
    else:
        light_arr = np.vstack(
            [
                light_pos["Y"].to_numpy(),
                light_pos["X"].to_numpy(),
            ]
        ).T
        la = LightArray(light_arr, image_filename)
        logger.info(f"Dumping new pickled {_pkl_name}")
        with open(_pkl_name, "wb") as fi:
            pkl.dump(la, fi)

    la.blend_image_to_strip(
        strip=strip, ids=light_pos["ID"], runtime=runtime, reverse=reverse
    )


if __name__ == "__main__":
    LIGHT_POS = pd.read_csv("./light_coordinates.csv")
    LIGHT_ARR = np.vstack(
        [
            LIGHT_POS["Y"].to_numpy(),
            LIGHT_POS["X"].to_numpy(),
        ]
    ).T
    la = LightArray(LIGHT_ARR, "./thunderstorm.jpg")
    NUM_LEDS = 150
    LED_PIN = 18
    RUNTIME = 20 * 60
    STRIP = ws.PixelStrip(NUM_LEDS, LED_PIN)
    STRIP.begin()
    la.image_to_strip(STRIP, LIGHT_POS["ID"])

    if IS_STUB_WS:
        print("Saving to plotted.pdf")
        fig, ax = plt.subplots()
        ax = STRIP.plot_onto(LIGHT_ARR, LIGHT_POS["ID"], ax)
        fig.savefig("./plotted.pdf")
