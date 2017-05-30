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


from builtins import range
from builtins import object
import sys
import mock
import os

from mslib.msui.mss_qt import QtWidgets, QtTest, QtCore
from mslib._tests.utils import BASE_DIR
import mslib.msui.mss_pyui as mss_pyui
from mslib.plugins.io.text import load_from_txt, save_to_txt
from mslib.plugins.io.flitestar import load_from_flitestar


class Test_MSSSideViewWindow(object):
    sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "samples", "flight-tracks")
    save_csv = os.path.join(BASE_DIR, "example.csv")
    save_ftml = os.path.join(BASE_DIR, "example.ftml")
    save_txt = os.path.join(BASE_DIR, "example.txt")

    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)

        self.window = mss_pyui.MSSMainWindow()
        self.window.createNewFlightTrack(activate=True)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        try:
            QtTest.QTest.qWaitForWindowExposed(self.window)
        except AttributeError:
            QtTest.QTest.qWaitForWindowShown(self.window)
        QtWidgets.QApplication.processEvents()

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
    def test_app_start(self, mockbox):
        assert mockbox.critical.call_count == 0

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_new_flightrack(self, mockbox):
        assert self.window.listFlightTracks.count() == 1
        self.window.actionNewFlightTrack.trigger()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockbox.critical.call_count == 0

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_open_topview(self, mockbox):
        assert self.window.listViews.count() == 0
        self.window.actionTopView.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        assert self.window.listViews.count() == 1

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_open_sideview(self, mockbox):
        assert self.window.listViews.count() == 0
        self.window.actionSideView.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        assert self.window.listViews.count() == 1

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_open_tableview(self, mockbox):
        assert self.window.listViews.count() == 0
        self.window.actionTableView.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        assert self.window.listViews.count() == 1

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_open_trajectory_tool(self, mockbox):
        assert self.window.listTools.count() == 0
        self.window.actionTrajectoryToolLagranto.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        assert self.window.listTools.count() == 1

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_open_timeseries_tool(self, mockbox):
        assert self.window.listTools.count() == 0
        self.window.actionTimeSeriesViewTrajectories.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        assert self.window.listTools.count() == 1

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_open_loopview_tool(self, mockbox):
        assert self.window.listTools.count() == 0
        self.window.actionLoopView.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        assert self.window.listTools.count() == 1

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_open_about(self, mockbox):
        self.window.actionAboutMSUI.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getOpenFileName",
                return_value=os.path.join(sample_path, "example.ftml"))
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getSaveFileName",
                return_value=save_ftml)
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox.question",
                return_value=QtWidgets.QMessageBox.Yes)
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox.warning",
                return_value=QtWidgets.QMessageBox.Yes)
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox.information")
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox.critical")
    def test_loadsaveas_flighttrack(self, mockcrit, mockinfo, mockwarn, mockques, mocksave, mockopen):
        assert self.window.listFlightTracks.count() == 1
        self.window.actionOpenFlightTrack.trigger()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1
        assert mocksave.call_count == 0
        assert mockcrit.call_count == 0
        self.window.actionSaveActiveFlightTrackAs.trigger()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1
        assert mocksave.call_count == 1
        assert mockcrit.call_count == 0
        assert os.path.exists(self.save_ftml)
        os.remove(self.save_ftml)
        self.window.actionSaveActiveFlightTrack.trigger()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1
        assert mocksave.call_count == 1
        assert mockcrit.call_count == 0
        assert os.path.exists(self.save_ftml)
        os.remove(self.save_ftml)
        self.window.actionCloseSelectedFlightTrack.trigger()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1
        assert mocksave.call_count == 1
        assert mockcrit.call_count == 0
        assert mockinfo.call_count == 1
        assert not os.path.exists(self.save_ftml)
        flighttrack = self.window.listFlightTracks.visualItemRect(
            self.window.listFlightTracks.item(0))
        QtTest.QTest.mouseClick(
            self.window.listFlightTracks.viewport(),
            QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, flighttrack.center())
        QtWidgets.QApplication.processEvents()
        self.window.actionCloseSelectedFlightTrack.trigger()
        assert self.window.listFlightTracks.count() == 1
        assert mockopen.call_count == 1
        assert mocksave.call_count == 1
        assert mockcrit.call_count == 0
        assert mockinfo.call_count == 1

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getOpenFileName",
                return_value=os.path.join(sample_path, "example.csv"))
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getSaveFileName",
                return_value=save_csv)
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_plugin_csv(self, mockbox, mocksave, mockopen):
        assert self.window.listFlightTracks.count() == 1
        self.window.actionImportFlightTrackCSV()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1
        assert mocksave.call_count == 0
        assert mockbox.critical.call_count == 0
        self.window.actionExportFlightTrackCSV()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1
        assert mocksave.call_count == 1
        assert mockbox.critical.call_count == 0
        assert os.path.exists(self.save_csv)
        # todo check for content of saved file
        os.remove(self.save_csv)

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getOpenFileName",
                return_value=os.path.join(sample_path, "example.txt"))
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getSaveFileName",
                return_value=save_txt)
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_plugin_txt(self, mockbox, mocksave, mockopen):
        self.window.addImportFilter("_TXT", "txt", load_from_txt)
        self.window.addExportFilter("_TXT", "txt", save_to_txt)

        assert self.window.listFlightTracks.count() == 1
        self.window.actionImportFlightTrack_TXT()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1
        assert mocksave.call_count == 0
        assert mockbox.critical.call_count == 0
        self.window.actionExportFlightTrack_TXT()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1
        assert mocksave.call_count == 1
        assert mockbox.critical.call_count == 0
        assert os.path.exists(self.save_txt)
        # todo check for content of saved file
        os.remove(self.save_txt)

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getOpenFileName",
                return_value=os.path.join(sample_path, "flitestar.txt"))
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_plugin_flitestar(self, mockbox, mockopen):
        self.window.addImportFilter("_FliteStar", "txt", load_from_flitestar)
        assert self.window.listFlightTracks.count() == 1
        self.window.actionImportFlightTrack_FliteStar()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1
        assert mockbox.critical.call_count == 0
