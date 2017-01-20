# -*- coding: iso-8859-1 -*-
"""
    MSS - some common code for testing

    @copyright: 2016 - 2017 Reimar Bauer,

    @license: License: Apache-2.0, see LICENSE.txt for details.
"""

import sys
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


BASE_DIR = os.path.join(tempfile.tempdir, 'mss%s' % SHA)
sys.path.insert(0, BASE_DIR)


DATA_DIR = os.path.join(BASE_DIR, 'testdata')
SERVER_CONFIG_FILE = os.path.join(BASE_DIR, "mss_wms_settings.py")
VALID_TIME_CACHE = os.path.join(BASE_DIR, 'testdata', 'vt_cache')

if not os.path.exists(DATA_DIR):
    examples = DataFiles(data_dir=DATA_DIR,
                         server_config_dir=BASE_DIR)
    examples.create_datadir()
    examples.create_server_config()
    examples.hybrid_data()
    examples.pressure_data()
    examples.sfc_data()
