# -*- coding: utf-8 -*-
"""

    mslib._test.test_thermoblib
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for the thermolib module.

    This file is part of mss.

    :copyright: Copyright 2017 Marc Rautenhaus
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

import numpy as np
import pytest
from metpy.units import units

import mslib.thermolib as tl


def test_flightlevel2pressure2flightlevel():
    fs = np.arange(1, 71000, 1000.) / 30.48 * units.hft
    ps = tl.flightlevel2pressure(fs)
    fs_p = tl.pressure2flightlevel(ps).magnitude
    assert fs.magnitude == pytest.approx(fs_p)


def test_pressure2flightlevel2pressure():
    ps = np.arange(5, 105000, 1.)[::-1] * units.Pa
    fs = tl.pressure2flightlevel(ps)
    ps_p = tl.flightlevel2pressure(fs).magnitude
    assert ps.magnitude == pytest.approx(ps_p)


def test_flightlevel2pressure():
    assert tl.flightlevel2pressure(182.8850 * units.hft).magnitude == pytest.approx(50000)
    assert tl.flightlevel2pressure(530.8279 * units.hft).magnitude == pytest.approx(10000)
    assert tl.flightlevel2pressure(782.4335 * units.hft).magnitude == pytest.approx(3000)
    assert tl.flightlevel2pressure(1151.9583 * units.hft).magnitude == pytest.approx(550)
    assert tl.flightlevel2pressure(1626.8966 * units.hft).magnitude == pytest.approx(80)
    assert tl.flightlevel2pressure(1804.2727 * units.hft).magnitude == pytest.approx(40)
    with pytest.raises(ValueError):
        tl.flightlevel2pressure(72000 * units.m)


def test_pressure2flightlevel():
    assert tl.pressure2flightlevel(100000 * units.Pa).magnitude == pytest.approx(3.6378724)
    assert tl.pressure2flightlevel(75000 * units.Pa).magnitude == pytest.approx(80.91139)
    assert tl.pressure2flightlevel(50000 * units.Pa).magnitude == pytest.approx(182.8850)
    assert tl.pressure2flightlevel(10000 * units.Pa).magnitude == pytest.approx(530.8279)
    assert tl.pressure2flightlevel(3000 * units.Pa).magnitude == pytest.approx(782.4335)
    assert tl.pressure2flightlevel(550 * units.Pa).magnitude == pytest.approx(1151.9583)
    assert tl.pressure2flightlevel(80 * units.Pa).magnitude == pytest.approx(1626.8966)
    assert tl.pressure2flightlevel(40 * units.Pa).magnitude == pytest.approx(1804.2727)
    with pytest.raises(ValueError):
        tl.pressure2flightlevel(3.9 * units.Pa)


def test_isa_temperature():
    assert tl.isa_temperature(100 * units.hft).magnitude == pytest.approx(268.338)
    assert tl.isa_temperature(200 * units.hft).magnitude == pytest.approx(248.526)
    assert tl.isa_temperature(300 * units.hft).magnitude == pytest.approx(228.714)
    assert tl.isa_temperature(400 * units.hft).magnitude == pytest.approx(216.650)
    assert tl.isa_temperature(500 * units.hft).magnitude == pytest.approx(216.650)
    assert tl.isa_temperature(600 * units.hft).magnitude == pytest.approx(216.650)
    assert tl.isa_temperature(700 * units.hft).magnitude == pytest.approx(217.986)
    assert tl.isa_temperature(800 * units.hft).magnitude == pytest.approx(221.034)
    assert tl.isa_temperature(1000 * units.hft).magnitude == pytest.approx(227.13)
    with pytest.raises(ValueError):
        tl.isa_temperature(71001 * units.m)
    assert tl.isa_temperature(11000 * units.m).magnitude == pytest.approx(216.65)
    assert tl.isa_temperature(20000 * units.m).magnitude == pytest.approx(216.65)
    assert tl.isa_temperature(32000 * units.m).magnitude == pytest.approx(228.65)
    assert tl.isa_temperature(47000 * units.m).magnitude == pytest.approx(270.65)
    assert tl.isa_temperature(51000 * units.m).magnitude == pytest.approx(270.65)


def test_geop_thickness():
    """Test geop_thickness() with some values from the 1976 US standard
       atmosphere.
    """
    pytest.skip("this test does not make sense, yet")
    # Define some std. atmosphere values (height in m, T in K, p in Pa).
    std_atm_76 = np.array([[0, 288.15, 101325],
                           [500, 284.9, 95460.839342],
                           [1000, 281.65, 89874.570502],
                           [1500, 278.4, 84556.004841],
                           [2000, 275.15, 79495.215511],
                           [2500, 271.9, 74682.533661],
                           [3000, 268.65, 70108.54467],
                           [3500, 265.4, 65764.084371],
                           [4000, 262.15, 61640.235304],
                           [4500, 258.9, 57728.32297],
                           [5000, 255.65, 54019.912104],
                           [5500, 252.4, 50506.802952],
                           [6000, 249.15, 47181.027568],
                           [6500, 245.9, 44034.846117],
                           [7000, 242.65, 41060.743191],
                           [7500, 239.4, 38251.424142],
                           [8000, 236.15, 35599.811423],
                           [8500, 232.9, 33099.040939],
                           [9000, 229.65, 30742.45842],
                           [9500, 226.4, 28523.615797],
                           [10000, 223.15, 26436.267594],
                           [10500, 219.9, 24474.367338],
                           [11000, 216.65, 22632.063973],
                           [11500, 216.65, 20916.189034],
                           [12000, 216.65, 19330.405049],
                           [12500, 216.65, 17864.849029],
                           [13000, 216.65, 16510.405758],
                           [13500, 216.65, 15258.6511],
                           [14000, 216.65, 14101.799606],
                           [14500, 216.65, 13032.656085],
                           [15000, 216.65, 12044.570862],
                           [15500, 216.65, 11131.398413],
                           [16000, 216.65, 10287.459141],
                           [16500, 216.65, 9507.504058],
                           [17000, 216.65, 8786.682132],
                           [17500, 216.65, 8120.510116],
                           [18000, 216.65, 7504.844668],
                           [18500, 216.65, 6935.856576],
                           [19000, 216.65, 6410.006945],
                           [19500, 216.65, 5924.025185],
                           [20000, 216.65, 5474.88867]])

    # Extract p and T arrays.
    p = std_atm_76[:, 2]
    t = std_atm_76[:, 1]

    # Compute geopotential difference and layer thickness. Layer thickness
    # should be similar to the actual altitude given above.
    geopd = tl.geop_difference(p, t, method='cumtrapz')  # noqa
    geopt = tl.geop_thickness(p, t, cumulative=True)  # noqa
