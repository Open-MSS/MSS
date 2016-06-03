"""Collection of thermodynamic functions.

********************************************************************************

   Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
   Copyright 2011-2014 Marc Rautenhaus

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

********************************************************************************

The function sat_vapour_pressure() has been ported from the IDL function
'VaporPressure' by Holger Voemel, available at
              http://cires.colorado.edu/~voemel/vp.html.

AUTHORS:
========

* Marc Rautenhaus (mr)

"""

# related third party imports
import numpy
import pylab
import scipy.integrate

"""
EXCEPTION CLASSES
"""


class VapourPressureError(Exception):
    """Exception class to handle error arising during the computation of vapour
       pressures.
    """
    pass


"""
Vapour Pressure
"""


def sat_vapour_pressure(t, liquid='HylandWexler', ice='GoffGratch',
                        force_phase='None'):
    """Compute the saturation vapour pressure over liquid water and over ice
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
    if force_phase == 'ice':
        idx_ice = ()  # numpy.where(t is not None)
        idx_liq = None
    elif force_phase == 'liquid':
        idx_liq = ()  # numpy.where(t is not None)
        idx_ice = None
    elif force_phase == 'None':
        idx_ice = numpy.where(t <= 273.15)
        idx_liq = numpy.where(t > 273.15)
    else:
        raise VapourPressureError("Cannot recognize the force_phase " \
                                   "keyword: %s (valid are ice, liquid, None)" % force_phase)

    # Initialise output field.
    e_sat = numpy.zeros(numpy.shape(t))

    # =============================================================================
    #  Calculate saturation pressure over liquid water ----------------------------
    if not force_phase == 'ice':

        if liquid == 'MartiMauersberger':
            raise VapourPressureError("Marti and Mauersberger don't " \
                                       "have a vapour pressure curve over liquid.")

        elif liquid == 'HylandWexler':
            # Source: Hyland, R. W. and A. Wexler, Formulations for the
            # Thermodynamic Properties of the saturated Phases of H2O
            # from 173.15K to 473.15K, ASHRAE Trans, 89(2A), 500-519, 1983.
            e_sat[idx_liq] = numpy.exp(-0.58002206E4 / t[idx_liq]
                                       + 0.13914993E1
                                       - 0.48640239E-1 * t[idx_liq]
                                       + 0.41764768E-4 * t[idx_liq] ** 2.
                                       - 0.14452093E-7 * t[idx_liq] ** 3.
                                       + 0.65459673E1 * numpy.log(t[idx_liq])) / 100.

        elif liquid == 'Wexler':
            # Wexler, A., Vapor pressure formulation for ice, Journal of
            # Research of the National Bureau of Standards-A. 81A, 5-20, 1977.
            e_sat[idx_liq] = numpy.exp(-2.9912729E3 * t[idx_liq] ** (-2.)
                                       - 6.0170128E3 * t[idx_liq] ** (-1.)
                                       + 1.887643854E1 * t[idx_liq] ** 0.
                                       - 2.8354721E-2 * t[idx_liq] ** 1.
                                       + 1.7838301E-5 * t[idx_liq] ** 2.
                                       - 8.4150417E-10 * t[idx_liq] ** 3.
                                       - 4.4412543E-13 * t[idx_liq] ** 4.
                                       + 2.858487 * numpy.log(t[idx_liq])) / 100.

        elif liquid == 'GoffGratch':
            # Goff Gratch formulation.
            # Source: Smithsonian Meteorological Tables, 5th edition,
            # p. 350, 1984
            # From original source: Goff and Gratch (1946), p. 107.
            ts = 373.16  # steam point temperature in K
            ews = 1013.246  # saturation pressure at steam point
            # temperature, normal atmosphere
            e_sat[idx_liq] = 10. ** (-7.90298 * (ts / t[idx_liq] - 1.)
                                     + 5.02808 * numpy.log10(ts / t[idx_liq])
                                     - 1.3816E-7 * (10. ** (11.344 * (1. - t[idx_liq] / ts)) - 1.)
                                     + 8.1328E-3 * (10. ** (-3.49149 * (ts / t[idx_liq] - 1)) - 1.)
                                     + numpy.log10(ews))

        elif liquid == 'MagnusTeten':
            # Source: Murray, F. W., On the computation of saturation
            # vapor pressure, J. Appl. Meteorol., 6, 203-204, 1967.
            tc = t - 273.15
            e_sat[idx_liq] = 10. ** (7.5 * (tc[idx_liq]) / (tc[idx_liq] + 237.5)
                                     + 0.7858)

        elif liquid == 'Buck_original':
            # Bucks vapor pressure formulation based on Tetens formula
            # Source: Buck, A. L., New equations for computing vapor
            # pressure and enhancement factor, J. Appl. Meteorol., 20,
            # 1527-1532, 1981.
            tc = t - 273.15
            e_sat[idx_liq] = 6.1121 * numpy.exp(17.502 * tc[idx_liq] /
                                                (240.97 + tc[idx_liq]))

        elif liquid == 'Buck_manual':
            # Bucks vapor pressure formulation based on Tetens formula
            # Source: Buck Research, Model CR-1A Hygrometer Operating
            # Manual, Sep 2001
            tc = t - 273.15
            e_sat[idx_liq] = 6.1121 * numpy.exp((18.678 - (tc[idx_liq]) / 234.5)
                                                * (tc[idx_liq])
                                                / (257.14 + tc[idx_liq]))

        elif liquid == 'WMO_Goff':
            # Intended WMO formulation, originally published by Goff (1957)
            # incorrectly referenced by WMO technical regulations, WMO-NO 49,
            # Vol I, General Meteorological Standards and Recommended
            # Practices, App. A, Corrigendum Aug 2000.
            # and incorrectly referenced by WMO technical regulations,
            # WMO-NO 49, Vol I, General Meteorological Standards and
            # Recommended Practices, App. A, 1988.
            ts = 273.16  # steam point temperature in K
            e_sat[idx_liq] = 10. ** (10.79574 * (1. - ts / t[idx_liq])
                                     - 5.02800 * numpy.log10(t[idx_liq] / ts)
                                     + 1.50475E-4 * (1. - 10. ** (-8.2969 * (t[idx_liq] / ts - 1.)))
                                     + 0.42873E-3 * (10. ** (+4.76955 * (1. - ts / t[idx_liq])) - 1.)
                                     + 0.78614)

        elif liquid == 'WMO2000':
            # WMO formulation, which is very similar to Goff Gratch
            # Source: WMO technical regulations, WMO-NO 49, Vol I,
            # General Meteorological Standards and Recommended Practices,
            # App. A, Corrigendum Aug 2000.
            ts = 273.16  # steam point temperature in K
            e_sat[idx_liq] = 10. ** (10.79574 * (1. - ts / t[idx_liq])
                                     - 5.02800 * numpy.log10(t[idx_liq] / ts)
                                     + 1.50475E-4 * (1. - 10. ** (-8.2969 * (t[idx_liq] / ts - 1.)))
                                     + 0.42873E-3 * (10. ** (-4.76955 * (1. - ts / t[idx_liq])) - 1.)
                                     + 0.78614)

        elif liquid == 'Sonntag':
            # Source: Sonntag, D., Advancements in the field of hygrometry,
            # Meteorol. Z., N. F., 3, 51-66, 1994.
            e_sat[idx_liq] = numpy.exp(-6096.9385 * t[idx_liq] ** (-1.)
                                       + 16.635794
                                       - 2.711193E-2 * t[idx_liq] ** 1.
                                       + 1.673952E-5 * t[idx_liq] ** 2.
                                       + 2.433502 * numpy.log(t[idx_liq]))

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
            nu = (1 - t[idx_liq] / Tc)
            a1 = -7.85951783
            a2 = 1.84408259
            a3 = -11.7866497
            a4 = 22.6807411
            a5 = -15.9618719
            a6 = 1.80122502
            e_sat[idx_liq] = Pc * numpy.exp(Tc / t[idx_liq] *
                                            (a1 * nu + a2 * nu ** 1.5 + a3 * nu ** 3.
                                             + a4 * nu ** 3.5 + a5 * nu ** 4. + a6 * nu ** 7.5))

        elif liquid == 'MurphyKoop':
            # Source : Murphy and Koop, Review of the vapour pressure
            # of ice and supercooled water for atmospheric applications,
            # Q. J. R. Meteorol. Soc (2005), 131, pp. 1539-1565.
            e_sat[idx_liq] = numpy.exp(54.842763 - 6763.22 / t[idx_liq]
                                       - 4.210 * numpy.log(t[idx_liq])
                                       + 0.000367 * t[idx_liq]
                                       + numpy.tanh(0.0415 * (t[idx_liq] - 218.8))
                                       * (53.878 - 1331.22 / t[idx_liq]
                                          - 9.44523 * numpy.log(t[idx_liq])
                                          + 0.014025 * t[idx_liq])) / 100.

        else:
            raise VapourPressureError("Unkown method for computing " \
                                       "the vapour pressure curve over liquid: %s" % liquid)

    # =============================================================================
    #  Calculate saturation pressure over ice -------------------------------------
    if not force_phase == 'liquid':

        if ice == 'WMO2000':
            ice = 'WMO_Goff'

        elif ice == 'IAWPS':
            raise VapourPressureError("IAPWS does not provide a vapour " \
                                       "pressure formulation over ice")

        elif ice == 'MartiMauersberger':
            # Source: Marti, J. and K Mauersberger, A survey and new
            # measurements of ice vapor pressure at temperatures between
            # 170 and 250 K, GRL 20, 363-366, 1993.
            e_sat[idx_ice] = 10. ** (-2663.5 / t[idx_ice] + 12.537) / 100.

        elif ice == 'HylandWexler':
            # Source Hyland, R. W. and A. Wexler, Formulations for the
            # Thermodynamic Properties of the saturated Phases of H2O
            # from 173.15K to 473.15K, ASHRAE Trans, 89(2A), 500-519, 1983.
            e_sat[idx_ice] = numpy.exp(-0.56745359E4 / t[idx_ice]
                                       + 0.63925247E1
                                       - 0.96778430E-2 * t[idx_ice]
                                       + 0.62215701E-6 * t[idx_ice] ** 2.
                                       + 0.20747825E-8 * t[idx_ice] ** 3.
                                       - 0.94840240E-12 * t[idx_ice] ** 4.
                                       + 0.41635019E1 * numpy.log(t[idx_ice])) / 100.

        elif ice == 'GoffGratch':
            # Source: Smithsonian Meteorological Tables, 5th edition,
            # p. 350, 1984

            ei0 = 6.1071  # mbar
            T0 = 273.16  # freezing point in K

            e_sat[idx_ice] = 10. ** (-9.09718 * (T0 / t[idx_ice] - 1.)
                                     - 3.56654 * numpy.log10(T0 / t[idx_ice])
                                     + 0.876793 * (1. - t[idx_ice] / T0)
                                     + numpy.log10(ei0))

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
            e_sat[idx_ice] = 6.1115 * numpy.exp((23.036 - tc[idx_ice] / 333.7)
                                                * tc[idx_ice] / (279.82 + tc[idx_ice]))

        elif ice == 'WMO_Goff':
            # WMO formulation, which is very similar to Goff Gratch
            # Source: WMO technical regulations, WMO-NO 49, Vol I,
            # General Meteorological Standards and Recommended Practices,
            # Aug 2000, App. A.

            T0 = 273.16  # steam point temperature in K

            e_sat[idx_ice] = 10. ** (-9.09685 * (T0 / t[idx_ice] - 1.)
                                     - 3.56654 * numpy.log10(T0 / t[idx_ice])
                                     + 0.87682 * (1. - t[idx_ice] / T0) + 0.78614)

        elif ice == 'Sonntag':
            # Source: Sonntag, D., Advancements in the field of hygrometry,
            # Meteorol. Z., N. F., 3, 51-66, 1994.
            e_sat[idx_ice] = numpy.exp(-6024.5282 * t[idx_ice] ** (-1.)
                                       + 24.721994
                                       + 1.0613868E-2 * t[idx_ice] ** 1.
                                       - 1.3198825E-5 * t[idx_ice] ** 2.
                                       - 0.49382577 * numpy.log(t[idx_ice]))

        elif ice == 'MurphyKoop':
            # Source: Murphy and Koop, Review of the vapour pressure of ice
            # and supercooled water for atmospheric applications, Q. J. R.
            # Meteorol. Soc (2005), 131, pp. 1539-1565.
            e_sat[idx_ice] = numpy.exp(9.550426 - 5723.265 / t[idx_ice]
                                       + 3.53068 * numpy.log(t[idx_ice])
                                       - 0.00728332 * t[idx_ice]) / 100.

        else:
            raise VapourPressureError("Unkown method for computing " \
                                       "the vapour pressure curve over ice: %s" % ice)

    # Convert return value units from hPa to Pa.
    return e_sat * 100. if not input_scalar else e_sat[0] * 100.


def test_vapour_pressure():
    """Make test plots of the saturation vapour pressure curves.
    """

    # Specify a temperature range in [K].
    t = numpy.arange(173, 313, 0.1)

    # Compute saturation pressure over liquid water.
    e_sat_liq_HylandWexler = sat_vapour_pressure(t, liquid='HylandWexler', force_phase='liquid')
    e_sat_liq_GoffGratch = sat_vapour_pressure(t, liquid='GoffGratch', force_phase='liquid')
    e_sat_liq_Wexler = sat_vapour_pressure(t, liquid='Wexler', force_phase='liquid')
    e_sat_liq_MagnusTeten = sat_vapour_pressure(t, liquid='MagnusTeten', force_phase='liquid')
    e_sat_liq_Buck_original = sat_vapour_pressure(t, liquid='Buck_original', force_phase='liquid')
    e_sat_liq_Buck_manual = sat_vapour_pressure(t, liquid='Buck_manual', force_phase='liquid')
    e_sat_liq_WMO_Goff = sat_vapour_pressure(t, liquid='WMO_Goff', force_phase='liquid')
    e_sat_liq_WMO2000 = sat_vapour_pressure(t, liquid='WMO2000', force_phase='liquid')
    e_sat_liq_Sonntag = sat_vapour_pressure(t, liquid='Sonntag', force_phase='liquid')
    e_sat_liq_Bolton = sat_vapour_pressure(t, liquid='Bolton', force_phase='liquid')
    # e_sat_liq_Fukuta = sat_vapour_pressure(t, liquid='Fukuta', force_phase='liquid')
    e_sat_liq_IAPWS = sat_vapour_pressure(t, liquid='IAPWS', force_phase='liquid')
    e_sat_liq_MurphyKoop = sat_vapour_pressure(t, liquid='MurphyKoop', force_phase='liquid')

    # Compute saturation pressure over ice.
    e_sat_ice_MartiMauersberger = sat_vapour_pressure(t, ice='MartiMauersberger', force_phase='ice')
    e_sat_ice_HylandWexler = sat_vapour_pressure(t, ice='HylandWexler', force_phase='ice')
    e_sat_ice_GoffGratch = sat_vapour_pressure(t, ice='GoffGratch', force_phase='ice')
    e_sat_ice_MagnusTeten = sat_vapour_pressure(t, ice='MagnusTeten', force_phase='ice')
    e_sat_ice_Buck_original = sat_vapour_pressure(t, ice='Buck_original', force_phase='ice')
    e_sat_ice_Buck_manual = sat_vapour_pressure(t, ice='Buck_manual', force_phase='ice')
    e_sat_ice_WMO_Goff = sat_vapour_pressure(t, ice='WMO_Goff', force_phase='ice')
    e_sat_ice_Sonntag = sat_vapour_pressure(t, ice='Sonntag', force_phase='ice')
    e_sat_ice_MurphyKoop = sat_vapour_pressure(t, ice='MurphyKoop', force_phase='ice')

    # Plot saturation pressure curves over liquid water.
    pylab.figure()
    pylab.plot(t, e_sat_liq_HylandWexler, 'b-')
    pylab.plot(t, e_sat_liq_GoffGratch, 'b--')
    pylab.plot(t, e_sat_liq_Wexler, 'g-')
    pylab.plot(t, e_sat_liq_MagnusTeten, 'g--')
    pylab.plot(t, e_sat_liq_Buck_original, 'r-')
    pylab.plot(t, e_sat_liq_Buck_manual, 'r-.')
    pylab.plot(t, e_sat_liq_WMO_Goff, 'c-')
    pylab.plot(t, e_sat_liq_WMO2000, 'c:')
    pylab.plot(t, e_sat_liq_Sonntag, 'm-')
    pylab.plot(t, e_sat_liq_Bolton, 'm:')
    # pylab.plot(t, e_sat_liq_Fukuta, 'k-')
    pylab.plot(t, e_sat_liq_IAPWS, 'k-.')
    pylab.plot(t, e_sat_liq_MurphyKoop, 'k:')
    pylab.title("Saturation vapour pressure curves over liquid water.")
    pylab.xlabel("Temperature [K]")
    pylab.ylabel("Pressure [Pa]")

    # Plot saturation pressure curves over ice.
    pylab.figure()
    pylab.plot(t, e_sat_ice_MartiMauersberger, 'b-')
    pylab.plot(t, e_sat_ice_HylandWexler, 'b--')
    pylab.plot(t, e_sat_ice_GoffGratch, 'g-')
    pylab.plot(t, e_sat_ice_MagnusTeten, 'g:')
    pylab.plot(t, e_sat_ice_Buck_original, 'r-')
    pylab.plot(t, e_sat_ice_Buck_manual, 'r-.')
    pylab.plot(t, e_sat_ice_WMO_Goff, 'c-')
    pylab.plot(t, e_sat_ice_Sonntag, 'm-')
    pylab.plot(t, e_sat_ice_MurphyKoop, 'k-')
    pylab.title("Saturation vapour pressure curves over ice.")
    pylab.xlabel("Temperature [K]")
    pylab.ylabel("Pressure [Pa]")

    # Plot deviation in [%] of the liquid water saturation curves to the
    # GoffGratch curve.
    def deviation_from_GoffGratch_liquid(e_sat):
        return 100. * (e_sat - e_sat_liq_GoffGratch) / e_sat_liq_GoffGratch

    pylab.figure()
    pylab.plot(t, deviation_from_GoffGratch_liquid(e_sat_liq_HylandWexler), 'b-')
    pylab.plot(t, deviation_from_GoffGratch_liquid(e_sat_liq_GoffGratch), 'b--')
    pylab.plot(t, deviation_from_GoffGratch_liquid(e_sat_liq_Wexler), 'g-')
    pylab.plot(t, deviation_from_GoffGratch_liquid(e_sat_liq_MagnusTeten), 'g--')
    pylab.plot(t, deviation_from_GoffGratch_liquid(e_sat_liq_Buck_original), 'r-')
    pylab.plot(t, deviation_from_GoffGratch_liquid(e_sat_liq_Buck_manual), 'r-.')
    pylab.plot(t, deviation_from_GoffGratch_liquid(e_sat_liq_WMO_Goff), 'c-')
    pylab.plot(t, deviation_from_GoffGratch_liquid(e_sat_liq_WMO2000), 'c:')
    pylab.plot(t, deviation_from_GoffGratch_liquid(e_sat_liq_Sonntag), 'm-')
    pylab.plot(t, deviation_from_GoffGratch_liquid(e_sat_liq_Bolton), 'm:')
    # pylab.plot(t, deviation_from_GoffGratch_liquid(e_sat_liq_Fukuta), 'k-')
    pylab.plot(t, deviation_from_GoffGratch_liquid(e_sat_liq_IAPWS), 'k-.')
    pylab.plot(t, deviation_from_GoffGratch_liquid(e_sat_liq_MurphyKoop), 'k:')
    pylab.title("Saturation vapour pressure curves over liquid water.")
    pylab.xlabel("Temperature [K]")
    pylab.ylabel("Deviation from Goff Gratch [%]")

    # Plot deviation in [%] of the ice water saturation curves to the
    # GoffGratch curve.
    def deviation_from_GoffGratch_ice(e_sat):
        return 100. * (e_sat - e_sat_ice_GoffGratch) / e_sat_ice_GoffGratch

    pylab.figure()
    pylab.plot(t, deviation_from_GoffGratch_ice(e_sat_ice_MartiMauersberger), 'b-')
    pylab.plot(t, deviation_from_GoffGratch_ice(e_sat_ice_HylandWexler), 'b--')
    pylab.plot(t, deviation_from_GoffGratch_ice(e_sat_ice_GoffGratch), 'g-')
    pylab.plot(t, deviation_from_GoffGratch_ice(e_sat_ice_MagnusTeten), 'g:')
    pylab.plot(t, deviation_from_GoffGratch_ice(e_sat_ice_Buck_original), 'r-')
    pylab.plot(t, deviation_from_GoffGratch_ice(e_sat_ice_Buck_manual), 'r-.')
    pylab.plot(t, deviation_from_GoffGratch_ice(e_sat_ice_WMO_Goff), 'c-')
    pylab.plot(t, deviation_from_GoffGratch_ice(e_sat_ice_Sonntag), 'm-')
    pylab.plot(t, deviation_from_GoffGratch_ice(e_sat_ice_MurphyKoop), 'k-')
    pylab.title("Saturation vapour pressure curves over ice.")
    pylab.xlabel("Temperature [K]")
    pylab.ylabel("Deviation from Goff Gratch [%]")


"""
Relative Humidity
"""


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
        if type(p) is not numpy.ndarray:
            p = numpy.array(p)
        if type(t) is not numpy.ndarray:
            t = numpy.array(t)
        if type(q) is not numpy.ndarray:
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


"""
Virtual Temperature
"""


def virt_temp(t, q, method='exact'):
    """Compute virtual temperature in [K] from temperature and
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
        if type(t) is not numpy.ndarray:
            t = numpy.array(t)
        if type(q) is not numpy.ndarray:
            q = numpy.array(q)

    if method == 'exact':
        return t * (q + 0.622 * (1. - q)) / 0.622
    elif method == 'approx':
        # Compute mixing ratio w from specific humidiy q.
        w = q / (1. - q)
        return t * (1. + 0.61 * w)
    else:
        raise TypeError('virtual temperature method not understood')


