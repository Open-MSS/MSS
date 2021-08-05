# -*- coding: utf-8 -*-
"""

    mslib.mswms.mpl_vsec_styles
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Matplotlib VERTICAL section styles.
    This file corresponds to mpl_hsec_styles.py, but for vertical section styles.
    Please refer to the introductory docstring in mpl_hsec_styles.py for further
    information.

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

import matplotlib
import matplotlib.pyplot as plt
import mpl_toolkits.axes_grid1.inset_locator
from matplotlib import patheffects
import numpy as np

from mslib.mswms.mpl_vsec import AbstractVerticalSectionStyle
from mslib.mswms.utils import Targets, get_style_parameters, get_cbar_label_format, make_cbar_labels_readable
from mslib.utils.units import convert_to
from mslib import thermolib


class VS_TemperatureStyle_01(AbstractVerticalSectionStyle):
    """
    Temperature
    Vertical section of temperature.
    """

    name = "VS_T01"
    title = "Temperature (K) Vertical Section"
    abstract = "Temperature (K) and potential temperature (K)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "air_temperature", "K")]

    def _prepare_datafields(self):
        """
        Computes potential temperature from pressure and temperature if
        it has not been passed as a data field.
        """
        self.data['air_potential_temperature'] = thermolib.pot_temp(
            self.data['air_pressure'], self.data['air_temperature'])

    def _plot_style(self):
        """
        Make a temperature/potential temperature vertical section.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_t = self.data["air_temperature"]
        curtain_pt = self.data["air_potential_temperature"]

        # Filled contour plot of temperature.
        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.horizontal_coordinate,
                         curtain_p, curtain_t, np.arange(180, 250, 2))  # 180-200, gist_earth Greens
        # Contour line plot of temperature.
        cs_t = ax.contour(self.horizontal_coordinate,
                          curtain_p, curtain_t, np.arange(160, 330, 4),
                          colors='orange', linestyles='solid', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.horizontal_coordinate,
                           curtain_p, curtain_pt, np.arange(200, 700, 10), colors='grey',
                           linestyles='dashed', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :])

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            cbar = self.fig.colorbar(cs, fraction=0.05, pad=0.01)
            cbar.set_label("Temperature (K)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="1%", height="30%", loc=1)
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")
            make_cbar_labels_readable(self.fig, axins1)


class VS_GenericStyle(AbstractVerticalSectionStyle):
    """
    Vertical section of chemical species/other stuff
    """
    styles = [
        ("auto", "auto colour scale"),
        ("autolog", "auto log colour scale"), ]

    def _plot_style(self):
        ax = self.ax
        curtain_cc = self.data[self.dataname]
        curtain_cc = np.ma.masked_invalid(curtain_cc)
        curtain_p = self.data["air_pressure"]

        # Filled contour plot of cloud cover.
        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        if self.p_bot > self.p_top:
            visible = (curtain_p <= self.p_bot) & (curtain_p >= self.p_top)
        else:
            visible = (curtain_p >= self.p_bot) & (curtain_p <= self.p_top)

        if visible.sum() == 0:
            visible = np.ones_like(curtain_cc, dtype=bool)

        cmin, cmax = Targets.get_range(self.dataname)
        cmin, cmax, clevs, cmap, norm, ticks = get_style_parameters(
            self.dataname, self.style, cmin, cmax, curtain_cc[visible])

        cs = ax.contourf(self.horizontal_coordinate, curtain_p, curtain_cc,
                         clevs, cmap=cmap, extend="both", norm=norm)

        # Contour lines
        for cont_data, cont_levels, cont_colour, cont_label_colour, cont_style, cont_lw, pe in self.contours:
            if cont_levels is None:
                pl_cont = ax.plot(self.lat_inds, self.data[cont_data].reshape(-1),
                                  "o", color=cont_colour, zorder=100)
                plt.setp(pl_cont, path_effects=[
                    patheffects.withStroke(linewidth=4, foreground="w")])
            else:
                cs_pv = ax.contour(self.horizontal_coordinate, curtain_p, self.data[cont_data], cont_levels,
                                   colors=cont_colour, linestyles=cont_style, linewidths=cont_lw)
                plt.setp(cs_pv.collections,
                         path_effects=[patheffects.withStroke(linewidth=cont_lw + 2, foreground="w")])
                cs_pv_lab = ax.clabel(cs_pv, colors=cont_label_colour, fontsize=8, fmt='%i')
                plt.setp(cs_pv_lab, path_effects=[patheffects.withStroke(linewidth=1, foreground="w")])

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup()

        # Format for colorbar labels
        cbar_format = get_cbar_label_format(self.style, np.abs(clevs).max())
        cbar_label = self.title

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            self.fig.colorbar(cs, fraction=0.05, pad=0.01, format=cbar_format, label=cbar_label, ticks=ticks)
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="1%", height="40%", loc=1)
            self.fig.colorbar(cs, cax=axins1, orientation="vertical", format=cbar_format, ticks=ticks)
            axins1.yaxis.set_ticks_position("left")
            make_cbar_labels_readable(self.fig, axins1)


