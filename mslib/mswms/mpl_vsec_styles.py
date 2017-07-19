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
    :copyright: Copyright 2016-2017 by the mss team, see AUTHORS.
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

import matplotlib
import matplotlib.pyplot as plt
import mpl_toolkits.axes_grid1.inset_locator
from matplotlib import patheffects
import numpy as np

from mslib.mswms.mpl_vsec import AbstractVerticalSectionStyle
from mslib.mswms.utils import Targets, get_style_parameters, get_cbar_label_format
from mslib.mswms.msschem import MSSChemTargets
from mslib import thermolib


class VS_TemperatureStyle_01(AbstractVerticalSectionStyle):
    """
    Temperature
    Vertical section of temperature.

    """

    name = "VS_T01"
    title = "Temperature (K) Vertical Section"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure"),
        ("ml", "air_temperature")]

    def _prepare_datafields(self):
        """Computes potential temperature from pressure and temperature if
        it has not been passed as a data field.
        """
        if 'air_potential_temperature' not in self.data:
            self.data['air_potential_temperature'] = \
                thermolib.pot_temp(self.data['air_pressure'],
                                   self.data['air_temperature'])

    def _plot_style(self):
        """Make a temperature/potential temperature vertical section.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_t = self.data["air_temperature"]
        curtain_pt = self.data["air_potential_temperature"]

        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)

        # Filled contour plot of temperature.
        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                         curtain_p, curtain_t, np.arange(180, 250, 2))  # 180-200, gist_earth Greens
        # Contour line plot of temperature.
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, np.arange(160, 330, 4),
                          colors='orange', linestyles='solid', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_pt, np.arange(200, 700, 10), colors='grey',
                           linestyles='dashed', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :],
                                titlestring="Temperature (K) and potential temperature (K)")

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            cbar = self.fig.colorbar(cs, fraction=0.05, pad=0.01)
            cbar.set_label("Temperature (K)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="1%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=1)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")


class VS_GenericStyle(AbstractVerticalSectionStyle):
    """
    Vertical section of chemical species/other stuff
    """
    styles = [
        ("auto", "auto colour scale"),
        ("autolog", "auto log colour scale"), ]

    def _prepare_datafields(self):
        if self.name[-2:] == "pl":
            self.data["air_pressure"] = np.empty_like(self.data[self.dataname])
            self.data["air_pressure"][:] = self.driver.vert_data[::-self.driver.vert_order, np.newaxis]
            self.data_units["air_pressure"] = self.driver.vert_units
        elif self.name[-2:] == "tl":
            self.data["air_potential_temperature"] = np.empty_like(self.data[self.dataname])
            self.data["air_potential_temperature"][:] = self.driver.vert_data[::-self.driver.vert_order, np.newaxis]

        if self.data_units["air_pressure"] not in ["Pa", "hPa"]:
            raise ValueError("air_pressure neither hPa nor Pa: %s", self.data_units["air_pressure"])
        if self.data_units["air_pressure"] == "hPa":
            self.data["air_pressure"] *= 100

    def _plot_style(self):
        ax = self.ax
        curtain_cc = self.data[self.dataname] * self.unit_scale
        curtain_cc = np.ma.masked_invalid(curtain_cc)
        curtain_p = self.data["air_pressure"]

        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)
        curtain_lat = self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose()

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

        cs = ax.contourf(curtain_lat, curtain_p, curtain_cc, clevs, cmap=cmap, extend="both", norm=norm)

        # Contour lines
        for cont_data, cont_levels, cont_colour, cont_label_colour, cont_style, cont_lw, pe in self.contours:
            if cont_levels is None:
                pl_cont = ax.plot(self.lat_inds, self.data[cont_data].reshape(-1), "o", color="k", zorder=100)
                plt.setp(pl_cont, path_effects=[patheffects.withStroke(linewidth=4, foreground="w")])
            else:
                cs_pv = ax.contour(curtain_lat, curtain_p, self.data[cont_data], cont_levels,
                                   colors=cont_colour, linestyles=cont_style, linewidths=cont_lw)
                plt.setp(cs_pv.collections,
                         path_effects=[patheffects.withStroke(linewidth=cont_lw + 2, foreground="w")])
                cs_pv_lab = ax.clabel(cs_pv, colours=cont_label_colour, fontsize=8, fmt='%i')
                plt.setp(cs_pv_lab, path_effects=[patheffects.withStroke(linewidth=1, foreground="w")])

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(titlestring=self.title)

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

            # adjust colorbar fontsize to figure height
            fontsize = self.fig.bbox.height * 0.024
            axins1.yaxis.set_ticks_position("left")
            for x in axins1.yaxis.majorTicks:
                x.label1.set_path_effects([patheffects.withStroke(linewidth=4, foreground='w')])
                x.label1.set_fontsize(fontsize)


def make_generic_class(name, entity, vert, add_data=None, add_contours=None,
                       fix_styles=None, add_styles=None, add_prepare=None):
    if add_data is None:
        add_data = [(vert, "ertel_potential_vorticity")]
    if add_contours is None:
        add_contours = [  # ("ertel_potential_vorticity", [2, 4, 8, 16], "dimgrey", "dimgrey", "solid", 2, True)]
            ("ertel_potential_vorticity", [2, 4, 8, 16], "dimgrey", "dimgrey", "dashed", 2, True),
            ("air_potential_temperature", np.arange(200, 700, 10), "dimgrey", "dimgrey", "solid", 2, True)]

    class fnord(VS_GenericStyle):
        name = u"VS_{}_{}".format(entity, vert)
        dataname = entity
        units, unit_scale = Targets.get_unit(dataname)
        title = Targets.TITLES.get(entity, entity)
        if units:
            title += u" ({})".format(units)
        required_datafields = [(vert, entity)] + add_data
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
    "pl": [("pl", "ertel_potential_vorticity"), ("pl", "air_potential_temperature")],
    "ml": [("ml", "ertel_potential_vorticity"), ("ml", "air_pressure"), ("ml", "air_potential_temperature")],
    "tl": [("tl", "ertel_potential_vorticity"), ("tl", "air_pressure")]
}

for vert in ["pl", "ml", "tl"]:
    for ent in Targets.get_targets():
        make_generic_class(
            "VS_GenericStyle_{}_{}".format(vert.upper(), ent),
            ent, vert, add_data=_ADD_DATA[vert])
    make_generic_class(
        "VS_GenericStyle_{}_{}".format(vert.upper(), "ertel_potential_vorticity"),
        "ertel_potential_vorticity", vert, add_data=_ADD_DATA[vert],
        fix_styles=[("ertel_potential_vorticity_nh", "northern hemisphere"),
                    ("ertel_potential_vorticity_sh", "southern hemisphere")])
    make_generic_class(
        "VS_GenericStyle_{}_{}".format(vert.upper(), "equivalent_latitude"),
        "equivalent_latitude", vert, add_data=_ADD_DATA[vert],
        fix_styles=[("equivalent_latitude_nh", "northern hemisphere"),
                    ("equivalent_latitude_sh", "southern hemisphere")])
    make_generic_class(
        "VS_GenericStyle_{}_{}".format(vert.upper(), "square_of_brunt_vaisala_frequency_in_air"),
        "square_of_brunt_vaisala_frequency_in_air", vert, add_data=_ADD_DATA[vert],
        fix_styles=[("square_of_brunt_vaisala_frequency_in_air", "")])
vert = "al"
make_generic_class(
    "VS_GenericStyle_{}_{}".format(vert.upper(), "gravity_wave_temperature_perturbation"),
    "air_temperature_residual", vert,
    add_data=[("sfc", "secondary_tropopause_air_pressure"), ("sfc", "tropopause_air_pressure"), ("al", "air_pressure")],
    add_contours=[("tropopause_air_pressure", None, "dimgrey", "dimgrey", "solid", 2, True),
                  ("secondary_tropopause_air_pressure", None, "dimgrey", "dimgrey", "solid", 2, True)],
    fix_styles=[("gravity_wave_temperature_perturbation", "")])
make_generic_class(
    "VS_GenericStyle_{}_{}".format(vert.upper(), "square_of_brunt_vaisala_frequency_in_air"),
    "square_of_brunt_vaisala_frequency_in_air", vert,
    add_data=[("sfc", "tropopause_air_pressure"), ("al", "air_pressure")],
    add_contours=[("tropopause_air_pressure", None, "dimgrey", "dimgrey", "solid", 2, True)],
    fix_styles=[("square_of_brunt_vaisala_frequency_in_air", "")])

vert = "pl"
make_generic_class(
    "VS_GenericStyle_{}_{}".format(vert.upper(), "cloud_ice_mixing_ratio"),
    "cloud_ice_mixing_ratio", vert,
    add_data=[("pl", "maximum_relative_humidity_wrt_ice_on_backtrajectory")],
    add_contours=[("maximum_relative_humidity_wrt_ice_on_backtrajectory",
                  [90, 100, 120, 160],
                  ["dimgrey", "dimgrey", "#443322", "#045FB4"],
                  ["dimgrey", "dimgrey", "#443322", "#045FB4"],
                  ["dashed", "solid", "solid", "solid"], 2, True)],
    fix_styles=[("log_ice_cloud", "iwc")])

make_generic_class(
    "VS_GenericStyle_{}_{}".format(vert.upper(), "number_concentration_of_ice_crystals_in_air"),
    "number_concentration_of_ice_crystals_in_air", vert,
    add_data=[("pl", "maximum_relative_humidity_wrt_ice_on_backtrajectory")],
    add_contours=[("maximum_relative_humidity_wrt_ice_on_backtrajectory",
                  [90, 100, 120, 160],
                  ["dimgrey", "dimgrey", "#443322", "#045FB4"],
                  ["dimgrey", "dimgrey", "#443322", "#045FB4"],
                  ["dashed", "solid", "solid", "solid"], 2, True)],
    fix_styles=[("log_ice_cloud", "nice")])

make_generic_class(
    "VS_GenericStyle_{}_{}".format(vert.upper(), "mean_mass_radius_of_cloud_ice_crystals"),
    "mean_mass_radius_of_cloud_ice_crystals", vert,
    add_data=[("pl", "maximum_relative_humidity_wrt_ice_on_backtrajectory")],
    add_contours=[("maximum_relative_humidity_wrt_ice_on_backtrajectory",
                  [90, 100, 120, 160],
                  ["dimgrey", "dimgrey", "#443322", "#045FB4"],
                  ["dimgrey", "dimgrey", "#443322", "#045FB4"],
                  ["dashed", "solid", "solid", "solid"], 2, True)],
    fix_styles=[("ice_cloud", "radius")])

make_generic_class(
    "VS_GenericStyle_{}_{}".format(vert.upper(), "maximum_pressure_on_backtrajectory"),
    "maximum_pressure_on_backtrajectory", vert, [], [])


class VS_CloudsStyle_01(AbstractVerticalSectionStyle):
    """
    Clouds
    Vertical section of cloud cover.
    """

    name = "VS_CC01"
    title = "Cloud Cover (0-1) Vertical Section"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure"),
        ("ml", "air_temperature"),
        ("ml", "cloud_area_fraction_in_atmosphere_layer")]

    def _prepare_datafields(self):
        """Computes potential temperature from pressure and temperature if
        it has not been passed as a data field.
        """
        if 'air_potential_temperature' not in self.data:
            self.data['air_potential_temperature'] = \
                thermolib.pot_temp(self.data['air_pressure'],
                                   self.data['air_temperature'])

    def _plot_style(self):
        """Make a cloud cover vertical section with temperature/potential
           temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_t = self.data["air_temperature"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_cc = self.data["cloud_area_fraction_in_atmosphere_layer"]

        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)

        # Contour spacing for temperature lines.
        delta_t = 2 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 4
        delta_pt = 5 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 10

        # Filled contour plot of cloud cover.
        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                         curtain_p, curtain_cc, np.arange(0.2, 1.1, 0.1), cmap=plt.cm.winter)
        # Contour line plot of temperature.
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, np.arange(236, 330, delta_t),
                          colors='red', linestyles='solid', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, [234],
                          colors='red', linestyles='solid', linewidths=2)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, np.arange(160, 232, delta_t),
                          colors='red', linestyles='dashed', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_pt, np.arange(200, 700, delta_pt), colors='grey',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :],
                                titlestring="Cloud cover (0-1) with temperature (K) "
                                            "and potential temperature (K)")

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            cbar = self.fig.colorbar(cs, fraction=0.05, pad=0.01)
            cbar.set_label("Cloud cover (0-1)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="1%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=1)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")


