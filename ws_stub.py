#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sub functions for the ws module.

Created on Sun Dec 27 19:41:44 2020

@author: matthew-bailey
"""

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi


def sort_coordinates_anticlockwise(coordinates: np.ndarray) -> np.ndarray:
    """
    sort a list of coordinates to be in anticlockwise order.

    Parameters
    ----------
    coordinates
        Vertex coordinates of a polygon

    Returns
    -------
        Coordinates sorted in anticlockwise order
    """
    centroid = coordinates.mean(axis=0)
    angles = np.arctan2(
        coordinates[:, 1] - centroid[1], coordinates[:, 0] - centroid[0]
    )
    return coordinates[np.argsort(angles)]


def Color(red: int, green: int, blue: int, white: int = 0):
    """
    Convert the provided red, green, blue color to a 24-bit color value.
    Each color component should be a value 0-255 where 0 is the lowest intensity
    and 255 is the highest intensity.
    """
    assert 0 <= red <= 255
    assert 0 <= blue <= 255
    assert 0 <= green <= 255
    assert 0 <= white <= 255

    return (white << 24) | (red << 16) | (green << 8) | blue


def color_to_rgb(color):
    return (
        np.array(
            [(color >> 16) & 0xFF, (color >> 8) & 0xFF, (color >> 0) & 0xFF, 1.0],
            dtype=float,
        )
        / 255
    )


class PixelStrip:
    def __init__(self, num: int, pin: int):
        self.num = num
        self.pin = pin
        self._data = np.zeros([self.num], dtype=int)

    def begin(self):
        return True

    def show(self):
        print("Showing", self._data)
        return True

    def setPixelColor(self, n: int, color: Color):
        self._data[n] = color

    def getNumPixels(self):
        return self._data.shape[0]

    def plot_onto(self, points, ids, ax=None):
        print(self._data.shape, points.shape)
        if ax is None:
            fig, ax = plt.subplots()

        vor = Voronoi(points)

        polys = []
        name_order = []

        all_ridges: Dict[int, List[int]] = {}
        for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
            all_ridges.setdefault(p1, []).append((p2, v1, v2))
            all_ridges.setdefault(p2, []).append((p1, v1, v2))
        center = vor.points.mean(axis=0)
        radius = max(vor.points[:, 0].ptp(), vor.points[:, 1].ptp())

        for region_id, point_region in enumerate(vor.point_region):
            # Create the polygons
            vertices = vor.regions[point_region]
            coords_list = [
                np.array([vor.vertices[vertex][0], vor.vertices[vertex][1]])
                for vertex in vertices
                if vertex >= 0
            ]
            if -1 in vertices:
                # reconstruct a non-finite region
                for p2, v1, v2 in all_ridges[region_id]:
                    if v2 < 0:
                        v1, v2 = v2, v1
                    if v1 >= 0:
                        # finite ridge: already in the region
                        continue

                    # Compute the missing endpoint of an infinite ridge
                    t = vor.points[p2] - vor.points[region_id]  # tangent
                    t /= np.linalg.norm(t)
                    n = np.array([-t[1], t[0]])  # normal

                    midpoint = vor.points[[region_id, p2]].mean(axis=0)
                    direction = np.sign(np.dot(midpoint - center, n)) * n
                    far_point = vor.vertices[v2] + direction * radius
                    coords_list.append(far_point)

            coordinates = sort_coordinates_anticlockwise(np.vstack(coords_list))
            polys.append(
                mpl.patches.Polygon(coordinates, linewidth=1.0, edgecolor="black")
            )
        polys = mpl.collections.PatchCollection(
            polys, alpha=1.0, linewidth=0.0, edgecolor=None
        )
        polys.set_facecolors([color_to_rgb(self._data[idx]) for idx in ids])
        ax.add_collection(polys)
        ax.set_xlim(0, max(points[:, 0]) * 1.1)
        ax.set_ylim(0, max(points[:, 1]) * 1.1)
        return ax
