"""Matplotlib VERTICAL section styles.

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

This file is part of the DLR/IPA Mission Support System Web Map Service
(MSS-WMS).

This file corresponds to mpl_hsec_styles.py, but for vertical section styles.
Please refer to the introductory docstring in mpl_hsec_styles.py for further
information.

AUTHORS:
========

* Marc Rautenhaus (mr)

"""

# standard library imports
import logging

# related third party imports
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import mpl_toolkits.axes_grid1.inset_locator

# local application imports
from mpl_vsec import AbstractVerticalSectionStyle
from mslib import thermolib

"""
TEMPERATURE
"""


class VS_TemperatureStyle_01(AbstractVerticalSectionStyle):
    """Vertical section of temperature.
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
        if not 'air_potential_temperature' in self.data.keys():
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


CLAMS_CONFIG = {
    u'BVF': {'limits': (0.00029, 0.00095), 'units': u's**-2'},
    u'CH4': {'limits': (0.5, 1.7), 'units': u'ppmv'},
    u'CO': {'limits': (0., 150.), 'units': u'ppbv'},
    u'EQLAT': {'limits': (9.2, 90.0), 'units': u'deg N'},
    u'F11': {'limits': (0.0, 220.0), 'units': u'pptv'},
    u'F12': {'limits': (0.0, 550.0), 'units': u'pptv'},
    u'H2O': {'limits': (3.0, 3000.), 'units': u'ppmv'},
    u'N2O': {'limits': (45.0, 310.0), 'units': u'ppbv'},
    u'SEA': {'limits': (0.0, 70.), 'units': u'%'},
    u'ECH': {'limits': (0.0, 70.), 'units': u'%'},
    u'NIN': {'limits': (0.0, 70.), 'units': u'%'},
    u'SIN': {'limits': (0.0, 70.), 'units': u'%'},
    u'ICH': {'limits': (0.0, 50.), 'units': u'%'},
    u'O3': {'limits': (0.01, 3.0), 'units': u'ppmv'},
    u'PV': {'limits': (11.0, 120.0), 'units': u'PVU'},
    u'TEMP': {'limits': (180.0, 250.0), 'units': u'K'},
    u'THETA': {'limits': (440.0, 590.0), 'units': u'K'},
    u'U': {'limits': (-38.0, 69.0), 'units': u'm s^-1'},
    u'V': {'limits': (-67.0, 50.0), 'units': u'm s^-1'}}


class VS_ChemStyle_PL(AbstractVerticalSectionStyle):
    """Vertical section of chemical species
    """
    styles = [
        ("default", "fixed colour scale"),
        ("log", "logarithmic colour scale"),
        ("auto", "auto colour scale"),
        ("autolog", "auto log colour scale"), ]

    def _plot_style(self):
        """Make a cloud cover vertical section with temperature/potential
           temperature overlay.
        """
        ax = self.ax
        curtain_pt = self.data["air_potential_temperature"]
        curtain_pv = self.data["ertel_potential_vorticity"]
        curtain_cc = self.data[self.dataname]
        curtain_p = np.empty_like(curtain_cc)

        for i in range(len(self.driver.vert_data.reshape(-1))):
            curtain_p[i, :] = self.driver.vert_data[i] * 100
        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)

        delta_pt = 10 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 20

        # Filled contour plot of cloud cover.
        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cmap = plt.cm.gist_ncar_r
        cmin, cmax = CLAMS_CONFIG[self.name.replace("VS_", "")]["limits"]
        ##cmin, cmax = CLAMS_CONFIG[self.species]["limits"]
        if cmin > 0 and cmin < 0.05 * cmax and self.style != "log":
            cmin = 0.

        norm = None
        if self.style == "default":
            clev = np.linspace(cmin, cmax, 24)
        elif self.style == "log":
            # cmin = max(cmin, cmax * 0.001)
            # clev = np.exp(np.linspace(np.log(cmin), np.log(cmax), 12))
            # norm = matplotlib.colors.LogNorm(cmin, cmax)
            if cmin > 0:
                clev = np.exp(np.linspace(np.log(cmin), np.log(cmax), 24))
            elif cmax < 0:
                clev = np.exp(np.linspace(np.log(-cmax), np.log(-cmin), 24))
            else:
                delta = cmax - cmin
                clevlo = -np.exp(
                    np.linspace(np.log(-cmin), np.log(max(-cmin, cmax) * 0.001), 1 + int(24 * -cmin / delta)))
                clevhi = np.exp(np.linspace(np.log(max(-cmin, cmax) * 0.001), np.log(cmax), 1 + int(24 * cmax / delta)))
                clev = np.asarray(list(clevlo[:-1]) + list(clevhi[1:]))

            norm = matplotlib.colors.BoundaryNorm(clev, 255)
        elif self.style == "autolog":
            visible = (curtain_p <= self.p_bot) & (curtain_p >= self.p_top)
            cmin = curtain_cc[visible].min()
            cmax = curtain_cc[visible].max()
            if cmin > 0:
                clev = np.exp(np.linspace(np.log(cmin), np.log(cmax), 24))
            elif cmax < 0:
                clev = np.exp(np.linspace(np.log(-cmax), np.log(-cmin), 24))
            else:
                delta = cmax - cmin
                clevlo = -np.exp(
                    np.linspace(np.log(-cmin), np.log(max(-cmin, cmax) * 0.001), 1 + int(24 * -cmin / delta)))
                clevhi = np.exp(np.linspace(np.log(max(-cmin, cmax) * 0.001), np.log(cmax), 1 + int(24 * cmax / delta)))
                clev = np.asarray(list(clevlo[:-1]) + list(clevhi[1:]))

            norm = matplotlib.colors.BoundaryNorm(clev, 255)
        else:
            clev = np.linspace(curtain_cc.min(), curtain_cc.max(), 24)
            visible = (curtain_p <= self.p_bot) & (curtain_p >= self.p_top)
            cmin = curtain_cc[visible].min()
            cmax = curtain_cc[visible].max()
            clev = np.linspace(cmin, cmax, 24)

        cs = ax.contourf(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                         curtain_p, curtain_cc, clev, norm=norm,
                         cmap=cmap)
        # Contour line plot of PV.
        cs_pv = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_pv, [2, 4, 8, 16],
                           colors='lightgrey', linestyles='dashed', linewidths=2)
        ax.clabel(cs_pv, fontsize=8, fmt='%i')
        # Contour line plot of potential temperature.
        cs_pt = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_pt, np.arange(200, 700, delta_pt), colors='lightgrey',
                           linestyles='solid', linewidths=2)
        ax.clabel(cs_pt, fontsize=8, fmt='%i')

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(titlestring=self.title)

        # Format for colorbar labels
        clev_format = "%.3g"
        mclev = np.abs(clev).max()
        if self.style != "log":
            if mclev >= 100. and mclev < 10000.: clev_format = "%4i"
            if mclev >= 10. and mclev < 100.: clev_format = "%.1f"
            if mclev >= 1. and mclev < 10.: clev_format = "%.2f"
            if mclev >= .1 and mclev < 1.: clev_format = "%.3f"
            if mclev >= .01 and mclev < 0.1: clev_format = "%.4f"

            # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            cbar = self.fig.colorbar(cs, fraction=0.05, pad=0.01,
                                     format=clev_format, norm=norm)
            cbar.set_label(self.cbar_label)
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="1%",  # width = % of parent_bbox width
                                                                      height="40%",  # height : %
                                                                      loc=1)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical",
                                     format=clev_format, norm=norm)

            # adjust colorbar fontsize to figure height
            figheight = self.fig.bbox.height
            fontsize = figheight * 0.035
            axins1.yaxis.set_ticks_position("left")
            for x in axins1.yaxis.majorTicks:
                x.label1.set_backgroundcolor("w")
                x.label1.set_backgroundcolor("w")
                x.label1.set_fontsize(fontsize)


def make_clams_chem_class(entity):
    class fnord(VS_ChemStyle_PL):
        ln = {'ICH': 'India/China',
              'SEA': 'SE Asia',
              'NIN': 'North India',
              'SIN': 'South India',
              'ECH': 'East China'}
        species = entity
        name = 'VS_' + entity
        dataname = entity + "_volume_mixing_ratio"
        long_name = entity + " Mixing Ratio"
        if CLAMS_CONFIG[entity]["units"] == '%':
            long_name = ln[entity] + " Origin Tracer"
        title = long_name + " (" + CLAMS_CONFIG[entity]["units"] + ")"
        required_datafields = [
            ("pl", entity + "_volume_mixing_ratio"),
            ("pl", "air_potential_temperature"),
            ("pl", "ertel_potential_vorticity"), ]

    return fnord


for ent in CLAMS_CONFIG:
    globals()["VS_ChemStyle_PL_" + ent] = make_clams_chem_class(ent)

"""
GW
"""


class VS_GravityWaveForecast_ML(AbstractVerticalSectionStyle):
    """Vertical section of chemical species
    """
    name = "GW"
    title = "Gravity Wave Temperature Residual (K)"

    required_datafields = [
        ("ml", "gravity_wave_temperature_perturbation"),
        ("ml", "air_pressure"),
        ("sfc", "tropopause_altitude"),
    ]

    def _plot_style(self):
        """Make a cloud cover vertical section with temperature/potential
           temperature overlay.
        """
        ax = self.ax
        curtain_cc = self.data["gravity_wave_temperature_perturbation"]
        # curtain_p = np.empty_like(curtain_cc)
        # for i in range(len(self.driver.vert_data)):
        #    curtain_p[i, :] = 102300 * np.exp(-self.driver.vert_data[i] / 7.9)
        # curtain_p = curtain_p[::-1, :]
        tropo_p2 = 102300 * np.exp(-self.data["tropopause_altitude"].reshape(-1) / 7.9)
        curtain_p = self.data["air_pressure"] * 100
        tropo_p = np.empty_like(self.data["tropopause_altitude"].reshape(-1))
        for i in range(curtain_p.shape[1]):
            z = self.data["tropopause_altitude"].reshape(-1)[i]
            tropo_p[i] = np.interp(z, self.driver.vert_data[:], curtain_p[::-1, i])
        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)

        # Filled contour plot of cloud cover.
        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        cmap = plt.cm.Spectral_r
        norm = matplotlib.colors.BoundaryNorm([-3, -2.5, -2, -1.5, -1, -0.5, 0.5, 1, 1.5, 2, 2.5, 3], cmap.N)
        cs = ax.pcolormesh(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_cc, norm=norm,
                           cmap=cmap)
        ax.plot(self.lat_inds, tropo_p.reshape(-1), color="gray", zorder=100)

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(titlestring=self.title)

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            cbar = self.fig.colorbar(cs, fraction=0.05, pad=0.01)
            cbar.set_label(self.cbar_label)
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="1%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=1)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")
            for x in axins1.yaxis.majorTicks:
                x.label1.set_backgroundcolor("w")


"""
CLOUDS
"""


class VS_CloudsStyle_01(AbstractVerticalSectionStyle):
    """Vertical section of cloud cover.
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
        if not 'air_potential_temperature' in self.data.keys():
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
    """Vertical section of cloud cover and horizontal wind speed.
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
        if not 'air_potential_temperature' in self.data.keys():
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
        curtain_t = self.data["air_temperature"]
        curtain_pt = self.data["air_potential_temperature"]
        curtain_cc = self.data["cloud_area_fraction_in_atmosphere_layer"]
        curtain_v = self.data["horizontal_wind"]

        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)

        # Contour spacing for temperature lines.
        delta_t = 2 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 4
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


"""
RELATIVE HUMIDITY
"""


class VS_RelativeHumdityStyle_01(AbstractVerticalSectionStyle):
    """Vertical sections of relative humidity.
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
        if not 'air_potential_temperature' in self.data.keys():
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
        cs_rh2 = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
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
    """Vertical sections of specific humidity.
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
        if not 'air_potential_temperature' in self.data.keys():
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
        curtain_v = self.data["northward_wind"]

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


"""
VERTICAL VELOCITY
"""


class VS_VerticalVelocityStyle_01(AbstractVerticalSectionStyle):
    """Vertical sections of vertical velocity.
    """

    name = "VS_W01"
    title = "Vertical Velocity (cm/s) Vertical Section"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_pressure"),
        ("ml", "air_temperature"),
        ("ml", "omega")]

    def _prepare_datafields(self):
        """Computes potential temperature from pressure and temperature if
        it has not been passed as a data field. Also computes vertical
        velocity in cm/s.
        """
        if not 'air_potential_temperature' in self.data.keys():
            self.data['air_potential_temperature'] = \
                thermolib.pot_temp(self.data['air_pressure'],
                                   self.data['air_temperature'])
        self.data["upward_wind"] = \
            thermolib.omega_to_w(self.data["omega"],
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
        cs_w1 = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
                           curtain_p, curtain_w, [2],
                           colors="red", linestyles="solid", linewidths=0.5)
        cs_w2 = ax.contour(self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose(),
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


"""
HORIZONTAL VELOCITY
"""


class VS_HorizontalVelocityStyle_01(AbstractVerticalSectionStyle):
    """Vertical sections of horizontal velocity.
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
        if not 'air_potential_temperature' in self.data.keys():
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


