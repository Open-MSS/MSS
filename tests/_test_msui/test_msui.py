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
import logging
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
from unittest.mock import Mock, MagicMock, patch
from mslib.msui.topview import MSUITopViewWindow


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
    @pytest.fixture(autouse=True)
    def setup(self, qtbot, qapp):
        mock_ctypes = MagicMock()
        self.ctypes_patcher = patch.dict('sys.modules', {'ctypes': mock_ctypes})
        self.ctypes_patcher.start()
        qapp.setApplicationDisplayName("MSUI")

        self.config_patcher = patch('mslib.msui.msui_mainwindow.config_loader')
        self.mock_config_loader = self.config_patcher.start()
        self.config_data = {
            "data_dir": ROOT_DIR,
            "new_flighttrack_template": ["point1", "point2"],
            "new_flighttrack_flightlevel": 0,
            "filepicker_default": "qt",
            "restore_views": True,  # Default for storing test
            "layout": {
                "topview": [800, 600],
                "sideview": [800, 600],
                "tableview": [800, 600],
                "linearview": [800, 600],
                "immutable": False
            },
            "mscolab_server_url": "http://localhost:8084",
            "default_MSCOLAB": "http://localhost:8084",
            "MSS_auth": {"http://localhost:8084": "user@example.com"},
            "import_plugins": {},
            "export_plugins": {},
            "locations": ["point1", "point2"]  # Mock locations to match template
        }
        self.mock_config_loader.side_effect = lambda dataset=None, default=False: (
            self.config_data.get(dataset, {} if not default else {})
        )

        self.saved_settings = {}
        self.view_restoration_patcher = patch('mslib.msui.msui_mainwindow.view_restoration')
        self.mock_view_restoration = self.view_restoration_patcher.start()
        self.mock_view_restoration.save_view_settings.side_effect = (
            lambda views, global_data, json_key: self.saved_settings.update({json_key: {"views": views,
                                                                                        "global": global_data}})
        )
        self.mock_view_restoration.restore_view_settings.side_effect = (
            lambda json_key: self.saved_settings.get(json_key, {"views": [], "global": {}})
        )
        self.mock_view_restoration.set_global_data.return_value = {"flight_track_name": "test_flight",
                                                                   "mss_version": "10.1.0"}

        # Mock MSColab to avoid server interactions
        self.mscolab_patcher = patch('mslib.msui.msui_mainwindow.mscolab.MSUIMscolab')
        self.mock_mscolab = self.mscolab_patcher.start()
        self.mock_mscolab_instance = Mock()
        self.mock_mscolab_instance.token = None
        self.mock_mscolab_instance.mscolab_server_url = "http://localhost:8084"
        self.mock_mscolab_instance.switch_to_local = Mock()
        self.mock_mscolab.return_value = self.mock_mscolab_instance

        # Mock ConfigurationEditorWindow
        self.editor_patcher = patch('mslib.msui.msui_mainwindow.editor.ConfigurationEditorWindow')
        self.mock_editor = self.editor_patcher.start()
        self.mock_editor_instance = Mock()
        self.mock_editor_instance.last_saved = {
            "mscolab_server_url": "http://localhost:8084",
            "default_MSCOLAB": "http://localhost:8084",
            "MSS_auth": {"http://localhost:8084": "user@example.com"},
            "automated_plotting_flights": [],
            "automated_plotting_hsecs": [],
            "automated_plotting_vsecs": [],
            "automated_plotting_lsecs": []
        }
        self.mock_editor.return_value = self.mock_editor_instance
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data', 'empty_msui_settings.json')
        if os.path.exists(config_file):
            read_config_file(path=config_file)
        else:
            logging.debug("Skipping config file read: %s not found", config_file)
        self.config_patcher.stop()
        self.view_restoration_patcher.stop()
        self.mscolab_patcher.stop()
        self.editor_patcher.stop()
        self.ctypes_patcher.stop()

    def test_storing(self, qtbot):
        """Test the full scenario: create flight track, open TopView, modify settings,
           save on close, and restore settings on reopen."""
        window = msui_mw.MSUIMainWindow()
        window.show()
        QtTest.QTest.qWaitForWindowExposed(window)

        with mock.patch("mslib.msui.msui_mainwindow.ft.WaypointsTableModel") as mock_waypoints_model, \
             mock.patch("mslib.msui.msui_mainwindow.MSUIMainWindow.signal_activate_flighttrack") as mock_signal:
            mock_signal.emit = Mock()  # Mock the signal to avoid type checking
            mock_flight_track = Mock(spec=ft.WaypointsTableModel)
            mock_flight_track.name = "test_flight"
            mock_flight_track.waypoints = [
                Mock(spec=ft.Waypoint, lat=0, lon=0, location="point1"),
                Mock(spec=ft.Waypoint, lat=1, lon=1, location="point2")
            ]
            mock_flight_track.all_waypoint_data = Mock(return_value=[
                {"lat": 0, "lon": 0, "location": "point1"},
                {"lat": 1, "lon": 1, "location": "point2"}
            ])
            mock_flight_track.get_xml_doc = Mock(return_value="<xml>flight track</xml>")
            mock_flight_track.insertRows = Mock()
            mock_waypoints_model.return_value = mock_flight_track
            logging.debug("Creating flight track with name: %s, type: %s", mock_flight_track.name,
                          type(mock_flight_track.name))
            window.create_new_flight_track()

        assert window.listFlightTracks.count() == 1
        assert window.active_flight_track.name == "test_flight"
        assert "test_flight" in window.activated_flight_tracks

        mock_topview = Mock(spec=MSUITopViewWindow)
        mock_topview.view_type = "topview"
        mock_topview.view_id = "view_topview_0"
        mock_topview.name = "Topview"
        mock_topview.active_flighttrack = mock_flight_track
        mock_topview.waypoints_model = mock_flight_track
        mock_topview.get_settings = Mock(return_value={
            "view_type": "topview",
            "map_section": "00 global (cyl)",
            "projection": "EPSG:4326",
            "wms": {
                "url": "http://open-mss.org/",
                "layer": "ecmwf_EUR_LL015.PLRelHum01",
                "level": "100.0",
                "styles": "",
                "init_time": "2012-10-17T12:00:00Z",
                "valid_time": "2012-10-17T12:00:00Z"
            }
        })
        mock_topview.mpl = Mock()
        mock_topview.mpl.resize = Mock()
        mock_topview.set_settings = Mock()
        mock_topview.refresh_signal_emit = Mock()
        mock_topview.viewCloses = Mock()
        mock_topview.setWindowTitle = Mock()
        mock_topview.handle_force_close = Mock()
        mock_topview.enable_navbar_action_buttons = Mock()
        mock_topview.disable_navbar_action_buttons = Mock()

        with mock.patch("mslib.msui.topview.MSUITopViewWindow") as mock_topview_class:
            mock_topview_class.return_value = mock_topview
            window.create_view("topview", mock_flight_track)

        assert window.listViews.count() == 1
        assert window.listViews.item(0).window == mock_topview

        mock_topview.get_settings = Mock(return_value={
            "view_type": "topview",
            "map_section": "00 global (cyl)",
            "projection": "EPSG:4326",
            "wms": {
                "url": "http://open-mss.org/",
                "layer": "ecmwf_EUR_LL015.PLRelHum01",
                "level": "200.0",  # Modified level
                "styles": "",
                "init_time": "2012-10-17T12:00:00Z",
                "valid_time": "2012-10-17T12:00:00Z"
            }
        })
        window.update_flight_track_settings(mock_flight_track, view=mock_topview)

        expected_settings = {
            "test_flight": {
                "views": [{
                    "map_section": "00 global (cyl)",
                    "projection": "EPSG:4326",
                    "view_type": "topview",
                    "view_id": "view_topview_0",
                    "wms": {
                        "url": "http://open-mss.org/",
                        "layer": "ecmwf_EUR_LL015.PLRelHum01",
                        "level": "200.0",
                        "styles": "",
                        "init_time": "2012-10-17T12:00:00Z",
                        "valid_time": "2012-10-17T12:00:00Z"
                    }
                }],
                "global": {"flight_track_name": "test_flight", "mss_version": "10.1.0"}
            }
        }
        assert window.flight_track_settings == expected_settings
        assert "test_flight" in window.activated_flight_tracks
        assert "test_flight" in window.activated_flight_tracks
