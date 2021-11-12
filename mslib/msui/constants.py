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

import fs
import os
import logging

# ToDo refactor to generic functions, keep only constants
HOME = os.path.expanduser(f"~{os.path.sep}")
MSS_CONFIG_PATH = os.getenv("MSS_CONFIG_PATH", os.path.join(HOME, ".config", "mss"))
if '://' in MSS_CONFIG_PATH:
    try:
        _fs = fs.open_fs(MSS_CONFIG_PATH)
    except fs.errors.CreateFailed:
        _fs.makedirs(MSS_CONFIG_PATH)
    except fs.opener.errors.UnsupportedProtocol:
        logging.error(f'FS url "{MSS_CONFIG_PATH}" not supported')
else:
    _dir = os.path.expanduser(MSS_CONFIG_PATH)
    if not os.path.exists(_dir):
        os.makedirs(_dir)

GRAVATAR_DIR_PATH = fs.path.join(MSS_CONFIG_PATH, "gravatars")

MSS_SETTINGS = os.getenv('MSS_SETTINGS', os.path.join(MSS_CONFIG_PATH, "mss_settings.json"))

# We try to create an empty MSS_SETTINGS file if not existing
# but there can be a permission problem
if '://' in MSS_SETTINGS:
    dir_path, file_name = fs.path.split(MSS_SETTINGS)
    try:
        _fs = fs.open_fs(dir_path)
        if not _fs.exists(file_name):
            with _fs.open(file_name, 'w') as fid:
                fid.write("{}")
    except fs.errors.CreateFailed:
        logging.error(f'"{MSS_SETTINGS}" can''t be created')
else:
    if not os.path.exists(MSS_SETTINGS):
        try:
            with open(MSS_SETTINGS, 'w') as fid:
                fid.write("{}")
        except IOError:
            logging.error(f'"{MSS_SETTINGS}" can''t be created')

WMS_LOGIN_CACHE = {}
MSC_LOGIN_CACHE = {}

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