"""
Geopotential
"""


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
    """Compute the geopotential thickness in [m] between the pressure levels
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


def test_geop_thickness():
    """Test geop_thickness() with some values from the 1976 US standard
       atmosphere.
    """
    # Define some std. atmosphere values (height in m, T in K, p in Pa).
    std_atm_76 = numpy.array([[0, 288.15, 101325],
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
    print p
    t = std_atm_76[:, 1]
    print t

    # Compute geopotential difference and layer thickness. Layer thickness
    # should be similar to the actual altitude given above.
    geop = geop_difference(p, t, method='cumtrapz')
    print geop
    geop = geop_thickness(p, t, cumulative=True)
    print geop


"""
Specific Humidity
"""


def spec_hum_from_pTd(p, td, liquid='HylandWexler'):
    """Computes specific humidity in [kg/kg] from pressure and dew point
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


"""
Dew Point
"""


def dewpoint_approx(p, q, method='Bolton'):
    """Computes dew point in [K] from pressure and specific humidity.

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
        if type(p) is not numpy.ndarray:
            p = numpy.array(p)
        if type(q) is not numpy.ndarray:
            q = numpy.array(q)

    # Compute mixing ratio w from specific humidiy q.
    w = q / (1. - q)

    # Compute vapour pressure from pressure and mixing ratio
    # (Wallace and Hobbs 2nd ed. eq. 3.59).
    e_q = w / (w + 0.622) * p

    if method == 'Bolton':
        td = 243.5 / (17.67 / numpy.log(e_q / 100. / 6.112) - 1) + 273.15
    else:
        raise ValueError("invalid dew point method <%s>" % method)

    return td


"""
Potential Temperature
"""


def pot_temp(p, t):
    """Computes potential temperature in [K] from pressure and temperature.

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
    """Computes equivalent potential temperature in [K] from pressure,
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
    """Convert pressure vertical velocity to geometric vertical velocity.

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
    return omega / (-9.80665 * rho)


