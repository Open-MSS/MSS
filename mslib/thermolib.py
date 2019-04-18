# -*- coding: utf-8 -*-
"""

    mslib.thermolib
    ~~~~~~~~~~~~~~~~

    Collection of thermodynamic functions.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2019 by the mss team, see AUTHORS.
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

from __future__ import division

# The function sat_vapour_pressure() has been ported from the IDL function
# 'VaporPressure' by Holger Voemel, available at http://cires.colorado.edu/~voemel/vp.html.

import numpy
import scipy.integrate


class VapourPressureError(Exception):
    """Exception class to handle error arising during the computation of vapour
       pressures.
    """
    pass


def sat_vapour_pressure(t, liquid='HylandWexler', ice='GoffGratch',
                        force_phase='None'):
    """
    Compute the saturation vapour pressure over liquid water and over ice
    with a variety of formulations.

    This function is a direct port from the IDL function 'VaporPressure' by
    Holger Voemel, available at http://cires.colorado.edu/~voemel/vp.html.

    By default, for temperatures > 0 degC, the saturation pressure over
    liquid water is computed; from temperatures <= 0 degC a formulation
    over ice is used.

    The current default fomulas are Hyland and Wexler for liquid and
    Goff Gratch for ice. (hv20040521)

    Arguments:
    t -- Temperature in [K]. Can be a scaler or an n-dimensional NumPy array.
    liquid -- Optional; specify the formulation for computing the saturation
              pressure over liquid water. Can be one of:

              HylandWexler, GoffGratch, Wexler, MagnusTeten, Buck_original,
              Buck_manual, WMO_Goff, WMO2000, Sonntag, Bolton, [Fukuta (N/A)],
              IAPWS, MurphyKoop.

    ice -- Optional; specify the formulation for computing the saturation
           pressure over ice. Can be one of:

           MartiMauersberger, HylandWexler, GoffGratch, MagnusTeten,
           Buck_original, Buck_manual, WMO_Goff, Sonntag, MurphyKoop.

           Please have a look at the source code for further information
           about the formulations.

    force_phase -- Optional; force liquid or ice phase to avoid automatic
                   switching of formulations at 0 degC. Can be 'liquid'
                   or 'ice'.

    Returns:
    Saturation vapor pressure [Pa], in the same dimensions as the input.
    """

    # Make sure the input is a NumPy array.
    if numpy.isscalar(t):
        t = numpy.array([t])
        input_scalar = True
    else:
        t = numpy.array(t)
        input_scalar = False

    # Get indexes of input temperatures above and below freezing, to select
    # the appropriate method for each temperature.
    if force_phase == "ice":
        idx_ice = ()  # numpy.where(t is not None)
        idx_liq = None
    elif force_phase == "liquid":
        idx_liq = ()  # numpy.where(t is not None)
        idx_ice = None
    elif force_phase == "None":
        idx_ice = numpy.where(t <= 273.15)
        idx_liq = numpy.where(t > 273.15)
    else:
        raise VapourPressureError(u"Cannot recognize the force_phase "
                                  u"keyword: '{}' (valid are ice, liquid, None)".format(force_phase))

    # Initialise output field.
    e_sat = numpy.zeros(numpy.shape(t))

    # =============================================================================
    #  Calculate saturation pressure over liquid water ----------------------------
    if not force_phase == 'ice':

        if liquid == 'MartiMauersberger':
            raise VapourPressureError("Marti and Mauersberger don't "
                                      "have a vapour pressure curve over liquid.")

        elif liquid == 'HylandWexler':
            # Source: Hyland, R. W. and A. Wexler, Formulations for the
            # Thermodynamic Properties of the saturated Phases of H2O
            # from 173.15K to 473.15K, ASHRAE Trans, 89(2A), 500-519, 1983.
            e_sat[idx_liq] = (numpy.exp((-0.58002206E4 / t[idx_liq]) +
                                        0.13914993E1 -
                                        0.48640239E-1 * t[idx_liq] +
                                        0.41764768E-4 * t[idx_liq] ** 2. -
                                        0.14452093E-7 * t[idx_liq] ** 3. +
                                        0.65459673E1 * numpy.log(t[idx_liq])) / 100.)

        elif liquid == 'Wexler':
            # Wexler, A., Vapor pressure formulation for ice, Journal of
            # Research of the National Bureau of Standards-A. 81A, 5-20, 1977.
            e_sat[idx_liq] = (numpy.exp(-2.9912729E3 * t[idx_liq] ** (-2.) -
                                        6.0170128E3 * t[idx_liq] ** (-1.) +
                                        1.887643854E1 * t[idx_liq] ** 0. -
                                        2.8354721E-2 * t[idx_liq] ** 1. +
                                        1.7838301E-5 * t[idx_liq] ** 2. -
                                        8.4150417E-10 * t[idx_liq] ** 3. -
                                        4.4412543E-13 * t[idx_liq] ** 4. +
                                        2.858487 * numpy.log(t[idx_liq])) / 100.)

        elif liquid == 'GoffGratch':
            # Goff Gratch formulation.
            # Source: Smithsonian Meteorological Tables, 5th edition,
            # p. 350, 1984
            # From original source: Goff and Gratch (1946), p. 107.
            ts = 373.16  # steam point temperature in K
            ews = 1013.246  # saturation pressure at steam point
            # temperature, normal atmosphere
            e_sat[idx_liq] = 10. ** (-7.90298 * ((ts / t[idx_liq]) - 1.) +
                                     5.02808 * numpy.log10((ts / t[idx_liq])) -
                                     1.3816E-7 * (10. ** (11.344 * (1. - (t[idx_liq] / ts))) - 1.) +
                                     8.1328E-3 * (10. ** (-3.49149 * ((ts / t[idx_liq]) - 1)) - 1.) +
                                     numpy.log10(ews))

        elif liquid == 'MagnusTeten':
            # Source: Murray, F. W., On the computation of saturation
            # vapor pressure, J. Appl. Meteorol., 6, 203-204, 1967.
            tc = t - 273.15
            e_sat[idx_liq] = 10. ** (7.5 * (tc[idx_liq]) / (tc[idx_liq] + 237.5) + 0.7858)

        elif liquid == 'Buck_original':
            # Bucks vapor pressure formulation based on Tetens formula
            # Source: Buck, A. L., New equations for computing vapor
            # pressure and enhancement factor, J. Appl. Meteorol., 20,
            # 1527-1532, 1981.
            tc = t - 273.15
            e_sat[idx_liq] = 6.1121 * numpy.exp(17.502 * tc[idx_liq] / (240.97 + tc[idx_liq]))

        elif liquid == 'Buck_manual':
            # Bucks vapor pressure formulation based on Tetens formula
            # Source: Buck Research, Model CR-1A Hygrometer Operating
            # Manual, Sep 2001
            tc = t - 273.15
            e_sat[idx_liq] = 6.1121 * numpy.exp((18.678 - (tc[idx_liq] / 234.5)) *
                                                (tc[idx_liq]) / (257.14 + tc[idx_liq]))

        elif liquid == 'WMO_Goff':
            # Intended WMO formulation, originally published by Goff (1957)
            # incorrectly referenced by WMO technical regulations, WMO-NO 49,
            # Vol I, General Meteorological Standards and Recommended
            # Practices, App. A, Corrigendum Aug 2000.
            # and incorrectly referenced by WMO technical regulations,
            # WMO-NO 49, Vol I, General Meteorological Standards and
            # Recommended Practices, App. A, 1988.
            ts = 273.16  # steam point temperature in K
            e_sat[idx_liq] = 10. ** (10.79574 * (1. - (ts / t[idx_liq])) -
                                     5.02800 * numpy.log10((t[idx_liq] / ts)) +
                                     1.50475E-4 * (1. - 10. ** (-8.2969 * ((t[idx_liq] / ts) - 1.))) +
                                     0.42873E-3 * (10. ** (+4.76955 * (1. - (ts / t[idx_liq]))) - 1.) +
                                     0.78614)

        elif liquid == 'WMO2000':
            # WMO formulation, which is very similar to Goff Gratch
            # Source: WMO technical regulations, WMO-NO 49, Vol I,
            # General Meteorological Standards and Recommended Practices,
            # App. A, Corrigendum Aug 2000.
            ts = 273.16  # steam point temperature in K
            e_sat[idx_liq] = 10. ** (10.79574 * (1. - (ts / t[idx_liq])) -
                                     5.02800 * numpy.log10((t[idx_liq] / ts)) +
                                     1.50475E-4 * (1. - 10. ** (-8.2969 * ((t[idx_liq] / ts) - 1.))) +
                                     0.42873E-3 * (10. ** (-4.76955 * (1. - (ts / t[idx_liq]))) - 1.) +
                                     0.78614)

        elif liquid == 'Sonntag':
            # Source: Sonntag, D., Advancements in the field of hygrometry,
            # Meteorol. Z., N. F., 3, 51-66, 1994.
            e_sat[idx_liq] = numpy.exp(-6096.9385 * t[idx_liq] ** (-1.) +
                                       16.635794 -
                                       2.711193E-2 * t[idx_liq] ** 1. +
                                       1.673952E-5 * t[idx_liq] ** 2. +
                                       2.433502 * numpy.log(t[idx_liq]))

        elif liquid == 'Bolton':
            # Source: Bolton, D., The computation of equivalent potential
            # temperature, Monthly Weather Report, 108, 1046-1053, 1980.
            # equation (10)
            tc = t - 273.15
            e_sat[idx_liq] = 6.112 * numpy.exp(17.67 * tc[idx_liq] / (tc[idx_liq] + 243.5))

        # THIS CURVE LOOKS WRONG!
        #         elif liquid == 'Fukuta':
        #             # Source: Fukuta, N. and C. M. Gramada, Vapor pressure
        #             # measurement of supercooled water, J. Atmos. Sci., 60,
        #             # 1871-1875, 2003.
        #             # This paper does not give a vapor pressure formulation,
        #             # but rather a correction over the Smithsonian Tables.
        #             # Thus calculate the table value first, then use the
        #             # correction to get to the measured value.
        #             ts    = 373.16       # steam point temperature in K
        #             ews   = 1013.246     # saturation pressure at steam point
        #                                  # temperature, normal atmosphere

        #             e_sat[idx_liq] = 10.**(-7.90298*(ts/t[idx_liq]-1.)
        #                                    + 5.02808 * numpy.log10(ts/t[idx_liq])
        #                                    - 1.3816E-7 * (10.**(11.344*(1.-t[idx_liq]/ts))-1.)
        #                                    + 8.1328E-3*(10.**(-3.49149*(ts/t[idx_liq]-1)) -1.)
        #                                    + numpy.log10(ews))

        #             tc = t - 273.15
        #             x = tc[idx_liq] + 19
        #             e_sat[idx_liq] = e_sat[idx_liq] * (0.9992 + 7.113E-4*x
        #                                                - 1.847E-4*x**2.
        #                                                + 1.189E-5*x**3.
        #                                                + 1.130E-7*x**4.
        #                                                - 1.743E-8*x**5.)

        #             e_sat[numpy.where(tc < -39.)] = None

        elif liquid == 'IAPWS':
            # Source: Wagner W. and A. Pruss (2002), The IAPWS
            # formulation 1995 for the thermodynamic properties
            # of ordinary water substance for general and scientific
            # use, J. Phys. Chem. Ref. Data, 31(2), 387-535.
            # This is the 'official' formulation from the International
            # Association for the Properties of Water and Steam
            # The valid range of this formulation is 273.16 <= T <=
            # 647.096 K and is based on the ITS90 temperature scale.
            Tc = 647.096  # K   : Temperature at the critical point
            Pc = 22.064 * 10 ** 4  # hPa : Vapor pressure at the critical point
            nu = (1. - (t[idx_liq] / Tc))
            a1 = -7.85951783
            a2 = 1.84408259
            a3 = -11.7866497
            a4 = 22.6807411
            a5 = -15.9618719
            a6 = 1.80122502
            e_sat[idx_liq] = Pc * numpy.exp(Tc / t[idx_liq] *
                                            (a1 * nu + a2 * nu ** 1.5 + a3 * nu ** 3. +
                                             a4 * nu ** 3.5 + a5 * nu ** 4. + a6 * nu ** 7.5))

        elif liquid == 'MurphyKoop':
            # Source : Murphy and Koop, Review of the vapour pressure
            # of ice and supercooled water for atmospheric applications,
            # Q. J. R. Meteorol. Soc (2005), 131, pp. 1539-1565.
            e_sat[idx_liq] = (numpy.exp(54.842763 - (6763.22 / t[idx_liq]) -
                                        4.210 * numpy.log(t[idx_liq]) +
                                        0.000367 * t[idx_liq] +
                                        numpy.tanh(0.0415 * (t[idx_liq] - 218.8)) *
                                        (53.878 - (1331.22 / t[idx_liq]) -
                                         9.44523 * numpy.log(t[idx_liq]) +
                                         0.014025 * t[idx_liq])) / 100.)

        else:
            raise VapourPressureError(u"Unkown method for computing "
                                      u"the vapour pressure curve over liquid: {}".format(liquid))

    # =============================================================================
    #  Calculate saturation pressure over ice -------------------------------------
    if not force_phase == 'liquid':

        if ice == 'WMO2000':
            ice = 'WMO_Goff'

        if ice == 'IAWPS':
            raise VapourPressureError("IAPWS does not provide a vapour "
                                      "pressure formulation over ice")

        elif ice == 'MartiMauersberger':
            # Source: Marti, J. and K Mauersberger, A survey and new
            # measurements of ice vapor pressure at temperatures between
            # 170 and 250 K, GRL 20, 363-366, 1993.
            e_sat[idx_ice] = (10. ** ((-2663.5 / t[idx_ice]) + 12.537) / 100.)

        elif ice == 'HylandWexler':
            # Source Hyland, R. W. and A. Wexler, Formulations for the
            # Thermodynamic Properties of the saturated Phases of H2O
            # from 173.15K to 473.15K, ASHRAE Trans, 89(2A), 500-519, 1983.
            e_sat[idx_ice] = (numpy.exp((-0.56745359E4 / t[idx_ice]) +
                                        0.63925247E1 -
                                        0.96778430E-2 * t[idx_ice] +
                                        0.62215701E-6 * t[idx_ice] ** 2. +
                                        0.20747825E-8 * t[idx_ice] ** 3. -
                                        0.94840240E-12 * t[idx_ice] ** 4. +
                                        0.41635019E1 * numpy.log(t[idx_ice])) / 100.)

        elif ice == 'GoffGratch':
            # Source: Smithsonian Meteorological Tables, 5th edition,
            # p. 350, 1984

            ei0 = 6.1071  # mbar
            T0 = 273.16  # freezing point in K

            e_sat[idx_ice] = 10. ** (-9.09718 * ((T0 / t[idx_ice]) - 1.) -
                                     3.56654 * numpy.log10((T0 / t[idx_ice])) +
                                     0.876793 * (1. - (t[idx_ice] / T0)) +
                                     numpy.log10(ei0))

        elif ice == 'MagnusTeten':
            # Source: Murray, F. W., On the computation of saturation
            # vapour pressure, J. Appl. Meteorol., 6, 203-204, 1967.
            tc = t - 273.15
            e_sat[idx_ice] = 10. ** (9.5 * tc[idx_ice] / (265.5 + tc[idx_ice]) + 0.7858)

        elif ice == 'Buck_original':
            # Bucks vapor pressure formulation based on Tetens formula
            # Source: Buck, A. L., New equations for computing vapor
            # pressure and enhancement factor, J. Appl. Meteorol., 20,
            # 1527-1532, 1981.
            tc = t - 273.15
            e_sat[idx_ice] = 6.1115 * numpy.exp(22.452 * tc[idx_ice] / (272.55 + tc[idx_ice]))

        elif ice == 'Buck_manual':
            # Bucks vapor pressure formulation based on Tetens formula
            # Source: Buck Research, Model CR-1A Hygrometer Operating
            # Manual, Sep 2001
            tc = t - 273.15
            e_sat[idx_ice] = 6.1115 * numpy.exp((23.036 - (tc[idx_ice] / 333.7)) *
                                                tc[idx_ice] / (279.82 + tc[idx_ice]))

        elif ice == 'WMO_Goff':
            # WMO formulation, which is very similar to Goff Gratch
            # Source: WMO technical regulations, WMO-NO 49, Vol I,
            # General Meteorological Standards and Recommended Practices,
            # Aug 2000, App. A.

            T0 = 273.16  # steam point temperature in K

            e_sat[idx_ice] = 10. ** (-9.09685 * ((T0 / t[idx_ice]) - 1.) -
                                     3.56654 * numpy.log10((T0 / t[idx_ice])) +
                                     0.87682 * (1. - (t[idx_ice] / T0)) + 0.78614)

        elif ice == 'Sonntag':
            # Source: Sonntag, D., Advancements in the field of hygrometry,
            # Meteorol. Z., N. F., 3, 51-66, 1994.
            e_sat[idx_ice] = numpy.exp(-6024.5282 * t[idx_ice] ** (-1.) +
                                       24.721994 +
                                       1.0613868E-2 * t[idx_ice] ** 1. -
                                       1.3198825E-5 * t[idx_ice] ** 2. -
                                       0.49382577 * numpy.log(t[idx_ice]))

        elif ice == 'MurphyKoop':
            # Source: Murphy and Koop, Review of the vapour pressure of ice
            # and supercooled water for atmospheric applications, Q. J. R.
            # Meteorol. Soc (2005), 131, pp. 1539-1565.
            e_sat[idx_ice] = (numpy.exp(9.550426 - (5723.265 / t[idx_ice]) +
                                        3.53068 * numpy.log(t[idx_ice]) -
                                        0.00728332 * t[idx_ice]) / 100.)

        else:
            raise VapourPressureError("Unkown method for computing "
                                      "the vapour pressure curve over ice: {}".format(ice))

    # Convert return value units from hPa to Pa.
    return e_sat * 100. if not input_scalar else e_sat[0] * 100.


def rel_hum(p, t, q, liquid='HylandWexler', ice='GoffGratch',
            force_phase='None'):
    """Compute relative humidity in [%] from pressure, temperature, and
       specific humidity.

    Arguments:
    p -- pressure in [Pa]
    t -- temperature in [K]
    q -- specific humidity in [kg/kg]

    p, t and q can be scalars of NumPy arrays. They just have to either all
    scalars, or all arrays.

    liquid, ice, force_phase -- optional keywords to control the calculation
                                of the saturation vapour pressure; see
                                help of function 'sat_vapour_pressure()' for
                                details.

    Returns: Relative humidity in [%]. Same dimension as input fields.
    """
    if not (numpy.isscalar(p) or numpy.isscalar(t) or numpy.isscalar(q)):
        if not isinstance(p, numpy.ndarray):
            p = numpy.array(p)
        if not isinstance(t, numpy.ndarray):
            t = numpy.array(t)
        if not isinstance(q, numpy.ndarray):
            q = numpy.array(q)

    # Compute mixing ratio w from specific humidiy q.
    w = q / (1. - q)

    # Compute saturation vapour pressure from temperature t.
    e_sat = sat_vapour_pressure(t, liquid=liquid, ice=ice,
                                force_phase=force_phase)

    # Compute saturation mixing ratio from e_sat and pressure p.
    w_sat = 0.622 * e_sat / (p - e_sat)

    # Return the relative humidity, computed from w and w_sat.
    return 100. * w / w_sat


def virt_temp(t, q, method='exact'):
    """
    Compute virtual temperature in [K] from temperature and
    specific humidity.

    Arguments:
    t -- temperature in [K]
    q -- specific humidity in [kg/kg]

    t and q can be scalars of NumPy arrays. They just have to either all
    scalars, or all arrays.

    method -- optional keyword to specify the equation used. Default is
              'exact', which uses
                      Tv = T * (q + 0.622(1-q)) / 0.622,
              'approx' uses
                      Tv = T * (1 + 0.61w),
              with w = q/(1-q) being the water vapour mixing ratio.

              Reference: Wallace&Hobbs 2nd ed., eq. 3.16, 3.59, and 3.60
              (substitute w=q/(1-q) in 3.16 and 3.59 to obtain the exact
              formula).

    Returns: Virtual temperature in [K]. Same dimension as input fields.
    """
    if not (numpy.isscalar(t) or numpy.isscalar(q)):
        if not isinstance(t, numpy.ndarray):
            t = numpy.array(t)
        if not isinstance(q, numpy.ndarray):
            q = numpy.array(q)

    if method == 'exact':
        return t * (q + 0.622 * (1. - q)) / 0.622
    elif method == 'approx':
        # Compute mixing ratio w from specific humidiy q.
        w = q / (1. - q)
        return t * (1. + 0.61 * w)
    else:
        raise TypeError('virtual temperature method not understood')


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


def geop_thickness(p, t, q=None, cumulative=False, axis=-1):
    """
    Compute the geopotential thickness in [m] between the pressure levels
    given by the first and last element in p (= pressure).

    Implements the hypsometric equation (1.18) from Holton, 3rd edition (or
    alternatively (3.24) in Wallace and Hobbs, 2nd ed.).

    Arguments:
    p -- pressure in [Pa]
    t -- temperature in [K]
    q -- [optional] specific humidity in [kg/kg]. If q is given, T will
         be converted to virtual temperature to account for the effects
         of moisture in the air.

    All inputs need to be NumPy arrays with at least 2 elements.

    cumulative -- optional keyword to specify whether the single geopotential
                  thickness between p[0] and p[-1] is returned (False, default),
                  or whether an array containing the thicknesses between
                  p[0] and all other elements in p is returned (True). The
                  latter option is useful for computing the geopotential height
                  of all model levels.

    axis -- see geop_difference().

    Uses geop_difference() for the integral in the above equations.

    Returns: Geopotential thickness between p[0] and p[-1] in [m].
             If 'cumtrapz' is specified, an array of dimension dim(p)-1
             will be returned, in which value n represents the geopotential
             thickness between p[0] and p[n+1].
    """

    # Check whether humidity effects should be considered. If q is specified,
    # simply evaluate the hypsometric equation with virtual temperature instead
    # of absolute temperature (see Wallace and Hobbs, 2nd ed., section 3.2.1).
    if q is None:
        tv = t
    else:
        tv = virt_temp(t, q)

    # Evaluate equation 3.24 in Wallace and Hobbs:
    #     delta Z = -Rd/g0 * int( Tv,  d ln(p), p1, p2 ),
    # where Z denotes the geopotential height, Z = phi/g0.
    return -1. / 9.80665 * geop_difference(p, tv, method='cumtrapz' if cumulative else 'trapz', axis=axis)


def spec_hum_from_pTd(p, td, liquid='HylandWexler'):
    """
    Computes specific humidity in [kg/kg] from pressure and dew point
    temperature.

    Arguments:
    p -- pressure in [Pa]
    td -- dew point temperature in [K]

    p and td can be scalars or NumPy arrays. They just have to either both
    scalars, or both arrays.

    liquid -- optional keyword to specify the method used for computing the
              saturation water wapour. See sat_vapour_pressure() for
              further details.

    Returns: specific humidity in [kg/kg]. Same dimensions as the inputs.

    Method:
      Specific humidity q = w / (1+w), with w = mixing ratio. (Wallace & Hobbs,
      2nd ed., (3.57)). W&H write: 'The dew point [Td] is the temperature at
      which the saturation mixing ratio ws with respect to liquid water becomes
      equal to the actual mixing ratio w.'. Hence we need ws(Td).
      From W&H 3.62, we get ws = 0.622 * es / (p-es). Plugging this into the
      above equation for q and simplifying, we get
                      q = 0.622 * es / (p + es * [0.622-1.])
    """
    # Compute saturation vapour pressure from dew point temperature td.
    e_sat = sat_vapour_pressure(td, liquid=liquid)

    return 0.622 * e_sat / (p + e_sat * (0.622 - 1.))


def dewpoint_approx(p, q, method='Bolton'):
    """
    Computes dew point in [K] from pressure and specific humidity.

    Arguments:
    p -- pressure in [Pa]
    q -- specific humidity in [kg/kg]

    p and q can be scalars or NumPy arrays. They just have to either both
    scalars, or both arrays.

    method -- optional keyword to specify the method used to approximate
              the dew point temperature. Valid values are:

              'Bolton' (default): Use the inversion of Bolton (1980), eq.
              10, to compute dewpoint. According to Bolton, this is accurate
              to 0.03 K in the range 238..308 K. See also Emanuel (1994,
              'Atmospheric Convection', eq. 4.6.2).

    Returns: dew point temperature in [K].
    """
    if not (numpy.isscalar(p) or numpy.isscalar(q)):
        if not isinstance(p, numpy.ndarray):
            p = numpy.array(p)
        if not isinstance(q, numpy.ndarray):
            q = numpy.array(q)

    # Compute mixing ratio w from specific humidiy q.
    w = q / (1. - q)

    # Compute vapour pressure from pressure and mixing ratio
    # (Wallace and Hobbs 2nd ed. eq. 3.59).
    e_q = w / (w + 0.622) * p

    if method == 'Bolton':
        td = (243.5 / ((17.67 / numpy.log(e_q / 100. / 6.112)) - 1)) + 273.15
    else:
        raise ValueError(u"invalid dew point method '{}'".format(method))

    return td


def pot_temp(p, t):
    """
    Computes potential temperature in [K] from pressure and temperature.

    Arguments:
    p -- pressure in [Pa]
    t -- temperature in [K]

    p and t can be scalars of NumPy arrays. They just have to either both
    scalars, or both arrays.

    Returns: potential temperature in [K]. Same dimensions as the inputs.

    Method:
                            theta = T * (p0/p)^(R/cp)
      with p0 = 100000. Pa, R = 287.058 JK-1kg-1, cp = 1004 JK-1kg-1.
    """
    return t * (100000. / p) ** (287.058 / 1004.)


def eqpt_approx(p, t, q, liquid='HylandWexler', ice='GoffGratch',
                force_phase='None'):
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

    Method:
                  theta_e = theta * exp((Lv*w_sat)/(cp*T))
      with theta = potential temperature (see pot_temp()), Lv = 2.25e6 Jkg-1,
      cp = 1004 JK-1kg-1.

    Reference:  Wallace & Hobbs, 2nd ed., eq. 3.71
    """
    # Compute potential temperature from p and t.
    theta = pot_temp(p, t)

    # Compute saturation vapour pressure from temperature t.
    e_sat = sat_vapour_pressure(t, liquid=liquid, ice=ice,
                                force_phase=force_phase)

    # Compute saturation mixing ratio from e_sat and pressure p.
    w_sat = 0.622 * e_sat / (p - e_sat)

    # Latent heat of evaporation.
    Lv = 2.25 * 1.e6
    cp = 1004.

    # Equation 3.71 from Wallace & Hobbs, 2nd ed.
    theta_e = theta * numpy.exp((Lv * w_sat) / (cp * t))
    return theta_e


