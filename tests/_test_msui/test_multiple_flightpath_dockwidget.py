# -*- coding: utf-8 -*-
"""

    _tests._test_msui.test_multiple_flightpath_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tesst for the MultipleFlightpathControlWidget

    This file is part of MSS.

    :copyright: Copyright 2023 Reimar Bauer
    :copyright: Copyright 2023-2024 by the MSS team, see AUTHORS.
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
import pytest
from PyQt5 import QtTest
from mslib.msui import msui
from mslib.msui.multiple_flightpath_dockwidget import MultipleFlightpathControlWidget
from mslib.msui import flighttrack as ft
import mslib.msui.topview as tv


class Test_MultipleFlightpathControlWidget:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.window = msui.MSUIMainWindow()
        self.window.create_new_flight_track()

        self.window.actionNewFlightTrack.trigger()
        self.window.actionTopView.trigger()
        initial_waypoints = [ft.Waypoint(40., 25., 0), ft.Waypoint(60., -10., 0), ft.Waypoint(40., 10, 0)]
        self.waypoints_model = ft.WaypointsTableModel("myname")
        self.waypoints_model.insertRows(
            0, rows=len(initial_waypoints), waypoints=initial_waypoints)

        self.widget = tv.MSUITopViewWindow(model=self.waypoints_model, mainwindow=self.window, parent=self.window)
        self.window.show()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        yield
        self.window.hide()

    def test_initialization(self):
        widget = MultipleFlightpathControlWidget(parent=self.widget,
                                                 listFlightTracks=self.window.listFlightTracks)
        assert widget.color == (0, 0, 1, 1)
