# -*- coding: utf-8 -*-
"""

    mslib.tutorials.utils.picture
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides functions to read images for the different tutorials for comparison

    This file is part of MSS.

    :copyright: Copyright 2016-2022 by the MSS team, see AUTHORS.
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
import time
from pathlib import Path
from slugify import slugify
from PIL import Image
from mslib.msui.constants import MSUI_CONFIG_PATH


def picture(name, bounding_box=None):
    filename = os.path.join(MSUI_CONFIG_PATH, "tutorial_images", name)
    if bounding_box is not None:
        with Image.open(filename) as img:
            cropped_img = img.crop(bounding_box)
            part = '-'.join([str(val) for val in bounding_box])
            new_name = slugify(f'{Path(name).stem}-{part}')
            filename = os.path.join(MSUI_CONFIG_PATH, "tutorial_images", f'{new_name}.png')
            cropped_img.save(filename)
        time.sleep(1)
    return filename
