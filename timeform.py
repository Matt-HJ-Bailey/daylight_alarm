#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 27 18:50:15 2020

@author: matthew-bailey
"""

from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms.validators import NumberRange


class TimeForm(FlaskForm):
    """
    Form to recieve two integers, as hours and minutes
    """

    hours = IntegerField("Hours", validators=[NumberRange(min=0, max=23)])
    minutes = IntegerField("Minutes", validators=[NumberRange(min=0, max=59)])
    submit = SubmitField("Change Time")
