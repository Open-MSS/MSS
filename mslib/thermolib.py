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
from metpy.units import check_units, units
from metpy.xarray import preprocess_and_wrap
from xarray.ufuncs import exp, log
from xarray import zeros_like
import metpy.calc as mpcalc
from metpy.units import units


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


def flightlevel2pressure(flightlevel):
    """Conversion of flight level (given in hft) to pressure (Pa) with
       hydrostatic equation, according to the profile of the ICAO
       standard atmosphere.

    Reference:
        For example, H. Kraus, Die Atmosphaere der Erde, Springer, 2001,
        470pp., Sections II.1.4. and II.6.1.2.

    Arguments:
        flightlevel -- flight level in hft
    Returns:
        static pressure (Pa)
    """
    # Convert flight level (ft) to m (1 ft = 30.48 cm; 1/0.3048m = 3.28...).
    z = flightlevel * 30.48

    # g and R are used by all equations below.
    g = 9.80665
    R = 287.058

    if z <= 11000.:
        # ICAO standard atmosphere between 0 and 11 km: T(z=0km) = 15 degC,
        # p(z=0km) = 1013.25 hPa. Temperature gradient is 6.5 K/km.
        z0 = 0.
        T0 = 288.15
        gamma = 6.5e-3
        p0 = 101325.

        # Hydrostatic equation with linear temperature gradient.
        p = p0 * ((T0 - gamma * z - z0) / T0) ** (g / (gamma * R))
        return p

    elif z <= 20000.:
        # ICAO standard atmosphere between 11 and 20 km: T(z=11km) = -56.5 degC,
        # p(z=11km) = 226.32 hPa. Temperature is constant at -56.5 degC.
        z0 = 11000.
        p0 = 22632.64
        T = 216.65

        # Hydrostatic equation with constant temperature profile.
        p = p0 * numpy.exp(-g * (z - z0) / (R * T))
        return p

    elif z <= 32000.:
        # ICAO standard atmosphere between 20 and 32 km: T(z=20km) = -56.5 degC,
        # p(z=20km) = 54.75 hPa. Temperature gradient is -1.0 K/km.
        z0 = 20000.
        T0 = 216.65
        gamma = -1.0e-3
        p0 = 5475.16

        # Hydrostatic equation with linear temperature gradient.
        p = p0 * ((T0 - gamma * (z - z0)) / T0) ** (g / (gamma * R))
        return p

    elif z <= 47000.:
        # ICAO standard atmosphere between 32 and 47 km: T(z=32km) = -44.5 degC,
        # p(z=32km) = 8.68019 hPa. Temperature gradient is -2.8 K/km.
        z0 = 32000.
        T0 = 228.66
        gamma = -2.8e-3
        p0 = 868.089

        # Hydrostatic equation with linear temperature gradient.
        p = p0 * ((T0 - gamma * (z - z0)) / T0) ** (g / (gamma * R))
        return p

    elif z <= 51000:
        # ICAO standard atmosphere between 47 and 51 km: T(z=47km) = -2.5 degC,
        # p(z=47km) = 1.10906 hPa. Temperature is constant at -2.5 degC.
        z0 = 47000.
        p0 = 110.928
        T = 270.65

        # Hydrostatic equation with constant temperature profile.
        p = p0 * numpy.exp(-g * (z - z0) / (R * T))
        return p

    elif z <= 71000:
        # ICAO standard atmosphere between 51 and 71 km: T(z=51km) = -2.5 degC,
        # p(z=71km) = 0.66939 hPa. Temperature gradient is 2.8 K/km.
        z0 = 51000.
        T0 = 270.65
        gamma = 2.8e-3
        p0 = 66.952

        # Hydrostatic equation with linear temperature gradient.
        p = p0 * ((T0 - gamma * (z - z0)) / T0) ** (g / (gamma * R))
        return p

    else:
        raise ValueError("flight level to pressure conversion not "
                         "implemented for z > 71km")


