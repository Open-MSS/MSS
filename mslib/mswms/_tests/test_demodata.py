# -*- coding: utf-8 -*-
"""

    mslib.mswms._tests.test_demodata
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mswms.demodata

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2017 Reimar Bauer
    :copyright: Copyright 2016-2021 by the mss team, see AUTHORS.
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

from past.builtins import basestring

import imp
import numpy as np
from mslib._tests.constants import SERVER_CONFIG_FS, DATA_FS, ROOT_FS, SERVER_CONFIG_FILE, SERVER_CONFIG_FILE_PATH
import mslib.mswms.demodata as demodata


class TestDemodata(object):
    def test_data_creation(self):
        assert ROOT_FS.exists(u'.')
        assert DATA_FS.exists(u'.')
        assert SERVER_CONFIG_FS.exists(SERVER_CONFIG_FILE)
        assert len(DATA_FS.listdir(u'.')) == 19

    def test_server_config_file(self):
        imp.load_source('mss_wms_settings', SERVER_CONFIG_FILE_PATH)

    def test_get_profile(self):
        mean, std = demodata.get_profile("air_pressure", [1000, 10000, 50000], "air_temperature")
        assert np.allclose(mean, [223., 212., 255.])
        assert np.allclose(std, [3.03, 6.31, 6.33])

        mean, std = demodata.get_profile("air_potential_temperature", [300, 350, 400], "geopotential_height")
        assert np.allclose(mean, [2970., 12026.92307692, 15307.89473684])
        assert np.allclose(std, [118, 247.69230769, 164.34210526])

        mean, std = demodata.get_profile("ertel_potential_vorticity", [2, 4, 8], "geopotential_height")
        assert np.allclose(mean, [9565.89928058, 11148.1865285, 14139.43661972])
        assert np.allclose(std, [255.705035971, 257.943005181, 196.591549296])

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
        for key, entry in list(demodata._SURFACE.items()):
            assert "data" in entry
            assert "unit" in entry
            assert isinstance(entry["unit"], basestring)
            assert isinstance(entry["data"], np.ndarray)

    def test_PROFILES(self):
        assert isinstance(demodata._PROFILES, dict)
        for key, entry in list(demodata._PROFILES.items()):
            assert "data" in entry
            assert "unit" in entry
            assert isinstance(entry["unit"], basestring)
            assert isinstance(entry["data"], np.ndarray)
