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
import fs
import os
import pytest
from urllib.request import urlopen
from PyQt5 import QtWidgets, QtTest
from mslib import __version__
from mslib._tests.constants import ROOT_DIR
import mslib.msui.mss_pyui as mss_pyui
from mslib._tests.utils import ExceptionMock


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


class Test_MSS_ShortcutDialog():
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.main_window = mss_pyui.MSSMainWindow()
        self.main_window.show()
        self.shortcuts = mss_pyui.MSS_ShortcutsDialog()

    def teardown(self):
        self.shortcuts.hide()
        self.main_window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    def test_shortcuts_present(self):
        # Assert list gets filled properly
        self.shortcuts.fill_list()
        assert self.shortcuts.treeWidget.topLevelItemCount() == 1
        self.shortcuts.filter_shortcuts("Nothing")
        assert self.shortcuts.treeWidget.topLevelItem(0).isHidden()

        # Assert changing display type works
        self.shortcuts.cbAdvanced.click()
        old_text = self.shortcuts.treeWidget.topLevelItem(0).child(1).text(0)
        self.shortcuts.cbDisplayType.setCurrentIndex(2)
        assert self.shortcuts.treeWidget.topLevelItem(0).child(1).text(0) != old_text

        # Assert double clicking works
        self.shortcuts.cbNoShortcut.setCheckState(True)
        self.shortcuts.leShortcutFilter.setText("actionConfiguration")
        for i in range(self.shortcuts.treeWidget.topLevelItem(0).childCount()):
            child = self.shortcuts.treeWidget.topLevelItem(0).child(i)
            if not child.isHidden():
                self.shortcuts.double_clicked(child)
                self.shortcuts.fill_list()
                break
        assert self.shortcuts.treeWidget.topLevelItemCount() == 2