class VS_CloudsWindStyle_01(AbstractVerticalSectionStyle):
    """
    Vertical section of cloud cover and horizontal wind speed.
    """

    name = "VS_CW01"
    title = "Cloud Cover (0-1) and Wind Speed (m/s) Vertical Section"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure"),
        ("ml", "air_temperature"),
        ("ml", "cloud_area_fraction_in_atmosphere_layer"),
        ("ml", "eastward_wind"),
        ("ml", "northward_wind")]

    def _prepare_datafields(self):
        """Computes potential temperature from pressure and temperature and
           total horizontal wind speed.
        """
        if 'air_potential_temperature' not in self.data:
            self.data['air_potential_temperature'] = \
                thermolib.pot_temp(self.data['air_pressure'],
                                   self.data['air_temperature'])
        self.data["horizontal_wind"] = np.sqrt(self.data["eastward_wind"] ** 2 +
                                               self.data["northward_wind"] ** 2)

    def _plot_style(self):
        """Make a cloud cover vertical section with wind speed and potential
           temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_cc = self.data["cloud_area_fraction_in_atmosphere_layer"]
        curtain_v = self.data["horizontal_wind"]

        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)

        # Contour spacing for temperature lines.
        delta_pt = 5 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 10

        wind_contours = np.arange(20, 70, 10)

        # Filled contour plot of cloud cover.
        cs = ax.contourf(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                         curtain_p, curtain_cc, np.arange(0.2, 1.1, 0.1), cmap=plt.cm.winter)

        # Contour line plot of wind speed.
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_v, wind_contours,
                          colors='red', linestyles='solid', linewidths=2)  # gist_earth
        ax.clabel(cs_t, fontsize=12, fmt='%i')

        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_pt, np.arange(200, 700, delta_pt), colors='0.40',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=12, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :],
                                titlestring="Cloud cover (0-1) with wind speed (m/s) "
                                            "and potential temperature (K)")

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            cbar = self.fig.colorbar(cs, fraction=0.05, pad=0.01)
            cbar.set_label("Cloud cover (0-1)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="1%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=1)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")


class VS_RelativeHumdityStyle_01(AbstractVerticalSectionStyle):
    """
    Vertical sections of relative humidity.
    """

    name = "VS_RH01"
    title = "Relative Humdity (%) Vertical Section"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure"),
        ("ml", "air_temperature"),
        ("ml", "specific_humidity")]

    def _prepare_datafields(self):
        """Computes potential temperature from pressure and temperature if
        it has not been passed as a data field. Also computes relative humdity.
        """
        if 'air_potential_temperature' not in self.data:
            self.data['air_potential_temperature'] = \
                thermolib.pot_temp(self.data['air_pressure'],
                                   self.data['air_temperature'])
        self.data["relative_humidity"] = \
            thermolib.rel_hum(self.data['air_pressure'],
                              self.data["air_temperature"],
                              self.data["specific_humidity"])

    def _plot_style(self):
        """Make a relative humidity vertical section with temperature/potential
           temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_t = self.data["air_temperature"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_rh = self.data["relative_humidity"]

        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)

        # Contour spacing for temperature lines.
        delta_t = 2 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 4
        delta_pt = 5 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 10

        filled_contours = np.arange(70, 140, 15)
        thin_contours = np.arange(10, 140, 15)

        # Filled contour plot of relative humidity.
        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                         curtain_p, curtain_rh,
                         filled_contours, cmap=plt.cm.winter_r)
        # Contour line plot of relative humidity.
        cs_rh1 = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                            curtain_p, curtain_rh, thin_contours,
                            colors="grey", linestyles="solid", linewidths=0.5)  # gist_earth
        ax.clabel(cs_rh1, fontsize=8, fmt='%i')
        ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                   curtain_p, curtain_rh, np.arange(100, 170, 15),
                   colors="yellow", linestyles="solid", linewidths=1)  # gist_earth
        # Contour line plot of temperature.
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, np.arange(236, 330, delta_t),
                          colors='red', linestyles='solid', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, [234],
                          colors='red', linestyles='solid', linewidths=2)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, np.arange(160, 232, delta_t),
                          colors='red', linestyles='dashed', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_pt, np.arange(200, 700, delta_pt), colors='orange',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :],
                                titlestring="Relative humdity (%) with temperature (K) "
                                            "and potential temperature (K)")

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            cbar = self.fig.colorbar(cs, fraction=0.05, pad=0.01)
            cbar.set_label("Relative humdity (%)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="1%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=1)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")