def make_generic_class(name, entity, vert, add_data=None, add_contours=None,
                       fix_styles=None, add_styles=None, add_prepare=None):
    if add_data is None:
        add_data = [(vert, "ertel_potential_vorticity", "PVU")]
    if add_contours is None:
        add_contours = [  # ("ertel_potential_vorticity", [2, 4, 8, 16], "dimgrey", "dimgrey", "solid", 2, True)]
            ("ertel_potential_vorticity", [2, 4, 8, 16], "dimgrey", "dimgrey", "dashed", 2, True),
            ("air_potential_temperature", np.arange(200, 700, 10), "dimgrey", "dimgrey", "solid", 2, True)]

    class fnord(VS_GenericStyle):
        name = f"VS_{entity}_{vert}"
        dataname = entity
        units, _ = Targets.get_unit(dataname)
        title = Targets.TITLES.get(entity, entity)
        if units:
            title += f" ({units})"
        required_datafields = [(vert, entity, units)] + add_data
        contours = add_contours

    fnord.__name__ = name
    fnord.styles = list(fnord.styles)
    if Targets.get_thresholds(entity) is not None:
        fnord.styles = fnord.styles + [("nonlinear", "nonlinear colour scale")]
    if all(_x is not None for _x in Targets.get_range(entity)):
        fnord.styles = fnord.styles + [
            ("default", "fixed colour scale"),
            ("log", "fixed logarithmic colour scale")]

    if add_styles is not None:
        fnord.styles += add_styles
    if fix_styles is not None:
        fnord.styles = fix_styles
    if add_prepare is not None:
        fnord._prepare_datafields = add_prepare

    globals()[name] = fnord


_ADD_DATA = {
    "al": [("al", "ertel_potential_vorticity", "PVU"),
           ("al", "air_pressure", "Pa"),
           ("al", "air_potential_temperature", "K")],
    "ml": [("ml", "ertel_potential_vorticity", "PVU"),
           ("ml", "air_pressure", "Pa"),
           ("ml", "air_potential_temperature", "K")],
    "pl": [("pl", "ertel_potential_vorticity", "PVU"),
           ("pl", "air_potential_temperature", "K")],
    "tl": [("tl", "ertel_potential_vorticity", "PVU"),
           ("tl", "air_pressure", "Pa")],
}

for vert in ["al", "ml", "pl", "tl"]:
    for ent in Targets.get_targets():
        make_generic_class(
            f"VS_GenericStyle_{vert.upper()}_{ent}", ent, vert,
            add_data=_ADD_DATA[vert])
    make_generic_class(
        f"VS_GenericStyle_{vert.upper()}_{'ertel_potential_vorticity'}",
        "ertel_potential_vorticity", vert,
        add_data=_ADD_DATA[vert],
        fix_styles=[("ertel_potential_vorticity_nh", "northern hemisphere"),
                    ("ertel_potential_vorticity_sh", "southern hemisphere")])
    make_generic_class(
        f"VS_GenericStyle_{vert.upper()}_{'equivalent_latitude'}",
        "equivalent_latitude", vert,
        add_data=_ADD_DATA[vert],
        fix_styles=[("equivalent_latitude_nh", "northern hemisphere"),
                    ("equivalent_latitude_sh", "southern hemisphere")])
    make_generic_class(
        f"VS_GenericStyle_{vert.upper()}_{'gravity_wave_temperature_perturbation'}",
        "air_temperature_residual", vert,
        add_data=_ADD_DATA[vert] + [("sfc", "tropopause_air_pressure", "Pa"),
                                    ("sfc", "secondary_tropopause_air_pressure", "Pa")],
        add_contours=[("tropopause_air_pressure", None, "darkgrey", "darkgrey", "solid", 2, True),
                      ("secondary_tropopause_air_pressure", None, "dimgrey", "dimgrey", "solid", 2, True)],
        fix_styles=[("gravity_wave_temperature_perturbation", "")])
    make_generic_class(
        f"VS_GenericStyle_{vert.upper()}_{'square_of_brunt_vaisala_frequency_in_air'}",
        "square_of_brunt_vaisala_frequency_in_air", vert,
        add_data=_ADD_DATA[vert] + [("sfc", "tropopause_air_pressure", "Pa"),
                                    ("sfc", "secondary_tropopause_air_pressure", "Pa")],
        add_contours=[("tropopause_air_pressure", None, "dimgrey", "dimgrey", "solid", 2, True),
                      ("secondary_tropopause_air_pressure", None, "dimgrey", "dimgrey", "solid", 2, True)],
        fix_styles=[("square_of_brunt_vaisala_frequency_in_air", "")])

vert = "pl"
make_generic_class(
    f"VS_GenericStyle_{vert.upper()}_{'cloud_ice_mixing_ratio'}",
    "cloud_ice_mixing_ratio", vert,
    add_data=[("pl", "maximum_relative_humidity_wrt_ice_on_backtrajectory", None)],
    add_contours=[("maximum_relative_humidity_wrt_ice_on_backtrajectory",
                   [90, 100, 120, 160],
                   ["dimgrey", "dimgrey", "#443322", "#045FB4"],
                   ["dimgrey", "dimgrey", "#443322", "#045FB4"],
                   ["dashed", "solid", "solid", "solid"], 2, True)],
    fix_styles=[("log_ice_cloud", "iwc")])

make_generic_class(
    f"VS_GenericStyle_{vert.upper()}_{'number_concentration_of_ice_crystals_in_air'}",
    "number_concentration_of_ice_crystals_in_air", vert,
    add_data=[("pl", "maximum_relative_humidity_wrt_ice_on_backtrajectory", None)],
    add_contours=[("maximum_relative_humidity_wrt_ice_on_backtrajectory",
                   [90, 100, 120, 160],
                   ["dimgrey", "dimgrey", "#443322", "#045FB4"],
                   ["dimgrey", "dimgrey", "#443322", "#045FB4"],
                   ["dashed", "solid", "solid", "solid"], 2, True)],
    fix_styles=[("log_ice_cloud", "nice")])

make_generic_class(
    f"VS_GenericStyle_{vert.upper()}_{'mean_mass_radius_of_cloud_ice_crystals'}",
    "mean_mass_radius_of_cloud_ice_crystals", vert,
    add_data=[("pl", "maximum_relative_humidity_wrt_ice_on_backtrajectory", None)],
    add_contours=[("maximum_relative_humidity_wrt_ice_on_backtrajectory",
                   [90, 100, 120, 160],
                   ["dimgrey", "dimgrey", "#443322", "#045FB4"],
                   ["dimgrey", "dimgrey", "#443322", "#045FB4"],
                   ["dashed", "solid", "solid", "solid"], 2, True)],
    fix_styles=[("ice_cloud", "radius")])

