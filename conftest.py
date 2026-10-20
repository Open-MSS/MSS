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

import logging
import sys
# Disable pyc files
sys.dont_write_bytecode = True

import pytest

# Only what every suite needs is here: each package's suite must run with only that package installed. The
# fixtures of the desktop client (test keyring, reset of the msui configuration, Qt helpers) are in
# tests/msui_fixtures.py, loaded by the conftest.py of tests/_test_msui and tests/_test_plugins.

# as mslib.utils.loggerdef.configure_mpl_logger does; mslib.utils isn't in every suite's environment
logging.getLogger("matplotlib").setLevel(logging.INFO)

# This import must come first: tests.constants creates the temporary configuration directories and sets
# MSUI_CONFIG_PATH and XDG_CACHE_HOME before any mslib module reads them.
import tests.constants  # noqa: E402,F401


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


@pytest.fixture(scope="session", autouse=True)
def _ensure_mswms_server_if_needed(request):
    """Fork the mswms server before anything else in this worker touches Qt,
    multiprocessing state, or opens netCDF/HDF5 datasets in-process.
    """
    if any("mswms_server" in item.fixturenames for item in request.session.items):
        request.getfixturevalue("mswms_server")


# Make the server fixtures available everywhere. tests.fixtures imports nothing but the standard library and
# pytest at module level (mslib.mscolab, mslib.mswms etc. are imported inside the fixtures that need them),
# so this is safe and cheap regardless of which test directories are in scope.
from tests.fixtures import *  # noqa: E402,F401,F403
