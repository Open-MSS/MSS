# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_circle_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests the geometry of msui.circle_dockwidget

    This file is part of MSS.

    :copyright: Copyright 2026 by the MSS team, see AUTHORS.
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
import numpy as np
import pytest
from pyproj import Geod

from mslib.msui.circle_dockwidget import circle_radius, create_circle

GEOD = Geod(ellps="WGS84")


def test_circle_radius():
    # 400 kt for 10 min = 123.47 km; a hexagon's perimeter is six radii.
    assert circle_radius(400, 10, 6) == pytest.approx(400 * 1.852 / 6 / 6)
    # Many vertices approach a circle.
    assert circle_radius(400, 10, 3600) == pytest.approx(400 * 1.852 / 6 / (2 * np.pi), rel=1e-6)


@pytest.mark.parametrize("lat, lon, heading, vertices", [
    (48.1, 10.27, 30., 6), (-60., 170., 250., 8), (0., 0., 0., 3)])
def test_create_circle(lat, lon, heading, vertices):
    radius = 50.
    points = create_circle(lat, lon, heading, radius, vertices)
    assert len(points) == vertices
    assert points[-1] == (lat, lon)
    lats, lons = np.array([(lat, lon)] + points).T

    # The first leg keeps the heading.
    azimuth, _, _ = GEOD.inv(lon, lat, lons[1], lats[1])
    assert ((azimuth - heading + 180 + 360. / vertices / 2) % 360) - 180 == pytest.approx(0, abs=0.5)

    # All legs have the same length, the chord of the circle.
    _, _, legs = GEOD.inv(lons[:-1], lats[:-1], lons[1:], lats[1:])
    chord = 2 * radius * 1000 * np.sin(np.pi / vertices)
    assert np.allclose(legs, chord, rtol=1e-3)

    # It is a left turn: every leg turns left relative to the arrival heading
    # of the previous one.
    departures, arrivals, _ = GEOD.inv(lons[:-1], lats[:-1], lons[1:], lats[1:])
    turns = (departures[1:] - (arrivals[:-1] + 180) + 180) % 360 - 180
    assert np.allclose(turns, -360. / vertices, atol=0.1)
