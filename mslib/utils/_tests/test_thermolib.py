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

from mslib.utils.units import units
from mslib.utils import thermolib


def test_flightlevel2pressure2flightlevel():
    fs = (np.arange(1, 71000, 1000.) * units.m).to(units.hft)
    ps = thermolib.flightlevel2pressure(fs)
    fs_p = thermolib.pressure2flightlevel(ps).magnitude
    assert fs.magnitude == pytest.approx(fs_p)


def test_pressure2flightlevel2pressure():
    ps = np.arange(5, 105000, 1.)[::-1] * units.Pa
    fs = thermolib.pressure2flightlevel(ps)
    ps_p = thermolib.flightlevel2pressure(fs).magnitude
    assert ps.magnitude == pytest.approx(ps_p)


def test_flightlevel2pressure():
    assert thermolib.flightlevel2pressure(182.8850 * units.hft).magnitude == pytest.approx(50000)
    assert thermolib.flightlevel2pressure(530.8279 * units.hft).magnitude == pytest.approx(10000)
    assert thermolib.flightlevel2pressure(782.4335 * units.hft).magnitude == pytest.approx(3000)
    assert thermolib.flightlevel2pressure(1151.9583 * units.hft).magnitude == pytest.approx(550)
    assert thermolib.flightlevel2pressure(1626.8966 * units.hft).magnitude == pytest.approx(80)
    assert thermolib.flightlevel2pressure(1804.2727 * units.hft).magnitude == pytest.approx(40)
    with pytest.raises(ValueError):
        thermolib.flightlevel2pressure(72000 * units.m)


def test_pressure2flightlevel():
    assert thermolib.pressure2flightlevel(100000 * units.Pa).magnitude == pytest.approx(3.6378724)
    assert thermolib.pressure2flightlevel(75000 * units.Pa).magnitude == pytest.approx(80.91139)
    assert thermolib.pressure2flightlevel(50000 * units.Pa).magnitude == pytest.approx(182.8850)
    assert thermolib.pressure2flightlevel(10000 * units.Pa).magnitude == pytest.approx(530.8279)
    assert thermolib.pressure2flightlevel(3000 * units.Pa).magnitude == pytest.approx(782.4335)
    assert thermolib.pressure2flightlevel(550 * units.Pa).magnitude == pytest.approx(1151.9583)
    assert thermolib.pressure2flightlevel(80 * units.Pa).magnitude == pytest.approx(1626.8966)
    assert thermolib.pressure2flightlevel(40 * units.Pa).magnitude == pytest.approx(1804.2727)
    with pytest.raises(ValueError):
        thermolib.pressure2flightlevel(3.9 * units.Pa)


def test_isa_temperature():
    assert thermolib.isa_temperature(100 * units.hft).magnitude == pytest.approx(268.338)
    assert thermolib.isa_temperature(200 * units.hft).magnitude == pytest.approx(248.526)
    assert thermolib.isa_temperature(300 * units.hft).magnitude == pytest.approx(228.714)
    assert thermolib.isa_temperature(400 * units.hft).magnitude == pytest.approx(216.650)
    assert thermolib.isa_temperature(500 * units.hft).magnitude == pytest.approx(216.650)
    assert thermolib.isa_temperature(600 * units.hft).magnitude == pytest.approx(216.650)
    assert thermolib.isa_temperature(700 * units.hft).magnitude == pytest.approx(217.986)
    assert thermolib.isa_temperature(800 * units.hft).magnitude == pytest.approx(221.034)
    assert thermolib.isa_temperature(1000 * units.hft).magnitude == pytest.approx(227.13)
    with pytest.raises(ValueError):
        thermolib.isa_temperature(71001 * units.m)
    assert thermolib.isa_temperature(11000 * units.m).magnitude == pytest.approx(216.65)
    assert thermolib.isa_temperature(20000 * units.m).magnitude == pytest.approx(216.65)
    assert thermolib.isa_temperature(32000 * units.m).magnitude == pytest.approx(228.65)
    assert thermolib.isa_temperature(47000 * units.m).magnitude == pytest.approx(270.65)
    assert thermolib.isa_temperature(51000 * units.m).magnitude == pytest.approx(270.65)
