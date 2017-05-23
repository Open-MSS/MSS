# -*- coding: utf-8 -*-
"""

    mslib.msui.mpl_qtwidget
    ~~~~~~~~~~~~~~~~~~~~~~~

    Definitions of Matplotlib widgets for Qt4 Designer.

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

# Parts of the code have been adapted from Chapter 6 of Sandro Tosi,
# 'Matplotlib for Python Developers'.

from builtins import zip
from past.builtins import basestring
from past.utils import old_div
from datetime import datetime

import logging
from mslib.utils import config_loader
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default
# related third party imports
import numpy as np
import matplotlib.pyplot as plt

# local application imports
from mslib.msui import mpl_pathinteractor as mpl_pi
from mslib.msui import mpl_map
from mslib.msui import trajectory_item_tree as titree
from mslib import thermolib


# Python Qt4 bindings for GUI objects
from mslib.msui.mss_qt import QtCore, QtWidgets, FigureCanvas, NavigationToolbar

# Matplotlib Figure object
from matplotlib.figure import Figure

# With Matplotlib 1.2, PIL images are rotated differently when plotted with
# imshow(). See Basemap __init__.py file, in which the same issue occurs
# (https://github.com/matplotlib/basemap/pull/52). (mr, 08Feb2013)
from matplotlib import __version__ as _matplotlib_version

if _matplotlib_version >= '1.2':
    # orientation of arrays returned by pil_to_array
    # changed (https://github.com/matplotlib/matplotlib/pull/616)
    PIL_image_origin = "upper"
else:
    PIL_image_origin = "lower"


class MplCanvas(FigureCanvas):
    """Class to represent the FigureCanvas widget.

    Main axes instance has zorder 99 (important when additional
    axes are added).
    """

    def __init__(self):
        # setup Matplotlib Figure and Axis
        self.fig = Figure(facecolor="w")  # 0.75
        self.ax = self.fig.add_subplot(111, zorder=99)
        self.default_filename = "_image"

        # initialization of the canvas
        FigureCanvas.__init__(self, self.fig)

        # we define the widget as expandable
        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)

        # notify the system of updated policy
        FigureCanvas.updateGeometry(self)

    def get_default_filename(self):
        result = self.basename + self.default_filename
        if len(result) > 100:
            result = result[:100]
        return result + ".png"

    def drawMetadata(self, title="", init_time=None, valid_time=None,
                     level=None, style=None):
        """Draw a title indicating the init and valid time of the
           image that has been drawn, and the vertical elevation level.
        """
        self.default_filename = ""
        if title:
            self.default_filename += u"_{:>5}".format(title.split()[0])
        if isinstance(style, basestring) and style:
            title += u' ({})'.format(style)
        if isinstance(level, basestring):
            title += u' at {}'.format(level)
            self.default_filename += u"_{}".format(level.split()[0])
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
                    title += u"\nValid: {} (step {:d} hrs from {})".format(
                        valid_time, old_div((time_step.days * 86400 + time_step.seconds), 3600), init_time)
                else:
                    title += u"\nValid: {} (initialisation: {})".format(valid_time, init_time)
            else:
                title += u"\nValid: {}".format(valid_time)

        # Set title.
        self.ax.set_title(title, horizontalalignment='left', x=0)
        self.draw()
        # without the repaint the title is not properly updated
        self.repaint()

    def getPlotSizePx(self):
        """Determines the size of the current figure in pixels.

        Returns the tuple width, height.
        """
        # (bounds = left, bottom, width, height)
        ax_bounds = self.ax.bbox.bounds
        width = int(round(ax_bounds[2]))
        height = int(round(ax_bounds[3]))
        return width, height


class MplWidget(QtWidgets.QWidget):
    """Matplotlib canvas widget defined in Qt Designer"""

    def __init__(self, parent=None):
        # initialization of Qt MainWindow widget
        QtWidgets.QWidget.__init__(self, parent)

        # set the canvas to the Matplotlib widget
        self.canvas = MplCanvas()

        # create a vertical box layout
        self.vbl = QtWidgets.QVBoxLayout()

        # add mpl widget to vertical box
        self.vbl.addWidget(self.canvas)

        # set the layout to th vertical box
        self.setLayout(self.vbl)


class MplNavBarWidget(QtWidgets.QWidget):
    """Matplotlib canvas widget with navigation toolbar defined in Qt Designer"""

    def __init__(self, parent=None, canvas=None):
        # initialization of Qt MainWindow widget
        QtWidgets.QWidget.__init__(self, parent)

        # set the canvas to the Matplotlib widget
        if canvas:
            self.canvas = canvas
        else:
            self.canvas = MplCanvas()

        # instantiate the navigation toolbar
        self.navbar = NavigationToolbar(self.canvas, self)

        # create a vertical box layout
        self.vbl = QtWidgets.QVBoxLayout()

        # add mpl widget to vertical box
        self.vbl.addWidget(self.navbar)
        self.vbl.addWidget(self.canvas)

        # set the layout to th vertical box
        self.setLayout(self.vbl)


class MplSideViewCanvas(MplCanvas):
    """Specialised MplCanvas that draws a side view (vertical section) of a
       flight track / list of waypoints.
    """

    def __init__(self, model=None, settings=None,
                 numlabels=None):

        """
        Arguments:
        model -- WaypointsTableModel defining the vertical section.
        """
        if numlabels is None:
            numlabels = config_loader(dataset='num_labels', default=mss_default.num_labels)
        super(MplSideViewCanvas, self).__init__()

        # Default settings.
        self.settings_dict = {"vertical_extent": (1050, 180),
                              "flightlevels": [],
                              "draw_flightlevels": True,
                              "draw_flighttrack": True,
                              "fill_flighttrack": True,
                              "label_flighttrack": True,
                              "colour_ft_vertices": (0, 0, 1, 1),
                              "colour_ft_waypoints": (1, 0, 0, 1),
                              "colour_ft_fill": (0, 0, 1, 0.15)}
        if settings is not None:
            self.settings_dict.update(settings)

        # Setup the plot.
        self.p_bot = self.settings_dict["vertical_extent"][0] * 100
        self.p_top = self.settings_dict["vertical_extent"][1] * 100
        self.numlabels = numlabels
        self.setupSideView()
        # Draw a number of flight level lines.
        self.flightlevels = []
        self.fl_label_list = []
        self.drawFlightLevels()
        self.imgax = None
        self.image = None
        # If a waypoints model has been passed, create an interactor on it.
        self.waypoints_interactor = None
        self.basename = "sideview"
        if model:
            self.setWaypointsModel(model)

        self.setSettings(self.settings_dict)

    def setWaypointsModel(self, model):
        """Set the WaypointsTableModel defining the vertical section.
        If no model had been set before, create a new interactor object on the
        model to let the user interactively move the altitude of the waypoints.
        """
        self.waypoints_model = model
        if self.waypoints_interactor:
            self.waypoints_interactor.set_waypoints_model(model)
        else:
            # Create a path interactor object. The interactor object connects
            # itself to the change() signals of the flight track data model.
            self.waypoints_interactor = mpl_pi.VPathInteractor(
                self.ax, self.waypoints_model,
                numintpoints=config_loader(dataset="num_interpolation_points",
                                           default=mss_default.num_interpolation_points),
                redrawXAxis=self.redrawXAxis
            )

    def setupSideView(self):
        """Set up a vertical section view.

        Vertical cross section code (log-p axis etc.) taken from
        mss_batch_production/visualisation/mpl_vsec.py.
        """
        ax = self.ax
        self.fig.subplots_adjust(left=0.08, right=0.96,
                                 top=0.9, bottom=0.14)

        ax.set_title("vertical flight profile", horizontalalignment="left", x=0)
        ax.set_xlim(0, 10)

        p_bot = self.p_bot
        p_top = self.p_top

        ax.set_yscale("log")

        # Compute the position of major and minor ticks. Major ticks are labelled.
        # By default, major ticks are drawn every 100hPa. If p_top < 100hPa,
        # the distance is reduced to every 10hPa above 100hPa.
        label_distance = 10000
        label_bot = p_bot - (p_bot % label_distance)
        major_ticks = np.arange(label_bot, p_top - 1, -label_distance)

        # .. check step reduction to 10 hPa ..
        if p_top < 10000:
            major_ticks2 = np.arange(major_ticks[-1], p_top - 1,
                                     old_div(-label_distance, 10))
            len_major_ticks = len(major_ticks)
            major_ticks = np.resize(major_ticks,
                                    len_major_ticks + len(major_ticks2) - 1)
            major_ticks[len_major_ticks:] = major_ticks2[1:]

        labels = ["{:d}".format(int(old_div(l, 100.))) for l in major_ticks]

        # .. the same for the minor ticks ..
        p_top_minor = max(label_distance, p_top)
        label_distance_minor = 1000
        label_bot_minor = p_bot - (p_bot % label_distance_minor)
        minor_ticks = np.arange(label_bot_minor, p_top_minor - 1,
                                -label_distance_minor)

        if p_top < 10000:
            minor_ticks2 = np.arange(minor_ticks[-1], p_top - 1,
                                     old_div(-label_distance_minor, 10))
            len_minor_ticks = len(minor_ticks)
            minor_ticks = np.resize(minor_ticks,
                                    len_minor_ticks + len(minor_ticks2) - 1)
            minor_ticks[len_minor_ticks:] = minor_ticks2[1:]

        # Draw ticks and tick labels.
        ax.set_yticks(minor_ticks, minor=True)
        ax.set_yticks(major_ticks, minor=False)
        ax.set_yticklabels([], minor=True, fontsize=10)
        ax.set_yticklabels(labels, minor=False, fontsize=10)

        # Set axis limits and draw grid for major ticks.
        ax.set_ylim(p_bot, p_top)
        ax.grid(b=True)

        ax.set_xlabel("lat/lon")
        ax.set_ylabel("pressure (hPa)")

    def redrawXAxis(self, lats, lons):
        """Redraw the x-axis of the side view on path changes. Also remove
           a vertical section image if one exists, as it is invalid after
           a path change.
        """
        logging.debug("path of side view has changed.. removing invalidated "
                      "image (if existent) and redrawing.")

        # Remove image (it is now invalid).
        if self.image is not None:
            self.image.remove()
            self.image = None
            self.ax.set_title("vertical flight profile", horizontalalignment="left", x=0)

        # Re-label x-axis.
        self.ax.set_xlim(0, len(lats) - 1)
        # Set xticks so that they display lat/lon. Plot "numlabels" labels.
        lat_inds = np.arange(len(lats))
        tick_index_step = old_div(len(lat_inds), self.numlabels)
        self.ax.set_xticks(lat_inds[::tick_index_step])
        self.ax.set_xticklabels(["{:2.1f}, {:2.1f}".format(d[0], d[1])
                                 for d in zip(lats[::tick_index_step],
                                              lons[::tick_index_step])],
                                rotation=25, fontsize=10, horizontalalignment="right")

    def setVerticalExtent(self, pbot, ptop):
        """Set the vertical extent of the view to the specified pressure
           values (hPa) and redraw the plot.
        """
        changed = False
        if self.p_bot != pbot * 100:
            self.p_bot = pbot * 100
            changed = True
        if self.p_top != ptop * 100:
            self.p_top = ptop * 100
            changed = True
        if changed:
            if self.image is not None:
                self.image.remove()
                self.image = None
            self.setupSideView()
            self.waypoints_interactor.redraw_figure()

    def getVerticalExtent(self):
        """Returns the bottom and top pressure (hPa) of the plot.
        """
        return old_div(self.p_bot, 100), old_div(self.p_top, 100)

    def drawFlightLevels(self):
        """Draw horizontal lines indicating the altitude of the flight levels.
        """
        # Remove currently displayed flight level artists.
        for artist in self.fl_label_list:
            artist.remove()
        self.fl_label_list = []
        # Plot lines indicating flight level altitude.
        ax = self.ax
        for level in self.flightlevels:
            pressure = thermolib.flightlevel2pressure(level)
            self.fl_label_list.append(ax.axhline(pressure, color='k'))
            self.fl_label_list.append(ax.text(0.1, pressure, u"FL{:d}".format(level)))
        self.draw()

    def getFlightLevels(self):
        """
        """
        return self.flightlevels

    def setFlightLevels(self, flightlevels):
        """
        """
        self.flightlevels = flightlevels
        self.drawFlightLevels()

    def setFlightLevelsVisible(self, visible):
        """Toggle the visibility of the flight level lines.
        """
        for gxelement in self.fl_label_list:
            gxelement.set_visible(visible)
        self.draw()

    def getSettings(self):
        """Returns a dictionary containing settings regarding the side view
           appearance.
        """
        return self.settings_dict

    def setSettings(self, settings):
        """Apply settings to view.
        """
        if settings is not None:
            self.settings_dict.update(settings)
        settings = self.settings_dict
        self.setFlightLevels(settings["flightlevels"])
        self.setVerticalExtent(*settings["vertical_extent"])
        self.setFlightLevelsVisible(settings["draw_flightlevels"])
        if self.waypoints_interactor is not None:
            self.waypoints_interactor.set_vertices_visible(
                settings["draw_flighttrack"])
            self.waypoints_interactor.set_path_color(
                line_color=settings["colour_ft_vertices"],
                marker_facecolor=settings["colour_ft_waypoints"],
                patch_facecolor=settings["colour_ft_fill"])
            self.waypoints_interactor.set_patch_visible(
                settings["fill_flighttrack"])
            self.waypoints_interactor.set_labels_visible(
                settings["label_flighttrack"])

        self.settings_dict = settings

    def getBBOX(self):
        """Get the bounding box of the view (returns a 4-tuple
           x1, y1(p_bot[hPa]), x2, y2(p_top[hPa])).
        """
        # Get the bounding box of the current view
        # (bbox = llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat; i.e. for the side
        #  view bbox = x1, y1(p_bot), x2, y2(p_top)).
        axis = self.ax.axis()

        # Get the number of (great circle) interpolation points and the
        # number of labels along the x-axis.
        if self.waypoints_interactor is not None:
            num_interpolation_points = \
                self.waypoints_interactor.get_num_interpolation_points()
            num_labels = self.numlabels

        # Return a tuple (num_interpolation_points, p_bot[hPa],
        #                 num_labels, p_top[hPa]) as BBOX.
        bbox = (num_interpolation_points, old_div(axis[2], 100),
                num_labels, old_div(axis[3], 100))
        return bbox

    def drawLegend(self, img):
        if img is not None:
            logging.error("Legends not supported in SideView mode!")
            raise NotImplementedError

    def drawImage(self, img):
        """Draw the image img on the current plot.

        NOTE: The image is plotted in a separate axes object that is located
        below the axes that display the flight profile. This is necessary
        because imshow() does not work with logarithmic axes.
        """
        logging.debug("plotting vertical section image..")
        ix, iy = img.size
        logging.debug(u"  image size is {:d}{:d} px, format is {}".format(ix, iy, img.format))
        # Test if the image axes exist. If not, create them.
        if self.imgax is None:
            # Disable old white figure background so that the new underlying
            # axes become visible.
            self.ax.patch.set_facecolor("None")
            # self.mpl.canvas.ax.patch.set_alpha(0.5)

            # Add new axes to the plot (imshow doesn't work with logarithmic axes).
            ax_bbox = self.ax.get_position()
            # Main axes instance of mplwidget has zorder 99.
            self.imgax = self.fig.add_axes(ax_bbox, frameon=True,
                                           xticks=[], yticks=[],
                                           label="ax2", zorder=0)

        # If an image is currently displayed, remove it from the plot.
        if self.image is not None:
            self.image.remove()

        # Plot the new image in the image axes and adjust the axes limits.
        self.image = self.imgax.imshow(img, interpolation="nearest", aspect="auto",
                                       origin=PIL_image_origin)
        self.imgax.set_xlim(0, ix - 1)
        if _matplotlib_version >= "1.2":
            self.imgax.set_ylim(iy - 1, 0)
        else:
            self.imgax.set_ylim(0, iy - 1)
        self.draw()
        logging.debug("done.")


class MplSideViewWidget(MplNavBarWidget):
    """MplNavBarWidget using an MplSideViewCanvas as the Matplotlib
       view instance.
    """

    def __init__(self, parent=None):
        super(MplSideViewWidget, self).__init__(parent=parent,
                                                canvas=MplSideViewCanvas())
        # Disable some elements of the Matplotlib navigation toolbar.
        # Available actions: Home, Back, Forward, Pan, Zoom, Subplots,
        #                    Customize, Save
        actions = self.navbar.actions()
        for action in actions:
            if action.text() in ["Home", "Back", "Forward", "Pan", "Zoom",
                                 "Subplots", "Customize"]:
                action.setEnabled(False)


class MplTopViewCanvas(MplCanvas):
    """Specialised MplCanvas that draws a top view (map), together with a
       flight track, trajectories and other items.
    """

    redrawn = QtCore.pyqtSignal(name="redrawn")

    def __init__(self, settings=None):
        """
        """
        super(MplTopViewCanvas, self).__init__()
        self.waypoints_interactor = None
        self.satoverpasspatch = None
        self.kmloverlay = None
        self.map = None
        self.basename = "topview"

        # Axes and image object to display the legend graphic, if available.
        self.legax = None
        self.legimg = None

        # Set map appearance from parameter or, if not specified, to default
        # values.
        self.setMapAppearance(settings)

        # Progress dialog to inform the user about map redraws.
        self.pdlg = QtWidgets.QProgressDialog("redrawing map...", "Cancel", 0, 10, self)
        self.pdlg.close()

    def initMap(self, model=None, **kwargs):
        """Set up the map view.
        """
        ax = self.ax
        self.map = mpl_map.MapCanvas(appearance=self.getMapAppearance(),
                                     resolution="l", area_thresh=1000., ax=ax,
                                     **kwargs)
        ax.set_autoscale_on(False)
        ax.set_title("Top view", horizontalalignment="left", x=0)
        self.draw()  # necessary?

        if model:
            self.setWaypointsModel(model)

    def setWaypointsModel(self, model):
        """Set the WaypointsTableModel defining the flight track.
        If no model had been set before, create a new interactor object on the
        model to let the user interactively move the altitude of the waypoints.
        """
        self.waypoints_model = model
        if self.waypoints_interactor:
            self.waypoints_interactor.set_waypoints_model(model)
        else:
            # Create a path interactor object. The interactor object connects
            # itself to the change() signals of the flight track data model.
            appearance = self.getMapAppearance()
            self.waypoints_interactor = mpl_pi.HPathInteractor(
                self.map, self.waypoints_model,
                linecolor=appearance["colour_ft_vertices"],
                markerfacecolor=appearance["colour_ft_waypoints"])
            self.waypoints_interactor.set_vertices_visible(appearance["draw_flighttrack"])

    def setTrajectoryModel(self, model):
        """
        """
        self.map.set_trajectory_tree(model)

    def redrawMap(self, kwargs_update=None):
        """Redraw map canvas.

        Executed on clicked() of btMapRedraw.

        See MapCanvas.update_with_coordinate_change(). After the map redraw,
        coordinates of all objects overlain on the map have to be updated.
        """

        # remove legend
        self.drawLegend(None)

        # Show the progress dialog, since the retrieval can take a few seconds.
        self.pdlg.setValue(0)
        self.pdlg.show()
        QtWidgets.QApplication.processEvents()

        logging.debug("redrawing map")

        # 1) STORE COORDINATES OF NON-MAP OBJECTS IN LAT/LON.

        # (Currently none.)
        self.pdlg.setValue(1)
        QtWidgets.QApplication.processEvents()

        # 2) UPDATE MAP.
        self.map.update_with_coordinate_change(kwargs_update)
        self.draw()  # this one is required to trigger a
        # drawevent to update the background
        # in waypoints_interactor()

        self.pdlg.setValue(5)
        QtWidgets.QApplication.processEvents()

        # 3) UPDATE COORDINATES OF NON-MAP OBJECTS.
        self.pdlg.setValue(8)
        QtWidgets.QApplication.processEvents()

        if self.satoverpasspatch:
            self.satoverpasspatch.update()

        if self.kmloverlay:
            self.kmloverlay.update()

        self.drawMetadata("Top view")

        # Update in case of a projection change
        self.waypoints_interactor.update()

        self.pdlg.setValue(10)
        QtWidgets.QApplication.processEvents()

        logging.debug("finished redrawing map")
        self.pdlg.close()

        # Emit signal so other parts of the module can react to a redraw event.
        self.redrawn.emit()

    def getCRS(self):
        """Get the coordinate reference system of the displayed map.
        """
        return self.map.crs

    def getBBOX(self):
        """Get the bounding box of the map (returns a 4-tuple
           lllon, lllat, urlon, urlat).
        """
        # Get the bounding box of the current map view
        # (bbox = llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat).
        axis = self.ax.axis()

        if self.map.bbox_units == "latlon":
            # Convert the current axis corners to lat/lon coordinates.
            axis0, axis2 = self.map(axis[0], axis[2], inverse=True)
            axis1, axis3 = self.map(axis[1], axis[3], inverse=True)
            axis = [axis0, axis1, axis2, axis3]

        bbox = (axis[0], axis[2], axis[1], axis[3])
        return bbox

    def drawImage(self, img):
        """Draw the image img on the current plot.
        """
        logging.debug("plotting image..")
        self.wms_image = self.map.imshow(img, interpolation="nearest", alpha=1.,
                                         origin=PIL_image_origin)
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

    def drawLegend(self, img):
        """Draw the legend graphics img on the current plot.

        Adds new axes to the plot that accomodate the legend.
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
            ax_extent_x = old_div(img.size[0], figsize_px[0])
            ax_extent_y = old_div(img.size[1], figsize_px[1])

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
            self.legimg = self.legax.imshow(img, origin=PIL_image_origin, aspect="equal",
                                            interpolation="nearest")
        self.draw()
        # required so that it is actually drawn...
        QtWidgets.QApplication.processEvents()

    def plotSatelliteOverpass(self, segment):
        """Plots a satellite track on top of the map.
        """
        if self.satoverpasspatch:
            # If track is currently plotted on the map, remove it.
            self.satoverpasspatch.remove()
            if not segment:
                self.satoverpasspatch = None
                self.draw()
        if segment:
            # Create a new patch.
            self.satoverpasspatch = mpl_map.SatelliteOverpassPatch(self.map, segment)

    def plotKML(self, kmloverlay):
        """Plots a satellite track on top of the map.
        """
        if self.kmloverlay:
            # If track is currently plotted on the map, remove it.
            self.kmloverlay.remove()
            if not kmloverlay:
                self.kmloverlay = None
                self.draw()
        if kmloverlay:
            # Create a new patch.
            self.kmloverlay = kmloverlay

    def setMapAppearance(self, settings_dict):
        """Apply settings from dictionary 'settings_dict' to the view.

        If settings is None, apply default settings.
        """
        # logging.debug("applying map appearance settings %s." % settings)
        settings = {"draw_graticule": True,
                    "draw_coastlines": True,
                    "fill_waterbodies": True,
                    "fill_continents": True,
                    "draw_flighttrack": True,
                    "label_flighttrack": True,
                    "colour_water": (old_div(153, 255.), old_div(255, 255.), old_div(255, 255.), old_div(255, 255.)),
                    "colour_land": (old_div(204, 255.), old_div(153, 255.), old_div(102, 255.), old_div(255, 255.)),
                    "colour_ft_vertices": (0, 0, 1, 1),
                    "colour_ft_waypoints": (1, 0, 0, 1)}
        if settings_dict is not None:
            settings.update(settings_dict)

        self.appearance_settings = settings

        if self.map is not None:
            self.map.set_graticule_visible(settings["draw_graticule"])
            self.map.set_coastlines_visible(settings["draw_coastlines"])
            self.map.set_fillcontinents_visible(visible=settings["fill_continents"],
                                                land_color=settings["colour_land"],
                                                lake_color=settings["colour_water"])
            self.map.set_mapboundary_visible(visible=settings["fill_waterbodies"],
                                             bg_color=settings["colour_water"])
            self.waypoints_interactor.set_path_color(line_color=settings["colour_ft_vertices"],
                                                     marker_facecolor=settings["colour_ft_waypoints"])
            self.waypoints_interactor.set_vertices_visible(settings["draw_flighttrack"])
            self.waypoints_interactor.set_labels_visible(settings["label_flighttrack"])

    def setRemoteSensingAppearance(self, settings):
        self.waypoints_interactor.set_remote_sensing(settings["reference"])
        self.waypoints_interactor.set_tangent_visible(settings["draw_tangents"])
        self.waypoints_interactor.set_solar_angle_visible(settings["show_solar_angle"])

        self.waypoints_interactor.redraw_path()

    def getMapAppearance(self):
        """
        """
        return self.appearance_settings


