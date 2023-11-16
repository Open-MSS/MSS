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
from PIL import Image
from slugify import slugify


MSUI_CONFIG_PATH = os.environ.get('MSUI_CONFIG_PATH')


def picture(name="layers.png", boundingbox=None):
    """
    picture('multilayersdialog-temperature.png', (627,0, 657,20)) creates multilayersdialog-temperature-627-0-657-20.png
    """
    filename = os.path.join(MSUI_CONFIG_PATH, 'tutorial_images', name)
    # ToDo figure how the tutorial mode can catch all elements of the UI
    if boundingbox is not None:
        im = Image.open(filename)
        im1 = im.crop(boundingbox)
        attr = '-'.join([str(item) for item in boundingbox])
        filename = slugify(f"{name[:-4]}-{attr}")
        filename = os.path.join(MSUI_CONFIG_PATH, f"{filename}.png")
        im1.save(filename)
    return filename
