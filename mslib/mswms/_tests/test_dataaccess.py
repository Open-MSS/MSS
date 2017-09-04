# -*- coding: utf-8 -*-
"""

    mslib.mswms._tests.test_dataaccess
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mswms.dataaccess

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
from datetime import datetime
from mslib.mswms.dataaccess import DefaultDataAccess
from mslib._tests.utils import DATA_DIR


class Test_DefaultDataAccess(object):
    def setup(self):
        self.dut = DefaultDataAccess(DATA_DIR, "EUR_LL015")
        self.dut.setup()

    def test_get_filename(self):
        filename = self.dut.get_filename("air_pressure", "ml",
                                         datetime(2012, 10, 17, 12, 0),
                                         datetime(2012, 10, 17, 15, 0))
        assert filename == "20121017_12_ecmwf_forecast.P_derived.EUR_LL015.036.ml.nc"

        filename = self.dut.get_filename("air_pressure", "ml",
                                         datetime(2012, 10, 17, 12, 0),
                                         datetime(2012, 10, 17, 15, 0),
                                         fullpath=True)
        assert filename == os.path.join(DATA_DIR, filename)

    def test_get_datapath(self):
        assert self.dut.get_datapath() == DATA_DIR

    def test_get_all_datafiles(self):
        all_files = self.dut.get_all_datafiles()
        assert all_files == os.listdir(DATA_DIR)

    def test_get_init_times(self):
        all_init_times = self.dut.get_init_times()
        assert all_init_times == [datetime(2012, 10, 17, 12, 0)]

    def test_mfDatasetArgs(self):
        mfDatasetArgs = self.dut.mfDatasetArgs()
        assert mfDatasetArgs == {'skipDimCheck': ['lon']}

    def test_get_valid_times(self):
        valid_times = self.dut.get_valid_times("air_pressure", "ml", datetime(2012, 10, 17, 12, 0))
        assert valid_times == [datetime(2012, 10, 17, 12, 0),
                               datetime(2012, 10, 17, 15, 0),
                               datetime(2012, 10, 17, 18, 0),
                               datetime(2012, 10, 17, 21, 0),
                               datetime(2012, 10, 18, 0, 0),
                               datetime(2012, 10, 18, 3, 0),
                               datetime(2012, 10, 18, 6, 0),
                               datetime(2012, 10, 18, 9, 0),
                               datetime(2012, 10, 18, 12, 0),
                               datetime(2012, 10, 18, 15, 0),
                               datetime(2012, 10, 18, 18, 0),
                               datetime(2012, 10, 18, 21, 0),
                               datetime(2012, 10, 19, 0, 0)]

    def test_get_all_valid_times(self):
        all_valid_times = self.dut.get_all_valid_times("air_pressure", "ml")
        assert sorted(all_valid_times) == \
            sorted([datetime(2012, 10, 17, 15, 0),
                    datetime(2012, 10, 17, 21, 0),
                    datetime(2012, 10, 18, 21, 0),
                    datetime(2012, 10, 18, 18, 0),
                    datetime(2012, 10, 18, 3, 0),
                    datetime(2012, 10, 18, 15, 0),
                    datetime(2012, 10, 18, 0, 0),
                    datetime(2012, 10, 17, 12, 0),
                    datetime(2012, 10, 18, 6, 0),
                    datetime(2012, 10, 17, 18, 0),
                    datetime(2012, 10, 18, 12, 0),
                    datetime(2012, 10, 18, 9, 0),
                    datetime(2012, 10, 19, 0, 0)])