class VS_SpecificHumdityStyle_01(AbstractVerticalSectionStyle):
    """
    Vertical sections of specific humidity.
    """

    name = "VS_Q01"
    # title = "Specific Humdity (g/kg) and Northward Wind (m/s) Vertical Section"
    title = "Specific Humdity (g/kg) Vertical Section"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure"),
        ("ml", "air_temperature"),
        ("ml", "specific_humidity"),
        ("ml", "northward_wind")]

    def _prepare_datafields(self):
        """Computes potential temperature from pressure and temperature if
        it has not been passed as a data field. Also computes relative humdity.
        """
        if 'air_potential_temperature' not in self.data:
            self.data['air_potential_temperature'] = \
                thermolib.pot_temp(self.data['air_pressure'],
                                   self.data['air_temperature'])

    def _plot_style(self):
        """Make a relative humidity vertical section with temperature/potential
           temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_t = self.data["air_temperature"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_q = self.data["specific_humidity"] * 1000.  # convert from kg/kg to g/kg

        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)

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
        cs = ax.contourf(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                         curtain_p, curtain_q,
                         filled_contours, cmap=plt.cm.YlGnBu)  # YlGnBu
        cs_q = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_q,
                          filled_contours, colours="c", linestyles="solid", linewidths=1)
        ax.clabel(cs_q, fontsize=8, fmt='%.2f')

        # Contour line plot of northward wind (v).
        # cs_v = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
        #                  curtain_p, curtain_v, np.arange(5,15,2.5),
        #                  colors="black", linestyles="solid", linewidths=1)
        # ax.clabel(cs_v, fontsize=8, fmt='%.1f')

        # Contour line plot of temperature.
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, np.arange(236, 330, delta_t),
                          colors='red', linestyles='solid', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, [234],
                          colors='red', linestyles='solid', linewidths=2)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, np.arange(160, 232, delta_t),
                          colors='red', linestyles='dashed', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')

        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_pt, np.arange(200, 700, delta_pt), colors='orange',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%.1f')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :],
                                titlestring="Specific humdity (g/kg) with temperature (K) "
                                            "and potential temperature (K)")

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            cbar = self.fig.colorbar(cs, fraction=0.05, pad=0.01)
            cbar.set_label("Specific humdity (g/kg)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="1%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=1)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")


class VS_VerticalVelocityStyle_01(AbstractVerticalSectionStyle):
    """
    Vertical sections of vertical velocity.
    """

    name = "VS_W01"
    title = "Vertical Velocity (cm/s) Vertical Section"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure"),
        ("ml", "air_temperature"),
        ("ml", "lagrangian_tendency_of_air_pressure")]

    def _prepare_datafields(self):
        """Computes potential temperature from pressure and temperature if
        it has not been passed as a data field. Also computes vertical
        velocity in cm/s.
        """
        if 'air_potential_temperature' not in self.data:
            self.data['air_potential_temperature'] = \
                thermolib.pot_temp(self.data['air_pressure'],
                                   self.data['air_temperature'])
        self.data["upward_wind"] = \
            thermolib.omega_to_w(self.data["lagrangian_tendency_of_air_pressure"],
                                 self.data['air_pressure'],
                                 self.data["air_temperature"])

    def _plot_style(self):
        """Make a vertical velocity vertical section with temperature/potential
           temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_t = self.data["air_temperature"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_w = self.data["upward_wind"] * 100.

        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)

        # Contour spacing for temperature lines.
        delta_t = 2 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 4
        delta_pt = 5 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 10

        upward_contours = np.arange(-42, 46, 4)

        # Filled contour plot of relative humidity.
        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                         curtain_p, curtain_w,
                         upward_contours, cmap=plt.cm.bwr)
        # Contour line plot of relative humidity.
        ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                   curtain_p, curtain_w, [2],
                   colors="red", linestyles="solid", linewidths=0.5)
        ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                   curtain_p, curtain_w, [-2],
                   colors="blue", linestyles="solid", linewidths=0.5)
        # Contour line plot of temperature.
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, np.arange(236, 330, delta_t),
                          colors='green', linestyles='solid', linewidths=1)
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, [234],
                          colors='green', linestyles='solid', linewidths=2)
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, np.arange(160, 232, delta_t),
                          colors='green', linestyles='dashed', linewidths=1)
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_pt, np.arange(200, 700, delta_pt), colors='grey',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :],
                                titlestring="Vertical velocity (cm/s) with temperature (K) "
                                            "and potential temperature (K)")

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            cbar = self.fig.colorbar(cs, fraction=0.05, pad=0.01)
            cbar.set_label("Vertical velocity (cm/s)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="1%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=1)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")