class MplTopViewWidget(MplNavBarWidget):
    """MplNavBarWidget using an MplSideViewCanvas as the Matplotlib
       view instance.
    """

    def __init__(self, parent=None):
        super(MplTopViewWidget, self).__init__(parent=parent,
                                               canvas=MplTopViewCanvas())
        # Disable some elements of the Matplotlib navigation toolbar.
        # Available actions: Home, Back, Forward, Pan, Zoom, Subplots,
        #                    Customize, Save
        actions = self.navbar.actions()
        for action in actions:
            if action.text() in ["Subplots", "Customize"]:
                action.setEnabled(False)
            elif action.text() in ["Home", "Back", "Forward"]:
                action.triggered.connect(self.historyEvent)
        # Identify zoom events to redraw the map, if necessary.
        self.canvas.mpl_connect('button_release_event', self.zoomEvent)

    def zoomEvent(self, event):
        """Slot to react to zoom events. Called on button release events.
           Redraws the map after the user has zoomed or panned the image.
        """
        if self.navbar.mode in ["zoom rect", "pan/zoom"]:
            self.canvas.redrawMap()

    def historyEvent(self):
        """Slot to react to clicks on one of the history buttons in the
           navigation toolbar. Redraws the image.
        """
        self.canvas.redrawMap()


