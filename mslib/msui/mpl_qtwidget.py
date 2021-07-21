# -*- coding: utf-8 -*-
"""

    mslib.msui.mpl_qtwidget
    ~~~~~~~~~~~~~~~~~~~~~~~

    Definitions of Matplotlib widgets for Qt Designer.

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

# Parts of the code have been adapted from Chapter 6 of Sandro Tosi,
# 'Matplotlib for Python Developers'.

from datetime import datetime
import enum
import os
import six
import logging
import numpy as np
import matplotlib
from fs import open_fs
from fslib.fs_filepicker import getSaveFileNameAndFilter
from matplotlib import cbook, figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT, FigureCanvasQTAgg
import matplotlib.backend_bases
from mslib import thermolib
from mslib.utils import config_loader, FatalUserError
from mslib.msui import mpl_pathinteractor as mpl_pi
from mslib.msui import mpl_map
from mslib.msui.icons import icons
from PyQt5 import QtCore, QtWidgets, QtGui
from mslib.utils import convert_pressure_to_vertical_axis_measure

PIL_IMAGE_ORIGIN = "upper"
LAST_SAVE_DIRECTORY = config_loader(dataset="data_dir")

matplotlib.rcParams['savefig.directory'] = LAST_SAVE_DIRECTORY


class MplCanvas(FigureCanvasQTAgg):
    """Class to represent the FigureCanvasQTAgg widget.

    Main axes instance has zorder 99 (important when additional
    axes are added).
    """

    def __init__(self):
        # setup Matplotlib Figure and Axis
        self.fig = figure.Figure(facecolor="w")  # 0.75
        self.ax = self.fig.add_subplot(111, zorder=99)
        self.default_filename = "_image"

        # initialization of the canvas
        super(MplCanvas, self).__init__(self.fig)

        # we define the widget as expandable
        super(MplCanvas, self).setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # notify the system of updated policy
        super(MplCanvas, self).updateGeometry()

    def get_default_filename(self):
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
        if style:
            title += f" ({style})"
        if level:
            title += f" at {level}"
            self.default_filename += f"_{level.split()[0]}"
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
        self.draw()
        # without the repaint the title is not properly updated
        self.repaint()

    def get_plot_size_in_px(self):
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
        super(MplWidget, self).__init__(parent)

        # set the canvas to the Matplotlib widget
        self.canvas = MplCanvas()

        # create a vertical box layout
        self.vbl = QtWidgets.QVBoxLayout()

        # add mpl widget to vertical box
        self.vbl.addWidget(self.canvas)

        # set the layout to th vertical box
        self.setLayout(self.vbl)


def _getSaveFileName(parent, title="Choose a filename to save to", filename="test.png",
                     filters=" Images (*.png)"):
    _dirname, _name = os.path.split(filename)
    _dirname = os.path.join(_dirname, "")
    return getSaveFileNameAndFilter(parent, fs_url=_dirname, file_pattern=filters,
                                    title=title, default_filename=_name, show_save_action=True)


save_figure_original = NavigationToolbar2QT.save_figure


def save_figure(self, *args):
    picker_type = config_loader(dataset="filepicker_default")
    if picker_type in ["default", "qt"]:
        save_figure_original(self, *args)
    elif picker_type == "fs":
        filetypes = self.canvas.get_supported_filetypes_grouped()
        sorted_filetypes = sorted(six.iteritems(filetypes))
        startpath = matplotlib.rcParams.get('savefig.directory', LAST_SAVE_DIRECTORY)
        startpath = os.path.expanduser(startpath)
        start = os.path.join(startpath, self.canvas.get_default_filename())
        filters = []
        for name, exts in sorted_filetypes:
            exts_list = " ".join(['*.%s' % ext for ext in exts])
            filter = '%s (%s)' % (name, exts_list)
            filters.append(filter)

        fname, filter = _getSaveFileName(self.parent,
                                         title="Choose a filename to save to",
                                         filename=start, filters=filters)
        if fname is not None:
            if not fname.endswith(filter[1:]):
                fname = filter.replace('*', fname)
            if startpath == '':
                # explicitly missing key or empty str signals to use cwd
                matplotlib.rcParams['savefig.directory'] = startpath
            else:
                # save dir for next time
                savefig_dir = os.path.dirname(six.text_type(fname))
                matplotlib.rcParams['savefig.directory'] = savefig_dir
            try:
                _dirname, _name = os.path.split(fname)
                _fs = open_fs(_dirname)
                with _fs.open(_name, 'wb') as source:
                    self.canvas.print_figure(source, format=filter.replace('*.', ''))
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Error saving file", six.text_type(e),
                    QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.NoButton)
    else:
        raise FatalUserError(f"Unknown file picker type '{picker_type}'")


# Patch matplotlib function
NavigationToolbar2QT.save_figure = save_figure


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
        super(NavigationToolbar, self).__init__(canvas, parent, coordinates)
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
            return super(NavigationToolbar, self)._icon(name, *args)

    def _zoom_pan_handler(self, event):
        """
        extend zoom_pan_handler of base class with our own tools
        """
        super(NavigationToolbar, self)._zoom_pan_handler(event)
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
            super(NavigationToolbar, self).push_current()
        elif self.no_push_history:
            pass
        else:
            self._nav_stack.push(self.canvas.map.kwargs.copy())
            self.set_history_buttons()

    def _update_view(self):
        """
        Update the viewlim and position from the view and position stack for
        each axes.
        """
        if self.sideview:
            super(NavigationToolbar, self)._update_view()
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
        super(NavigationToolbar, self).release_zoom(event)
        self.no_push_history = False
        self.canvas.redraw_map()
        self.push_current()

    def release_pan(self, event):
        self.no_push_history = True
        super(NavigationToolbar, self).release_pan(event)
        self.no_push_history = False
        self.canvas.redraw_map()
        self.push_current()

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
                self.set_message(f"lat={lat: <6.2f} lon={lon: <7.2f} altitude={alt/100: <.2f}hPa")
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
                    self.canvas.settings_dict["vertical_axis"], event.ydata)
                self.set_message(f"{self.mode} lat={lat:6.2f} lon={lon:7.2f} altitude={y_value:.2f}")

    def _update_buttons_checked(self):
        super(NavigationToolbar, self)._update_buttons_checked()
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
        super(MplNavBarWidget, self).__init__(parent)

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
    _pres_maj = np.concatenate([np.arange(top * 10, top, -top) for top in (10000, 1000, 100, 10)] + [[10]])
    _pres_min = np.concatenate([np.arange(top * 10, top, -top // 10) for top in (10000, 1000, 100, 10)] + [[10]])

    _pres_maj = np.concatenate([np.arange(top * 10, top, -top) for top in (10000, 1000, 100, 10)] + [[10]])
    _pres_min = np.concatenate([np.arange(top * 10, top, -top // 10) for top in (10000, 1000, 100, 10)] + [[10]])

    def __init__(self, model=None, settings=None, numlabels=None):
        """
        Arguments:
        model -- WaypointsTableModel defining the vertical section.
        """
        if numlabels is None:
            numlabels = config_loader(dataset='num_labels')
        super(MplSideViewCanvas, self).__init__()

        # Default settings.
        self.settings_dict = {"vertical_extent": (1050, 180),
                              "vertical_axis": "pressure",
                              "secondary_axis": "no secondary axis",
                              "plot_title_size": "default",
                              "axes_label_size": "default",
                              "flightlevels": [],
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
        if settings is not None:
            self.settings_dict.update(settings)

        # Setup the plot.
        self.update_vertical_extent_from_settings(init=True)

        self.numlabels = numlabels
        self.ax2 = self.ax.twinx()
        self.ax.patch.set_facecolor("None")
        self.ax2.patch.set_facecolor("None")
        # Main axes instance of mplwidget has zorder 99.
        self.imgax = self.fig.add_axes(
            self.ax.get_position(), frameon=True, xticks=[], yticks=[], label="imgax", zorder=0)

        # Sets the default value of sideview fontsize settings from MSSDefaultConfig.
        self.sideview_size_settings = config_loader(dataset="sideview")
        self.setup_side_view()
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
        if model:
            self.set_waypoints_model(model)

        self.set_settings(self.settings_dict)

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
                self.ax, self.waypoints_model,
                numintpoints=config_loader(dataset="num_interpolation_points"),
                redraw_xaxis=self.redraw_xaxis, clear_figure=self.clear_figure
            )

    def _determine_ticks_labels(self, typ):
        if typ == "no secondary axis":
            major_ticks = []
            minor_ticks = []
            labels = []
            ylabel = ""
        elif typ == "pressure":
            # Compute the position of major and minor ticks. Major ticks are labelled.
            major_ticks = self._pres_maj[(self._pres_maj <= self.p_bot) & (self._pres_maj >= self.p_top)]
            minor_ticks = self._pres_min[(self._pres_min <= self.p_bot) & (self._pres_min >= self.p_top)]
            labels = [f"{int(_x / 100)}"
                      if (_x / 100) - int(_x / 100) == 0 else f"{float(_x / 100)}" for _x in major_ticks]
            if len(labels) > 20:
                labels = ["" if x.split(".")[-1][0] in "975" else x for x in labels]
            elif len(labels) > 10:
                labels = ["" if x.split(".")[-1][0] in "9" else x for x in labels]
            ylabel = "pressure (hPa)"
        elif typ == "pressure altitude":
            bot_km = thermolib.pressure2flightlevel(self.p_bot) * 0.03048
            top_km = thermolib.pressure2flightlevel(self.p_top) * 0.03048
            ma_dist, mi_dist = 4, 1.0
            if (top_km - bot_km) <= 20:
                ma_dist, mi_dist = 1, 0.5
            elif (top_km - bot_km) <= 40:
                ma_dist, mi_dist = 2, 0.5
            major_heights = np.arange(0, top_km + 1, ma_dist)
            minor_heights = np.arange(0, top_km + 1, mi_dist)
            major_ticks = thermolib.flightlevel2pressure_a(major_heights / 0.03048)
            minor_ticks = thermolib.flightlevel2pressure_a(minor_heights / 0.03048)
            labels = major_heights
            ylabel = "pressure altitude (km)"
        elif typ == "flight level":
            bot_km = thermolib.pressure2flightlevel(self.p_bot) * 0.03048
            top_km = thermolib.pressure2flightlevel(self.p_top) * 0.03048
            ma_dist, mi_dist = 50, 10
            if (top_km - bot_km) <= 10:
                ma_dist, mi_dist = 20, 10
            elif (top_km - bot_km) <= 40:
                ma_dist, mi_dist = 40, 10
            major_fl = np.arange(0, 2132, ma_dist)
            minor_fl = np.arange(0, 2132, mi_dist)
            major_ticks = thermolib.flightlevel2pressure_a(major_fl)
            minor_ticks = thermolib.flightlevel2pressure_a(minor_fl)
            labels = major_fl
            ylabel = "flight level (hft)"
        else:
            raise RuntimeError(f"Unsupported vertical axis type: '{typ}'")
        return ylabel, major_ticks, minor_ticks, labels

    def redraw_yaxis(self):
        """ Redraws the y-axis on map after setting the values from sideview options dialog box
        and also updates the sizes for map title and x and y axes labels and ticklabels"""

        vaxis = self.settings_dict["vertical_axis"]
        vaxis2 = self.settings_dict["secondary_axis"]

        # Sets fontsize value for x axis ticklabel.
        axes_label_size = (self.sideview_size_settings["axes_label_size"]
                           if self.settings_dict["axes_label_size"] == "default"
                           else int(self.settings_dict["axes_label_size"]))
        # Sets fontsize value for plot title and axes title/label
        plot_title_size = (self.sideview_size_settings["plot_title_size"]
                           if self.settings_dict["plot_title_size"] == "default"
                           else int(self.settings_dict["plot_title_size"]))
        # Updates the fontsize of the x-axis ticklabels of sideview.
        self.ax.tick_params(axis='x', labelsize=axes_label_size)
        # Updates the fontsize of plot title and x-axis title of sideview.
        self.ax.set_title("vertical flight profile", fontsize=plot_title_size, horizontalalignment="left", x=0)
        self.ax.set_xlabel("lat/lon", fontsize=plot_title_size)

        for ax, typ in zip((self.ax, self.ax2), (vaxis, vaxis2)):
            ylabel, major_ticks, minor_ticks, labels = self._determine_ticks_labels(typ)

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

    def setup_side_view(self):
        """Set up a vertical section view.

        Vertical cross section code (log-p axis etc.) taken from
        mss_batch_production/visualisation/mpl_vsec.py.
        """

        self.ax.set_title("vertical flight profile", horizontalalignment="left", x=0)
        self.ax.grid(b=True)

        self.ax.set_xlabel("lat/lon")

        for ax in (self.ax, self.ax2):
            ax.set_yscale("log")
            ax.set_ylim(self.p_bot, self.p_top)

        self.redraw_yaxis()

    def clear_figure(self):
        logging.debug("path of side view has changed.. removing invalidated "
                      "image (if existent) and redrawing.")
        if self.image is not None:
            self.image.remove()
            self.image = None
            self.ax.set_title("vertical flight profile", horizontalalignment="left", x=0)
            self.ax.figure.canvas.draw()

    def redraw_xaxis(self, lats, lons, times):
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

        if self.waypoints_model is not None and self.waypoints_model.performance_settings["visible"]:
            self.ax.set_xticklabels([f'{d[0]:2.1f}, {d[1]:2.1f}\n{d[2].strftime("%H:%M")}Z'
                                     for d in zip(lats[::tick_index_step],
                                                  lons[::tick_index_step],
                                                  times[::tick_index_step])],
                                    rotation=25, horizontalalignment="right")
        else:
            self.ax.set_xticklabels([f"{d[0]:2.1f}, {d[1]:2.1f}"
                                     for d in zip(lats[::tick_index_step],
                                                  lons[::tick_index_step],
                                                  times[::tick_index_step])],
                                    rotation=25, horizontalalignment="right")

        for _line in self.ceiling_alt:
            _line.remove()
        self.ceiling_alt = []
        if self.waypoints_model is not None and self.waypoints_interactor is not None:
            vertices = self.waypoints_interactor.pathpatch.get_path().vertices
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

                self.ceiling_alt = self.ax.plot(
                    xs, thermolib.flightlevel2pressure_a(np.asarray(ys)),
                    color="k", ls="--")
                self.update_ceiling(
                    self.settings_dict["draw_ceiling"] and self.waypoints_model.performance_settings["visible"],
                    self.settings_dict["colour_ceiling"])

            # Remove all vertical lines
            vertical_lines = [line for line in self.ax.lines if
                              all(x == line.get_path().vertices[0, 0] for x in line.get_path().vertices[:, 0])]
            for line in vertical_lines:
                self.ax.lines.remove(line)

            # Add vertical lines
            if self.settings_dict["draw_verticals"]:
                ipoint = 0
                highlight = [[wp.lat, wp.lon] for wp in self.waypoints_model.waypoints]
                for i, (lat, lon) in enumerate(zip(lats, lons)):
                    if (ipoint < len(highlight) and
                            np.hypot(lat - highlight[ipoint][0],
                                     lon - highlight[ipoint][1]) < 2E-10):
                        self.ax.axvline(i, color='k', linewidth=2, linestyle='--', alpha=0.5)
                        ipoint += 1

        self.draw()

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
        ax = self.ax
        for level in self.flightlevels:
            pressure = thermolib.flightlevel2pressure(level)
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

    def get_settings(self):
        """Returns a dictionary containing settings regarding the side view
           appearance.
        """
        return self.settings_dict

    def set_settings(self, settings):
        """Apply settings to view.
        """
        vertical_lines = self.settings_dict["draw_verticals"]
        if settings is not None:
            self.settings_dict.update(settings)
        settings = self.settings_dict
        self.set_flight_levels(settings["flightlevels"])
        self.set_flight_levels_visible(settings["draw_flightlevels"])
        self.update_ceiling(
            settings["draw_ceiling"] and (
                self.waypoints_model is not None and
                self.waypoints_model.performance_settings["visible"]),
            settings["colour_ceiling"])
        self.update_vertical_extent_from_settings()

        if self.waypoints_interactor is not None:
            self.waypoints_interactor.line.set_marker("o" if settings["draw_marker"] else None)
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

        if self.waypoints_model is not None and self.waypoints_interactor is not None \
                and settings["draw_verticals"] != vertical_lines:
            self.redraw_xaxis(self.waypoints_interactor.path.ilats, self.waypoints_interactor.path.ilons,
                              self.waypoints_interactor.path.itimes)

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
        bbox = (num_interpolation_points, (axis[2] / 100),
                num_labels, (axis[3] / 100))
        return bbox

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
        self.draw()
        logging.debug("done.")

    def update_vertical_extent_from_settings(self, init=False):
        """ Checks for current units of axis and convert the upper and lower limit
        to pa(pascals) for the internal computation by code """

        if not init:
            p_bot_old = self.p_bot
            p_top_old = self.p_top

        if self.settings_dict["vertical_axis"] == "pressure altitude":
            self.p_bot = thermolib.flightlevel2pressure(self.settings_dict["vertical_extent"][0] * 32.80)
            self.p_top = thermolib.flightlevel2pressure(self.settings_dict["vertical_extent"][1] * 32.80)
        elif self.settings_dict["vertical_axis"] == "flight level":
            self.p_bot = thermolib.flightlevel2pressure(self.settings_dict["vertical_extent"][0])
            self.p_top = thermolib.flightlevel2pressure(self.settings_dict["vertical_extent"][1])
        else:
            self.p_bot = self.settings_dict["vertical_extent"][0] * 100
            self.p_top = self.settings_dict["vertical_extent"][1] * 100

        if not init:
            if (p_bot_old != self.p_bot) or (p_top_old != self.p_top):
                if self.image is not None:
                    self.image.remove()
                    self.image = None
                self.setup_side_view()
                self.waypoints_interactor.redraw_figure()
            else:
                self.redraw_yaxis()


class MplSideViewWidget(MplNavBarWidget):
    """MplNavBarWidget using an MplSideViewCanvas as the Matplotlib
       view instance.
    """

    def __init__(self, parent=None):
        super(MplSideViewWidget, self).__init__(
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
        super(MplLinearViewCanvas, self).__init__()

        self.settings_dict = {"plot_title_size": "default",
                              "axes_label_size": "default"}

        # Setup the plot.
        self.numlabels = numlabels
        self.setup_linear_view()
        # If a waypoints model has been passed, create an interactor on it.
        self.waypoints_interactor = None
        self.waypoints_model = None
        self.basename = "linearview"
        self.draw()
        if model:
            self.set_waypoints_model(model)

        # Sets the default values of plot sizes from MissionSupportDefaultConfig.
        self.linearview_size_settings = config_loader(dataset="linearview")
        self.set_settings(self.settings_dict)

    def set_waypoints_model(self, model):
        """Set the WaypointsTableModel defining the linear section.
        If no model had been set before, create a new interactor object on the model
        """
        self.waypoints_model = model
        pass
        if self.waypoints_interactor:
            self.waypoints_interactor.set_waypoints_model(model)
        else:
            # Create a path interactor object. The interactor object connects
            # itself to the change() signals of the flight track data model.
            self.waypoints_interactor = mpl_pi.LPathInteractor(
                self.ax, self.waypoints_model,
                numintpoints=config_loader(dataset="num_interpolation_points"),
                clear_figure=self.clear_figure,
                redraw_xaxis=self.redraw_xaxis
            )
        self.redraw_xaxis()
        # self.set_settings(self.settings_dict)

    def setup_linear_view(self):
        """Set up a linear section view.
        """
        self.fig.subplots_adjust(left=0.08, right=0.96, top=0.9, bottom=0.14)

    def clear_figure(self):
        logging.debug("path of linear view has changed.. removing invalidated plots")
        self.ax.figure.clf()
        self.ax = self.fig.add_subplot(111, zorder=99)
        self.ax.figure.patch.set_visible(False)

    def getBBOX(self):
        """Get the bounding box of the view.
        """
        # Get the number of (great circle) interpolation points and the
        # number of labels along the x-axis.
        if self.waypoints_interactor is not None:
            num_interpolation_points = \
                self.waypoints_interactor.get_num_interpolation_points()

        # Return a tuple (num_interpolation_points) as BBOX.
        bbox = (num_interpolation_points,)
        return bbox

    def draw_legend(self, img):
        if img is not None:
            logging.error("Legends not supported in LinearView mode!")
            raise NotImplementedError

    def redraw_xaxis(self):
        """Redraw the x-axis of the linear view on path changes.
        """
        if self.waypoints_interactor is not None:
            lats = self.waypoints_interactor.path.ilats
            lons = self.waypoints_interactor.path.ilons
            logging.debug("redrawing x-axis")

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

            ipoint = 0
            highlight = [[wp.lat, wp.lon] for wp in self.waypoints_model.waypoints]
            for i, (lat, lon) in enumerate(zip(lats, lons)):
                if (ipoint < len(highlight) and
                        np.hypot(lat - highlight[ipoint][0],
                                 lon - highlight[ipoint][1]) < 2E-10):
                    self.ax.axvline(i, color='k', linewidth=2, linestyle='--', alpha=0.5)
                    ipoint += 1
            self.draw()

    def draw_image(self, xmls, colors=None, scales=None):
        self.clear_figure()
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
        self.redraw_xaxis()
        self.fig.tight_layout()
        self.fig.subplots_adjust(top=0.85, bottom=0.20)
        # self.set_settings(self.settings_dict)
        self.draw()

    def get_settings(self):
        """Returns a dictionary containing settings regarding the linear view
           appearance.
        """
        return self.settings_dict

    def set_settings(self, settings):
        """
        Apply settings from options ui to the linear view
        """

        if settings is not None:
            self.settings_dict.update(settings)

        pts = (self.linearview_size_settings["plot_title_size"] if self.settings_dict["plot_title_size"] == "default"
               else int(self.settings_dict["plot_title_size"]))
        als = (self.linearview_size_settings["axes_label_size"] if self.settings_dict["axes_label_size"] == "default"
               else int(self.settings_dict["axes_label_size"]))
        self.ax.tick_params(axis='both', labelsize=als)
        self.ax.set_title("Linear flight profile", fontsize=pts, horizontalalignment='left', x=0)
        self.draw()


class MplLinearViewWidget(MplNavBarWidget):
    """MplNavBarWidget using an MplLinearViewCanvas as the Matplotlib
       view instance.
    """

    def __init__(self, parent=None):
        super(MplLinearViewWidget, self).__init__(
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
        super(MplTopViewCanvas, self).__init__()
        self.waypoints_interactor = None
        self.satoverpasspatch = []
        self.kmloverlay = None
        self.map = None
        self.basename = "topview"

        # Axes and image object to display the legend graphic, if available.
        self.legax = None
        self.legimg = None

        # stores the  topview plot title size(tov_pts) and topview axes label size(tov_als),initially as None.
        self.tov_pts = None
        self.tov_als = None
        # Sets the default fontsize parameters' values for topview from MSSDefaultConfig.
        self.topview_size_settings = config_loader(dataset="topview")

        # Set map appearance from parameter or, if not specified, to default
        # values.
        self.set_map_appearance(settings)

        # Progress dialog to inform the user about map redraws.
        self.pdlg = QtWidgets.QProgressDialog("redrawing map...", "Cancel", 0, 10, self)
        self.pdlg.close()

    def init_map(self, model=None, **kwargs):
        """Set up the map view.
        """
        ax = self.ax
        self.map = mpl_map.MapCanvas(appearance=self.get_map_appearance(),
                                     resolution="l", area_thresh=1000., ax=ax,
                                     **kwargs)

        # Sets the selected fontsize only if draw_graticule box from topview options is checked in.
        if self.appearance_settings["draw_graticule"]:
            try:
                self.map._draw_auto_graticule(self.tov_als)
            except Exception as ex:
                logging.error("ERROR: cannot plot graticule (message: %s - '%s')", type(ex), ex)
        else:
            self.map.set_graticule_visible(self.appearance_settings["draw_graticule"])

        ax.set_autoscale_on(False)
        ax.set_title("Top view", fontsize=self.tov_pts, horizontalalignment="left", x=0)
        self.draw()  # necessary?

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
            appearance = self.get_map_appearance()
            if appearance["draw_airports"]:
                self.map.set_draw_airports(True, port_type=appearance["airport_type"])
            if appearance["draw_airspaces"]:
                self.map.set_draw_airspaces(True, (appearance["filter_from"], appearance["filter_to"])
                                            if appearance["filter_airspaces"] else None)
            try:
                self.waypoints_interactor = mpl_pi.HPathInteractor(
                    self.map, self.waypoints_model,
                    linecolor=appearance["colour_ft_vertices"],
                    markerfacecolor=appearance["colour_ft_waypoints"],
                    show_marker=appearance["draw_marker"])
                self.waypoints_interactor.set_vertices_visible(appearance["draw_flighttrack"])
            except IOError as err:
                logging.error("%s" % err)

    def redraw_map(self, kwargs_update=None):
        """Redraw map canvas.

        Executed on clicked() of btMapRedraw.

        See MapCanvas.update_with_coordinate_change(). After the map redraw,
        coordinates of all objects overlain on the map have to be updated.
        """
        # remove legend
        self.draw_legend(None)

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

        # Sets the graticule ticklabels/labels fontsize for topview when map is redrawn.
        if self.appearance_settings["draw_graticule"]:
            self.map.set_graticule_visible(False)
            self.map._draw_auto_graticule(self.tov_als)
        else:
            self.map.set_graticule_visible(self.appearance_settings["draw_graticule"])
        if self.appearance_settings["draw_airports"]:
            self.map.set_draw_airports(True, port_type=self.appearance_settings["airport_type"])
        else:
            self.map.set_draw_airports(False)
        if self.appearance_settings["draw_airspaces"]:
            self.map.set_draw_airspaces(True, (self.appearance_settings["filter_from"],
                                               self.appearance_settings["filter_to"])
                                        if self.appearance_settings["filter_airspaces"] else None)
        else:
            self.map.set_draw_airspaces(False)
        self.draw()  # this one is required to trigger a
        # drawevent to update the background
        # in waypoints_interactor()

        self.pdlg.setValue(5)
        QtWidgets.QApplication.processEvents()

        # 3) UPDATE COORDINATES OF NON-MAP OBJECTS.
        self.pdlg.setValue(8)
        QtWidgets.QApplication.processEvents()

        for segment in self.satoverpasspatch:
            segment.update()

        if self.kmloverlay:
            self.kmloverlay.update()

        # self.draw_metadata() ; It is not needed here, since below here already plot title is being set.

        # Setting fontsize for topview plot title when map is redrawn.
        self.ax.set_title("Top view", fontsize=self.tov_pts, horizontalalignment='left', x=0)
        self.draw()
        self.repaint()

        # Update in case of a projection change
        self.waypoints_interactor.update()

        self.pdlg.setValue(10)
        QtWidgets.QApplication.processEvents()

        logging.debug("finished redrawing map")
        self.pdlg.close()

        # Emit signal so other parts of the module can react to a redraw event.
        self.redrawn.emit()

    def get_crs(self):
        """Get the coordinate reference system of the displayed map.
        """
        return self.map.crs

    def getBBOX(self):
        """
        Get the bounding box of the map
        (returns a 4-tuple llx, lly, urx, ury) in degree or meters.
        """

        axis = self.ax.axis()

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
                # self.legax.set_yticklabels("ax2", fontsize=32, minor=False)
                # print("Legax=if" + self.legax)

            # If axes exist, adjust their position.
            else:
                self.legax.set_position([1 - ax_extent_x, 0.01, ax_extent_x, ax_extent_y])
                # self.legax.set_yticklabels("ax2", fontsize=32, minor=False)
                # print("Legax=else" + self.legax)
            # Plot the new legimg in the legax axes.
            self.legimg = self.legax.imshow(img, origin=PIL_IMAGE_ORIGIN, aspect="equal", interpolation="nearest")
            # print("Legimg" + self.legimg)
        self.draw()
        # required so that it is actually drawn...
        QtWidgets.QApplication.processEvents()

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

    def set_map_appearance(self, settings_dict):
        """Apply settings from dictionary 'settings_dict' to the view.

        If settings is None, apply default settings.
        """
        # logging.debug("applying map appearance settings %s." % settings)
        settings = {"draw_graticule": True,
                    "draw_coastlines": True,
                    "fill_waterbodies": True,
                    "fill_continents": True,
                    "draw_flighttrack": True,
                    "draw_marker": True,
                    "draw_airports": False,
                    "airport_type": "small_airport",
                    "draw_airspaces": False,
                    "filter_airspaces": False,
                    "filter_from": 0,
                    "filter_to": 100,
                    "label_flighttrack": True,
                    "tov_plot_title_size": "default",
                    "tov_axes_label_size": "default",
                    "colour_water": ((153 / 255.), (255 / 255.), (255 / 255.), (255 / 255.)),
                    "colour_land": ((204 / 255.), (153 / 255.), (102 / 255.), (255 / 255.)),
                    "colour_ft_vertices": (0, 0, 1, 1),
                    "colour_ft_waypoints": (1, 0, 0, 1)}
        if settings_dict is not None:
            settings.update(settings_dict)

        # Stores the exact value of fontsize for topview plot title size(tov_pts)
        self.tov_pts = (self.topview_size_settings["plot_title_size"] if settings["tov_plot_title_size"] == "default"
                        else int(settings["tov_plot_title_size"]))
        # Stores the exact value of fontsize for topview axes label size(tov_als)
        self.tov_als = (self.topview_size_settings["axes_label_size"] if settings["tov_axes_label_size"] == "default"
                        else int(settings["tov_axes_label_size"]))

        self.appearance_settings = settings
        ax = self.ax

        if self.map is not None:
            self.map.set_coastlines_visible(settings["draw_coastlines"])
            self.map.set_draw_airports(settings["draw_airports"], port_type=settings["airport_type"])
            self.map.set_draw_airspaces(settings["draw_airspaces"], (settings["filter_from"], settings["filter_to"])
                                        if settings["filter_airspaces"] else None)
            self.map.set_fillcontinents_visible(visible=settings["fill_continents"],
                                                land_color=settings["colour_land"],
                                                lake_color=settings["colour_water"])
            self.map.set_mapboundary_visible(visible=settings["fill_waterbodies"],
                                             bg_color=settings["colour_water"])
            self.waypoints_interactor.set_path_color(line_color=settings["colour_ft_vertices"],
                                                     marker_facecolor=settings["colour_ft_waypoints"])
            self.waypoints_interactor.show_marker = settings["draw_marker"]
            self.waypoints_interactor.set_vertices_visible(settings["draw_flighttrack"])
            self.waypoints_interactor.set_labels_visible(settings["label_flighttrack"])

            # Updates plot title size as selected from combobox labelled plot title size.
            ax.set_autoscale_on(False)
            ax.set_title("Top view", fontsize=self.tov_pts, horizontalalignment="left", x=0)

            # Updates graticule ticklabels/labels fontsize if draw_graticule is True.
            if settings["draw_graticule"]:
                self.map.set_graticule_visible(False)
                self.map._draw_auto_graticule(self.tov_als)
            else:
                self.map.set_graticule_visible(settings["draw_graticule"])
            self.draw()

    def set_remote_sensing_appearance(self, settings):
        self.waypoints_interactor.set_remote_sensing(settings["reference"])
        self.waypoints_interactor.set_tangent_visible(settings["draw_tangents"])
        self.waypoints_interactor.set_solar_angle_visible(settings["show_solar_angle"])

        self.waypoints_interactor.redraw_path()

    def get_map_appearance(self):
        """
        """
        return self.appearance_settings


class MplTopViewWidget(MplNavBarWidget):
    """MplNavBarWidget using an MplSideViewCanvas as the Matplotlib
       view instance.
    """

    def __init__(self, parent=None):
        super(MplTopViewWidget, self).__init__(
            sideview=False, parent=parent, canvas=MplTopViewCanvas())
        # Disable some elements of the Matplotlib navigation toolbar.
        # Available actions: Home, Back, Forward, Pan, Zoom, Subplots,
        #                    Customize, Save
        actions = self.navbar.actions()
        for action in actions:
            if action.text() in ["Subplots", "Customize"]:
                action.setEnabled(False)
