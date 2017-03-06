# -*- coding: utf-8 -*-
"""

    mslib._tests.test_netCDF4tools
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mslib.netCDF4tools

    This file is part of mss.

    :copyright: Copyright 2016-2017 Reimar Bauer
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
import pytest
import datetime
from netCDF4 import Dataset
from conftest import DATA_DIR
from mslib.netCDF4tools import (identify_variable, identify_CF_coordhybrid, identify_CF_hybrid, hybrid_orientation,
                                identify_CF_isopressure, identify_CF_isopotvort, identify_CF_isoaltitude,
                                identify_CF_isopottemp, identify_CF_time, identify_CF_ensemble, num2date,
                                get_latlon_data
                                )

DATA_FILE_ML = os.path.join(DATA_DIR, "20121017_12_ecmwf_forecast.CC.EUR_LL015.036.ml.nc")
DATA_FILE_PL = os.path.join(DATA_DIR, "20121017_12_ecmwf_forecast.PRESSURE_LEVELS.EUR_LL015.036.pl.nc")


class Test_netCDF4tools():
    def setup(self):
        self.ncfile_ml = Dataset(DATA_FILE_ML, 'r')
        self.ncfile_pl = Dataset(DATA_FILE_PL, 'r')

    def teardown(self):
        self.ncfile_ml.close()
        self.ncfile_pl.close()

    def test_identify_variable(self):
        checklist = [('time', u'time'),
                     ('latitude', u'lat'),
                     ('longitude', u'lon'),
                     ('atmosphere_pressure_coordinate', 'hyam'),
                     ('atmosphere_hybrid_height_coordinate', 'hybm'),
                     ('cloud_area_fraction_in_atmosphere_layer', 'Fraction_of_cloud_cover_hybrid')]
        for standard_name, short_name in checklist:
            variable = identify_variable(self.ncfile_ml, standard_name)
            assert variable[0] == short_name

    def test_identify_CF_coordhybrid(self):
        lat_name, lat_var, lon_name, lon_var, hybrid_name, hybrid_var = identify_CF_coordhybrid(self.ncfile_ml)
        assert (lat_name, lon_name, hybrid_name) == (u'lat', u'lon', 'hybrid')
        assert lat_var.size == 41
        assert lon_var.size == 51

    def test_hybrid_orientation(self):
        lat_name, lat_var, lon_name, lon_var, hybrid_name, hybrid_var = identify_CF_coordhybrid(self.ncfile_ml)
        assert hybrid_orientation(hybrid_var) == 1

    def test_identify_CF_hybrid(self):
        hybrid_name, hybrid_var, orientation = identify_CF_hybrid(self.ncfile_ml)
        assert hybrid_name == "hybrid"
        assert hybrid_var.size == 72
        assert orientation == 1

    def test_identify_CF_isopressure(self):
        hybrid_name, hybrid_var, orientation = identify_CF_isopressure(self.ncfile_ml)
        assert hybrid_name == "hyam"
        assert hybrid_var.size == 72
        assert orientation == -1

    def test_identify_CF_isopotvort(self):
        pytest.skip("no demodata available yet")

    def test_identify_CF_isoaltitude(self):
        pytest.skip("no demodata available yet")

    def test_identify_CF_isopottemp(self):
        pytest.skip("no demodata available yet")

    def test_identify_CF_time(self):
        time_name, time_var = identify_CF_time(self.ncfile_ml)
        assert time_name == "time"
        assert time_var.size == 13

    def test_identify_CF_ensemble(self):
        pytest.skip("no demodata available yet")

    def test_get_latlon_data(self):
        lat_data, lon_data, lat_order = get_latlon_data(self.ncfile_pl)
        assert lat_data.size == 41
        assert lon_data.size == 51
        assert lat_order == -1

    def test_num2date(self):
        date = num2date(0, "hours since 2012-10-17T12:00:00.000Z", calendar='standard')
        assert date == datetime.datetime(2012, 10, 17, 12, 0)