class VS_HorizontalVelocityStyle_01(AbstractVerticalSectionStyle):
    """
    Vertical sections of horizontal velocity.
    """

    name = "VS_HV01"
    title = "Horizontal Wind (m/s) Vertical Section"

    # NOTE: This style is used for the flight performance computations. Make sure
    # that it always requests air_pressure, air_temperature, eastward_wind,
    # northward_wind! (mr, 2012Nov09)

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure"),
        ("ml", "air_temperature"),
        ("ml", "eastward_wind"),
        ("ml", "northward_wind")]

    def _prepare_datafields(self):
        """Computes potential temperature from pressure and temperature and
           total horizontal wind speed.
        """
        if 'air_potential_temperature' not in self.data:
            self.data['air_potential_temperature'] = \
                thermolib.pot_temp(self.data['air_pressure'],
                                   self.data['air_temperature'])
        self.data["horizontal_wind"] = np.sqrt(self.data["eastward_wind"] ** 2 +
                                               self.data["northward_wind"] ** 2)

    def _plot_style(self):
        """Make a horizontal velocity vertical section with temperature/potential
           temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_t = self.data["air_temperature"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_v = self.data["horizontal_wind"]

        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)

        # Contour spacing for temperature lines.
        delta_t = 2 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 4
        delta_pt = 5 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 10

        wind_contours = np.arange(10, 90, 5)

        # Filled contour plot of relative humidity.
        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                         curtain_p, curtain_v,
                         wind_contours, cmap=plt.cm.hot_r)
        # Contour line plot of relative humidity.
        cs_v1 = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_v, np.arange(5, 90, 5),
                           colors="orange", linestyles="solid", linewidths=1)
        ax.clabel(cs_v1, fontsize=8, fmt='%i')
        cs_v2 = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_v, np.arange(95, 150, 5),
                           colors="black", linestyles="solid", linewidths=0.5)
        ax.clabel(cs_v2, fontsize=8, fmt='%i')
        # Contour line plot of temperature.
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, np.arange(236, 330, delta_t),
                          colors='green', linestyles='solid', linewidths=1)
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, [234],
                          colors='green', linestyles='solid', linewidths=2)
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, np.arange(160, 232, delta_t),
                          colors='green', linestyles='dashed', linewidths=1)
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_pt, np.arange(200, 700, delta_pt), colors='grey',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :],
                                titlestring="Horizontal wind speed (m/s) with temperature (K) "
                                            "and potential temperature (K)")

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            cbar = self.fig.colorbar(cs, fraction=0.05, pad=0.01)
            cbar.set_label("Horizontal wind speed (m/s)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="1%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=1)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")


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
    styles = [
        ("default", "Northern Hemisphere"),
        ("NH", "Northern Hemisphere"),
        ("SH", "Southern Hemisphere, neg. PVU")]

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure"),
        ("ml", "air_temperature"),
        ("ml", "eastward_wind"),
        ("ml", "northward_wind"),
        ("ml", "specific_cloud_liquid_water_content"),
        ("ml", "specific_cloud_ice_water_content"),
        ("ml", "ertel_potential_vorticity")]

    def _prepare_datafields(self):
        """Computes potential temperature from pressure and temperature and
           total horizontal wind speed.
        """
        if 'air_potential_temperature' not in self.data:
            self.data['air_potential_temperature'] = \
                thermolib.pot_temp(self.data['air_pressure'],
                                   self.data['air_temperature'])
        self.data["horizontal_wind"] = np.sqrt(self.data["eastward_wind"] ** 2 +
                                               self.data["northward_wind"] ** 2)

    def _plot_style(self):
        """Make a horizontal velocity vertical section with temperature/potential
           temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_pv = self.data["ertel_potential_vorticity"]
        curtain_clwc = self.data["specific_cloud_liquid_water_content"] * 1000.
        curtain_ciwc = self.data["specific_cloud_ice_water_content"] * 1000.

        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)

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
        cs = ax.contourf(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                         curtain_p, curtain_pv,
                         pv_contours, cmap=pv_eth_cmap_1)

        # Contour line plot of horizontal wind.
        # cs_v1 = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
        #                     curtain_p, curtain_v, np.arange(5, 90, 5),
        #                     colors="green", linestyles="solid", linewidths=2)
        # ax.clabel(cs_v1, fontsize=8, fmt='%i')
        # cs_v2 = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
        #                     curtain_p, curtain_v, np.arange(95, 150, 5),
        #                     colors="black", linestyles="solid", linewidths=0.5)
        # ax.clabel(cs_v2, fontsize=8, fmt='%i')

        # [0.01, 0.03, 0.05, 0.07, 0.1, 0.3, 0.5, 0.7, 1.0]

        cs_v1 = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_clwc, [0.01, 0.03, 0.05, 0.07, 0.1, 0.3, 0.5, 0.7, 1.0],
                           colors="blue", linestyles="solid", linewidths=1)
        ax.clabel(cs_v1, fontsize=8, fmt='%.1f')

        cs_v1 = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_ciwc, [0.01, 0.03, 0.05, 0.07, 0.1, 0.3, 0.5, 0.7, 1.0],
                           colors="white", linestyles="solid", linewidths=1)
        ax.clabel(cs_v1, fontsize=8, fmt='%.1f')

        # Contour line plot of temperature.
        # cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
        #                   curtain_p, curtain_t, np.arange(236, 330, delta_t),
        #                   colors='green', linestyles='solid', linewidths=1)
        # ax.clabel(cs_t, fontsize=8, fmt='%i')
        # cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
        #                   curtain_p, curtain_t, [234],
        #                   colors='green', linestyles='solid', linewidths=2)
        # ax.clabel(cs_t, fontsize=8, fmt='%i')
        # cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
        #                   curtain_p, curtain_t, np.arange(160, 232, delta_t),
        #                   colors='green', linestyles='dashed', linewidths=1)
        # ax.clabel(cs_t, fontsize=8, fmt='%i')

        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_pt, np.arange(200, 700, delta_pt), colors='black',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        if self.style.upper() == "SH":
            tstr = "Neg. potential vorticity (PVU) with CLWC/CIWC (g/kg) " \
                   "and potential temperature (K)"
        else:
            tstr = "Potential vorticity (PVU) with CLWC/CIWC (g/kg) " \
                   "and potential temperature (K)"
        self._latlon_logp_setup(orography=curtain_p[0, :], titlestring=tstr)

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            cbar = self.fig.colorbar(cs, fraction=0.05, pad=0.01)
            if self.style.upper() == "SH":
                cbar.set_label("Negative Potential vorticity (PVU)")
            else:
                cbar.set_label("Potential vorticity (PVU)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="1%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=1)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")