def pressure2flightlevel(p):
    """Conversion of pressure (Pa) to flight level (hft) with
       hydrostatic equation, according to the profile of the ICAO
       standard atmosphere.

    Reference:
        For example, H. Kraus, Die Atmosphaere der Erde, Springer, 2001,
        470pp., Sections II.1.4. and II.6.1.2.

    Arguments:
        p -- pressure (Pa)
    Returns:
        flight level in hft
    """
    # g and R are used by all equations below.
    g = 9.80665
    R = 287.058

    if p < 3.956:
        raise ValueError("pressure to flight level conversion not "
                         "implemented for z > 71km (p ~ 4 Pa)")

    elif p <= 66.952:
        # ICAO standard atmosphere between 51 and 71 km: T(z=51km) = -2.5 degC,
        # p(z=71km) = 0.66939 hPa. Temperature gradient is 2.8 K/km.
        z0 = 51000.
        T0 = 270.65
        gamma = 2.8e-3
        p0 = 66.952

        # Hydrostatic equation with linear temperature gradient.
        z = z0 + 1. / gamma * (T0 - T0 * numpy.exp(gamma * R / g * numpy.log(p / p0)))

    elif p < 110.928:
        # ICAO standard atmosphere between 47 and 51 km: T(z=47km) = -2.5 degC,
        # p(z=47km) = 1.10906 hPa. Temperature is constant at -2.5 degC.
        z0 = 47000.
        p0 = 110.928
        T = 270.65

        # Hydrostatic equation with constant temperature profile.
        z = z0 - (R * T) / g * numpy.log(p / p0)

    elif p < 868.089:
        # ICAO standard atmosphere between 32 and 47 km: T(z=32km) = -44.5 degC,
        # p(z=32km) = 54.75 hPa. Temperature gradient is -2.8 K/km.
        z0 = 32000.
        T0 = 228.66
        gamma = -2.8e-3
        p0 = 868.089

        # Hydrostatic equation with linear temperature gradient.
        z = z0 + 1. / gamma * (T0 - T0 * numpy.exp(gamma * R / g * numpy.log(p / p0)))

    elif p < 5474.16:
        # ICAO standard atmosphere between 20 and 32 km: T(z=20km) = -56.5 degC,
        # p(z=20km) = 54.75 hPa. Temperature gradient is -1.0 K/km.
        z0 = 20000.
        T0 = 216.65
        gamma = -1.0e-3
        p0 = 5475.16

        # Hydrostatic equation with linear temperature gradient.
        z = z0 + 1. / gamma * (T0 - T0 * numpy.exp(gamma * R / g * numpy.log(p / p0)))

    elif p < 22632.:
        # ICAO standard atmosphere between 11 and 20 km: T(z=11km) = -56.5 degC,
        # p(z=11km) = 226.32 hPa. Temperature is constant at -56.5 degC.
        z0 = 11000.
        p0 = 22632.64
        T = 216.65

        # Hydrostatic equation with constant temperature profile.
        z = z0 - (R * T) / g * numpy.log(p / p0)

    else:
        # ICAO standard atmosphere between 0 and 11 km: T(z=0km) = 15 degC,
        # p(z=0km) = 1013.25 hPa. Temperature gradient is 6.5 K/km.
        z0 = 0
        T0 = 288.15
        gamma = 6.5e-3
        p0 = 101325.

        # Hydrostatic equation with linear temperature gradient.
        z = 1. / gamma * (T0 - T0 * numpy.exp(gamma * R / g * numpy.log(p / p0)))

    # Convert from m to flight level (ft).
    flightlevel = z * 0.0328083989502

    return flightlevel


def height_to_atmosphere(height):
    height_m = height.to(units.meter)
    # ICAO standard atmosphere between 0 and 11 km: T(z=0km) = 15 degC,
    # p(z=0km) = 1013.25 hPa. Temperature gradient is 6.5 K/km.
    if height_m <= 11000:
        z0 = 0 * units.meter
        T0 = 288.15 * units.kelvin
        gamma = 6.5e-3 * units.kelvin / units.kilometer
        p0 = 101325. * units.pascal
    # ICAO standard atmosphere between 11 and 20 km: T(z=11km) = -56.5 degC,
    # p(z=11km) = 226.32 hPa. Temperature is constant at -56.5 degC.
    elif height_m <= 20000:
        z0 = 11000. * units.meter
        p0 = 22632.64 * units.pascal
        T0 = 216.65 * units.kelvin
        gamma = None
    # ICAO standard atmosphere between 20 and 32 km: T(z=20km) = -56.5 degC,
    # p(z=20km) = 54.75 hPa. Temperature gradient is -1.0 K/km.
    elif height_m <= 32000:
        z0 = 20000. * units.meter
        T0 = 216.65 * units.kelvin
        gamma = -1.0e-3 * units.kelvin / units.kilometer
        p0 = 5475.16 * units.pascal
    # ICAO standard atmosphere between 32 and 47 km: T(z=32km) = -44.5 degC,
    # p(z=32km) = 8.68019 hPa. Temperature gradient is -2.8 K/km.
    elif height_m <= 47000:
        z0 = 32000. * units.meter
        T0 = 228.66 * units.kelvin
        gamma = -2.8e-3 * units.kelvin / units.kilometer
        p0 = 868.089 * units.pascal
    # ICAO standard atmosphere between 47 and 51 km: T(z=47km) = -2.5 degC,
    # p(z=47km) = 1.10906 hPa. Temperature is constant at -2.5 degC.
    elif height_m <= 51000:
        z0 = 47000. * units.meter
        T0 = 270.65 * units.kelvin
        p0 = 110.928 * units.pascal
        gamma = None
    # ICAO standard atmosphere between 51 and 71 km: T(z=51km) = -2.5 degC,
    # p(z=71km) = 0.66939 hPa. Temperature gradient is 2.8 K/km.
    elif height_m <= 71000:
        z0 = 51000. * units.meter
        T0 = 270.65 * units.kelvin
        gamma = 2.8e-3 * units.kelvin / units.kilometer
        p0 = 66.952 * units.pascal
    else:
        raise ValueError("height to pressure conversion not implemented for z > 71km")
    return z0, T0, gamma, p0


