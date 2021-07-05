# -*- coding: utf-8 -*-
"""

    mslib.thermolib
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
import scipy.integrate
import logging
from metpy.package_tools import Exporter
from metpy.constants import Rd, g
from metpy.xarray import preprocess_and_wrap
import metpy.calc as mpcalc
from metpy.units import units, check_units

exporter = Exporter(globals())


class VapourPressureError(Exception):
    """Exception class to handle error arising during the computation of vapour
       pressures.
    """

    def __init__(self, error_string):
        logging.debug("%s", error_string)


def sat_vapour_pressure(t):
    """Compute saturation vapour presure in Pa from temperature.

    Arguments:
    t -- temperature in [K]

    Returns: Saturation Vapour Pressure in [Pa], in the same dimensions as the input.
    """
    v_pr = mpcalc.saturation_vapor_pressure(t * units.kelvin)

    # Convert return value units from mbar to Pa.
    return v_pr.to('Pa').magnitude


def rel_hum(p, t, q):
    """Compute relative humidity in [%] from pressure, temperature, and
       specific humidity.

    Arguments:
    p -- pressure in [Pa]
    t -- temperature in [K]
    q -- specific humidity in [kg/kg]

    Returns: Relative humidity in [%]. Same dimension as input fields.
    """
    p = units.Quantity(p, "Pa")
    t = units.Quantity(t, "K")
    rel_humidity = mpcalc.relative_humidity_from_specific_humidity(p, t, q)

    # Return specific humidity in [%].
    return rel_humidity * 100


def virt_temp(t, q):
    """
    Compute virtual temperature in [K] from temperature and
    specific humidity.

    Arguments:
    t -- temperature in [K]
    q -- specific humidity in [kg/kg]

    t and q can be scalars of NumPy arrays. They just have to either all
    scalars, or all arrays.

    Returns: Virtual temperature in [K]. Same dimension as input fields.
    """
    t = units.Quantity(t, "K")
    mix_rat = mpcalc.mixing_ratio_from_specific_humidity(q)
    v_temp = mpcalc.virtual_temperature(t, mix_rat)
    return v_temp


def geop_difference(p, t, method='trapz', axis=-1):
    """Compute geopotential difference in [m**2 s**-2] between the pressure
       levels given by the first and last element in p (= pressure).

    Implements the hypsometric equation (1.17) from Holton, 3rd edition (or
    alternatively the integral form of (3.23) in Wallace and Hobbs, 2nd ed.).

    Arguments:
    p -- pressure in [Pa], needs to be a NumPy array with at least 2 elements.
    t -- temperature in [K], needs to be a NumPy array with at least 2 elements.

         Both arrays can be multidimensional, in this case pay attention to
         the 'axis' argument.

    method -- optional keyword to specify the integration method used.
              Default is 'trapz', which uses the trapezoidal rule.
              Alternatively, 'simps' causes Simpson's rule to be used.
              'cumtrapz' returns an array with the integrals between the
              first value in p and all other values. This is useful, for
              instance, for computing the geopotential on all model
              levels.

              See the 'scipy.integrate' documentation for further details.

    axis -- optional keyword to specify the vertical coordinate axis if p, t
            are multidimensional (e.g. if the axes of p, t specify [time,
            level, lat, lon] set axis=1). Default is the last dimension.

    Returns: Geopotential difference between p[0] and p[-1] in [m**2 s**-2].
             If 'cumtrapz' is specified, an array of dimension dim(p)-1
             will be returned, in which value n represents the geopotential
             difference between p[0] and p[n+1].
    """

    # The hypsometric equation integrates over ln(p).
    lnp = numpy.log(p)

    # Use scipy.intgerate to evaluate the integral. It is
    #     phi2 - phi1 = Rd * int( T,  d ln(p), p1, p2 ),
    # where phi denotes the geopotential.
    if method == 'trapz':
        return 287.058 * scipy.integrate.trapz(t, lnp, axis=axis)
    elif method == 'cumtrapz':
        return 287.058 * scipy.integrate.cumtrapz(t, lnp, axis=axis)
    elif method == 'simps':
        return 287.058 * scipy.integrate.simps(t, lnp, axis=axis)
    else:
        raise TypeError('integration method for geopotential not understood')


def pot_temp(p, t):
    """
    Computes potential temperature in [K] from pressure and temperature.

    Arguments:
    p -- pressure in [Pa]
    t -- temperature in [K]

    p and t can be scalars of NumPy arrays. They just have to either both
    scalars, or both arrays.

    Returns: potential temperature in [K]. Same dimensions as the inputs.
    """
    p = units.Quantity(p, "Pa")
    t = units.Quantity(t, "K")
    potential_temp = mpcalc.potential_temperature(p, t)
    return potential_temp


def eqpt_approx(p, t, q):
    """
    Computes equivalent potential temperature in [K] from pressure,
    temperature and specific humidity.

    Arguments:
    p -- pressure in [Pa]
    t -- temperature in [K]
    q -- specific humidity in [kg/kg]

    p, t and q can be scalars or NumPy arrays.

    Returns: equivalent potential temperature in [K]. Same dimensions as
    the inputs.
    """
    p = units.Quantity(p, "Pa")
    t = units.Quantity(t, "K")
    dew_temp = mpcalc.dewpoint_from_specific_humidity(p, t, q)
    eqpt_temp = mpcalc.equivalent_potential_temperature(p, t, dew_temp)
    return eqpt_temp.to('K').magnitude


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
    omega = units.Quantity(omega, "Pa/s")
    p = units.Quantity(p, "Pa")
    t = units.Quantity(t, "K")
    om_w = mpcalc.vertical_velocity(omega, p, t)
    return om_w


# Values according to the 1976 U.S. Standard atmosphere [NOAA1976]_.
# List of tuples (height, temperature, pressure, temperature gradient)
standard_atmosphere = [
    (0 * units.km, 288.15 * units.K, 101325 * units.Pa, 0.0065 * units.K / units.m),
    (11 * units.km, 216.65 * units.K, 22632.1 * units.Pa, 0 * units.K / units.m),
    (20 * units.km, 216.65 * units.K, 5474.89 * units.Pa, -0.001 * units.K / units.m),
    (32 * units.km, 228.65 * units.K, 868.019 * units.Pa, -0.0028 * units.K / units.m),
    (47 * units.km, 270.65 * units.K, 110.906 * units.Pa, 0 * units.K / units.m),
    (51 * units.km, 270.65 * units.K, 66.9389 * units.Pa, 0.0028 * units.K / units.m),
    (71 * units.km, 214.65 * units.K, 3.95642 * units.Pa, float("NaN") * units.K / units.m)
]


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

    for i, ((z0, t0, p0, gamma), (z1, t1, p1, _)) in enumerate(zip(standard_atmosphere[:-1], standard_atmosphere[1:])):
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

    for i, ((z0, t0, p0, gamma), (z1, t1, p1, _)) in enumerate(zip(standard_atmosphere[:-1], standard_atmosphere[1:])):
        p1 = standard_atmosphere[i + 1][-2]
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
    for i, ((z0, t0, p0, gamma), (z1, t1, p1, _)) in enumerate(zip(standard_atmosphere[:-1], standard_atmosphere[1:])):
        if ((i == 0) and (height < z0)) or (z0 <= height < z1):
            return t0 - gamma * (height - z0)

    raise ValueError("ISA temperature from flight level not "
                     "implemented for z > 71km")
