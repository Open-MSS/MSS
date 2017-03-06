# -*- coding: utf-8 -*-
"""

    mslib.conftest
    ~~~~~~~~~~~~~~

    common definitions for py.test

    This file is part of mss.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2017 by the mss team, see AUTHORS.
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


import imp
import os
import tempfile

try:
    import git
except ImportError:
    git = None
from mslib.mswms.demodata import DataFiles

SHA = ""
if git is not None:
    repo = git.Repo(search_parent_directories=True)
    SHA = repo.head.object.hexsha

BASE_DIR = os.path.join(tempfile.tempdir, u'mss{}'.format(SHA))
DATA_DIR = os.path.join(BASE_DIR, 'testdata')
SERVER_CONFIG_FILE = os.path.join(BASE_DIR, "mss_wms_settings.py")
VALID_TIME_CACHE = os.path.join(BASE_DIR, 'vt_cache')

if not os.path.exists(DATA_DIR):
    examples = DataFiles(data_dir=DATA_DIR,
                         server_config_dir=BASE_DIR)
    examples.create_datadir()
    examples.create_server_config()
    examples.hybrid_data()
    examples.pressure_data()
    examples.sfc_data()

try:
    imp.load_source('mss_wms_settings', SERVER_CONFIG_FILE)
except IOError:
    pass
