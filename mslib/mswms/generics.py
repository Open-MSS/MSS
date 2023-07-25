# -*- coding: utf-8 -*-
"""

    mslib.mslib.generics
    ~~~~~~~~~~~~~~~~~

    This module provides functions for the wms server

    This file is part of MSS.

    :copyright: Copyright 2016-2022 by the MSS team, see AUTHORS.
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

import logging
import numpy as np
import matplotlib

from mslib.utils.units import convert_to

"""
Number of levels in discrete colourmaps
"""
N_LEVELS = 16

DEFAULT_CMAP = matplotlib.pyplot.cm.turbo

"""
List of supported targets using the CF standard_name as unique identifier.
For each standard_name listed here, simple plotting classes will be instantiated
for vertical and horizontal cross-sections.
"""
_TARGETS = [
    "air_temperature",
    "air_potential_temperature",
    "eastward_wind",
    "equivalent_latitude",
    "ertel_potential_vorticity",
    "mean_age_of_air",
    "mole_fraction_of_active_chlorine_in_air",
    "mole_fraction_of_ammonia_in_air",
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
    "mole_fraction_of_ethene_in_air",
    "mole_fraction_of_formaldehyde_in_air",
    "mole_fraction_of_formic_acid_in_air",
    "mole_fraction_of_hcfc22_in_air",
    "mole_fraction_of_hydrogen_chloride_in_air",
    "mole_fraction_of_hydrogen_peroxide_in_air",
    "mole_fraction_of_hypobromite_in_air",
    "mole_fraction_of_methane_in_air",
    "mole_fraction_of_methanol_in_air",
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

"""
Units for each standard_name. If not given, dimensionless is assumed.
"""
_UNITS = {
    "air_temperature": "K",
    "air_potential_temperature": "K",
    "eastward_wind": "m/s",
    "equivalent_latitude": "degree N",
    "ertel_potential_vorticity": "PVU",
    "gravity_wave_temperature_perturbation": "K",
    "mean_age_of_air": "month",
    "median_of_age_of_air_spectrum": "month",
    "northward_wind": "m/s",
    "square_of_brunt_vaisala_frequency_in_air": "1/s²",
    "tropopause_altitude": "km",
    "cloud_ice_mixing_ratio": "ppmv",
    "number_concentration_of_ice_crystals_in_air": "1/cm³",
    "mean_mass_radius_of_cloud_ice_crystals": "µm",
    "maximum_pressure_on_backtrajectory": "hPa",
    "maximum_relative_humidity_wrt_ice_on_backtrajectory": "percent",
}


"""
"""
_RANGES = {}


"""
The _THRESHOLDS are used to determine a single colourmap suitable for all
plotting purposes (that is vertical and horizontal on all levels. The given
thresholds have been manually designed.
"""
_THRESHOLDS = {
    "ertel_potential_vorticity":
        (-1, 0, 1, 2, 4, 6, 9, 12, 15, 25, 40),
    "mole_fraction_of_carbon_monoxide_in_air":
        (10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 300),
    "mole_fraction_of_nitric_acid_in_air":
        (0, 0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5, 2, 4),
    "mole_fraction_of_ozone_in_air":
        (0, 0.02, 0.03, 0.04, 0.06, 0.1, 0.16, 0.25, 0.45, 1, 4),
    "mole_fraction_of_peroxyacetyl_nitrate_in_air":
        (0, 50, 70, 100, 150, 200, 250, 300, 350, 400, 450, 500),
    "mole_fraction_of_water_vapor_in_air":
        (0, 3, 4, 6, 10, 16, 60, 150, 500, 1000),
}

for standard_name in _TARGETS:
    if standard_name.startswith("surface_origin_tracer_from_"):
        _UNITS[standard_name] = "percent"

for standard_name in [
        "mole_fraction_of_carbon_dioxide_in_air",
        "mole_fraction_of_methane_in_air",
        "mole_fraction_of_ozone_in_air",
        "mole_fraction_of_water_vapor_in_air",
]:
    _UNITS[standard_name] = "µmol/mol"

for standard_name in [
        "mole_fraction_of_active_chlorine_in_air",
        "mole_fraction_of_carbon_monoxide_in_air",
        "mole_fraction_of_chlorine_nitrate_in_air",
        "mole_fraction_of_hydrogen_chloride_in_air",
        "mole_fraction_of_nitric_acid_in_air",
        "mole_fraction_of_nitrous_oxide_in_air",
]:
    _UNITS[standard_name] = "nmol/mol"

for standard_name in [
        "mole_fraction_of_ammonia_in_air",
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
        "mole_fraction_of_hydrogen_peroxide_in_air",
        "mole_fraction_of_ethane_in_air",
        "mole_fraction_of_ethene_in_air",
        "mole_fraction_of_formaldehyde_in_air",
        "mole_fraction_of_formic_acid_in_air",
        "mole_fraction_of_hypobromite_in_air",
        "mole_fraction_of_methanol_in_air",
        "mole_fraction_of_nitrogen_dioxide_in_air",
        "mole_fraction_of_nitrogen_monoxide_in_air",
        "mole_fraction_of_peroxyacetyl_nitrate_in_air",
        "mole_fraction_of_sulfur_dioxide_in_air",
]:
    _UNITS[standard_name] = "pmol/mol"

for standard_name in [
        "fraction_below_6months_of_age_of_air_spectrum",
        "fraction_above_24months_of_age_of_air_spectrum",
]:
    _UNITS[standard_name] = "percent"

_TITLES = {
    "ertel_potential_vorticity": "PV",
    "square_of_brunt_vaisala_frequency_in_air": "N²",
    "gravity_wave_temperature_perturbation": "Gravity Wave Temperature Residual",
    "tropopause_altitude": "Thermal Tropopause",
}
for standard_name in _TARGETS:
    if standard_name.startswith("mole_fraction_of_") and standard_name.endswith("_in_air"):
        _TITLES[standard_name] = standard_name[17:-7].replace("_", " ")
    elif standard_name not in _TITLES:
        _TITLES[standard_name] = standard_name.replace("_", " ")


def get_standard_names():
    return _TARGETS


def get_title(standard_name):
    """
    Returns unit type and scaling factor for target.
    Args:
        standard_name: string of CF standard_name

    Returns:
        Tuple of string describing the unit and scaling factor to apply on data.
    """
    return _TITLES.get(standard_name, standard_name)


def get_unit(standard_name):
    """
    Returns unit type and scaling factor for target.
    Args:
        standard_name: string of CF standard_name

    Returns:
        Tuple of string describing the unit and scaling factor to apply on data.

    """
    return _UNITS.get(standard_name, "dimensionless")


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
    if standard_name in _RANGES:
        if level == "total" and "total" in _RANGES[standard_name]:
            unit, values = _RANGES[standard_name]["total"]
            return convert_to(values, unit, get_unit(standard_name))
        if typ in _RANGES[standard_name]:
            if level in _RANGES[standard_name][typ]:
                unit, values = _RANGES[standard_name][typ][level]
                return convert_to(values, unit, get_unit(standard_name))
            elif level is None:
                return 0, 0
    if standard_name.startswith("surface_origin_tracer_from_"):
        return 0, 100
    return None, None


def get_thresholds(standard_name):
    """
    Returns a list of meaningful values for a BoundaryNorm for plotting.
    Args:
        standard_name(str): a CF standard_name

    Returns:
        Tuple of threshold values to be supplied to a BoundaryNorm.
    """
    return _THRESHOLDS.get(standard_name)


def get_log_levels(cmin, cmax, levels=None):
    """
    Returns 'levels' levels in a logarithmic spacing. Takes care of ranges
    crossing zero and starting/ending at zero.
    Args:
        cmin: minimum value
        cmax: maximum value
        levels (optional): number of levels to be generated

    Returns:
        numpy array of values
    """
    if levels is None:
        levels = N_LEVELS
    if cmin >= cmax:
        cmin, cmax = cmin - 0.5, cmax + 0.5
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


CBAR_LABEL_FORMATS = {
    "log": "%.3g",
    "log_ice_cloud": "%.0E",
}


def get_cbar_label_format(style, maxvalue):
    if style in CBAR_LABEL_FORMATS:
        return CBAR_LABEL_FORMATS[style]
    if 100 <= maxvalue < 10000.:
        label_format = "%4i"
    elif 10 <= maxvalue < 100.:
        label_format = "%.1f"
    elif 1 <= maxvalue < 10.:
        label_format = "%.2f"
    elif 0.1 <= maxvalue < 1.:
        label_format = "%.3f"
    elif 0.01 <= maxvalue < 0.1:
        label_format = "%.4f"
    else:
        label_format = "%.3g"
    return label_format


def _style_default(_dataname, _style, cmin, cmax, cmap, _data):
    clev = np.linspace(cmin, cmax, 16)
    norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    return cmin, cmax, clev, cmap, norm, None


def _style_auto(_dataname, _style, cmin, cmax, cmap, data):
    cmin_p = data.min()
    cmax_p = data.max()
    if not any([isinstance(_x, np.ma.core.MaskedConstant) for _x in (cmin_p, cmax_p)]):
        cmin, cmax = cmin_p, cmax_p
    if cmin == cmax:
        cmin, cmax = 0., 1.
    if 0 < cmin < 0.05 * cmax:
        cmin = 0.
    clev = np.linspace(cmin, cmax, 16)
    norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    return cmin, cmax, clev, cmap, norm, None


def _style_log(_dataname, _style, cmin, cmax, cmap, _data):
    clev = get_log_levels(cmin, cmax, 16)
    norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    return cmin, cmax, clev, cmap, norm, None


def _style_autolog(_dataname, _style, cmin, cmax, cmap, data):
    cmin_p = data.min()
    cmax_p = data.max()
    if not any([isinstance(_x, np.ma.core.MaskedConstant) for _x in (cmin_p, cmax_p)]):
        cmin, cmax = cmin_p, cmax_p
    if cmin == cmax:
        cmin, cmax = 0., 1.
    clev = get_log_levels(cmin, cmax, 16)
    norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    return cmin, cmax, clev, cmap, norm, None


def _style_nonlinear(dataname, _style, cmin, cmax, cmap, _data):
    clev = get_thresholds(dataname)
    norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    return cmin, cmax, clev, cmap, norm, None


def _style_tropopause_altitude(_dataname, _style, cmin, cmax, cmap, _data):
    cmap = matplotlib.pyplot.cm.terrain
    clev = np.arange(5, 18.1, 0.25)
    return cmin, cmax, clev, cmap, None, None


def _style_ertel_potential_vorticity(_dataname, style, cmin, cmax, cmap, _data, hemisphere):
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
    if hemisphere == "nh":
        cmap = matplotlib.pyplot.cm.colors.ListedColormap(colors, name="pv_map")
        cmap.set_over((0.8, 0.8, 0.8, 1.0))
    else:
        assert hemisphere == "sh"
        cmap = matplotlib.pyplot.cm.colors.ListedColormap(colors[::-1], name="pv_map")
        cmap.set_under((0.8, 0.8, 0.8, 1.0))
        clev = [-_x for _x in clev[::-1]]
    norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    return cmin, cmax, clev, cmap, norm, None


def _style_ertel_potential_vorticity_nh(dataname, style, cmin, cmax, cmap, data):
    return _style_ertel_potential_vorticity(dataname, style, cmin, cmax, cmap, data, "nh")


def _style_ertel_potential_vorticity_sh(dataname, style, cmin, cmax, cmap, data):
    return _style_ertel_potential_vorticity(dataname, style, cmin, cmax, cmap, data, "sh")


def _style_equivalent_latitude(_dataname, style, cmin, cmax, cmap, _data, hemisphere):
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
    if hemisphere == "nh":
        cmap = matplotlib.pyplot.cm.colors.ListedColormap(colors)
    else:
        assert hemisphere == "sh"
        cmap = matplotlib.pyplot.cm.colors.ListedColormap(colors[::-1])
        clev = [-_x for _x in clev[::-1]]
    norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    return cmin, cmax, clev, cmap, norm, None


def _style_equivalent_latitude_sh(dataname, style, cmin, cmax, cmap, data):
    return _style_equivalent_latitude(dataname, style, cmin, cmax, cmap, data, "sh")


def _style_equivalent_latitude_nh(dataname, style, cmin, cmax, cmap, data):
    return _style_equivalent_latitude(dataname, style, cmin, cmax, cmap, data, "nh")


def _style_gravity_wave_temperature_perturbation(_dataname, style, _cmin, _cmax, cmap, _data):
    cmap = matplotlib.pyplot.cm.Spectral_r
    clev = [-3, -2.5, -2, -1.5, -1, -0.5, 0.5, 1, 1.5, 2, 2.5, 3]
    norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    ticks = -3, -2, -1, 1, 2, 3
    return -3, 3, clev, cmap, norm, ticks


def _style_square_of_brunt_vaisala_frequency_in_air(_dataname, style, cmin, cmax, cmap, _data):
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
    return cmin, cmax, clev, cmap, norm, None


def _style_number_concentration_of_ice_crystals_in_air(dataname, _style, cmin, cmax, cmap, _data):
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
    clev = np.append(np.array([-1e31, -0.1]), get_log_levels(1e-4, 100., 7))
    ticks = np.append(np.array([0.]), get_log_levels(1e-4, 100., 7))
    norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    return cmin, cmax, clev, cmap, norm, ticks


def _style_cloud_ice_mixing_ratio(_dataname, _style, cmin, cmax, cmap, _data):
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
    clev = np.append(np.array([-1e31, -0.1]), get_log_levels(1e-3, 1e3, 7))
    ticks = np.append(np.array([0.]), get_log_levels(1e-3, 1e3, 7))
    norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    return cmin, cmax, clev, cmap, norm, ticks


def _style_mean_mass_radius_of_cloud_ice_crystals(dataname, _style, cmin, cmax, cmap, _data):
    cmap = matplotlib.pyplot.cm.colors.ListedColormap(
        [(1., 1., 1.0, 1.0),
         (0., 0., 1.0, 1.0),
         (0., 0.949, 0.988, 1.0),
         (0., 1., 0., 1.0),
         (1., 1.0, 0.0, 1.0),
         (1.0, 0., 0.0, 1.0),
         (0.212, 0.114, 0.075, 1.0),
         ], name="ice_map")
    clev = np.array([0, 1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    norm = matplotlib.colors.BoundaryNorm(clev, cmap.N)
    return cmin, cmax, clev, cmap, norm, None


STYLES = {
    "default": _style_default,
    "log": _style_log,
    "auto": _style_auto,
    "autolog": _style_autolog,
    "nonlinear": _style_nonlinear,
    "tropopause_altitude": _style_tropopause_altitude,
    "ertel_potential_vorticity": _style_ertel_potential_vorticity_nh,
    "ertel_potential_vorticity_nh": _style_ertel_potential_vorticity_nh,
    "ertel_potential_vorticity_sh": _style_ertel_potential_vorticity_sh,
    "equivalent_latitude": _style_equivalent_latitude_nh,
    "equivalent_latitude_nh": _style_equivalent_latitude_nh,
    "equivalent_latitude_sh": _style_equivalent_latitude_sh,
    "gravity_wave_temperature_perturbation": _style_gravity_wave_temperature_perturbation,
    "square_of_brunt_vaisala_frequency_in_air": _style_square_of_brunt_vaisala_frequency_in_air,
    "mean_mass_radius_of_cloud_ice_crystals": _style_mean_mass_radius_of_cloud_ice_crystals,
    "cloud_ice_mixing_ratio": _style_cloud_ice_mixing_ratio,
    "number_concentration_of_ice_crystals_in_air": _style_number_concentration_of_ice_crystals_in_air,
}


def get_style_parameters(dataname, style, cmin, cmax, data):
    """
    Returns a list of meaningful values for a BoundaryNorm for plotting.

    All other _style_* functions have the same interface. This function
    calls the other functions via the STYLES module level variable.
    This allows to add styles from the server configuration side.

    Args:
        dataname: standard_name of the data product
        style: name of the plotting style
        cmin: configured/precomputed minimal value
        cmax: configured/precomputed maximal value
        cmap: default colormap
        data: the 2-D data field to be plotted
    Returns:
        tuple of (minimal data value, maximal data value,
        list of levels for contour plots, color map, norm,
        list of tick values for the colorbar)
    """
    if cmin is None or cmax is None:
        try:
            cmin, cmax = data.min(), data.max()
        except ValueError:
            cmin, cmax = 0., 1.
        if 0 < cmin < 0.05 * cmax:
            cmin = 0.
    cmap = DEFAULT_CMAP
    ticks = None

    if any(isinstance(_x, np.ma.core.MaskedConstant) for _x in (cmin, cmax)):
        cmin, cmax = 0., 1.

    try:
        cmin, cmax, clev, cmap, norm, ticks = \
            STYLES[style](dataname, style, cmin, cmax, cmap, data)
    except KeyError:
        logging.error("Unknown plotting style '%s' for dataname '%s'", style, dataname)
        raise
    except (ValueError, TypeError):
        logging.error("Illegal number of arguments/return values for plotting style '%s' "
                      "and dataname '%s'", style, dataname)
        raise
    except BaseException:
        logging.error("Unknown error in style call: plotting style '%s' "
                      "and dataname '%s'", style, dataname)
        raise
    if clev[0] == clev[-1]:
        cmin, cmax = 0., 1.
        clev = np.linspace(0., 1., len(clev))
    return cmin, cmax, clev, cmap, norm, ticks


def register_standard_name(standard_name, unit, title=None, range_=None, threshold=None):
    """_
    Registers or updates a standard_name for the generic plotting layers.

    Args:
        standard_name (str): CF standard_name
        unit (str): a pint parseable unit string
        title (str, optional): A name for the title field in the layer. Defaults to the standard_name.
        range_ (dict, optional): A dictionary specifying ranges for all vertical level
                types and levels. Example:
                    {'pl': {500.0: (3.1e-08, 2e-07),
                            300.0: (3.2e-08, 3.3e-07),
                            150.0: (1e-07, 6.5e-07), },
                     'tl': {350.0: (8.1e-08, 5e-07),
                            400.0: (2.3e-07, 7.8e-07),
                            450.0: (5.6e-07, 1.7e-06)},
                     'total': (1.6e-09, 2e-06)}
                For ozone, here pressure and theta levels. The tuples specify min/max value
                for the given level. The "total" entry is used for vertical cross-sections.
        threshold (list, optional): A list for the "nonlinear" style specifying a list of
                values for the contour surfaces. Example:
                        (-1, 0, 1, 2, 4, 6, 9, 12, 15, 25, 40),
    """
    if standard_name not in _TARGETS:
        _TARGETS.append(standard_name)
    _UNITS[standard_name] = unit
    if title is not None:
        _TITLES[standard_name] = title
    if range_ is not None:
        _RANGES[standard_name] = range_
    if threshold is not None:
        _THRESHOLDS[standard_name] = threshold
