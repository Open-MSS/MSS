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

import os
import imp
import numpy as np
from mslib._tests.utils import BASE_DIR, DATA_DIR, SERVER_CONFIG_FILE
import mslib.mswms.demodata as demodata


class TestDemodate(object):
    def test_data_creation(self):
        assert os.path.exists(BASE_DIR)
        assert os.path.exists(DATA_DIR)
        assert os.path.exists(SERVER_CONFIG_FILE)
        assert len(os.listdir(DATA_DIR)) == 18

    def test_server_config_file(self):
        imp.load_source('mss_wms_settings', SERVER_CONFIG_FILE)

    def test_get_profile(self):
        mean, std = demodata.get_profile("air_pressure", [10, 100, 500], "air_temperature")
        assert np.allclose(mean, [215., 212., 255.])
        assert np.allclose(std, [3.79, 6.31, 6.33])

        mean, std = demodata.get_profile("air_potential_temperature", [300, 350, 400], "geopotential_height")
        assert np.allclose(mean, [2953.99369248, 12007.44365002, 15285.95068235])
        assert np.allclose(std, [1176.75343762, 2481.27730176, 1649.47761167])

        mean, std = demodata.get_profile("ertel_potential_vorticity", [2, 4, 8], "geopotential_height")
        assert np.allclose(mean, [9565.89928058, 11148.1865285, 14139.43661972])
        assert np.allclose(std, [2557.05035971, 2579.43005181, 1965.91549296])

    def test_generate_field(self):
        data, unit = demodata.generate_field("air_pressure", [10, 100, 500], "geopotential_height", 2, 4, 5)
        assert isinstance(data, np.ndarray)
        assert isinstance(unit, basestring)
        assert len(data.shape) == 4
        assert all(_x == _y for _x, _y in zip(data.shape, (2, 3, 4, 5)))

    def test_generate_surface(self):
        data, unit = demodata.generate_surface("atmosphere_boundary_layer_thickness", 2, 4, 5)
        assert isinstance(data, np.ndarray)
        assert isinstance(unit, basestring)
        assert len(data.shape) == 3
        assert all(_x == _y for _x, _y in zip(data.shape, (2, 4, 5)))

    def test_SURFACE(self):
        assert isinstance(demodata._SURFACE, dict)
        for key, entry in demodata._SURFACE.items():
            assert "data" in entry
            assert "unit" in entry
            assert isinstance(entry["unit"], basestring)
            assert isinstance(entry["data"], np.ndarray)

    def test_PROFILES(self):
        assert isinstance(demodata._PROFILES, dict)
        for key, entry in demodata._PROFILES.items():
            assert "data" in entry
            assert "unit" in entry
            assert isinstance(entry["unit"], basestring)
            assert isinstance(entry["data"], np.ndarray)