def omega_to_w(omega, p, t):
    """
    Convert pressure vertical velocity to geometric vertical velocity.

    Arguments:
    omega -- vertical velocity in pressure coordinates, in [Pa/s]
    p -- pressure in [Pa]
    t -- temperature in [K]

    All inputs can be scalars or NumPy arrays.

    Returns the vertical velocity in geometric coordinates, [m/s].

    For all grid points, the pressure vertical velocity in Pa/s is converted
    to m/s via
                    w[m/s] =(approx) omega[Pa/s] / (-g*rho)
                       rho = p / R*T
    with R = 287.058 JK-1kg-1, g = 9.80665 m2s-2.
    (see p.13 of 'Introduction to circulating atmospheres' by Ian N. James).

    NOTE: Please check the resulting values, especially in the upper atmosphere!
    """
    rho = p / (287.058 * t)
    return (omega / (-9.80665 * rho))


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


def flightlevel2pressure_a(flightlevel):
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
    # Make sure flightlevel is a numpy array.
    if not isinstance(flightlevel, numpy.ndarray):
        raise ValueError("argument flightlevel must be a numpy array")

    # Convert flight level (ft) to m (1 ft = 30.48 cm; 1/0.3048m = 3.28...).
    z = flightlevel * 30.48

    if (z > 71000).any():
        raise ValueError("flight level to pressure conversion not "
                         "implemented for z > 71km")

    # g and R are used by all equations below.
    g = 9.80665
    R = 287.058

    # Initialize the return array.
    p = numpy.zeros(flightlevel.shape)

    # ICAO standard atmosphere between 0 and 11 km: T(z=0km) = 15 degC,
    # p(z=0km) = 1013.25 hPa. Temperature gradient is 6.5 K/km.
    indices = z <= 11000.
    z0 = 0
    T0 = 288.15
    gamma = 6.5e-3
    p0 = 101325.

    # Hydrostatic equation with linear temperature gradient.
    p[indices] = p0 * ((T0 - gamma * (z[indices] - z0)) / T0) ** (g / (gamma * R))

    # ICAO standard atmosphere between 11 and 20 km: T(z=11km) = -56.5 degC,
    # p(z=11km) = 226.32 hPa. Temperature is constant at -56.5 degC.
    indices = (z > 11000.) & (z <= 20000.)
    z0 = 11000.
    p0 = 22632.64
    T = 216.65

    # Hydrostatic equation with constant temperature profile.
    p[indices] = p0 * numpy.exp(-g * (z[indices] - z0) / (R * T))

    # ICAO standard atmosphere between 20 and 32 km: T(z=20km) = -56.5 degC,
    # p(z=20km) = 54.75 hPa. Temperature gradient is -1.0 K/km.
    indices = (z > 20000.) & (z <= 32000.)
    z0 = 20000.
    T0 = 216.65
    gamma = -1.0e-3
    p0 = 5475.16

    # Hydrostatic equation with linear temperature gradient.
    p[indices] = p0 * ((T0 - gamma * (z[indices] - z0)) / T0) ** (g / (gamma * R))

    # ICAO standard atmosphere between 32 and 47 km: T(z=32km) = -44.5 degC,
    # p(z=32km) = 8.68019 hPa. Temperature gradient is -2.8 K/km.
    indices = (z > 32000.) & (z <= 47000.)
    z0 = 32000.
    T0 = 228.66
    gamma = -2.8e-3
    p0 = 868.089

    # Hydrostatic equation with linear temperature gradient.
    p[indices] = p0 * ((T0 - gamma * (z[indices] - z0)) / T0) ** (g / (gamma * R))

    # ICAO standard atmosphere between 47 and 51 km: T(z=47km) = -2.5 degC,
    # p(z=47km) = 1.10906 hPa. Temperature is constant at -2.5 degC.
    indices = (z > 47000.) & (z <= 51000)
    z0 = 47000.
    T = 270.65
    p0 = 110.928

    # Hydrostatic equation with constant temperature profile.
    p[indices] = p0 * numpy.exp(-g * (z[indices] - z0) / (R * T))

    # ICAO standard atmosphere between 51 and 71 km: T(z=51km) = -2.5 degC,
    # p(z=71km) = 0.66939 hPa. Temperature gradient is 2.8 K/km.
    indices = (z > 51000.) & (z <= 71000)
    z0 = 51000.
    T0 = 270.65
    gamma = 2.8e-3
    p0 = 66.952

    # Hydrostatic equation with linear temperature gradient.
    p[indices] = p0 * ((T0 - gamma * (z[indices] - z0)) / T0) ** (g / (gamma * R))

    return p


