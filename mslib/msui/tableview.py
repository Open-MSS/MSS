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
from mslib.utils import view_restoration
from mslib.utils.config import config_loader
from mslib.msui import flighttrack as ft

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

        self.hexagon_center_lon = 0.0
        self.hexagon_center_lat = 0.0
        self.hexagon_radius = 200.0
        self.hexagon_angle = 0.0
        self.hexagon_direction = "clockwise"

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
        self.active_flighttrack = model
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
        """Return a dictionary of all Table View settings."""
        try:
            performance_settings = {}
            dock_states = [False, False]
            column_widths = {}
            hexagon_settings = {
                "center_lon": getattr(self, 'hexagon_center_lon', 0.0),
                "center_lat": getattr(self, 'hexagon_center_lat', 0.0),
                "radius": getattr(self, 'hexagon_radius', 200.0),
                "angle": getattr(self, 'hexagon_angle', 0.0),
                "direction": getattr(self, 'hexagon_direction', "clockwise")
            }

            # Performance settings
            if hasattr(self, 'waypoints_model') and self.waypoints_model:
                raw_perf = getattr(self.waypoints_model, 'performance_settings', {})
                if isinstance(raw_perf, dict):
                    try:
                        performance_settings = view_restoration.serialize_settings(raw_perf)
                        for key, value in raw_perf.items():
                            if isinstance(value, QtCore.QDateTime):
                                performance_settings[key] = value.toString(QtCore.Qt.ISODate)
                    except Exception as ex:
                        logging.error("Failed to serialize performance_settings: %s", ex)
                else:
                    logging.warning("performance_settings is not a dict: %s", type(raw_perf))

            # Dock states
            if hasattr(self, 'docks') and isinstance(self.docks, list):
                dock_states = [dock.isVisible() if dock else False for dock in self.docks]

            # Column widths
            sort_column = None
            sort_order = None
            if hasattr(self, 'tableWayPoints') and self.tableWayPoints:
                model = self.tableWayPoints.model()
                if model:
                    for col in range(model.columnCount()):
                        header_data = model.headerData(col, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole)
                        header = str(header_data) if header_data else f"Column_{col}"
                        column_widths[header] = self.tableWayPoints.columnWidth(col)

                    # Sorting info (safe access)
                    try:
                        sort_col = self.tableWayPoints.horizontalHeader().sortIndicatorSection()
                        sort_order = self.tableWayPoints.horizontalHeader().sortIndicatorOrder()
                        if sort_col >= 0:
                            sort_column = model.headerData(sort_col, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole)
                    except Exception as ex:
                        logging.warning("Could not get sort column info: %s", ex)

            # Hexagon settings from widget
            try:
                if self.docks and len(self.docks) > 0 and self.docks[0] and self.docks[0].widget():
                    hex_control = self.docks[0].widget()
                    if isinstance(hex_control, hex_dock.HexagonControlWidget):
                        hexagon_settings = hex_control._get_parameters()
            except Exception as ex:
                logging.warning("Failed to collect hexagon settings: %s", ex)

            # Final settings dictionary
            settings = {
                "view_type": "tableview",
                "performance_settings": performance_settings,
                "docks_open": dock_states,
                "column_widths": column_widths,
                "hexagon": hexagon_settings,
            }
            if sort_column:
                settings["sort_column"] = str(sort_column)
                settings["sort_order"] = "ascending" if sort_order == QtCore.Qt.AscendingOrder else "descending"

            logging.debug("Collected Table View settings: %s", settings)
            return settings

        except Exception as ex:
            logging.error("Failed to get TableView settings: %s", ex)
            return {
                "view_type": "tableview",
                "performance_settings": {},
                "docks_open": [False, False],
                "column_widths": config_loader(dataset="default_table_column_widths", default={}),
                "hexagon": {
                    "center_lon": 0.0,
                    "center_lat": 0.0,
                    "radius": 200.0,
                    "angle": 0.0,
                    "direction": "clockwise"
                }
            }

    def set_settings(self, view):
        """Restore Table View settings from view_settings.json."""
        try:
            if isinstance(view, list):
                view = next((v for v in view if v.get("view_type") == "tableview"), {})

            self.docks = getattr(self, 'docks', [None, None])

            # Restore waypoints_model data
            if hasattr(self, 'waypoints_model') and self.waypoints_model:
                try:
                    for row in range(self.waypoints_model.rowCount()):
                        index = self.waypoints_model.index(
                            row, self.waypoints_model.column_index("flightlevel")
                        )
                        value = self.waypoints_model.data(index, QtCore.Qt.DisplayRole)
                        if isinstance(value, QtCore.QVariant):
                            value = value.value()
                        try:
                            flightlevel = float(value)
                        except (TypeError, ValueError):
                            logging.warning("Invalid flightlevel at row %d: %s", row, value)
                            flightlevel = 300.0
                        if flightlevel < 300:
                            self.waypoints_model.setData(index, 300.0, QtCore.Qt.EditRole)
                    self.tableWayPoints.setModel(self.waypoints_model)
                    self.resizeColumns()
                except Exception as e:
                    logging.error(
                        "Error updating waypoints in Table View: %s\n%s", str(e), traceback.format_exc()
                    )
            else:
                logging.warning("waypoints_model not initialized; skipping waypoint update")

            # Restore hexagon settings
            hexagon_settings = view.get("hexagon", {})
            if hexagon_settings:
                if self.docks[0] is None:
                    self.openTool(1)
                if self.docks[0]:
                    self.hexagon_control = self.docks[0].widget()
                    if isinstance(self.hexagon_control, hex_dock.HexagonControlWidget):
                        self.restore_hexagon_settings(hexagon_settings)
                    else:
                        logging.warning(
                            "Hexagon control widget not available; got %s", type(self.hexagon_control)
                        )
                else:
                    logging.warning("Hexagon control dock not initialized")

            # Restore performance settings
            perf = view.get("performance_settings", {})
            if self.docks[1] is None:
                self.openTool(2)
            if self.docks[1]:
                perf_ctrl = self.docks[1].widget()
                if isinstance(perf_ctrl, perfset.MSUI_PerformanceSettingsWidget):
                    try:
                        aircraft_data = perf.get(
                            "aircraft", {"name": "DUMMY", "empty_weight": 0.0, "takeoff_weight": 0.0}
                        )
                        perf_ctrl.aircraft = aircraft.SimpleAircraft(aircraft_data)
                        perf_ctrl.lbAircraftName.setText(perf_ctrl.aircraft.name)
                        perf_ctrl.cbShowPerformance.setChecked(perf.get("visible", False))
                        takeoff_weight = perf.get(
                            "takeoff_weight", aircraft_data.get("takeoff_weight", 0.0)
                        )
                        empty_weight = perf.get(
                            "empty_weight", aircraft_data.get("empty_weight", 0.0)
                        )
                        perf_ctrl.dsbTakeoffWeight.setValue(float(takeoff_weight))
                        perf_ctrl.dsbEmptyWeight.setValue(float(empty_weight))
                        takeoff_time = perf.get(
                            "takeoff_time",
                            QtCore.QDateTime.currentDateTimeUtc().toString(QtCore.Qt.ISODate)
                        )
                        if isinstance(takeoff_time, str):
                            takeoff_time = QtCore.QDateTime.fromString(takeoff_time, QtCore.Qt.ISODate)
                        perf_ctrl.dteTakeoffTime.setDateTime(
                            takeoff_time or QtCore.QDateTime.currentDateTimeUtc()
                        )
                        perf_ctrl.update_parent_performance()
                    except Exception as e:
                        logging.warning("Failed to restore performance settings: %s", str(e))
                else:
                    logging.warning("Performance settings widget not available; got %s", type(perf_ctrl))
            else:
                logging.warning("Performance settings dock not initialized")

            # Restore column widths
            column_widths = view.get("column_widths", {})
            if self.tableWayPoints and column_widths:
                model = self.tableWayPoints.model()
                if model:
                    headers = {}
                    for col in range(model.columnCount()):
                        header = model.headerData(col, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole)
                        header_str = str(header) if header is not None else f"Column_{col}"
                        headers[header_str] = col
                    for col_name, width in column_widths.items():
                        col_idx = headers.get(str(col_name))
                        if col_idx is not None:
                            try:
                                self.tableWayPoints.setColumnWidth(col_idx, int(width))
                            except Exception as e:
                                logging.warning(
                                    "Failed to set column width for %s: %s", col_name, str(e)
                                )
                        else:
                            logging.warning(
                                "Column '%s' not found in table headers: %s",
                                col_name, list(headers.keys())
                            )

            # Restore dock visibility
            docks_open = view.get("docks_open", [False, False])
            for idx, open_ in enumerate(docks_open):
                if idx < len(self.docks):
                    if open_ and self.docks[idx] is None:
                        self.openTool(idx + 1)
                    elif self.docks[idx]:
                        self.docks[idx].setVisible(open_)

            # Repaint table
            if self.tableWayPoints:
                self.tableWayPoints.viewport().repaint()

        except Exception as e:
            logging.error("Error in set_settings: %s\n%s", str(e), traceback.format_exc())

    def restore_hexagon_settings(self, hexagon_settings):
        """Restore hexagon settings into the existing HexagonControlWidget."""
        try:
            center_lon = float(hexagon_settings.get("center_lon", 0.0))
            center_lat = float(hexagon_settings.get("center_lat", 0.0))
            radius = float(hexagon_settings.get("radius", 200.0))
            angle = float(hexagon_settings.get("angle", 0.0))
            direction = str(hexagon_settings.get("direction", "clockwise"))

            self.hexagon_center_lon = center_lon
            self.hexagon_center_lat = center_lat
            self.hexagon_radius = radius
            self.hexagon_angle = angle
            self.hexagon_direction = direction

            if self.hexagon_control and isinstance(self.hexagon_control, hex_dock.HexagonControlWidget):
                if hasattr(self.hexagon_control, 'dsbHexagonLongitude'):
                    self.hexagon_control.dsbHexagonLongitude.setValue(center_lon)
                else:
                    logging.warning("Hexagon longitude spinbox 'dsbHexagonLongitude' not found")

                if hasattr(self.hexagon_control, 'dsbHexagonLatitude'):
                    self.hexagon_control.dsbHexagonLatitude.setValue(center_lat)
                else:
                    logging.warning("Hexagon latitude spinbox 'dsbHexagonLatitude' not found")

                if hasattr(self.hexagon_control, 'dsbHexgaonRadius'):
                    self.hexagon_control.dsbHexgaonRadius.setValue(radius)
                else:
                    logging.warning("Hexagon radius spinbox 'dsbHexgaonRadius' not found")

                if hasattr(self.hexagon_control, 'dsbHexagonAngle'):
                    self.hexagon_control.dsbHexagonAngle.setValue(angle)
                else:
                    logging.warning("Hexagon angle spinbox 'dsbHexagonAngle' not found")

                if hasattr(self.hexagon_control, 'cbClock'):
                    dir_text = direction if direction in ["clockwise", "counterclockwise"] else "clockwise"
                    self.hexagon_control.cbClock.setCurrentText(dir_text)
                else:
                    logging.warning("Hexagon direction combobox 'cbClock' not found")

                QtCore.QCoreApplication.processEvents()
            else:
                logging.warning(
                    "Hexagon control widget not available or incorrect type: %s",
                    type(self.hexagon_control) if self.hexagon_control else "None"
                )
        except Exception as e:
            logging.error("Error restoring hexagon settings: %s\n%s", str(e), traceback.format_exc())
