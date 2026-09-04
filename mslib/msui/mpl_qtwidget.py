# -*- coding: utf-8 -*-
"""

    mslib.msui.mpl_qtwidget
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

import enum
import os
import logging
import numpy as np
from matplotlib import cbook
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT, FigureCanvasQTAgg
import matplotlib.backend_bases
from PyQt5 import QtCore, QtWidgets, QtGui
from mslib.msui.viewplotter import LAST_SAVE_DIRECTORY, TopViewPlotter, SideViewPlotter, LinearViewPlotter

from mslib.utils.thermolib import convert_pressure_to_vertical_axis_measure
from mslib.utils import thermolib
from mslib.utils.config import config_loader, load_settings_qsettings, save_settings_qsettings
from mslib.utils.qt import Worker
from mslib.utils.units import units
from mslib.msui import mpl_pathinteractor as mpl_pi
from mslib.msui import mpl_map
from mslib.msui.icons import icons

matplotlib.rcParams['savefig.directory'] = LAST_SAVE_DIRECTORY


class MplCanvas(FigureCanvasQTAgg):
    """Class to represent the FigureCanvasQTAgg widget.
    Main axes instance has zorder 99 (important when additional
    axes are added).
    """

    def __init__(self, plotter):
        self.default_filename = "_image"
        self.plotter = plotter
        # initialization of the canvas
        super().__init__(self.plotter.fig)

        # we define the widget as expandable
        super().setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # notify the system of updated policy
        super().updateGeometry()

    def get_default_filename(self):
        """
        defines the image file name for storing from a view
        return: default png filename of a view
        """
        result = self.basename + self.default_filename
        if len(result) > 100:
            result = result[:100]
        return result + ".png"

    def draw_metadata(self, title="", init_time=None, valid_time=None,
                      level=None, style=None):
        """Draw a title indicating the init and valid time of the
           image that has been drawn, and the vertical elevation level.
        """
        self.default_filename = ""
        if title:
            self.default_filename += f"_{title.split()[0]:>5}"
        if level:
            self.default_filename += f"_{level.split()[0]}"

        self.plotter.draw_metadata(title, init_time, valid_time, level, style)
        self.draw()
        # without the repaint the title is not properly updated
        self.repaint()

    def get_plot_size_in_px(self):
        """Determines the size of the current figure in pixels.
        Returns the tuple width, height.
        """
        return self.plotter.get_plot_size_in_px()

    def get_settings(self):
        return self.plotter.get_settings()

    def set_settings(self, settings, save=False):
        """
        Apply settings from options ui to the linear view
        """
        self.plotter.set_settings(settings, save)


class _Mode(str, enum.Enum):
    """
    Override _Mode of backend_base to include our tools.
    """
    NONE = ""
    PAN = "pan/zoom"
    ZOOM = "zoom rect"
    INSERT_WP = "insert waypoint"
    DELETE_WP = "delete waypoint"
    MOVE_WP = "move waypoint"

    def __str__(self):
        return self.value

    @property
    def _navigate_mode(self):
        return self.name if self is not _Mode.NONE else None


matplotlib.backend_bases._Mode = _Mode


class NavigationToolbar(NavigationToolbar2QT):
    """
    parts of this class have been copied from the NavigationToolbar2QT class.
    According to https://matplotlib.org/users/license.html we shall
    summarise our changes to matplotlib code:
    We copied small parts of the given implementation of the navigation
    toolbar class to allow for our custom waypoint buttons. Our code extends
    the matplotlib toolbar to allow for less or additional buttons and properly
    update all plots and elements in case the pan or zoom elements were
    triggered by the user.
    """

    def __init__(self, canvas, parent, sideview=False, coordinates=True):
        self.sideview = sideview

        if sideview:
            self.toolitems = [
                _x for _x in self.toolitems if _x[0] in ('Save',)]
            self.set_history_buttons = lambda: None
        else:
            self.toolitems = [
                _x for _x in self.toolitems if
                _x[0] in (None, 'Home', 'Back', 'Forward', 'Pan', 'Zoom', 'Save')]

        self.toolitems.extend([
            (None, None, None, None),
            ('Mv WP', 'Move waypoints', "wp_move", 'move_wp'),
            ('Ins WP', 'Insert waypoints', "wp_insert", 'insert_wp'),
            ('Del WP', 'Delete waypoints', "wp_delete", 'delete_wp'),
        ])
        super().__init__(canvas, parent, coordinates)
        self._actions["move_wp"].setCheckable(True)
        self._actions["insert_wp"].setCheckable(True)
        self._actions["delete_wp"].setCheckable(True)

        self.setIconSize(QtCore.QSize(24, 24))
        self.layout().setSpacing(12)
        self.canvas = canvas
        self.no_push_history = False

    def _icon(self, name, *args):
        """
        wrapper around base method to inject our own icons.
        """
        myname = icons("32x32", name)
        if os.path.exists(myname):
            return QtGui.QIcon(myname)
        else:
            return super()._icon(name)

    def _zoom_pan_handler(self, event):
        """
        extend zoom_pan_handler of base class with our own tools
        """
        super()._zoom_pan_handler(event)
        if event.name == "button_press_event":
            if self.mode in (_Mode.INSERT_WP, _Mode.MOVE_WP, _Mode.DELETE_WP):
                self.canvas.waypoints_interactor.button_press_callback(event)
        elif event.name == "button_release_event":
            if self.mode == _Mode.INSERT_WP:
                self.canvas.waypoints_interactor.button_release_insert_callback(event)
            elif self.mode == _Mode.MOVE_WP:
                self.canvas.waypoints_interactor.button_release_move_callback(event)
            elif self.mode == _Mode.DELETE_WP:
                self.canvas.waypoints_interactor.button_release_delete_callback(event)

    def clear_history(self):
        self._nav_stack.clear()
        self.push_current()
        self.set_history_buttons()

    def push_current(self):
        """Push the current view limits and position onto the stack."""
        if self.sideview:
            super().push_current()
        elif self.no_push_history:
            pass
        else:
            kwargs = self.canvas.map.kwargs.copy()
            self._nav_stack.push(kwargs)
            self.set_history_buttons()
            # Persist the map's current lon/lat extent, so an external process
            # can read the view actually displayed after a pan/zoom
            # rather than a predefined section's static extent.
            # Merge into any existing settings for this tag
            # (e.g. canvas_screen_region/os_screen_region) instead of
            # overwriting them, since save_settings_qsettings replaces the
            # whole per-tag dict.
            settings = load_settings_qsettings(self.canvas.basename, {})
            settings['map_extent_region'] = (kwargs['llcrnrlon'], kwargs['llcrnrlat'],
                                             kwargs['urcrnrlon'], kwargs['urcrnrlat'])
            save_settings_qsettings(self.canvas.basename, settings)

    def _update_view(self):
        """
        Update the viewlim and position from the view and position stack for
        each axes.
        """
        if self.sideview:
            super()._update_view()
        else:
            nav_info = self._nav_stack()
            if nav_info is None:
                return
            self.canvas.redraw_map(nav_info)

    def insert_wp(self, *args):
        """
        activate insert_wp tool
        """
        if self.mode == _Mode.INSERT_WP:
            self.mode = _Mode.NONE
            self.canvas.widgetlock.release(self)
        else:
            self.mode = _Mode.INSERT_WP
            self.canvas.widgetlock(self)
        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self.mode._navigate_mode)
        self.set_message(self.mode)
        self._update_buttons_checked()

    def delete_wp(self, *args):
        """
        activate delete_wp tool
        """
        if self.mode == _Mode.DELETE_WP:
            self.mode = _Mode.NONE
            self.canvas.widgetlock.release(self)
        else:
            self.mode = _Mode.DELETE_WP
            self.canvas.widgetlock(self)
        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self.mode._navigate_mode)
        self.set_message(self.mode)
        self._update_buttons_checked()

    def move_wp(self, *args):
        """
        activate move_wp tool
        """
        if self.mode == _Mode.MOVE_WP:
            self.mode = _Mode.NONE
            self.canvas.widgetlock.release(self)
        else:
            self.mode = _Mode.MOVE_WP
            self.canvas.widgetlock(self)
        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self.mode._navigate_mode)
        self.set_message(self.mode)
        self._update_buttons_checked()

    def release_zoom(self, event):
        self.no_push_history = True
        super().release_zoom(event)
        self.no_push_history = False
        self.canvas.redraw_map(on_finished=self.push_current)

    def release_pan(self, event):
        self.no_push_history = True
        super().release_pan(event)
        self.no_push_history = False
        self.canvas.redraw_map(on_finished=self.push_current)

    def mouse_move(self, event):
        """
        overwrite mouse_move to print lon/lat instead of x/y coordinates.
        """
        if self.mode == _Mode.MOVE_WP:
            self.canvas.waypoints_interactor.motion_notify_callback(event)

        if isinstance(self.canvas.waypoints_interactor, mpl_pi.LPathInteractor):
            if not event.ydata or not event.xdata:
                self.set_message(self.mode)
            else:
                (lat, lon, alt), _ = self.canvas.waypoints_interactor.get_lat_lon(event)
                self.set_message(f"lat={lat: <6.2f} lon={lon: <7.2f} altitude={alt: <3.0f}hft")
        elif not self.sideview:
            self._update_cursor(event)

            if event.inaxes and event.inaxes.get_navigate():
                try:
                    lat, lon = self.canvas.waypoints_interactor.get_lat_lon(event)
                except (ValueError, OverflowError) as ex:
                    logging.error("%s", ex)
                else:
                    s = f"lat={lat:6.2f}, lon={lon:7.2f}"
                    artists = [a for a in event.inaxes._mouseover_set
                               if a.contains(event)[0] and a.get_visible()]
                    if artists:
                        a = cbook._topmost_artist(artists)
                        if a is not event.inaxes.patch:
                            data = a.get_cursor_data(event)
                            if data is not None:
                                data_str = a.format_cursor_data(data)
                                if data_str is not None:
                                    s += " " + data_str
                    if self.mode:
                        s = self.mode + ", " + s
                    self.set_message(s)
            else:
                self.set_message(self.mode)
        else:
            if not event.ydata or not event.xdata:
                self.set_message(self.mode)
            else:
                (lat, lon), _ = self.canvas.waypoints_interactor.get_lat_lon(event)
                y_value = convert_pressure_to_vertical_axis_measure(
                    self.canvas.plotter.settings["vertical_axis"], event.ydata)
                units = {
                    "pressure altitude": "km",
                    "flight level": "hft",
                    "pressure": "hPa"}[self.canvas.plotter.settings["vertical_axis"]]
                self.set_message(f"{self.mode} lat={lat:6.2f} lon={lon:7.2f} altitude={y_value:.2f}{units}")

    def _update_buttons_checked(self):
        super()._update_buttons_checked()
        if "insert_wp" in self._actions:
            self._actions['insert_wp'].setChecked(self.mode.name == 'INSERT_WP')
        if "delete_wp" in self._actions:
            self._actions['delete_wp'].setChecked(self.mode.name == 'DELETE_WP')
        if "move_wp" in self._actions:
            self._actions['move_wp'].setChecked(self.mode.name == 'MOVE_WP')


class MplNavBarWidget(QtWidgets.QWidget):
    """Matplotlib canvas widget with navigation toolbar defined in Qt Designer"""

    def __init__(self, sideview=False, parent=None, canvas=None):
        # initialization of Qt MainWindow widget
        super().__init__(parent)

        # set the canvas to the Matplotlib widget
        if canvas:
            self.canvas = canvas
        else:
            self.canvas = MplCanvas()

        # instantiate the navigation toolbar
        self.navbar = NavigationToolbar(self.canvas, self, sideview)

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

    def __init__(self, model=None, settings=None, numlabels=None):
        """
        Arguments:
        model -- WaypointsTableModel defining the vertical section.
        """
        if numlabels is None:
            numlabels = config_loader(dataset='num_labels')
        self.plotter = SideViewPlotter()
        super().__init__(self.plotter)

        if settings is not None:
            self.plotter.set_settings(settings)

        # Setup the plot.
        self.update_vertical_extent_from_settings(init=True)

        self.numlabels = numlabels
        self.plotter.ax.patch.set_facecolor("None")
        # Main axes instance of mplwidget has zorder 99.
        self.vertical_lines = []

        # Sets the default value of sideview fontsize settings from MSSDefaultConfig.
        self.sideview_size_settings = config_loader(dataset="sideview")
        self.plotter.setup_side_view()
        # Draw a number of flight level lines.
        self.flightlevels = []
        self.fl_label_list = []
        self.draw_flight_levels()
        self.image = None
        self.ceiling_alt = []
        # If a waypoints model has been passed, create an interactor on it.
        self.waypoints_interactor = None
        self.waypoints_model = None
        self.basename = "sideview"
        if model is not None:
            self.set_waypoints_model(model)

    def set_waypoints_model(self, model):
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
                self.plotter.ax, self.waypoints_model,
                numintpoints=config_loader(dataset="num_interpolation_points"),
                redraw_xaxis=self.redraw_xaxis, clear_figure=self.plotter.clear_figure
            )
            self.set_settings(None)

    def redraw_xaxis(self, lats, lons, times):
        """Redraw the x-axis of the side view on path changes. Also remove
           a vertical section image if one exists, as it is invalid after
           a path change.
        """
        times_visible = False
        if self.waypoints_model is not None:
            times_visible = self.waypoints_model.performance_settings["visible"]
        self.plotter.redraw_xaxis(lats, lons, times, times_visible)

        for _line in self.ceiling_alt:
            _line.remove()
        self.ceiling_alt = []
        if self.waypoints_model is not None and self.waypoints_interactor is not None:
            vertices = self.waypoints_interactor.plotter.pathpatch.get_path().vertices
            vx, vy = list(zip(*vertices))
            wpd = self.waypoints_model.all_waypoint_data()
            if len(wpd) > 0:
                xs, ys = [], []
                aircraft = self.waypoints_model.performance_settings["aircraft"]
                for i in range(len(wpd) - 1):
                    weight = np.linspace(wpd[i].weight, wpd[i + 1].weight, 5, endpoint=False)
                    ceil = [aircraft.get_ceiling_altitude(_w) for _w in weight]
                    xs.extend(np.linspace(vx[i], vx[i + 1], 5, endpoint=False))
                    ys.extend(ceil)
                xs.append(vx[-1])
                ys.append(aircraft.get_ceiling_altitude(wpd[-1].weight))

                self.ceiling_alt = self.plotter.ax.plot(
                    xs, thermolib.flightlevel2pressure(np.asarray(ys) * units.hft).magnitude,
                    color="k", ls="--")
                self.update_ceiling(
                    self.plotter.get_settings()["draw_ceiling"] and
                    self.waypoints_model.performance_settings["visible"],
                    self.plotter.get_settings()["colour_ceiling"])
                highlight = [[wp.lat, wp.lon] for wp in self.waypoints_model.waypoints]
                self.plotter.draw_vertical_lines(highlight, lats, lons)

    def get_vertical_extent(self):
        """Returns the bottom and top pressure (hPa) of the plot.
        """
        return (self.p_bot // 100), (self.p_top // 100)

    def draw_flight_levels(self):
        """Draw horizontal lines indicating the altitude of the flight levels.
        """
        # Remove currently displayed flight level artists.
        for artist in self.fl_label_list:
            artist.remove()
        self.fl_label_list = []
        # Plot lines indicating flight level altitude.
        ax = self.plotter.ax
        for level in self.flightlevels:
            pressure = thermolib.flightlevel2pressure(level * units.hft).magnitude
            self.fl_label_list.append(ax.axhline(pressure, color='k'))
            self.fl_label_list.append(ax.text(0.1, pressure, f"FL{level:d}"))
        self.draw()

    def get_flight_levels(self):
        """
        """
        return self.flightlevels

    def set_flight_levels(self, flightlevels):
        """
        """
        self.flightlevels = flightlevels
        self.draw_flight_levels()

    def set_flight_levels_visible(self, visible):
        """Toggle the visibility of the flight level lines.
        """
        for gxelement in self.fl_label_list:
            gxelement.set_visible(visible)
        self.draw()

    def update_ceiling(self, visible, color):
        """Toggle the visibility of the flight level lines.
        """
        for line in self.ceiling_alt:
            line.set_color(color)
            line.set_visible(visible)
        self.draw()

    def set_settings(self, settings, save=False):
        """Apply settings to view.
        """
        if settings is None:
            settings = self.plotter.get_settings()
            settings.setdefault("line_thickness", 2)
            settings.setdefault("line_style", "Solid")
            settings.setdefault("line_transparency", 1.0)
            settings.setdefault("colour_ft_vertices", "blue")
            settings.setdefault("colour_ft_waypoints", "red")
            settings.setdefault("draw_marker", True)
            settings.setdefault("draw_flighttrack", True)
            settings.setdefault("label_flighttrack", True)

        old_vertical_lines = self.plotter.settings["draw_verticals"]
        if settings is not None:
            self.plotter.set_settings(settings, save)
        settings = self.plotter.get_settings()
        self.set_flight_levels(settings["flightlevels"])
        self.set_flight_levels_visible(settings["draw_flightlevels"])
        self.update_ceiling(
            settings["draw_ceiling"] and (
                self.waypoints_model is not None and
                self.waypoints_model.performance_settings["visible"]),
            settings["colour_ceiling"])
        self.update_vertical_extent_from_settings()

        if self.waypoints_interactor is not None:
            wpi_plotter = self.waypoints_interactor.plotter
            wpi_plotter.line.set_marker("o" if settings["draw_marker"] else "")
            wpi_plotter.set_vertices_visible(settings["draw_flighttrack"])
            wpi_plotter.set_path_color(
                line_color=settings["colour_ft_vertices"],
                marker_facecolor=settings["colour_ft_waypoints"],
                patch_facecolor=settings["colour_ft_fill"])
            wpi_plotter.set_patch_visible(settings["fill_flighttrack"])
            wpi_plotter.set_labels_visible(settings["label_flighttrack"])
            wpi_plotter.set_line_thickness(settings["line_thickness"])
            wpi_plotter.set_line_style(settings["line_style"])
            wpi_plotter.set_line_transparency(
                settings["line_transparency"] / 100.0 if settings["line_transparency"] > 1 else settings[
                    "line_transparency"])  # Normalize the (transparency) value

            if self.waypoints_model is not None \
                    and settings["draw_verticals"] != old_vertical_lines:
                self.redraw_xaxis(wpi_plotter.path.ilats,
                                  wpi_plotter.path.ilons,
                                  wpi_plotter.path.itimes)

    def getBBOX(self):
        """Get the bounding box of the view (returns a 4-tuple
           x1, y1(p_bot[hPa]), x2, y2(p_top[hPa])).
        """
        # Get the bounding box of the current view
        # (bbox = llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat; i.e. for the side
        #  view bbox = x1, y1(p_bot), x2, y2(p_top)).
        axis = self.plotter.ax.axis()

        # Get the number of (great circle) interpolation points and the
        # number of labels along the x-axis.
        if self.waypoints_interactor is not None:
            num_interpolation_points = \
                self.waypoints_interactor.plotter.get_num_interpolation_points()
            num_labels = self.numlabels

            # Return a tuple (num_interpolation_points, p_bot[hPa],
            #                 num_labels, p_top[hPa]) as BBOX.
            bbox = (num_interpolation_points, (axis[2] / 100),
                    num_labels, (axis[3] / 100))
            return bbox
        else:
            self.plotter.getBBOX()

    def draw_legend(self, img):
        if img is not None:
            logging.error("Legends not supported in SideView mode!")
            raise NotImplementedError

    def draw_image(self, img):
        """Draw the image img on the current plot.

        NOTE: The image is plotted in a separate axes object that is located
        below the axes that display the flight profile. This is necessary
        because imshow() does not work with logarithmic axes.
        """
        self.plotter.draw_image(img)

    def update_vertical_extent_from_settings(self, init=False):
        """ Checks for current units of axis and convert the upper and lower limit
        to pa(pascals) for the internal computation by code """

        self.plotter.update_vertical_extent_from_settings(init)


class MplSideViewWidget(MplNavBarWidget):
    """MplNavBarWidget using an MplSideViewCanvas as the Matplotlib
       view instance.
    """

    def __init__(self, parent=None):
        super().__init__(
            sideview=True, parent=parent, canvas=MplSideViewCanvas())
        # Disable some elements of the Matplotlib navigation toolbar.
        # Available actions: Home, Back, Forward, Pan, Zoom, Subplots,
        #                    Customize, Save, Insert Waypoint, Delete Waypoint
        actions = self.navbar.actions()
        for action in actions:
            if action.text() in ["Home", "Back", "Forward", "Pan", "Zoom",
                                 "Subplots", "Customize"]:
                action.setEnabled(False)


class MplLinearViewCanvas(MplCanvas):
    """Specialised MplCanvas that draws a linear view of a
       flight track / list of waypoints.
    """

    def __init__(self, model=None, numlabels=None):
        """
        Arguments:
        model -- WaypointsTableModel defining the linear section.
        """
        if numlabels is None:
            numlabels = config_loader(dataset='num_labels')
        self.plotter = LinearViewPlotter()
        super().__init__(self.plotter)

        # Setup the plot.
        self.numlabels = numlabels
        self.plotter.setup_linear_view()
        # If a waypoints model has been passed, create an interactor on it.
        self.waypoints_interactor = None
        self.waypoints_model = None
        self.vertical_lines = []
        self.basename = "linearview"
        self.draw()
        if model:
            self.set_waypoints_model(model)

    def set_waypoints_model(self, model):
        """Set the WaypointsTableModel defining the linear section.
        If no model had been set before, create a new interactor object on the model
        """
        self.waypoints_model = model

        if self.waypoints_interactor:
            self.waypoints_interactor.set_waypoints_model(model)
        else:
            # Create a path interactor object. The interactor object connects
            # itself to the change() signals of the flight track data model.
            self.waypoints_interactor = mpl_pi.LPathInteractor(
                self.plotter.ax, self.waypoints_model,
                numintpoints=config_loader(dataset="num_interpolation_points"),
                clear_figure=self.plotter.clear_figure,
                redraw_xaxis=self.redraw_xaxis
            )
            self.set_settings(None)
        self.redraw_xaxis()

    def setup_linear_view(self):
        """Set up a linear section view.
        """
        self.fig.subplots_adjust(left=0.08, right=0.96, top=0.9, bottom=0.14)

    def getBBOX(self):
        """Get the bounding box of the view.
        """
        # Get the number of (great circle) interpolation points and the
        # number of labels along the x-axis.
        if self.waypoints_interactor is not None:
            num_interpolation_points = \
                self.waypoints_interactor.plotter.get_num_interpolation_points()

        # Return a tuple (num_interpolation_points) as BBOX.
        bbox = (num_interpolation_points,)
        return bbox

    def draw_legend(self, img):
        if img is not None:
            logging.error("Legends not supported in LinearView mode!")
            raise NotImplementedError

    def draw_image(self, xmls, colors=None, scales=None):
        self.plotter.draw_image(xmls, colors, scales)
        self.redraw_xaxis()
        # Hand the retrieved values over to the flight track model, so that
        # other views (e.g. the table view) can show the data at a waypoint.
        if self.waypoints_model is not None:
            self.waypoints_model.set_linear_data_from_xml(xmls)

    def redraw_xaxis(self):
        """Redraw the x-axis of the linear view on path changes.
        """
        if self.waypoints_interactor is not None:
            lats = self.waypoints_interactor.plotter.path.ilats
            lons = self.waypoints_interactor.plotter.path.ilons
            logging.debug("redrawing x-axis")

            self.plotter.redraw_xaxis(lats, lons)

            highlight = [[wp.lat, wp.lon] for wp in self.waypoints_model.waypoints]
            self.plotter.draw_vertical_lines(highlight, lats, lons)


class MplLinearViewWidget(MplNavBarWidget):
    """MplNavBarWidget using an MplLinearViewCanvas as the Matplotlib
       view instance.
    """

    def __init__(self, parent=None):
        super().__init__(
            sideview=False, parent=parent, canvas=MplLinearViewCanvas())
        # Disable some elements of the Matplotlib navigation toolbar.
        # Available actions: Home, Back, Forward, Pan, Zoom, Subplots,
        #                    Customize, Save, Insert Waypoint, Delete Waypoint
        actions = self.navbar.actions()
        for action in actions[:-1]:
            if action.text() in ["Home", "Back", "Forward", "Pan", "Zoom", "",
                                 "Subplots", "Customize", "Mv WP", "Del WP", "Ins WP"]:
                action.setVisible(False)


class MplTopViewCanvas(MplCanvas):
    """Specialised MplCanvas that draws a top view (map), together with a
       flight track, trajectories and other items.
    """

    redrawn = QtCore.pyqtSignal(name="redrawn")

    def __init__(self, settings=None):
        """
        """
        self.plotter = TopViewPlotter()
        super().__init__(self.plotter)
        self.waypoints_interactor = None
        self.satoverpasspatch = []
        self.kmloverlay = None
        self.multiple_flightpath = None
        self.basename = "topview"

        # Set map appearance from parameter or, if not specified, to default
        # values.
        self.set_settings(settings)

        # Progress dialog to inform the user about map redraws.
        self.pdlg = QtWidgets.QProgressDialog("redrawing map...", "Cancel", 0, 10, self)
        self.pdlg.close()

        # Async redraw state. While a redraw is running, incoming redraw
        # requests are coalesced to the latest kwargs.
        self._redraw_worker = None
        self._redraw_in_progress = False
        self._active_redraw_callbacks = []
        self._queued_redraw_pending = False
        self._queued_redraw_kwargs = None
        self._queued_redraw_callbacks = []

    @property
    def map(self):  # noqa: A003
        return self.plotter.map

    def _update_progress_dialog(self, value):
        """Update progress state without re-entering the full Qt event loop."""
        # with help from PyCharm
        self.pdlg.setValue(value)
        self.pdlg.repaint()
        self.repaint()

    @staticmethod
    def _copy_redraw_kwargs(kwargs_update):
        # with help from PyCharm
        if isinstance(kwargs_update, dict):
            return kwargs_update.copy()
        return kwargs_update

    @staticmethod
    def _run_redraw_callbacks(callbacks):
        # with help from PyCharm
        for callback in callbacks:
            try:
                callback()
            except Exception as ex:  # nosec B110
                logging.error("redraw completion callback failed: %s", ex)

    def _start_redraw_worker(self, kwargs_update):
        # with help from PyCharm
        self._redraw_in_progress = True
        self._update_progress_dialog(1)
        self._redraw_worker = Worker(lambda: self.plotter.redraw_map(kwargs_update))
        self._redraw_worker.finished.connect(self._on_redraw_worker_finished)
        self._redraw_worker.failed.connect(self._on_redraw_worker_failed)
        self._redraw_worker.start()

    def _continue_with_queued_redraw(self):
        # with help from PyCharm
        if not self._queued_redraw_pending:
            return
        queued_kwargs = self._queued_redraw_kwargs
        queued_callbacks = self._queued_redraw_callbacks
        self._queued_redraw_pending = False
        self._queued_redraw_kwargs = None
        self._queued_redraw_callbacks = []
        self.redraw_map(queued_kwargs, on_finished=queued_callbacks)

    def _finish_redraw(self):
        # with help from PyCharm
        self._update_progress_dialog(5)

        # 3) UPDATE COORDINATES OF NON-MAP OBJECTS.
        self._update_progress_dialog(8)
        for segment in self.satoverpasspatch:
            segment.update()
        if self.kmloverlay:
            self.kmloverlay.update()
        if self.multiple_flightpath:
            self.multiple_flightpath.update()

        self.repaint()

        # Update in case of an operation change.
        if self.waypoints_interactor is not None:
            self.waypoints_interactor.update()

        self._update_progress_dialog(10)
        logging.debug("finished redrawing map")
        self.pdlg.close()

        callbacks = self._active_redraw_callbacks
        self._active_redraw_callbacks = []
        self._run_redraw_callbacks(callbacks)

        # Emit signal so other parts of the module can react to a redraw event.
        self.redrawn.emit()

    @QtCore.pyqtSlot(object)
    def _on_redraw_worker_finished(self, _result):
        # with help from PyCharm
        self._redraw_worker = None
        self._redraw_in_progress = False
        self._finish_redraw()
        self._continue_with_queued_redraw()

    @QtCore.pyqtSlot(Exception)
    def _on_redraw_worker_failed(self, ex):
        # with help from PyCharm
        logging.error("map redraw failed: %s", ex)
        self._redraw_worker = None
        self._redraw_in_progress = False
        self._active_redraw_callbacks = []
        self.pdlg.close()
        self._continue_with_queued_redraw()

    def init_map(self, model=None, **kwargs):
        """Set up the map view.
        """
        self.plotter.init_map(**kwargs)

        if model:
            self.set_waypoints_model(model)

    def set_waypoints_model(self, model):
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
            settings = self.get_settings()
            try:
                self.waypoints_interactor = mpl_pi.HPathInteractor(
                    self.plotter.map, self.waypoints_model,
                    linecolor=settings["colour_ft_vertices"],
                    markerfacecolor=settings["colour_ft_waypoints"],
                    show_marker=settings["draw_marker"])
                self.set_settings(None)
            except IOError as err:
                logging.error("%s" % err)

    def redraw_map(self, kwargs_update=None, on_finished=None):
        """Redraw map canvas.

        Executed on clicked() of btMapRedraw.

        See MapCanvas.update_with_coordinate_change(). After the map redraw,
        coordinates of all objects overlain on the map have to be updated.
        """
        if on_finished is None:
            callbacks = []
        elif isinstance(on_finished, (list, tuple)):
            callbacks = [cb for cb in on_finished if cb is not None]
        else:
            callbacks = [on_finished]

        kwargs_update = self._copy_redraw_kwargs(kwargs_update)
        if self._redraw_in_progress:
            self._queued_redraw_pending = True
            self._queued_redraw_kwargs = kwargs_update
            self._queued_redraw_callbacks.extend(callbacks)
            logging.debug("map redraw already in progress, coalescing request")
            return

        self._active_redraw_callbacks = callbacks

        # remove legend
        self.draw_legend(None)

        # Show the progress dialog, since the retrieval can take a few seconds.
        self._update_progress_dialog(0)
        self.pdlg.show()

        logging.debug("redrawing map")

        # 1) STORE COORDINATES OF NON-MAP OBJECTS IN LAT/LON.
        # (Currently none.)
        self._start_redraw_worker(kwargs_update)

    def get_crs(self):
        """Get the coordinate reference system of the displayed map.
        """
        return self.plotter.map.crs

    def getBBOX(self):
        """
        Get the bounding box of the map
        (returns a 4-tuple llx, lly, urx, ury) in degree or meters.
        """
        return self.plotter.getBBOX()

    def clear_figure(self):
        logging.debug("Removing image")
        self.plotter.clear_figure()

    def draw_image(self, img):
        self.plotter.draw_image(img)

    def draw_legend(self, img):
        """Draw the legend graphics img on the current plot.
        Adds new axes to the plot that accommodate the legend.
        """
        self.plotter.draw_legend(img)
        # Force an immediate repaint without pumping arbitrary queued events.
        self.draw()
        self.repaint()

    def update_flightpath_legend(self, flightpath_dict):
        """
        Update the flight path legend.
        flightpath_dict: Dictionary where keys are flighttrack names, and values are tuples with (color, linestyle).
        """
        self.plotter.draw_flightpath_legend(flightpath_dict)

    def plot_satellite_overpass(self, segments):
        """Plots a satellite track on top of the map.
        """
        # If track is currently plotted on the map, remove it.
        for segment in self.satoverpasspatch:
            segment.remove()
        self.satoverpasspatch = []

        if segments:
            # Create a new patch.
            self.satoverpasspatch = [
                mpl_map.SatelliteOverpassPatch(self.map, segment)
                for segment in segments]
        self.draw()

    def plot_kml(self, kmloverlay):
        """Plots a satellite track on top of the map.
        """
        self.kmloverlay = kmloverlay

    def plot_multiple_flightpath(self, multiple_flightpath):
        """Plots a multiple flightpaths on topview of the map
        """
        self.multiple_flightpath = multiple_flightpath

    def set_settings(self, settings, save=False):
        """Apply settings from dictionary 'settings_dict' to the view.

        If settings is None, apply default settings.
        """
        if settings is None:
            # Default value if not present
            settings = self.plotter.get_settings()
            settings.setdefault("line_thickness", 2)
            settings.setdefault("line_style", "Solid")
            settings.setdefault("line_transparency", 1.0)
            settings.setdefault("colour_ft_vertices", "blue")
            settings.setdefault("colour_ft_waypoints", "red")
            settings.setdefault("draw_marker", True)
            settings.setdefault("draw_flighttrack", True)
            settings.setdefault("label_flighttrack", True)

        self.plotter.set_settings(settings, save)
        settings = self.get_settings()
        if self.waypoints_interactor is not None:
            wpi_plotter = self.waypoints_interactor.plotter
            wpi_plotter.set_path_color(line_color=settings["colour_ft_vertices"],
                                       marker_facecolor=settings["colour_ft_waypoints"])
            wpi_plotter.show_marker = settings["draw_marker"]
            wpi_plotter.set_vertices_visible(settings["draw_flighttrack"])
            wpi_plotter.set_labels_visible(settings["label_flighttrack"])
            wpi_plotter.set_line_thickness(settings["line_thickness"])
            wpi_plotter.set_line_style(settings["line_style"])
            wpi_plotter.set_line_transparency(
                settings["line_transparency"] / 100.0 if settings["line_transparency"] > 1 else settings[
                    "line_transparency"])  # Normalize the (transparency) value
        self.draw()

    def set_remote_sensing_appearance(self, settings):
        wpi_plotter = self.waypoints_interactor.plotter
        wpi_plotter.set_remote_sensing(settings["reference"])
        wpi_plotter.set_tangent_visible(settings["draw_tangents"])
        wpi_plotter.set_solar_angle_visible(settings["show_solar_angle"])

        self.waypoints_interactor.redraw_path()


class MplTopViewWidget(MplNavBarWidget):
    """MplNavBarWidget using an MplSideViewCanvas as the Matplotlib
       view instance.
    """

    def __init__(self, parent=None):
        super().__init__(
            sideview=False, parent=parent, canvas=MplTopViewCanvas())
        # Disable some elements of the Matplotlib navigation toolbar.
        # Available actions: Home, Back, Forward, Pan, Zoom, Subplots,
        #                    Customize, Save
        actions = self.navbar.actions()
        for action in actions:
            if action.text() in ["Subplots", "Customize"]:
                action.setEnabled(False)
