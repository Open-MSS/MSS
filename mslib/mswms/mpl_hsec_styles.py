"""Matplotlib horizontal section styles.

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

AUTHORS:
========

* Marc Rautenhaus (mr)

"""

# standard library imports
import logging

# related third party imports
import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.axes_grid1.inset_locator
import matplotlib.colors
import mpl_toolkits.basemap

# local application imports
from mslib.mswms.mpl_hsec import MPLBasemapHorizontalSectionStyle
from mslib import thermolib

"""
Surface Field: CLOUDS
"""


class HS_CloudsStyle_01(MPLBasemapHorizontalSectionStyle):
    """
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
                axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                          width="3%",  # width = % of parent_bbox width
                                                                          height="30%",  # height : %
                                                                          loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
                cbar = self.fig.colorbar(lcc, cax=axins1, orientation="vertical")
                axins1.yaxis.set_ticks_position("left")

        if self.style in ["MED", "TOT"]:
            mcc = bm.contourf(lonmesh, latmesh, data['medium_cloud_area_fraction'],
                              np.arange(0.2, 1.1, 0.1), cmap=plt.cm.summer_r)
            if not self.noframe:
                self.fig.colorbar(mcc, fraction=0.05, pad=-0.02, shrink=0.7, format='')
            else:
                axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                          width="2%" if self.style == "TOT" else "3%",
                                                                          # width = % of parent_bbox width
                                                                          height="30%",  # height : %
                                                                          loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
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
                axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                          width="1%" if self.style == "TOT" else "3%",
                                                                          # width = % of parent_bbox width
                                                                          height="30%",  # height : %
                                                                          loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
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
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) / 3600
        titlestring = titlestring + '\nValid: %s (step %i hrs from %s)' % \
                                    (self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                                     time_step_hrs,
                                     self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


"""
Surface Field: Mean Sea Level Pressure
"""


# from scipy.ndimage import minimum_filter
# def local_minima(fits, window=15):
#     """Find the local minima within fits, and return them and their
#        indices.

#     Returns a list of indices at which the minima were found, and a
#     list of the minima, sorted in order of increasing minimum. The
#     keyword argument window determines how close two local minima
#     are allowed to be to one another.  If two local minima are found
#     closer together than that, then the lowest of them is taken as
#     the real minimum.  window=1 will return all local minima.

#     Taken from
#     http://mail.scipy.org/pipermail/scipy-user/2008-August/017886.html
#     """
#     fits = np.asarray(fits)
#     minfits = minimum_filter(fits, size=window, mode="wrap")
#     minima_mask = fits == minfits
#     good_indices = np.arange(len(fits))[minima_mask]
#     good_fits = fits[minima_mask]
#     order = good_fits.argsort()
#     return good_indices[order], good_fits[order]

