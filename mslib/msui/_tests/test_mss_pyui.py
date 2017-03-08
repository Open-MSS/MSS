# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mss_pyui
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.mss_pyui

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
from mslib.msui.mss_qt import QtWidgets, QtTest, QtCore
from mslib._tests.utils import close_modal_messagebox
import mslib.msui.mss_pyui as mss_pyui


class Test_MSSSideViewWindow(object):
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)

        self.window = mss_pyui.MSSMainWindow()
        self.window.createNewFlightTrack(activate=True)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowShown(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        del self.window

    def test_app_start(self):
        assert not close_modal_messagebox(self.window)

    def test_new_flightrack(self):
        assert self.window.listFlightTracks.count() == 1
        self.window.actionNewFlightTrack.trigger()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert not close_modal_messagebox(self.window)

    def test_open_topview(self):
        assert self.window.listViews.count() == 0
        self.window.actionTopView.trigger()
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)
        assert self.window.listViews.count() == 1

    def test_open_sideview(self):
        assert self.window.listViews.count() == 0
        self.window.actionSideView.trigger()
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)
        assert self.window.listViews.count() == 1

    def test_open_tableview(self):
        assert self.window.listViews.count() == 0
        self.window.actionTableView.trigger()
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)
        assert self.window.listViews.count() == 1

    def test_open_trajectory_tool(self):
        assert self.window.listTools.count() == 0
        self.window.actionTrajectoryToolLagranto.trigger()
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)
        assert self.window.listTools.count() == 1

    def test_open_timeseries_tool(self):
        assert self.window.listTools.count() == 0
        self.window.actionTimeSeriesViewTrajectories.trigger()
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)
        assert self.window.listTools.count() == 1

    def test_open_loopview_tool(self):
        assert self.window.listTools.count() == 0
        self.window.actionLoopView.trigger()
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)
        assert self.window.listTools.count() == 1

    def test_open_about(self):
        self.window.actionAboutMSUI.trigger()
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)