"""
Flight Level / Pressure Conversion
"""


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
    z = flightlevel * 100. / 3.28083989501

    # g and R are used by all equations below.
    g = 9.80665
    R = 287.058

    if z <= 11000.:
        # ICAO standard atmosphere between 0 and 11 km: T(z=0km) = 15 degC,
        # p(z=0km) = 1013.25 hPa. Temperature gradient is 6.5 K/km.
        z0 = 0
        T0 = 288.15
        gamma = 6.5e-3
        p0 = 101325.

        # Hydrostatic equation with linear temperature gradient.
        p = p0 * ((T0 - gamma * z) / (T0 - gamma * z0)) ** (g / (gamma * R))
        return p

    elif z <= 20000.:
        # ICAO standard atmosphere between 11 and 20 km: T(z=11km) = -56.5 degC,
        # p(z=11km) = 226.32 hPa. Temperature is constant at -56.5 degC.
        z0 = 11000.
        p0 = 22632.
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
        p0 = 5475.006582501095

        # Hydrostatic equation with linear temperature gradient.
        p = p0 * ((T0 - gamma * z) / (T0 - gamma * z0)) ** (g / (gamma * R))
        return p

    else:
        raise ValueError("flight level to pressure conversion not "
                         "implemented for z > 32km")


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

    if p < 1011.:
        raise ValueError("pressure to flight level conversion not "
                         "implemented for z > 32km (p ~ 10.11 hPa)")

    elif p < 5475.006582501095:
        # ICAO standard atmosphere between 20 and 32 km: T(z=20km) = -56.5 degC,
        # p(z=20km) = 54.75 hPa. Temperature gradient is -1.0 K/km.
        z0 = 20000.
        T0 = 216.65
        gamma = -1.0e-3
        p0 = 5475.006582501095

        # Hydrostatic equation with linear temperature gradient.
        z = 1. / gamma * (T0 - (T0 - gamma * z0) * numpy.exp(gamma * R / g * numpy.log(p / p0)))

    elif p < 22632.:
        # ICAO standard atmosphere between 11 and 20 km: T(z=11km) = -56.5 degC,
        # p(z=11km) = 226.32 hPa. Temperature is constant at -56.5 degC.
        z0 = 11000.
        p0 = 22632.
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
        z = 1. / gamma * (T0 - (T0 - gamma * z0) * numpy.exp(gamma * R / g * numpy.log(p / p0)))

    # Convert from m to flight level (ft).
    flightlevel = z * 3.28083989501 / 100.

    return flightlevel


