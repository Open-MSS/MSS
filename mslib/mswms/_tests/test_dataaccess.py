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
from mslib.mswms import dataaccess
from mslib.mswms.dataaccess import ECMWFDataAccess
from mslib._tests.utils import DATA_DIR, VALID_TIME_CACHE

# ToDo improve
dataaccess.valid_time_cache = VALID_TIME_CACHE


class Test_NWPDataAccess(object):
    def setup(self):
        self.ECMWFDataAccess = ECMWFDataAccess(DATA_DIR, "EUR_LL015")

    def test_get_filename(self):
        filename = self.ECMWFDataAccess.get_filename("air_pressure", "ml",
                                                     datetime(2012, 10, 17, 12, 0),
                                                     datetime(2012, 10, 17, 11, 0))
        assert filename == "20121017_12_ecmwf_forecast.P_derived.EUR_LL015.036.ml.nc"

        filename = self.ECMWFDataAccess.get_filename("air_pressure", "ml",
                                                     datetime(2012, 10, 17, 12, 0),
                                                     datetime(2012, 10, 17, 11, 0),
                                                     fullpath=True)
        assert filename == os.path.join(DATA_DIR, filename)

    def test_get_datapath(self):
        assert self.ECMWFDataAccess.get_datapath() == DATA_DIR

    def test_get_all_datafiles(self):
        all_files = self.ECMWFDataAccess.get_all_datafiles()
        assert all_files == os.listdir(DATA_DIR)

    def test_get_init_times(self):
        all_init_times = self.ECMWFDataAccess.get_init_times()
        assert all_init_times == [datetime(2012, 10, 17, 12, 0)]

    def test_md5_filename(self):
        filename = self.ECMWFDataAccess.get_filename("air_pressure", "ml",
                                                     datetime(2012, 10, 17, 12, 0),
                                                     datetime(2012, 10, 17, 11, 0),
                                                     fullpath=True)
        md5_filename = self.ECMWFDataAccess.md5_filename(filename)
        assert md5_filename.endswith("vt_cache_pickle")

    def test_check_valid_cache(self):
        filename = self.ECMWFDataAccess.get_filename("air_pressure", "ml",
                                                     datetime(2012, 10, 17, 12, 0),
                                                     datetime(2012, 10, 17, 11, 0),
                                                     fullpath=True)
        valid_cache = self.ECMWFDataAccess.check_valid_cache(filename)
        if not os.path.exists(filename):
            assert valid_cache is not None
        else:
            if valid_cache is not None:
                # follow up test can remove a cache file
                assert datetime(2012, 10, 17, 12, 0) in valid_cache

    def test_save_valid_cache(self):
        filename = self.ECMWFDataAccess.get_filename("air_pressure", "ml",
                                                     datetime(2012, 10, 17, 12, 0),
                                                     datetime(2012, 10, 17, 11, 0),
                                                     fullpath=True)
        valid_times = datetime(2012, 10, 17, 12, 0)
        self.ECMWFDataAccess.save_valid_cache(filename, valid_times)
        assert os.path.exists(VALID_TIME_CACHE)
        assert len(os.listdir(VALID_TIME_CACHE)) > 0

    def test_serviceCache(self):
        # set lowest possible number to delete all files
        dataaccess.valid_time_cache_max_age_seconds = 0
        self.ECMWFDataAccess.serviceCache()
        assert len(os.listdir(VALID_TIME_CACHE)) == 0

    def test_mfDatasetArgs(self):
        mfDatasetArgs = self.ECMWFDataAccess.mfDatasetArgs()
        assert mfDatasetArgs == {'skipDimCheck': ['lon']}

    def test_build_filetree(self):
        tree = self.ECMWFDataAccess.build_filetree()
        assert tree == {datetime(2012, 10, 17, 12, 0): {
            36: {'CIWC': '20121017_12_ecmwf_forecast.CIWC.EUR_LL015.036.ml.nc',
                 'PVU': '20121017_12_ecmwf_forecast.PVU.EUR_LL015.036.pv.nc',
                 'W': '20121017_12_ecmwf_forecast.W.EUR_LL015.036.ml.nc',
                 'THETA_LEVELS': '20121017_12_ecmwf_forecast.THETA_LEVELS.EUR_LL015.036.tl.nc',
                 'CC': '20121017_12_ecmwf_forecast.CC.EUR_LL015.036.ml.nc',
                 'PV_derived': '20121017_12_ecmwf_forecast.PV_derived.EUR_LL015.036.ml.nc',
                 'CLWC': '20121017_12_ecmwf_forecast.CLWC.EUR_LL015.036.ml.nc',
                 'Q': '20121017_12_ecmwf_forecast.Q.EUR_LL015.036.ml.nc',
                 'EMAC': '20121017_12_ecmwf_forecast.EMAC.EUR_LL015.036.ml.nc',
                 'P_derived': '20121017_12_ecmwf_forecast.P_derived.EUR_LL015.036.ml.nc',
                 'U': '20121017_12_ecmwf_forecast.U.EUR_LL015.036.ml.nc',
                 'T': '20121017_12_ecmwf_forecast.T.EUR_LL015.036.ml.nc',
                 'SEA': '20121017_12_ecmwf_forecast.SEA.EUR_LL015.036.sfc.nc',
                 'V': '20121017_12_ecmwf_forecast.V.EUR_LL015.036.ml.nc',
                 'ProbWCB_LAGRANTO_derived': '20121017_12_ecmwf_forecast.ProbWCB_LAGRANTO_derived.EUR_LL015.036.sfc.nc',
                 'SFC': '20121017_12_ecmwf_forecast.SFC.EUR_LL015.036.sfc.nc',
                 'PRESSURE_LEVELS': '20121017_12_ecmwf_forecast.PRESSURE_LEVELS.EUR_LL015.036.pl.nc'}}}

    def test_get_valid_times(self):
        valid_times = self.ECMWFDataAccess.get_valid_times("air_pressure", "ml", datetime(2012, 10, 17, 12, 0))
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
        all_valid_times = self.ECMWFDataAccess.get_all_valid_times("air_pressure", "ml")
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
