#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 27 20:43:44 2020

@author: matthew-bailey
"""

import scipy.spatial
from PIL import Image
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

try:
    import rpi_ws281x as ws
except ImportError:
    import ws_stub as ws

class LightArray():
    def __init__(self, position_data):
        self.kdtree = scipy.spatial.cKDTree(position_data,
                                            compact_nodes=True,
                                            copy_data=True)
    
    def image_to_colors(self, im):
        pixel_positions = np.array([[x / im.width, y / im.height]
                                    for x in range(im.width) for y in range(im.height)])
        distances, regions = self.kdtree.query(pixel_positions)
        color_data = np.array(im.getdata())
        ret_colors = np.zeros([self.kdtree.data.shape[0], 3], dtype=int)
        for region in range(min(regions), max(regions)):
            colors_in_region = color_data[regions == region]
            kmeans = KMeans(n_clusters=1, random_state=0).fit(colors_in_region)
            ret_colors[region, :] = [int(item) for item in kmeans.cluster_centers_[0]]
        return ret_colors
    
    def image_to_strip(self, strip, im, ids):
        colors = self.image_to_colors(im)
        for i in range(colors.shape[0]):
            this_color = ws.Color(*colors[i])
            strip.setPixelColor(i, this_color)
        strip.show()
        
    def plot_onto(self, ax=None, im=None):
        if ax is None:
            fig, ax = plt.subplots()
        
        ax.imshow(im)
        colors = self.image_to_colors(im)
        ax.scatter((self.kdtree.data[:, 0]) * im.width, (self.kdtree.data[:, 1]) * im.height,
                   c=colors / 255.0)
        

if __name__ == "__main__":
    IMAGE = Image.open("./sunrise.jpg")
    LIGHT_POS = pd.read_csv("./light_coordinates.csv")
    LIGHT_ARR = np.vstack([LIGHT_POS["X"].to_numpy() / LIGHT_POS["X"].max(),
                           LIGHT_POS["Y"].to_numpy() / LIGHT_POS["Y"].max()]).T
    la = LightArray(LIGHT_ARR)
    colors = la.image_to_colors(IMAGE)
    
    FIG, AX = plt.subplots()
    la.plot_onto(ax=AX, im=IMAGE)
    