class VS_ProbabilityOfWCBStyle_01(AbstractVerticalSectionStyle):
    """
    Probability of WCB
    Vertical sections of probability of WCB trajectory occurence,
    derived from Lagranto trajectories (TNF 2012 product).
    """

    name = "VS_PWCB01"
    title = "Probability of WCB (%) Vertical Section"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure"),
        ("ml", "air_temperature"),
        ("ml", "eastward_wind"),
        ("ml", "northward_wind"),
        ("ml", "specific_cloud_liquid_water_content"),
        ("ml", "specific_cloud_ice_water_content"),
        ("ml", "probability_of_wcb_occurrence")]

    def _prepare_datafields(self):
        """Computes potential temperature from pressure and temperature and
           total horizontal wind speed.
        """
        if 'air_potential_temperature' not in self.data:
            self.data['air_potential_temperature'] = \
                thermolib.pot_temp(self.data['air_pressure'],
                                   self.data['air_temperature'])
        self.data["horizontal_wind"] = np.sqrt(self.data["eastward_wind"] ** 2 +
                                               self.data["northward_wind"] ** 2)

    def _plot_style(self):
        """Make a horizontal velocity vertical section with temperature/potential
           temperature overlay.
        """
        ax = self.ax
        curtain_p = self.data["air_pressure"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_pwcb = self.data["probability_of_wcb_occurrence"] * 100.
        curtain_clwc = self.data["specific_cloud_liquid_water_content"] * 1000.
        curtain_ciwc = self.data["specific_cloud_ice_water_content"] * 1000.

        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)

        # Contour spacing for temperature lines.
        delta_pt = 5 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 10

        pwcb_contours = np.arange(0, 101, 10)

        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                         curtain_p, curtain_pwcb,
                         pwcb_contours, cmap=plt.cm.pink_r)

        # Contour line plot of horizontal wind.
        # cs_v1 = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
        #                     curtain_p, curtain_v, np.arange(5, 90, 5),
        #                     colors="green", linestyles="solid", linewidths=2)
        # ax.clabel(cs_v1, fontsize=8, fmt='%i')
        # cs_v2 = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
        #                     curtain_p, curtain_v, np.arange(95, 150, 5),
        #                     colors="black", linestyles="solid", linewidths=0.5)
        # ax.clabel(cs_v2, fontsize=8, fmt='%i')

        # [0.01, 0.03, 0.05, 0.07, 0.1, 0.3, 0.5, 0.7, 1.0]

        cs_v1 = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_clwc, [0.01, 0.03, 0.05, 0.07, 0.1, 0.3, 0.5, 0.7, 1.0],
                           colors="blue", linestyles="solid", linewidths=1)
        ax.clabel(cs_v1, fontsize=8, fmt='%.1f')

        cs_v1 = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_ciwc, [0.01, 0.03, 0.05, 0.07, 0.1, 0.3, 0.5, 0.7, 1.0],
                           colors="white", linestyles="solid", linewidths=1)
        ax.clabel(cs_v1, fontsize=8, fmt='%.1f')

        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_pt, np.arange(200, 700, delta_pt), colors='black',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :],
                                titlestring="Probability of WCB (%) with CLWC/CIWC (g/kg) "
                                            "and potential temperature (K)")

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            cbar = self.fig.colorbar(cs, fraction=0.05, pad=0.01)
            cbar.set_label("Probability of WCB (%)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="1%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=1)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")


