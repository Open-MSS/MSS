# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.conftest
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Directory-scoped test setup for mscolab: resets the mscolab config dir
    (and the example.ftml copy) before every test in this directory.

    Config generation itself (mscolab_settings/mscolab_auth) is lazy, inside
    the mscolab_session_app fixture in tests/fixtures.py -- see
    tests/server_setup.py.

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

from tests.server_setup import ensure_example_ftml, reset_mscolab_config_dir


@pytest.fixture(autouse=True)
def _reset_mscolab_state():
    reset_mscolab_config_dir()
    ensure_example_ftml()
