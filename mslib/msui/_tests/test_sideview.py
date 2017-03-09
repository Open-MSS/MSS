# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_sideview
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.sideview

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017 by the mss team, see AUTHORS.
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


import sys
from mslib.msui.mss_qt import QtWidgets, QtTest
from mslib.msui import flighttrack as ft
from mslib._tests.utils import close_modal_messagebox
import mslib.msui.sideview as tv


class Test_MSSSideViewWindow(object):
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        initial_waypoints = [ft.Waypoint(40., 25., 300), ft.Waypoint(60., -10., 400), ft.Waypoint(40., 10, 300)]

        waypoints_model = ft.WaypointsTableModel("")
        waypoints_model.insertRows(
            0, rows=len(initial_waypoints), waypoints=initial_waypoints)

        self.window = tv.MSSSideViewWindow(model=waypoints_model)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowShown(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    def test_open_wms(self):
        self.window.cbTools.currentIndexChanged.emit(1)
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)
