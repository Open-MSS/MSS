# -*- coding: utf-8 -*-
"""

    mslib.utils.thermolib
    ~~~~~~~~~~~~~~~~

    Collection of thermodynamic functions.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
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

import numpy

from mslib.utils.units import units, check_units

from metpy.package_tools import Exporter
from metpy.constants import Rd, g
from metpy.xarray import preprocess_and_wrap
import metpy.calc as mpcalc

exporter = Exporter(globals())


def rel_hum(p, t, q):
    """Compute relative humidity in [%] from pressure, temperature, and
       specific humidity.

    Arguments:
    p -- pressure in [Pa]
    t -- temperature in [K]
    q -- specific humidity in [kg/kg]

    Returns: Relative humidity in [%].
    """
    return mpcalc.relative_humidity_from_specific_humidity(
        units.Pa * p, units.K * t, q).to("dimensionless").m * 100


def pot_temp(p, t):
    """
    Computes potential temperature in [K] from pressure and temperature.

    Arguments:
    p -- pressure in [Pa]
    t -- temperature in [K]

    p and t can be scalars of NumPy arrays. They just have to either both
    scalars, or both arrays.

    Returns: potential temperature in [K].
    """
    return mpcalc.potential_temperature(
        units.Pa * p, units.K * t).to("K").m


def eqpt_approx(p, t, q):
    """
    Computes equivalent potential temperature in [K] from pressure,
    temperature and specific humidity.

    Arguments:
    p -- pressure in [Pa]
    t -- temperature in [K]
    q -- specific humidity in [kg/kg]

    p, t and q can be scalars or NumPy arrays.

    Returns: equivalent potential temperature in [K].
    """

    return mpcalc.equivalent_potential_temperature(
        units.Pa * p, units.K * t,
        mpcalc.dewpoint_from_specific_humidity(units.Pa * p, units.K * t, q)).to("K").m


def omega_to_w(omega, p, t):
    """
    Convert pressure vertical velocity to geometric vertical velocity.

    Arguments:
    omega -- vertical velocity in pressure coordinates, in [Pa/s]
    p -- pressure in [Pa]
    t -- temperature in [K]

    All inputs can be scalars or NumPy arrays.

    Returns the vertical velocity in geometric coordinates, [m/s].
    """
    return mpcalc.vertical_velocity(
        units("Pa/s") * omega, units.Pa * p, units.K * t).to("m/s").m


# Values according to the 1976 U.S. Standard atmosphere [NOAA1976]_.
# List of tuples (height, temperature, pressure, temperature gradient)
_STANDARD_ATMOSPHERE = [
    (0 * units.km, 288.15 * units.K, 101325 * units.Pa, 0.0065 * units.K / units.m),
    (11 * units.km, 216.65 * units.K, 22632.1 * units.Pa, 0 * units.K / units.m),
    (20 * units.km, 216.65 * units.K, 5474.89 * units.Pa, -0.001 * units.K / units.m),
    (32 * units.km, 228.65 * units.K, 868.019 * units.Pa, -0.0028 * units.K / units.m),
    (47 * units.km, 270.65 * units.K, 110.906 * units.Pa, 0 * units.K / units.m),
    (51 * units.km, 270.65 * units.K, 66.9389 * units.Pa, 0.0028 * units.K / units.m),
    (71 * units.km, 214.65 * units.K, 3.95642 * units.Pa, float("NaN") * units.K / units.m)
]
_HEIGHT, _TEMPERATURE, _PRESSURE, _TEMPERATURE_GRADIENT = 0, 1, 2, 3


@exporter.export
@preprocess_and_wrap(wrap_like='height')
@check_units('[length]')
def flightlevel2pressure(height):
    r"""
    Conversion of flight level to pressure (Pa) with
    hydrostatic equation, according to the profile of the 1976 U.S. Standard atmosphere [NOAA1976]_.
    Reference:
        H. Kraus, Die Atmosphaere der Erde, Springer, 2001, 470pp., Sections II.1.4. and II.6.1.2.

    Parameters
    ----------
    height : `pint.Quantity` or `xarray.DataArray`
        Atmospheric height

    Returns
    -------
    `pint.Quantity` or `xarray.DataArray`
        Corresponding pressure value(s) (Pa)

    Notes
    -----
    .. math:: p = \begin{cases}
              p_0 \cdot \left[\frac{T_0 - \Gamma \cdot (Z - Z_0)}{T_0}\right]^{\frac{g}{\Gamma \cdot R}}
              &\Gamma \neq 0\\
              p_0 \cdot \exp\left(\frac{-g \cdot (Z - Z_0)}{R \cdot T_0}\right) &\text{else}
              \end{cases}
    """
    is_array = hasattr(height.magnitude, "__len__")
    if not is_array:
        height = [height.magnitude] * height.units

    # Initialize the return array.
    p = numpy.full_like(height, numpy.nan) * units.Pa

    for i, ((z0, t0, p0, gamma), (z1, t1, p1, _)) in enumerate(zip(_STANDARD_ATMOSPHERE[:-1],
                                                                   _STANDARD_ATMOSPHERE[1:])):
        indices = (height >= z0) & (height < z1)
        if i == 0:
            indices |= height < z0
        if gamma != 0:
            p[indices] = p0 * ((t0 - gamma * (height[indices] - z0)) / t0) ** (g / (gamma * Rd))
        else:
            p[indices] = p0 * numpy.exp(-g * (height[indices] - z0) / (Rd * t0))

    if numpy.isnan(p).any():
        raise ValueError("flight level to pressure conversion not "
                         "implemented for z > 71km")

    return p if is_array else p[0]


@exporter.export
@preprocess_and_wrap(wrap_like='pressure')
@check_units('[pressure]')
def pressure2flightlevel(pressure):
    r"""
    Conversion of pressure to height (hft) with
    hydrostatic equation, according to the profile of the 1976 U.S. Standard atmosphere [NOAA1976]_.
    Reference:
        H. Kraus, Die Atmosphaere der Erde, Springer, 2001, 470pp., Sections II.1.4. and II.6.1.2.

    Parameters
    ----------
    pressure : `pint.Quantity` or `xarray.DataArray`
        Atmospheric pressure

    Returns
    -------
    `pint.Quantity` or `xarray.DataArray`
        Corresponding height value(s) (hft)

    Notes
    -----
    .. math:: Z = \begin{cases}
              Z_0 + \frac{T_0 - T_0 \cdot \exp\left(\frac{\Gamma \cdot R}{g\cdot\log(\frac{p}{p0})}\right)}{\Gamma}
              &\Gamma \neq 0\\
              Z_0 - \frac{R \cdot T_0}{g \cdot \log(\frac{p}{p_0})} &\text{else}
              \end{cases}
    """
    is_array = hasattr(pressure.magnitude, "__len__")
    if not is_array:
        pressure = [pressure.magnitude] * pressure.units

    # Initialize the return array.
    z = numpy.full_like(pressure, numpy.nan) * units.hft

    for i, ((z0, t0, p0, gamma), (z1, t1, p1, _)) in enumerate(zip(_STANDARD_ATMOSPHERE[:-1],
                                                                   _STANDARD_ATMOSPHERE[1:])):
        p1 = _STANDARD_ATMOSPHERE[i + 1][_PRESSURE]
        indices = (pressure > p1) & (pressure <= p0)
        if i == 0:
            indices |= (pressure >= p0)
        if gamma != 0:
            z[indices] = z0 + 1. / gamma * (t0 - t0 * numpy.exp(gamma * Rd / g * numpy.log(pressure[indices] / p0)))
        else:
            z[indices] = z0 - (Rd * t0) / g * numpy.log(pressure[indices] / p0)

    if numpy.isnan(z).any():
        raise ValueError("flight level to pressure conversion not "
                         "implemented for z > 71km")

    return z if is_array else z[0]


@exporter.export
@preprocess_and_wrap(wrap_like='height')
@check_units('[length]')
def isa_temperature(height):
    """
    International standard atmosphere temperature at the given flight level.

    Reference:
        For example, H. Kraus, Die Atmosphaere der Erde, Springer, 2001,
        470pp., Sections II.1.4. and II.6.1.2.

    Arguments:
        flightlevel -- flight level in hft
    Returns:
        temperature (K)
    """
    for i, ((z0, t0, p0, gamma), (z1, t1, p1, _)) in enumerate(zip(_STANDARD_ATMOSPHERE[:-1],
                                                                   _STANDARD_ATMOSPHERE[1:])):
        if ((i == 0) and (height < z0)) or (z0 <= height < z1):
            return t0 - gamma * (height - z0)

    raise ValueError("ISA temperature from flight level not "
                     "implemented for z > 71km")


def convert_pressure_to_vertical_axis_measure(vertical_axis, pressure):
    """
    vertical_axis can take following values
    - pressure altitude
    - flight level
    - pressure
    """
    if vertical_axis == "pressure":
        return float(pressure / 100)
    elif vertical_axis == "flight level":
        return pressure2flightlevel(pressure * units.Pa).magnitude
    elif vertical_axis == "pressure altitude":
        return pressure2flightlevel(pressure * units.Pa).to(units.km).magnitude
    else:
        return pressure