class VS_LagrantoTrajStyle_PL_01(AbstractVerticalSectionStyle):
    """
    Number of Lagranto trajectories per grid box for WCB, MIX, INSITU
    trajectories (ML-Cirrus 2014 product).
    """

    name = "VS_LGTRAJ01"
    title = "Cirrus density, insitu red, mix blue, wcb colour (1E-6/km^2/hPa) Vertical Section"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("pl", "air_pressure"),
        ("pl", "number_of_wcb_trajectories"),
        ("pl", "number_of_insitu_trajectories"),
        ("pl", "number_of_mix_trajectories")
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

        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)

        thin_contours = [0.1, 0.5, 1., 2., 3., 4., 5., 6., 7., 8.]

        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                         curtain_p, curtain_wcb,
                         thin_contours, cmap=plt.cm.gist_ncar_r, extend="max")

        cs_v1 = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_insitu, thin_contours,
                           colors="red", linestyles="solid", linewidths=1)
        ax.clabel(cs_v1, fontsize=8, fmt='%.1f')

        cs_v1 = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_mix, thin_contours,
                           colors="darkblue", linestyles="solid", linewidths=1)
        ax.clabel(cs_v1, fontsize=8, fmt='%.1f')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :],
                                titlestring="Cirrus density, insitu red, mix blue, wcb colour (1E-6/km^2/hPa) "
                                            "Vertical Section")

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            cbar = self.fig.colorbar(cs, fraction=0.05, pad=0.01)
            cbar.set_label("Cirrus density")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="1%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=1)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")


