# -*- coding: utf-8 -*-
"""

    mslib._tests.test_mss_util
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mslib.mss_util

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

import pytest
import datetime
from mslib import mss_util


class TestConfigLoader(object):
    """
    tests config file for client
    """

    def test_default_config(self):
        try:
            data = mss_util.config_loader()
        except IOError:
            pytest.skip("no config file found")
        assert isinstance(data, dict)
        assert data["num_labels"] == 10
        assert data["num_interpolation_points"] == 201

    def test_default_config_dataset(self):
        try:
            data = mss_util.config_loader(dataset="num_labels")
        except IOError:
            pytest.skip("no config file found")
        assert data == 10
        # defined value and not a default one
        data = mss_util.config_loader(dataset="num_labels", default=5)
        assert data == 10
        # default for non existing entry
        data = mss_util.config_loader(dataset="foobar", default=5)
        assert data == 5

    def test_default_config_wrong_file(self):
        # return default if no access to config file given
        data = mss_util.config_loader(config_file="foo.json", default={"foo": "123"})
        assert data == {"foo": "123"}


class TestGetDistance(object):
    """
    tests for distance based calculations
    """
    # we don't test the utils method here, may be that method should me refactored off
    def test_get_distance(self):
        coordinates_distance = [((50.355136, 7.566077), (50.353968, 4.577915), 212),
                                ((-5.135943, -42.792442), (4.606085, 120.028077), 18130)]
        for coord1, coord2, distance in coordinates_distance:
            assert int(mss_util.get_distance(coord1, coord2)) == distance


class TestTimes(object):
    """
    tests about times
    """
    def test_datetime_to_jsec(self):
        assert mss_util.datetime_to_jsec(datetime.datetime(2000, 2, 1, 0, 0, 0, 0)) == 2678400.0
        assert mss_util.datetime_to_jsec(datetime.datetime(2000, 1, 1, 0, 0, 0, 0)) == 0
        assert mss_util.datetime_to_jsec(datetime.datetime(1995, 1, 1, 0, 0, 0, 0)) == -157766400.0

    def test_jsec_to_datetime(self):
        assert mss_util.jsec_to_datetime(0) == datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
        assert mss_util.jsec_to_datetime(3600) == datetime.datetime(2000, 1, 1, 1, 0, 0, 0)
        assert mss_util.jsec_to_datetime(-157766400.0) == datetime.datetime(1995, 1, 1, 0, 0, 0, 0)

    def test_compute_hour_of_day(self):
        assert mss_util.compute_hour_of_day(0) == 0
        assert mss_util.compute_hour_of_day(86400) == 0
        assert mss_util.compute_hour_of_day(3600) == 1
        assert mss_util.compute_hour_of_day(82800) == 23


class TestAngles(object):
    """
    tests about angles
    """
    def test_normalize_angle(self):
        assert mss_util.fix_angle(0) == 0
        assert mss_util.fix_angle(180) == 180
        assert mss_util.fix_angle(270) == 270
        assert mss_util.fix_angle(-90) == 270
        assert mss_util.fix_angle(-180) == 180
        assert mss_util.fix_angle(-181) == 179

    def test_rotate_point(self):
        assert mss_util.rotate_point([0, 0], 0) == (0.0, 0.0)
        assert mss_util.rotate_point([0, 0], 180) == (0.0, 0.0)
        assert mss_util.rotate_point([1, 0], 0) == (1.0, 0.0)
        assert mss_util.rotate_point([100, 90], 90) == (-90, 100)


class TestConverter(object):
    def test_convert_pressure_to_altitude(self):
        assert mss_util.convertHPAToKM(1013.25) == 0
        assert int(mss_util.convertHPAToKM(25) * 1000) == 22415
