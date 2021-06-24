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
from metpy.constants import g, Rd
from metpy.xarray import preprocess_and_wrap
from xarray.ufuncs import exp, log
from xarray import zeros_like
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
    return eqpt_temp.to('degC').magnitude


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


# Values according to ICAO standard atmosphere
z0 = [0, 11, 20, 32, 47, 51, 71] * units.km
t0 = [288.15, 216.65, 216.65, 228.66, 270.65, 270.65, float("NaN")] * units.K
p0 = [101325, 22632.64, 5475.16, 868.089, 110.928, 66.952, 3.9591] * units.Pa
gamma = [6.5e-3, 0, -1.0e-3, -2.8e-3, 0, -2.8e-3, float("NaN")] * units.K / units.km


@exporter.export
@preprocess_and_wrap(wrap_like='height')
@check_units('[length]')
def flightlevel2pressure(height):
    """
    Conversion of flight level (given in hft) to pressure (Pa) with
    hydrostatic equation, according to the profile of the ICAO
    standard atmosphere.

    Array version, the argument "flightlevel" must be a numpy array.

    Reference:
        For example, H. Kraus, Die Atmosphaere der Erde, Springer, 2001,
        470pp., Sections II.1.4. and II.6.1.2.

    Arguments:
        flightlevel -- numpy array of flight level in hft
    Returns:
        static pressure (Pa)
    """
    def hydrostatic_equation(z):
        layer = next((i - 1 for i in range(len(z0)) if z0[i] > (z if hasattr(z, "__len__") else z[0])), -1)

        if gamma[layer] != 0:
            # Hydrostatic equation with linear temperature gradient gamma.
            return p0[layer] * ((t0[layer] - gamma[layer] * (z - z0[layer])) / t0[layer]) ** (g / (gamma[layer] * Rd))
        else:
            # Hydrostatic equation with constant temperature gradient gamma.
            return p0[layer] * numpy.exp(-g * (z - z0[layer]) / (Rd * t0[layer]))

    if not hasattr(height, "__len__"):
        return hydrostatic_equation(height)
    test = len(height)

    # Initialize the return array.
    p = numpy.full_like(height, numpy.nan)

    # Get indices for each atmosphere layer in array
    for segment_indices in [[(z0[i] < height <= z0[i + 1]) for i in range(len(z0) - 1)]]:
        if any(segment_indices):
            test = hydrostatic_equation(height[segment_indices])
            p[segment_indices] = hydrostatic_equation(height[segment_indices])

    return p * units.Pa


@exporter.export
@preprocess_and_wrap(wrap_like='pressure')
@check_units('[pressure]')
def pressure2flightlevel(pressure):
    """
    Conversion of pressure (Pa) to flight level (hft) with
    hydrostatic equation, according to the profile of the ICAO
    standard atmosphere.

    Array version, the argument "p" must be a numpy array.

    Reference:
        For example, H. Kraus, Die Atmosphaere der Erde, Springer, 2001,
        470pp., Sections II.1.4. and II.6.1.2.

    Arguments:
        p -- numpy array of pressure (Pa)
        fake_above_32km -- compute values above 54.75 hPa (32km) with the
                           profile valid for 20..32km. WARNING: This gives
                           unphysical results. Use this option only for
                           testing purposes.
    Returns:
        flight level in hft
    """
    def inverted_hydrostatic_equation(p):
        layer = next((i - 1 for i in range(len(p0)) if p0[i] < (p if hasattr(p, "__len__") else p[0])), -1)

        if gamma[layer] != 0:
            # Hydrostatic equation with linear temperature gradient gamma.
            return z0[layer] + 1. / gamma[layer] * \
                   (t0[layer] - t0[layer] * exp(gamma[layer] * Rd / g * log(p / p0[layer])))
        else:
            # Hydrostatic equation with constant temperature gradient gamma.
            return p0[layer] * exp(-g * (p - z0[layer]) / (Rd * t0[layer]))

    if not hasattr(pressure, "__len__"):
        return inverted_hydrostatic_equation()

    # Initialize the return array.
    z = numpy.full_like(pressure, numpy.nan)

    for segment_indices, height in [[(p0[i] > pressure >= p0[i + 1]) for i in range(len(p0) - 1)]]:
        if segment_indices:
            z[segment_indices] = inverted_hydrostatic_equation(pressure[segment_indices])

    return z * units.hft
