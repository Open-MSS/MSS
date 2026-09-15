# -*- coding: utf-8 -*-
"""

    tests.server_setup
    ~~~~~~~~~~~~~~~~~~~

    Lazy setup helpers for the mswms/mscolab test server config and demo data.

    These are split out of the old monolithic root conftest.py so that only the
    test directories that actually need a running mswms/mscolab server (or their
    settings modules importable) pay for generating them. This module itself has
    no mscolab/msui/Qt imports, so importing it has no side effects.

    This file is part of MSS.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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

import importlib.util
import os
import shutil
import sys

from mslib.mswms.seed import DataFiles
import tests.constants as constants


def _load_module(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)


def ensure_example_ftml():
    """Refresh the shared example.ftml copy in tests.constants.ROOT_DIR.

    Mscolab/msui tests read and mutate this path, so it needs to be reset
    before every test that touches it.
    """
    sample_path = os.path.join(os.path.dirname(__file__), "data")
    shutil.copy(os.path.join(sample_path, "example.ftml"), constants.ROOT_DIR)


def ensure_mswms_testdata():
    """Create demo NetCDF data + mswms_settings.py once, then (re-)load
    mswms_settings into sys.modules.

    Must run before anything imports mslib.mswms.mswms, which binds its
    config from mswms_settings at import time.
    """
    if not constants.MSWMS_SERVER_CONFIG_FILE_PATH.exists():
        print('\n configure testdata')
        print(constants.MSWMS_DATA_DIR)
        examples = DataFiles(mswms_data_dir=constants.MSWMS_DATA_DIR,
                             mswms_server_config_dir=constants.MSWMS_SERVER_CONFIG_DIR)
        examples.create_server_config(detailed_information=True)
        examples.create_data()
    _load_module("mswms_settings", constants.MSWMS_SERVER_CONFIG_FILE_PATH)


def ensure_mscolab_config():
    """Write mscolab_settings.py/mscolab_auth.py once, then (re-)load them
    into sys.modules.

    Must run before anything imports mslib.mscolab.server, which binds its
    SQLAlchemy URI from mscolab_settings at import time.
    """
    if not constants.MSCOLAB_SERVER_CONFIG_FILE_PATH.exists():
        config_string = f'''
# SQLALCHEMY_DATABASE_URI = 'mysql://user:pass@127.0.0.1/mscolab'
import os
import logging
import secrets
from pathlib import Path
from urllib.parse import urljoin

ROOT_DIR = "{constants.ROOT_DIR}"
# directory where mss output files are stored
DATA_DIR = "{constants.MSCOLAB_DATA_DIR}"
# this will be removed
OPERATIONS_DATA = Path(DATA_DIR)
BASE_DIR = ROOT_DIR
# mscolab data directory for operation git repositories
SSO_DIR = os.path.join(ROOT_DIR, 'datasso')

# In the unit days when Operations get archived because not used
ARCHIVE_THRESHOLD = 30

# To enable logging set to True or pass a logger object to use.
SOCKETIO_LOGGER = True

# To enable Engine.IO logging set to True or pass a logger object to use.
ENGINEIO_LOGGER = True

# used to generate and parse tokens
SECRET_KEY = secrets.token_urlsafe(16)

# used to generate the password token
SECURITY_PASSWORD_SALT = secrets.token_urlsafe(16)

# looks for a given category for an operation ending with GROUP_POSTFIX
# e.g. category = Tex will look for TexGroup
# all users in that Group are set to the operations of that category
# having the roles in the TexGroup
GROUP_POSTFIX = "Group"

# mail settings
MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USE_TLS = False
MAIL_USE_SSL = True

# mail authentication
MAIL_USERNAME = os.environ.get('APP_MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('APP_MAIL_PASSWORD')

# mail accounts
MAIL_DEFAULT_SENDER = 'MSS@localhost'

# enable verification by Mail
MAIL_ENABLED = False

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + urljoin(DATA_DIR, 'mscolab.db')

# enable SQLALCHEMY_ECHO
SQLALCHEMY_ECHO = False

# mscolab file upload settings
UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
MAX_UPLOAD_SIZE = 2 * 1024 * 1024  # 2MB

ENABLE_BASIC_HTTP_AUTHENTICATION = False

# enable login by identity provider
USE_SAML2 = False
'''
        MSCOLAB_CONFIG = constants.MSCOLAB_SERVER_CONFIG_FILE_PATH
        MSCOLAB_CONFIG.write_text(config_string)
        MSCOLAB_AUTH_FILE = constants.MSCOLAB_SERVER_CONFIG_DIR / constants.MSCOLAB_AUTH_FILE
        if not MSCOLAB_AUTH_FILE.exists():
            config_string = '''
import hashlib

class mscolab_auth:
     password = "testvaluepassword"
     allowed_users = [("user", hashlib.md5(password.encode('utf-8')).hexdigest())]
'''
            MSCOLAB_AUTH_FILE.write_text(config_string)

    _load_module("mscolab_settings", constants.MSCOLAB_SERVER_CONFIG_FILE_PATH)
    _load_module("mscolab_auth", constants.MSCOLAB_SERVER_CONFIG_DIR / constants.MSCOLAB_AUTH_FILE)


def reset_mscolab_config_dir():
    """Wipe and regenerate the mscolab config dir; called before every test
    in directories that exercise mscolab (moved verbatim out of the old
    root conftest.py `reset_config` fixture).
    """
    # Ideally this would just be shutil.rmtree(constants.MSCOLAB_SERVER_CONFIG_DIR),
    # but SQLAlchemy complains if the SQLite file is deleted.
    for item_name in constants.MSCOLAB_SERVER_CONFIG_DIR.iterdir():
        if item_name.is_dir():
            shutil.rmtree(item_name)
        else:
            if item_name.name != "mscolab.db":
                item_name.unlink()

    # Remove the client-side "work locally" cache. create_local_operation_file reuses an
    # existing FTML file, so stale waypoints would leak into any later test (or repeated
    # run of the same test) that toggles the work-locally mode.
    local_colabdata = constants.ROOT_DIR / "local_colabdata"
    if local_colabdata.exists():
        shutil.rmtree(local_colabdata, ignore_errors=True)

    ensure_mscolab_config()