def flightlevel2pressure_a(flightlevel):
    """Conversion of flight level (given in hft) to pressure (Pa) with
       hydrostatic equation, according to the profile of the ICAO
       standard atmosphere.

    Array version, the argument "p" must be a numpy array.

    Reference:
        For example, H. Kraus, Die Atmosphaere der Erde, Springer, 2001,
        470pp., Sections II.1.4. and II.6.1.2.

    Arguments:
        flightlevel -- numpy array of flight level in hft
    Returns:
        static pressure (Pa)
    """
    # Make sure flightlevel is a numpy array.
    if type(flightlevel) is not numpy.ndarray:
        raise ValueError("argument flightlevel must be a numpy array")

    # Convert flight level (ft) to m (1 ft = 30.48 cm; 1/0.3048m = 3.28...).
    z = flightlevel * 100. / 3.28083989501

    if (z > 32000.).any():
        raise ValueError("flight level to pressure conversion not "
                         "implemented for z > 32km")

    # g and R are used by all equations below.
    g = 9.80665
    R = 287.058

    # Initialize the return array.
    p = numpy.zeros(flightlevel.shape)

    # ICAO standard atmosphere between 0 and 11 km: T(z=0km) = 15 degC,
    # p(z=0km) = 1013.25 hPa. Temperature gradient is 6.5 K/km.
    indices = numpy.where(z <= 11000.)
    # print "0..11km", indices
    z0 = 0
    T0 = 288.15
    gamma = 6.5e-3
    p0 = 101325.

    # Hydrostatic equation with linear temperature gradient.
    p[indices] = p0 * ((T0 - gamma * z[indices]) / (T0 - gamma * z0)) ** (g / (gamma * R))

    # ICAO standard atmosphere between 11 and 20 km: T(z=11km) = -56.5 degC,
    # p(z=11km) = 226.32 hPa. Temperature is constant at -56.5 degC.
    indices = numpy.where((z > 11000.) & (z <= 20000.))
    # print "11..20km", indices
    z0 = 11000.
    p0 = 22632.
    T = 216.65

    # Hydrostatic equation with constant temperature profile.
    p[indices] = p0 * numpy.exp(-g * (z[indices] - z0) / (R * T))

    # ICAO standard atmosphere between 20 and 32 km: T(z=20km) = -56.5 degC,
    # p(z=20km) = 54.75 hPa. Temperature gradient is -1.0 K/km.
    indices = numpy.where((z > 20000.) & (z <= 32000.))
    # print "20..32km", indices
    z0 = 20000.
    T0 = 216.65
    gamma = -1.0e-3
    p0 = 5475.006582501095

    # Hydrostatic equation with linear temperature gradient.
    p[indices] = p0 * ((T0 - gamma * z[indices]) / (T0 - gamma * z0)) ** (g / (gamma * R))

    return p


