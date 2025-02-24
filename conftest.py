# -*- coding: utf-8 -*-
"""

    mslib.conftest
    ~~~~~~~~~~~~~~

    common definitions for py.test

    This file is part of MSS.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2024 by the MSS team, see AUTHORS.
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
import sys
# Disable pyc files
sys.dont_write_bytecode = True

import pytest
import fs
import shutil
import keyring
from mslib.mswms.demodata import DataFiles
import tests.constants as constants
from mslib.utils.loggerdef import configure_mpl_logger

matplotlib_logger = configure_mpl_logger()

# This import must come after importing tests.constants due to MSUI_CONFIG_PATH being set there
from mslib.utils.config import read_config_file


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
    """Generate an initial state for the configuration directory in tests.constants.ROOT_FS
    """
    if not constants.ROOT_FS.exists("msui/testdata"):
        constants.ROOT_FS.makedirs("msui/testdata")

    # make a copy for mscolab test, so that we read different paths during parallel tests.
    sample_path = os.path.join(os.path.dirname(__file__), "tests", "data")
    shutil.copy(os.path.join(sample_path, "example.ftml"), constants.ROOT_DIR)

    if not constants.SERVER_CONFIG_FS.exists(constants.SERVER_CONFIG_FILE):
        print('\n configure testdata')
        # ToDo check pytest tmpdir_factory
        examples = DataFiles(data_fs=constants.DATA_FS,
                             server_config_fs=constants.SERVER_CONFIG_FS)
        examples.create_server_config(detailed_information=True)
        examples.create_data()

    if not constants.SERVER_CONFIG_FS.exists(constants.MSCOLAB_CONFIG_FILE):
        config_string = f'''
# SQLALCHEMY_DB_URI = 'mysql://user:pass@127.0.0.1/mscolab'
import os
import logging
import fs
import secrets
from urllib.parse import urljoin

ROOT_DIR = '{constants.ROOT_DIR}'
# directory where mss output files are stored
root_fs = fs.open_fs(ROOT_DIR)
if not root_fs.exists('colabTestData'):
    root_fs.makedir('colabTestData')
BASE_DIR = ROOT_DIR
DATA_DIR = fs.path.join(ROOT_DIR, 'colabTestData')
# mscolab data directory for operation git repositories
OPERATIONS_DATA = fs.path.join(DATA_DIR, 'filedata')
SSO_DIR = fs.path.join(DATA_DIR, 'datasso')

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

SQLALCHEMY_DB_URI = 'sqlite:///' + urljoin(DATA_DIR, 'mscolab.db')

# enable SQLALCHEMY_ECHO
SQLALCHEMY_ECHO = False

# mscolab file upload settings
UPLOAD_FOLDER = fs.path.join(DATA_DIR, 'uploads')
MAX_UPLOAD_SIZE = 2 * 1024 * 1024  # 2MB

# text to be written in new mscolab based ftml files.
STUB_CODE = """<?xml version="1.0" encoding="utf-8"?>
<FlightTrack version="1.7.6">
  <ListOfWaypoints>
    <Waypoint flightlevel="250" lat="67.821" location="Kiruna" lon="20.336">
      <Comments></Comments>
    </Waypoint>
    <Waypoint flightlevel="250" lat="78.928" location="Ny-Alesund" lon="11.986">
      <Comments></Comments>
    </Waypoint>
  </ListOfWaypoints>
</FlightTrack>
"""
enable_basic_http_authentication = False

# enable login by identity provider
USE_SAML2 = False
'''
        ROOT_FS = fs.open_fs(constants.ROOT_DIR)
        if not ROOT_FS.exists('mscolab'):
            ROOT_FS.makedir('mscolab')
        with fs.open_fs(fs.path.join(constants.ROOT_DIR, "mscolab")) as mscolab_fs:
            # windows needs \\ or / but mixed is terrible. *nix needs /
            mscolab_fs.writetext(constants.MSCOLAB_CONFIG_FILE, config_string.replace('\\', '/'))
        path = fs.path.join(constants.ROOT_DIR, 'mscolab', constants.MSCOLAB_CONFIG_FILE)

    if not constants.SERVER_CONFIG_FS.exists(constants.MSCOLAB_AUTH_FILE):
        config_string = '''
import hashlib

class mscolab_auth:
     password = "testvaluepassword"
     allowed_users = [("user", hashlib.md5(password.encode('utf-8')).hexdigest())]
'''
        ROOT_FS = fs.open_fs(constants.ROOT_DIR)
        if not ROOT_FS.exists('mscolab'):
            ROOT_FS.makedir('mscolab')
        with fs.open_fs(fs.path.join(constants.ROOT_DIR, "mscolab")) as mscolab_fs:
            # windows needs \\ or / but mixed is terrible. *nix needs /
            mscolab_fs.writetext(constants.MSCOLAB_AUTH_FILE, config_string.replace('\\', '/'))

    def _load_module(module_name, path):
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

    _load_module("mswms_settings", constants.SERVER_CONFIG_FILE_PATH)
    _load_module("mscolab_settings", path)


generate_initial_config()


# This import must come after the call to generate_initial_config, otherwise SQLAlchemy will have a wrong database path
from tests.utils import create_msui_settings_file


@pytest.fixture(autouse=True)
def reset_config():
    """Reset the configuration directory used in the tests (tests.constants.ROOT_FS) after every test
    """
    # Ideally this would just be constants.ROOT_FS.removetree("/"), but SQLAlchemy complains if the SQLite file is
    # deleted.
    for e in constants.ROOT_FS.walk.files(exclude=["mscolab.db"]):
        constants.ROOT_FS.remove(e)
    for e in constants.ROOT_FS.walk.dirs(search="depth"):
        constants.ROOT_FS.removedir(e)

    generate_initial_config()
    create_msui_settings_file("{}")
    read_config_file()


# Make fixtures available everywhere
from tests.fixtures import *  # noqa: F401, F403
