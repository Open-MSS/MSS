# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.conftest
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Directory-scoped test setup for mscolab: writes and loads the test settings
    (mscolab_settings/mscolab_auth, see tests/server_setup.py) before the test
    modules are collected, and resets the mscolab config dir (and the
    example.ftml copy) before every test in this directory.

    This file is part of MSS.

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

import pytest

from tests.server_setup import ensure_example_ftml, ensure_mscolab_config, reset_mscolab_config_dir

# The test modules import mslib.mscolab at module level, mslib.mscolab.conf binds mscolab_settings at its first
# import: write and load the test settings before they are collected.
ensure_mscolab_config()


@pytest.fixture(autouse=True)
def _reset_mscolab_state():
    reset_mscolab_config_dir()
    ensure_example_ftml()
