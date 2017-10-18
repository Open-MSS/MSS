# -*- coding: utf-8 -*-
"""

    mslib._tests.utils
    ~~~~~~~~~~~~~~~~~~

    This module provides common functions for MSS testing

    This file is part of mss.

    :copyright: Copyright 2017 Reimar Bauer, Joern Ungermann
    :copyright: Copyright 2017 by the mss team, see AUTHORS.
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
    repo = git.Repo(search_parent_directories=True)
    SHA = repo.head.object.hexsha

SERVER_CONFIG_FILE = u"mss_wms_settings.py"
ROOT_FS = TempFS(identifier="mss{}".format(SHA))
ROOT_DIR = ROOT_FS.root_path

if not ROOT_FS.exists(u"mss/testdata"):
    ROOT_FS.makedirs(u"mss/testdata")
SERVER_CONFIG_FS = fs.open_fs(fs.path.join(ROOT_DIR, u'mss'))
DATA_FS = fs.open_fs(fs.path.join(ROOT_DIR, u'mss/testdata'))

os.environ["MSS_CONFIG_PATH"] = SERVER_CONFIG_FS.root_path
SERVER_CONFIG_FILE_PATH = fs.path.join(SERVER_CONFIG_FS.root_path, SERVER_CONFIG_FILE)

# just now
DATA_DIR = DATA_FS.root_path
BASE_DIR = ROOT_DIR