class HS_MSLPStyle_01(MPLBasemapHorizontalSectionStyle):
    """
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
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) / 3600
        titlestring = titlestring + '\nValid: %s (step %i hrs from %s)' % \
                                    (self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                                     time_step_hrs,
                                     self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


"""
Surface Field: Solar Elevation Angle
"""


class HS_SEAStyle_01(MPLBasemapHorizontalSectionStyle):
    """
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
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="3%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(scs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        # Contour lines plot.
        # Colors in python2.6/site-packages/matplotlib/colors.py
        cs1 = bm.contour(lonmesh, latmesh, sea,
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
        titlestring = titlestring + "\nValid: %s" % \
                                    self.valid_time.strftime("%a %Y-%m-%d %H:%M UTC")
        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


"""
Surface Field: Sea Ice Cover
"""


class HS_SeaIceStyle_01(MPLBasemapHorizontalSectionStyle):
    """
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
            lonmesh_ = lonmesh_ - (self.lons[1] - self.lons[0]) / 2.
            latmesh_ = latmesh_ - (self.lats[1] - self.lats[0]) / 2.
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
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="3%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(scs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        # Plot title.
        titlestring = "Sea Ice Cover"
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) / 3600
        titlestring = titlestring + '\nValid: %s (step %i hrs from %s)' % \
                                    (self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                                     time_step_hrs,
                                     self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))
        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


"""
Upper Air Field: Temperature
"""


class HS_TemperatureStyle_ML_01(MPLBasemapHorizontalSectionStyle):
    """
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
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="3%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
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

        titlestring = "Temperature (degC) at model level %i" % self.level
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) / 3600
        titlestring = titlestring + '\nValid: %s (step %i hrs from %s)' % \
                                    (self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                                     time_step_hrs,
                                     self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


"""
Chemical Mixing Ratios (CLaMS)
"""

CLAMS_CONFIG = {
    u'BVF': {'levels': {50: (0.00029, 0.00095),
                        70: (0.00029, 0.00074),
                        100: (0.00029, 0.00064),
                        125: (0.00031, 0.00062),
                        150: (0.0003, 0.00067),
                        175: (0.00031, 0.00065),
                        200: (0.00026, 0.00065),
                        250: (5.9e-05, 0.00067),
                        350: (-6.7e-06, 0.0005),
                        500: (-9.4e-07, 0.00058)},
             'units': u's**-2'},
    u'CH4': {'levels': {50: (0.5, 1.7),
                        70: (0.81, 1.7),
                        100: (1.1, 1.8),
                        125: (1.2, 1.8),
                        150: (1.3, 1.8),
                        175: (1.4, 1.8),
                        200: (1.5, 1.9),
                        250: (1.6, 1.9),
                        350: (1.6, 2.0),
                        500: (1.7, 2.0)},
             'units': u'ppmv'},
    u'CO': {'levels': {50: (0., 20),
                       500: (0, 200.0)},
            'units': u'ppbv'},
    u'F12': {'levels': {50: (0., 550.0),
                        500: (0, 550.0)},
             'units': u'pptv'},
    u'SEA': {'levels': {50: (0., 50.0),
                        500: (0, 100.0)},
             'units': u'%'},
    u'ECH': {'levels': {50: (0., 50.0),
                        500: (0, 100.0)},
             'units': u'%'},
    u'NIN': {'levels': {50: (0., 50.0),
                        500: (0, 100.0)},
             'units': u'%'},
    u'SIN': {'levels': {50: (0., 50.0),
                        500: (0, 100.0)},
             'units': u'%'},
    u'ICH': {'levels': {50: (0., 50.0),
                        500: (0, 100.0)},
             'units': u'%'},
    u'EQLAT': {'levels': {50: (9.2, 90.0),
                          70: (8.0, 90.0),
                          100: (-0.18, 90.0),
                          125: (10.0, 90.0),
                          150: (20.0, 90.0),
                          175: (22.0, 90.0),
                          200: (-6.7, 90.0),
                          250: (-46.0, 90.0),
                          350: (-42.0, 90.0),
                          500: (-47.0, 90.0)},
               'units': u'deg N'},
    u'F11': {'levels': {50: (0.0, 220.0),
                        70: (0.0, 230.0),
                        100: (32.0, 240.0),
                        125: (65.0, 240.0),
                        150: (110.0, 240.0),
                        175: (150.0, 240.0),
                        200: (180.0, 240.0),
                        250: (210.0, 240.0),
                        350: (220.0, 240.0),
                        500: (220.0, 240.0)},
             'units': u'pptv'},
    u'H2O': {'levels': {50: (3.4, 6.1),
                        70: (3.2, 5.0),
                        100: (3.6, 4.6),
                        125: (3.7, 8.2),
                        150: (3.9, 23.0),
                        175: (4.0, 44.0),
                        200: (0.0, 9400.0),
                        250: (0.0, 9600.0),
                        350: (0.0, 11000.0),
                        500: (0.0, 9100.0)},
             'units': u'ppmv'},
    u'N2O': {'levels': {50: (45.0, 310.0),
                        70: (95.0, 310.0),
                        100: (160.0, 320.0),
                        125: (190.0, 320.0),
                        150: (230.0, 320.0),
                        175: (260.0, 330.0),
                        200: (280.0, 330.0),
                        250: (300.0, 330.0),
                        350: (300.0, 330.0),
                        500: (310.0, 330.0)},
             'units': u'ppbv'},
    u'O3': {'levels': {50: (0.97, 4.8),
                       70: (0.56, 3.4),
                       100: (0.2, 2.4),
                       125: (0.13, 1.9),
                       150: (0.14, 1.6),
                       175: (0.073, 1.2),
                       200: (0.0, 0.83),
                       250: (0.031, 0.33),
                       350: (0.033, 0.24),
                       500: (0.036, 0.21)},
            'units': u'ppmv'},
    u'PV': {'levels': {50: (11.0, 120.0),
                       70: (7.9, 54.0),
                       100: (-0.31, 28.0),
                       125: (3.4, 21.0),
                       150: (1.6, 18.0),
                       175: (0.74, 13.0),
                       200: (0.0, 11.0),
                       250: (-0.6, 9.1),
                       350: (-0.44, 7.6),
                       500: (-0.26, 4.4)},
            'units': u'PVU'},
    u'TEMP': {'levels': {50: (180.0, 250.0),
                         70: (190.0, 250.0),
                         100: (190.0, 240.0),
                         125: (190.0, 240.0),
                         150: (190.0, 240.0),
                         175: (190.0, 240.0),
                         200: (190.0, 240.0),
                         250: (200.0, 240.0),
                         350: (210.0, 250.0),
                         500: (220.0, 260.0)},
              'units': u'K'},
    u'THETA': {'levels': {50: (440.0, 590.0),
                          70: (400.0, 520.0),
                          100: (370.0, 460.0),
                          125: (350.0, 420.0),
                          150: (330.0, 400.0),
                          175: (320.0, 390.0),
                          200: (310.0, 370.0),
                          250: (290.0, 350.0),
                          350: (280.0, 330.0),
                          500: (270.0, 320.0)},
               'units': u'K'},
    u'U': {'levels': {50: (-38.0, 69.0),
                      70: (-23.0, 67.0),
                      100: (-22.0, 70.0),
                      125: (-20.0, 66.0),
                      150: (-20.0, 72.0),
                      175: (-20.0, 67.0),
                      200: (-22.0, 76.0),
                      250: (-37.0, 92.0),
                      350: (-36.0, 85.0),
                      500: (-29.0, 63.0)},
           'units': u'm s^-1'},
    u'V': {'levels': {50: (-67.0, 50.0),
                      70: (-56.0, 43.0),
                      100: (-48.0, 39.0),
                      125: (-46.0, 35.0),
                      150: (-48.0, 36.0),
                      175: (-47.0, 45.0),
                      200: (-52.0, 57.0),
                      250: (-70.0, 71.0),
                      350: (-70.0, 78.0),
                      500: (-46.0, 47.0)},
           'units': u'm s^-1'}}


class HS_ChemStyle_PL(MPLBasemapHorizontalSectionStyle):
    """Pressure level version for Chemical Mixing ratios.
    """
    styles = [
        ("default", "fixed colour scale"),
        ("log", "logarithmic colour scale"),
        ("auto", "auto colour scale"),
        ("autolog", "auto logcolour scale"), ]

    def _plot_style(self):
        bm = self.bm
        ax = self.bm.ax

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        show_data = np.ma.masked_invalid(self.data[self.dataname])
        cbar_label = self.name + "(" + CLAMS_CONFIG[self.name]["units"] + ")"

        clevs = CLAMS_CONFIG[self.name]["levels"].keys()
        diff = np.array(clevs) - self.level
        nextlev = clevs[abs(diff).argmin()]

        # colour scale of plot
        # cmap = plt.cm.cubehelix_r
        cmap = plt.cm.gist_rainbow_r

        # get cmin, cmax, cbar_log and cbar_format for level_key
        cmin, cmax = CLAMS_CONFIG[self.name]["levels"][nextlev]

        if self.style == "auto":
            cmin, cmax = show_data.min(), show_data.max()
            if cmin > 0 and cmin < 0.05 * cmax:
                cmin = 0.
            clevs = np.linspace(cmin, cmax, 17)
            norm = None
        elif self.style == "autolog":
            cmin, cmax = show_data.min(), show_data.max()
            if cmin <= 1.E-6 * cmax and cmax > 0.:
                cmin = cmax * 1.E-6
            lncmin, lncmax = np.log([cmin, cmax])
            clevs = np.exp(np.linspace(lncmin, lncmax, 17))
            norm = matplotlib.colors.LogNorm(cmin, cmax)

        elif self.style == "log":
            cmin = max(cmin, cmax * 0.001)
            lncmin, lncmax = np.log([cmin, cmax])
            clevs = np.exp(np.linspace(lncmin, lncmax, 17))
            norm = matplotlib.colors.LogNorm(cmin, cmax)
        else:
            clevs = np.linspace(cmin, cmax, 17)
            norm = None

        tc = bm.contourf(lonmesh, latmesh, show_data, levels=clevs,
                         cmap=cmap, norm=norm)
        pv = bm.contour(lonmesh, latmesh, self.data["ertel_potential_vorticity"],
                        [2, 4, 8, 16],
                        colors=(1.0, 1.0, 1.0, 1), linewidths=5, zorder=50)
        ax.clabel(pv, fmt="%d", zorder=200)
        pv = bm.contour(lonmesh, latmesh, self.data["ertel_potential_vorticity"],
                        [2, 4, 8, 16],
                        colors=(0.4, 0.4, 0.4, 1), linewidths=2, zorder=100)
        ax.clabel(pv, fmt="%d", zorder=200)

        # define position of the colorbar and the orientation of the ticks
        if self.epsg == 77774020:
            cbar_location = 3
            tick_pos = 'right'
        else:
            cbar_location = 4
            tick_pos = 'left'

        # Format for colorbar labels
        clev_format = "%.3g"
        mclev = np.abs(clevs).max()
        if self.style != "log":
            if mclev >= 100. and mclev < 10000.:
                clev_format = "%4i"
            if mclev >= 10. and mclev < 100.:
                clev_format = "%.1f"
            if mclev >= 1. and mclev < 10.:
                clev_format = "%.2f"
            if mclev >= .1 and mclev < 1.:
                clev_format = "%.3f"
            if mclev >= .01 and mclev < 0.1:
                clev_format = "%.4f"

        if not self.noframe:
            cbar = self.fig.colorbar(tc, fraction=0.05, pad=0.08, shrink=0.7,
                                     norm=norm, label=cbar_label)
            cbar.set_ticklabels(clevs)
            cbar.set_ticks(clevs)
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax,
                width="3%",  # width = % of parent_bbox width
                height="30%",  # height : %
                loc=cbar_location)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(tc, cax=axins1, orientation="vertical",
                                     format=clev_format, norm=norm)

            # adjust colorbar fontsize to figure height
            figheight = self.fig.bbox.height
            fontsize = figheight * 0.026
            axins1.yaxis.set_ticks_position(tick_pos)
            for x in axins1.yaxis.majorTicks:
                x.label1.set_backgroundcolor("w")
                x.label2.set_backgroundcolor("w")
                x.label1.set_fontsize(fontsize)
                x.label2.set_fontsize(fontsize)