def pressure2flightlevel_a(p):
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
    # Make sure p is a numpy array.
    if not isinstance(p, numpy.ndarray):
        raise ValueError("argument p must be a numpy array")

    # g and R are used by all equations below.
    g = 9.80665
    R = 287.058

    if (p < 3.9591).any():
        raise ValueError("pressure to flight level conversion not "
                         "implemented for z > 71km (p ~ 4 Pa)")

    # Initialize the return array.
    z = numpy.zeros_like(p)

    indices = p < 66.952
    # ICAO standard atmosphere between 51 and 71 km: T(z=51km) = -2.5 degC,
    # p(z=71km) = 0.66939 hPa. Temperature gradient is 2.8 K/km.
    z0 = 51000.
    T0 = 270.65
    gamma = 2.8e-3
    p0 = 66.952

    # Hydrostatic equation with linear temperature gradient.
    z[indices] = z0 + 1. / gamma * (T0 - T0 * numpy.exp(gamma * R / g * numpy.log(p[indices] / p0)))

    # ICAO standard atmosphere between 47 and 51km: T(z=47km) = -2.5 degC,
    # p(z=11km) = 1.10906 hPa. Temperature is constant at -2.5 degC.
    indices = (p >= 66.952) & (p < 110.928)
    z0 = 47000.
    p0 = 110.928
    T = 270.65

    # Hydrostatic equation with constant temperature profile.
    z[indices] = z0 - (R * T) / g * numpy.log(p[indices] / p0)

    # ICAO standard atmosphere between 32 and 47 km: T(z=32km) = -44.5 degC,
    # p(z=20km) = 8.68019 hPa. Temperature gradient is -2.8 K/km.
    indices = (p >= 110.928) & (p < 868.089)
    z0 = 32000.
    T0 = 228.66
    gamma = -2.8e-3
    p0 = 868.089

    # Hydrostatic equation with linear temperature gradient.
    z[indices] = z0 + 1. / gamma * (T0 - T0 * numpy.exp(gamma * R / g * numpy.log(p[indices] / p0)))

    # ICAO standard atmosphere between 20 and 32 km: T(z=20km) = -56.5 degC,
    # p(z=20km) = 54.75 hPa. Temperature gradient is -1.0 K/km.
    indices = (p >= 868.089) & (p < 5474.16)
    z0 = 20000.
    T0 = 216.65
    gamma = -1.0e-3
    p0 = 5475.16

    # Hydrostatic equation with linear temperature gradient.
    z[indices] = z0 + 1. / gamma * (T0 - T0 * numpy.exp(gamma * R / g * numpy.log(p[indices] / p0)))

    # ICAO standard atmosphere between 11 and 20 km: T(z=11km) = -56.5 degC,
    # p(z=11km) = 226.32 hPa. Temperature is constant at -56.5 degC.
    indices = (p >= 5474.16) & (p < 22632.)
    z0 = 11000.
    p0 = 22632.64
    T = 216.65

    # Hydrostatic equation with constant temperature profile.
    z[indices] = z0 - (R * T) / g * numpy.log(p[indices] / p0)

    # ICAO standard atmosphere between 0 and 11 km: T(z=0km) = 15 degC,
    # p(z=0km) = 1013.25 hPa. Temperature gradient is 6.5 K/km.
    indices = p >= 22632.
    z0 = 0
    T0 = 288.15
    gamma = 6.5e-3
    p0 = 101325.

    # Hydrostatic equation with linear temperature gradient.
    z[indices] = 1. / gamma * (T0 - T0 * numpy.exp(gamma * R / g * numpy.log(p[indices] / p0)))

    # Convert from m to flight level (ft).
    flightlevel = z * 0.0328083989502

    return flightlevel


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