class Test_MSSSideViewWindow(object):
    # temporary file paths to test open feature
    sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "samples", "flight-tracks")
    open_csv = os.path.join(sample_path, "example.csv")
    open_ftml = os.path.join(sample_path, "example.ftml")
    open_txt = os.path.join(sample_path, "example.txt")
    open_fls = os.path.join(sample_path, "flitestar.txt")
    # temporary file paths to test save feature
    save_csv = os.path.join(ROOT_DIR, "example.csv")
    save_ftml = os.path.join(ROOT_DIR, "example.ftml")
    save_ftml = save_ftml.replace('\\', '/')
    save_txt = os.path.join(ROOT_DIR, "example.txt")
    # import/export plugins
    import_plugins = {
        "Text": ["txt", "mslib.plugins.io.text", "load_from_txt"],
        "FliteStar": ["fls", "mslib.plugins.io.flitestar", "load_from_flitestar"],
    }
    export_plugins = {
        "Text": ["txt", "mslib.plugins.io.text", "save_to_txt"],
        # "KML": ["kml", "mslib.plugins.io.kml", "save_to_kml"],
        # "GPX": ["gpx", "mslib.plugins.io.gpx", "save_to_gpx"]
    }

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

    def test_no_updater(self):
        assert not hasattr(self.window, "updater")

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
    def test_open_linearview(self, mockbox):
        assert self.window.listViews.count() == 0
        self.window.actionLinearView.trigger()
        self.window.listViews.itemActivated.emit(self.window.listViews.item(0))
        QtWidgets.QApplication.processEvents()
        assert self.window.listViews.count() == 1
        assert mockbox.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_open_about(self, mockbox):
        self.window.actionAboutMSUI.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_open_config(self, mockbox):
        pytest.skip("To be done")
        self.window.actionConfigurationEditor.trigger()
        QtWidgets.QApplication.processEvents()
        self.window.config_editor.close()
        assert mockbox.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_open_shortcut(self, mockbox):
        self.window.actionShortcuts.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0

    @pytest.mark.parametrize("save_file", [[save_ftml], [save_csv], [save_txt]])
    def test_plugin_saveas(self, save_file):
        with mock.patch("mslib.msui.mss_pyui.config_loader", return_value=self.export_plugins):
            self.window.add_export_plugins("qt")
        with mock.patch("mslib.msui.mss_pyui.get_save_filename", return_value=save_file[0]) as mocksave:
            assert self.window.listFlightTracks.count() == 1
            assert mocksave.call_count == 0
            self.window.last_save_directory = ROOT_DIR
            self.window.actionSaveActiveFlightTrackAs.trigger()
            QtWidgets.QApplication.processEvents()
            assert mocksave.call_count == 1
            assert os.path.exists(save_file[0])
            os.remove(save_file[0])

    @pytest.mark.parametrize(
        "open_file", [(open_ftml, "ftml"), (open_csv, "csv"), (open_txt, "txt"), (open_fls, "fls")])
    def test_plugin_import(self, open_file):
        with mock.patch("mslib.msui.mss_pyui.config_loader", return_value=self.import_plugins):
            self.window.add_import_plugins("qt")
        with mock.patch("mslib.msui.mss_pyui.get_open_filename", return_value=open_file[0]) as mockopen:
            assert self.window.listFlightTracks.count() == 1
            assert mockopen.call_count == 0
            self.window.last_save_directory = ROOT_DIR
            ext = open_file[1]
            full_name = f"actionImportFlightTrack{ext}"
            for action in self.window.menuImportFlightTrack.actions():
                if action.objectName() == full_name:
                    action.trigger()
                    break
            QtWidgets.QApplication.processEvents()
            assert mockopen.call_count == 1
            assert self.window.listFlightTracks.count() == 2

    @pytest.mark.parametrize("save_file", [[save_ftml], [save_csv], [save_txt]])
    def test_plugin_export(self, save_file):
        with mock.patch("mslib.msui.mss_pyui.config_loader", return_value=self.export_plugins):
            self.window.add_export_plugins("qt")
        with mock.patch("mslib.msui.mss_pyui.get_save_filename", return_value=save_file[0]) as mocksave:
            assert self.window.listFlightTracks.count() == 1
            assert mocksave.call_count == 0
            self.window.last_save_directory = ROOT_DIR
            ext = fs.path.splitext(save_file[0])[-1][1:]
            full_name = f"actionExportFlightTrack{ext}"
            for action in self.window.menuExportActiveFlightTrack.actions():
                if action.objectName() == full_name:
                    action.trigger()
                    break
            QtWidgets.QApplication.processEvents()
            assert mocksave.call_count == 1
            assert os.path.exists(save_file[0])
            os.remove(save_file[0])

    @pytest.mark.skip("needs to be refactored to become independent")
    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    @mock.patch("mslib.msui.mss_pyui.config_loader", return_value=export_plugins)
    def test_add_plugins(self, mockopen, mockbox):
        assert len(self.window.menuImportFlightTrack.actions()) == 2
        assert len(self.window.menuExportActiveFlightTrack.actions()) == 2
        assert len(self.window.import_plugins) == 1
        assert len(self.window.export_plugins) == 1

        self.window.remove_plugins()
        self.window.add_import_plugins("qt")
        self.window.add_export_plugins("qt")
        assert len(self.window.import_plugins) == 1
        assert len(self.window.export_plugins) == 1
        assert len(self.window.menuImportFlightTrack.actions()) == 2
        assert len(self.window.menuExportActiveFlightTrack.actions()) == 2
        assert mockbox.critical.call_count == 0

        self.window.remove_plugins()
        with mock.patch("importlib.import_module", new=ExceptionMock(Exception()).raise_exc):
            self.window.add_import_plugins("qt")
            self.window.add_export_plugins("qt")
            assert mockbox.critical.call_count == 2

        self.window.remove_plugins()
        with mock.patch("mslib.msui.mss_pyui.MSSMainWindow.add_plugin_submenu",
                        new=ExceptionMock(Exception()).raise_exc):
            self.window.add_import_plugins("qt")
            self.window.add_export_plugins("qt")
            assert mockbox.critical.call_count == 4

        self.window.remove_plugins()
        assert len(self.window.import_plugins) == 0
        assert len(self.window.export_plugins) == 0
        assert len(self.window.menuImportFlightTrack.actions()) == 1
        assert len(self.window.menuExportActiveFlightTrack.actions()) == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox.critical")
    @mock.patch("PyQt5.QtWidgets.QMessageBox.warning", return_value=QtWidgets.QMessageBox.Yes)
    @mock.patch("PyQt5.QtWidgets.QMessageBox.information", return_value=QtWidgets.QMessageBox.Yes)
    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    @mock.patch("mslib.msui.mss_pyui.get_save_filename", return_value=save_ftml)
    @mock.patch("mslib.msui.mss_pyui.get_open_filename", return_value=save_ftml)
    def test_flight_track_io(self, mockload, mocksave, mockq, mocki, mockw, mockbox):
        self.window.actionCloseSelectedFlightTrack.trigger()
        assert mocki.call_count == 1
        self.window.actionNewFlightTrack.trigger()
        self.window.listFlightTracks.setCurrentRow(0)
        assert self.window.listFlightTracks.count() == 2
        tmp_ft = self.window.active_flight_track
        self.window.active_flight_track = self.window.listFlightTracks.currentItem().flighttrack_model
        self.window.actionCloseSelectedFlightTrack.trigger()
        assert mocki.call_count == 2
        self.window.last_save_directory = self.sample_path
        self.window.actionSaveActiveFlightTrack.trigger()
        self.window.actionSaveActiveFlightTrack.trigger()
        self.window.active_flight_track = tmp_ft
        self.window.actionCloseSelectedFlightTrack.trigger()
        assert self.window.listFlightTracks.count() == 1
        self.window.actionImportFlightTrackftml.trigger()
        assert self.window.listFlightTracks.count() == 2
        assert os.path.exists(self.save_ftml)
        os.remove(self.save_ftml)
