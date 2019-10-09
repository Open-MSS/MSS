# -*- coding: utf-8 -*-
"""

    mslib.mswms._tests.test_dataaccess
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mswms.dataaccess

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2017 Reimar Bauer
    :copyright: Copyright 2016-2019 by the mss team, see AUTHORS.
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

import mock

from mslib.mswms.dataaccess import DefaultDataAccess, CachedDataAccess
from mslib._tests.constants import DATA_DIR


class Test_DefaultDataAccess(object):
    def setup(self):
        self.dut = DefaultDataAccess(DATA_DIR, "EUR_LL015")
        self.dut.setup()

    def test_get_filename(self):
        filename = self.dut.get_filename("air_pressure", "ml",
                                         datetime(2012, 10, 17, 12, 0),
                                         datetime(2012, 10, 17, 18, 0))
        assert filename == "20121017_12_ecmwf_forecast.P_derived.EUR_LL015.036.ml.nc"

        filename = self.dut.get_filename("air_pressure", "ml",
                                         datetime(2012, 10, 17, 12, 0),
                                         datetime(2012, 10, 17, 18, 0),
                                         fullpath=True)
        assert filename == os.path.join(DATA_DIR, filename)

    def test_get_datapath(self):
        assert self.dut.get_datapath() == DATA_DIR

    def test_get_all_datafiles(self):
        all_files = self.dut.get_all_datafiles()
        assert sorted(all_files) == sorted(os.listdir(DATA_DIR))

    def test_get_init_times(self):
        all_init_times = self.dut.get_init_times()
        assert all_init_times == [datetime(2012, 10, 17, 12, 0)]

    def test_mfDatasetArgs(self):
        mfDatasetArgs = self.dut.mfDatasetArgs()
        assert mfDatasetArgs == {'skip_dim_check': []}
        mfDatasetArgs2 = DefaultDataAccess(DATA_DIR, "EUR_LL015", skip_dim_check=["time1"]).mfDatasetArgs()
        assert mfDatasetArgs2 == {'skip_dim_check': ['time1']}

    def test_get_valid_times(self):
        valid_times = self.dut.get_valid_times("air_pressure", "ml", datetime(2012, 10, 17, 12, 0))
        assert valid_times == [datetime(2012, 10, 17, 12, 0),
                               datetime(2012, 10, 17, 18, 0),
                               datetime(2012, 10, 18, 0, 0),
                               datetime(2012, 10, 18, 6, 0),
                               datetime(2012, 10, 18, 12, 0),
                               datetime(2012, 10, 18, 18, 0),
                               datetime(2012, 10, 19, 0, 0)]

    def test_get_all_valid_times(self):
        all_valid_times = self.dut.get_all_valid_times("air_pressure", "ml")
        assert sorted(all_valid_times) == \
            sorted([datetime(2012, 10, 18, 18, 0),
                    datetime(2012, 10, 18, 0, 0),
                    datetime(2012, 10, 17, 12, 0),
                    datetime(2012, 10, 18, 6, 0),
                    datetime(2012, 10, 17, 18, 0),
                    datetime(2012, 10, 18, 12, 0),
                    datetime(2012, 10, 19, 0, 0)])


class Test_CachedDataAccess(Test_DefaultDataAccess):
    """
    Reuse default testcases and add some more
    """

    def setup(self):
        self.dut = CachedDataAccess(DATA_DIR, "EUR_LL015")
        self.dut.setup()

    def test_cache_full(self):
        self.dut._parse_file = mock.MagicMock()
        self.dut._add_to_filetree = mock.MagicMock()
        self.dut.setup()
        assert self.dut._parse_file.call_count == 0

    def test_cache_modified(self):
        self.dut._parse_file = mock.MagicMock()
        self.dut._add_to_filetree = mock.MagicMock()
        n = len(self.dut.get_all_datafiles())
        fn = list(self.dut._file_cache.keys())[0]
        self.dut._file_cache[fn] = (
            self.dut._file_cache[fn][0] + 1,
            self.dut._file_cache[fn][1])
        self.dut.setup()
        self.dut._parse_file.assert_called_once_with(fn)
        assert self.dut._add_to_filetree.call_count == n

    def test_cache_incomplete(self):
        self.dut._parse_file = mock.MagicMock()
        self.dut._add_to_filetree = mock.MagicMock()
        n = len(self.dut.get_all_datafiles())
        fn = list(self.dut._file_cache.keys())[0]
        del self.dut._file_cache[fn]
        self.dut.setup()
        assert self.dut._parse_file.call_count == 1
        assert self.dut._add_to_filetree.call_count == n

    def test_cache_too_large(self):
        self.dut._file_cache["nothere"] = [0, {}]
        self.dut.setup()
        assert "nothere" not in self.dut._file_cache


class Test_DefaultDataAccessNoInit(object):
    def setup(self):
        self.dut = DefaultDataAccess(DATA_DIR, "EUR_LL015", uses_init_time=False)
        self.dut.setup()

    def test_get_init_times(self):
        all_init_times = self.dut.get_init_times()
        assert all_init_times == [None]
