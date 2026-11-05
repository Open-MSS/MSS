# -*- coding: utf-8 -*-
"""

    tests._test_msui.conftest
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    common definitions for _test_msui

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
import pytest
from mslib.msui.utils.service_manager import WMSServiceManager

from tests.server_setup import ensure_example_ftml, ensure_mscolab_config, reset_mscolab_config_dir
# the test keyring, the reset of the msui configuration and the Qt helpers
from tests.msui_fixtures import *  # noqa: F401,F403

# Some test modules import mslib.mscolab at module level (they run against an MSColab server),
# mslib.mscolab.conf binds mscolab_settings at its first import: write and load the test settings first.
ensure_mscolab_config()


@pytest.fixture(autouse=True)
def _reset_mscolab_state():
    reset_mscolab_config_dir()
    ensure_example_ftml()


@pytest.fixture(autouse=True)
def _reset_wms_service_manager():
    WMSServiceManager._shared_cache.clear()
    yield
    WMSServiceManager._shared_cache.clear()
