#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 27 18:18:23 2020

@author: matthew-bailey
"""

class Config:
    def __init__(self, filename:str = ".api_keys"):
        """
        Read the config from a file.
        """
        with open(filename, "r") as fi:
            for line in fi:
                key, val = line.split("=")
                setattr(self, key.strip(), val.strip())