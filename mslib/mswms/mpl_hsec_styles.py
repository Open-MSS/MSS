# -*- coding: utf-8 -*-
"""

    mslib.mswms.mpl_hsec_styles
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Matplotlib horizontal section styles.

    In this module, the visualisation styles of the horizontal map products
    that can be provided through the WMS are defined. The styles are classes
    that are derived from MPLBasemapHorizontalSectionStyle (defined in
    mpl_hsec.py). If you want to define a new product, copy an existing
    implementation and modify it according to your needs.

    A few notes:

    1) The idea: Each product defines the data fields it requires as NetCDF-CF
    compliant standard names in the variable 'required_datafields' (a list
    of tuples (leveltype, variablename), where leveltype can be ml (model levels),
    pl (pressure levels), or whatever you data source may provide. The data
    driver invoked by the WSGI module is responsible for loading the data.
    The superclass MPLBasemapHorizontalSectionStyle sets up the plot and
    draws the map. What is left to do for the product class is to implement
    specific post-processing actions on the data, and to do the visualisation
    on the map.

    2) If your product requires some sort of post-processing (e.g. the derivation
    of potential temperature or any other parameter, place it in the
    _prepare_datafields() method.

    3) All visualisation commands go to the _plot_style() method. In this
    method, you can assume that the data fields you have requested are available
    as 2D arrays in the 'self.data' field.

    4) All defined products MUST define a name (the WMS layer name) and a title.

    5) If you want to provide different styles according to the WMS standard,
    define the names of the styles in the 'styles' variable and check in
    _plot_style() for the 'self.style' variable to know which style to deliver.

    6) Your products should consider the 'self.noframe' variable to place a
    legend and a title. If this variable is True (default WMS behaviour), plotting
    anything outside the map axis will lead to erroneous plots. Look at the
    provided styles to get a feeling of how title and legends can be best placed.

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

import logging

import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.axes_grid1.inset_locator
import matplotlib.colors
import mpl_toolkits.basemap
from matplotlib import patheffects

from mslib.mswms.mpl_hsec import MPLBasemapHorizontalSectionStyle
from mslib.mswms.utils import Targets, get_style_parameters, get_cbar_label_format, convert_to
from mslib.mswms.msschem import MSSChemTargets
from mslib import thermolib


class HS_CloudsStyle_01(MPLBasemapHorizontalSectionStyle):
    """
    Surface Field: CLOUDS
    """
    name = "TCC"
    title = "Cloud Cover (0-1)"
    styles = [
        ("default", "Total Cloud Cover"),
        ("TOT", "Total Cloud Cover"),
        ("LOW", "Low Cloud Cover"),
        ("MED", "Medium Cloud Cover"),
        ("HIGH", "High Cloud Cover")]

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ('sfc', 'low_cloud_area_fraction'),
        ('sfc', 'medium_cloud_area_fraction'),
        ('sfc', 'high_cloud_area_fraction'),
        ('sfc', 'air_pressure_at_sea_level')]

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        if self.style.lower() == "default":
            self.style = "TOT"
        if self.style in ["LOW", "TOT"]:
            lcc = bm.contourf(lonmesh, latmesh, data['low_cloud_area_fraction'],
                              np.arange(0.2, 1.1, 0.1), cmap=plt.cm.autumn_r)
            if not self.noframe:
                cbar = self.fig.colorbar(lcc, fraction=0.05, pad=-0.02, shrink=0.7)
                cbar.set_label("Cloud cover fraction in grid box (0-1)")
            else:
                axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                    ax, width="3%", height="30%", loc=4)
                cbar = self.fig.colorbar(lcc, cax=axins1, orientation="vertical")
                axins1.yaxis.set_ticks_position("left")

        if self.style in ["MED", "TOT"]:
            mcc = bm.contourf(lonmesh, latmesh, data['medium_cloud_area_fraction'],
                              np.arange(0.2, 1.1, 0.1), cmap=plt.cm.summer_r)
            if not self.noframe:
                self.fig.colorbar(mcc, fraction=0.05, pad=-0.02, shrink=0.7, format='')
            else:
                axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                    ax, width="2%" if self.style == "TOT" else "3%", height="30%", loc=4)
                cbar = self.fig.colorbar(mcc, cax=axins1, orientation="vertical",
                                         format='' if self.style == "TOT" else "%.1f")
                axins1.yaxis.set_ticks_position("left")

        if self.style in ["HIGH", "TOT"]:
            hcc = bm.contourf(lonmesh, latmesh, data['high_cloud_area_fraction'],
                              np.arange(0.2, 1.1, 0.1), cmap=plt.cm.Blues)
            bm.contour(lonmesh, latmesh, data['high_cloud_area_fraction'],
                       [0.2], colors="blue", linestyles="dotted")
            if not self.noframe:
                self.fig.colorbar(hcc, fraction=0.05, pad=0.08, shrink=0.7, format='')
            else:
                axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                    ax, width="1%" if self.style == "TOT" else "3%", height="30%", loc=4)
                cbar = self.fig.colorbar(hcc, cax=axins1, orientation="vertical",
                                         format='' if self.style == "TOT" else "%.1f")
                axins1.yaxis.set_ticks_position("left")

        # Colors in python2.6/site-packages/matplotlib/colors.py
        cs = bm.contour(lonmesh, latmesh, 0.01 * data['air_pressure_at_sea_level'],
                        np.arange(950, 1050, 4), colors="burlywood", linewidths=2)
        ax.clabel(cs, fontsize=8, fmt='%i')

        titlestring = "Total cloud cover (high, medium, low) (0-1)"
        if self.style == "LOW":
            titlestring = "Low cloud cover (0-1)"
        elif self.style == "MED":
            titlestring = "Medium cloud cover (0-1)"
        elif self.style == "HIGH":
            titlestring = "High cloud cover (0-1)"
        time_step = self.valid_time - self.init_time
        time_step_hrs = ((time_step.days * 86400 + time_step.seconds) // 3600)
        titlestring += '\nValid: {} (step {:d} hrs from {})' \
            .format(self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                    time_step_hrs,
                    self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_MSLPStyle_01(MPLBasemapHorizontalSectionStyle):
    """
    Surface Field: Mean Sea Level Pressure

    """
    name = "MSLP"
    title = "Mean Sea Level Pressure (hPa)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("sfc", "air_pressure_at_sea_level"),
        ("sfc", "surface_eastward_wind"),
        ("sfc", "surface_northward_wind")]

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        thick_contours = np.arange(952, 1050, 8)
        thin_contours = [c for c in np.arange(952, 1050, 2)
                         if c not in thick_contours]

        mslp = 0.01 * data['air_pressure_at_sea_level']

        # Colors in python2.6/site-packages/matplotlib/colors.py
        cs = bm.contour(lonmesh, latmesh, mslp,
                        thick_contours, colors="darkblue", linewidths=2)
        ax.clabel(cs, fontsize=12, fmt='%i')
        cs = bm.contour(lonmesh, latmesh, mslp,
                        thin_contours, colors="darkblue", linewidths=1)

        # Convert wind data from m/s to knots.
        u = data['surface_eastward_wind'] * 1.944
        v = data['surface_northward_wind'] * 1.944

        # Transform wind vector field to fit map.
        lons2 = ((self.lons + 180) % 360) - 180
        lons2_ind = lons2.argsort()
        udat, vdat, xv, yv = bm.transform_vector(u[:, lons2_ind], v[:, lons2_ind],
                                                 lons2[lons2_ind], self.lats,
                                                 16, 16, returnxy=True)
        # udat, vdat, xv, yv = bm.transform_vector(u, v, self.lons, self.lats,
        #                                         16, 16, returnxy=True)

        # Plot wind barbs.
        bm.barbs(xv, yv, udat, vdat,
                 barbcolor='firebrick', flagcolor='firebrick', pivot='middle',
                 linewidths=1)

        # Find local minima and maxima.
        #         min_indices, min_values = local_minima(mslp.ravel(), window=50)
        #         #min_indices, min_values = local_minima(mslp, window=(50,50))
        #         minfits = minimum_filter(mslp, size=(50,50), mode="wrap")
        #         logging.debug("%s", minfits)
        #         #logging.debug("%s // %s // %s", min_values, lonmesh_.ravel()[min_indices],
        #         #              latmesh_.ravel()[min_indices])

        #         bm.scatter(lonmesh.ravel()[min_indices], latmesh.ravel()[min_indices],
        #                    s=20, c='blue', marker='s')

        titlestring = "Mean sea level pressure (hPa) and surface wind"
        time_step = self.valid_time - self.init_time
        time_step_hrs = ((time_step.days * 86400 + time_step.seconds) // 3600)
        titlestring += '\nValid: {} (step {:d} hrs from {})' \
            .format(self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                    time_step_hrs,
                    self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_SEAStyle_01(MPLBasemapHorizontalSectionStyle):
    """
    Surface Field: Solar Elevation Angle
    """
    name = "SEA"
    title = "Solar Elevation Angle (degrees)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("sfc", "solar_elevation_angle")]

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        thick_contours = np.arange(-10, 95, 5)
        thin_contours = [c for c in np.arange(0, 90, 1)
                         if c not in thick_contours]
        neg_thin_contours = [c for c in np.arange(-10, 0, 1)
                             if c not in thick_contours]

        sea = data['solar_elevation_angle']

        # Filled contour plot.
        scs = bm.contourf(lonmesh, latmesh, sea,
                          np.arange(0, 91, 1), cmap=plt.cm.spectral)
        if not self.noframe:
            cbar = self.fig.colorbar(scs, fraction=0.05, pad=0.08, shrink=0.7)
            cbar.set_label("Solar Elevation Angle (degrees)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="30%", loc=4)
            cbar = self.fig.colorbar(scs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        # Contour lines plot.
        # Colors in python2.6/site-packages/matplotlib/colors.py
        bm.contour(lonmesh, latmesh, sea,
                   thick_contours, colors="saddlebrown",
                   linewidths=3, linestyles="solid")
        cs2 = bm.contour(lonmesh, latmesh, sea,
                         thin_contours, colors="white", linewidths=1)
        cs2.clabel(thin_contours, fontsize=14, fmt='%i')
        cs3 = bm.contour(lonmesh, latmesh, sea,
                         neg_thin_contours, colors="saddlebrown",
                         linewidths=1, linestyles="solid")
        cs3.clabel(neg_thin_contours, fontsize=14, fmt='%i')

        # Plot title.
        titlestring = "Solar Elevation Angle "
        titlestring += u"\nValid: {}" \
            .format(self.valid_time.strftime("%a %Y-%m-%d %H:%M UTC"))
        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_SeaIceStyle_01(MPLBasemapHorizontalSectionStyle):
    """
    Surface Field: Sea Ice Cover
    """
    name = "CI"
    title = "Sea Ice Cover Fraction (0-1)"

    styles = [
        ("default", "pseudocolor plot"),
        ("PCOL", "pseudocolor plot"),
        ("CONT", "contour plot")]

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("sfc", "sea_ice_area_fraction")]

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        if self.style == "PCOL":
            # Shift lat/lon grid for PCOLOR (see comments in HS_EMAC_TracerStyle_SFC_01).
            lonmesh_ = lonmesh_ - ((self.lons[1] - self.lons[0]) / 2.)
            latmesh_ = latmesh_ - ((self.lats[1] - self.lats[0]) / 2.)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        ice = data['sea_ice_area_fraction']

        if self.style.lower() == "default":
            self.style = "PCOL"

        # Filled contour plot.
        if self.style == "PCOL":
            scs = bm.pcolor(lonmesh, latmesh, ice,
                            cmap=plt.cm.Blues,
                            norm=matplotlib.colors.Normalize(vmin=0.1, vmax=1.0),
                            edgecolors='none')
        else:
            scs = bm.contourf(lonmesh, latmesh, ice,
                              np.arange(0.1, 1.1, .1), cmap=plt.cm.Blues)
        if not self.noframe:
            cbar = self.fig.colorbar(scs, fraction=0.05, pad=0.08, shrink=0.7)
            cbar.set_label("Sea Ice Cover Fraction (0-1)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="30%", loc=4)
            cbar = self.fig.colorbar(scs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        # Plot title.
        titlestring = "Sea Ice Cover"
        time_step = self.valid_time - self.init_time
        time_step_hrs = ((time_step.days * 86400 + time_step.seconds) // 3600)
        titlestring += '\nValid: {} (step {:d} hrs from {})' \
            .format(self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                    time_step_hrs,
                    self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))
        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_TemperatureStyle_ML_01(MPLBasemapHorizontalSectionStyle):
    """
    Upper Air Field: Temperature
    """
    name = "MLTemp01"
    title = "Temperature (Model Level) (degC)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "air_temperature")]

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        cmin = -72
        cmax = 42
        thick_contours = np.arange(cmin, cmax, 6)
        thin_contours = [c for c in np.arange(cmin, cmax, 2)
                         if c not in thick_contours]

        tempC = data['air_temperature'] - 273.15

        tc = bm.contourf(lonmesh, latmesh, tempC,
                         np.arange(cmin, cmax, 2), cmap=plt.cm.spectral)
        if not self.noframe:
            cbar = self.fig.colorbar(tc, fraction=0.05, pad=0.08, shrink=0.7)
            cbar.set_label("Temperature (degC)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="30%", loc=4)
            cbar = self.fig.colorbar(tc, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        # Colors in python2.6/site-packages/matplotlib/colors.py
        cs = bm.contour(lonmesh, latmesh, tempC,
                        [0], colors="red", linewidths=4)
        cs = bm.contour(lonmesh, latmesh, tempC,
                        thick_contours, colors="saddlebrown", linewidths=2)
        ax.clabel(cs, fontsize=14, fmt='%i')
        cs = bm.contour(lonmesh, latmesh, tempC,
                        thin_contours, colors="saddlebrown", linewidths=1)

        titlestring = "Temperature (degC) at model level {}".format(self.level)
        time_step = self.valid_time - self.init_time
        time_step_hrs = ((time_step.days * 86400 + time_step.seconds) // 3600)
        titlestring += '\nValid: {} (step {:d} hrs from {})' \
            .format(self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                    time_step_hrs,
                    self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_GenericStyle(MPLBasemapHorizontalSectionStyle):
    """
    Pressure level version for Chemical Mixing ratios.
    """
    styles = [
        ("auto", "auto colour scale"),
        ("autolog", "auto logcolour scale"), ]

    def _plot_style(self):
        bm = self.bm
        ax = self.bm.ax

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        show_data = np.ma.masked_invalid(self.data[self.dataname]) * self.unit_scale
        # get cmin, cmax, cbar_log and cbar_format for level_key
        cmin, cmax = Targets.get_range(self.dataname, self.level, self.name[-2:])
        cmin, cmax, clevs, cmap, norm, ticks = get_style_parameters(
            self.dataname, self.style, cmin, cmax, show_data)

        tc = bm.contourf(lonmesh, latmesh, show_data, levels=clevs, cmap=cmap, extend="both", norm=norm)

        for cont_data, cont_levels, cont_colour, cont_label_colour, cont_style, cont_lw, pe in self.contours:
            cs_pv = ax.contour(lonmesh, latmesh, self.data[cont_data], cont_levels,
                               colors=cont_colour, linestyles=cont_style, linewidths=cont_lw)
            cs_pv_lab = ax.clabel(cs_pv, colors=cont_label_colour, fmt='%i')
            if pe:
                plt.setp(cs_pv.collections, path_effects=[patheffects.withStroke(linewidth=cont_lw + 2,
                                                                                 foreground="w")])
                plt.setp(cs_pv_lab, path_effects=[patheffects.withStroke(linewidth=1, foreground="w")])

        # define position of the colorbar and the orientation of the ticks
        if self.epsg == 77774020:
            cbar_location = 3
            tick_pos = 'right'
        else:
            cbar_location = 4
            tick_pos = 'left'

        # Format for colorbar labels
        cbar_label = self.title
        cbar_format = get_cbar_label_format(self.style, np.median(np.abs(clevs)))

        if not self.noframe:
            cbar = self.fig.colorbar(tc, fraction=0.05, pad=0.08, shrink=0.7,
                                     norm=norm, label=cbar_label, format=cbar_format, ticks=ticks)
            cbar.set_ticklabels(clevs)
            cbar.set_ticks(clevs)
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="40%", loc=cbar_location)
            self.fig.colorbar(tc, cax=axins1, orientation="vertical", format=cbar_format, ticks=ticks)

            # adjust colorbar fontsize to figure height
            fontsize = self.fig.bbox.height * 0.024
            axins1.yaxis.set_ticks_position(tick_pos)
            for x in axins1.yaxis.majorTicks:
                x.label1.set_path_effects([patheffects.withStroke(linewidth=4, foreground='w')])
                x.label1.set_fontsize(fontsize)


def make_generic_class(name, entity, vert, add_data=None, add_contours=None,
                       fix_styles=None, add_styles=None, add_prepare=None):
    if add_data is None:
        add_data = [(vert, "ertel_potential_vorticity")]
    if add_contours is None:
        add_contours = [("ertel_potential_vorticity", [2, 4, 8, 16], "dimgrey", "dimgrey", "solid", 2, True)]

    class fnord(HS_GenericStyle):
        name = u"{}_{}".format(entity, vert)
        dataname = entity
        title = Targets.TITLES.get(entity, entity)
        long_name = entity
        units, unit_scale = Targets.get_unit(entity)
        if units:
            title += u" ({})".format(units)

        required_datafields = [(vert, entity)] + add_data
        contours = add_contours

    fnord.__name__ = name
    fnord.styles = list(fnord.styles)
    if Targets.get_thresholds(entity) is not None:
        fnord.styles += [("nonlinear", "nonlinear colour scale")]
    if all(_x is not None for _x in Targets.get_range(entity, None, vert)):
        fnord.styles += [
            ("default", "fixed colour scale"),
            ("log", "fixed logarithmic colour scale")]

    if add_styles is not None:
        fnord.styles += add_styles
    if fix_styles is not None:
        fnord.styles = fix_styles
    if add_prepare is not None:
        fnord._prepare_datafields = add_prepare
    globals()[name] = fnord


for vert in ["al", "ml", "pl", "tl"]:
    for ent in Targets.get_targets():
        make_generic_class("HS_GenericStyle_{}_{}".format(vert.upper(), ent), ent, vert)
    make_generic_class(
        "HS_GenericStyle_{}_{}".format(vert.upper(), "equivalent_latitude"),
        "equivalent_latitude", vert, [], [],
        fix_styles=[("equivalent_latitude_nh", "northern hemisphere"),
                    ("equivalent_latitude_sh", "southern hemisphere")])
    make_generic_class(
        "HS_GenericStyle_{}_{}".format(vert.upper(), "ertel_potential_vorticity"),
        "ertel_potential_vorticity", vert, [], [],
        fix_styles=[("ertel_potential_vorticity_nh", "northern hemisphere"),
                    ("ertel_potential_vorticity_sh", "southern hemisphere")])
    make_generic_class(
        "HS_GenericStyle_{}_{}".format(vert.upper(), "square_of_brunt_vaisala_frequency_in_air"),
        "square_of_brunt_vaisala_frequency_in_air", vert, [], [],
        fix_styles=[("square_of_brunt_vaisala_frequency_in_air", "")])
    make_generic_class(
        "HS_GenericStyle_{}_{}".format(vert.upper(), "gravity_wave_temperature_perturbation"),
        "air_temperature_residual", vert,
        [("sfc", "tropopause_altitude")],
        [("tropopause_altitude", [8, 10, 12, 14, 16, 18], "dimgrey", "dimgrey", "solid", 2, True)],
        fix_styles=[("gravity_wave_temperature_perturbation", "")])
    make_generic_class(
        "HS_GenericStyle_{}_{}".format(vert.upper(), "cloud_ice_mixing_ratio"),
        "cloud_ice_mixing_ratio", vert,
        [("pl", "maximum_relative_humidity_wrt_ice_on_backtrajectory")],
        [("maximum_relative_humidity_wrt_ice_on_backtrajectory",
          [90, 100, 120, 160], ["dimgrey", "dimgrey", "#443322", "#045FB4"],
          ["dimgrey", "dimgrey", "#443322", "#045FB4"],
          ["dashed", "solid", "solid", "solid"], 2, True)],
        fix_styles=[("log_ice_cloud", "iwc")])
    make_generic_class(
        "HS_GenericStyle_{}_{}".format(vert.upper(), "number_concentration_of_ice_crystals_in_air"),
        "number_concentration_of_ice_crystals_in_air", vert,
        [("pl", "maximum_relative_humidity_wrt_ice_on_backtrajectory")],
        [("maximum_relative_humidity_wrt_ice_on_backtrajectory",
          [90, 100, 120, 160], ["dimgrey", "dimgrey", "#443322", "#045FB4"],
          ["dimgrey", "dimgrey", "#443322", "#045FB4"],
          ["dashed", "solid", "solid", "solid"], 2, True)],
        fix_styles=[("log_ice_cloud", "nice")])
    make_generic_class(
        "HS_GenericStyle_{}_{}".format(vert.upper(), "mean_mass_radius_of_cloud_ice_crystals"),
        "mean_mass_radius_of_cloud_ice_crystals", vert,
        [("pl", "maximum_relative_humidity_wrt_ice_on_backtrajectory")],
        [("maximum_relative_humidity_wrt_ice_on_backtrajectory",
          [90, 100, 120, 160], ["dimgrey", "dimgrey", "#443322", "#045FB4"],
          ["dimgrey", "dimgrey", "#443322", "#045FB4"],
          ["dashed", "solid", "solid", "solid"], 2, True)],
        fix_styles=[("ice_cloud", "radius")])
    make_generic_class(
        "HS_GenericStyle_{}_{}".format(vert.upper(), "maximum_pressure_on_backtrajectory"),
        "maximum_pressure_on_backtrajectory", vert, [], [])

make_generic_class(
    "HS_GenericStyle_SFC_tropopause_altitude",
    "tropopause_altitude", "sfc", [],
    [("tropopause_altitude", np.arange(5, 20.1, 0.500), "yellow", "red", "solid", 0.5, False)],
    fix_styles=[("tropopause_altitude", "tropopause_altitude")])
make_generic_class(
    "HS_GenericStyle_SFC_max_of_square_of_brunt_vaisala_frequency_above_tropopause_in_air",
    "max_of_square_of_brunt_vaisala_frequency_above_tropopause_in_air", "sfc", [("sfc", "tropopause_altitude")],
    [("tropopause_altitude", np.arange(6, 20.1, 2), "dimgrey", "dimgrey", "solid", 2, True)],
    fix_styles=[("square_of_brunt_vaisala_frequency_in_air", "")])
make_generic_class(
    "HS_GenericStyle_SFC_mean_of_square_of_brunt_vaisala_frequency_above_tropopause_in_air",
    "mean_of_square_of_brunt_vaisala_frequency_above_tropopause_in_air", "sfc", [("sfc", "tropopause_altitude")],
    [("tropopause_altitude", np.arange(6, 20.1, 2), "dimgrey", "dimgrey", "solid", 2, True)],
    fix_styles=[("square_of_brunt_vaisala_frequency_in_air", "")])


class HS_TemperatureStyle_PL_01(MPLBasemapHorizontalSectionStyle):
    """
    Pressure level version of the temperature style.
    """
    name = "PLTemp01"
    title = "Temperature (degC) and Geopotential Height (m)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("pl", "air_temperature"),
        ("pl", "geopotential_height")]

    def _prepare_datafields(self):
        self.data["geopotential_height"] = convert_to(
            self.data["geopotential_height"], self.data_units["geopotential_height"], "m", 1. / 9.81)

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        cmin = -72
        cmax = 42
        thick_contours = np.arange(cmin, cmax, 6)
        thin_contours = [c for c in np.arange(cmin, cmax, 2)
                         if c not in thick_contours]

        tempC = data['air_temperature'] - 273.15

        tc = bm.contourf(lonmesh, latmesh, tempC,
                         np.arange(cmin, cmax, 2), cmap=plt.cm.spectral)
        if not self.noframe:
            cbar = self.fig.colorbar(tc, fraction=0.05, pad=0.08, shrink=0.7)
            cbar.set_label("Temperature (degC)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="30%", loc=4)
            cbar = self.fig.colorbar(tc, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        # Colors in python2.6/site-packages/matplotlib/colors.py
        cs = bm.contour(lonmesh, latmesh, tempC,
                        [0], colors="red", linewidths=4)
        cs = bm.contour(lonmesh, latmesh, tempC,
                        thick_contours, colors="saddlebrown",
                        linewidths=2, linestyles="solid")
        ax.clabel(cs, colors="black", fontsize=14, fmt='%i')
        cs = bm.contour(lonmesh, latmesh, tempC,
                        thin_contours, colors="white",
                        linewidths=1, linestyles="solid")

        # Plot geopotential height contours.
        gpm = self.data["geopotential_height"]
        geop_contours = np.arange(400, 28000, 40)
        cs = bm.contour(lonmesh, latmesh, gpm,
                        geop_contours, colors="black", linewidths=1)
        ax.clabel(cs, geop_contours[::2], fontsize=10, fmt='%i')

        titlestring = "Temperature (degC) and Geopotential Height (m) at " \
            "{:.0f} hPa".format(self.level)
        time_step = self.valid_time - self.init_time
        time_step_hrs = ((time_step.days * 86400 + time_step.seconds) // 3600)
        titlestring += '\nValid: {} (step {:d} hrs from {})' \
            .format(self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                    time_step_hrs,
                    self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_GeopotentialWindStyle_PL(MPLBasemapHorizontalSectionStyle):
    """
    Upper Air Field: Geopotential and Wind

    """
    name = "PLGeopWind"
    title = "Geopotential Height (m) and Horizontal Wind (m/s)"
    styles = [
        ("default", "Wind Speed 10-85 m/s"),
        ("wind_10_65", "Wind Speed 10-65 m/s"),
        ("wind_20_55", "Wind Speed 20-55 m/s"),
        ("wind_15_55", "Wind Speed 15-55 m/s")]

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("pl", "geopotential_height"),
        ("pl", "eastward_wind"),
        ("pl", "northward_wind")]

    def _prepare_datafields(self):
        self.data["geopotential_height"] = convert_to(
            self.data["geopotential_height"], self.data_units["geopotential_height"], "m", 1. / 9.81)

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        # Compute wind speed.
        u = data["eastward_wind"]
        v = data["northward_wind"]
        wind = np.sqrt(u ** 2 + v ** 2)

        # Plot wind contours.
        # NOTE: Setting alpha=0.8 raises the transparency problem in the client
        # (the imshow issue, see ../issues/transparency; surfaces with alpha
        # values < 1 are mixed with grey). Hence, it is better to disable
        # alpha blending here until a fix has been found. (mr 2011-02-01)
        wind_contours = np.arange(10, 90, 5)  # default wind contours
        if self.style.lower() == "wind_10_65":
            wind_contours = np.arange(10, 70, 5)
        elif self.style.lower() == "wind_20_55":
            wind_contours = np.arange(20, 60, 5)
        elif self.style.lower() == "wind_15_55":
            wind_contours = np.arange(15, 60, 5)
        cs = bm.contourf(lonmesh, latmesh, wind,
                         # wind_contours, cmap=plt.cm.hot_r, alpha=0.8)
                         wind_contours, cmap=plt.cm.hot_r)
        if not self.noframe:
            cbar = self.fig.colorbar(cs, fraction=0.05, pad=0.08, shrink=0.7)
            cbar.set_label("Wind Speed (m/s)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="30%", loc=4)
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        # Convert wind data from m/s to knots for the wind barbs.
        u *= 1.944
        v *= 1.944

        # Transform wind vector field to fit map.
        lons2 = ((self.lons + 180) % 360) - 180
        lons2_ind = lons2.argsort()
        udat, vdat, xv, yv = bm.transform_vector(u[:, lons2_ind], v[:, lons2_ind],
                                                 lons2[lons2_ind], self.lats,
                                                 16, 16, returnxy=True)

        # Plot wind barbs.
        bm.barbs(xv, yv, udat, vdat,
                 barbcolor='firebrick', flagcolor='firebrick', pivot='middle',
                 linewidths=0.5, length=6)

        # Plot geopotential height contours.
        gpm = self.data["geopotential_height"]
        gpm_interval = 40 if self.level <= 500 else 20
        geop_contours = np.arange(400, 28000, gpm_interval)
        cs = bm.contour(lonmesh, latmesh, gpm,
                        geop_contours, colors="green", linewidths=2)
        ax.clabel(cs, geop_contours[::2], fontsize=14, fmt='%i')

        # Plot title.
        titlestring = "Geopotential Height (m) and Horizontal Wind (m/s) " \
            "at {:.0f} hPa".format(self.level)
        time_step = self.valid_time - self.init_time
        time_step_hrs = ((time_step.days * 86400 + time_step.seconds) // 3600)
        titlestring += '\nValid: {} (step {:d} hrs from {})' \
            .format(self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                    time_step_hrs,
                    self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_RelativeHumidityStyle_PL_01(MPLBasemapHorizontalSectionStyle):
    """
    Upper Air Field: Relative Humidity
    Relative humidity and geopotential on pressure levels.
    """
    name = "PLRelHum01"
    title = "Relative Humditiy (%) and Geopotential Height (m)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("pl", "air_temperature"),
        ("pl", "geopotential_height"),
        ("pl", "specific_humidity")]

    def _prepare_datafields(self):
        """Computes relative humidity from p, t, q.
        """
        self.data["geopotential_height"] = convert_to(
            self.data["geopotential_height"], self.data_units["geopotential_height"], "m", 1. / 9.81)
        self.data["relative_humidity"] = thermolib.rel_hum(
            self.level * 100., self.data["air_temperature"], self.data["specific_humidity"])

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        filled_contours = np.arange(70, 140, 15)
        thin_contours = np.arange(10, 140, 15)

        rh = data["relative_humidity"]

        rhc = bm.contourf(lonmesh, latmesh, rh,
                          filled_contours, cmap=plt.cm.winter_r)
        if not self.noframe:
            cbar = self.fig.colorbar(rhc, fraction=0.05, pad=0.08, shrink=0.7)
            cbar.set_label("Relative Humidity (%)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="30%", loc=4)
            cbar = self.fig.colorbar(rhc, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        # Colors in python2.6/site-packages/matplotlib/colors.py
        cs = bm.contour(lonmesh, latmesh, rh,
                        thin_contours, colors="grey",
                        linewidths=0.5, linestyles="solid")
        ax.clabel(cs, colors="grey", fontsize=10, fmt='%i')
        cs = bm.contour(lonmesh, latmesh, rh,
                        np.arange(100, 170, 15), colors="yellow", linewidths=1)

        # Plot geopotential height contours.
        gpm = self.data["geopotential_height"]
        gpm_interval = 40 if self.level <= 500 else 20
        geop_contours = np.arange(400, 28000, gpm_interval)
        cs = bm.contour(lonmesh, latmesh, gpm,
                        geop_contours, colors="darkred", linewidths=2)
        ax.clabel(cs, geop_contours[::2], fontsize=10, fmt='%i')

        titlestring = "Relative Humditiy (%%) and Geopotential Height (m) at " \
            "{:.0f} hPa".format(self.level)
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) // 3600
        titlestring += '\nValid: {} (step {:d} hrs from {})' \
            .format(self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                    time_step_hrs,
                    self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_EQPTStyle_PL_01(MPLBasemapHorizontalSectionStyle):
    """
    Upper Air Field: Equivalent Potential Temperature
    Equivalent potential temperature and geopotential on pressure levels.
    """
    name = "PLEQPT01"
    title = "Equivalent Potential Temperature (degC) and Geopotential Height (m)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("pl", "air_temperature"),
        ("pl", "geopotential_height"),
        ("pl", "specific_humidity")]

    def _prepare_datafields(self):
        """Computes relative humidity from p, t, q.
        """
        self.data["geopotential_height"] = convert_to(
            self.data["geopotential_height"], self.data_units["geopotential_height"], "m", 1. / 9.81)
        self.data["equivalent_potential_temperature"] = thermolib.eqpt_approx(
            self.level * 100., self.data["air_temperature"], self.data["specific_humidity"])

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        filled_contours = np.arange(0, 72, 2)
        thin_contours = np.arange(-40, 100, 2)

        eqpt = data["equivalent_potential_temperature"] - 273.15

        eqptc = bm.contourf(lonmesh, latmesh, eqpt,
                            filled_contours, cmap=plt.cm.gist_rainbow_r)
        if not self.noframe:
            cbar = self.fig.colorbar(eqptc, fraction=0.05, pad=0.08, shrink=0.7)
            cbar.set_label("Equivalent Potential Temperature (degC)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="30%", loc=4)
            cbar = self.fig.colorbar(eqptc, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        # Colors in python2.6/site-packages/matplotlib/colors.py
        cs = bm.contour(lonmesh, latmesh, eqpt,
                        thin_contours, colors="grey",
                        linewidths=0.5, linestyles="solid")
        ax.clabel(cs, thin_contours[::2], colors="grey", fontsize=10, fmt='%i')
        # cs = bm.contour(lonmesh, latmesh, eqpt,
        #                np.arange(100, 170, 15), colors="yellow", linewidths=1)

        # Plot geopotential height contours.
        gpm = self.data["geopotential_height"]
        gpm_interval = 40 if self.level <= 500 else 20
        geop_contours = np.arange(400, 28000, gpm_interval)
        cs = bm.contour(lonmesh, latmesh, gpm,
                        geop_contours, colors="white", linewidths=2)
        ax.clabel(cs, geop_contours[::2], fontsize=10, fmt='%i')

        titlestring = "Equivalent Potential Temperature (degC) and Geopotential Height (m) at " \
                      "{:.0f} hPa".format(self.level)
        time_step = self.valid_time - self.init_time
        time_step_hrs = ((time_step.days * 86400 + time_step.seconds) // 3600)
        titlestring += '\nValid: {} (step {:d} hrs from {})' \
            .format(self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                    time_step_hrs,
                    self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_WStyle_PL_01(MPLBasemapHorizontalSectionStyle):
    """
    Upper Air Field: Vertical Velocity
    Vertical velocity and geopotential on pressure levels.
    """
    name = "PLW01"
    title = "Vertical Velocity (cm/s) and Geopotential Height (m)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("pl", "lagrangian_tendency_of_air_pressure"),
        ("pl", "air_temperature"),
        ("pl", "geopotential_height")]

    def _prepare_datafields(self):
        """Computes relative humidity from p, t, q.
        """
        self.data["geopotential_height"] = convert_to(
            self.data["geopotential_height"], self.data_units["geopotential_height"], "m", 1. / 9.81)
        self.data["upward_wind"] = thermolib.omega_to_w(
            self.data["lagrangian_tendency_of_air_pressure"],
            self.level * 100., self.data["air_temperature"])

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        upward_contours = np.arange(-42, 46, 4)
        w = data["upward_wind"] * 100.

        wc = bm.contourf(lonmesh, latmesh, w,
                         upward_contours, cmap=plt.cm.bwr)
        if not self.noframe:
            cbar = self.fig.colorbar(wc, fraction=0.05, pad=0.08, shrink=0.7)
            cbar.set_label("Vertical velocity (cm/s)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="30%", loc=4)
            cbar = self.fig.colorbar(wc, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        # Colors in python2.6/site-packages/matplotlib/colors.py
        cs = bm.contour(lonmesh, latmesh, w,
                        [2], colors="red",
                        linewidths=0.5, linestyles="solid")
        cs = bm.contour(lonmesh, latmesh, w,
                        [-2], colors="blue",
                        linewidths=0.5, linestyles="solid")
        # ax.clabel(cs, thin_contours[::2], colors="grey", fontsize=10, fmt='%i')
        # cs = bm.contour(lonmesh, latmesh, w,
        #                np.arange(100, 170, 15), colors="yellow", linewidths=1)

        # Plot geopotential height contours.
        gpm = self.data["geopotential_height"]
        gpm_interval = 40 if self.level <= 500 else 20
        geop_contours = np.arange(400, 28000, gpm_interval)
        cs = bm.contour(lonmesh, latmesh, gpm,
                        geop_contours, colors="darkgreen", linewidths=2)
        ax.clabel(cs, geop_contours[::2], fontsize=10, fmt='%i')

        titlestring = "Vertical Velocity (cm/s) and Geopotential Height (m) at " \
                      "{:.0f} hPa".format(self.level)
        time_step = self.valid_time - self.init_time
        time_step_hrs = ((time_step.days * 86400 + time_step.seconds) // 3600)
        titlestring += '\nValid: {} (step {:d} hrs from {})' \
            .format(self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                    time_step_hrs,
                    self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_DivStyle_PL_01(MPLBasemapHorizontalSectionStyle):
    """
    Upper Air Field: Divergence
    Divergence and geopotential on pressure levels.
    """
    name = "PLDiv01"
    title = "Divergence and Geopotential Height (m)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("pl", "divergence_of_wind"),
        ("pl", "geopotential_height")]

    def _prepare_datafields(self):
        self.data["geopotential_height"] = convert_to(
            self.data["geopotential_height"], self.data_units["geopotential_height"], "m", 1. / 9.81)

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        pos_contours = np.arange(4, 42, 4)
        neg_contours = np.arange(-40, 0, 4)

        d = data["divergence_of_wind"] * 1.e5

        # Colors in python2.6/site-packages/matplotlib/colors.py
        cs = bm.contour(lonmesh, latmesh, d,
                        pos_contours, colors="red",
                        linewidths=2, linestyles="solid")
        cs = bm.contour(lonmesh, latmesh, d,
                        neg_contours, colors="blue",
                        linewidths=2, linestyles="solid")

        # Plot geopotential height contours.
        gpm = self.data["geopotential_height"]
        gpm_interval = 40 if self.level <= 500 else 20
        geop_contours = np.arange(400, 28000, gpm_interval)
        cs = bm.contour(lonmesh, latmesh, gpm,
                        geop_contours, colors="darkgreen", linewidths=2)
        ax.clabel(cs, geop_contours[::2], fontsize=10, fmt='%i')

        titlestring = "Divergence (positive: red, negative: blue) and Geopotential Height (m) at " \
            "{:.0f} hPa".format(self.level)
        time_step = self.valid_time - self.init_time
        time_step_hrs = ((time_step.days * 86400 + time_step.seconds) // 3600)
        titlestring += '\nValid: {} (step {:d} hrs from {})' \
            .format(self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                    time_step_hrs,
                    self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_EMAC_TracerStyle_ML_01(MPLBasemapHorizontalSectionStyle):
    """
    Upper Air Field: EMAC Tracer
    """
    name = "EMAC_Eyja_Tracer"
    title = "EMAC Eyjafjallajokull Tracer (Model Level) (relative)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "emac_R12")]

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        tracer = data["emac_R12"] * 1.e4

        # Shift lat/lon grid for PCOLOR (see comments in HS_EMAC_TracerStyle_SFC_01).
        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh_ = lonmesh_ - ((self.lons[1] - self.lons[0]) / 2.)
        latmesh_ = latmesh_ - ((self.lats[1] - self.lats[0]) / 2.)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        tc = bm.pcolor(lonmesh, latmesh, tracer,
                       cmap=plt.cm.hot_r,
                       norm=matplotlib.colors.LogNorm(vmin=1., vmax=100.),
                       edgecolors='none')

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        ac = bm.contour(lonmesh, latmesh, tracer,
                        np.arange(1, 101, 1)[::2],
                        colors="b", linewidths=1)
        ax.clabel(ac, fontsize=10, fmt='%i')

        if not self.noframe:
            cbar = self.fig.colorbar(tc, fraction=0.05, pad=0.08, shrink=0.7)
            cbar.set_label("Tracer (relative)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="30%", loc=4)
            cbar = self.fig.colorbar(tc, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        titlestring = "EMAC Eyjafjallajokull Tracer (relative) at model level {:.0f}".format(self.level)
        time_step = self.valid_time - self.init_time
        time_step_hrs = ((time_step.days * 86400 + time_step.seconds) // 3600)
        titlestring += '\nValid: {} (step {:d} hrs from {})' \
            .format(self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                    time_step_hrs,
                    self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_EMAC_TracerStyle_SFC_01(MPLBasemapHorizontalSectionStyle):
    """
    2D field: EMAC total column density
    """
    name = "EMAC_Eyja_TotalColumn"
    title = "EMAC Eyjafjallajokull Tracer Total Column Density (kg/m^2)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("sfc", "emac_column_density")]

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        tracer = data["emac_column_density"]

        # PCOLOR draws the grid boxes so that the coordinates given for a point
        # become the lower left corner of the grid box. This, however, is wrong
        # for ECMWF and EMAC: the variable value is given at the point that is
        # specified by the coordinates, hence a correct visualisation has to draw
        # the point in the middle of the grid box. To achieve this with
        # pcolor, we shift the lat/lon grid by one half grid box size.
        # NOTE that this assumes a regular grid, which is not fully true for
        # EMAC's latitudes. The error, however, is small, thus we neglect it
        # here.
        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh_ -= ((self.lons[1] - self.lons[0]) / 2.)
        latmesh_ -= ((self.lats[1] - self.lats[0]) / 2.)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        tc = bm.pcolor(lonmesh, latmesh, tracer,
                       cmap=plt.cm.hot_r,
                       # norm=matplotlib.colors.Normalize(vmin=0.1, vmax=1.5),
                       norm=matplotlib.colors.LogNorm(vmin=0.05, vmax=0.5),
                       edgecolors='none')

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        ac = bm.contour(lonmesh, latmesh, tracer,
                        np.arange(0.05, 0.55, 0.05),
                        colors="b", linewidths=1)
        ax.clabel(ac, fontsize=10, fmt='%.2f')

        if not self.noframe:
            cbar = self.fig.colorbar(tc, fraction=0.05, pad=0.08, shrink=0.7)
            cbar.set_label("column density (kg/m^2)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="30%", loc=4)
            cbar = self.fig.colorbar(tc, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        titlestring = "EMAC Eyjafjallajokull Tracer Total Column Density (kg/m^2)"
        time_step = self.valid_time - self.init_time
        time_step_hrs = ((time_step.days * 86400 + time_step.seconds) // 3600)
        titlestring += '\nValid: {} (step {:d} hrs from {})' \
            .format(self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                    time_step_hrs,
                    self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_PVTropoStyle_PV_01(MPLBasemapHorizontalSectionStyle):
    """
    Dynamical (2PVU) Tropopause Fields
    Dynamical tropopause plots (2-PVU level). Three styles are available:
    Pressure, potential temperature, and geopotential height.
    """
    name = "PVTropo01"
    title = "Dynamical Tropopause"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("pv", "air_potential_temperature"),
        ("pv", "geopotential_height"),
        ("pv", "air_pressure")]

    styles = [
        ("default", "Pressure (hPa)"),
        ("GEOP", "Geopotential Height (m)"),
        ("PT", "Potential Temperature (K)"),
        ("PRES", "Pressure (hPa)")]

    def _prepare_datafields(self):
        self.data["air_pressure"] = convert_to(
            self.data["air_pressure"], self.data_units["air_pressure"], "hPa", 1)
        self.data["geopotential_height"] = convert_to(
            self.data["geopotential_height"], self.data_units["geopotential_height"], "m", 1. / 9.81)

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        # Default style is pressure.
        if self.style.lower() == "default":
            self.style = "PRES"

        # Define colourbars and contour levels for the three styles. For
        # pressure and height, a terrain colourmap is used (bluish colours for
        # low altitudes, brownish colours for high altitudes). For potential
        # temperature, a rainbow colourmap is used (blue=low temps, red=hight
        # temps).
        if self.style == "PRES":
            filled_contours = np.arange(120, 551, 10)
            thin_contours = np.arange(100, 601, 40)
            vardata = data["air_pressure"]
            label = "Pressure (hPa)"
            fcmap = plt.cm.terrain_r
        elif self.style == "PT":
            filled_contours = np.arange(280, 380, 2)
            thin_contours = np.arange(260, 440, 10)
            vardata = data["air_potential_temperature"]
            label = "Potential Temperature (K)"
            fcmap = plt.cm.gist_rainbow_r
        elif self.style == "GEOP":
            filled_contours = np.arange(5000, 15000, 250)
            thin_contours = np.arange(5000, 15000, 500)
            vardata = data["geopotential_height"]
            label = "Geopotential Height (m)"
            fcmap = plt.cm.terrain

        # Filled contour plot of pressure/geop./pot.temp. Extend the colourbar
        # to fill regions whose values exceed the colourbar range.
        contours = bm.contourf(lonmesh, latmesh, vardata,
                               filled_contours, cmap=fcmap, extend="both")
        if not self.noframe:
            cbar = self.fig.colorbar(contours, fraction=0.05, pad=0.08, shrink=0.7)
            cbar.set_label(label)
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="30%", loc=4)
            cbar = self.fig.colorbar(contours, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        # Colors in python2.6/site-packages/matplotlib/colors.py
        cs = bm.contour(lonmesh, latmesh, vardata,
                        thin_contours, colors="yellow",
                        linewidths=0.5, linestyles="solid")
        ax.clabel(cs, thin_contours[::2], colors="red", fontsize=11, fmt='%i')

        if self.style == "PRES":
            titlestring = "Dynamical Tropopause Pressure (hPa) at " \
                          "{:.1f} PVU".format(int(self.level))
        elif self.style == "PT":
            titlestring = "Dynamical Tropopause Potential Temperature (K) at " \
                          "{:.1f} PVU".format(int(self.level))
        elif self.style == "GEOP":
            titlestring = "Dynamical Tropopause Geopotential Height (m) at " \
                          "{:.1f} PVU".format(int(self.level))
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) // 3600
        titlestring += '\nValid: {} (step {:d} hrs from {})' \
            .format(self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                    time_step_hrs,
                    self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_ThermalTropoStyle_SFC_01(MPLBasemapHorizontalSectionStyle):
    """
    Dynamical (2PVU) Tropopause Fields
    Dynamical tropopause plots (2-PVU level). Three styles are available:
    Pressure, potential temperature, and geopotential height.
    """
    name = "ThermalTropo01"
    title = "Thermal Tropopause"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("sfc", "tropopause_altitude"),
        ("sfc", "secondary_tropopause_altitude"),
    ]

    styles = [
        ("default", "Overview"),
        ("primary", "Primary Thermal Tropopause"),
        ("secondary", "Secondary Thermal Tropopause"),
    ]

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        # Define colourbars and contour levels for the three styles. For
        # pressure and height, a terrain colourmap is used (bluish colours for
        # low altitudes, brownish colours for high altitudes). For potential
        # temperature, a rainbow colourmap is used (blue=low temps, red=hight
        # temps).
        fcmap = plt.cm.terrain

        if self.data_units["tropopause_altitude"] != "km":
            raise ValueError("tropopause_altitude has wrong unit %s. Should be 'km'",
                             self.data_units["tropopause_altitude"])
        if self.data_units["secondary_tropopause_altitude"] != "km":
            raise ValueError("secondary_tropopause_altitude has wrong unit %s. Should be 'km'",
                             self.data_units["secondary_tropopause_altitude"])

        if self.style == "default":
            vardata = data["tropopause_altitude"]
            label = "Primary Tropopause (km)"
        elif self.style == "primary":
            vardata = data["tropopause_altitude"]
            label = "Primary Tropopause (km)"
        elif self.style == "secondary":
            vardata = data["secondary_tropopause_altitude"]
            label = "Secondary Tropopause (km)"
        filled_contours = np.arange(5, 18, 0.25)
        thin_contours = np.arange(5, 18, 1.0)

        # Filled contour plot of pressure/geop./pot.temp. Extend the colourbar
        # to fill regions whose values exceed the colourbar range.
        contours = bm.contourf(lonmesh, latmesh, vardata,
                               filled_contours, cmap=fcmap, extend="both")

        data["secondary_tropopause_altitude"] = np.ma.masked_invalid(data["secondary_tropopause_altitude"])

        if self.style == "default":
            mask = ~data["secondary_tropopause_altitude"].mask
            bm.contourf(lonmesh, latmesh, mask, [0, 0.5, 1.5], hatches=["", "xx"], alpha=0)

        if not self.noframe:
            cbar = self.fig.colorbar(contours, fraction=0.05, pad=0.08, shrink=0.7)
            cbar.set_label(label)
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="30%", loc=4)
            self.fig.colorbar(contours, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

            # adjust colorbar fontsize to figure height
            fontsize = self.fig.bbox.height * 0.024
            for x in axins1.yaxis.majorTicks:
                x.label1.set_path_effects([patheffects.withStroke(linewidth=4, foreground='w')])
                x.label1.set_fontsize(fontsize)

        # Colors in python2.6/site-packages/matplotlib/colors.py
        cs = bm.contour(lonmesh, latmesh, vardata,
                        thin_contours, colors="yellow",
                        linewidths=0.5, linestyles="solid")
        ax.clabel(cs, thin_contours[::2], colors="red", fontsize=11, fmt='%i')


class HS_VIProbWCB_Style_01(MPLBasemapHorizontalSectionStyle):
    """
    Surface Field: Probability of WCB
    Total column probability of WCB trajectory occurence, derived from
    Lagranto trajectories (TNF 2012 product).
    """
    name = ""
    title = "Total Column Probability of WCB (%)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("sfc", "air_pressure_at_sea_level"),
        ("sfc", "vertically_integrated_probability_of_wcb_occurrence")
    ]

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        thick_contours = np.arange(952, 1050, 8)
        thin_contours = [c for c in np.arange(952, 1050, 2)
                         if c not in thick_contours]

        mslp = 0.01 * data["air_pressure_at_sea_level"]
        pwcb = 100. * data["vertically_integrated_probability_of_wcb_occurrence"]

        # Contour plot of mean sea level pressure.
        cs = bm.contour(lonmesh, latmesh, mslp,
                        thick_contours, colors="darkblue", linewidths=2)
        ax.clabel(cs, fontsize=12, fmt='%i')
        cs = bm.contour(lonmesh, latmesh, mslp,
                        thin_contours, colors="darkblue", linewidths=1)

        # Filled contours of p(WCB).
        contours = bm.contourf(lonmesh, latmesh, pwcb,
                               np.arange(0, 101, 10), cmap=plt.cm.pink_r)
        if not self.noframe:
            self.fig.colorbar(contours, fraction=0.05, pad=0.08, shrink=0.7)
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="30%", loc=4)
            self.fig.colorbar(contours, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        titlestring = "Mean sea level pressure (hPa) and total column probability of WCB (0-1)"
        time_step = self.valid_time - self.init_time
        time_step_hrs = ((time_step.days * 86400 + time_step.seconds) // 3600)
        titlestring += '\nValid: {} (step {:d} hrs from {})' \
            .format(self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                    time_step_hrs,
                    self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_LagrantoTrajStyle_PL_01(MPLBasemapHorizontalSectionStyle):
    """
    Upper level Field: Lagranto WCB/INSITU/MIX trajectories
    Number of Lagranto trajectories per grid box for WCB, MIX, INSITU
    trajectories (ML-Cirrus 2014 product).
    """
    name = ""
    title = "Cirrus density, insitu red, mix blue, wcb colour (1E-6/km^2/hPa)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("pl", "number_of_wcb_trajectories"),
        ("pl", "number_of_insitu_trajectories"),
        ("pl", "number_of_mix_trajectories")
    ]

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        thin_contours = [0.1, 0.5, 1., 2., 3., 4., 5., 6., 7., 8.]

        nwcb = 1.E6 * data["number_of_wcb_trajectories"]
        ninsitu = 1.E6 * data["number_of_insitu_trajectories"]
        nmix = 1.E6 * data["number_of_mix_trajectories"]

        # Contour plot of num(INSITU).
        # cs = bm.contour(lonmesh, latmesh, ninsitu,
        #                thick_contours, colors="darkred", linewidths=2)
        # ax.clabel(cs, fontsize=12, fmt='%i')
        cs = bm.contour(lonmesh, latmesh, ninsitu,
                        thin_contours, colors="red", linewidths=1)
        ax.clabel(cs, fontsize=12, fmt='%.1f')

        # Contour plot of num(MIX).
        # cs = bm.contour(lonmesh, latmesh, nmix,
        #                thick_contours, colors="darkblue", linewidths=2)
        # ax.clabel(cs, fontsize=12, fmt='%i')
        cs = bm.contour(lonmesh, latmesh, nmix,
                        thin_contours, colors="darkblue", linewidths=1)
        ax.clabel(cs, fontsize=12, fmt='%.1f')

        # Filled contours of num(WCB).
        contours = bm.contourf(lonmesh, latmesh, nwcb,
                               thin_contours, cmap=plt.cm.gist_ncar_r, extend="max")
        if not self.noframe:
            self.fig.colorbar(contours, fraction=0.05, pad=0.08, shrink=0.7)
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="30%", loc=4)
            self.fig.colorbar(contours, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        titlestring = "Cirrus density, insitu red, mix blue, wcb colour (1E-6/km^2/hPa)"
        time_step = self.valid_time - self.init_time
        time_step_hrs = ((time_step.days * 86400 + time_step.seconds) // 3600)
        titlestring += '\nValid: {} (step {:d} hrs from {})' \
            .format(self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                    time_step_hrs,
                    self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_BLH_MSLP_Style_01(MPLBasemapHorizontalSectionStyle):
    """
    Surface Field: Boundary Layer Height
    """
    name = "BLH"
    title = "Boundary Layer Height (m)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("sfc", "air_pressure_at_sea_level"),
        ("sfc", "atmosphere_boundary_layer_thickness")]

    def _prepare_datafields(self):
        self.data["air_pressure_at_sea_level"] = convert_to(
            self.data["air_pressure_at_sea_level"], self.data_units["air_pressure_at_sea_level"], "hPa", 1)
        self.data["atmosphere_boundary_layer_thickness"] = convert_to(
            self.data["atmosphere_boundary_layer_thickness"],
            self.data_units["atmosphere_boundary_layer_thickness"], "m", 1)

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        thick_contours = np.arange(952, 1050, 8)
        thin_contours = [c for c in np.arange(952, 1050, 2)
                         if c not in thick_contours]

        mslp = data["air_pressure_at_sea_level"]

        # Colors in python2.6/site-packages/matplotlib/colors.py
        cs = bm.contour(lonmesh, latmesh, mslp,
                        thick_contours, colors="darkred", linewidths=2)
        ax.clabel(cs, fontsize=12, fmt='%i')
        cs = bm.contour(lonmesh, latmesh, mslp,
                        thin_contours, colors="darkred", linewidths=1)

        # Filled contours of BLH, interval 100m.
        blh = data["atmosphere_boundary_layer_thickness"]
        contours = bm.contourf(lonmesh, latmesh, blh,
                               np.arange(0, 3000, 100), cmap=plt.cm.terrain, extend="max")
        if not self.noframe:
            self.fig.colorbar(contours, fraction=0.05, pad=0.08, shrink=0.7)
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="30%", loc=4)
            self.fig.colorbar(contours, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        # Labelled thin grey contours of BLH, interval 500m.
        cs = bm.contour(lonmesh, latmesh, blh,
                        np.arange(0, 3000, 500), colors="grey", linewidths=0.5)
        ax.clabel(cs, fontsize=12, fmt='%i')

        # Title
        titlestring = "Boundary layer height (m) and mean sea level pressure (hPa)"
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) // 3600
        titlestring += '\nValid: {} (step {:d} hrs from {})' \
            .format(self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                    time_step_hrs,
                    self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_Meteosat_BT108_01(MPLBasemapHorizontalSectionStyle):
    """
    Meteosat brightness temperature
    """
    name = "MSG_BT108"
    title = "Brightness Temperature 10.8um (K)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("sfc", "msg_brightness_temperature_108")]

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        cmin = 230
        cmax = 300
        # thick_contours = np.arange(cmin, cmax, 6)
        # thin_contours = [c for c in np.arange(cmin, cmax, 2) \
        #                  if c not in thick_contours]

        tempC = data["msg_brightness_temperature_108"]

        logging.debug("Min: %.2f K, Max: %.2f K", tempC.min(), tempC.max())

        tc = bm.contourf(lonmesh, latmesh, tempC,
                         np.arange(cmin, cmax, 2), cmap=plt.cm.gray_r, extend="both")
        if not self.noframe:
            cbar = self.fig.colorbar(tc, fraction=0.05, pad=0.08, shrink=0.7)
            cbar.set_label("Brightness Temperature (K)")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="30%", loc=4)
            cbar = self.fig.colorbar(tc, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        # Colors in python2.6/site-packages/matplotlib/colors.py
        # cs = bm.contour(lonmesh, latmesh, tempC,
        #                 [0], colors="red", linewidths=4)
        # cs = bm.contour(lonmesh, latmesh, tempC,
        #                 thick_contours, colors="saddlebrown", linewidths=2)
        # ax.clabel(cs, fontsize=14, fmt='%i')
        # cs = bm.contour(lonmesh, latmesh, tempC,
        #                 thin_contours, colors="saddlebrown", linewidths=1)

        titlestring = "10.8 um Brightness Temperature (K)"
        titlestring += u'\nValid: {}' \
            .format(self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


class HS_MSSChemStyle(MPLBasemapHorizontalSectionStyle):
    """
    Pressure level version for Chemical Mixing ratios.
    """
    styles = [
        ("auto", "auto colour scale"),
        ("autolog", "auto logcolour scale"), ]

    # In order to use information from the DataAccess class to construct the titles, we override the set_driver to set
    # self.title.  This cannot happen in __init__, as the WMSServer doesn't initialize the layers with the driver but
    # rather sets the driver only after initialization.
    def set_driver(self, driver):
        super(HS_MSSChemStyle, self).set_driver(driver=driver)
        self.title = self._title_tpl.format(modelname=self.driver.data_access._modelname)

    def _plot_style(self):
        bm = self.bm
        ax = self.bm.ax

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        show_data = np.ma.masked_invalid(self.data[self.dataname]) * self.unit_scale
        # get cmin, cmax, cbar_log and cbar_format for level_key
        cmin, cmax = Targets.get_range(self.dataname, self.level, self.name[-2:])
        cmin, cmax, clevs, cmap, norm, ticks = get_style_parameters(
            self.dataname, self.style, cmin, cmax, show_data)

        tc = bm.contourf(lonmesh, latmesh, show_data, levels=clevs, cmap=cmap, extend="both", norm=norm)

        for cont_data, cont_levels, cont_colour, cont_label_colour, cont_style, cont_lw, pe in self.contours:
            cs_pv = ax.contour(lonmesh, latmesh, self.data[cont_data], cont_levels,
                               colors=cont_colour, linestyles=cont_style, linewidths=cont_lw)
            cs_pv_lab = ax.clabel(cs_pv, colors=cont_label_colour, fmt='%i')
            if pe:
                plt.setp(cs_pv.collections, path_effects=[patheffects.withStroke(linewidth=cont_lw + 2,
                                                                                 foreground="w")])
                plt.setp(cs_pv_lab, path_effects=[patheffects.withStroke(linewidth=1, foreground="w")])

        # define position of the colorbar and the orientation of the ticks
        if self.epsg == 77774020:
            cbar_location = 3
            tick_pos = 'right'
        else:
            cbar_location = 4
            tick_pos = 'left'

        # Format for colorbar labels
        cbar_label = self.title
        cbar_format = get_cbar_label_format(self.style, np.abs(clevs).max())

        if not self.noframe:
            cbar = self.fig.colorbar(tc, fraction=0.05, pad=0.08, shrink=0.7,
                                     norm=norm, label=cbar_label, format=cbar_format, ticks=ticks)
            cbar.set_ticklabels(clevs)
            cbar.set_ticks(clevs)
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="40%", loc=cbar_location)
            self.fig.colorbar(tc, cax=axins1, orientation="vertical", format=cbar_format, ticks=ticks)

            # adjust colorbar fontsize to figure height
            fontsize = self.fig.bbox.height * 0.024
            axins1.yaxis.set_ticks_position(tick_pos)
            for x in axins1.yaxis.majorTicks:
                x.label1.set_path_effects([patheffects.withStroke(linewidth=4, foreground='w')])
                x.label1.set_fontsize(fontsize)


def make_msschem_class(entity, nam, vert, units, scale, add_data=None, add_contours=None, fix_styles=None,
                       add_styles=None, add_prepare=None):
    if add_data is None:
        add_data = []
    _contourname = ""
    if add_contours is None:
        add_contours = []
    elif add_contours[0][0] == "air_pressure":
        _contourname = "_pcontours"

    class fnord(HS_MSSChemStyle):
        name = u"HS_{}_{}{}".format(entity, vert, _contourname)
        dataname = entity
        units, unit_scale = Targets.get_unit(dataname)
        units = units
        unit_scale = scale
        _title_tpl = nam + " (" + vert + ")"
        long_name = entity
        if units:
            _title_tpl += u" ({})".format(units)

        required_datafields = [(vert, entity)] + add_data
        contours = add_contours

    fnord.__name__ = nam
    fnord.styles = list(fnord.styles)

    return fnord


for vert in ["ml", "al", "pl"]:
    for stdname, props in list(MSSChemTargets.items()):
        name, qty, units, scale = props
        key = "HS_MSSChemStyle_" + vert.upper() + "_" + name + "_" + qty
        globals()[key] = make_msschem_class(stdname, name, vert, units, scale)

_pressurelevels = np.linspace(5000, 95000, 19)
_npressurelevels = len(_pressurelevels)
for vert in ["ml"]:
    for stdname, props in list(MSSChemTargets.items()):
        name, qty, units, scale = props
        # ToDo string substitution
        key = "HS_MSSChemStyle_" + vert.upper() + "_" + name + "_" + qty + "_pcontours"
        globals()[key] = make_msschem_class(stdname, name, vert, units, scale, add_data=[(vert, "air_pressure")],
                                            add_contours=[("air_pressure", _pressurelevels,
                                                           ["dimgrey"] * _npressurelevels,
                                                           ["dimgrey"] * _npressurelevels,
                                                           ["dotted"] * _npressurelevels, 1, True)],)
