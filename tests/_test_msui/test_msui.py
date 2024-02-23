# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_msui
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.msui

    This file is part of MSS.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2023 by the MSS team, see AUTHORS.
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


import mock
import os
import fs
import platform
import argparse
import pytest
from urllib.request import urlopen
from PyQt5 import QtWidgets, QtTest
from mslib import __version__
from tests.constants import ROOT_DIR, POSIX, MSUI_CONFIG_PATH
from mslib.msui import msui
from mslib.msui import msui_mainwindow as msui_mw
from tests.utils import ExceptionMock
from mslib.utils.config import read_config_file


@mock.patch("mslib.msui.msui.constants.POSIX", POSIX)
def test_main():
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        with mock.patch("mslib.msui.msui.argparse.ArgumentParser.parse_args",
                        return_value=argparse.Namespace(version=True)):
            msui.main()
        assert pytest_wrapped_e.typename == "SystemExit"

    if platform.system() == "Linux":
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            with mock.patch("mslib.msui.msui.argparse.ArgumentParser.parse_args",
                            return_value=argparse.Namespace(version=False, update=False, menu=True,
                                                            deinstall=False, debug=False, logfile="log.log")):
                msui.main()
            assert pytest_wrapped_e.typename == "SystemExit"
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            with mock.patch("mslib.msui.msui.argparse.ArgumentParser.parse_args",
                            return_value=argparse.Namespace(version=False, update=False, menu=False,
                                                            deinstall=True, debug=False, logfile="log.log")):
                msui.main()
            assert pytest_wrapped_e.typename == "SystemExit"


class Test_MSS_TutorialMode:
    @pytest.fixture(autouse=True)
    def setup(self, qapp):
        qapp.setApplicationDisplayName("MSUI")
        self.main_window = msui_mw.MSUIMainWindow(tutorial_mode=True)
        self.main_window.create_new_flight_track()
        self.main_window.show()
        self.main_window.shortcuts_dlg = msui_mw.MSUI_ShortcutsDialog(
            tutorial_mode=True)
        self.main_window.show_shortcuts(search_mode=True)
        self.tutorial_dir = fs.path.combine(MSUI_CONFIG_PATH, 'tutorial_images')
        yield
        self.main_window.hide()

    def test_tutorial_dir(self):
        dir_name, name = fs.path.split(self.tutorial_dir)
        with fs.open_fs(dir_name) as _fs:
            assert _fs.exists(name)
        # seems we don't have a window manager in the test environment on github
        # checking only for a few
        with (fs.open_fs(self.tutorial_dir) as _fs):
            common_images = _fs.listdir('/')
            assert 'menufile-file.png' in common_images
            assert 'msuimainwindow-operation-archive.png' in common_images
            assert 'msuimainwindow-work-asynchronously.png' in common_images
            assert 'msuimainwindow-connect.png' in common_images


class Test_MSS_AboutDialog:
    @pytest.fixture(autouse=True)
    def setup(self, qapp):
        self.window = msui_mw.MSUI_AboutDialog()
        yield
        self.window.hide()

    def test_milestone_url(self):
        with urlopen(self.window.milestone_url) as f:
            text = f.read()
        pattern = f'value="is:closed milestone:{__version__[:-1]}"'
        assert pattern in text.decode('utf-8')


class Test_MSS_ShortcutDialog:
    @pytest.fixture(autouse=True)
    def setup(self, qapp):
        self.main_window = msui_mw.MSUIMainWindow()
        self.main_window.show()
        self.shortcuts = msui_mw.MSUI_ShortcutsDialog()
        yield
        self.shortcuts.hide()
        self.main_window.hide()

    def test_shortcuts_present(self):
        # Assert list gets filled properly
        self.shortcuts.fill_list()
        assert self.shortcuts.treeWidget.topLevelItemCount() == 1
        self.shortcuts.leShortcutFilter.setText("Nothing")
        self.shortcuts.filter_shortcuts()
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

    # ToDo we need a test for reset_highlight when e.g. Transparent was selected and afterwards topview was destroyed


