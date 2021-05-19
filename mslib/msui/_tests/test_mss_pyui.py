# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mss_pyui
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.mss_pyui

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2021 by the mss team, see AUTHORS.
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
from urllib.request import urlopen
from PyQt5 import QtWidgets, QtTest
from mslib import __version__
from mslib._tests.constants import ROOT_DIR
import mslib.msui.mss_pyui as mss_pyui
from mslib.plugins.io.text import load_from_txt, save_to_txt
from mslib.plugins.io.flitestar import load_from_flitestar


class Test_MSS_AboutDialog():
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = mss_pyui.MSS_AboutDialog()

    def test_milestone_url(self):
        with urlopen(self.window.milestone_url) as f:
            text = f.read()
        pattern = f'value="is:closed milestone:{__version__[:-1]}"'
        assert pattern in text.decode('utf-8')

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()


class Test_MSSSideViewWindow(object):
    sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "samples", "flight-tracks")
    save_csv = os.path.join(ROOT_DIR, "example.csv")
    save_ftml = os.path.join(ROOT_DIR, "example.ftml")
    save_ftml = save_ftml.replace('\\', '/')
    save_txt = os.path.join(ROOT_DIR, "example.txt")

    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)

        self.window = mss_pyui.MSSMainWindow()
        self.window.create_new_flight_track()
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        for i in range(self.window.listViews.count()):
            self.window.listViews.item(i).window.hide()
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_app_start(self, mockbox):
        assert mockbox.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_new_flightrack(self, mockbox):
        assert self.window.listFlightTracks.count() == 1
        self.window.actionNewFlightTrack.trigger()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockbox.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_open_topview(self, mockbox):
        assert self.window.listViews.count() == 0
        self.window.actionTopView.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        assert self.window.listViews.count() == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_open_sideview(self, mockbox):
        assert self.window.listViews.count() == 0
        self.window.actionSideView.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        assert self.window.listViews.count() == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_open_tableview(self, mockbox):
        assert self.window.listViews.count() == 0
        self.window.actionTableView.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        assert self.window.listViews.count() == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_open_about(self, mockbox):
        self.window.actionAboutMSUI.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0

    @mock.patch("mslib.msui.mss_pyui.get_save_filename", return_value=save_ftml)
    def test_plugin_ftml_saveas(self, mocksave):
        assert self.window.listFlightTracks.count() == 1
        assert mocksave.call_count == 0
        self.window.last_save_directory = ROOT_DIR
        self.window.actionSaveActiveFlightTrackAs.trigger()
        QtWidgets.QApplication.processEvents()
        assert mocksave.call_count == 1
        assert os.path.exists(self.save_ftml)
        os.remove(self.save_ftml)

    @mock.patch("mslib.msui.mss_pyui.get_open_filename", return_value=os.path.join(sample_path, u"example.csv"))
    def test_plugin_csv_read(self, mockopen):
        assert self.window.listFlightTracks.count() == 1
        assert mockopen.call_count == 0
        self.window.last_save_directory = self.sample_path
        self.window.actionImportFlightTrackCSV()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1

    @mock.patch("mslib.msui.mss_pyui.get_save_filename", return_value=save_csv)
    def test_plugin_csv_write(self, mocksave):
        assert self.window.listFlightTracks.count() == 1
        assert mocksave.call_count == 0
        self.window.last_save_directory = ROOT_DIR
        self.window.actionExportFlightTrackCSV()
        assert mocksave.call_count == 1
        assert os.path.exists(self.save_csv)
        os.remove(self.save_csv)

    @mock.patch("mslib.msui.mss_pyui.get_open_filename", return_value=os.path.join(sample_path, u"example.txt"))
    def test_plugin_txt_read(self, mockopen):
        self.window.add_import_filter("_TXT", "txt", load_from_txt)
        assert self.window.listFlightTracks.count() == 1
        assert mockopen.call_count == 0
        self.window.last_save_directory = self.sample_path
        self.window.actionImportFlightTrack_TXT()
        assert mockopen.call_count == 1
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2

    @mock.patch("mslib.msui.mss_pyui.get_save_filename", return_value=save_txt)
    def test_plugin_txt_write(self, mocksave):
        self.window.add_export_filter("_TXT", "txt", save_to_txt)
        self.window.last_save_directory = ROOT_DIR
        self.window.actionExportFlightTrack_TXT()
        assert mocksave.call_count == 1
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 1
        assert os.path.exists(self.save_txt)
        os.remove(self.save_txt)

    @mock.patch("mslib.msui.mss_pyui.get_open_filename",
                return_value=os.path.join(sample_path, u"flitestar.txt"))
    def test_plugin_flitestar(self, mockopen):
        self.window.last_save_directory = self.sample_path
        self.window.add_import_filter("_FliteStar", "txt", load_from_flitestar)
        assert self.window.listFlightTracks.count() == 1
        self.window.actionImportFlightTrack_FliteStar()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1
