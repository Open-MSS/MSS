# -*- coding: utf-8 -*-
"""

    tests._test_mswms.test_dataaccess
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mswms.dataaccess

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2017 Reimar Bauer
    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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
import shutil
from datetime import datetime

import mock
import pytest

from mslib.mswms.dataaccess import DefaultDataAccess, CachedDataAccess, WatchModificationDataAccess
from tests.constants import MSWMS_DATA_DIR

ML_FILE = "20121017_12_ecmwf_forecast.P_derived.EUR_LL015.036.ml.nc"
SFC_FILE = "20121017_12_ecmwf_forecast.SEA.EUR_LL015.036.sfc.nc"
INIT_TIME = datetime(2012, 10, 17, 12, 0)
VALID_TIME = datetime(2012, 10, 17, 18, 0)


def _copy_datafile(filename, target_dir):
    """
    Copy one of the generated test data files into an isolated data directory.
    """
    shutil.copy(os.path.join(MSWMS_DATA_DIR, filename), os.path.join(target_dir, filename))


class Test_DefaultDataAccess:
    def setup_method(self):
        self.dut = DefaultDataAccess(MSWMS_DATA_DIR, "EUR_LL015")
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
        assert filename == os.path.join(MSWMS_DATA_DIR, filename)

    def test_get_datapath(self):
        assert self.dut.get_datapath() == MSWMS_DATA_DIR

    def test_get_all_datafiles(self):
        all_files = self.dut.get_all_datafiles()
        assert sorted(all_files) == sorted(os.listdir(MSWMS_DATA_DIR))

    def test_get_init_times(self):
        all_init_times = self.dut.get_init_times()
        assert all_init_times == [datetime(2012, 10, 17, 12, 0)]

    def test_mfDatasetArgs(self):
        mfDatasetArgs = self.dut.mfDatasetArgs()
        assert mfDatasetArgs == {'skip_dim_check': []}
        mfDatasetArgs2 = DefaultDataAccess(MSWMS_DATA_DIR, "EUR_LL015", skip_dim_check=["time1"]).mfDatasetArgs()
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

    def setup_method(self):
        self.dut = CachedDataAccess(MSWMS_DATA_DIR, "EUR_LL015")
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


class Test_DefaultDataAccessReload:
    """
    Tests the reload mechanism of DefaultDataAccess, i.e. the rescan of the data
    directory that is triggered by _determine_filename() when a requested entry
    is missing from the file tree.
    """

    @pytest.fixture(autouse=True)
    def _dut(self, tmp_path):
        self.data_dir = str(tmp_path)
        _copy_datafile(ML_FILE, self.data_dir)
        self.dut = DefaultDataAccess(self.data_dir, "EUR_LL015")
        self.dut.setup()

    def test_no_reload_for_known_data(self):
        """A known variable is served from the file tree without rescanning the disk."""
        with mock.patch.object(self.dut, "setup", wraps=self.dut.setup) as setup:
            assert self.dut.get_filename("air_pressure", "ml", INIT_TIME, VALID_TIME) == ML_FILE
            setup.assert_not_called()

    def test_reload_detects_new_file(self):
        """An unknown variable triggers a rescan, which picks up a newly arrived file."""
        with pytest.raises(ValueError):
            self.dut.get_filename("solar_elevation_angle", "sfc", INIT_TIME, VALID_TIME)

        _copy_datafile(SFC_FILE, self.data_dir)

        with mock.patch.object(self.dut, "setup", wraps=self.dut.setup) as setup:
            filename = self.dut.get_filename("solar_elevation_angle", "sfc", INIT_TIME, VALID_TIME)
            setup.assert_called_once_with()
        assert filename == SFC_FILE
        assert sorted(self.dut.get_all_datafiles()) == sorted([ML_FILE, SFC_FILE])

    def test_removed_file_is_not_noticed_without_a_miss(self):
        """
        A removed file is still served from the file tree, because a successful
        lookup does not trigger a rescan. Only a rescan drops it from the cache.
        """
        assert self.dut.get_filename("air_pressure", "ml", INIT_TIME, VALID_TIME) == ML_FILE
        os.remove(os.path.join(self.data_dir, ML_FILE))

        with mock.patch.object(self.dut, "setup", wraps=self.dut.setup) as setup:
            assert self.dut.get_filename("air_pressure", "ml", INIT_TIME, VALID_TIME) == ML_FILE
            setup.assert_not_called()

        # a rescan, e.g. triggered by a miss for another variable, cleans up
        with pytest.raises(ValueError):
            self.dut.get_filename("solar_elevation_angle", "sfc", INIT_TIME, VALID_TIME)
        assert self.dut.get_all_datafiles() == []
        assert ML_FILE not in self.dut._file_cache
        with pytest.raises(ValueError):
            self.dut.get_filename("air_pressure", "ml", INIT_TIME, VALID_TIME)

    def test_reload_happens_only_once(self):
        """A variable that stays unavailable rescans exactly once, then fails."""
        with mock.patch.object(self.dut, "setup", wraps=self.dut.setup) as setup:
            with pytest.raises(ValueError, match="not available"):
                self.dut.get_filename("not_a_standard_name", "ml", INIT_TIME, VALID_TIME)
            assert setup.call_count == 1

    def test_no_reload_when_disabled(self):
        """With reload=False a new file on disk stays invisible and no rescan happens."""
        _copy_datafile(SFC_FILE, self.data_dir)

        with mock.patch.object(self.dut, "setup", wraps=self.dut.setup) as setup:
            with pytest.raises(ValueError):
                self.dut._determine_filename(
                    "solar_elevation_angle", "sfc", INIT_TIME, VALID_TIME, reload=False)
            setup.assert_not_called()

    def test_have_data_does_not_reload(self):
        """have_data() answers from the known file tree and never rescans the disk."""
        _copy_datafile(SFC_FILE, self.data_dir)

        with mock.patch.object(self.dut, "setup", wraps=self.dut.setup) as setup:
            assert self.dut.have_data("air_pressure", "ml", INIT_TIME, VALID_TIME) is True
            assert self.dut.have_data("solar_elevation_angle", "sfc", INIT_TIME, VALID_TIME) is False
            setup.assert_not_called()

        # ... while get_filename() does reload and therefore finds the new file
        assert self.dut.get_filename("solar_elevation_angle", "sfc", INIT_TIME, VALID_TIME) == SFC_FILE

    def test_reload_requires_setup(self):
        """Reloading is not attempted before setup() has built an initial file tree."""
        dut = DefaultDataAccess(self.data_dir, "EUR_LL015")
        with pytest.raises(AssertionError, match="Forgot to call setup"):
            dut.get_filename("air_pressure", "ml", INIT_TIME, VALID_TIME)

    def test_is_reload_required_always_false(self):
        """DefaultDataAccess ignores modifications of already read files."""
        path = os.path.join(self.data_dir, ML_FILE)
        os.utime(path, (0, 0))
        assert self.dut.is_reload_required([path]) is False


class Test_WatchModificationDataAccessReload:
    """
    Tests the reload mechanism of WatchModificationDataAccess, which additionally
    watches the modification times of the files it has already read.
    """

    @pytest.fixture(autouse=True)
    def _dut(self, tmp_path):
        self.data_dir = str(tmp_path)
        _copy_datafile(ML_FILE, self.data_dir)
        self.dut = WatchModificationDataAccess(self.data_dir, "EUR_LL015")
        self.dut.setup()

    def _touch(self, filename):
        """Set a distinct modification time and return it."""
        path = os.path.join(self.data_dir, filename)
        mtime = os.path.getmtime(path) + 10
        os.utime(path, (mtime, mtime))
        return mtime

    def test_no_reload_for_unmodified_file(self):
        with mock.patch.object(self.dut, "setup", wraps=self.dut.setup) as setup:
            assert self.dut.get_filename("air_pressure", "ml", INIT_TIME, VALID_TIME) == ML_FILE
            setup.assert_not_called()

    def test_modified_file_triggers_reload(self):
        """A file modified after the last read is re-read on the next request."""
        mtime = self._touch(ML_FILE)

        with mock.patch.object(self.dut, "setup", wraps=self.dut.setup) as setup:
            assert self.dut.get_filename("air_pressure", "ml", INIT_TIME, VALID_TIME) == ML_FILE
            setup.assert_called_once_with()
        assert self.dut._file_cache[ML_FILE][0] == mtime

    def test_new_file_triggers_reload(self):
        _copy_datafile(SFC_FILE, self.data_dir)
        assert self.dut.get_filename("solar_elevation_angle", "sfc", INIT_TIME, VALID_TIME) == SFC_FILE

    def test_removed_file_triggers_reload(self):
        """A vanished file leads to a rescan and afterwards to a ValueError."""
        os.remove(os.path.join(self.data_dir, ML_FILE))

        with mock.patch.object(self.dut, "setup", wraps=self.dut.setup) as setup:
            with pytest.raises(ValueError, match="not available"):
                self.dut.get_filename("air_pressure", "ml", INIT_TIME, VALID_TIME)
            assert setup.call_count == 1

    def test_no_reload_when_disabled(self):
        """With reload=False a modified file is neither rescanned nor reported."""
        self._touch(ML_FILE)

        with mock.patch.object(self.dut, "setup", wraps=self.dut.setup) as setup:
            with pytest.raises(ValueError):
                self.dut._determine_filename("air_pressure", "ml", INIT_TIME, VALID_TIME, reload=False)
            setup.assert_not_called()

    def test_is_reload_required_unmodified(self):
        with mock.patch.object(self.dut, "setup", wraps=self.dut.setup) as setup:
            assert self.dut.is_reload_required([os.path.join(self.data_dir, ML_FILE)]) is False
            setup.assert_not_called()

    def test_is_reload_required_modified(self):
        """A modified file reports a reload once, the rescan makes the next check quiet."""
        mtime = self._touch(ML_FILE)
        fullpath = os.path.join(self.data_dir, ML_FILE)

        with mock.patch.object(self.dut, "setup", wraps=self.dut.setup) as setup:
            assert self.dut.is_reload_required([fullpath]) is True
            setup.assert_called_once_with()
        assert self.dut._file_cache[ML_FILE][0] == mtime
        assert self.dut.is_reload_required([fullpath]) is False

    def test_is_reload_required_removed(self):
        os.remove(os.path.join(self.data_dir, ML_FILE))
        assert self.dut.is_reload_required([os.path.join(self.data_dir, ML_FILE)]) is True
        assert self.dut.get_all_datafiles() == []

    def test_is_reload_required_unknown_file(self):
        assert self.dut.is_reload_required([os.path.join(self.data_dir, "not_a_datafile.nc")]) is True


class Test_DefaultDataAccessNoInit:
    def setup_method(self):
        self.dut = DefaultDataAccess(MSWMS_DATA_DIR, "EUR_LL015", uses_init_time=False)
        self.dut.setup()

    def test_get_init_times(self):
        all_init_times = self.dut.get_init_times()
        assert all_init_times == [None]
