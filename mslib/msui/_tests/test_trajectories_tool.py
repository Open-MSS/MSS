# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_trajectory_tool
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.trajectories_tool

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


import os
import sys
import mock
from mslib.msui.mss_qt import QtWidgets, QtTest, QtCore
import mslib.msui.trajectories_tool as tt
import mslib.msui.mss_pyui as mss_pyui


class Test_TrajectoriesTool(object):
    sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "samples")

    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.listViews = mock.Mock()
        self.listTools = mock.Mock()
        self.listViews.findItems = mock.Mock(side_effect=lambda x, y: [])
        self.listTools.findItems = mock.Mock(side_effect=lambda x, y: [])
        self.window = tt.MSSTrajectoriesToolWindow(listviews=self.listViews, listtools=self.listTools)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowShown(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox.critical")
    def test_show(self, mockcrit):
        assert mockcrit.call_count == 0

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getExistingDirectory",
                return_value=os.path.join(sample_path, "trajectories"))
    def test_load_trajectories(self, mockopen, mockcrit):
        self.window.actionOpenTrajectories.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockopen.call_count == 1
        assert mockcrit.critical.call_count == 0

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getOpenFileName",
                return_value=os.path.join(sample_path, "nas", "sample.nas"))
    def test_load_nas(self, mockopen, mockcrit):
        self.window.actionOpenFlightTrack.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockopen.call_count == 1
        assert mockcrit.critical.call_count == 0

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getOpenFileName",
                return_value=os.path.join(sample_path, "kml", "line.kml"))
    def test_load_nas_kml(self, mockopen, mockcrit):
        self.window.actionOpenFlightTrack.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockopen.call_count == 1
        assert mockcrit.critical.call_count == 1


class Test_TrajectoryToolComples(object):
    sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "samples")

    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)

        self.window = mss_pyui.MSSMainWindow()
        self.window.createNewFlightTrack(activate=True)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowShown(self.window)
        QtWidgets.QApplication.processEvents()
        self.window.actionTopView.trigger()
        QtWidgets.QApplication.processEvents()
        self.window.actionTrajectoryToolLagranto.trigger()
        QtWidgets.QApplication.processEvents()
        self.topview = self.window.listViews.item(0).window
        self.trajtool = self.window.listTools.item(0).window

    def teardown(self):
        for i in range(self.window.listViews.count()):
            self.window.listViews.item(i).window.hide()
        for i in range(self.window.listTools.count()):
            self.window.listTools.item(i).window.hide()
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getOpenFileName",
                return_value=os.path.join(sample_path, "nas", "sample.nas"))
    def test_show_nas(self, mockopen, mockcrit):
        self.trajtool.actionOpenFlightTrack.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockopen.call_count == 1
        assert mockcrit.critical.call_count == 0
        self.trajtool.cbPlotInView.setCurrentIndex(1)
        QtWidgets.QApplication.processEvents()
        root = self.trajtool.traj_item_tree.getRootItem()
        flighttrack = self.trajtool.tvVisibleElements.visualRect(
            self.trajtool.traj_item_tree.createIndex(0, 0, root.childItems[0].childItems[0]))
        QtTest.QTest.mouseClick(
            self.trajtool.tvVisibleElements.viewport(),
            QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, flighttrack.center())
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.trajtool.btPlotInView, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert mockcrit.critical.call_count == 0

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getExistingDirectory",
                return_value=os.path.join(sample_path, "trajectories"))
    def test_show_trajectories(self, mockopen, mockcrit):
        self.trajtool.actionOpenTrajectories.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockopen.call_count == 1
        assert mockcrit.critical.call_count == 0
        self.trajtool.cbPlotInView.setCurrentIndex(1)
        QtWidgets.QApplication.processEvents()
        root = self.trajtool.traj_item_tree.getRootItem()
        self.trajtool.tvVisibleElements.expandAll()
        flighttrack = self.trajtool.tvVisibleElements.visualRect(
            self.trajtool.traj_item_tree.createIndex(0, 0, root.childItems[1].childItems[0].childItems[0]))
        QtTest.QTest.mouseClick(
            self.trajtool.tvVisibleElements.viewport(),
            QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, flighttrack.center())
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.trajtool.btPlotInView, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert mockcrit.critical.call_count == 0
