#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contains default values for weather animations.

Created on Thurs Sep 01 17:49:27 2022

@author: matthew-bailey
"""
from collections import defaultdict
from light_array import display_image

weather_animations = defaultdict(lambda: sunrise_animation)
weather_animations["Clear"] = lambda strip, runtime, reverse: display_image(
    strip=strip, image_filename="sunrise.jpg", runtime=runtime, reverse=reverse
)
weather_animations["Rain"] = lambda strip, runtime, reverse: display_image(
    strip=strip, image_filename="rain.jpg", runtime=runtime, reverse=reverse
)

weather_animations["Snow"] = lambda strip, runtime, reverse: display_image(
    strip=strip, image_filename="snow.jpg", runtime=runtime, reverse=reverse
)
weather_animations["Thunderstorm"] = lambda strip, runtime, reverse: display_image(
    strip=strip, image_filename="thunderstorm.jpg", runtime=runtime, reverse=reverse
)
weather_animations["Drizzle"] = lambda strip, runtime, reverse: display_image(
    strip=strip, image_filename="drizzle.jpeg", runtime=runtime, reverse=reverse
)

weather_animations["Clouds"] = lambda strip, runtime, reverse: display_image(
    strip=strip, image_filename="clouds.jpeg", runtime=runtime, reverse=reverse
)
