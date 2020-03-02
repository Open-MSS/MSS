# -*- coding: utf-8 -*-
"""

    mslib.mslib.utils
    ~~~~~~~~~~~~~~~~~

    This module provides functions for the wms server

    This file is part of mss.

    :copyright: Copyright 2016 Joern Ungermann
    :copyright: Copyright 2016-2020 by the mss team, see AUTHORS.
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
import matplotlib
import pint

UR = pint.UnitRegistry()
N_LEVELS = 16


class Targets(object):
    """
    This class defines the names, units, and ranges of supported generic physical
    quantities for vertical and horizontal plots.

    RANGES, UNITS, and THRESHOLDS can be overwritten from outside to determine ranges for plotting in settings.

    Dictionary containing valid value ranges for the different targes. The first level uses CF standard_name as key
    to determine the target. The second level uses either the level type
    ("pl", "ml", ...) as key or "total" for the level-overarching valid range. The level-type has a third level
    using the level altitude as key. The leafs are made of 2-tuples indicating the lowest and the highest valid
    value.
    """
    RANGES = {}

    # List of supported targets using the CF standard_name as unique identifier.
    _TARGETS = [
        "air_temperature",
        "eastward_wind",
        "equivalent_latitude",
        "ertel_potential_vorticity",
        "mean_age_of_air",
        "mole_fraction_of_active_chlorine_in_air",
        "mole_fraction_of_bromine_nitrate_in_air",
        "mole_fraction_of_bromo_methane_in_air",
        "mole_fraction_of_bromochlorodifluoromethane_in_air",
        "mole_fraction_of_bromotrifluoromethane_in_air",
        "mole_fraction_of_carbon_monoxide_in_air",
        "mole_fraction_of_carbon_dioxide_in_air",
        "mole_fraction_of_carbon_tetrachloride_in_air",
        "mole_fraction_of_chlorine_nitrate_in_air",
        "mole_fraction_of_chlorine_dioxide_in_air",
        "mole_fraction_of_cfc11_in_air",
        "mole_fraction_of_cfc113_in_air",
        "mole_fraction_of_cfc12_in_air",
        "mole_fraction_of_ethane_in_air",
        "mole_fraction_of_formaldehyde_in_air",
        "mole_fraction_of_hcfc22_in_air",
        "mole_fraction_of_hydrogen_chloride_in_air",
        "mole_fraction_of_hypobromite_in_air",
        "mole_fraction_of_methane_in_air",
        "mole_fraction_of_nitric_acid_in_air",
        "mole_fraction_of_nitrous_oxide_in_air",
        "mole_fraction_of_nitrogen_dioxide_in_air",
        "mole_fraction_of_nitrogen_monoxide_in_air",
        "mole_fraction_of_ozone_in_air",
        "mole_fraction_of_peroxyacetyl_nitrate_in_air",
        "mole_fraction_of_sulfur_dioxide_in_air",
        "mole_fraction_of_water_vapor_in_air",

        "northward_wind",
        "square_of_brunt_vaisala_frequency_in_air",
        "surface_origin_tracer_from_india_and_china",
        "surface_origin_tracer_from_southeast_asia",
        "surface_origin_tracer_from_east_china",
        "surface_origin_tracer_from_north_india",
        "surface_origin_tracer_from_south_india",
        "surface_origin_tracer_from_north_africa",
        "median_of_age_of_air_spectrum",
        "fraction_below_6months_of_age_of_air_spectrum",
        "fraction_above_24months_of_age_of_air_spectrum",
        "cloud_ice_mixing_ratio",
        "number_concentration_of_ice_crystals_in_air",
        "mean_mass_radius_of_cloud_ice_crystals",
        "maximum_pressure_on_backtrajectory",
    ]

    UNITS = {
        "air_temperature": ("K", 1),
        "eastward_wind": ("1/ms", 1),
        "equivalent_latitude": ("degree N", 1),
        "ertel_potential_vorticity": ("PVU", 1),
        "gravity_wave_temperature_perturbation": ("K", 1),
        "mean_age_of_air": ("month", 1),
        "median_of_age_of_air_spectrum": ("month", 1),
        "northward_wind": ("1/ms", 1),
        "square_of_brunt_vaisala_frequency_in_air": ("1/s²", 1),
        "tropopause_altitude": ("km", 1),
        "cloud_ice_mixing_ratio": ("ppmv", 1),
        "number_concentration_of_ice_crystals_in_air": ("1/cm³", 1),
        "mean_mass_radius_of_cloud_ice_crystals": ("µm", 1),
        "maximum_pressure_on_backtrajectory": ("hPa", 1),
        "maximum_relative_humidity_wrt_ice_on_backtrajectory": ("%", 1),
    }

    # The THRESHOLDS are used to determine a single colourmap suitable for all plotting purposes (that is vertical
    # and horizontal on all levels. The given thresholds have been manually designed.
    THRESHOLDS = {
        "ertel_potential_vorticity":
            (-1, 0, 1, 2, 4, 6, 9, 12, 15, 25, 40),
        "mole_fraction_of_carbon_monoxide_in_air":
            (10e-9, 20e-9, 30e-9, 40e-9, 50e-9, 60e-9, 70e-9, 80e-9, 90e-9, 100e-9, 300e-9),
        "mole_fraction_of_nitric_acid_in_air":
            (0e-9, 0.3e-9, 0.5e-9, 0.7e-9, 0.9e-9, 1.1e-9, 1.3e-9, 1.5e-9, 2e-9, 4e-9),
        "mole_fraction_of_ozone_in_air":
            (0e-6, 0.02e-6, 0.03e-6, 0.04e-6, 0.06e-6, 0.1e-6, 0.16e-6, 0.25e-6, 0.45e-6, 1e-6, 4e-6),
        "mole_fraction_of_peroxyacetyl_nitrate_in_air":
            (0, 50e-12, 70e-12, 100e-12, 150e-12, 200e-12, 250e-12, 300e-12, 350e-12, 400e-12, 450e-12, 500e-12),
        "mole_fraction_of_water_vapor_in_air":
            (0, 3e-6, 4e-6, 6e-6, 10e-6, 16e-6, 60e-6, 150e-6, 500e-6, 1000e-6),
    }

    for standard_name in _TARGETS:
        if standard_name.startswith("surface_origin_tracer_from_"):
            UNITS[standard_name] = ("%", 1)

    for standard_name in [
            "mole_fraction_of_carbon_dioxide_in_air",
            "mole_fraction_of_methane_in_air",
            "mole_fraction_of_ozone_in_air",
            "mole_fraction_of_water_vapor_in_air",
    ]:
        UNITS[standard_name] = ("µmol/mol", 1e6)

    for standard_name in [
            "mole_fraction_of_active_chlorine_in_air",
            "mole_fraction_of_carbon_monoxide_in_air",
            "mole_fraction_of_chlorine_nitrate_in_air",
            "mole_fraction_of_hydrogen_chloride_in_air",
            "mole_fraction_of_nitric_acid_in_air",
            "mole_fraction_of_nitrous_oxide_in_air",
    ]:
        UNITS[standard_name] = ("nmol/mol", 1e9)

    for standard_name in [
            "mole_fraction_of_bromine_nitrate_in_air",
            "mole_fraction_of_bromo_methane_in_air",
            "mole_fraction_of_bromochlorodifluoromethane_in_air",
            "mole_fraction_of_bromotrifluoromethane_in_air",
            "mole_fraction_of_carbon_tetrachloride_in_air",
            "mole_fraction_of_chlorine_dioxide_in_air",
            "mole_fraction_of_cfc11_in_air",
            "mole_fraction_of_cfc12_in_air",
            "mole_fraction_of_cfc113_in_air",
            "mole_fraction_of_hcfc22_in_air",
            "mole_fraction_of_ethane_in_air",
            "mole_fraction_of_formaldehyde_in_air",
            "mole_fraction_of_hypobromite_in_air",
            "mole_fraction_of_nitrogen_dioxide_in_air",
            "mole_fraction_of_nitrogen_monoxide_in_air",
            "mole_fraction_of_peroxyacetyl_nitrate_in_air",
            "mole_fraction_of_sulfur_dioxide_in_air",
    ]:
        UNITS[standard_name] = ("pmol/mol", 1e12)

    for standard_name in [
            "fraction_below_6months_of_age_of_air_spectrum",
            "fraction_above_24months_of_age_of_air_spectrum",
    ]:
        UNITS[standard_name] = ("%", 100)

    TITLES = {
        "ertel_potential_vorticity": "PV",
        "square_of_brunt_vaisala_frequency_in_air": "N²",
        "gravity_wave_temperature_perturbation": "Gravity Wave Temperature Residual",
        "tropopause_altitude": "Thermal Tropopause",
    }
    for standard_name in _TARGETS:
        if standard_name.startswith("mole_fraction_of_") and standard_name.endswith("_in_air"):
            TITLES[standard_name] = standard_name[17:-7].replace("_", " ")
        elif standard_name not in TITLES:
            TITLES[standard_name] = standard_name.replace("_", " ")

    @staticmethod
    def get_targets():
        """
        List to determine what targets are supported.
        Returns:
        list of supported targets
        """
        return Targets._TARGETS

    @staticmethod
    def get_unit(standard_name):
        """
        Returns unit type and scaling factor for target.
        Args:
            standard_name: string of CF standard_name

        Returns:
            Tuple of string describing the unit and scaling factor to apply on data.

        """
        return Targets.UNITS.get(standard_name, (None, 1))

    @staticmethod
    def get_range(standard_name, level="total", typ=None):
        """
        Returns valid range of values for target at given level
        Args:
            standard_name: string of CF standard_name
            level (optional): horizontal level of data
            type (optional): type of data (pl, ml, tl, ...)

        Returns:
            Tuple of lowest and highest valid value
        """
        if standard_name in Targets.RANGES:
            if typ in Targets.RANGES[standard_name]:
                if level in Targets.RANGES[standard_name][typ]:
                    return [_x * Targets.get_unit(standard_name)[1]
                            for _x in Targets.RANGES[standard_name][typ][level]]
                elif level is None:
                    return 0, 0
            if level == "total" and "total" in Targets.RANGES[standard_name]:
                return [_x * Targets.get_unit(standard_name)[1]
                        for _x in Targets.RANGES[standard_name]["total"]]
        if standard_name.startswith("surface_origin_tracer_from_"):
            return 0, 100
        return None, None

    @staticmethod
    def get_thresholds(standard_name, level=None, type=None):
        """
        Returns a list of meaningful values for a BoundaryNorm for plotting.
        Args:
            standard_name: string of CF standard_name
            level (optional): horizontal level of data
            type (optional): type of data (pl, ml, tl, ...)

        Returns:
            Tuple of threshold values to be supplied to a BoundaryNorm.
        """
        try:
            return [_x * Targets.get_unit(standard_name)[1] for _x in Targets.THRESHOLDS[standard_name]]
        except KeyError:
            return None


def get_log_levels(cmin, cmax, levels=N_LEVELS):
    """
    Returns 'levels' levels in a lgarithmic spacing. Takes care of ranges crossing zero and starting/ending at zero.
    Args:
        cmin: minimum value
        cmax: maximum value
        levels (optional): number of levels to be generated

    Returns:
        numpy array of values
    """
    assert cmin < cmax
    if cmin >= 0:
        if cmin == 0:
            cmin = 0.001 * cmax
        clev = np.exp(np.linspace(np.log(cmin), np.log(cmax), levels))
    elif cmax <= 0:
        if cmax == 0:
            cmax = 0.001 * cmin
        clev = -np.exp(np.linspace(np.log(-cmin), np.log(-cmax), levels))
    else:
        delta = cmax - cmin
        clevlo = -np.exp(
            np.linspace(np.log(-cmin), np.log(max(-cmin, cmax) * 0.001),
                        max(2, 1 + int(levels * -cmin / delta))))
        clevhi = np.exp(np.linspace(np.log(max(-cmin, cmax) * 0.001),
                                    np.log(cmax), max(2, 1 + int(levels * cmax / delta))))
        clev = np.asarray(list(clevlo) + list(clevhi))
    return clev


def get_style_parameters(dataname, style, cmin, cmax, data):
    if cmin is None or cmax is None:
        try:
            cmin, cmax = data.min(), data.max()
        except ValueError:
            cmin, cmax = 0, 1
        if 0 < cmin < 0.05 * cmax:
            cmin = 0.
    cmap = matplotlib.pyplot.cm.rainbow
    ticks = None

    if any(isinstance(_x, np.ma.core.MaskedConstant) for _x in (cmin, cmax)):
        cmin, cmax = 0, 1

    if style == "default":
        clev = np.linspace(cmin, cmax, 16)
        norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    elif style == "auto":
        cmin_p = data.min()
        cmax_p = data.max()
        if not any([isinstance(_x, np.ma.core.MaskedConstant) for _x in (cmin_p, cmax_p)]):
            cmin, cmax = cmin_p, cmax_p
        if cmin == cmax:
            cmin, cmax = 0, 1
        if 0 < cmin < 0.05 * cmax:
            cmin = 0.
        clev = np.linspace(cmin, cmax, 16)
        norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    elif style == "log":
        clev = get_log_levels(cmin, cmax, 16)
        norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    elif style == "autolog":
        cmin_p = data.min()
        cmax_p = data.max()
        if not any([isinstance(_x, np.ma.core.MaskedConstant) for _x in (cmin_p, cmax_p)]):
            cmin, cmax = cmin_p, cmax_p
        if cmin == cmax:
            cmin, cmax = 0, 1
        clev = get_log_levels(cmin, cmax, 16)
        norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    elif style == "nonlinear":
        clev = Targets.get_thresholds(dataname)
        norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    elif style.startswith("ertel_potential_vorticity"):
        colors = [
            (1.0, 0.55000000000000004, 1.0, 1.0),
            (0.82333333333333336, 0.40000000000000002, 1.0, 1.0),
            (0.64666666666666672, 0.25, 1.0, 1.0),
            (0.46999999999999997, 0.10000000000000001, 1.0, 1.0),
            (0.69999999999999996, 1.0, 1.0, 1.0),
            (0.46666666666666667, 0.73333333333333339, 1.0, 1.0),
            (0.23333333333333334, 0.46666666666666667, 1.0, 1.0),
            (0.0, 0.20000000000000001, 1.0, 1.0),
            (0.65000000000000002, 1.0, 0.65000000000000002, 1.0),
            (0.43333333333333335, 0.90000000000000002, 0.43333333333333335, 1.0),
            (0.21666666666666667, 0.80000000000000004, 0.21666666666666667, 1.0),
            (0.0, 0.69999999999999996, 0.0, 1.0),
            (1.0, 1.0, 0.0, 1.0),
            (1.0, 0.375, 0.0, 1.0),
            (0.90000000000000002, 0.0, 0.041666666666666664, 1.0),
            (0.40000000000000002, 0.0, 0.25, 1.0)]
        clev = list(np.arange(0, 4, 0.5)) + list(range(4, 8)) + list(range(8, 18, 2))
        if style[-2:] == "nh":
            cmap = matplotlib.pyplot.cm.colors.ListedColormap(colors, name="pv_map")
            cmap.set_over((0.8, 0.8, 0.8, 1.0))
        else:
            cmap = matplotlib.pyplot.cm.colors.ListedColormap(colors[::-1], name="pv_map")
            cmap.set_under((0.8, 0.8, 0.8, 1.0))
            clev = [-_x for _x in clev[::-1]]
        norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    elif style.startswith("equivalent_latitude"):
        colors = [
            (1.0, 0.55000000000000004, 1.0, 1.0),
            (0.82333333333333336, 0.40000000000000002, 1.0, 1.0),
            (0.64666666666666672, 0.25, 1.0, 1.0),
            (0.46999999999999997, 0.10000000000000001, 1.0, 1.0),
            (0.69999999999999996, 1.0, 1.0, 1.0),
            (0.46666666666666667, 0.73333333333333339, 1.0, 1.0),
            (0.23333333333333334, 0.46666666666666667, 1.0, 1.0),
            (0.0, 0.20000000000000001, 1.0, 1.0),
            (0.65000000000000002, 1.0, 0.65000000000000002, 1.0),
            (0.43333333333333335, 0.90000000000000002, 0.43333333333333335, 1.0),
            (0.21666666666666667, 0.80000000000000004, 0.21666666666666667, 1.0),
            (0.0, 0.69999999999999996, 0.0, 1.0),
            (1.0, 1.0, 0.0, 1.0),
            (1.0, 0.375, 0.0, 1.0),
            (0.90000000000000002, 0.0, 0.041666666666666664, 1.0),
            (0.40000000000000002, 0.0, 0.25, 1.0)]
        clev = np.arange(5, 86, 5)
        if style[-2:] == "nh":
            cmap = matplotlib.pyplot.cm.colors.ListedColormap(colors)
        else:
            cmap = matplotlib.pyplot.cm.colors.ListedColormap(colors[::-1])
            clev = [-_x for _x in clev[::-1]]
        norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    elif style == "gravity_wave_temperature_perturbation":
        cmap = matplotlib.pyplot.cm.Spectral_r
        clev = [-3, -2.5, -2, -1.5, -1, -0.5, 0.5, 1, 1.5, 2, 2.5, 3]
        norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
        ticks = -3, -2, -1, 1, 2, 3
    elif style == "square_of_brunt_vaisala_frequency_in_air":
        cmap = matplotlib.pyplot.cm.colors.ListedColormap(
            [(1.0, 0.55000000000000004, 1.0, 1.0),
             (0.82333333333333336, 0.40000000000000002, 1.0, 1.0),
             (0.64666666666666672, 0.25, 1.0, 1.0),
             (0.46999999999999997, 0.10000000000000001, 1.0, 1.0),
             (0.69999999999999996, 1.0, 1.0, 1.0),
             (0.0, 0.20000000000000001, 1.0, 1.0),
             (0.65000000000000002, 1.0, 0.65000000000000002, 1.0),
             (0.0, 0.69999999999999996, 0.0, 1.0),
             (1.0, 1.0, 0.0, 1.0),
             (1.0, 0.73529411764705888, 0.0, 1.0),
             (1.0, 0.46323529411764708, 0.0, 1.0),
             (1.0, 0.21568627450980393, 0.0, 1.0),
             (1.0, 0.034313725490196068, 0.0, 1.0),
             (0.8294117647058824, 0.0, 0.071078431372549017, 1.0),
             (0.61176470588235299, 0.0, 0.16176470588235295, 1.0),
             (0.40000000000000002, 0.0, 0.25, 1.0),
             ], name="n2_map")
        cmap.set_over((0.8, 0.8, 0.8, 1.0))
        clev = np.arange(0., 8.5 / 1e4, 0.5 / 1e4)
        norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    elif style == "tropopause_altitude":
        cmap = matplotlib.pyplot.cm.terrain
        norm = None
        clev = np.arange(5, 18.1, 0.25)
    elif style == "log_ice_cloud":
        cmap = matplotlib.pyplot.cm.colors.ListedColormap(
            [(0.8, 0.8, 0.8, 1.0),
             (1., 1., 1.0, 1.0),
             (0., 0., 1.0, 1.0),
             (0., 0.949, 0.988, 1.0),
             (0., 1., 0., 1.0),
             (1., 1.0, 0.0, 1.0),
             (1.0, 0., 0.0, 1.0),
             (0.212, 0.114, 0.075, 1.0),
             ], name="ice_map_log")
        if dataname == "number_concentration_of_ice_crystals_in_air":
            clev = np.append(np.array([-1e31, -0.1]),
                             get_log_levels(1e-4, 100., 7))
            ticks = np.append(np.array([0.]), get_log_levels(1e-4, 100., 7))
        if dataname == "cloud_ice_mixing_ratio":
            clev = np.append(np.array([-1e31, -0.1]),
                             get_log_levels(1e-3, 1e3, 7))
            ticks = np.append(np.array([0.]), get_log_levels(1e-3, 1e3, 7))
        norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    elif style == "ice_cloud":
        cmap = matplotlib.pyplot.cm.colors.ListedColormap(
            [(1., 1., 1.0, 1.0),
             (0., 0., 1.0, 1.0),
             (0., 0.949, 0.988, 1.0),
             (0., 1., 0., 1.0),
             (1., 1.0, 0.0, 1.0),
             (1.0, 0., 0.0, 1.0),
             (0.212, 0.114, 0.075, 1.0),
             ], name="ice_map")
        if dataname == "mean_mass_radius_of_cloud_ice_crystals":
            clev = np.array([0, 1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    else:
        raise RuntimeError("Illegal plotting style?! ({})".format(style))
    if clev[0] == clev[-1]:
        cmin, cmax = 0, 1
        clev = np.linspace(0, 1, len(clev))
    return cmin, cmax, clev, cmap, norm, ticks


def get_cbar_label_format(style, maxvalue):
    format = "%.3g"
    if style != "log":
        if 100 <= maxvalue < 10000.:
            format = "%4i"
        elif 10 <= maxvalue < 100.:
            format = "%.1f"
        elif 1 <= maxvalue < 10.:
            format = "%.2f"
        elif 0.1 <= maxvalue < 1.:
            format = "%.3f"
        elif 0.01 <= maxvalue < 0.1:
            format = "%.4f"
    if style == 'log_ice_cloud':
        format = "%.0E"
    return format


def conditional_decorator(dec, condition):
    def decorator(func):
        if not condition:
            # Return the function unchanged, not decorated.
            return func
        return dec(func)
    return decorator
