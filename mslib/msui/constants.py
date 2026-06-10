# -*- coding: utf-8 -*-
"""

    mslib.msui.constants
    ~~~~~~~~~~~~~~~~~~~~

    This module provides constants

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr), Tongxi Lou (tl)
    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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
import platformdirs
from pathlib import Path

def _get_config_path():
    home = Path.home()
    return Path(os.getenv("MSUI_CONFIG_PATH", home / ".config" / "msui"))

MSUI_CONFIG_PATH = _get_config_path()
MSUI_CONFIG_SYSPATH = str(MSUI_CONFIG_PATH.resolve())
GRAVATAR_DIR_PATH = MSUI_CONFIG_PATH / "gravatars"

def _get_settings_path():
    return Path(os.getenv("MSUI_SETTINGS", MSUI_CONFIG_PATH / "msui_settings.json"))

def _get_autoplot_path():
    return Path(os.getenv("MSS_AUTOPLOT", MSUI_CONFIG_PATH / "mssautoplot.json"))

MSUI_SETTINGS = _get_settings_path()
MSS_AUTOPLOT = _get_autoplot_path()


AUTH_LOGIN_CACHE = {}