"""
POTENTIAL VORTICITY
"""

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
    return (pvu + 2.) / 10.


S = 0.0000000001

_pv_eth_data = (
    (scale_pvu_to_01(-2.), (142. / 255., 178. / 255., 255. / 255.)),
    (scale_pvu_to_01(0. - S), (142. / 255., 178. / 255., 255. / 255.)),

    (scale_pvu_to_01(0.), (181. / 255., 201. / 255., 255. / 255.)),
    (scale_pvu_to_01(0.2 - S), (181. / 255., 201. / 255., 255. / 255.)),

    (scale_pvu_to_01(0.2), (214. / 255., 226. / 255., 237. / 255.)),
    (scale_pvu_to_01(0.5 - S), (214. / 255., 226. / 255., 237. / 255.)),

    (scale_pvu_to_01(0.5), (242. / 255., 221. / 255., 160. / 255.)),
    (scale_pvu_to_01(0.8 - S), (242. / 255., 221. / 255., 160. / 255.)),

    (scale_pvu_to_01(0.8), (239. / 255., 193. / 255., 130. / 255.)),
    (scale_pvu_to_01(1.0 - S), (239. / 255., 193. / 255., 130. / 255.)),

    (scale_pvu_to_01(1.0), (242. / 255., 132. / 255., 68. / 255.)),
    (scale_pvu_to_01(1.5 - S), (242. / 255., 132. / 255., 68. / 255.)),

    (scale_pvu_to_01(1.5), (220. / 255., 60. / 255., 30. / 255.)),
    (scale_pvu_to_01(2.0 - S), (220. / 255., 60. / 255., 30. / 255.)),

    (scale_pvu_to_01(2.0), (255. / 255., 120. / 255., 20. / 255.)),
    (scale_pvu_to_01(3.0 - S), (255. / 255., 120. / 255., 20. / 255.)),

    (scale_pvu_to_01(3.0), (255. / 255., 190. / 255., 20. / 255.)),
    (scale_pvu_to_01(4.0 - S), (255. / 255., 190. / 255., 20. / 255.)),

    (scale_pvu_to_01(4.0), (255. / 255., 249. / 255., 20. / 255.)),
    (scale_pvu_to_01(6.0 - S), (255. / 255., 249. / 255., 20. / 255.)),

    (scale_pvu_to_01(6.0), (170. / 255., 255. / 255., 60. / 255.)),
    (scale_pvu_to_01(8.0), (170. / 255., 255. / 255., 60. / 255.))
)

