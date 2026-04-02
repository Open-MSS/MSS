# -*- coding: utf-8 -*-
"""

    mslib.msui.viewplotter
    ~~~~~~~~~~~~~~~~~~~~~~~

    Definitions of Matplotlib widgets for Qt Designer.

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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

# Parts of the code have been adapted from Chapter 6 of Sandro Tosi,
# 'Matplotlib for Python Developers'.


import logging
from datetime import datetime

import numpy as np
from matplotlib import figure
from matplotlib.lines import Line2D
from metpy.units import units
from mslib.msui import mpl_map
from mslib.utils import thermolib
from mslib.utils.config import config_loader, load_settings_qsettings, save_settings_qsettings
from mslib.utils.loggerdef import configure_mpl_logger


PIL_IMAGE_ORIGIN = "upper"
LAST_SAVE_DIRECTORY = config_loader(dataset="data_dir")

_DEFAULT_SETTINGS_TOPVIEW = {
    "draw_graticule": True,
    "draw_coastlines": True,
    "fill_waterbodies": True,
    "fill_continents": True,
    "draw_flighttrack": True,
    "draw_marker": True,
    "label_flighttrack": True,
    "tov_plot_title_size": "default",
    "tov_axes_label_size": "default",
    "colour_water": ((153 / 255.), (255 / 255.), (255 / 255.), (255 / 255.)),
    "colour_land": ((204 / 255.), (153 / 255.), (102 / 255.), (255 / 255.)),
    "colour_ft_vertices": (0, 0, 1, 1),
    "colour_ft_waypoints": (1, 0, 0, 1)}

_DEFAULT_SETTINGS_SIDEVIEW = {
    "vertical_extent": (1050, 180),
    "vertical_axis": "pressure",
    "secondary_axis": "no secondary axis",
    "plot_title_size": "default",
    "axes_label_size": "default",
    "flightlevels": [300],
    "draw_flightlevels": True,
    "draw_flighttrack": True,
    "fill_flighttrack": True,
    "label_flighttrack": True,
    "draw_verticals": True,
    "draw_marker": True,
    "draw_ceiling": True,
    "colour_ft_vertices": (0, 0, 1, 1),
    "colour_ft_waypoints": (1, 0, 0, 1),
    "colour_ft_fill": (0, 0, 1, 0.15),
    "colour_ceiling": (0, 0, 1, 0.15)}

_DEFAULT_SETTINGS_LINEARVIEW = {
    "plot_title_size": "default",
    "axes_label_size": "default"}
mpl_logger = configure_mpl_logger()


class ViewPlotter:
    def __init__(self, fig=None, ax=None, settings_tag=None, settings=None, layout=None):
        # setup Matplotlib Figure and Axis
        self.fig, self.ax = fig, ax
        self.settings = settings
        self.settings_tag = settings_tag
        if self.fig is None:
            assert ax is None
            if layout is not None:
                self.fig = figure.Figure(facecolor="w", figsize=(layout[0] / 100, layout[1] / 100))  # 0.75
            else:
                self.fig = figure.Figure(facecolor="w")
        if self.ax is None:
            self.ax = self.fig.add_subplot(111, zorder=99)

    def draw_metadata(self, title="", init_time=None, valid_time=None,
                      level=None, style=None):

        if style:
            title += f" ({style})"
        if level:
            title += f" at {level}"
        if isinstance(valid_time, datetime) and isinstance(init_time, datetime):
            time_step = valid_time - init_time
        else:
            time_step = None
        if isinstance(valid_time, datetime):
            valid_time = valid_time.strftime('%a %Y-%m-%d %H:%M UTC')
        if isinstance(init_time, datetime):
            init_time = init_time.strftime('%a %Y-%m-%d %H:%M UTC')

        # Add valid time / init time information to the title.
        if valid_time:
            if init_time:
                if time_step is not None:
                    title += f"\nValid: {valid_time} (step {((time_step.days * 86400 + time_step.seconds) // 3600):d}" \
                             f" hrs from {init_time})"
                else:
                    title += f"\nValid: {valid_time} (initialisation: {init_time})"
            else:
                title += f"\nValid: {valid_time}"

        # Set title.
        self.ax.set_title(title, horizontalalignment='left', x=0)

    def get_plot_size_in_px(self):
        """Determines the size of the current figure in pixels.
        Returns the tuple width, height.
        """
        # (bounds = left, bottom, width, height)
        ax_bounds = self.ax.bbox.bounds
        width = int(round(ax_bounds[2]))
        height = int(round(ax_bounds[3]))
        return width, height

    def get_settings(self):
        """Retrieve dictionary of plotting settings.

        Returns:
            dict: dictionary of settings.
        """
        return self.settings

    def set_settings(self, settings, save=False):
        """Update local settings influencing the plotting

        Args:
            settings (dict): Dictionary of string/value pairs
        """
        if settings is not None:
            self.settings.update(settings)
        if save:
            self.save_settings()

    def load_settings(self):
        self.settings = load_settings_qsettings(self.settings_tag, self.settings)

    def save_settings(self):
        save_settings_qsettings(self.settings_tag, self.settings)


class TopViewPlotter(ViewPlotter):
    def __init__(self, fig=None, ax=None, settings=None):
        super().__init__(fig, ax, settings_tag="topview", settings=_DEFAULT_SETTINGS_TOPVIEW,
                         layout=config_loader(dataset="layout")["topview"])
        self.map = None
        self.legimg = None
        self.legax = None
        # stores the  topview plot title size(tov_pts) and topview axes label size(tov_als),initially as None.
        self.tov_pts = None
        self.tov_als = None
        # Sets the default fontsize parameters' values for topview from MSSDefaultConfig.
        self.topview_size_settings = config_loader(dataset="topview")
        self.load_settings()
        self.set_settings(settings)
        self.ax.figure.canvas.draw()

    def init_map(self, **kwargs):
        self.map = mpl_map.MapCanvas(appearance=self.get_settings(),
                                     resolution="l", area_thresh=1000., ax=self.ax,
                                     **kwargs)

        # Sets the selected fontsize only if draw_graticule box from topview options is checked in.
        if self.settings["draw_graticule"]:
            try:
                self.map._draw_auto_graticule(self.tov_als)
            except Exception as ex:
                logging.error("ERROR: cannot plot graticule (message: %s - '%s')", type(ex), ex)
        else:
            self.map.set_graticule_visible(False)
        self.ax.set_autoscale_on(False)
        self.ax.set_title("Top view", fontsize=self.tov_pts, horizontalalignment="left", x=0)

    def getBBOX(self, bbox_units=None):
        axis = self.ax.axis()
        if bbox_units is not None:
            self.map.bbox_units = bbox_units
        if self.map.bbox_units == "degree":
            # Convert the current axis corners to lat/lon coordinates.
            axis0, axis2 = self.map(axis[0], axis[2], inverse=True)
            axis1, axis3 = self.map(axis[1], axis[3], inverse=True)
            bbox = (axis0, axis2, axis1, axis3)

        elif self.map.bbox_units.startswith("meter"):
            center_x, center_y = self.map(
                *(float(_x) for _x in self.map.bbox_units[6:-1].split(",")))
            bbox = (axis[0] - center_x, axis[2] - center_y, axis[1] - center_x, axis[3] - center_y)

        else:
            bbox = axis[0], axis[2], axis[1], axis[3]

        return bbox

    def clear_figure(self):
        logging.debug("Removing image")
        if self.map.image is not None:
            self.map.image.remove()
            self.map.image = None
            self.ax.set_title("Top view", horizontalalignment="left", x=0)
            self.ax.figure.canvas.draw()

    def set_settings(self, settings, save=False):
        """Apply settings from dictionary 'settings' to the view.
        If settings is None, apply default settings.
        """
        super().set_settings(settings, save)

        # Stores the exact value of fontsize for topview plot title size(tov_pts)
        self.tov_pts = (self.topview_size_settings["plot_title_size"]
                        if self.settings["tov_plot_title_size"] == "default"
                        else int(self.settings["tov_plot_title_size"]))
        # Stores the exact value of fontsize for topview axes label size(tov_als)
        self.tov_als = (self.topview_size_settings["axes_label_size"]
                        if self.settings["tov_axes_label_size"] == "default"
                        else int(self.settings["tov_axes_label_size"]))

        ax = self.ax

        if self.map is not None:
            self.map.set_coastlines_visible(self.settings["draw_coastlines"])
            self.map.set_fillcontinents_visible(visible=self.settings["fill_continents"],
                                                land_color=self.settings["colour_land"],
                                                lake_color=self.settings["colour_water"])
            self.map.set_mapboundary_visible(visible=self.settings["fill_waterbodies"],
                                             bg_color=self.settings["colour_water"])

            # Updates plot title size as selected from combobox labelled plot title size.
            ax.set_autoscale_on(False)
            ax.set_title("Top view", fontsize=self.tov_pts, horizontalalignment="left", x=0)

            # Updates graticule ticklabels/labels fontsize if draw_graticule is True.
            if self.settings["draw_graticule"]:
                self.map.set_graticule_visible(False)
                self.map._draw_auto_graticule(self.tov_als)
            else:
                self.map.set_graticule_visible(self.settings["draw_graticule"])

    def redraw_map(self, kwargs_update=None):
        """Redraw map canvas.
        Executed on clicked() of btMapRedraw.
        See MapCanvas.update_with_coordinate_change(). After the map redraw,
        coordinates of all objects overlain on the map have to be updated.
        """

        # 2) UPDATE MAP.
        self.map.update_with_coordinate_change(kwargs_update)

        # Sets the graticule ticklabels/labels fontsize for topview when map is redrawn.
        if self.settings["draw_graticule"]:
            self.map.set_graticule_visible(False)
            self.map._draw_auto_graticule(self.tov_als)
        else:
            self.map.set_graticule_visible(self.settings["draw_graticule"])
        self.ax.figure.canvas.draw()  # this one is required to trigger a
        # drawevent to update the background

        # self.draw_metadata() ; It is not needed here, since below here already plot title is being set.

        # Setting fontsize for topview plot title when map is redrawn.
        self.ax.set_title("Top view", fontsize=self.tov_pts, horizontalalignment='left', x=0)
        self.ax.figure.canvas.draw()

    def draw_image(self, img):
        """Draw the image img on the current plot.
        """
        logging.debug("plotting image..")
        self.wms_image = self.map.imshow(img, interpolation="nearest", origin=PIL_IMAGE_ORIGIN)
        # NOTE: imshow always draws the images to the lowest z-level of the
        # plot.
        # See these mailing list entries:
        # http://www.mail-archive.com/matplotlib-devel@lists.sourceforge.net/msg05955.html
        # http://old.nabble.com/Re%3A--Matplotlib-users--imshow-zorder-tt19047314.html#a19047314
        #
        # Question: Is this an issue for us or do we always want the images in the back
        # anyhow? At least we need to remove filled continents here.
        # self.map.set_fillcontinents_visible(False)
        # ** UPDATE 2011/01/14 ** seems to work with version 1.0!
        logging.debug("done.")

    def draw_legend(self, img):
        """Draw the legend graphics img on the current plot.
        Adds new axes to the plot that accommodate the legend.
        """
        # If the method is called with a "None" image, the current legend
        # graphic should be removed (if one exists).
        if self.legimg is not None:
            logging.debug("removing image %s", self.legimg)
            self.legimg.remove()
            self.legimg = None

        if img is not None:
            # The size of the legend axes needs to be given in relative figure
            # coordinates. To determine those from the legend graphics size in
            # pixels, we need to determine the size of the currently displayed
            # figure in pixels.
            figsize_px = self.fig.get_size_inches() * self.fig.get_dpi()
            ax_extent_x = float(img.size[0]) / figsize_px[0]
            ax_extent_y = float(img.size[1]) / figsize_px[1]

            # If no legend axes have been created, do so now.
            if self.legax is None:
                # Main axes instance of mplwidget has zorder 99.
                self.legax = self.fig.add_axes([1 - ax_extent_x, 0.01, ax_extent_x, ax_extent_y],
                                               frameon=False,
                                               xticks=[], yticks=[],
                                               label="ax2", zorder=0)
                self.legax.patch.set_facecolor("None")

            # If axes exist, adjust their position.
            else:
                self.legax.set_position([1 - ax_extent_x, 0.01, ax_extent_x, ax_extent_y])
            # Plot the new legimg in the legax axes.
            self.legimg = self.legax.imshow(img, origin=PIL_IMAGE_ORIGIN, aspect="equal", interpolation="nearest")
        self.ax.figure.canvas.draw()

    def draw_flightpath_legend(self, flightpath_dict):
        """
        Draw the flight path legend on the plot, attached to the upper-left corner.
        """
        # Clear any existing legend
        if self.ax.get_legend() is not None:
            self.ax.get_legend().remove()

        if not flightpath_dict:
            self.ax.figure.canvas.draw()
            return

        # Create legend handles
        legend_handles = []
        for name, (color, linestyle) in flightpath_dict.items():
            line = Line2D([0], [0], color=color, linestyle=linestyle, linewidth=2)
            legend_handles.append((line, name))

        # Add legend directly to the main axis, attached to the upper-left corner
        self.ax.legend(
            [handle for handle, _ in legend_handles],
            [name for _, name in legend_handles],
            loc='upper left',
            bbox_to_anchor=(0, 1),  # (x, y) coordinates relative to the figure
            bbox_transform=self.fig.transFigure,  # Use figure coordinates
            frameon=False
        )

        self.ax.figure.canvas.draw_idle()


class SideViewPlotter(ViewPlotter):
    _pres_maj = np.concatenate([np.arange(top * 10, top, -top) for top in (10000, 1000, 100, 10, 1, 0.1)] +
                               [[0.1]])
    _pres_min = np.concatenate([np.arange(top * 10, top, -top // 10) for top in (10000, 1000, 100, 10, 1, 0.1)] +
                               [[0.1]])

    def __init__(self, fig=None, ax=None, settings=None, numlabels=None, num_interpolation_points=None):
        """
        Arguments:
        model -- WaypointsTableModel defining the vertical section.
        """
        if numlabels is None:
            numlabels = config_loader(dataset='num_labels')
        if num_interpolation_points is None:
            num_interpolation_points = config_loader(dataset='num_interpolation_points')
        super().__init__(fig, ax, settings_tag="sideview", settings=_DEFAULT_SETTINGS_SIDEVIEW,
                         layout=config_loader(dataset="layout")["sideview"])
        self.load_settings()
        self.set_settings(settings)

        self.numlabels = numlabels
        self.num_interpolation_points = num_interpolation_points
        self.ax2 = self.ax.twinx()
        self.ax.patch.set_facecolor("None")
        self.ax2.patch.set_facecolor("None")
        # Main axes instance of mplwidget has zorder 99.
        self.imgax = self.fig.add_axes(
            self.ax.get_position(), frameon=True, xticks=[], yticks=[], label="imgax", zorder=0)
        self.vertical_lines = []

        # Sets the default value of sideview fontsize settings from MSSDefaultConfig.
        self.sideview_size_settings = config_loader(dataset="sideview")
        # Draw a number of flight level lines.
        self.flightlevels = []
        self.fl_label_list = []
        self.image = None
        self.update_vertical_extent_from_settings(init=True)

    def _determine_ticks_labels(self, typ):
        if typ == "no secondary axis":
            major_ticks = [] * units.pascal
            minor_ticks = [] * units.pascal
            labels = []
            ylabel = ""
        elif typ == "pressure":
            # Compute the position of major and minor ticks. Major ticks are labelled.
            major_ticks = self._pres_maj[(self._pres_maj <= self.p_bot) & (self._pres_maj >= self.p_top)]
            minor_ticks = self._pres_min[(self._pres_min <= self.p_bot) & (self._pres_min >= self.p_top)]
            labels = [f"{_x / 100:.0f}" if _x / 100 >= 1 else (
                      f"{_x / 100:.1f}" if _x / 100 >= 0.1 else (
                          f"{_x / 100:.2f}" if _x / 100 >= 0.01 else (
                              f"{_x / 100:.3f}"))) for _x in major_ticks]
            if len(labels) > 40:
                labels = ["" if any(y in x for y in "9865") else x for x in labels]
            elif len(labels) > 20:
                labels = ["" if any(y in x for y in "975") else x for x in labels]
            elif len(labels) > 10:
                labels = ["" if "9" in x else x for x in labels]
            ylabel = "pressure (hPa)"
        elif typ == "pressure altitude":
            bot_km = thermolib.pressure2flightlevel(self.p_bot * units.Pa).to(units.km).magnitude
            top_km = thermolib.pressure2flightlevel(self.p_top * units.Pa).to(units.km).magnitude
            ma_dist, mi_dist = 5, 1.0
            if (top_km - bot_km) <= 20:
                ma_dist, mi_dist = 1, 0.5
            elif (top_km - bot_km) <= 40:
                ma_dist, mi_dist = 2, 0.5
            elif (top_km - bot_km) <= 60:
                ma_dist, mi_dist = 4, 1.0
            major_heights = np.arange(0, top_km + 0.1, ma_dist)
            minor_heights = np.arange(0, top_km + 0.1, mi_dist)
            major_ticks = thermolib.flightlevel2pressure(major_heights * units.km).magnitude
            minor_ticks = thermolib.flightlevel2pressure(minor_heights * units.km).magnitude
            labels = major_heights
            ylabel = "pressure altitude (km)"
        elif typ == "flight level":
            bot_km = thermolib.pressure2flightlevel(self.p_bot * units.Pa).to(units.km).magnitude
            top_km = thermolib.pressure2flightlevel(self.p_top * units.Pa).to(units.km).magnitude
            ma_dist, mi_dist = 100, 20
            if (top_km - bot_km) <= 10:
                ma_dist, mi_dist = 20, 10
            elif (top_km - bot_km) <= 40:
                ma_dist, mi_dist = 40, 10
            elif (top_km - bot_km) <= 60:
                ma_dist, mi_dist = 50, 10
            major_fl = np.arange(0, 3248, ma_dist)
            minor_fl = np.arange(0, 3248, mi_dist)
            major_ticks = thermolib.flightlevel2pressure(major_fl * units.hft).magnitude
            minor_ticks = thermolib.flightlevel2pressure(minor_fl * units.hft).magnitude
            labels = major_fl
            ylabel = "flight level (hft)"
        else:
            raise RuntimeError(f"Unsupported vertical axis type: '{typ}'")
        return ylabel, major_ticks, minor_ticks, labels

    def setup_side_view(self):
        """Set up a vertical section view.

        Vertical cross section code (log-p axis etc.) taken from
        mss_batch_production/visualisation/mpl_vsec.py.
        """

        self.ax.set_title("vertical flight profile", horizontalalignment="left", x=0)
        self.ax.grid(visible=True)

        self.ax.set_xlabel("lat/lon")

        for ax in (self.ax, self.ax2):
            ax.set_yscale("log")
            ax.set_ylim(self.p_bot, self.p_top)

        self.redraw_yaxis()

    def redraw_yaxis(self):
        """ Redraws the y-axis on map after setting the values from sideview options dialog box
        and also updates the sizes for map title and x and y axes labels and ticklabels"""

        vaxis = self.settings["vertical_axis"]
        vaxis2 = self.settings["secondary_axis"]

        # Sets fontsize value for x axis ticklabel.
        axes_label_size = (self.sideview_size_settings["axes_label_size"]
                           if self.settings["axes_label_size"] == "default"
                           else int(self.settings["axes_label_size"]))
        # Sets fontsize value for plot title and axes title/label
        plot_title_size = (self.sideview_size_settings["plot_title_size"]
                           if self.settings["plot_title_size"] == "default"
                           else int(self.settings["plot_title_size"]))
        # Updates the fontsize of the x-axis ticklabels of sideview.
        self.ax.tick_params(axis='x', labelsize=axes_label_size)
        # Updates the fontsize of plot title and x-axis title of sideview.
        self.ax.set_title("vertical flight profile", fontsize=plot_title_size, horizontalalignment="left", x=0)
        self.ax.set_xlabel("lat/lon", fontsize=plot_title_size)

        for ax, typ in zip((self.ax, self.ax2), (vaxis, vaxis2)):
            ylabel, major_ticks, minor_ticks, labels = self._determine_ticks_labels(typ)

            major_ticks_units = getattr(major_ticks, "units", None)
            if ax.yaxis.units is None and major_ticks_units is not None:
                ax.yaxis.set_units(major_ticks_units)

            ax.set_ylabel(ylabel, fontsize=plot_title_size)
            ax.set_yticks(minor_ticks, minor=True)
            ax.set_yticks(major_ticks, minor=False)
            ax.set_yticklabels([], minor=True)
            ax.set_yticklabels(labels, minor=False, fontsize=axes_label_size)
            ax.set_ylim(self.p_bot, self.p_top)

        if vaxis2 == "no secondary axis":
            self.fig.subplots_adjust(left=0.08, right=0.96, top=0.9, bottom=0.14)
            self.imgax.set_position(self.ax.get_position())
        else:
            self.fig.subplots_adjust(left=0.08, right=0.92, top=0.9, bottom=0.14)
            self.imgax.set_position(self.ax.get_position())

    def redraw_xaxis(self, lats, lons, times, times_visible):
        """Redraw the x-axis of the side view on path changes. Also remove
           a vertical section image if one exists, as it is invalid after
           a path change.
        """
        logging.debug("redrawing x-axis")

        # Re-label x-axis.
        self.ax.set_xlim(0, len(lats) - 1)
        # Set xticks so that they display lat/lon. Plot "numlabels" labels.
        lat_inds = np.arange(len(lats))
        tick_index_step = len(lat_inds) // self.numlabels
        self.ax.set_xticks(lat_inds[::tick_index_step])

        if times_visible:
            self.ax.set_xticklabels([f'{d[0]:2.1f}, {d[1]:2.1f}\n{d[2].strftime("%H:%M")}Z'
                                     for d in zip(lats[::tick_index_step],
                                                  lons[::tick_index_step],
                                                  times[::tick_index_step])],
                                    rotation=25, horizontalalignment="right")
        else:
            self.ax.set_xticklabels([f"{d[0]:2.1f}, {d[1]:2.1f}"
                                     for d in zip(lats[::tick_index_step],
                                                  lons[::tick_index_step])],
                                    rotation=25, horizontalalignment="right")

        self.ax.figure.canvas.draw()

    def draw_vertical_lines(self, highlight, lats, lons):
        # Remove all vertical lines
        for line in self.vertical_lines:
            try:
                line.remove()
            except ValueError as e:
                logging.debug("Vertical line was somehow already removed:\n%s", e)
        self.vertical_lines = []

        # Add vertical lines
        if self.settings["draw_verticals"]:
            ipoint = 0
            for i, (lat, lon) in enumerate(zip(lats, lons)):
                if (ipoint < len(highlight) and
                        np.hypot(lat - highlight[ipoint][0],
                                 lon - highlight[ipoint][1]) < 2E-10):
                    self.vertical_lines.append(
                        self.ax.axvline(i, color='k', linewidth=2, linestyle='--', alpha=0.5))
                    ipoint += 1
        self.fig.canvas.draw()

    def getBBOX(self):
        """Get the bounding box of the view (returns a 4-tuple
           x1, y1(p_bot[hPa]), x2, y2(p_top[hPa])).
        """
        # Get the bounding box of the current view
        # (bbox = llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat; i.e. for the side
        #  view bbox = x1, y1(p_bot), x2, y2(p_top)).
        axis = self.ax.axis()

        num_interpolation_points = self.num_interpolation_points
        num_labels = self.numlabels

        # Return a tuple (num_interpolation_points, p_bot[hPa],
        #                 num_labels, p_top[hPa]) as BBOX.
        bbox = (num_interpolation_points, (axis[2] / 100),
                num_labels, (axis[3] / 100))
        return bbox

    def clear_figure(self):
        logging.debug("path of side view has changed.. removing invalidated "
                      "image (if existent) and redrawing.")
        if self.image is not None:
            self.image.remove()
            self.image = None
            self.ax.set_title("vertical flight profile", horizontalalignment="left", x=0)
            self.ax.figure.canvas.draw()

    def draw_image(self, img):
        """Draw the image img on the current plot.

        NOTE: The image is plotted in a separate axes object that is located
        below the axes that display the flight profile. This is necessary
        because imshow() does not work with logarithmic axes.
        """
        logging.debug("plotting vertical section image..")
        ix, iy = img.size
        logging.debug("  image size is %dx%d px, format is '%s'", ix, iy, img.format)

        # If an image is currently displayed, remove it from the plot.
        if self.image is not None:
            self.image.remove()

        # Plot the new image in the image axes and adjust the axes limits.
        self.image = self.imgax.imshow(
            img, interpolation="nearest", aspect="auto", origin=PIL_IMAGE_ORIGIN)
        self.imgax.set_xlim(0, ix - 1)
        self.imgax.set_ylim(iy - 1, 0)
        self.ax.figure.canvas.draw()
        logging.debug("done.")

    def update_vertical_extent_from_settings(self, init=False):
        """ Checks for current units of axis and convert the upper and lower limit
        to pa(pascals) for the internal computation by code """

        if not init:
            p_bot_old = self.p_bot
            p_top_old = self.p_top

        if self.settings["vertical_axis"] == "pressure altitude":
            self.p_bot = thermolib.flightlevel2pressure(self.settings["vertical_extent"][0] * units.km).magnitude
            self.p_top = thermolib.flightlevel2pressure(self.settings["vertical_extent"][1] * units.km).magnitude
        elif self.settings["vertical_axis"] == "flight level":
            self.p_bot = thermolib.flightlevel2pressure(self.settings["vertical_extent"][0] * units.hft).magnitude
            self.p_top = thermolib.flightlevel2pressure(self.settings["vertical_extent"][1] * units.hft).magnitude
        else:
            self.p_bot = self.settings["vertical_extent"][0] * 100
            self.p_top = self.settings["vertical_extent"][1] * 100

        if not init:
            if (p_bot_old != self.p_bot) or (p_top_old != self.p_top):
                if self.image is not None:
                    self.image.remove()
                    self.image = None
                self.setup_side_view()
            else:
                self.redraw_yaxis()


class LinearViewPlotter(ViewPlotter):
    """Specialised MplCanvas that draws a linear view of a
       flight track / list of waypoints.
    """

    def __init__(self, model=None, numlabels=None, settings=None):
        """
        Arguments:
        model -- WaypointsTableModel defining the linear section.
        """
        if numlabels is None:
            numlabels = config_loader(dataset='num_labels')
        super().__init__(settings_tag="linearview", settings=_DEFAULT_SETTINGS_LINEARVIEW,
                         layout=config_loader(dataset="layout")["linearview"])
        self.load_settings()

        # Sets the default values of plot sizes from MissionSupportDefaultConfig.
        self.linearview_size_settings = config_loader(dataset="linearview")
        self.set_settings(settings)

        # Setup the plot.
        self.numlabels = numlabels
        self.setup_linear_view()
        # If a waypoints model has been passed, create an interactor on it.
        self.waypoints_interactor = None
        self.waypoints_model = None
        self.vertical_lines = []
        self.basename = "linearview"

    def setup_linear_view(self):
        """Set up a linear section view.
        """
        self.fig.subplots_adjust(left=0.08, right=0.96, top=0.9, bottom=0.14)

    def clear_figure(self):
        logging.debug("path of linear view has changed.. removing invalidated plots")
        self.fig.clf()
        self.ax = self.fig.add_subplot(111, zorder=99)
        self.ax.figure.patch.set_visible(False)
        self.vertical_lines = []
        self.fig.canvas.draw()

    def redraw_xaxis(self, lats, lons):
        # Re-label x-axis.
        self.ax.set_xlim(0, len(lats) - 1)
        # Set xticks so that they display lat/lon. Plot "numlabels" labels.
        lat_inds = np.arange(len(lats))
        tick_index_step = len(lat_inds) // self.numlabels
        self.ax.set_xticks(lat_inds[::tick_index_step])
        self.ax.set_xticklabels([f'{d[0]:2.1f}, {d[1]:2.1f}'
                                 for d in zip(lats[::tick_index_step],
                                              lons[::tick_index_step])],
                                rotation=25, horizontalalignment="right")

        # Remove all vertical lines
        for line in self.vertical_lines:
            try:
                line.remove()
            except ValueError as e:
                logging.debug("Vertical line was somehow already removed:\n%s", e)
        self.vertical_lines = []

    def draw_vertical_lines(self, highlight, lats, lons):
        # draw vertical lines
        self.vertical_lines = []
        ipoint = 0
        for i, (lat, lon) in enumerate(zip(lats, lons)):
            if (ipoint < len(highlight) and np.hypot(lat - highlight[ipoint][0],
               lon - highlight[ipoint][1]) < 2E-10):
                self.vertical_lines.append(self.ax.axvline(i, color='k', linewidth=2, linestyle='--', alpha=0.5))
                ipoint += 1
        self.fig.tight_layout()
        self.fig.subplots_adjust(top=0.85, bottom=0.20)
        self.fig.canvas.draw()

    def draw_legend(self, img):
        if img is not None:
            logging.error("Legends not supported in LinearView mode!")
            raise NotImplementedError

    def draw_image(self, xmls, colors=None, scales=None):
        title = self.fig._suptitle.get_text()
        self.clear_figure()
        self.fig.suptitle(title, x=0.95, ha='right')
        offset = 40
        self.ax.patch.set_visible(False)

        for i, xml in enumerate(xmls):
            data = xml.find("Data")
            values = [float(value) for value in data.text.split(",")]
            unit = data.attrib["unit"]
            numpoints = int(data.attrib["num_waypoints"])

            if colors:
                color = colors[i] if len(colors) > i else colors[-1]
            else:
                color = "#00AAFF"

            if scales:
                scale = scales[i] if len(scales) > i else scales[-1]
            else:
                scale = "linear"

            par = self.ax.twinx() if i > 0 else self.ax
            par.set_yscale(scale)

            par.plot(range(numpoints), values, color)
            if i > 0:
                par.spines["right"].set_position(("outward", (i - 1) * offset))
            if unit:
                par.set_ylabel(unit)

            par.yaxis.label.set_color(color.replace("0x", "#"))

    def set_settings(self, settings, save=False):
        """
        Apply settings from options ui to the linear view
        """

        super().set_settings(settings, save)

        pts = (self.linearview_size_settings["plot_title_size"] if self.settings["plot_title_size"] == "default"
               else int(self.settings["plot_title_size"]))
        label_size = (self.linearview_size_settings["axes_label_size"] if self.settings["axes_label_size"] == "default"
                      else int(self.settings["axes_label_size"]))
        self.ax.tick_params(axis='both', labelsize=label_size)
        self.ax.set_title("Linear flight profile", fontsize=pts, horizontalalignment='left', x=0)
        self.ax.figure.canvas.draw()
