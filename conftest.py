# -*- coding: utf-8 -*-
"""

    mslib.conftest
    ~~~~~~~~~~~~~~

    common definitions for py.test

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
import shutil
import importlib.util
import os
import sys
import tempfile
from pathlib import Path
# Disable pyc files
sys.dont_write_bytecode = True

_tmpdir_kwargs = {"ignore_cleanup_errors": True} if sys.version_info >= (3, 10) else {}
_tmp_dir = tempfile.TemporaryDirectory(**_tmpdir_kwargs)
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
os.environ["MSUI_CONFIG_PATH"] = str(MSUI_CONFIG_PATH.resolve())
MSUI_CONFIG_FILE_PATH = MSUI_CONFIG_PATH / "msui_settings.json"

if not MSUI_CONFIG_PATH.exists():
    MSUI_CONFIG_PATH.mkdir(parents=True)

_xdg_cache_home_temporary_directory = tempfile.TemporaryDirectory(**_tmpdir_kwargs)
os.environ["XDG_CACHE_HOME"] = _xdg_cache_home_temporary_directory.name

import pytest
import keyring
from mslib.mswms.seed import DataFiles
from mslib.utils.loggerdef import configure_mpl_logger

matplotlib_logger = configure_mpl_logger()

# This import must come after importing tests.constants due to MSUI_CONFIG_PATH being set there


class TestKeyring(keyring.backend.KeyringBackend):
    """A test keyring which always outputs the same password
    from Runtime Configuration
    https://pypi.org/project/keyring/#third-party-backends
    """
    priority = 1

    passwords = {}

    def reset(self):
        self.passwords = {}

    def set_password(self, servicename, username, password):
        self.passwords[servicename + username] = password

    def get_password(self, servicename, username):
        return self.passwords.get(servicename + username, "password from TestKeyring")

    def delete_password(self, servicename, username):
        if servicename + username in self.passwords:
            del self.passwords[servicename + username]


# set the keyring for keyring lib
keyring.set_keyring(TestKeyring())


@pytest.fixture(autouse=True)
def keyring_reset():
    keyring.get_keyring().reset()


def generate_initial_config():
    """Generate an initial state for the configuration directory in ROOT_DIR.
    """
    # make a copy for mscolab test, so that we read different paths during parallel tests.
    sample_path = os.path.join(os.path.dirname(__file__), "tests", "data")
    shutil.copy(os.path.join(sample_path, "example.ftml"), ROOT_DIR)

    if not MSWMS_SERVER_CONFIG_FILE_PATH.exists():
        print('\n configure testdata')
        # ToDo check pytest tmpdir_factory
        print(MSWMS_DATA_DIR)
        examples = DataFiles(mswms_data_dir=MSWMS_DATA_DIR,
                             mswms_server_config_dir=MSWMS_SERVER_CONFIG_DIR)
        examples.create_server_config(detailed_information=True)
        examples.create_data()

    if not MSCOLAB_SERVER_CONFIG_FILE_PATH.exists():
        config_string = f'''
# SQLALCHEMY_DATABASE_URI = 'mysql://user:pass@127.0.0.1/mscolab'
import os
import logging
import secrets
from pathlib import Path
from urllib.parse import urljoin

ROOT_DIR = "{ROOT_DIR.as_posix()}"
# directory where mss output files are stored
DATA_DIR = "{MSCOLAB_DATA_DIR.as_posix()}"
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

SQLALCHEMY_DATABASE_URI = 'sqlite:///{MSCOLAB_SERVER_CONFIG_DIR.as_posix()}/mscolab.db'

# Extend SQLite busy-wait timeout (seconds) so concurrent workers don't
# immediately fail with "database is locked" during Alembic migrations.
SQLALCHEMY_ENGINE_OPTIONS = {{"connect_args": {{"timeout": 30}}}}

# enable SQLALCHEMY_ECHO
SQLALCHEMY_ECHO = False

# mscolab file upload settings
UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
MAX_UPLOAD_SIZE = 2 * 1024 * 1024  # 2MB

enable_basic_http_authentication = False

# enable login by identity provider
USE_SAML2 = False
'''
        MSCOLAB_CONFIG = MSCOLAB_SERVER_CONFIG_FILE_PATH
        MSCOLAB_CONFIG.write_text(config_string)
        mscolab_auth_file = MSCOLAB_SERVER_CONFIG_DIR / MSCOLAB_AUTH_FILE
        if not mscolab_auth_file.exists():
            config_string = '''
import hashlib

class mscolab_auth:
     password = "testvaluepassword"
     allowed_users = [("user", hashlib.md5(password.encode('utf-8')).hexdigest())]
'''
            mscolab_auth_file.write_text(config_string)

    def _load_module(module_name, path):
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

    _load_module("mswms_settings", MSWMS_SERVER_CONFIG_FILE_PATH)
    _load_module("mscolab_settings", MSCOLAB_SERVER_CONFIG_FILE_PATH)


def pytest_configure(config):
    """In xdist workers, give each worker its own log file to avoid closed-stream
    errors when multiple workers share the same pytest.log file handle."""
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    if worker_id:
        log_file = getattr(config.option, "log_file", None) or config.getini("log_file")
        if log_file:
            base, ext = os.path.splitext(log_file)
            config.option.log_file = f"{base}_{worker_id}{ext}"


generate_initial_config()

# Make fixtures available everywhere
from tests.fixtures import *  # noqa: F401, F403
