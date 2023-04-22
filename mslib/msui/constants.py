# -*- coding: utf-8 -*-
"""

    mslib.msui.constants
    ~~~~~~~~~~~~~~~~~~~~

    This module provides constants

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr), Tongxi Lou (tl)
    :copyright: Copyright 2016-2017 Reimar Bauer
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

import fs
import os
import logging

# ToDo refactor to generic functions, keep only constants
HOME = os.path.expanduser(f"~{os.path.sep}")
MSUI_CONFIG_PATH = os.getenv("MSUI_CONFIG_PATH", os.path.join(HOME, ".config", "msui"))
if '://' in MSUI_CONFIG_PATH:
    try:
        _fs = fs.open_fs(MSUI_CONFIG_PATH)
    except fs.errors.CreateFailed:
        _fs.makedirs(MSUI_CONFIG_PATH)
    except fs.opener.errors.UnsupportedProtocol:
        logging.error('FS url "%s" not supported', MSUI_CONFIG_PATH)
else:
    _dir = os.path.expanduser(MSUI_CONFIG_PATH)
    if not os.path.exists(_dir):
        os.makedirs(_dir)

GRAVATAR_DIR_PATH = fs.path.join(MSUI_CONFIG_PATH, "gravatars")

MSUI_SETTINGS = os.getenv('MSUI_SETTINGS', os.path.join(MSUI_CONFIG_PATH, "msui_settings.json"))

# We try to create an empty MSUI_SETTINGS file if not existing
# but there can be a permission problem
if '://' in MSUI_SETTINGS:
    dir_path, file_name = fs.path.split(MSUI_SETTINGS)
    try:
        _fs = fs.open_fs(dir_path)
        if not _fs.exists(file_name):
            with _fs.open(file_name, 'w') as fid:
                fid.write("{}")
    except fs.errors.CreateFailed:
        logging.error('"%s" can''t be created', MSUI_SETTINGS)
else:
    if not os.path.exists(MSUI_SETTINGS):
        try:
            with open(MSUI_SETTINGS, 'w') as fid:
                fid.write("{}")
        except IOError:
            logging.error('"%s" can''t be created', MSUI_SETTINGS)

# ToDo refactor to a function
MSS_AUTOPLOT = os.getenv('MSS_AUTOPLOT', os.path.join(MSUI_CONFIG_PATH, "mssautoplot.json"))

# We try to create an empty MSUI_SETTINGS file if not existing
# but there can be a permission problem
if '://' in MSS_AUTOPLOT:
    dir_path, file_name = fs.path.split(MSS_AUTOPLOT)
    try:
        _fs = fs.open_fs(dir_path)
        if not _fs.exists(file_name):
            with _fs.open(file_name, 'w') as fid:
                fid.write("{}")
    except fs.errors.CreateFailed:
        logging.error('"%s" can''t be created', MSS_AUTOPLOT)
else:
    if not os.path.exists(MSS_AUTOPLOT):
        try:
            with open(MSS_AUTOPLOT, 'w') as fid:
                fid.write("{}")
        except IOError:
            logging.error('"%s" can''t be created', MSS_AUTOPLOT)

AUTH_LOGIN_CACHE = {}

POSIX = {"application_destination": os.path.join(HOME, ".local/share/applications/msui{}.desktop"),
         "icon_destination": os.path.join(HOME, ".local/share/icons/hicolor/{}/apps/mss-logo{}.png"),
         "desktop": """[Desktop Entry]
Name=msui {}
Comment=A web service based tool to plan atmospheric research flights (mission support system).
Keywords=documentation;information;
Exec={}
Icon={}
Type=Application
Categories=Science;Education;
StartupNotify=true
X-GNOME-SingleWindow=false
X-Ubuntu-Gettext-Domain=msui
"""}
