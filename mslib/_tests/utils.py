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
import tempfile

try:
    import git
except ImportError:
    SHA = ""
else:
    repo = git.Repo(search_parent_directories=True)
    SHA = repo.head.object.hexsha


BASE_DIR = os.path.join(tempfile.gettempdir(), u"mss{}".format(SHA))
DATA_DIR = os.path.join(BASE_DIR, u'testdata')
SERVER_CONFIG_FILE = os.path.join(BASE_DIR, u"mss_wms_settings.py")
os.environ["MSS_CONFIG_PATH"] = BASE_DIR
