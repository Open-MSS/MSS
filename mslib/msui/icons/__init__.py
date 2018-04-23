# -*- coding: utf-8 -*-
"""

    mslib.msui.icons
    ~~~~~~~~~~~~~~~~

    This module provides functions to process ECMWF forecast data.

    This file is part of mss.

    :copyright: Copyright 2016-2018 by the mss team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
import os


ICONSIZE = [
    "128x128",
    "16x16",
    "256x256",
    "32x32",
    "48x48",
    "64x64"
]


def icons(icon_size, name="mss-logo.png"):
    if icon_size in ICONSIZE:
        return os.path.join(os.path.abspath(os.path.normpath(os.path.dirname(__file__))), icon_size, name)


def python_powered():
    return os.path.join(os.path.abspath(os.path.normpath(os.path.dirname(__file__))), "python-powered-w-100x40.png")
