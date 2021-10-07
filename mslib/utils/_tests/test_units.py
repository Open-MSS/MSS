# -*- coding: utf-8 -*-
"""

    mslib.mswms._tests.test_convert
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mswms.utils convert_to function.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2017 Reimar Bauer
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

import pytest
from mslib.utils.units import convert_to, units


def test_units():
    assert units("10 degree_north").to("degree").m == 10
    assert units("10 degrees_north").to("degree").m == 10
    assert units("10 degreeN").to("degree").m == 10
    assert units("10 degree_N").to("degree").m == 10
    assert units("-10 degree_south").to("degree").m == 10
    assert units("-10 degrees_south").to("degree").m == 10
    assert units("-10 degreeS").to("degree").m == 10
    assert units("-10 degree_S").to("degree").m == 10
    assert units("10 degree_east").to("degree").m == 10
    assert units("10 degrees_east").to("degree").m == 10
    assert units("10 degreeE").to("degree").m == 10
    assert units("10 degree_E").to("degree").m == 10
    assert units("-10 degree_west").to("degree").m == 10
    assert units("-10 degrees_west").to("degree").m == 10
    assert units("-10 degreeW").to("degree").m == 10
    assert units("-10 degree_W").to("degree").m == 10
    assert units("1 percent"). to("dimensionless").m == 0.01
    assert units("1 permille"). to("dimensionless").m == 0.001
    assert units("1 ppm"). to("dimensionless").m == pytest.approx(1e-6)
    assert units("1 ppb"). to("dimensionless").m == pytest.approx(1e-9)
    assert units("1 ppt"). to("dimensionless").m == pytest.approx(1e-12)
    assert units("1 ppmv"). to("dimensionless").m == pytest.approx(1e-6)
    assert units("1 ppbv"). to("dimensionless").m == pytest.approx(1e-9)
    assert units("1 pptv"). to("dimensionless").m == pytest.approx(1e-12)

    assert units("1 PVU").to_base_units().m == pytest.approx(units("1E-6 m^2 s^-1 K kg^-1").to_base_units().m)


def test_convert_to():
    assert convert_to(10, "km", "m", None) == 10000
    assert convert_to(1000, "m", "km", None) == 1

    assert convert_to(1000, "Pa", "hPa", None) == 10
    assert convert_to(1000, "hPa", "Pa", None) == 100000

    assert convert_to(10, "degC", "K", None) == 283.15

    assert convert_to(10 * 9.81, "m^2s^-2", "m", None) == pytest.approx(10)
    assert convert_to(10 * 9.81, "m**2s**-2", "m", None) == pytest.approx(10)

    with pytest.raises(TypeError):
        assert convert_to(10, "m", "m**2s**-2", None) == 10

    assert convert_to(10, "m", "m**2s**-2", 1) == 10
    assert convert_to(10, "m", "m**2s**-2", 9.81) == pytest.approx(98.1)

    assert convert_to(1000, "", "Pa", 999) == 999000
    assert convert_to(1000, "Pa", "", 999) == 999000
    assert convert_to(1000, "whattheheck", "Pa", 999) == 999000
    assert convert_to(1000, "hPa", "whattheheck", 999) == 999000
    assert convert_to(1000, "whattheheck", "whatthehock", 999) == 999000

    assert convert_to(10, "percent", "dimensionless", None) == 0.1
    assert convert_to(10, "permille", "dimensionless", None) == 0.01
    assert convert_to(10, "ppm", "dimensionless", None) == pytest.approx(10e-6)
    assert convert_to(10, "ppb", "dimensionless", None) == pytest.approx(10e-9)
    assert convert_to(10, "ppt", "dimensionless", None) == pytest.approx(10e-12)
    assert convert_to(10, "ppm", "ppt", None) == pytest.approx(10e6)
    assert convert_to(10, "ppb", "ppm", None) == pytest.approx(10e-3)
