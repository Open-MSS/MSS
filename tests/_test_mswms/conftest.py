# -*- coding: utf-8 -*-
"""

    tests._test_mswms.conftest
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Directory-scoped test setup for mswms: several test modules here import
    mslib.mswms.wms/mswms directly at module scope (not just via the mswms_app
    fixture in tests/fixtures.py). mslib.mswms.app binds its mswms_settings
    fallback the first time it is imported, anywhere, and caches that binding
    for the rest of the process -- so the demo NetCDF data + mswms_settings.py
    must exist before pytest imports any test module in this directory, which
    is exactly when conftest.py itself gets imported.

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

from tests.server_setup import ensure_mswms_testdata

ensure_mswms_testdata()