pv_eth_cmap_1 = matplotlib.colors.LinearSegmentedColormap.from_list("pv_eth_cmap_1", _pv_eth_data)


class VS_PotentialVorticityStyle_01(AbstractVerticalSectionStyle):
    """Vertical sections of potential vorticity.
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
        if not 'air_potential_temperature' in self.data.keys():
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
        curtain_pv = self.data["ertel_potential_vorticity"]
        curtain_clwc = self.data["specific_cloud_liquid_water_content"] * 1000.
        curtain_ciwc = self.data["specific_cloud_ice_water_content"] * 1000.

        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)

        # Contour spacing for temperature lines.
        delta_t = 2 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 4
        delta_pt = 5 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 10

        # Change PV sign on southern hemisphere.
        if self.style.lower() == "default": self.style = "NH"
        if self.style.upper() == "SH": curtain_pv = -curtain_pv

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


"""
PROBABILITY OF WCB
"""


class VS_ProbabilityOfWCBStyle_01(AbstractVerticalSectionStyle):
    """Vertical sections of probability of WCB trajectory occurence,
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
        if not 'air_potential_temperature' in self.data.keys():
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
        curtain_pwcb = self.data["probability_of_wcb_occurrence"] * 100.
        curtain_clwc = self.data["specific_cloud_liquid_water_content"] * 1000.
        curtain_ciwc = self.data["specific_cloud_ice_water_content"] * 1000.

        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)

        # Contour spacing for temperature lines.
        delta_t = 2 if (np.log(self.p_bot) - np.log(self.p_top)) < 2.2 else 4
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
    """Number of Lagranto trajectories per grid box for WCB, MIX, INSITU
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
                                titlestring="Cirrus density, insitu red, mix blue, wcb colour (1E-6/km^2/hPa) Vertical Section")

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


"""
EMAC Eyjafjallajokull
"""


class VS_EMACEyja_Style_01(AbstractVerticalSectionStyle):
    """EMAC Eyja tracer vertical cross sections.
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
        if not 'air_potential_temperature' in self.data.keys():
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
