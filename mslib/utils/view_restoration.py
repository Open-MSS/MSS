# -*- coding: utf-8 -*-
"""

    mslib/utils/view_restoration.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This file is part of MSS.

    :copyright: Copyright 2017-2025 by the MSS team, see AUTHORS.
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


def save_view_settings(settings: dict):
    try:
        config_path = Path(constants.MSUI_CONFIG_PATH)
        config_path.mkdir(parents=True, exist_ok=True)
        save_path = config_path / "view_settings.json"
        with open(save_path, "w") as f:
            json.dump(settings, f, indent=4)
        logging.info("Saved top view settings to %s", save_path)
    except Exception as e:
        logging.error("Failed to save top view settings: %s", e)
