# -*- coding: utf-8 -*-
"""

    mslib.utils._tests.test_coordinate
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mslib.utils.coordinate

    This file is part of mss.

    :copyright: Copyright 2016-2017 Reimar Bauer
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
import logging
import datetime

import numpy as np
import pytest

import mslib.utils.coordinate as coordinate

LOGGER = logging.getLogger(__name__)


class TestGetDistance(object):
    """
    tests for distance based calculations
    """
    # we don't test the utils method here, may be that method should me refactored off

    def test_get_distance(self):
        coordinates_distance = [(50.355136, 7.566077, 50.353968, 4.577915, 212),
                                (-5.135943, -42.792442, 4.606085, 120.028077, 18130)]
        for lat0, lon0, lat1, lon1, distance in coordinates_distance:
            assert int(coordinate.get_distance(lat0, lon0, lat1, lon1)) == distance

    def test_find_location(self):
        assert coordinate.find_location(50.92, 6.36) == ([50.92, 6.36], 'Juelich')
        assert coordinate.find_location(50.9200002, 6.36) == ([50.92, 6.36], 'Juelich')


class TestProjections(object):
    def test_get_projection_params(self):
        assert coordinate.get_projection_params("epsg:4839") == {'basemap': {'epsg': '4839'}, 'bbox': 'meter(10.5,51)'}
        with pytest.raises(ValueError):
            coordinate.get_projection_params('auto2:42005')
        with pytest.raises(ValueError):
            coordinate.get_projection_params('auto:42001')
        with pytest.raises(ValueError):
            coordinate.get_projection_params('crs:84')


class TestAngles(object):
    """
    tests about angles
    """

    def test_normalize_angle(self):
        assert coordinate.fix_angle(0) == 0
        assert coordinate.fix_angle(180) == 180
        assert coordinate.fix_angle(270) == 270
        assert coordinate.fix_angle(-90) == 270
        assert coordinate.fix_angle(-180) == 180
        assert coordinate.fix_angle(-181) == 179
        assert coordinate.fix_angle(420) == 60

    def test_rotate_point(self):
        assert coordinate.rotate_point([0, 0], 0) == (0.0, 0.0)
        assert coordinate.rotate_point([0, 0], 180) == (0.0, 0.0)
        assert coordinate.rotate_point([1, 0], 0) == (1.0, 0.0)
        assert coordinate.rotate_point([100, 90], 90) == (-90, 100)


class TestLatLonPoints(object):
    def test_linear(self):
        ref_lats = [0, 10]
        ref_lons = [0, 0]

        lats, lons = coordinate.latlon_points(ref_lats[0], ref_lons[0], ref_lats[1], ref_lons[1],
                                              numpoints=2, connection="linear")
        assert len(lats) == len(ref_lats)
        assert all(lats == ref_lats)
        assert len(lons) == len(ref_lons)
        assert all(lons == ref_lons)

        lats, lons = coordinate.latlon_points(ref_lats[0], ref_lons[0], ref_lats[1], ref_lons[1],
                                              numpoints=3, connection="linear")
        assert len(lats) == 3
        assert len(lons) == 3
        assert all(lats == [0, 5, 10])

        ref_lats = [0, 0]
        ref_lons = [0, 10]
        lats, lons = coordinate.latlon_points(ref_lats[0], ref_lons[0], ref_lats[1], ref_lons[1],
                                              numpoints=3, connection="linear")
        assert len(lats) == 3
        assert len(lons) == 3
        assert all(lons == [0, 5, 10])

        lats, lons = coordinate.latlon_points(ref_lats[0], ref_lons[0], ref_lats[1], ref_lons[1],
                                              numpoints=3, connection="linear")
        assert len(lats) == 3
        assert len(lons) == 3
        assert all(lons == [0, 5, 10])

    def test_greatcircle(self):
        ref_lats = [0, 10]
        ref_lons = [0, 0]

        lats, lons = coordinate.latlon_points(ref_lats[0], ref_lons[0], ref_lats[1], ref_lons[1],
                                              numpoints=2, connection="greatcircle")
        assert len(lats) == len(ref_lats)
        assert lats == ref_lats
        assert len(lons) == len(ref_lons)
        assert lons == ref_lons

        lats, lons = coordinate.latlon_points(ref_lats[0], ref_lons[0], ref_lats[1], ref_lons[1],
                                              numpoints=3, connection="linear")
        assert len(lats) == 3
        assert len(lons) == 3
        assert all(np.asarray(lats) == [0, 5, 10])

        ref_lats = [0, 0]
        ref_lons = [0, 10]
        lats, lons = coordinate.latlon_points(ref_lats[0], ref_lons[0], ref_lats[1], ref_lons[1],
                                              numpoints=3, connection="linear")
        assert len(lats) == 3
        assert len(lons) == 3
        assert all(np.asarray(lons) == [0, 5, 10])


def test_pathpoints():
    lats = [0, 10]
    lons = [0, 10]
    times = [datetime.datetime(2012, 7, 1, 10, 30),
             datetime.datetime(2012, 7, 1, 10, 40)]
    ref = [lats, lons, times]
    result = coordinate.path_points(lats, lons, 100, times=times, connection="linear")
    assert all(len(_x) == 100 for _x in result)
    for i in range(3):
        assert pytest.approx(result[i][0]) == ref[i][0]
        assert pytest.approx(result[i][-1]) == ref[i][-1]

    result = coordinate.path_points(lats, lons, 100, times=times, connection="greatcircle")
    assert all(len(_x) == 100 for _x in result)
    for i in range(3):
        assert pytest.approx(result[i][0]) == ref[i][0]
        assert pytest.approx(result[i][-1]) == ref[i][-1]

    result = coordinate.path_points(lats, lons, 200, times=times, connection="linear")
    assert all(len(_x) == 200 for _x in result)
    for i in range(3):
        assert pytest.approx(result[i][0]) == ref[i][0]
        assert pytest.approx(result[i][-1]) == ref[i][-1]

    result = coordinate.path_points(lats, lons, 200, times=times, connection="greatcircle")
    assert all(len(_x) == 200 for _x in result)
    for i in range(3):
        assert pytest.approx(result[i][0]) == ref[i][0]
        assert pytest.approx(result[i][-1]) == ref[i][-1]

    lats = [0, 10, -20]
    lons = [0, 10, 20]
    times = [datetime.datetime(2012, 7, 1, 10, 30),
             datetime.datetime(2012, 7, 1, 10, 40),
             datetime.datetime(2012, 7, 1, 10, 50)]
    ref = [lats, lons, times]

    result = coordinate.path_points(lats, lons, 100, times=times, connection="linear")
    assert all([len(_x) == 100 for _x in result])
    for i in range(3):
        assert pytest.approx(result[i][0]) == ref[i][0]
        assert pytest.approx(result[i][-1]) == ref[i][-1]

    result = coordinate.path_points(lats, lons, 100, times=times, connection="greatcircle")
    assert all(len(_x) == 100 for _x in result)
    for i in range(3):
        assert pytest.approx(result[i][0]) == ref[i][0]
        assert pytest.approx(result[i][-1]) == ref[i][-1]
