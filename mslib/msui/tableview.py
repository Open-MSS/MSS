# -*- coding: utf-8 -*-
"""

    mslib.msui.tableview
    ~~~~~~~~~~~~~~~~~~~~

    Table view of the msui
    See the reference documentation, Supplement, for details on the
    implementation.

    To better understand of the code, look at the 'ships' example from
    chapter 14/16 of 'Rapid GUI Programming with Python and Qt: The
    Definitive Guide to PyQt Programming' (Mark Summerfield).

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2025 by the MSS team, see AUTHORS.
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

import types
import traceback
import logging
from mslib.msui import aircraft
from mslib.msui import hexagon_dockwidget as hex_dock
from mslib.msui import performance_settings as perfset
from PyQt5 import QtWidgets, QtGui
from mslib.msui.qt5 import ui_tableview_window as ui
from mslib.utils.qt import dropEvent, dragEnterEvent
from mslib.msui import flighttrack as ft
from mslib.msui.viewwindows import MSUIViewWindow
from mslib.msui.icons import icons
from PyQt5 import QtCore

try:
    import mpl_toolkits.basemap.pyproj as pyproj
except ImportError:
    import pyproj


class MSUITableViewWindow(MSUIViewWindow, ui.Ui_TableViewWindow):
    """
    Implements the table view of the flight plan. Data comes from a
    flight track data model.
    """

    name = "Table View"

    def __init__(self, parent=None, model=None, _id=None, tutorial_mode=False):
        """
        """
        super().__init__(parent, model, _id)
        self.tutorial_mode = tutorial_mode
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(icons('64x64')))
        self.settings_tag = "tableview"

        self.setFlightTrackModel(model)
        self.tableWayPoints.setItemDelegate(ft.WaypointDelegate(self))

        toolitems = ["(select to open control)", "Hexagon Control", "Performance Settings"]
        self.cbTools.clear()
        self.cbTools.addItems(toolitems)
        self.tableWayPoints.dropEvent = types.MethodType(dropEvent, self.tableWayPoints)
        self.tableWayPoints.dragEnterEvent = types.MethodType(dragEnterEvent, self.tableWayPoints)

        # Dock windows [Hexagon].
        self.docks = [None, None]

        # Connect slots and signals.
        self.btAddWayPointToFlightTrack.clicked.connect(self.addWayPoint)
        self.btCloneWaypoint.clicked.connect(self.cloneWaypoint)
        self.btDeleteWayPoint.clicked.connect(self.removeWayPoint)
        self.btInvertDirection.clicked.connect(self.invertDirection)
        self.btRoundtrip.clicked.connect(self.make_roundtrip)
        self.tableWayPoints.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # Tool opener.
        self.cbTools.currentIndexChanged.connect(self.openTool)

        self.resizeColumns()

    def setPerformance(self, settings):
        """
        Updating Table View with updated performance settings.
        """
        self.waypoints_model.performance_settings = settings
        self.waypoints_model.update_distances(0)
        self.waypoints_model.save_settings()
        self.resizeColumns()
        self.tableWayPoints.viewport().repaint()

    def on_selection_changed(self, index):
        """
        Disables insert and clone when multiple rows are selected
        """
        enable = len(self.tableWayPoints.selectionModel().selectedRows()) <= 1
        self.btCloneWaypoint.setEnabled(enable)
        self.btAddWayPointToFlightTrack.setEnabled(enable)

    def openTool(self, index):
        """
        Slot that handles requests to open tool windows.
        """
        index = self.controlToBeCreated(index)
        if index >= 0:
            if index == 0:
                title = "Hexagon Control"
                widget = hex_dock.HexagonControlWidget(view=self)
            elif index == 1:
                title = "Performance Settings"
                widget = perfset.MSUI_PerformanceSettingsWidget(
                    parent=self,
                    view=self,
                    settings_dict=self.waypoints_model.performance_settings
                )
            else:
                raise IndexError(f"invalid control index ({index})")
            self.createDockWidget(index, title, widget)

    def invertDirection(self):
        self.waypoints_model.invert_direction()

    def addWayPoint(self):
        """
        Handler for button <btAddWayPointToFlightTrack>. Adds a new waypoint
        behind the currently selected waypoint.
        """
        tableView = self.tableWayPoints
        index = tableView.currentIndex()
        lon, lat = 0, 0
        if not index.isValid():
            row = 0
            flightlevel = 0
        else:
            row = index.row() + 1
            flightlevel = self.waypoints_model.waypoint_data(row - 1).flightlevel
            if row < len(self.waypoints_model.all_waypoint_data()):
                wp_prev = self.waypoints_model.waypoint_data(row - 1)
                wp_next = self.waypoints_model.waypoint_data(row)
                gc = pyproj.Geod(ellps="WGS84")  # a=40e6, b=40e6)
                lon, lat = gc.npts(wp_prev.lon, wp_prev.lat, wp_next.lon, wp_next.lat, 3)[1]

        self.waypoints_model.insertRows(
            row, waypoints=[ft.Waypoint(lat=lat, lon=lon, flightlevel=flightlevel)])

        index = self.waypoints_model.index(row, 0)
        tableView = self.tableWayPoints
        tableView.setFocus()
        tableView.setCurrentIndex(index)
        # tableView.edit(index)
        tableView.resizeRowsToContents()

    def cloneWaypoint(self):
        """
        Handler for button <btCloneWaypoint>. Adds a new waypoint
        after the currently selected waypoint, with same data.
        """
        tableView = self.tableWayPoints
        index = tableView.currentIndex()
        lon, lat = 0, 0
        if not index.isValid():
            row = 0
            flightlevel = 0
        else:

            row = index.row() + 1
            wp = self.waypoints_model.waypoint_data(row - 1)
            lon = wp.lon
            lat = wp.lat
            flightlevel = self.waypoints_model.waypoint_data(row - 1).flightlevel

        self.waypoints_model.insertRows(
            row, waypoints=[ft.Waypoint(lat=lat, lon=lon, flightlevel=flightlevel)])

        index = self.waypoints_model.index(row, 0)
        tableView = self.tableWayPoints
        tableView.setFocus()
        tableView.setCurrentIndex(index)
        # tableView.edit(index)
        tableView.resizeRowsToContents()

    def confirm_delete_waypoint(self, rows):
        """
        Open a QMessageBox and ask the user if he really wants to
        delete the waypoint at index <row>.

        Returns TRUE if the user confirms the deletion.

        If the flight track consists of only two points deleting a waypoint
        is not possible. In this case the user is informed correspondingly.
        """
        wps = self.waypoints_model.all_waypoint_data()
        if len(wps) - len(rows) < 2:
            QtWidgets.QMessageBox.warning(
                self.tableWayPoints, "Remove waypoint",
                "Cannot remove waypoint, the flight track needs to consist of at least two points.")
            return False
        else:
            waypoints = [wps[row] for row in rows]
            text = "\n".join(
                [f"Remove waypoint at {waypoint.lat:.2f}/{waypoint.lon:.2f}, flightlevel {waypoint.flightlevel:.2f}?"
                    for waypoint in waypoints])

            return QtWidgets.QMessageBox.question(
                self.tableWayPoints, "Remove waypoint", text,
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Yes) == QtWidgets.QMessageBox.Yes

    def removeWayPoint(self):
        """
        Handler for button <btDeleteWayPoint>. Deletes the currently selected
        waypoint.
        """
        tableView = self.tableWayPoints
        indices = tableView.selectionModel().selectedRows()
        rows = [index.row() for index in indices]
        # Let the user confirm the deletion.
        if len(rows) > 0:
            if self.confirm_delete_waypoint(rows):
                for row in sorted(rows, reverse=True):
                    self.waypoints_model.removeRows(row)

    def make_roundtrip(self):
        """
        Copies the first waypoint and inserts it at the back of the list again
        Essentially creating a roundtrip
        """
        # This case should never be True for users, but might be for developers at some point
        if not self.is_roundtrip_possible():
            return

        first_waypoint = self.waypoints_model.waypoint_data(0)

        self.waypoints_model.insertRows(self.waypoints_model.rowCount(), rows=1, waypoints=[
            ft.Waypoint(lat=first_waypoint.lat, lon=first_waypoint.lon, flightlevel=first_waypoint.flightlevel,
                        location=first_waypoint.location)])

    def is_roundtrip_possible(self):
        """
        Checks if there are at least 2 waypoints, and the first and last are not the same
        """
        condition = self.waypoints_model.rowCount() > 1

        if condition:
            first_waypoint = self.waypoints_model.waypoint_data(0)
            last_waypoint = self.waypoints_model.waypoint_data(self.waypoints_model.rowCount() - 1)

            condition = first_waypoint.lat != last_waypoint.lat or first_waypoint.lon != last_waypoint.lon or \
                first_waypoint.flightlevel != last_waypoint.flightlevel

        return condition

    def update_roundtrip_enabled(self):
        self.btRoundtrip.setEnabled(self.is_roundtrip_possible())

    def resizeColumns(self):
        for column in range(self.waypoints_model.columnCount()):
            self.tableWayPoints.resizeColumnToContents(column)

    def setFlightTrackModel(self, model):
        """
        Set the QAbstractItemModel instance that the table displays.
        """
        super().setFlightTrackModel(model)
        self.tableWayPoints.setModel(self.waypoints_model)

        # Automatically enable or disable roundtrip when data changes
        self.waypoints_model.dataChanged.connect(self.update_roundtrip_enabled)
        self.update_roundtrip_enabled()

    def viewPerformance(self):
        """
        Slot to toggle the view mode of the table between 'USER' and
        'PERFORMANCE'.
        """
        # Restore the original button face colour (as inherited from this window's palette).
        self.btViewPerformance.setPalette(self.palette())
        self.tableWayPoints.setPalette(self.palette())
        self.btAddWayPointToFlightTrack.setEnabled(True)
        self.btDeleteWayPoint.setEnabled(True)
        self.resizeColumns()

    def get_settings(self):
        """Return a dictionary of all table view settings."""

        # Get performance settings from waypoints_model and convert to serializable format
        performance_settings = {}
        if hasattr(self, 'waypoints_model') and self.waypoints_model is not None:
            raw_performance = self.waypoints_model.performance_settings or {}
            for key, value in raw_performance.items():
                # Serialize objects like SimpleAircraft
                if hasattr(value, '__dict__'):
                    performance_settings[key] = {
                        attr: getattr(value, attr)
                        for attr in dir(value)
                        if not attr.startswith('_') and isinstance(
                            getattr(value, attr),
                            (str, int, float, bool, list, dict, type(None))
                        )
                    }
                else:
                    performance_settings[key] = value

        # Get waypoints
        waypoints = []
        if hasattr(self, 'waypoints_model') and self.waypoints_model is not None:
            for wp in self.waypoints_model.waypoints:
                waypoints.append({
                    "lat": wp.lat,
                    "lon": wp.lon,
                    "flightlevel": wp.flightlevel,
                    "location": wp.location,
                    "comments": wp.comments
                })

        # Get dock widget states
        dock_states = []
        if hasattr(self, 'docks'):
            dock_states = [dock is not None and dock.isVisible() for dock in self.docks]

        # Get column widths for table layout
        column_widths = {}
        if hasattr(self, 'tableWayPoints') and self.tableWayPoints:
            model = self.tableWayPoints.model()
            if model:
                for col in range(model.columnCount()):
                    header_text = model.headerData(col, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole)
                    if header_text:
                        column_widths[str(header_text)] = self.tableWayPoints.columnWidth(col)
                    else:
                        column_widths[f"Column_{col}"] = self.tableWayPoints.columnWidth(col)

        return {
            "view_type": "tableview",
            "performance_settings": performance_settings,
            "waypoints": waypoints,
            "docks_open": dock_states,
            "column_widths": column_widths,
        }

    def set_settings(self, view):
        """
        Restore Table View settings from view_settings.json.
        """
        try:
            # Extract settings dict
            view_settings = None
            if isinstance(view, list):
                view_settings = next((v for v in view if v.get("view_type") == "tableview"), {})
                if not view_settings:
                    logging.warning("No tableview settings found; using defaults")
            else:
                view_settings = view or {}

            # Restore hexagon params
            hexagon_params = view_settings.get("hexagon_parameters")
            if hexagon_params and hasattr(self, 'docks'):
                if self.docks[0] is None:
                    self.openTool(1)
                if self.docks[0]:
                    hex_control = self.docks[0].widget()
                    if isinstance(hex_control, hex_dock.HexagonControlWidget):
                        hex_control.dsbHexagonLongitude.setValue(float(hexagon_params.get("center_lon", 0.0)))
                        hex_control.dsbHexagonLatitude.setValue(float(hexagon_params.get("center_lat", 0.0)))
                        hex_control.dsbHexgaonRadius.setValue(float(hexagon_params.get("radius", 200.0)))
                        hex_control.dsbHexagonAngle.setValue(float(hexagon_params.get("angle", 0.0)))
                        dir_text = str(hexagon_params.get("direction", "clockwise"))
                        hex_control.cbClock.setCurrentText(dir_text if dir_text in ["clockwise", "counterclockwise"] else "clockwise")

            # Restore performance settings
            perf = view_settings.get("performance_settings", {})
            if hasattr(self, 'docks'):
                if self.docks[1] is None:
                    self.openTool(2)
                if self.docks[1]:
                    perf_ctrl = self.docks[1].widget()
                    if perf_ctrl:
                        aircraft_data = perf.get("aircraft", {})
                        try:
                            perf_ctrl.aircraft = aircraft.SimpleAircraft(aircraft_data)
                        except Exception:
                            perf_ctrl.aircraft = aircraft.SimpleAircraft(aircraft.AIRCRAFT_DUMMY)
                        perf_ctrl.lbAircraftName.setText(perf_ctrl.aircraft.name)
                        perf_ctrl.cbShowPerformance.setChecked(perf.get("visible", False))
                        perf_ctrl.dsbTakeoffWeight.setValue(float(perf.get("takeoff_weight", 0.0)))
                        perf_ctrl.dsbEmptyWeight.setValue(float(perf.get("empty_weight", 0.0)))
                        takeoff_time = perf.get("takeoff_time") or QtCore.QDateTime.currentDateTimeUtc()
                        perf_ctrl.dteTakeoffTime.setDateTime(takeoff_time)
                        perf_ctrl.update_parent_performance()

            # Restore waypoints
            waypoints = view_settings.get("waypoints", [])
            if waypoints and hasattr(self, 'waypoints_model'):
                valid = []
                for wp in waypoints:
                    if all(isinstance(wp.get(k), (int, float)) for k in ("lat", "lon")):
                        valid.append(ft.Waypoint(
                            lat=wp["lat"], lon=wp["lon"],
                            flightlevel=wp.get("flightlevel", 0),
                            location=wp.get("location", ""), comments=wp.get("comments", "")
                        ))
                if valid:
                    self.waypoints_model.removeRows(0, self.waypoints_model.rowCount())
                    self.waypoints_model.insertRows(0, rows=len(valid), waypoints=valid)
                    if hasattr(self, 'tableWayPoints') and self.tableWayPoints:
                        self.tableWayPoints.setModel(self.waypoints_model)
                        self.resizeColumns()

            # Restore column widths
            column_widths = view_settings.get("column_widths", {})
            if hasattr(self, 'tableWayPoints') and self.tableWayPoints and column_widths:
                model = self.tableWayPoints.model()
                if model:
                    headers = {
                            str(model.headerData(c, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole)): c
                            for c in range(model.columnCount())
                            }

                    for col_name, width in column_widths.items():
                        col_idx = headers.get(col_name)
                        if col_idx is not None:
                            self.tableWayPoints.setColumnWidth(col_idx, width)

            # Restore dock visibility
            docks_open = view_settings.get("docks_open", [])
            if hasattr(self, 'docks'):
                for idx, open_ in enumerate(docks_open):
                    if idx < len(self.docks):
                        if open_ and self.docks[idx] is None:
                            self.openTool(idx + 1)
                        elif self.docks[idx]:
                            self.docks[idx].setVisible(open_)

            logging.debug("Finished restoring Table View settings")
        except Exception as e:
            logging.error("Error in set_settings: %s\n%s", str(e), traceback.format_exc())
