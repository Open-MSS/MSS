# -*- coding: iso-8859-1 -*-
"""
    MSS - some common code for testing

    @copyright: 2017 Reimar Bauer,

    @license: License: Apache-2.0, see LICENSE.txt for details.
"""


import pytest
import os
import sys
import importlib
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
        importlib.import_module("mss_wms_settings")
        assert "mss_wms_settings" in sys.modules
