# -*- coding: utf-8 -*-
"""

    mslib.tutorials.pictures
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides functions to read images for the different tutorials for comparison

    This file is part of MSS.

    :copyright: Copyright 2016-2023 by the MSS team, see AUTHORS.
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


MSUI_CONFIG_PATH = os.environ.get('MSUI_CONFIG_PATH')


def picture(name="layers.png"):
    return os.path.join(MSUI_CONFIG_PATH, 'tutorial_images', name)