make_generic_class(
    f"VS_GenericStyle_{vert.upper()}_{'maximum_pressure_on_backtrajectory'}",
    "maximum_pressure_on_backtrajectory", vert, [], [])


class VS_CloudsStyle_01(AbstractVerticalSectionStyle):
    """
    Clouds
    Vertical section of cloud cover.
    """

    name = "VS_CC01"
    title = "Cloud Cover (0-1) Vertical Section"
    abstract = "Cloud cover (0-1) with temperature (K) and potential temperature (K)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "air_temperature", "K"),
        ("ml", "cloud_area_fraction_in_atmosphere_layer", 'dimensionless')]

    def _prepare_datafields(self):
        """Computes potential temperature from pressure and temperature if
        it has not been passed as a data field.
        """
        self.data['air_potential_temperature'] = thermolib.pot_temp(
            self.data['air_pressure'], self.data['air_temperature'])

    def _plot_style(self):
        """
        Make a cloud cover vertical section with temperature/potential
        temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_t = self.data["air_temperature"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_cc = self.data["cloud_area_fraction_in_atmosphere_layer"]

        # Contour spacing for temperature lines.
        delta_t = 2 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 4
        delta_pt = 5 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 10
        # Filled contour plot of cloud cover.
        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.horizontal_coordinate, curtain_p, curtain_cc,
                         np.arange(0.2, 1.1, 0.1), cmap=plt.cm.winter)
        # Contour line plot of temperature.
        cs_t = ax.contour(self.horizontal_coordinate,
                          curtain_p, curtain_t, np.arange(236, 330, delta_t),
                          colors='red', linestyles='solid', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.horizontal_coordinate, curtain_p, curtain_t, [234],
                          colors='red', linestyles='solid', linewidths=2)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.horizontal_coordinate, curtain_p, curtain_t,
                          np.arange(160, 232, delta_t),
                          colors='red', linestyles='dashed', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.horizontal_coordinate, curtain_p, curtain_pt,
                           np.arange(200, 700, delta_pt), colors='grey',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :])

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            cbar = self.fig.colorbar(cs, fraction=0.05, pad=0.01)
            cbar.set_label("Cloud cover (0-1)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="1%", height="30%", loc=1)
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")
            make_cbar_labels_readable(self.fig, axins1)


class VS_CloudsWindStyle_01(AbstractVerticalSectionStyle):
    """
    Vertical section of cloud cover and horizontal wind speed.
    """

    name = "VS_CW01"
    title = "Cloud Cover (0-1) and Wind Speed (m/s) Vertical Section"
    abstract = "Cloud cover (0-1) with wind speed (m/s) and potential temperature (K)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "air_temperature", "K"),
        ("ml", "cloud_area_fraction_in_atmosphere_layer", 'dimensionless'),
        ("ml", "eastward_wind", "m/s"),
        ("ml", "northward_wind", "m/s")]

    def _prepare_datafields(self):
        """
        Computes potential temperature from pressure and temperature and
        total horizontal wind speed.
        """
        self.data['air_potential_temperature'] = thermolib.pot_temp(
            self.data['air_pressure'], self.data['air_temperature'])
        self.data["horizontal_wind"] = np.hypot(
            self.data["eastward_wind"], self.data["northward_wind"])

    def _plot_style(self):
        """
        Make a cloud cover vertical section with wind speed and potential
        temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_cc = self.data["cloud_area_fraction_in_atmosphere_layer"]
        curtain_v = self.data["horizontal_wind"]

        # Contour spacing for temperature lines.
        delta_pt = 5 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 10

        wind_contours = np.arange(20, 70, 10)

        # Filled contour plot of cloud cover.
        cs = ax.contourf(self.horizontal_coordinate, curtain_p, curtain_cc,
                         np.arange(0.2, 1.1, 0.1), cmap=plt.cm.winter)

        # Contour line plot of wind speed.
        cs_t = ax.contour(self.horizontal_coordinate, curtain_p, curtain_v,
                          wind_contours, colors='red', linestyles='solid',
                          linewidths=2)  # gist_earth
        ax.clabel(cs_t, fontsize=12, fmt='%i')

        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.horizontal_coordinate, curtain_p, curtain_pt,
                           np.arange(200, 700, delta_pt), colors='0.40',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=12, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :])

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            cbar = self.fig.colorbar(cs, fraction=0.05, pad=0.01)
            cbar.set_label("Cloud cover (0-1)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="1%", height="30%", loc=1)
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")
            make_cbar_labels_readable(self.fig, axins1)


class VS_RelativeHumdityStyle_01(AbstractVerticalSectionStyle):
    """
    Vertical sections of relative humidity.
    """

    name = "VS_RH01"
    title = "Relative Humdity (%) Vertical Section"
    abstract = "Relative humdity (%) with temperature (K) and potential temperature (K)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "air_temperature", "K"),
        ("ml", "specific_humidity", "kg/kg")]

    def _prepare_datafields(self):
        """
        Computes potential temperature from pressure and temperature if
        it has not been passed as a data field. Also computes relative humdity.
        """
        self.data['air_potential_temperature'] = thermolib.pot_temp(
            self.data['air_pressure'], self.data['air_temperature'])
        self.data["relative_humidity"] = thermolib.rel_hum(
            self.data['air_pressure'], self.data["air_temperature"],
            self.data["specific_humidity"])

    def _plot_style(self):
        """
        Make a relative humidity vertical section with temperature/potential
        temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_t = self.data["air_temperature"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_rh = self.data["relative_humidity"]

        # Contour spacing for temperature lines.
        delta_t = 2 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 4
        delta_pt = 5 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 10

        filled_contours = np.arange(70, 140, 15)
        thin_contours = np.arange(10, 140, 15)

        # Filled contour plot of relative humidity.
        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.horizontal_coordinate, curtain_p, curtain_rh,
                         filled_contours, cmap=plt.cm.winter_r)
        # Contour line plot of relative humidity.
        cs_rh1 = ax.contour(self.horizontal_coordinate,
                            curtain_p, curtain_rh, thin_contours,
                            colors="grey", linestyles="solid", linewidths=0.5)  # gist_earth
        ax.clabel(cs_rh1, fontsize=8, fmt='%i')
        ax.contour(self.horizontal_coordinate,
                   curtain_p, curtain_rh, np.arange(100, 170, 15),
                   colors="yellow", linestyles="solid", linewidths=1)  # gist_earth
        # Contour line plot of temperature.
        cs_t = ax.contour(self.horizontal_coordinate,
                          curtain_p, curtain_t, np.arange(236, 330, delta_t),
                          colors='red', linestyles='solid', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.horizontal_coordinate, curtain_p, curtain_t, [234],
                          colors='red', linestyles='solid', linewidths=2)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.horizontal_coordinate,
                          curtain_p, curtain_t, np.arange(160, 232, delta_t),
                          colors='red', linestyles='dashed', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.horizontal_coordinate,
                           curtain_p, curtain_pt, np.arange(200, 700, delta_pt), colors='orange',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :])

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            cbar = self.fig.colorbar(cs, fraction=0.05, pad=0.01)
            cbar.set_label("Relative humdity (%)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="1%", height="30%", loc=1)
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")
            make_cbar_labels_readable(self.fig, axins1)


class VS_SpecificHumdityStyle_01(AbstractVerticalSectionStyle):
    """
    Vertical sections of specific humidity.
    """

    name = "VS_Q01"
    # title = "Specific Humdity (g/kg) and Northward Wind (m/s) Vertical Section"
    title = "Specific Humdity (g/kg) Vertical Section"
    abstract = "Specific humdity (g/kg) with temperature (K) and potential temperature (K)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "air_temperature", "K"),
        ("ml", "specific_humidity", "g/kg"),
        ("ml", "northward_wind", "m/s")]

    def _prepare_datafields(self):
        """
        Computes potential temperature from pressure and temperature if
        it has not been passed as a data field. Also computes relative humdity.
        """
        self.data['air_potential_temperature'] = thermolib.pot_temp(
            self.data['air_pressure'], self.data['air_temperature'])

    def _plot_style(self):
        """
        Make a relative humidity vertical section with temperature/potential
        temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_t = self.data["air_temperature"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_q = self.data["specific_humidity"]

        # Contour spacing.
        vertical_log_extent = (np.log(self.p_bot) - np.log(self.p_top))

        # delta_t = 2 if vertical_log_extent < 2.2 else 4
        delta_t = 2 if vertical_log_extent < 1.5 else 4

        # if vertical_log_extent > 2.2:
        if vertical_log_extent > 1.5:
            delta_pt = 10
        elif vertical_log_extent > 0.5:
            delta_pt = 5
        else:
            delta_pt = 1.

        # filled_contours = np.arange(1, 16, 1)
        filled_contours = [0.01, 0.05, 0.1, 0.5, 1, 3, 4, 6, 8]

        # Filled contour plot of specific humidity.
        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.horizontal_coordinate, curtain_p, curtain_q,
                         filled_contours, cmap=plt.cm.YlGnBu)  # YlGnBu
        cs_q = ax.contour(self.horizontal_coordinate, curtain_p, curtain_q,
                          filled_contours, colors="c", linestyles="solid", linewidths=1)
        ax.clabel(cs_q, fontsize=8, fmt='%.2f')

        # Contour line plot of northward wind (v).
        # cs_v = ax.contour(self.horizontal_coordinate,
        #                  curtain_p, curtain_v, np.arange(5,15,2.5),
        #                  colors="black", linestyles="solid", linewidths=1)
        # ax.clabel(cs_v, fontsize=8, fmt='%.1f')

        # Contour line plot of temperature.
        cs_t = ax.contour(self.horizontal_coordinate,
                          curtain_p, curtain_t, np.arange(236, 330, delta_t),
                          colors='red', linestyles='solid', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.horizontal_coordinate, curtain_p, curtain_t, [234],
                          colors='red', linestyles='solid', linewidths=2)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.horizontal_coordinate,
                          curtain_p, curtain_t, np.arange(160, 232, delta_t),
                          colors='red', linestyles='dashed', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')

        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.horizontal_coordinate, curtain_p, curtain_pt,
                           np.arange(200, 700, delta_pt), colors='orange',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%.1f')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :])
        self.add_colorbar(cs, "Specific humdity (g/kg)")


