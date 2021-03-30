#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 27 20:43:44 2020

@author: matthew-bailey
"""
import os

import time
import scipy.spatial
from PIL import Image
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import pickle as pkl

from led_animations import dither_fade

try:
    import rpi_ws281x as ws
except ImportError:
    print("Using stub")
    import ws_stub as ws


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
    def __init__(self, position_data):
        """
        Calculate the KD Tree for these pixels, to find which regions are closest
        to each pixel and no others
        """
        assert position_data.shape[1] == 2, "Pixel positions must be a 2D array"
        self.kdtree = scipy.spatial.cKDTree(
            position_data, compact_nodes=True, copy_data=True
        )

    def image_to_colors(self, im):
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
                [x / im.width, y / im.height]
                for x in range(im.width)
                for y in range(im.height)
            ]
        )
        _, regions = self.kdtree.query(pixel_positions)
        color_data = np.array(im.getdata())
        ret_colors = np.zeros([self.kdtree.data.shape[0], 3], dtype=int)
        for region in range(min(regions), max(regions)):
            colors_in_region = color_data[regions == region]
            kmeans = KMeans(n_clusters=1, random_state=0).fit(colors_in_region)
            ret_colors[region, :] = [int(item) for item in kmeans.cluster_centers_[0]]
        return ret_colors

    def image_to_strip(self, strip, im, ids):
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
        colors = self.image_to_colors(im)
        for i in range(colors.shape[0]):
            this_color = ws.Color(
                int(colors[i, 0]), int(colors[i, 1]), int(colors[i, 2])
            )
            strip.setPixelColor(int(ids[i]), this_color)
        strip.show()

    def blend_image_to_strip(self, strip, im, ids, runtime=60, reverse=False):
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

        colors = self.image_to_colors(im)
        NUM_STEPS = 256
        TIME_PER_STEP = runtime / NUM_STEPS

        if reverse:
            # Remember that range doesn't include the end point.
            steps = range(NUM_STEPS - 1, -1, -1)
        else:
            steps = range(NUM_STEPS)

        for step in steps:
            color_arr = [ws.Color(0, 0, 0) for _ in range(strip.numPixels())]
            interp_colors = gamma_adjust(colors[i, :] * step / NUM_STEPS)
            for i in range(colors.shape[0] - 1, 0, -1):
                color_arr[int(ids[i])] = ws.Color(
                    *[int(round(item)) for item in interp_colors[i, :]]
                )
            dither_fade(strip, color_arr, dither_time=TIME_PER_STEP)

    def plot_onto(self, ax=None, im=None):
        """
        Display the image and the closest points on an axis.

        Parameters
        ----------
        ax
            Matplotlib axis to draw onto
        im
            Background image to show
        """
        if ax is None:
            fig, ax = plt.subplots()

        ax.imshow(im)
        colors = self.image_to_colors(im)
        ax.scatter(
            (self.kdtree.data[:, 0]) * im.width,
            (self.kdtree.data[:, 1]) * im.height,
            c=colors / 255.0,
        )


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
        with open(_pkl_name, "rb") as fi:
            la = pkl.load(fi)
    else:
        light_arr = np.vstack(
            [
                light_pos["Y"].to_numpy() / light_pos["Y"].max(),
                light_pos["X"].to_numpy() / light_pos["X"].max(),
            ]
        ).T
        la = LightArray(light_arr)
        with open(_pkl_name, "wb") as fi:
            pkl.dump(la, fi)

    image = Image.open(image_filename)
    la.blend_image_to_strip(
        strip=strip, im=image, ids=light_pos["ID"], runtime=runtime, reverse=reverse
    )


if __name__ == "__main__":
    IMAGE = Image.open("./sunrise.jpg")
    LIGHT_POS = pd.read_csv("./light_coordinates.csv")
    LIGHT_ARR = np.vstack(
        [
            LIGHT_POS["Y"].to_numpy() / LIGHT_POS["Y"].max(),
            LIGHT_POS["X"].to_numpy() / LIGHT_POS["X"].max(),
        ]
    ).T
    la = LightArray(LIGHT_ARR)
    colors = la.image_to_colors(IMAGE)
    NUM_LEDS = 150
    LED_PIN = 18
    RUNTIME = 20 * 60
    STRIP = ws.PixelStrip(NUM_LEDS, LED_PIN)
    STRIP.begin()
    la.blend_image_to_strip(STRIP, IMAGE, LIGHT_POS["ID"], runtime=20)