def make_clams_chem_class(entity):
    class fnord(HS_ChemStyle_PL):
        ln = {'ICH': 'India/China',
              'SEA': 'SE Asia',
              'NIN': 'North India',
              'SIN': 'South India',
              'ECH': 'East China'}
        name = entity
        dataname = name + "_volume_mixing_ratio"
        long_name = entity + " Mixing Ratio"
        if CLAMS_CONFIG[entity]["units"] == '%':
            long_name = ln[entity] + " Origin Tracer"
        title = long_name + " (" + CLAMS_CONFIG[entity]["units"] + ")"

        required_datafields = [
            ("pl", name + "_volume_mixing_ratio"),
            ("pl", "ertel_potential_vorticity"), ]

    return fnord


for ent in [u'CH4', u'CO', u'F11', u'F12', u'H2O', u'N2O',
            u'O3', u'SEA', u'ECH', u'NIN', u'SIN', u'ICH']:
    globals()["HS_ChemStyle_PL_" + ent] = make_clams_chem_class(ent)

"""
Gravity Wave Forecast
"""


class HS_GravityWaveForecast_ML(MPLBasemapHorizontalSectionStyle):
    """Pressure level version for Chemical Mixing ratios.
    """
    name = "GW T residual"

    title = "Gravity Wave Temperature Residual"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("ml", "gravity_wave_temperature_perturbation"),
        ("sfc", "tropopause_altitude"),
    ]
    styles = [
        ("default", "fixed colour scale"),
        #        ("auto", "auto colour scale"), ]
    ]

    def _plot_style(self):
        """
        """
        bm = self.bm
        ax = self.bm.ax
        data = self.data

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        show_data = np.ma.masked_invalid(data["gravity_wave_temperature_perturbation"])

        cmap = plt.cm.Spectral_r
        tc = bm.contourf(lonmesh, latmesh, show_data, [-3, -2.5, -2, -1.5, -1, -0.5, 0.5, 1, 1.5, 2, 2.5, 3], cmap=cmap)
        tr = bm.contour(lonmesh, latmesh, data["tropopause_altitude"], [8, 10, 12, 14, 16],
                        colors="grey", linewidths=2, zorder=100)
        ax.clabel(tr, fmt="%d")

        if not self.noframe:
            self.fig.colorbar(tc, fraction=0.05, pad=0.08, shrink=0.7, label="gw")
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax,
                width="3%",  # width = % of parent_bbox width
                height="30%",  # height : %
            )
            self.fig.colorbar(tc, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")
            for x in axins1.yaxis.majorTicks:
                x.label1.set_backgroundcolor("w")


class HS_TemperatureStyle_PL_01(MPLBasemapHorizontalSectionStyle):
    """Pressure level version of the temperature style.
    """
    name = "PLTemp01"
    title = "Temperature (degC) and Geopotential Height (m)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("pl", "air_temperature"),
        ("pl", "geopotential_height")]

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
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="3%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
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
        gpm = self.data["geopotential_height"] / 9.81
        geop_contours = np.arange(400, 28000, 40)
        cs = bm.contour(lonmesh, latmesh, gpm,
                        geop_contours, colors="black", linewidths=1)
        ax.clabel(cs, geop_contours[::2], fontsize=10, fmt='%i')

        titlestring = "Temperature (degC) and Geopotential Height (m) at " \
                      "%i hPa" % self.level
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) / 3600
        titlestring = titlestring + '\nValid: %s (step %i hrs from %s)' % \
                                    (self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                                     time_step_hrs,
                                     self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


"""
Upper Air Field: Geopotential and Wind
"""


class HS_GeopotentialWindStyle_PL(MPLBasemapHorizontalSectionStyle):
    """
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
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="3%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(cs, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        # Convert wind data from m/s to knots for the wind barbs.
        u = u * 1.944
        v = v * 1.944

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
        gpm = self.data["geopotential_height"] / 9.81
        gpm_interval = 40 if self.level <= 500 else 20
        geop_contours = np.arange(400, 28000, gpm_interval)
        cs = bm.contour(lonmesh, latmesh, gpm,
                        geop_contours, colors="green", linewidths=2)
        ax.clabel(cs, geop_contours[::2], fontsize=14, fmt='%i')

        # Plot title.
        titlestring = "Geopotential Height (m) and Horizontal Wind (m/s) " \
                      "at %i hPa" % self.level
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) / 3600
        titlestring = titlestring + '\nValid: %s (step %i hrs from %s)' % \
                                    (self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                                     time_step_hrs,
                                     self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


"""
Upper Air Field: Relative Humidity
"""


class HS_RelativeHumidityStyle_PL_01(MPLBasemapHorizontalSectionStyle):
    """Relative humidity and geopotential on pressure levels.
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
        self.data["relative_humidity"] = \
            thermolib.rel_hum(self.level * 100.,
                              self.data["air_temperature"],
                              self.data["specific_humidity"])

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
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="3%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
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
        gpm = self.data["geopotential_height"] / 9.81
        gpm_interval = 40 if self.level <= 500 else 20
        geop_contours = np.arange(400, 28000, gpm_interval)
        cs = bm.contour(lonmesh, latmesh, gpm,
                        geop_contours, colors="darkred", linewidths=2)
        ax.clabel(cs, geop_contours[::2], fontsize=10, fmt='%i')

        titlestring = "Relative Humditiy (%%) and Geopotential Height (m) at " \
                      "%i hPa" % self.level
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) / 3600
        titlestring = titlestring + '\nValid: %s (step %i hrs from %s)' % \
                                    (self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                                     time_step_hrs,
                                     self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


"""
Upper Air Field: Equivalent Potential Temperature
"""


class HS_EQPTStyle_PL_01(MPLBasemapHorizontalSectionStyle):
    """Equivalent potential temperature and geopotential on pressure levels.
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
        self.data["equivalent_potential_temperature"] = \
            thermolib.eqpt_approx(self.level * 100.,
                                  self.data["air_temperature"],
                                  self.data["specific_humidity"])

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
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="3%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
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
        gpm = self.data["geopotential_height"] / 9.81
        gpm_interval = 40 if self.level <= 500 else 20
        geop_contours = np.arange(400, 28000, gpm_interval)
        cs = bm.contour(lonmesh, latmesh, gpm,
                        geop_contours, colors="white", linewidths=2)
        ax.clabel(cs, geop_contours[::2], fontsize=10, fmt='%i')

        titlestring = "Equivalent Potential Temperature (degC) and Geopotential Height (m) at " \
                      "%i hPa" % self.level
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) / 3600
        titlestring = titlestring + '\nValid: %s (step %i hrs from %s)' % \
                                    (self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                                     time_step_hrs,
                                     self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


"""
Upper Air Field: Vertical Velocity
"""


class HS_WStyle_PL_01(MPLBasemapHorizontalSectionStyle):
    """Vertical velocity and geopotential on pressure levels.
    """
    name = "PLW01"
    title = "Vertical Velocity (cm/s) and Geopotential Height (m)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("pl", "omega"),
        ("pl", "air_temperature"),
        ("pl", "geopotential_height")]

    def _prepare_datafields(self):
        """Computes relative humidity from p, t, q.
        """
        self.data["upward_wind"] = \
            thermolib.omega_to_w(self.data["omega"],
                                 self.level * 100.,
                                 self.data["air_temperature"])

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
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="3%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
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
        gpm = self.data["geopotential_height"] / 9.81
        gpm_interval = 40 if self.level <= 500 else 20
        geop_contours = np.arange(400, 28000, gpm_interval)
        cs = bm.contour(lonmesh, latmesh, gpm,
                        geop_contours, colors="darkgreen", linewidths=2)
        ax.clabel(cs, geop_contours[::2], fontsize=10, fmt='%i')

        titlestring = "Vertical Velocity (cm/s) and Geopotential Height (m) at " \
                      "%i hPa" % self.level
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) / 3600
        titlestring = titlestring + '\nValid: %s (step %i hrs from %s)' % \
                                    (self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                                     time_step_hrs,
                                     self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


"""
Upper Air Field: Divergence
"""


class HS_DivStyle_PL_01(MPLBasemapHorizontalSectionStyle):
    """Divergence and geopotential on pressure levels.
    """
    name = "PLDiv01"
    title = "Divergence and Geopotential Height (m)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("pl", "divergence_of_wind"),
        ("pl", "geopotential_height")]

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
        gpm = self.data["geopotential_height"] / 9.81
        gpm_interval = 40 if self.level <= 500 else 20
        geop_contours = np.arange(400, 28000, gpm_interval)
        cs = bm.contour(lonmesh, latmesh, gpm,
                        geop_contours, colors="darkgreen", linewidths=2)
        ax.clabel(cs, geop_contours[::2], fontsize=10, fmt='%i')

        titlestring = "Divergence (positive: red, negative: blue) and Geopotential Height (m) at " \
                      "%i hPa" % self.level
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) / 3600
        titlestring = titlestring + '\nValid: %s (step %i hrs from %s)' % \
                                    (self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                                     time_step_hrs,
                                     self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


"""
Upper Air Field: EMAC Tracer
"""


class HS_EMAC_TracerStyle_ML_01(MPLBasemapHorizontalSectionStyle):
    """
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
        lonmesh_ = lonmesh_ - (self.lons[1] - self.lons[0]) / 2.
        latmesh_ = latmesh_ - (self.lats[1] - self.lats[0]) / 2.
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
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="3%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(tc, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        titlestring = "EMAC Eyjafjallajokull Tracer (relative) at model level %i" % self.level
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) / 3600
        titlestring = titlestring + '\nValid: %s (step %i hrs from %s)' % \
                                    (self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                                     time_step_hrs,
                                     self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


"""
2D field: EMAC total column density
"""


class HS_EMAC_TracerStyle_SFC_01(MPLBasemapHorizontalSectionStyle):
    """
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
        lonmesh_ = lonmesh_ - (self.lons[1] - self.lons[0]) / 2.
        latmesh_ = latmesh_ - (self.lats[1] - self.lats[0]) / 2.
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
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="3%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(tc, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        titlestring = "EMAC Eyjafjallajokull Tracer Total Column Density (kg/m^2)"
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) / 3600
        titlestring = titlestring + '\nValid: %s (step %i hrs from %s)' % \
                                    (self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                                     time_step_hrs,
                                     self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


"""
Dynamical (2PVU) Tropopause Fields
"""


class HS_PVTropoStyle_PV_01(MPLBasemapHorizontalSectionStyle):
    """Dynamical tropopause plots (2-PVU level). Three styles are available:
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
            vardata = data["air_pressure"] / 100.
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
            vardata = data["geopotential_height"] / 9.81
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
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="3%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(contours, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        # Colors in python2.6/site-packages/matplotlib/colors.py
        cs = bm.contour(lonmesh, latmesh, vardata,
                        thin_contours, colors="yellow",
                        linewidths=0.5, linestyles="solid")
        ax.clabel(cs, thin_contours[::2], colors="red", fontsize=11, fmt='%i')

        if self.style == "PRES":
            titlestring = "Dynamical Tropopause Pressure (hPa) at " \
                          "%i PVU" % (int(self.level) / 1000)
        elif self.style == "PT":
            titlestring = "Dynamical Tropopause Potential Temperature (K) at " \
                          "%i PVU" % (int(self.level) / 1000)
        elif self.style == "GEOP":
            titlestring = "Dynamical Tropopause Geopotential Height (m) at " \
                          "%i PVU" % (int(self.level) / 1000)
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) / 3600
        titlestring = titlestring + '\nValid: %s (step %i hrs from %s)' % \
                                    (self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                                     time_step_hrs,
                                     self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


"""
Surface Field: Probability of WCB
"""


class HS_VIProbWCB_Style_01(MPLBasemapHorizontalSectionStyle):
    """Total column probability of WCB trajectory occurence, derived from
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
            cbar = self.fig.colorbar(contours, fraction=0.05, pad=0.08, shrink=0.7)
            cbar.set_label(label)
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="3%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(contours, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        titlestring = "Mean sea level pressure (hPa) and total column probability of WCB (0-1)"
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) / 3600
        titlestring = titlestring + '\nValid: %s (step %i hrs from %s)' % \
                                    (self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                                     time_step_hrs,
                                     self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


"""
Upper level Field: Lagranto WCB/INSITU/MIX trajectories
"""


class HS_LagrantoTrajStyle_PL_01(MPLBasemapHorizontalSectionStyle):
    """Number of Lagranto trajectories per grid box for WCB, MIX, INSITU
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

        thick_contours = [0, 4, 8, 12]
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
            cbar = self.fig.colorbar(contours, fraction=0.05, pad=0.08, shrink=0.7)
            cbar.set_label(label)
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="3%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(contours, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        titlestring = "Cirrus density, insitu red, mix blue, wcb colour (1E-6/km^2/hPa)"
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) / 3600
        titlestring = titlestring + '\nValid: %s (step %i hrs from %s)' % \
                                    (self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                                     time_step_hrs,
                                     self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


"""
Surface Field: Boundary Layer Height
"""


class HS_BLH_MSLP_Style_01(MPLBasemapHorizontalSectionStyle):
    """
    """
    name = "BLH"
    title = "Boundary Layer Height (m)"

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [
        ("sfc", "air_pressure_at_sea_level"),
        ("sfc", "atmosphere_boundary_layer_thickness")]

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
            cbar = self.fig.colorbar(contours, fraction=0.05, pad=0.08, shrink=0.7)
            cbar.set_label(label)
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="3%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
            cbar = self.fig.colorbar(contours, cax=axins1, orientation="vertical")
            axins1.yaxis.set_ticks_position("left")

        # Labelled thin grey contours of BLH, interval 500m.
        cs = bm.contour(lonmesh, latmesh, blh,
                        np.arange(0, 3000, 500), colors="grey", linewidths=0.5)
        ax.clabel(cs, fontsize=12, fmt='%i')

        # Title
        titlestring = "Boundary layer height (m) and mean sea level pressure (hPa)"
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) / 3600
        titlestring = titlestring + '\nValid: %s (step %i hrs from %s)' % \
                                    (self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'),
                                     time_step_hrs,
                                     self.init_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))


"""
Meteosat brightness temperature
"""


class HS_Meteosat_BT108_01(MPLBasemapHorizontalSectionStyle):
    """
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
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(ax,
                                                                      width="3%",  # width = % of parent_bbox width
                                                                      height="30%",  # height : %
                                                                      loc=4)  # 4 = lr, 3 = ll, 2 = ul, 1 = ur
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
        titlestring = titlestring + '\nValid: %s' % \
                                    (self.valid_time.strftime('%a %Y-%m-%d %H:%M UTC'))

        if not self.noframe:
            ax.set_title(titlestring,
                         horizontalalignment='left', x=0, fontsize=14)
        else:
            ax.text(bm.llcrnrx, bm.llcrnry, titlestring,
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.6))
