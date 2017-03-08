# -*- coding: utf-8 -*-
"""

    mslib.msui.hexagon_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Control widget to configure remote sensing overlays.

    This file is part of mss.

    :copyright: Copyright 2016-2017 Joern Ungermann, Stefan Ensmann
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


import numpy as np

from mslib.msui.mss_qt import QtWidgets
from mslib.msui.mss_qt import ui_hexagon_dockwidget as ui
from mslib.msui import flighttrack as ft
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default
from mslib.utils import config_loader, rotate_point


class HexagonException(Exception):
    pass


def create_hexagon(center_lat, center_lon, radius, angle=0.):
    coords_0 = (radius, 0.)
    CoordsCart_0 = [rotate_point(coords_0, angle=0. + angle),
                    rotate_point(coords_0, angle=60. + angle),
                    rotate_point(coords_0, angle=120. + angle),
                    rotate_point(coords_0, angle=180. + angle),
                    rotate_point(coords_0, angle=240. + angle),
                    rotate_point(coords_0, angle=300. + angle),
                    rotate_point(coords_0, angle=360. + angle)]
    CoordsSphere_rot = [(center_lat + vec[0] / 110.,
                         center_lon + vec[1] / (110. *
                                                np.cos(np.deg2rad(vec[0] / 110. + center_lat))))
                        for vec in CoordsCart_0]
    return CoordsSphere_rot


class HexagonControlWidget(QtWidgets.QWidget, ui.Ui_HexagonDockWidget):
    """This class implements the remote sensing functionality as dockable widget.
    """

    def __init__(self, parent=None, view=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        view -- reference to mpl canvas class
        """
        super(HexagonControlWidget, self).__init__(parent)
        self.setupUi(self)
        self.view = view

        self.dsbHexgaonRadius.setValue(200)

        self.pbAddHexagon.clicked.connect(self._add_hexagon)
        self.pbRemoveHexagon.clicked.connect(self._remove_hexagon)

    def _get_parameters(self):
        return {
            "center_lon": self.dsbHexagonLongitude.value(),
            "center_lat": self.dsbHexagonLatitude.value(),
            "radius": self.dsbHexgaonRadius.value(),
            "angle": self.dsbHexagonAngle.value()
        }

    def _add_hexagon(self):
        table_view = self.view.tableWayPoints
        waypoints_model = self.view.waypoints_model
        params = self._get_parameters()

        if params["radius"] < 0.01:
            QtWidgets.QMessageBox.warning(
                self, "Add hexagon", "You cannot create a hexagon with zero radius!")
            return
        points = create_hexagon(params["center_lat"], params["center_lon"], params["radius"], params["angle"])
        index = table_view.currentIndex()
        if not index.isValid():
            row = 0
            flightlevel = config_loader(dataset="new_flighttrack_flightlevel",
                                        default=mss_default.new_flighttrack_flightlevel)
        else:
            row = index.row() + 1
            flightlevel = waypoints_model.waypointData(row - 1).flightlevel
        waypoints = []
        for i, point in enumerate(points):
            waypoints.append(
                ft.Waypoint(lon=float(round(point[1], 2)), lat=float(round(point[0], 2)),
                            flightlevel=float(flightlevel), comments="Hexagon {:d}".format(i + 1)))
        waypoints_model.insertRows(row, rows=len(waypoints), waypoints=waypoints)
        index = waypoints_model.index(row, 0)
        table_view.setCurrentIndex(index)
        table_view.resizeRowsToContents()

    def _remove_hexagon(self):
        table_view = self.view.tableWayPoints
        waypoints_model = self.view.waypoints_model

        index = table_view.currentIndex()

        try:
            if not index.isValid():
                raise HexagonException("A waypoint of the hexagon must be selected.")
            row = index.row()
            comm = unicode(waypoints_model.waypointData(row).comments)
            if len(comm) == 9 and comm.startswith("Hexagon "):
                if (len(waypoints_model.allWaypointData()) - 7) < 2:  # = 3 waypoints + 7 hexagon points
                    raise HexagonException("Cannot remove hexagon, the flight track needs to consist "
                                           "of at least two points.")
                idx = int(comm[-1])
                row_min = row - (idx - 1)
                row_max = row + (7 - idx)
                if row_min < 0 or row_max > len(waypoints_model.allWaypointData()):
                    raise HexagonException("Cannot remove hexagon, hexagon is not complete "
                                           "(min, max = {:d}, {:d})".format(row_min, row_max))
                else:
                    found_one = False
                    for i in range(0, row_max - row_min):
                        if unicode(waypoints_model.waypointData(row_min + i).comments) != "Hexagon {:d}".format(i + 1):
                            found_one = True
                            break
                    if found_one:
                        raise HexagonException("Cannot remove hexagon, hexagon comments are not found in all "
                                               "points (min, max = {:d}, {:d})".format(row_min, row_max))
                    else:
                        sel = QtWidgets.QMessageBox.question(
                            None, "Remove hexagon",
                            "This will remove waypoints {:d}-{:d}. Continue?".format(row_min, row_max),
                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                        if sel == QtWidgets.QMessageBox.Yes:
                            waypoints_model.removeRows(row_min, rows=7)
            else:
                raise HexagonException("Cannot remove hexagon, please select a hexagon "
                                       "waypoint ('Hexagon x' in comments field)")
        except HexagonException, ex:
            QtWidgets.QMessageBox.warning(self, "Remove hexagon", str(ex))
