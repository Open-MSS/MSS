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

import sys
# Disable pyc files
sys.dont_write_bytecode = True

import pytest
import keyring
from mslib.utils.loggerdef import configure_mpl_logger

matplotlib_logger = configure_mpl_logger()

# This import must come first: importing tests.constants sets MSUI_CONFIG_PATH,
# which mslib.utils.config needs at import time.
from tests.constants import create_msui_settings_file
from mslib.utils.config import read_config_file

# mslib.mscolab.conf binds its mscolab_settings fallback the first time it is
# imported, anywhere, and then caches that binding for the rest of the
# process -- so this must run before anything imports mslib.mscolab.auth/
# seed/mscolab/server, including transitively via tests.utils/tests.fixtures
# below. It's cheap (just (re)writing two small config files); the actual
# expensive setup (NetCDF demo data, the server fork) stays lazy inside the
# fixtures that need it -- see tests/server_setup.py.
from tests.server_setup import ensure_mscolab_config

ensure_mscolab_config()


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


@pytest.fixture(autouse=True)
def reset_config():
    """Reset the msui configuration file used in the tests after every test.

    The expensive parts of mswms/mscolab server setup (NetCDF demo data, the
    server fork) happen lazily, inside the fixtures that need them (see
    tests/fixtures.py and tests/server_setup.py), so that test-fast doesn't
    pay for them.
    """
    create_msui_settings_file("{}")
    read_config_file()


@pytest.fixture(scope="session", autouse=True)
def _ensure_mscolab_server_if_needed(request):
    """Fork the mscolab server before anything else in this worker touches Qt
    or multiprocessing state -- but only if a collected test actually needs
    it (see the autouse comment on mscolab_session_server in
    tests/fixtures.py for why the fork has to happen first).

    This must be a global, root-conftest autouse fixture rather than one
    scoped to tests/_test_msui/conftest.py: autouse only applies within a
    fixture's own directory subtree, but with pytest-xdist a single worker
    can interleave tests from several directories in one process, so the
    ordering guarantee only holds if this runs before the very first test of
    the whole session, regardless of which directory it belongs to.
    """
    if any("mscolab_session_server" in item.fixturenames for item in request.session.items):
        request.getfixturevalue("mscolab_session_server")


# Make fixtures available everywhere. tests.fixtures itself has no
# mscolab/mswms/Qt side effects at import time (those are lazy, inside the
# fixtures that need them), so this is safe and cheap regardless of which
# test directories are in scope.
from tests.fixtures import *  # noqa: E402,F401,F403
