# -*- coding: utf-8 -*-
"""

    mslib.msui.circle_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Control widget to insert (and remove) left-turning circles of a given
    duration, approximated by a regular polygon, into a flight track.

    This file is part of MSS.

    :copyright: Copyright 2026 by the MSS team, see AUTHORS.
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
import re

import numpy as np
from pyproj import Geod
from PyQt5 import QtWidgets

from mslib.msui.qt5 import ui_circle_dockwidget as ui
from mslib.msui import flighttrack as ft
from mslib.msui.utils.qt import plain_text_as_html

_GEOD = Geod(ellps="WGS84")
_COMMENT = re.compile(r"^Circle (\d+)$")


class CircleException(Exception):
    pass


def circle_radius(tas, minutes, vertices):
    """
    Radius [km] of a regular polygon with <vertices> corners whose perimeter is
    flown in <minutes> at a true airspeed of <tas> knots.
    """
    distance = tas * 1.852 * minutes / 60.
    return distance / (2 * vertices * np.sin(np.pi / vertices))


def create_circle(lat, lon, heading, radius, vertices):
    """
    Returns the (lat, lon) corners of a left-turning regular polygon that
    starts at (lat, lon) with the given heading [deg] and has a circumscribed
    radius of <radius> km. The first corner (the starting point) is not
    included, the last returned point closes the polygon at the starting
    point, so <vertices> points are returned.
    """
    radius_m = radius * 1000.
    center_lon, center_lat, _ = _GEOD.fwd(lon, lat, heading - 90., radius_m)
    # Bearing from the center to the starting point, decreasing for a left turn.
    _, back_azimuth, _ = _GEOD.inv(lon, lat, center_lon, center_lat)
    bearings = [back_azimuth - i * 360. / vertices for i in range(1, vertices)]
    lons, lats, _ = _GEOD.fwd([center_lon] * len(bearings), [center_lat] * len(bearings),
                              bearings, [radius_m] * len(bearings))
    return list(zip(lats, lons)) + [(lat, lon)]


def inbound_heading(waypoints, row):
    """
    Heading [deg] with which the waypoint at <row> is passed: the course of the
    leg leading to it, else that of the leg leaving it, else north.
    """
    wp = waypoints[row]
    if row > 0:
        prev = waypoints[row - 1]
        _, back_azimuth, distance = _GEOD.inv(prev.lon, prev.lat, wp.lon, wp.lat)
        if distance > 0:
            return back_azimuth + 180.
    if row + 1 < len(waypoints):
        nxt = waypoints[row + 1]
        azimuth, _, distance = _GEOD.inv(wp.lon, wp.lat, nxt.lon, nxt.lat)
        if distance > 0:
            return azimuth
    return 0.


def _circle_index(comment):
    match = _COMMENT.match(str(comment))
    return int(match.group(1)) if match else None


class CircleControlWidget(QtWidgets.QWidget, ui.Ui_CircleDockWidget):
    """
    Inserts left-turning circles starting and ending at the selected waypoint.
    """

    def __init__(self, parent=None, view=None):
        super().__init__(parent)
        self.setupUi(self)
        self.view = view
        if self.view:
            self.view.tableWayPoints.selectionModel().selectionChanged.connect(self.on_selection_changed)
            self.on_selection_changed(None)

        self.pbAddCircle.clicked.connect(self._add_circle)
        self.pbRemoveCircle.clicked.connect(self._remove_circle)

    def on_selection_changed(self, index):
        """
        Disables add and remove when multiple rows are selected
        """
        enable = len(self.view.tableWayPoints.selectionModel().selectedRows()) <= 1
        self.pbAddCircle.setEnabled(enable)
        self.pbRemoveCircle.setEnabled(enable)

    def _add_circle(self):
        table_view = self.view.tableWayPoints
        waypoints_model = self.view.waypoints_model
        index = table_view.currentIndex()
        if not index.isValid():
            QtWidgets.QMessageBox.warning(
                self, "Add circle", "Please select the waypoint at which the circle shall start.")
            return
        row = index.row()
        all_waypoints = waypoints_model.all_waypoint_data()
        idx = _circle_index(all_waypoints[row].comments)
        if idx is not None and row + 1 < len(all_waypoints) and \
                _circle_index(all_waypoints[row + 1].comments) == idx + 1:
            QtWidgets.QMessageBox.warning(
                self, "Add circle", "Circles cannot be nested, please select the start or end point of a circle.")
            return
        start = waypoints_model.waypoint_data(row)
        vertices = self.sbCircleVertices.value()
        aircraft = waypoints_model.performance_settings["aircraft"]
        tas, _ = aircraft.get_cruise_performance(start.flightlevel * 100, start.weight)
        radius = circle_radius(tas, self.dsbCircleDuration.value(), vertices)
        heading = inbound_heading(all_waypoints, row)
        points = create_circle(start.lat, start.lon, heading, radius, vertices)
        waypoints = [
            ft.Waypoint(lat=float(lat), lon=float(lon), flightlevel=float(start.flightlevel),
                        comments=f"Circle {i + 1:d}")
            for i, (lat, lon) in enumerate(points)]
        waypoints_model.insertRows(row + 1, rows=len(waypoints), waypoints=waypoints, message="Circle created.")
        table_view.setCurrentIndex(waypoints_model.index(row + 1, 0))
        table_view.resizeRowsToContents()

    def _find_circle(self, row):
        """
        Returns first row and number of rows of the circle containing <row>.
        """
        waypoints = self.view.waypoints_model.all_waypoint_data()
        idx = _circle_index(waypoints[row].comments)
        if idx is None:
            raise CircleException("Cannot remove circle, please select a circle "
                                  "waypoint ('Circle x' in comments field).")
        row_min = row - (idx - 1)
        if row_min < 1 or any(_circle_index(waypoints[row_min + i].comments) != i + 1
                              for i in range(idx)):
            raise CircleException("Cannot remove circle, the circle is not complete.")
        row_max = row
        while row_max + 1 < len(waypoints) and \
                _circle_index(waypoints[row_max + 1].comments) == row_max + 2 - row_min:
            row_max += 1
        return row_min, row_max - row_min + 1

    def _remove_circle(self):
        table_view = self.view.tableWayPoints
        waypoints_model = self.view.waypoints_model
        index = table_view.currentIndex()
        try:
            if not index.isValid():
                raise CircleException("A waypoint of the circle must be selected.")
            row_min, rows = self._find_circle(index.row())
            if len(waypoints_model.all_waypoint_data()) - rows < 2:
                raise CircleException("Cannot remove circle, the flight track needs to consist "
                                      "of at least two points.")
            sel = QtWidgets.QMessageBox.question(
                table_view, "Remove circle",
                plain_text_as_html(f"This will remove waypoints {row_min:d}-{row_min + rows - 1:d}. Continue?"),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Yes)
            if sel == QtWidgets.QMessageBox.Yes:
                waypoints_model.removeRows(row_min, rows=rows, hexagonDeleted=True)
                table_view.setCurrentIndex(waypoints_model.index(row_min - 1, 0))
        except CircleException as ex:
            QtWidgets.QMessageBox.warning(self, "Remove circle", plain_text_as_html(str(ex)))
