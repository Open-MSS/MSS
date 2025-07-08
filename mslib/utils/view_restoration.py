# -*- coding: utf-8 -*-
"""

    mslib/utils/view_restoration.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This file is part of MSS.

    :copyright: Copyright 2025 Annapurna Gupta.
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

import json
import logging
from pathlib import Path
from mslib.msui import constants


def save_view_settings(settings):
    """
    Save view settings (for top, side, linear, and table views) to a JSON file.

    Args:
        settings: A list of dictionaries containing settings for view windows.
                 Each dictionary must have a 'view_type' key ('topview', 'sideview', 'linearview', 'tableview').

    Returns:
        bool: True if settings were saved successfully, False otherwise.
    """
    if not isinstance(settings, list):
        raise TypeError("Settings must be a list of dictionaries")
    for setting in settings:
        if not isinstance(setting, dict) or "view_type" not in setting:
            raise ValueError("Each setting must be a dictionary with a 'view_type' key")

    config_path = Path(constants.MSUI_CONFIG_PATH)
    config_path.mkdir(parents=True, exist_ok=True)
    save_path = config_path / "view_settings.json"
    with open(save_path, "w") as f:
        json.dump(settings, f, indent=4)
    logging.info("Saved view settings to %s", save_path)
    return True


def restore_view_settings():
    config_path = Path(constants.MSUI_CONFIG_PATH)
    save_path = config_path / "view_settings.json"

    if not save_path.exists():
        logging.info("No view setting file found at %s", save_path)

    with open(save_path, "r") as f:
        settings = json.load(f)

    return settings
