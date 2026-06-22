# -*- coding: utf-8 -*-
"""

    tests.constants
    ~~~~~~~~~~~~~~~

    This module provides common testdata for MSS testing

    This file is part of MSS.

    :copyright: Copyright 2017 Reimar Bauer, Joern Ungermann
    :copyright: Copyright 2017-2026 by the MSS team, see AUTHORS.
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
import tempfile
from pathlib import Path


CACHED_CONFIG_FILE = None
_tmp_dir = tempfile.TemporaryDirectory()
ROOT_DIR = Path(_tmp_dir.name)

MSWMS_SERVER_CONFIG_FILE = "mswms_settings.py"
MSWMS_SERVER_CONFIG_DIR = ROOT_DIR / "mswms"
MSWMS_DATA_DIR = MSWMS_SERVER_CONFIG_DIR / "testdata"
MSWMS_SERVER_CONFIG_FILE_PATH = MSWMS_SERVER_CONFIG_DIR / MSWMS_SERVER_CONFIG_FILE

if not MSWMS_DATA_DIR.exists():
    MSWMS_DATA_DIR.mkdir(parents=True)

MSCOLAB_CONFIG_FILE = "mscolab_settings.py"
MSCOLAB_AUTH_FILE = "mscolab_auth.py"
MSCOLAB_SERVER_CONFIG_DIR = ROOT_DIR / "mscolab"
MSCOLAB_DATA_DIR = MSCOLAB_SERVER_CONFIG_DIR / "filedata"
MSCOLAB_SERVER_CONFIG_FILE_PATH = MSCOLAB_SERVER_CONFIG_DIR / MSCOLAB_CONFIG_FILE

if not MSCOLAB_DATA_DIR.exists():
    MSCOLAB_DATA_DIR.mkdir(parents=True)

MSUI_CONFIG_PATH = ROOT_DIR / "msui"
if not MSUI_CONFIG_PATH.exists():
    MSUI_CONFIG_PATH.mkdir(parents=True)
os.environ["MSUI_CONFIG_PATH"] = str(MSUI_CONFIG_PATH.resolve())
MSUI_CONFIG_FILE_PATH = MSUI_CONFIG_PATH / "msui_settings.json"

_xdg_cache_home_temporary_directory = tempfile.TemporaryDirectory()
os.environ["XDG_CACHE_HOME"] = _xdg_cache_home_temporary_directory.name

# deployed mscolab url
MSCOLAB_URL = "http://localhost:8083"
# mscolab test server's url
MSCOLAB_URL_TEST = "http://localhost:8084"
