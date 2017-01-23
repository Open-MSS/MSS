# -*- coding: iso-8859-1 -*-
"""
    MSS - some common code for testing

    @copyright: 2017 Reimar Bauer,

    @license: License: Apache-2.0, see LICENSE.txt for details.
"""


import os
import importlib
from mslib.mswms.mpl_hsec import MPLBasemapHorizontalSectionStyle

from conftest import BASE_DIR, SERVER_CONFIG_FILE


class TestMPLBasemapHorizontalSectionStyle(object):
    def setup(self):
        if not os.path.exists(BASE_DIR):
            pytest.skip("Demo Data not existing")
        self.mss_wms_settings = importlib.import_module("mss_wms_settings", SERVER_CONFIG_FILE)

    def test_supported_epsg_codes(self):
        assert self.mss_wms_settings.epsg_to_mpl_basemap_table.keys() == [4326]

    def test_supported_crs(self):
        example = MPLBasemapHorizontalSectionStyle()
        assert example.supported_crs() == ['EPSG:4326']