class Test_MSSSideViewWindow:
    # temporary file paths to test open feature
    sample_path = os.path.join(os.path.dirname(__file__), "..", "data")
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
        "TXT": ["txt", "mslib.plugins.io.text", "load_from_txt"],
        "FliteStar": ["txt", "mslib.plugins.io.flitestar", "load_from_flitestar"],
    }
    export_plugins = {
        "Text": ["txt", "mslib.plugins.io.text", "save_to_txt"],
        # "KML": ["kml", "mslib.plugins.io.kml", "save_to_kml"],
        # "GPX": ["gpx", "mslib.plugins.io.gpx", "save_to_gpx"]
    }

    @pytest.fixture(autouse=True)
    def setup(self, qapp):
        self.sample_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../',
            'data/')

        self.window = msui.MSUIMainWindow()
        self.window.create_new_flight_track()
        self.window.show()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        yield
        config_file = os.path.join(
            self.sample_path,
            'empty_msui_settings.json',
        )
        read_config_file(path=config_file)
        for i in range(self.window.listViews.count()):
            self.window.listViews.item(i).window.hide()
        self.window.hide()

    def test_no_updater(self):
        assert not hasattr(self.window, "updater")

    def test_app_start(self):
        pass

    def test_new_flightrack(self):
        assert self.window.listFlightTracks.count() == 1
        self.window.actionNewFlightTrack.trigger()
        assert self.window.listFlightTracks.count() == 2

    def test_open_topview(self):
        assert self.window.listViews.count() == 0
        self.window.actionTopView.trigger()
        assert self.window.listViews.count() == 1

    def test_open_sideview(self):
        assert self.window.listViews.count() == 0
        self.window.actionSideView.trigger()
        assert self.window.listViews.count() == 1

    def test_open_tableview(self):
        assert self.window.listViews.count() == 0
        self.window.actionTableView.trigger()
        assert self.window.listViews.count() == 1

    def test_open_linearview(self):
        assert self.window.listViews.count() == 0
        self.window.actionLinearView.trigger()
        self.window.listViews.itemActivated.emit(self.window.listViews.item(0))
        assert self.window.listViews.count() == 1

    def test_open_about(self):
        self.window.actionAboutMSUI.trigger()

    def test_open_config(self):
        self.window.actionConfiguration.trigger()
        with mock.patch("PyQt5.QtWidgets.QMessageBox.warning", return_value=QtWidgets.QMessageBox.Yes):
            self.window.config_editor.close()

    def test_open_shortcut(self):
        self.window.actionShortcuts.trigger()

    @pytest.mark.parametrize("save_file", [[save_ftml]])
    def test_plugin_saveas(self, save_file):
        with mock.patch("mslib.msui.msui_mainwindow.config_loader", return_value=self.export_plugins):
            self.window.add_export_plugins("qt")
        with mock.patch("mslib.msui.msui_mainwindow.get_save_filename", return_value=save_file[0]) as mocksave:
            assert self.window.listFlightTracks.count() == 1
            assert mocksave.call_count == 0
            self.window.last_save_directory = ROOT_DIR
            self.window.actionSaveActiveFlightTrackAs.trigger()
            assert mocksave.call_count == 1
            assert os.path.exists(save_file[0])
            os.remove(save_file[0])

    @pytest.mark.parametrize("name", [("example.ftml", "actionImportFlightTrackFTML", 5),
                                      ("example.csv", "actionImportFlightTrackCSV", 5),
                                      ("example.txt", "actionImportFlightTrackTXT", 5),
                                      ("flitestar.txt", "actionImportFlightTrackFliteStar", 10)])
    def test_plugin_import(self, name):
        with mock.patch("mslib.msui.msui_mainwindow.config_loader", return_value=self.import_plugins):
            self.window.add_import_plugins("qt")
        assert self.window.listFlightTracks.count() == 1
        file_path = fs.path.join(self.sample_path, name[0])
        with mock.patch("mslib.msui.msui_mainwindow.get_open_filenames", return_value=[file_path]) as mockopen:
            for action in self.window.menuImportFlightTrack.actions():
                if action.objectName() == name[1]:
                    action.trigger()
                    break
            assert mockopen.call_count == 1
            assert self.window.listFlightTracks.count() == 2
            assert self.window.active_flight_track.name == name[0].split(".")[0]
            assert len(self.window.active_flight_track.waypoints) == name[2]

    @pytest.mark.parametrize("save_file", [[save_ftml, "actionExportFlightTrackFTML"],
                                           [save_txt, "actionExportFlightTrackText"]])
    def test_plugin_export(self, save_file):
        with mock.patch("mslib.msui.msui_mainwindow.config_loader", return_value=self.export_plugins):
            self.window.add_export_plugins("qt")
        with mock.patch("mslib.msui.msui_mainwindow.get_save_filename", return_value=save_file[0]) as mocksave:
            assert self.window.listFlightTracks.count() == 1
            assert mocksave.call_count == 0
            self.window.last_save_directory = ROOT_DIR
            obj_name = save_file[1]
            for action in self.window.menuExportActiveFlightTrack.actions():
                if obj_name == action.objectName():
                    action.trigger()
                    break
            assert mocksave.call_count == 1
            assert os.path.exists(save_file[0])
            os.remove(save_file[0])

    @mock.patch("mslib.msui.msui_mainwindow.config_loader", return_value=export_plugins)
    def test_add_plugins(self, mockopen):
        assert len(self.window.menuImportFlightTrack.actions()) == 2
        assert len(self.window.menuExportActiveFlightTrack.actions()) == 2
        assert len(self.window.import_plugins) == 0
        assert len(self.window.export_plugins) == 0

        self.window.remove_plugins()
        self.window.add_import_plugins("qt")
        self.window.add_export_plugins("qt")
        assert len(self.window.import_plugins) == 1
        assert len(self.window.export_plugins) == 1
        assert len(self.window.menuImportFlightTrack.actions()) == 3
        assert len(self.window.menuExportActiveFlightTrack.actions()) == 3

        self.window.remove_plugins()
        with mock.patch("importlib.import_module", new=ExceptionMock(Exception()).raise_exc), \
                mock.patch("PyQt5.QtWidgets.QMessageBox.critical") as critbox:
            self.window.add_import_plugins("qt")
            self.window.add_export_plugins("qt")
            assert critbox.call_count == 2

        self.window.remove_plugins()
        with mock.patch("mslib.msui.ms"
                        "ui.MSUIMainWindow.add_plugin_submenu",
                        new=ExceptionMock(Exception()).raise_exc), \
                mock.patch("PyQt5.QtWidgets.QMessageBox.critical") as critbox:
            self.window.add_import_plugins("qt")
            self.window.add_export_plugins("qt")
            assert critbox.call_count == 2

        self.window.remove_plugins()
        assert len(self.window.import_plugins) == 0
        assert len(self.window.export_plugins) == 0
        assert len(self.window.menuImportFlightTrack.actions()) == 2
        assert len(self.window.menuExportActiveFlightTrack.actions()) == 2

    @mock.patch("PyQt5.QtWidgets.QMessageBox.warning", return_value=QtWidgets.QMessageBox.Yes)
    @mock.patch("PyQt5.QtWidgets.QMessageBox.information", return_value=QtWidgets.QMessageBox.Yes)
    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    @mock.patch("mslib.msui.msui_mainwindow.get_save_filename", return_value=save_ftml)
    @mock.patch("mslib.msui.msui_mainwindow.get_open_filenames", return_value=[save_ftml])
    def test_flight_track_io(self, mockload, mocksave, mockq, mocki, mockw):
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
        self.window.active_flight_track = tmp_ft
        self.window.actionCloseSelectedFlightTrack.trigger()
        assert self.window.listFlightTracks.count() == 1
        self.window.actionImportFlightTrackFTML.trigger()
        assert self.window.listFlightTracks.count() == 2
        assert os.path.exists(self.save_ftml)
        os.remove(self.save_ftml)