class VS_VerticalVelocityStyle_01(AbstractVerticalSectionStyle):
    """
    Vertical sections of vertical velocity.
    """

    name = "VS_W01"
    title = "Vertical Velocity (cm/s) Vertical Section"
    abstract = "Veertical velocity (cm/s) with temperature (K) and potential temperature (K)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "air_temperature", "K"),
        ("ml", "lagrangian_tendency_of_air_pressure", "Pa/s")]

    def _prepare_datafields(self):
        """
        Computes potential temperature from pressure and temperature if
        it has not been passed as a data field. Also computes vertical
        velocity in cm/s.
        """
        self.data['air_potential_temperature'] = thermolib.pot_temp(
            self.data['air_pressure'], self.data['air_temperature'])
        self.data["upward_wind"] = convert_to(
            thermolib.omega_to_w(self.data["lagrangian_tendency_of_air_pressure"],
                                 self.data['air_pressure'], self.data["air_temperature"]),
            "m/s", "cm/s")

    def _plot_style(self):
        """
        Make a vertical velocity vertical section with temperature/potential
        temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_t = self.data["air_temperature"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_w = self.data["upward_wind"]

        # Contour spacing for temperature lines.
        delta_t = 2 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 4
        delta_pt = 5 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 10

        upward_contours = np.arange(-42, 46, 4)

        # Filled contour plot of relative humidity.
        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.horizontal_coordinate, curtain_p, curtain_w,
                         upward_contours, cmap=plt.cm.bwr)
        # Contour line plot of relative humidity.
        ax.contour(self.horizontal_coordinate, curtain_p, curtain_w, [2],
                   colors="red", linestyles="solid", linewidths=0.5)
        ax.contour(self.horizontal_coordinate, curtain_p, curtain_w, [-2],
                   colors="blue", linestyles="solid", linewidths=0.5)
        # Contour line plot of temperature.
        cs_t = ax.contour(self.horizontal_coordinate,
                          curtain_p, curtain_t, np.arange(236, 330, delta_t),
                          colors='green', linestyles='solid', linewidths=1)
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.horizontal_coordinate,
                          curtain_p, curtain_t, [234],
                          colors='green', linestyles='solid', linewidths=2)
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.horizontal_coordinate,
                          curtain_p, curtain_t, np.arange(160, 232, delta_t),
                          colors='green', linestyles='dashed', linewidths=1)
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.horizontal_coordinate, curtain_p, curtain_pt,
                           np.arange(200, 700, delta_pt), colors='grey',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :])
        self.add_colorbar(cs, "Vertical velocity (cm/s)")


class VS_HorizontalVelocityStyle_01(AbstractVerticalSectionStyle):
    """
    Vertical sections of horizontal velocity.
    """

    name = "VS_HV01"
    title = "Horizontal Wind (m/s) Vertical Section"
    abstract = "Horizontal wind speed (m/s) with temperature (K) and potential temperature (K)"

    # NOTE: This style is used for the flight performance computations. Make sure
    # that it always requests air_pressure, air_temperature, eastward_wind,
    # northward_wind! (mr, 2012Nov09)

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "air_temperature", "K"),
        ("ml", "eastward_wind", "m/s"),
        ("ml", "northward_wind", "m/s")]

    def _prepare_datafields(self):
        """
        Computes potential temperature from pressure and temperature and
        total horizontal wind speed.
        """
        self.data['air_potential_temperature'] = thermolib.pot_temp(
            self.data['air_pressure'], self.data['air_temperature'])
        self.data["horizontal_wind"] = np.hypot(
            self.data["eastward_wind"], self.data["northward_wind"])

    def _plot_style(self):
        """
        Make a horizontal velocity vertical section with temperature/potential
        temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_t = self.data["air_temperature"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_v = self.data["horizontal_wind"]

        # Contour spacing for temperature lines.
        delta_t = 2 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 4
        delta_pt = 5 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 10

        wind_contours = np.arange(10, 90, 5)

        # Filled contour plot of relative humidity.
        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.horizontal_coordinate, curtain_p, curtain_v,
                         wind_contours, cmap=plt.cm.hot_r)
        # Contour line plot of relative humidity.
        cs_v1 = ax.contour(self.horizontal_coordinate,
                           curtain_p, curtain_v, np.arange(5, 90, 5),
                           colors="orange", linestyles="solid", linewidths=1)
        ax.clabel(cs_v1, fontsize=8, fmt='%i')
        cs_v2 = ax.contour(self.horizontal_coordinate,
                           curtain_p, curtain_v, np.arange(95, 150, 5),
                           colors="black", linestyles="solid", linewidths=0.5)
        ax.clabel(cs_v2, fontsize=8, fmt='%i')
        # Contour line plot of temperature.
        cs_t = ax.contour(self.horizontal_coordinate,
                          curtain_p, curtain_t, np.arange(236, 330, delta_t),
                          colors='green', linestyles='solid', linewidths=1)
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.horizontal_coordinate, curtain_p, curtain_t, [234],
                          colors='green', linestyles='solid', linewidths=2)
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.horizontal_coordinate,
                          curtain_p, curtain_t, np.arange(160, 232, delta_t),
                          colors='green', linestyles='dashed', linewidths=1)
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.horizontal_coordinate, curtain_p, curtain_pt,
                           np.arange(200, 700, delta_pt), colors='grey',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :])
        self.add_colorbar(cs, "Horizontal wind speed (m/s)")


