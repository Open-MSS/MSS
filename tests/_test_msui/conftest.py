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
from mslib.utils.service_manager import WMSServiceManager


@pytest.fixture(autouse=True)
def _reset_wms_service_manager():
    WMSServiceManager._shared_cache.clear()
    yield
    WMSServiceManager._shared_cache.clear()