class MplTimeSeriesViewCanvas(MplCanvas):
    """Specialised MplCanvas that draws time series of trajectory data.
    """

    def __init__(self, identifier=None, traj_item_tree=None):
        """
        """
        super(MplTimeSeriesViewCanvas, self).__init__()
        self.identifier = identifier
        self.traj_item_tree = None
        if traj_item_tree:
            self.setTrajectoryModel(traj_item_tree)
        self.subPlots = []
        self.basename = "timeseries"

    def setIdentifier(self, identifier):
        self.identifier = identifier

    def setTrajectoryModel(self, tree):
        """Set a reference to the tree data structure containing the information
           about the elements plotted in the view (e.g. flight tracks,
           trajectories).
        """
        logging.debug("registering trajectory tree model")
        # Disconnect old tree, if defined.
        if self.traj_item_tree:
            self.traj_item_tree.dataChanged.disconnect(self.updateFromTrajectoryTree)
        # Set and connect new tree.
        self.traj_item_tree = tree
        self.traj_item_tree.dataChanged.connect(self.updateFromTrajectoryTree)
        # Draw tree items.
        self.updateTrajectoryItems()

    def updateFromTrajectoryTree(self, index1, index2):
        """This method should be connected to the 'dataChanged()' signal
           of the trajectory items tree.

        NOTE: If index1 != index2, the entire tree will be updated (I haven't
              found out so far how to get all the items between the two
              indices).
        """
        logging.debug("received dataChanged() signal")
        if not self.traj_item_tree:
            return
        # Update the map elements if the change that occured in traj_item_tree
        # affected a LagrantoMapItem.
        item = index1.internalPointer()
        item2 = index2.internalPointer()
        if isinstance(item, (titree.LagrantoMapItem, titree.AbstractVariableItem)):
            lastChange = self.traj_item_tree.getLastChange()
            if lastChange == "VISIBILITY_CHANGE":
                lastChange = "REDRAW"
                item = None
            elif lastChange == "MARKER_CHANGE":
                item = None
            # Update the given item or the entire tree if the two given
            # items are different.
            logging.debug("updating..")
            self.updateTrajectoryItems(item=item if item == item2 else None,
                                       mode=lastChange)

    def updateTrajectoryItems(self, item=None, mode="REDRAW"):
        """Delete the old figure and draw a new one.
        """
        # If no trajectory item tree is defined exit the method.
        if not self.traj_item_tree:
            return

        logging.debug("updating trajectory items on view '%s', mode '%s'",
                      self.identifier, mode)

        # Determine which items have to be plotted (these are the items that
        # own the variables that will be plotted, not the actual variables
        # themselves).
        itemsList = []
        stack = []
        if not item:
            # No item was passed -- determine all visible items from the
            # entire tree.
            logging.debug("processing all trajectory items")
            stack.extend(self.traj_item_tree.getRootItem().childItems)
        elif isinstance(item, titree.AbstractVariableItem):
            # The visibility of a single variable has been changed --
            # remember the item that owns this variable.
            stack.append(item.parent())
        else:
            # Remember the item that has been changed.
            stack.append(item)

        while len(stack) > 0:
            # Downwards traversal of the tree to determine all visible items
            # below the items that are on the stack.
            item = stack.pop()
            if item.isVisible(self.identifier):
                if isinstance(item, (titree.FlightTrackItem, titree.TrajectoryItem)):
                    itemsList.append(item)
                else:
                    stack.extend(item.childItems)

        logging.debug("Plotting elements '%s'", [i.getName() for i in itemsList])

        if mode in ["REDRAW", "MARKER_CHANGE"]:
            # Clear the figure -- it needs to be completely redrawn.
            self.fig.clf()

        if mode in ["REDRAW", "MARKER_CHANGE"]:
            # Iterative list traversal no. 1: Determine the earliest start time
            # and the required number of subplots.
            earliestStartTime = datetime(3000, 1, 1)
            self.subPlots = []
            for item in itemsList:
                earliestStartTime = min(earliestStartTime, item.getStartTime())
                for variable in item.childItems:
                    if variable.isVisible(self.identifier) and variable.getVariableName() not in self.subPlots:
                        self.subPlots.append(variable.getVariableName())

        # Iterative list traversal no. 2: Draw / update plots.
        for item in itemsList:

            logging.debug(u"plotting item {}".format(item.getName()))
            # The variables that have to be plotted are children of self.mapItem.
            # Plot all variables whose visible-flag is set to True.
            variablesToPlot = [variable for variable in item.childItems
                               if variable.getVariableName() in self.subPlots]

            if mode in ["GXPROPERTY_CHANGE"]:
                #
                # If only a graphics property has been changed: Apply setp with
                # the new properties to all variables of trajectory 'item'.
                for variable in variablesToPlot:
                    plt.setp(
                        variable.getGxElementProperty(
                            "timeseries", u"instance::{}".format(self.identifier)),
                        visible=item.isVisible(self.identifier),
                        color=item.getGxElementProperty("general", "colour"),
                        linestyle=item.getGxElementProperty("general", "linestyle"),
                        linewidth=item.getGxElementProperty("general", "linewidth"))

            elif mode in ["REDRAW", "MARKER_CHANGE"]:
                #
                # Loop over all variables to plot.
                for variable in variablesToPlot:
                    #
                    # A total of len(self.subPlots) subplots are drawn.
                    # Place the plot of this variable on the index+1-th subplot,
                    # where index is the index of the variable name in 'self.subPlots'.
                    index = self.subPlots.index(variable.getVariableName())
                    ax = self.fig.add_subplot(len(self.subPlots), 1, index + 1)
                    #
                    # The x-axis is the time axis. Shift the current time data
                    # so that the common time axis starts with the earliest
                    # start time determined above.
                    x = item.getTimeVariable().getVariableData() + \
                        old_div((item.getStartTime() - earliestStartTime).seconds, 3600.)
                    y = variable.getVariableData()
                    #
                    # Plot the variable data with the colour determines above, store
                    # the plot instance in the variable's gxElements.
                    plotInstance = ax.plot(x, y,
                                           color=item.getGxElementProperty("general", "colour"),
                                           linestyle=item.getGxElementProperty("general",
                                                                               "linestyle"),
                                           linewidth=item.getGxElementProperty("general",
                                                                               "linewidth"))
                    variable.setGxElementProperty("timeseries",
                                                  u"instance::{}".format(self.identifier),
                                                  plotInstance)
                    #
                    # If we've just plotted the pressure variable flip the y-axis
                    # upside down.
                    if variable == item.getPressureVariable():
                        ymin, ymax = ax.get_ylim()
                        if ymin < ymax:
                            ax.set_ylim(ymax, ymin)
                    #
                    # Put the variable name on the y-axis and tighten the x-axis range
                    # to the range in which data are actually available.
                    ax.set_ylabel(variable.getVariableName())
                    ax.axis('tight')

                    #
                    # Draw vertical dotted lines at the time marker indexes to help
                    # identify the time markers on the time series plot.
                    timeMarkerIndexes = item.getTimeMarkerIndexes()
                    if timeMarkerIndexes is not None:
                        for time in x[timeMarkerIndexes[1:]]:
                            ax.axvline(time, color='black', linestyle=':')

                    #
                    # The topmost subplot gets the title (the name of self.mapItem).
                    if index == 0:
                        if len(itemsList) > 1:
                            ax.set_title(u"Ensemble: {} to {}".format(
                                itemsList[0].getName(), itemsList[-1].getName()))
                        else:
                            ax.set_title(u"Single item: {}".format(itemsList[0].getName()))

                    #
                    # The bottommost subplot gets the x-label: The name of the time
                    # variable.
                    if index == len(self.subPlots) - 1:
                        ax.set_xlabel("time [hr since " +
                                      earliestStartTime.strftime("%Y-%m-%d %H:%M UTC") +
                                      "]")
        # Update the figure canvas.
        self.fig.canvas.draw()


class MplTimeSeriesViewWidget(MplNavBarWidget):
    """MplNavBarWidget using an MplTimeSeriesViewCanvas as the Matplotlib
       view instance.
    """

    def __init__(self, parent=None):
        super(MplTimeSeriesViewWidget, self).__init__(parent=parent,
                                                      canvas=MplTimeSeriesViewCanvas())
        # Disable some elements of the Matplotlib navigation toolbar.
        # Available actions: Home, Back, Forward, Pan, Zoom, Subplots,
        #                    Customize, Save
        actions = self.navbar.actions()
        for action in actions:
            if action.text() in ["Customize"]:
                action.setEnabled(False)