# POTENTIAL VORTICITY
pv_cmap_data = [
    [0.0000, 0.6000, 1.0000],
    [0.0980, 0.6039, 1.0000],
    [0.1961, 0.6157, 1.0000],
    [0.2941, 0.6314, 1.0000],
    [0.3922, 0.6588, 1.0000],
    [0.4902, 0.6941, 1.0000],
    [0.5882, 0.7373, 1.0000],
    [0.6863, 0.7882, 1.0000],
    [0.7843, 0.8431, 1.0000],
    [0.8824, 0.9098, 1.0000],
    [0.9804, 0.9843, 1.0000],
    [1.0000, 1.0000, 0.9961],
    [1.0000, 0.9888, 0.9778],
    [1.0000, 0.9612, 0.9229],
    [1.0000, 0.9189, 0.8390],
    [1.0000, 0.8729, 0.7475],
    [1.0000, 0.8324, 0.6669],
    [1.0000, 0.7946, 0.5919],
    [1.0000, 0.7569, 0.5168],
    [1.0000, 0.7116, 0.4430],
    [1.0000, 0.6407, 0.3732],
    [1.0000, 0.5422, 0.3078],
    [1.0000, 0.4320, 0.2441],
    [1.0000, 0.3039, 0.1717],
    [1.0000, 0.1998, 0.1129],
    [1.0000, 0.1480, 0.0836],
    [1.0000, 0.1141, 0.0645],
    [1.0000, 0.0815, 0.0460],
    [1.0000, 0.0511, 0.0281],
    [1.0000, 0.0317, 0.0134],
    [1.0000, 0.0333, 0.0047],
    [1.0000, 0.0533, 0.0011],
    [1.0000, 0.0819, 0.0001],
    [1.0000, 0.1141, 0],
    [1.0000, 0.1464, 0],
    [1.0000, 0.1788, 0],
    [1.0000, 0.2111, 0],
    [1.0000, 0.2435, 0],
    [1.0000, 0.2759, 0],
    [1.0000, 0.3082, 0],
    [1.0000, 0.3406, 0],
    [1.0000, 0.3730, 0],
    [1.0000, 0.4053, 0],
    [1.0000, 0.4377, 0],
    [1.0000, 0.4701, 0],
    [1.0000, 0.5038, 0],
    [1.0000, 0.5313, 0],
    [1.0000, 0.5589, 0],
    [1.0000, 0.5864, 0],
    [1.0000, 0.6140, 0],
    [1.0000, 0.6416, 0],
    [1.0000, 0.6692, 0],
    [1.0000, 0.6967, 0],
    [1.0000, 0.7243, 0],
    [1.0000, 0.7519, 0],
    [1.0000, 0.7794, 0],
    [1.0000, 0.8070, 0],
    [1.0000, 0.8346, 0],
    [1.0000, 0.8621, 0],
    [1.0000, 0.8897, 0],
    [1.0000, 0.9173, 0],
    [1.0000, 0.9449, 0],
    [1.0000, 0.9724, 0],
    [1.0000, 1.0000, 0]
]

