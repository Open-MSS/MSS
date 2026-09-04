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

import types

from mslib.msui import hexagon_dockwidget as hex_dock
from mslib.msui import performance_settings as perfset
from PyQt5 import QtWidgets, QtGui
from mslib.msui.qt5 import ui_tableview_window as ui
from mslib.utils.qt import dropEvent, dragEnterEvent
from mslib.msui import flighttrack as ft
from mslib.msui.viewwindows import MSUIViewWindow
from mslib.msui.icons import icons

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

        # Tooltip of <cbShowLinearData> while it is usable, a different one
        # explains the greyed out checkbox.
        self.show_linear_data_tooltip = self.cbShowLinearData.toolTip()
        # Whether the user wants the data columns. The checkbox itself only
        # shows them where a linear view provides data, this remembers the
        # wish across flight tracks that have none.
        self.show_linear_data_wanted = False
        # Guards the checkbox against taking a state set by this window for
        # the wish of the user.
        self._updating_show_linear_data = False

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
        self.cbShowLinearData.toggled.connect(self.setLinearDataVisible)
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

    def setLinearDataVisible(self, visible):
        """
        Handler for the <cbShowLinearData> checkbox. Shows or hides the
        columns with the data values of the linear view.
        """
        if not self._updating_show_linear_data:
            self.show_linear_data_wanted = visible
        self.waypoints_model.set_linear_data_visible(visible)

    def update_linear_data(self):
        """
        Slot called when the data retrieved by the linear view has changed.
        The values are not part of the flight plan, hence the model does not
        emit dataChanged() for them and the table has to be repainted here.
        """
        self.update_show_linear_data_enabled()
        self.tableWayPoints.viewport().update()
        self.resizeColumns()

    def update_show_linear_data_enabled(self):
        """
        Match the <cbShowLinearData> checkbox to the data of the active flight
        track. As long as no linear view provides data for it there is nothing
        to show, hence the checkbox is unchecked and greyed out; a tick without
        data columns would be misleading. The wish of the user is remembered,
        so the columns of a flight track reappear as soon as the linear view
        has data for it, e.g. after switching back and forth between tracks.
        """
        available = len(self.waypoints_model.linear_data_columns) > 0
        # The checkbox passes the change on to the flight track (toggled).
        self._updating_show_linear_data = True
        try:
            self.cbShowLinearData.setChecked(available and self.show_linear_data_wanted)
        finally:
            self._updating_show_linear_data = False
        self.cbShowLinearData.setEnabled(available)
        self.cbShowLinearData.setToolTip(
            self.show_linear_data_tooltip if available else
            "No linear view provides data values for this flight track")

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

        return bool(condition)

    def update_roundtrip_enabled(self):
        self.btRoundtrip.setEnabled(self.is_roundtrip_possible())

    def resizeColumns(self):
        for column in range(self.waypoints_model.columnCount()):
            self.tableWayPoints.resizeColumnToContents(column)

    def setFlightTrackModel(self, model):
        """
        Set the QAbstractItemModel instance that the table displays.
        """
        previous = self.waypoints_model
        super().setFlightTrackModel(model)
        if previous is not None and previous is not self.waypoints_model:
            # Stop listening to the flight track that is not displayed here
            # any more, otherwise the connections pile up on every switch.
            for signal, slot in ((previous.dataChanged, self.update_roundtrip_enabled),
                                 (previous.linearDataChanged, self.update_linear_data)):
                try:
                    signal.disconnect(slot)
                except (TypeError, RuntimeError):
                    pass
        self.tableWayPoints.setModel(self.waypoints_model)

        # Automatically enable or disable roundtrip when data changes
        self.waypoints_model.dataChanged.connect(self.update_roundtrip_enabled)
        self.update_roundtrip_enabled()

        self.waypoints_model.linearDataChanged.connect(self.update_linear_data)
        if previous is None or previous is self.waypoints_model:
            # Adopt what the flight track already shows, another table view
            # of the same track may have switched the data columns on.
            self.show_linear_data_wanted = self.waypoints_model.linear_data_visible
        else:
            # The wish of the user applies to the flight track that becomes
            # the active one, its data is what the linear view retrieved for
            # that track. The checkbox follows below, ticked only if there is
            # data to show.
            self.waypoints_model.set_linear_data_visible(self.show_linear_data_wanted)
        self.update_show_linear_data_enabled()
        self.resizeColumns()

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
