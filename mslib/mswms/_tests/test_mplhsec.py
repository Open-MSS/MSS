# -*- coding: utf-8 -*-
"""

    mslib.mswms._tests.test_mplhsec
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mswms.mplhsec

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2017 Reimar Bauer
    :copyright: Copyright 2016-2018 by the mss team, see AUTHORS.
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

import importlib

from mslib.mswms.mpl_hsec import MPLBasemapHorizontalSectionStyle
from mslib._tests.constants import SERVER_CONFIG_FILE


class TestMPLBasemapHorizontalSectionStyle(object):
    def setup(self):
        self.mss_wms_settings = importlib.import_module("mss_wms_settings", SERVER_CONFIG_FILE)

    def test_supported_epsg_codes(self):
        assert list(self.mss_wms_settings.epsg_to_mpl_basemap_table.keys()) == [4326]

    def test_supported_crs(self):
        example = MPLBasemapHorizontalSectionStyle()
        assert sorted(example.supported_crs()) == \
            sorted(["EPSG:3031", "EPSG:3995", "EPSG:3857", "EPSG:4326", "MSS:stere"])