pv_eth_cmap_0 = matplotlib.colors.ListedColormap(pv_cmap_data)


# die Farben fuer den PV colorbar mit folgenden Abstufungen:
#     -2.0,0.0,0.2,0.5,0.8,1.0,1.5,2.0,3.0,4.0
# muessten folgende sein:
#         ( (/142, 178, 255/) # -2 .. 0
#           (/181, 201, 255/) #  0 .. .2
#           (/214, 226, 237/) #
#           (/242, 221, 160/) #
#           (/239, 193, 130/) #
#           (/242, 132,  68/) #
#           (/220,  60,  30/) #
#           (/255, 120,  20/) #
#           (/255, 190,  20/) #
#           (/255, 249,  20/) #
#           (/170, 255,  60/) )/255

def scale_pvu_to_01(pvu):
    return ((pvu + 2.) / 10.)


S = 0.0000000001

_pv_eth_data = (
    (scale_pvu_to_01(-2.), ((142. / 255.), (178. / 255.), (255. / 255.))),
    (scale_pvu_to_01(0. - S), ((142. / 255.), (178. / 255.), (255. / 255.))),

    (scale_pvu_to_01(0.), ((181. / 255.), (201. / 255.), (255. / 255.))),
    (scale_pvu_to_01(0.2 - S), ((181. / 255.), (201. / 255.), (255. / 255.))),

    (scale_pvu_to_01(0.2), ((214. / 255.), (226. / 255.), (237. / 255.))),
    (scale_pvu_to_01(0.5 - S), ((214. / 255.), (226. / 255.), (237. / 255.))),

    (scale_pvu_to_01(0.5), ((242. / 255.), (221. / 255.), (160. / 255.))),
    (scale_pvu_to_01(0.8 - S), ((242. / 255.), (221. / 255.), (160. / 255.))),

    (scale_pvu_to_01(0.8), ((239. / 255.), (193. / 255.), (130. / 255.))),
    (scale_pvu_to_01(1.0 - S), ((239. / 255.), (193. / 255.), (130. / 255.))),

    (scale_pvu_to_01(1.0), ((242. / 255.), (132. / 255.), (68. / 255.))),
    (scale_pvu_to_01(1.5 - S), ((242. / 255.), (132. / 255.), (68. / 255.))),

    (scale_pvu_to_01(1.5), ((220. / 255.), (60. / 255.), (30. / 255.))),
    (scale_pvu_to_01(2.0 - S), ((220. / 255.), (60. / 255.), (30. / 255.))),

    (scale_pvu_to_01(2.0), ((255. / 255.), (120. / 255.), (20. / 255.))),
    (scale_pvu_to_01(3.0 - S), ((255. / 255.), (120. / 255.), (20. / 255.))),

    (scale_pvu_to_01(3.0), ((255. / 255.), (190. / 255.), (20. / 255.))),
    (scale_pvu_to_01(4.0 - S), ((255. / 255.), (190. / 255.), (20. / 255.))),

    (scale_pvu_to_01(4.0), ((255. / 255.), (249. / 255.), (20. / 255.))),
    (scale_pvu_to_01(6.0 - S), ((255. / 255.), (249. / 255.), (20. / 255.))),

    (scale_pvu_to_01(6.0), ((170. / 255.), (255. / 255.), (60. / 255.))),
    (scale_pvu_to_01(8.0), ((170. / 255.), (255. / 255.), (60. / 255.)))
)

pv_eth_cmap_1 = matplotlib.colors.LinearSegmentedColormap.from_list("pv_eth_cmap_1", _pv_eth_data)


