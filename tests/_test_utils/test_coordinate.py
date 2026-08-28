# -*- coding: utf-8 -*-
"""
    tests._test_utils.test_coordinate
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    This module provides pytest functions to test mslib.utils.coordinate.
    This file is part of MSS.
    :copyright: Copyright 2016-2017 Reimar Bauer
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
import logging
import datetime
import numpy as np
import pytest
import mslib.utils.coordinate as coordinate
from mslib.utils.find_location import find_location
from mslib.utils.get_projection_params import get_projection_params

LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize("lat0, lon0, lat1, lon1, expected", [
    (50.355136, 7.566077, 50.353968, 4.577915, 212),
    (-5.135943, -42.792442, 4.606085, 120.028077, 18130)
])
def test_get_distance(lat0, lon0, lat1, lon1, expected):
    """
    Test distance-based calculations.
    """
    assert int(coordinate.get_distance(lat0, lon0, lat1, lon1)) == expected


@pytest.mark.parametrize("lat, lon, expected", [
    (50.92, 6.36, ([50.92, 6.36], 'Juelich')),
    (50.9200002, 6.36, ([50.92, 6.36], 'Juelich'))
])
def test_find_location(lat, lon, expected):
    """
    Test location finding functionality.
    """
    assert find_location(lat, lon) == expected


@pytest.mark.parametrize("projection, expected", [
    ("epsg:4839", {'basemap': {'epsg': '4839'}, 'bbox': 'meter(10.5,51)'}),
    ('auto2:42005', ValueError),
    ('auto:42001', ValueError),
    ('crs:83', ValueError)
])
def test_get_projection_params(projection, expected):
    """
    Test projection parameter retrieval.
    """
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            get_projection_params(projection)
    else:
        assert get_projection_params(projection) == expected


@pytest.mark.parametrize("angle, expected", [
    (0, 0),
    (180, 180),
    (270, 270),
    (-90, 270),
    (-180, 180),
    (-181, 179),
    (420, 60)
])
def test_normalize_angle(angle, expected):
    """
    Test angle normalization.
    """
    assert coordinate.fix_angle(angle) == expected


@pytest.mark.parametrize("point, angle, rotated_point", [
    ([0, 0], 0, (0.0, 0.0)),
    ([0, 0], 180, (0.0, 0.0)),
    ([1, 0], 0, (1.0, 0.0)),
    ([100, 90], 90, (-90, 100)),
    ([0.0, 2.5], 45, (-1.767767, 1.767767))
])
def test_rotate_point(point, angle, rotated_point):
    """
    Test rotating points around the origin.
    """
    result = coordinate.rotate_point(point, angle)
    assert result == pytest.approx(rotated_point, rel=1e-6, abs=1e-6)


@pytest.mark.parametrize("ref_lats, ref_lons, numpoints, expected_lats, expected_lons, connection", [
    ([0, 10], [0, 0], 2, [0, 10], [0, 0], "linear"),
    ([0, 10], [0, 0], 3, [0, 5, 10], [0, 0, 0], "linear"),
    ([0, 0], [0, 10], 3, [0, 0, 0], [0, 5, 10], "linear"),
    ([0, 10], [0, 0], 2, [0, 10], [0, 0], "greatcircle"),
    ([0, 10], [0, 0], 3, [0, 5, 10], [0, 0, 0], "greatcircle"),
    ([0, 0], [0, 10], 3, [0, 0, 0], [0, 5, 10], "greatcircle")
])
def test_latlon_points(ref_lats, ref_lons, numpoints, expected_lats, expected_lons, connection):
    """
    Test path generation for lat/lon points.
    """
    lats, lons = coordinate.latlon_points(
        ref_lats[0], ref_lons[0], ref_lats[1], ref_lons[1],
        numpoints=numpoints, connection=connection
    )
    assert len(lats) == len(expected_lats)
    assert all(np.asarray(lats) == expected_lats)
    assert len(lons) == len(expected_lons)
    assert all(np.asarray(lons) == expected_lons)


def test_pathpoints():
    """
    Test path point generation.
    """
    # Test case 1: Two points
    lats = [0, 10]
    lons = [0, 10]
    times = [datetime.datetime(2012, 7, 1, 10, 30), datetime.datetime(2012, 7, 1, 10, 40)]
    ref = [lats, lons, times]

    for numpoints, connection in [(100, "linear"), (100, "greatcircle"), (200, "linear"), (200, "greatcircle")]:
        result = coordinate.path_points(lats, lons, numpoints, times=times, connection=connection)
        assert all(len(_x) == numpoints for _x in result)
        for i in range(3):
            assert pytest.approx(result[i][0]) == ref[i][0]
            assert pytest.approx(result[i][-1]) == ref[i][-1]

    # Test case 2: Three points
    lats = [0, 10, -20]
    lons = [0, 10, 20]
    times = [datetime.datetime(2012, 7, 1, 10, 30), datetime.datetime(2012, 7, 1, 10, 40),
             datetime.datetime(2012, 7, 1, 10, 50)]
    ref = [lats, lons, times]

    for numpoints, connection in [(100, "linear"), (100, "greatcircle")]:
        result = coordinate.path_points(lats, lons, numpoints, times=times, connection=connection)
        assert all(len(_x) == numpoints for _x in result)
        for i in range(3):
            assert pytest.approx(result[i][0]) == ref[i][0]
            assert pytest.approx(result[i][-1]) == ref[i][-1]
