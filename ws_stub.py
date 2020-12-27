#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sub functions for the ws module.

Created on Sun Dec 27 19:41:44 2020

@author: matthew-bailey
"""

import numpy as np

def Color(red:int, green:int, blue:int, white:int = 0):
    """
    Convert the provided red, green, blue color to a 24-bit color value.
    Each color component should be a value 0-255 where 0 is the lowest intensity
    and 255 is the highest intensity.
    """
    assert 0 <= red <= 255
    assert 0 <= blue <= 255
    assert 0 <= green <= 255
    assert 0 <= white <= 255
    
    return (white << 24) | (red << 16)| (green << 8) | blue


class PixelStrip():
    def __init__(self, num:int, pin:int):
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