class VS_PotentialVorticityStyle_01(AbstractVerticalSectionStyle):
    """
    Vertical sections of potential vorticity.
    """

    name = "VS_PV01"
    title = "Potential Vorticity (PVU) Vertical Section"
    abstract = "(Neg.) Potential vorticity (PVU) with CLWC/CIWC (g/kg) and potential temperature (K)"
    styles = [
        ("default", "Northern Hemisphere"),
        ("NH", "Northern Hemisphere"),
        ("SH", "Southern Hemisphere, neg. PVU")]

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "air_temperature", "K"),
        ("ml", "eastward_wind", "m/s"),
        ("ml", "northward_wind", "m/s"),
        ("ml", "specific_cloud_liquid_water_content", "g/kg"),
        ("ml", "specific_cloud_ice_water_content", "g/kg"),
        ("ml", "ertel_potential_vorticity", "PVU")]

    def _prepare_datafields(self):
        """Computes potential temperature from pressure and temperature and
           total horizontal wind speed.
        """
        self.data['air_potential_temperature'] = thermolib.pot_temp(
            self.data['air_pressure'], self.data['air_temperature'])
        self.data["horizontal_wind"] = np.hypot(
            self.data["eastward_wind"], self.data["northward_wind"])

    def _plot_style(self):
        """Make a horizontal velocity vertical section with temperature/potential
           temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_pv = self.data["ertel_potential_vorticity"]
        curtain_clwc = self.data["specific_cloud_liquid_water_content"]
        curtain_ciwc = self.data["specific_cloud_ice_water_content"]

        # Contour spacing for temperature lines.
        delta_pt = 5 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 10

        # Change PV sign on southern hemisphere.
        if self.style.lower() == "default":
            self.style = "NH"
        if self.style.upper() == "SH":
            curtain_pv = -curtain_pv

        pv_contours = np.arange(-2., 8.1, 0.1)

        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.horizontal_coordinate,
                         curtain_p, curtain_pv,
                         pv_contours, cmap=pv_eth_cmap_1)

        # Contour line plot of horizontal wind.
        # cs_v1 = ax.contour(self.horizontal_coordinate,
        #                     curtain_p, curtain_v, np.arange(5, 90, 5),
        #                     colors="green", linestyles="solid", linewidths=2)
        # ax.clabel(cs_v1, fontsize=8, fmt='%i')
        # cs_v2 = ax.contour(self.horizontal_coordinate,
        #                     curtain_p, curtain_v, np.arange(95, 150, 5),
        #                     colors="black", linestyles="solid", linewidths=0.5)
        # ax.clabel(cs_v2, fontsize=8, fmt='%i')

        # [0.01, 0.03, 0.05, 0.07, 0.1, 0.3, 0.5, 0.7, 1.0]

        cs_v1 = ax.contour(self.horizontal_coordinate,
                           curtain_p, curtain_clwc, [0.01, 0.03, 0.05, 0.07, 0.1, 0.3, 0.5, 0.7, 1.0],
                           colors="blue", linestyles="solid", linewidths=1)
        ax.clabel(cs_v1, fontsize=8, fmt='%.1f')

        cs_v1 = ax.contour(self.horizontal_coordinate,
                           curtain_p, curtain_ciwc, [0.01, 0.03, 0.05, 0.07, 0.1, 0.3, 0.5, 0.7, 1.0],
                           colors="white", linestyles="solid", linewidths=1)
        ax.clabel(cs_v1, fontsize=8, fmt='%.1f')

        # Contour line plot of temperature.
        # cs_t = ax.contour(self.horizontal_coordinate,
        #                   curtain_p, curtain_t, np.arange(236, 330, delta_t),
        #                   colors='green', linestyles='solid', linewidths=1)
        # ax.clabel(cs_t, fontsize=8, fmt='%i')
        # cs_t = ax.contour(self.horizontal_coordinate,
        #                   curtain_p, curtain_t, [234],
        #                   colors='green', linestyles='solid', linewidths=2)
        # ax.clabel(cs_t, fontsize=8, fmt='%i')
        # cs_t = ax.contour(self.horizontal_coordinate,
        #                   curtain_p, curtain_t, np.arange(160, 232, delta_t),
        #                   colors='green', linestyles='dashed', linewidths=1)
        # ax.clabel(cs_t, fontsize=8, fmt='%i')

        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.horizontal_coordinate,
                           curtain_p, curtain_pt, np.arange(200, 700, delta_pt), colors='black',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :])
        self.add_colorbar(cs, "Negative Potential vorticity (PVU)" if self.style.upper() == "SH"
                          else "Potential vorticity (PVU)")


class VS_ProbabilityOfWCBStyle_01(AbstractVerticalSectionStyle):
    """
    Probability of WCB
    Vertical sections of probability of WCB trajectory occurence,
    derived from Lagranto trajectories (TNF 2012 product).
    """

    name = "VS_PWCB01"
    title = "Probability of WCB (%) Vertical Section"
    abstract = "Probability of WCB (%) with CLWC/CIWC (g/kg) and potential temperature (K)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "air_temperature", "K"),
        ("ml", "eastward_wind", "m/s"),
        ("ml", "northward_wind", "m/s"),
        ("ml", "specific_cloud_liquid_water_content", "g/kg"),
        ("ml", "specific_cloud_ice_water_content", "g/kg"),
        ("ml", "probability_of_wcb_occurrence", 'dimensionless')]

    def _prepare_datafields(self):
        """
        Computes potential temperature from pressure and temperature and
        total horizontal wind speed.
        """
        self.data['air_potential_temperature'] = thermolib.pot_temp(
            self.data['air_pressure'], self.data['air_temperature'])
        self.data["horizontal_wind"] = np.hypot(
            self.data["eastward_wind"], self.data["northward_wind"])

    def _plot_style(self):
        """
        Make a horizontal velocity vertical section with temperature/potential
        temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_pwcb = self.data["probability_of_wcb_occurrence"] * 100.
        curtain_clwc = self.data["specific_cloud_liquid_water_content"]
        curtain_ciwc = self.data["specific_cloud_ice_water_content"]

        # Contour spacing for temperature lines.
        delta_pt = 5 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 10

        pwcb_contours = np.arange(0, 101, 10)

        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.horizontal_coordinate, curtain_p, curtain_pwcb,
                         pwcb_contours, cmap=plt.cm.pink_r)

        # Contour line plot of horizontal wind.
        # cs_v1 = ax.contour(self.horizontal_coordinate,
        #                     curtain_p, curtain_v, np.arange(5, 90, 5),
        #                     colors="green", linestyles="solid", linewidths=2)
        # ax.clabel(cs_v1, fontsize=8, fmt='%i')
        # cs_v2 = ax.contour(self.horizontal_coordinate,
        #                     curtain_p, curtain_v, np.arange(95, 150, 5),
        #                     colors="black", linestyles="solid", linewidths=0.5)
        # ax.clabel(cs_v2, fontsize=8, fmt='%i')

        # [0.01, 0.03, 0.05, 0.07, 0.1, 0.3, 0.5, 0.7, 1.0]

        cs_v1 = ax.contour(self.horizontal_coordinate,
                           curtain_p, curtain_clwc, [0.01, 0.03, 0.05, 0.07, 0.1, 0.3, 0.5, 0.7, 1.0],
                           colors="blue", linestyles="solid", linewidths=1)
        ax.clabel(cs_v1, fontsize=8, fmt='%.1f')

        cs_v1 = ax.contour(self.horizontal_coordinate,
                           curtain_p, curtain_ciwc, [0.01, 0.03, 0.05, 0.07, 0.1, 0.3, 0.5, 0.7, 1.0],
                           colors="white", linestyles="solid", linewidths=1)
        ax.clabel(cs_v1, fontsize=8, fmt='%.1f')

        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.horizontal_coordinate,
                           curtain_p, curtain_pt, np.arange(200, 700, delta_pt), colors='black',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :])
        self.add_colorbar(cs, "Probability of WCB (%)")


