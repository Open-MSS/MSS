# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_msui
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.msui

    This file is part of MSS.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2025 by the MSS team, see AUTHORS.
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


import re
import mock
import os
import argparse
import pytest
import json
import logging
import urllib.parse
from mslib.msui import constants
from pathlib import Path
from urllib.request import urlopen
from PyQt5 import QtWidgets, QtTest
from mslib import __version__
from tests.constants import ROOT_DIR, MSUI_CONFIG_PATH
from mslib.msui import msui
from mslib.msui import msui_mainwindow as msui_mw
from tests.utils import ExceptionMock
from mslib.utils.config import read_config_file
from mslib.msui import flighttrack as ft
from unittest.mock import patch
from mslib.msui.topview import MSUITopViewWindow
from mslib.msui.msui_mainwindow import QActiveViewsListWidgetItem


def test_main():
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        with mock.patch("mslib.msui.msui.argparse.ArgumentParser.parse_args",
                        return_value=argparse.Namespace(version=True)):
            msui.main()
        assert pytest_wrapped_e.typename == "SystemExit"


class Test_MSS_TutorialMode:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot, qapp):
        qapp.setApplicationDisplayName("MSUI")
        self.main_window = msui_mw.MSUIMainWindow(tutorial_mode=True)
        self.main_window.create_new_flight_track()
        self.main_window.show()
        self.main_window.shortcuts_dlg = msui_mw.MSUI_ShortcutsDialog(
            tutorial_mode=True)
        self.main_window.show_shortcuts(search_mode=True)
        self.tutorial_dir = Path(MSUI_CONFIG_PATH) / 'tutorial_images'
        yield
        self.main_window.hide()

    def test_tutorial_dir(self):
        dir_path = Path(self.tutorial_dir)
        assert dir_path.parent.exists()
        assert dir_path.name in [x.name for x in dir_path.parent.iterdir()]
        # seems we don't have a window manager in the test environment on github
        # checking only for a few
        common_images = [x.name for x in dir_path.iterdir()]
        assert 'menufile-file.png' in common_images
        assert 'msuimainwindow-operation-archive.png' in common_images
        assert 'msuimainwindow-work-asynchronously.png' in common_images
        assert 'msuimainwindow-connect.png' in common_images


class Test_MSS_AboutDialog:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.window = msui_mw.MSUI_AboutDialog()
        yield
        self.window.hide()

    def test_milestone_url(self):
        with urlopen(self.window.milestone_url) as f:
            text = f.read().decode("utf-8")
        expected_version = __version__
        pattern = rf'value="is:closed milestone:{re.escape(expected_version)} "'
        assert re.search(pattern, text), f"Expected milestone format not found: {expected_version}"


class Test_MSS_ShortcutDialog:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
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
    def setup(self, qtbot):
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
        file_path = str(Path(self.sample_path) / name[0])
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
        assert len(self.window.menuImportFlightTrack.actions()) == 3
        assert len(self.window.menuExportActiveFlightTrack.actions()) == 2
        assert len(self.window.import_plugins) == 0
        assert len(self.window.export_plugins) == 0

        self.window.remove_plugins()
        self.window.add_import_plugins("qt")
        self.window.add_export_plugins("qt")
        assert len(self.window.import_plugins) == 1
        assert len(self.window.export_plugins) == 1
        assert len(self.window.menuImportFlightTrack.actions()) == 4
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
        assert len(self.window.menuImportFlightTrack.actions()) == 3
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