class VS_EMACEyja_Style_01(AbstractVerticalSectionStyle):
    """
    EMAC Eyjafjallajokull
    EMAC Eyja tracer vertical cross sections.
    """

    name = "VS_EMAC_Eyja_01"
    title = "EMAC Eyjafjallajokull Tracer (relative) Vertical Section"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure"),
        ("ml", "air_temperature"),
        ("ml", "emac_R12")]

    def _prepare_datafields(self):
        """Computes potential temperature from pressure and temperature if
        it has not been passed as a data field.
        """
        if 'air_potential_temperature' not in self.data:
            self.data['air_potential_temperature'] = \
                thermolib.pot_temp(self.data['air_pressure'],
                                   self.data['air_temperature'])

    def _plot_style(self):
        """Make a volcanic ash cloud cover vertical section with temperature/potential
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

        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)

        # Filled contour plot of volcanic ash.
        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cs = ax.contourf(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                         curtain_p, curtain_cc, np.arange(1, 101, 1), cmap=plt.cm.hot_r,
                         norm=matplotlib.colors.LogNorm(vmin=1., vmax=100.))
        # csl = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
        #                 curtain_p, curtain_cc, np.arange(1, 101, 1), colors="k", linewidths=1)
        # ax.clabel(csl, fontsize=8, fmt='%i')
        # Contour line plot of temperature.
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, np.arange(236, 330, delta_t),
                          colors='red', linestyles='solid', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, [234],
                          colors='red', linestyles='solid', linewidths=2)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        cs_t = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                          curtain_p, curtain_t, np.arange(160, 232, delta_t),
                          colors='red', linestyles='dashed', linewidths=1)  # gist_earth
        ax.clabel(cs_t, fontsize=8, fmt='%i')
        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_pt, np.arange(200, 700, delta_pt), colors='grey',
                           linestyles='solid', linewidths=1)
        ax.clabel(cs_pt, fontsize=8, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(orography=curtain_p[0, :],
                                titlestring="EMAC Eyjafjallajokull Tracer (relative) "
                                            "with temperature (K) "
                                            "and potential temp. (K)")

        # Add colorbar.
        if not self.noframe:
            cbar = self.fig.colorbar(cs, fraction=0.08, pad=0.01)
            cbar.set_label("Eyjafjallajokull Tracer (relative)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="1%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=1)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")


class VS_MSSChemStyle(AbstractVerticalSectionStyle):
    """ CTM tracer vertical tracer cross sections via MSS-Chem
    """
    styles = [
        ("auto", "auto colour scale"),
        ("autolog", "auto log colour scale"), ]

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [("ml", "air_pressure")]

    # In order to use information from the DataAccess class to construct the titles, we override the set_driver to set
    # self.title.  This cannot happen in __init__, as the WMSServer doesn't initialize the layers with the driver but
    # rather sets the driver only after initialization.
    def set_driver(self, driver):
        super(VS_MSSChemStyle, self).set_driver(driver=driver)
        self.title = self._title_tpl.format(modelname=self.driver.data_access._modelname)
        # for altitude level model data, when we don't have air_pressure information, we want to warn users that the
        # vertical section is only an approximation
        if (self.name[-2:] == "al") and\
                ("air_pressure" not in list(self.driver.data_access.build_filetree().values())[0].values()[0]):
            self.title = self.title.replace(" al)", " al; WARNING: vert. distribution only approximate!)")

    def _prepare_datafields(self):
        """Computes potential temperature from pressure and temperature if
        it has not been passed as a data field.
        """
        if self.name[-2:] == "pl":
            self.data["air_pressure"] = np.empty_like(self.data[self.dataname])
            self.data["air_pressure"][:] = self.driver.vert_data[::-self.driver.vert_order, np.newaxis]
        elif self.name[-2:] == "tl":
            self.data["air_potential_temperature"] = np.empty_like(self.data[self.dataname])
            self.data["air_potential_temperature"][:] = self.driver.vert_data[::-self.driver.vert_order, np.newaxis]
        elif self.name[-2:] == "al":
            # CAMS Regional Ensemble doesn't provide any pressure information, but we want to plot vertical sections
            # anyways, so we do a poor-man's on-the-fly conversion here.
            if 'air_pressure' not in self.data:
                self.data["air_pressure"] = np.empty_like(self.data[self.dataname])
                flightlevel = 3.28083989501 / 100. * self.driver.vert_data[::-self.driver.vert_order, np.newaxis]
                self.data['air_pressure'][:] = thermolib.flightlevel2pressure_a(flightlevel)

    def _plot_style(self):
        ax = self.ax
        curtain_cc = self.data[self.dataname] * self.unit_scale
        curtain_cc = np.ma.masked_invalid(curtain_cc)
        curtain_p = self.data["air_pressure"]  # TODO* 100

        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)
        curtain_lat = self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose()

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

        cs = ax.contourf(curtain_lat, curtain_p, curtain_cc, clevs, cmap=cmap, extend="both", norm=norm)

        # Contour lines
        for cont_data, cont_levels, cont_colour, cont_label_colour, cont_style, cont_lw, pe in self.contours:
            if cont_levels is None:
                pl_cont = ax.plot(self.lat_inds, self.data[cont_data].reshape(-1), "o", color="k", zorder=100)
                plt.setp(pl_cont, path_effects=[patheffects.withStroke(linewidth=4, foreground="w")])
            else:
                cs_pv = ax.contour(curtain_lat, curtain_p, self.data[cont_data], cont_levels,
                                   colors=cont_colour, linestyles=cont_style, linewidths=cont_lw)
                plt.setp(cs_pv.collections,
                         path_effects=[patheffects.withStroke(linewidth=cont_lw + 2, foreground="w")])
                cs_pv_lab = ax.clabel(cs_pv, colours=cont_label_colour, fontsize=8, fmt='%i')
                plt.setp(cs_pv_lab, path_effects=[patheffects.withStroke(linewidth=1, foreground="w")])

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(titlestring=self.title)

        # Format for colorbar labels
        cbar_format = get_cbar_label_format(self.style, np.median(np.abs(clevs)))
        cbar_label = self.title

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            self.fig.colorbar(cs, fraction=0.05, pad=0.01, format=cbar_format, label=cbar_label, ticks=ticks)
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="1%", height="40%", loc=1)
            self.fig.colorbar(cs, cax=axins1, orientation="vertical", format=cbar_format, ticks=ticks)

            # adjust colorbar fontsize to figure height
            fontsize = self.fig.bbox.height * 0.024
            axins1.yaxis.set_ticks_position("left")
            for x in axins1.yaxis.majorTicks:
                x.label1.set_path_effects([patheffects.withStroke(linewidth=4, foreground='w')])
                x.label1.set_fontsize(fontsize)


def make_msschem_class(entity, nam, vert, units, scale, add_data=None,
                       add_contours=None, fix_styles=None, add_styles=None, add_prepare=None):

    # This is CTM output, so we cannot expect any additional meteorological
    # parameters except for air_pressure
    if add_data is None:
        if vert == "al":
            # "al" is altitude layer, i.e., for CTM output with no pressure information
            # at all (e.g., CAMS reg. Ensemble)
            # In those cases we derive air_pressure from the altitude alone, in the _prepare_datafields() method
            add_data = []
        elif vert == 'pl':
            # "pl" are pressure levels.  Here, the air_pressure information is implicitly contained in the vertical
            # dimension coordinate, so we don't need to explicitly load it here.
            add_data = []

        else:
            # all other layer types need to read air_pressure from the data
            add_data = [(vert, "air_pressure")]
    if add_contours is None:
        add_contours = []

    class fnord(VS_MSSChemStyle):
        name = "VS_" + entity + "_" + vert
        dataname = entity
        # units, unit_scale = Targets.get_unit(dataname)
        units = units
        unit_scale = scale
        _title_tpl = nam + " ({modelname}, " + vert + ")"
        long_name = entity
        if units:
            _title_tpl += u" ({})".format(units)
        required_datafields = [(vert, entity)] + add_data
        contours = add_contours if add_contours else []

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

    return fnord


for vert in ["ml", "tl", "pl", "al"]:
    for stdname, props in list(MSSChemTargets.items()):
        name, qty, units, scale = props
        key = "VS_MSSChemStyle_" + vert.upper() + "_" + name + "_" + qty
        globals()[key] = make_msschem_class(stdname, name, vert, units, scale)
