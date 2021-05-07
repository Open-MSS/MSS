# -*- coding: utf-8 -*-
"""

    mslib.msui.constants
    ~~~~~~~~~~~~~~~~~~~~

    This module provides constants

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr), Tongxi Lou (tl)
    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2021 by the mss team, see AUTHORS.
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

HOME = os.path.expanduser(f"~{os.path.sep}")
MSS_CONFIG_PATH = os.getenv("MSS_CONFIG_PATH", os.path.join(HOME, ".config", "mss"))
if not os.path.exists(MSS_CONFIG_PATH):
    os.makedirs(MSS_CONFIG_PATH)

MSS_SETTINGS = os.getenv('MSS_SETTINGS', os.path.join(MSS_CONFIG_PATH, "mss_settings.json"))

WMS_LOGIN_CACHE = {}
MSC_LOGIN_CACHE = {}

CACHED_CONFIG_FILE = None

if os.path.exists(MSS_SETTINGS):
    CACHED_CONFIG_FILE = MSS_SETTINGS

POSIX = {"application_destination": os.path.join(HOME, ".local/share/applications/mss{}.desktop"),
         "icon_destination": os.path.join(HOME, ".local/share/icons/hicolor/{}/apps/mss-logo{}.png"),
         "desktop": """[Desktop Entry]
Name=mss {}
Comment=A web service based tool to plan atmospheric research flights (mission support system).
Keywords=documentation;information;
Exec={}
Icon={}
Type=Application
Categories=Science;Education;
StartupNotify=true
X-GNOME-SingleWindow=false
X-Ubuntu-Gettext-Domain=mss
"""}
