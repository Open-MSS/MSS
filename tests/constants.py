# -*- coding: utf-8 -*-
"""

    tests.constants
    ~~~~~~~~~~~~~~~

    This module provides common testdata for MSS testing

    This file is part of MSS.

    :copyright: Copyright 2017 Reimar Bauer, Joern Ungermann
    :copyright: Copyright 2017-2024 by the MSS team, see AUTHORS.
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
import fs
import tempfile
from fs.tempfs import TempFS

CACHED_CONFIG_FILE = None
SERVER_CONFIG_FILE = "mswms_settings.py"
MSCOLAB_CONFIG_FILE = "mscolab_settings.py"
MSCOLAB_AUTH_FILE = "mscolab_auth.py"
ROOT_FS = TempFS(identifier="msui")
OSFS_URL = ROOT_FS.geturl("", purpose="fs")

ROOT_DIR = ROOT_FS.getsyspath("")

if not ROOT_FS.exists("msui/testdata"):
    ROOT_FS.makedirs("msui/testdata")
SERVER_CONFIG_FS = fs.open_fs(fs.path.join(ROOT_DIR, "msui"))
DATA_FS = fs.open_fs(fs.path.join(ROOT_DIR, "msui/testdata"))

MSUI_CONFIG_PATH = OSFS_URL
# MSUI_CONFIG_PATH = SERVER_CONFIG_FS.getsyspath("") would use a none osfs path
os.environ["MSUI_CONFIG_PATH"] = MSUI_CONFIG_PATH
SERVER_CONFIG_FILE_PATH = fs.path.join(SERVER_CONFIG_FS.getsyspath(""), SERVER_CONFIG_FILE)

_xdg_cache_home_temporary_directory = tempfile.TemporaryDirectory()
os.environ["XDG_CACHE_HOME"] = _xdg_cache_home_temporary_directory.name

# we keep DATA_DIR until we move netCDF4 files to pyfilesystem2
DATA_DIR = DATA_FS.getsyspath("")

# deployed mscolab url
MSCOLAB_URL = "http://localhost:8083"
# mscolab test server's url
MSCOLAB_URL_TEST = "http://localhost:8084"
