# -*- coding: utf-8 -*-
"""

    mslib.utils.constants
    ~~~~~~~~~~~~~~~~~~~~~

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

HOME = Path.home()
MSUI_CONFIG_PATH = Path(os.getenv("MSUI_CONFIG_PATH", HOME / ".config" / "msui"))

MSUI_CONFIG_SYSPATH = str(MSUI_CONFIG_PATH.resolve())

MSUI_CACHE_PATH = platformdirs.user_cache_path("msui", "mss")

GRAVATAR_DIR_PATH = MSUI_CONFIG_PATH / "gravatars"

MSUI_SETTINGS = Path(os.getenv('MSUI_SETTINGS', MSUI_CONFIG_PATH / "msui_settings.json"))

MSS_AUTOPLOT = Path(os.getenv('MSS_AUTOPLOT', MSUI_CONFIG_PATH / "mssautoplot.json"))

AUTH_LOGIN_CACHE = {}