class VS_LagrantoTrajStyle_PL_01(AbstractVerticalSectionStyle):
    """
    Number of Lagranto trajectories per grid box for WCB, MIX, INSITU
    trajectories (ML-Cirrus 2014 product).
    """

    name = "VS_LGTRAJ01"
    title = "Cirrus density, insitu red, mix blue, wcb colour (1E-6/km^2/hPa) Vertical Section"
    abstract = "Cirrus density, insitu red, mix blue, wcb colour (1E-6/km^2/hPa)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("pl", "air_pressure", "Pa"),
        ("pl", "number_of_wcb_trajectories", 'dimensionless'),
        ("pl", "number_of_insitu_trajectories", 'dimensionless'),
        ("pl", "number_of_mix_trajectories", 'dimensionless')
    ]

    def _plot_style(self):
        """Make a horizontal velocity vertical section with temperature/potential
           temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_wcb = 1.E6 * self.data["number_of_wcb_trajectories"]
        curtain_insitu = 1.E6 * self.data["number_of_insitu_trajectories"]
        curtain_mix = 1.E6 * self.data["number_of_mix_trajectories"]

        thin_contours = [0.1, 0.5, 1., 2., 3., 4., 5., 6., 7., 8.]

        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.horizontal_coordinate, curtain_p, curtain_wcb,
                         thin_contours, cmap=plt.cm.gist_ncar_r, extend="max")

        cs_v1 = ax.contour(self.horizontal_coordinate,
                           curtain_p, curtain_insitu, thin_contours,
                           colors="red", linestyles="solid", linewidths=1)
        ax.clabel(cs_v1, fontsize=8, fmt='%.1f')

        cs_v1 = ax.contour(self.horizontal_coordinate,
                           curtain_p, curtain_mix, thin_contours,
                           colors="darkblue", linestyles="solid", linewidths=1)
        ax.clabel(cs_v1, fontsize=8, fmt='%.1f')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :])
        self.add_colorbar(cs, "Cirrus density")


class VS_EMACEyja_Style_01(AbstractVerticalSectionStyle):
    """
    EMAC Eyjafjallajokull
    EMAC Eyja tracer vertical cross sections.
    """

    name = "VS_EMAC_Eyja_01"
    title = "EMAC Eyjafjallajokull Tracer (relative) Vertical Section"
    abstract = "EMAC Eyjafjallajokull Tracer (relative) with temperature (K) and potential temp. (K)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure", "Pa"),
        ("ml", "air_temperature", "K"),
        ("ml", "emac_R12", 'dimensionless')]

    def _prepare_datafields(self):
        """Computes potential temperature from pressure and temperature if
        it has not been passed as a data field.
        """
        self.data['air_potential_temperature'] = thermolib.pot_temp(
            self.data['air_pressure'], self.data['air_temperature'])

    def _plot_style(self):
        """
        Make a volcanic ash cloud cover vertical section with temperature/potential
        temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_t = self.data["air_temperature"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_cc = self.data["emac_R12"] * 1.e4

        # Contour spacing for temperature lines.
        delta_t = 2 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 4
        delta_pt = 5 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 10

        # Filled contour plot of volcanic ash.
        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.horizontal_coordinate,
                         curtain_p, curtain_cc, np.arange(1, 101, 1), cmap=plt.cm.hot_r,
                         norm=matplotlib.colors.LogNorm(vmin=1., vmax=100.))
        # csl = ax.contour(self.horizontal_coordinate,
        #                 curtain_p, curtain_cc, np.arange(1, 101, 1), colors="k", linewidths=1)
        # ax.clabel(csl, fontsize=8, fmt='%i')
        # Contour line plot of temperature.
        cs_t = ax.contour(self.horizontal_coordinate,
                          curtain_p, curtain_t, np.arange(236, 330, delta_t),
                          colors='red', linestyles='solid', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.horizontal_coordinate, curtain_p, curtain_t, [234],
                          colors='red', linestyles='solid', linewidths=2)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.horizontal_coordinate,
                          curtain_p, curtain_t, np.arange(160, 232, delta_t),
                          colors='red', linestyles='dashed', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.horizontal_coordinate, curtain_p, curtain_pt,
                           np.arange(200, 700, delta_pt), colors='grey',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :])
        self.add_colorbar(cs, "Eyjafjallajokull Tracer (relative)")