def pressure2flightlevel_a(p, fake_above_32km=False):
    """Conversion of pressure (Pa) to flight level (hft) with
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
    if type(p) is not numpy.ndarray:
        raise ValueError("argument p must be a numpy array")

    # g and R are used by all equations below.
    g = 9.80665
    R = 287.058

    if (p < 1011.).any() and not fake_above_32km:
        raise ValueError("pressure to flight level conversion not "
                         "implemented for z > 32km (p ~ 10.11 hPa)")

    # Initialize the return array.
    z = numpy.zeros(p.shape)

    # ICAO standard atmosphere between 20 and 32 km: T(z=20km) = -56.5 degC,
    # p(z=20km) = 54.75 hPa. Temperature gradient is -1.0 K/km.
    indices = numpy.where(p < 5475.006582501095)
    z0 = 20000.
    T0 = 216.65
    gamma = -1.0e-3
    p0 = 5475.006582501095

    # Hydrostatic equation with linear temperature gradient.
    z[indices] = 1. / gamma * (T0 - (T0 - gamma * z0) * numpy.exp(gamma * R / g * numpy.log(p[indices] / p0)))

    # ICAO standard atmosphere between 11 and 20 km: T(z=11km) = -56.5 degC,
    # p(z=11km) = 226.32 hPa. Temperature is constant at -56.5 degC.
    indices = numpy.where((p >= 5475.006582501095) & (p < 22632.))
    z0 = 11000.
    p0 = 22632.
    T = 216.65

    # Hydrostatic equation with constant temperature profile.
    z[indices] = z0 - (R * T) / g * numpy.log(p[indices] / p0)

    # ICAO standard atmosphere between 0 and 11 km: T(z=0km) = 15 degC,
    # p(z=0km) = 1013.25 hPa. Temperature gradient is 6.5 K/km.
    indices = numpy.where(p >= 22632.)
    z0 = 0
    T0 = 288.15
    gamma = 6.5e-3
    p0 = 101325.

    # Hydrostatic equation with linear temperature gradient.
    z[indices] = 1. / gamma * (T0 - (T0 - gamma * z0) * numpy.exp(gamma * R / g * numpy.log(p[indices] / p0)))

    # Convert from m to flight level (ft).
    flightlevel = z * 3.28083989501 / 100.

    return flightlevel


def isa_temperature(flightlevel):
    """International standard atmosphere temperature at the given flight level.

    Reference:
        For example, H. Kraus, Die Atmosphaere der Erde, Springer, 2001,
        470pp., Sections II.1.4. and II.6.1.2.

    Arguments:
        flightlevel -- flight level in hft
    Returns:
        temperature (K)
    """
    # Convert flight level (ft) to m (1 ft = 30.48 cm; 1/0.3048m = 3.28...).
    z = flightlevel * 100. / 3.28083989501

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

    else:
        raise ValueError("ISA temperature from flight level not "
                         "implemented for z > 32km")


"""
Schmidt/Appleman
"""


def schmidt_appleman_tdiff(p_Pa, T_K, rh_01):
    """Schmidt/Appleman criterion folded by relative humidity of 80%.

    Reference: U. Schumann, "On conditions for contrail formation from
        aircraft exhausts", Met.Z. (1996) 4-23.

    Arguments:
    p_Pa  -- pressure in Pa
    T_K   -- temperature in K
    rh_01 -- relative humidity mapped to 0..1

    Returns:
    Temperature difference T_K - Schm./Appl.Threshold. Of interest are
    return values below 0.

    NOTE: The current implementation returns a value of 1. if relative
    humidity is below 80% (as used, e.g. during CONCERT and ML-Cirrus).

    NOTE: This function is a port of U. Schumann's FORTRAN77 function in
    the old Metview3 scripts.

    mr/18Mar2014
    """

    # Original comments from the FORTRAN program are in CAPITAL LETTERS:

    # PROGRAMMED BY:
    # ULRICH SCHUMANN; DLR, INSTITUT FUER PHYSIK DER ATMOSPHAERE
    # OBERPFAFFENHOFEN, POSTFACH 1116, 82230 WESSLING, GERMANY
    # REFERENCE: U.SCHUMANN,
    #     ON CONDITIONS FOR CONTRAIL FORMATION FROM AIRCRAFT EXHAUSTS.
    #     METEOROL. Z., 5 (1996) 4-23.
    # VERSION OF FEBRUARY 7, 2000.

    # G IN PA/K, SLOPE OF MIXING LINE,
    #     G=EI*CP*R1*P/(Q*(1.-ETA)*R0)
    # WITH  DATA R1/461.5/,R0/287.04/,CP/1004./
    #     EI = EMISSION INDEX OF WATER VAPOR, E.G. 1.23 FOR KEROSENE
    #     Q =  COMBUSTION HEAT, E.G. Q = 43.2E6 FOR KEROSENE
    #     ETA= OVERALL EFFICIENCY, E.G. 0.3 FOR A SUBSONIC JET AIRCRAFT
    #     P =  AMBIENT PRESSURE IN PA

    EI = 1.23
    CP = 1004.
    R0 = 287.04
    R1 = 461.5
    Q = 43.2e6
    ETA = 0.3

    G = EI * CP * R1 * p_Pa / (Q * (1. - ETA) * R0)

    # SATURATION PRESSURE FROM SONNTAG, TT IN K, PSAT IN PA
    #    METEOROL. Z., 3 (1994) 51-66.
    def PSAT(TT):
        return 100. * numpy.exp(
            -6096.9385 / TT + 16.635794 - 2.711193E-2 * TT + 1.673952E-5 * TT * TT + 2.433502 * numpy.log(TT))

    def DPSAT(TT):
        return (PSAT(TT + 1.) - PSAT(TT - 1.)) / 2.

    def DDPSAT(TT):
        return PSAT(TT + 1.) + PSAT(TT - 1.) - 2. * PSAT(TT)

    if (rh_01 < 0.):
        rh_01 = 0.

    # TLM: THRESHOLD TEMPERATURE FOR U=1., IN K
    # COMPUTATION OF TLM BY APPROXIMATION ACCORDING TO SCHUMANN (1996)
    TLM = 273.15 - 46.46 + 9.43 * numpy.log(G - 0.053) + 0.720 * (numpy.log(G - 0.053)) ** 2

    for ITER in range(1, 11):
        F = DPSAT(TLM) - G
        DF = DDPSAT(TLM)
        DX = F / DF
        TLM = TLM - DX
        if (numpy.abs(DX) < 1.E-3):
            break

    # PRINT *,' ITER NOT LARGE ENOUGH FOR TLM, TLM,DX=',TLM,DX

    # TLC: THRESHOLD TEMPERATURE FOR GIVEN U, IN K
    # COMPUTATION OF TLC BY NEWTON ITERATION
    if (rh_01 < 1.E-6):
        TLC = TLM - PSAT(TLM) / G
    else:
        TLC = TLM
        if (rh_01 < 0.99999):
            EM = PSAT(TLM)
            T0 = TLM - EM / G
            E0 = PSAT(T0)
            C = 1. - numpy.sqrt(1. + 4. * rh_01 * E0 / ((1. - rh_01) * EM))
            TLC = TLM + (1. - rh_01) * (EM * (TLM - T0) / (2. * rh_01 * E0)) * C
            for ITER in range(1, 11):
                DELT = TLM - TLC
                F = PSAT(TLM) - G * DELT - rh_01 * PSAT(TLC)
                DF = G - rh_01 * DPSAT(TLC)
                DX = F / DF
                TLC = TLC - DX
                if (numpy.abs(DX) < 1.E-3):
                    break

    # Filter values with rel.hum. < 80%.
    TMKDIFF = 1.
    if (rh_01 > 0.8):
        TMKDIFF = T_K - TLC

    return TMKDIFF


def schmidt_appleman_tdiff_q(p, t, q, liquid='HylandWexler', ice='GoffGratch',
                             force_phase='None'):
    """Same as schmidt_appleman_tdiff(), but with specific humidity q
    instead of relative humidity.

    Arguments for q, liquid, ice, force_phase the same as for rel_hum().
    """
    rh01 = rel_hum(p, t, q, liquid=liquid, ice=ice, force_phase=force_phase)
    rh01 /= 100.
    return schmidt_appleman_tdiff(p, t, rh01)


def schmidt_appleman_tdiff_q_a_slow(p, t, q, liquid='HylandWexler', ice='GoffGratch',
                                    force_phase='None'):
    """Same as schmidt_appleman_tdiff_q(), but takes arrays as arguments.

    NOTE: This is the slow version, using Python loops to process the
    array elements.  Use schmidt_appleman_tdiff_q_a() instead.
    """
    rh01 = rel_hum(p, t, q, liquid=liquid, ice=ice, force_phase=force_phase)
    rh01 /= 100.

    # Remember array shape.
    shp = p.shape

    # Transform arrays into 1D fields.
    p_r = p.ravel()
    t_r = t.ravel()
    rh01_r = rh01.ravel()

    # Compute Schmidt-Applement threshold difference for each value.
    result = numpy.zeros(p_r.shape)
    for i in range(len(p_r)):
        result[i] = schmidt_appleman_tdiff(p_r[i], t_r[i], rh01_r[i])

    # Return the result in the shape of the input arrays.
    result.reshape(shp)
    return result


def schmidt_appleman_tdiff_q_a(p_Pa, T_K, q, liquid='HylandWexler', ice='GoffGratch',
                               force_phase='None'):
    """Same as schmidt_appleman_tdiff_q(), but takes arrays as arguments.
    """

    # For comments see schmidt_appleman_tdiff().
    # ==========================================

    rh_01 = rel_hum(p_Pa, T_K, q, liquid=liquid, ice=ice, force_phase=force_phase)
    rh_01 /= 100.

    EI = 1.23
    CP = 1004.
    R0 = 287.04
    R1 = 461.5
    Q = 43.2e6
    ETA = 0.3

    G = EI * CP * R1 * p_Pa / (Q * (1. - ETA) * R0)

    def PSAT(TT):
        return 100. * numpy.exp(
            -6096.9385 / TT + 16.635794 - 2.711193E-2 * TT + 1.673952E-5 * TT * TT + 2.433502 * numpy.log(TT))

    def DPSAT(TT):
        return (PSAT(TT + 1.) - PSAT(TT - 1.)) / 2.

    def DDPSAT(TT):
        return PSAT(TT + 1.) + PSAT(TT - 1.) - 2. * PSAT(TT)

    rh_01[numpy.where(rh_01 < 0.)] = 0.

    TLM = 273.15 - 46.46 + 9.43 * numpy.log(G - 0.053) + 0.720 * (numpy.log(G - 0.053)) ** 2

    for ITER in range(1, 11):
        F = DPSAT(TLM) - G
        DF = DDPSAT(TLM)
        DX = F / DF
        TLM = TLM - DX
        if (numpy.abs(DX) < 1.E-3).all():
            break

    TLC = numpy.zeros(TLM.shape)

    i_rh_verysmall = numpy.where(rh_01 < 1.E-6)
    TLC[i_rh_verysmall] = TLM[i_rh_verysmall] - PSAT(TLM[i_rh_verysmall]) / G[i_rh_verysmall]

    i_rh = numpy.where(rh_01 >= 1.E-6)
    TLC[i_rh] = TLM[i_rh]

    i_rhLT1 = numpy.where(rh_01 < 0.99999)

    EM = PSAT(TLM[i_rhLT1])
    T0 = TLM[i_rhLT1] - EM / G[i_rhLT1]
    E0 = PSAT(T0)
    C = 1. - numpy.sqrt(1. + 4. * rh_01[i_rhLT1] * E0 / ((1. - rh_01[i_rhLT1]) * EM))
    TLC[i_rhLT1] = TLM[i_rhLT1] + (1. - rh_01[i_rhLT1]) * (EM * (TLM[i_rhLT1] - T0) / (2. * rh_01[i_rhLT1] * E0)) * C
    for ITER in range(1, 11):
        DELT = TLM[i_rhLT1] - TLC[i_rhLT1]
        F = PSAT(TLM[i_rhLT1]) - G[i_rhLT1] * DELT - rh_01[i_rhLT1] * PSAT(TLC[i_rhLT1])
        DF = G[i_rhLT1] - rh_01[i_rhLT1] * DPSAT(TLC[i_rhLT1])
        DX = F / DF
        TLC[i_rhLT1] = TLC[i_rhLT1] - DX
        if (numpy.abs(DX) < 1.E-3).all():
            break

    TMKDIFF = T_K - TLC

    # Filter values with rel.hum. < 80%.
    TMKDIFF[numpy.where(rh_01 < 0.8)] = 1.

    return TMKDIFF