class Test_MSUIMainWindow:
    def test_storing_and_restoring(self, qtbot, mswms_server):
        """Test the full scenario: create flight track, open TopView, modify settings,
        save on close, and restore settings on reopen."""

        parsed_url = urllib.parse.urlparse(mswms_server)
        scheme, host, port = parsed_url.scheme, parsed_url.hostname, parsed_url.port
        server_url = f"{scheme}://{host}:{port}"
        logging.debug(server_url)

        window = msui_mw.MSUIMainWindow()
        window.show()

        # create 1st flighttrack
        window.create_new_flight_track()
        assert window.listFlightTracks.count() == 1
        flight_track = window.active_flight_track
        assert "new flight track (1)" in window.activated_flight_tracks

        waypoint_model = flight_track
        waypoint_model.insertRows(0, 2, waypoints=[
            ft.Waypoint(lat=34.44, lon=56.67, location="point1"),
            ft.Waypoint(lat=77.77, lon=98.67, location="point2")
        ])

        # Open top view for first flight track
        window.create_view("topview", flight_track)
        assert window.listViews.count() == 1
        top_view1 = window.listViews.item(0).window
        assert top_view1.view_type == "Top View"

        top_view1.cbChangeMapSection.setCurrentText("00 global (cyl)")
        wms_settings1 = {
            "url": server_url,
            "layer": "ecmwf_EUR_LL015.PLRelHum01",
            "level": "200.0",
            "styles": "",
            "init_time": "2012-10-17T12:00:00Z",
            "valid_time": "2012-10-17T12:00:00Z",
        }
        top_view1.restore_wms_settings(wms_settings1)
        assert top_view1.wms_control.multilayers.cbWMS_URL.currentText() == server_url

        # create 2nd flighttrack
        window.create_new_flight_track()
        assert window.listFlightTracks.count() == 2
        flight_track2 = window.active_flight_track
        assert flight_track2.name == "new flight track (2)"
        assert "new flight track (2)" in window.activated_flight_tracks

        waypoint_model2 = flight_track2
        waypoint_model2.insertRows(0, 2, waypoints=[
            ft.Waypoint(lat=22.44, lon=86.67, location="point1"),
            ft.Waypoint(lat=67.77, lon=48.67, location="point2")
        ])

        assert window.listViews.count() == 1
        top_view2_1 = window.listViews.item(0).window
        assert top_view2_1.view_type == "Top View"
        assert top_view2_1.wms_control.multilayers.cbWMS_URL.currentText() == server_url

        window.create_view("topview", flight_track2)
        assert window.listViews.count() == 2
        top_view2_2 = window.listViews.item(1).window
        assert top_view2_2.view_type == "Top View"

        top_view2_2.cbChangeMapSection.setCurrentText("00 global (cyl)")
        wms_settings2 = {
            "url": server_url,
            "layer": "ecmwf_EUR_LL015.PLW01",
            "level": "250.0",
            "styles": "",
            "init_time": "2012-10-17T12:00:00Z",
            "valid_time": "2012-10-17T12:00:00Z",
        }
        top_view2_2.restore_wms_settings(wms_settings2)
        assert top_view2_2.wms_control.multilayers.cbWMS_URL.currentText() == server_url

        settings1 = window.flight_track_settings["new flight track (1)"]
        assert settings1["views"][0]["wms"]["url"] == server_url

        with patch("PyQt5.QtWidgets.QMessageBox.warning", return_value=QtWidgets.QMessageBox.Yes):
            window.close()

        # Assert: Verify view_settings.json after closing
        config_path = Path(constants.MSUI_CONFIG_PATH)
        settings_file = config_path / "view_settings.json"
        assert settings_file.exists(), f"view_settings.json not found at {settings_file}"
        with settings_file.open("r") as f:
            settings_data = json.load(f)

        assert "new flight track (1)" in settings_data
        assert len(settings_data["new flight track (1)"]["views"]) == 1
        assert settings_data["new flight track (1)"]["views"][0]["view_type"] == "topview"
        assert settings_data["new flight track (1)"]["views"][0]["wms"]["url"] == server_url
        assert settings_data["new flight track (1)"]["views"][0]["wms"]["layer"] == "ecmwf_EUR_LL015.PLRelHum01", \
            f"expected {'ecmwf_EUR_LL015.PLRelHum01'} got {settings_data['new flight track (1)']['views'][0]['wms']['layer']}"
        assert settings_data["new flight track (1)"]["views"][0]["wms"]["level"] == "200.0"
        assert "new flight track (2)" in settings_data
        assert len(settings_data["new flight track (2)"]["views"]) == 2
        assert settings_data["new flight track (2)"]["views"][0]["view_type"] == "topview"
        assert settings_data["new flight track (2)"]["views"][0]["wms"]["url"] == server_url
        assert settings_data["new flight track (2)"]["views"][0]["wms"]["layer"] == "ecmwf_EUR_LL015.PLRelHum01", \
            f"expected {'ecmwf_EUR_LL015.PLRelHum01'} got {settings_data['new flight track (2)']['views'][0]['wms']['layer']}"
        assert settings_data["new flight track (2)"]["views"][0]["wms"]["level"] == "200.0"
        assert settings_data["new flight track (2)"]["views"][1]["view_type"] == "topview"
        assert settings_data["new flight track (2)"]["views"][0]["wms"]["url"] == server_url
        assert settings_data["new flight track (2)"]["views"][1]["wms"]["layer"] == "ecmwf_EUR_LL015.PLW01"
        assert settings_data["new flight track (2)"]["views"][1]["wms"]["level"] == "250.0"

        # Create MSUIMainWindow
        new_window = msui_mw.MSUIMainWindow()
        new_window.show()

        new_window.create_new_flight_track(template=[
            ft.Waypoint(lat=34.44, lon=56.67, location="point1"),
            ft.Waypoint(lat=77.77, lon=98.67, location="point2")
        ], activate=True)

        new_window.active_flight_track.name == "new flight track (1)"
        assert new_window.active_flight_track.name == "new flight track (1)"

        while new_window.listViews.count() > 0:
            new_window.listViews.item(0).window.handle_force_close()
        new_window.listViews.clear()
        new_window.viewsChanged.emit()
        QActiveViewsListWidgetItem.opened_views = 0
        new_window.restore_views_for_active_flighttrack()

        # Access restored view
        restored_top_view1 = new_window.listViews.item(0)
        assert restored_top_view1 is not None, "No view restored"
        restored_top_view1 = restored_top_view1.window
        assert isinstance(restored_top_view1, MSUITopViewWindow)

        # Verify WMS settings
        wms_control1 = restored_top_view1.wms_control
        wms_control1.get_capabilities()
        assert wms_control1.multilayers.cbWMS_URL.currentText() == server_url

        new_window.create_new_flight_track(template=[
            ft.Waypoint(lat=22.44, lon=86.67, location="point1"),
            ft.Waypoint(lat=67.77, lon=48.67, location="point2")
        ], activate=True)
        new_window.active_flight_track.name == "new flight track (2)"

        while new_window.listViews.count() > 0:
            new_window.listViews.item(0).window.handle_force_close()
        new_window.listViews.clear()
        new_window.viewsChanged.emit()
        QActiveViewsListWidgetItem.opened_views = 0
        new_window.restore_views_for_active_flighttrack()

        assert new_window.listFlightTracks.count() == 2
        assert new_window.listViews.count() == 2

        restored_top_view2_1 = new_window.listViews.item(0).window
        assert isinstance(restored_top_view2_1, MSUITopViewWindow)
        wms_control2_1 = restored_top_view2_1.wms_control
        wms_control2_1.get_capabilities()
        assert wms_control2_1.multilayers.cbWMS_URL.currentText().rstrip("/") == server_url, \
            f"Expected URL {server_url}, got {wms_control2_1.multilayers.cbWMS_URL.currentText()}"

        restored_top_view2_2 = new_window.listViews.item(1).window
        assert isinstance(restored_top_view2_2, MSUITopViewWindow)
        wms_control2_2 = restored_top_view2_2.wms_control
        wms_control2_2.get_capabilities()
        assert wms_control2_2.multilayers.cbWMS_URL.currentText().rstrip("/") == server_url, \
            f"Expected URL {server_url}, got {wms_control2_2.multilayers.cbWMS_URL.currentText()}"