exporter = Exporter(globals())
@exporter.export
@preprocess_and_wrap(wrap_like='height')
@check_units('[length]')
def flightlevel2pressure_a(height):
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
    if (height.to(units.meter) > 71000).any():
        raise ValueError("height to pressure conversion not implemented for z > 71km")

    # Initialize the return array.
    p = zeros_like(height)

    height_m = height.to(units.meter)
    for segment_indices in [height_m <= 11000,
                            11000 < height_m <= 20000,
                            20000 < height_m <= 32000,
                            32000 < height_m <= 47000,
                            47000 < height_m <= 51000,
                            51000 < height_m <= 71000,
                            height_m > 71000]:
        if segment_indices:
            z0, T0, gamma, p0 = height_to_atmosphere(height_m[segment_indices[0]])
            # Hydrostatic equation with linear temperature gradient.
            if gamma:
                p[segment_indices] = p0 * ((T0 - gamma * (height[segment_indices] - z0)) / T0) ** (g / (gamma * Rd))
            # Hydrostatic equation with constant temperature profile.
            else:
                p[segment_indices] = p0 * numpy.exp(-g * (height[segment_indices] - z0) / (Rd * T0))

    return p


@exporter.export
@preprocess_and_wrap(wrap_like='pressure')
@check_units('[pressure]')
def pressure2flightlevel_a(pressure):
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

    if (pressure.to(units.pascal) < 3.9591).any():
        raise ValueError("pressure to flight level conversion not "
                         "implemented for z > 71km (p ~ 4 Pa)")

    # Initialize the return array.
    z = zeros_like(pressure)

    pressure_Pa = pressure.to(units.pascal)
    for segment_indices, height in [(3.9591 > pressure_Pa <= 66.952, 71 * units.kilometer),
                                    (11000 < pressure_Pa <= 110.928, 51 * units.kilometer),
                                    (20000 < pressure_Pa <= 868.089, 47 * units.kilometer),
                                    (32000 < pressure_Pa <= 5474.16, 32 * units.kilometer),
                                    (47000 < pressure_Pa <= 22632, 20 * units.kilometer),
                                    (pressure_Pa > 22632, 11 * units.kilometer)]:
        if segment_indices:
            z0, T0, gamma, p0 = height_to_atmosphere(height)
            # Hydrostatic equation with linear temperature gradient.
            if gamma:
                z[segment_indices] = z0 + 1. / gamma * (T0 - T0 *
                                                        exp(gamma * Rd / g * log(pressure[segment_indices] / p0)))
            # Hydrostatic equation with constant temperature profile.
            else:
                z[segment_indices] = p0 * exp(-g * (pressure_Pa[segment_indices] - z0) / (Rd * T0))

    return z


def isa_temperature(flightlevel):
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
    # Convert flight level (ft) to m (1 ft = 30.48 cm; 1/0.3048m = 3.28...).
    z = flightlevel * 30.48

    if z <= 11000.:
        # ICAO standard atmosphere between 0 and 11 km: T(z=0km) = 15 degC,
        # p(z=0km) = 1013.25 hPa. Temperature gradient is 6.5 K/km.
        T0 = 288.15
        gamma = 6.5e-3
        return T0 - gamma * z

    elif z <= 20000.:
        # ICAO standard atmosphere between 11 and 20 km: T(z=11km) = -56.5 degC,
        # p(z=11km) = 226.32 hPa. Temperature is constant at -56.5 degC.
        T = 216.65
        return T

    elif z <= 32000.:
        # ICAO standard atmosphere between 20 and 32 km: T(z=20km) = -56.5 degC,
        # p(z=20km) = 54.75 hPa. Temperature gradient is -1.0 K/km.
        z0 = 20000.
        T0 = 216.65
        gamma = -1.0e-3
        return T0 - gamma * (z - z0)

    elif z <= 47000.:
        # ICAO standard atmosphere between 32 and 47 km: T(z=32km) = -44.5 degC,
        # p(z=32km) = 8.68019 hPa. Temperature gradient is -2.8 K/km.
        z0 = 32000.
        T0 = 228.65
        gamma = -2.8e-3
        return T0 - gamma * (z - z0)

    elif z <= 47820.070345213892438:
        # ICAO standard atmosphere between 47 and 47820.070345213892438 km: T(z=47km) = -2.5 degC,
        # p(z=47km) = 1.10906 hPa. Temperature is constant at -2.5 degC.
        T = 270.65
        return T

    else:
        raise ValueError("ISA temperature from flight level not "
                         "implemented for z > 71km")
