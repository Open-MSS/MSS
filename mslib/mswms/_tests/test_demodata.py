# -*- coding: utf-8 -*-
"""

    mslib.mswms._tests.test_demodata
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mswms.demodata

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2017 Reimar Bauer
    :copyright: Copyright 2016-2017 by the mss team, see AUTHORS.
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
import os
import imp
from conftest import BASE_DIR, DATA_DIR, SERVER_CONFIG_FILE


class TestDemodate(object):

    def test_data_creation(self):
        if not os.path.exists(BASE_DIR):
            pytest.skip("Demo Data not existing")
        assert os.path.exists(BASE_DIR)
        assert os.path.exists(DATA_DIR)
        assert os.path.exists(SERVER_CONFIG_FILE)
        assert len(os.listdir(DATA_DIR)) == 9

    def test_server_config_file(self):
        if not os.path.exists(BASE_DIR):
            pytest.skip("Demo Data not existing")
        imp.load_source('mss_wms_settings', SERVER_CONFIG_FILE)
