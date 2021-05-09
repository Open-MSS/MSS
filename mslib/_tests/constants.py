# -*- coding: utf-8 -*-
"""

    mslib._tests.utils
    ~~~~~~~~~~~~~~~~~~

    This module provides common functions for MSS testing

    This file is part of mss.

    :copyright: Copyright 2017 Reimar Bauer, Joern Ungermann
    :copyright: Copyright 2017-2021 by the mss team, see AUTHORS.
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
from fs.tempfs import TempFS

try:
    import git
except ImportError:
    SHA = ""
else:
    repo = git.Repo(os.path.dirname(os.path.realpath(__file__)), search_parent_directories=True)
    SHA = repo.head.object.hexsha[0:10]

CACHED_CONFIG_FILE = None
SERVER_CONFIG_FILE = "mss_wms_settings.py"
MSCOLAB_CONFIG_FILE = "mscolab_settings.py"
ROOT_FS = TempFS(identifier="mss{}".format(SHA))
OSFS_URL = ROOT_FS.geturl("", purpose="fs")

ROOT_DIR = ROOT_FS.getsyspath("")

if not ROOT_FS.exists("mss/testdata"):
    ROOT_FS.makedirs("mss/testdata")
SERVER_CONFIG_FS = fs.open_fs(fs.path.join(ROOT_DIR, "mss"))
DATA_FS = fs.open_fs(fs.path.join(ROOT_DIR, "mss/testdata"))

MSS_CONFIG_PATH = OSFS_URL
# MSS_CONFIG_PATH = SERVER_CONFIG_FS.getsyspath("") would use a none osfs path
os.environ["MSS_CONFIG_PATH"] = MSS_CONFIG_PATH
SERVER_CONFIG_FILE_PATH = fs.path.join(SERVER_CONFIG_FS.getsyspath(""), SERVER_CONFIG_FILE)

# we keep DATA_DIR until we move netCDF4 files to pyfilesystem2
DATA_DIR = DATA_FS.getsyspath("")

# deployed mscolab url
MSCOLAB_URL = "http://localhost:8083"
# mscolab test server's url
MSCOLAB_URL_TEST = "http://localhost:8084"
