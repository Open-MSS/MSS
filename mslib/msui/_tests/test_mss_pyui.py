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
import mock
import os

from mslib.msui.mss_qt import QtWidgets, QtTest
from mslib._tests.utils import close_modal_messagebox, BASE_DIR
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

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getOpenFileName",
                return_value=os.path.join(sample_path, "example.ftml"))
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getSaveFileName",
                return_value=save_ftml)
    def test_loadsaveas_flighttrack(self, mocksave, mockopen):
        assert self.window.listFlightTracks.count() == 1
        self.window.openFlightTrack()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1
        assert mocksave.call_count == 0
        assert not close_modal_messagebox(self.window)
        self.window.saveFlightTrackAs()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1
        assert mocksave.call_count == 1
        assert not close_modal_messagebox(self.window)
        assert os.path.exists(self.save_ftml)
        # todo check for content of saved file
        os.remove(self.save_ftml)

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getOpenFileName",
                return_value=os.path.join(sample_path, "example.csv"))
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getSaveFileName",
                return_value=save_csv)
    def test_plugin_csv(self, mocksave, mockopen):
        assert self.window.listFlightTracks.count() == 1
        self.window.actionImportFlightTrackCSV()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1
        assert mocksave.call_count == 0
        assert not close_modal_messagebox(self.window)
        self.window.actionExportFlightTrackCSV()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1
        assert mocksave.call_count == 1
        assert not close_modal_messagebox(self.window)
        assert os.path.exists(self.save_csv)
        # todo check for content of saved file
        os.remove(self.save_csv)

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getOpenFileName",
                return_value=os.path.join(sample_path, "example.txt"))
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getSaveFileName",
                return_value=save_txt)
    def test_plugin_txt(self, mocksave, mockopen):
        self.window.addImportFilter("_TXT", "txt", load_from_txt)
        self.window.addExportFilter("_TXT", "txt", save_to_txt)

        assert self.window.listFlightTracks.count() == 1
        self.window.actionImportFlightTrack_TXT()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1
        assert mocksave.call_count == 0
        assert not close_modal_messagebox(self.window)
        self.window.actionExportFlightTrack_TXT()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1
        assert mocksave.call_count == 1
        assert not close_modal_messagebox(self.window)
        assert os.path.exists(self.save_txt)
        # todo check for content of saved file
        os.remove(self.save_txt)

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getOpenFileName",
                return_value=os.path.join(sample_path, "flitestar.txt"))
    def test_plugin_flitestar(self, mockopen):
        self.window.addImportFilter("_FliteStar", "txt", load_from_flitestar)
        assert self.window.listFlightTracks.count() == 1
        self.window.actionImportFlightTrack_FliteStar()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1
        assert not close_modal_messagebox(self.window)
