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


import mock
import os
import argparse
import pytest
from pathlib import Path
from urllib.request import urlopen
from PyQt5 import QtWidgets, QtTest
from mslib import __version__
from tests.constants import ROOT_DIR, MSUI_CONFIG_PATH
from mslib.msui import msui
from mslib.msui import msui_mainwindow as msui_mw
from tests.utils import ExceptionMock
from mslib.utils.config import read_config_file
import re


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
    def setUp(self):
        # Create a QApplication instance for Qt tests
        self.app = QtWidgets.QApplication([])

        # Create temporary directory for JSON files
        self.temp_dir = tempfile.mkdtemp()

        # Mock config_loader to return temporary directory
        self.config_patcher = patch("mslib.msui.msui_mainwindow.config_loader")
        self.mock_config = self.config_patcher.start()
        self.mock_config.side_effect = lambda dataset=None, default=False: {
            "data_dir": self.temp_dir,
            "new_flighttrack_template": [("START", 0, 0), ("END", 10, 10)],
            "new_flighttrack_flightlevel": 350,
            "restore_views": True,
            "filepicker_default": "qt"
        }.get(dataset, {})

        # Mock view_restoration.save_view_settings
        self.save_view_settings_patcher = patch("mslib.msui.msui_mainwindow.view_restoration.save_view_settings")
        self.mock_save_view_settings = self.save_view_settings_patcher.start()

        # Mock view_restoration.restore_view_settings
        self.restore_view_settings_patcher = patch("mslib.msui.msui_mainwindow.view_restoration.restore_view_settings")
        self.mock_restore_view_settings = self.restore_view_settings_patcher.start()
        self.mock_restore_view_settings.side_effect = lambda name: {
            "global": {"flight_track_name": name, "waypoints": [{"location": "START", "lat": 0, "lon": 0, "flightlevel": 350}]},
            "views": [{"view_type": "topview", "view_id": f"view_topview_{name}", "settings": "topview_settings"}]
        }

        # Initialize MSUIMainWindow
        self.main_window = msui_mainwindow.MSUIMainWindow()

    def tearDown(self):
        # Clean up QApplication and temporary directory
        self.app.quit()
        self.config_patcher.stop()
        self.save_view_settings_patcher.stop()
        self.restore_view_settings_patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_create_new_flight_track(self):
        """Test that flight_track_settings is updated when a new flight track is created."""
        self.main_window.create_new_flight_track()
        flight_name = "new flight track (1)"
        self.assertIn(flight_name, self.main_window.flight_track_settings)
        self.assertEqual(self.main_window.flight_track_settings[flight_name]["views"], [])
        self.assertIn("global", self.main_window.flight_track_settings[flight_name])
        self.assertIn(flight_name, self.main_window.activated_flight_tracks)
        self.assertEqual(len(self.main_window.flight_track_settings), 1)

    def test_create_multiple_flight_tracks(self):
        """Test that multiple flight tracks are added to flight_track_settings."""
        self.main_window.create_new_flight_track()
        self.main_window.create_new_flight_track()
        self.assertEqual(len(self.main_window.flight_track_settings), 2)
        self.assertIn("new flight track (1)", self.main_window.flight_track_settings)
        self.assertIn("new flight track (2)", self.main_window.flight_track_settings)
        self.assertEqual(len(self.main_window.activated_flight_tracks), 2)

    def test_create_view_updates_settings(self):
        """Test that creating a view updates flight_track_settings with the correct number of views."""
        self.main_window.create_new_flight_track()
        flight_name = "new flight track (1)"
        with patch("mslib.msui.msui_mainwindow.topview", autospec=True) as mock_topview:
            mock_topview.MSUITopViewWindow = lambda **kwargs: MockViewWindow(view_type="topview", **kwargs)
            self.main_window.create_view("topview", self.main_window.active_flight_track)
        
        self.assertEqual(len(self.main_window.flight_track_settings[flight_name]["views"]), 1)
        view_settings = self.main_window.flight_track_settings[flight_name]["views"][0]
        self.assertEqual(view_settings["view_type"], "topview")
        self.assertEqual(self.main_window.listViews.count(), 1)

    def test_flight_track_switch_updates_settings(self):
        """Test that switching flight tracks updates settings for the previous flight track."""
        # Create two flight tracks
        self.main_window.create_new_flight_track()
        first_flight_name = "new flight track (1)"
        first_flight = self.main_window.active_flight_track
        with patch("mslib.msui.msui_mainwindow.topview", autospec=True) as mock_topview:
            mock_topview.MSUITopViewWindow = lambda **kwargs: MockViewWindow(view_type="topview", **kwargs)
            self.main_window.create_view("topview", first_flight)
        
        self.main_window.create_new_flight_track()
        second_flight_name = "new flight track (2)"

        # Switch back to the first flight track
        listitem = self.main_window.listFlightTracks.item(0)  # First flight track
        with patch("mslib.msui.msui_mainwindow.topview", autospec=True) as mock_topview:
            mock_topview.MSUITopViewWindow = lambda **kwargs: MockViewWindow(view_type="topview", **kwargs)
            self.main_window.activate_flight_track(listitem)

        # Check that settings for the first flight track are updated
        self.assertEqual(len(self.main_window.flight_track_settings[first_flight_name]["views"]), 1)
        self.assertIn("global", self.main_window.flight_track_settings[first_flight_name])
        self.assertEqual(self.main_window.active_flight_track.name, first_flight_name)
        self.assertEqual(len(self.main_window.flight_track_settings), 2)

    @pytest.mark.qt
    def test_close_event_saves_all_flight_tracks(self):
        """Test that closing the application saves settings for all flight tracks."""
        # Create two flight tracks with views
        self.main_window.create_new_flight_track()
        flight1_name = "new flight track (1)"
        with patch("mslib.msui.msui_mainwindow.topview", autospec=True) as mock_topview:
            mock_topview.MSUITopViewWindow = lambda **kwargs: MockViewWindow(view_type="topview", **kwargs)
            self.main_window.create_view("topview", self.main_window.active_flight_track)
        
        self.main_window.create_new_flight_track()
        flight2_name = "new flight track (2)"
        with patch("mslib.msui.msui_mainwindow.sideview", autospec=True) as mock_sideview:
            mock_sideview.MSUISideViewWindow = lambda **kwargs: MockViewWindow(view_type="sideview", **kwargs)
            self.main_window.create_view("sideview", self.main_window.active_flight_track)

        # Mock QMessageBox to accept the close confirmation
        with patch("PyQt5.QtWidgets.QMessageBox.warning", return_value=QtWidgets.QMessageBox.Yes):
            close_event = QtCore.QEvent(QtCore.QEvent.Close)
            self.main_window.closeEvent(close_event)

        # Verify that save_view_settings was called for both flight tracks
        expected_calls = [
            unittest.mock.call(
                self.main_window.flight_track_settings[flight1_name]["views"],
                self.main_window.flight_track_settings[flight1_name]["global"],
                flight1_name
            ),
            unittest.mock.call(
                self.main_window.flight_track_settings[flight2_name]["views"],
                self.main_window.flight_track_settings[flight2_name]["global"],
                flight2_name
            )
        ]
        self.mock_save_view_settings.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(self.mock_save_view_settings.call_count, 2)
        self.assertEqual(len(self.main_window.flight_track_settings[flight1_name]["views"]), 1)
        self.assertEqual(len(self.main_window.flight_track_settings[flight2_name]["views"]), 1)

    @pytest.mark.qt
    def test_single_flight_track_save_on_close(self):
        """Test that settings for a single flight track are saved on close."""
        self.main_window.create_new_flight_track()
        flight_name = "new flight track (1)"
        with patch("mslib.msui.msui_mainwindow.topview", autospec=True) as mock_topview:
            mock_topview.MSUITopViewWindow = lambda **kwargs: MockViewWindow(view_type="topview", **kwargs)
            self.main_window.create_view("topview", self.main_window.active_flight_track)

        # Mock QMessageBox to accept the close confirmation
        with patch("PyQt5.QtWidgets.QMessageBox.warning", return_value=QtWidgets.QMessageBox.Yes):
            close_event = QtCore.QEvent(QtCore.QEvent.Close)
            self.main_window.closeEvent(close_event)

        # Verify settings were saved
        self.assertIn(flight_name, self.main_window.flight_track_settings)
        self.assertEqual(len(self.main_window.flight_track_settings[flight_name]["views"]), 1)
        self.mock_save_view_settings.assert_called_once_with(
            self.main_window.flight_track_settings[flight_name]["views"],
            self.main_window.flight_track_settings[flight_name]["global"],
            flight_name
        )

    def test_restore_flight_tracks_and_views(self):
        """Test that restoring flight tracks and views matches the saved state."""
        # Create two flight tracks with views
        self.main_window.create_new_flight_track()
        flight1_name = "new flight track (1)"
        with patch("mslib.msui.msui_mainwindow.topview", autospec=True) as mock_topview:
            mock_topview.MSUITopViewWindow = lambda **kwargs: MockViewWindow(view_type="topview", **kwargs)
            self.main_window.create_view("topview", self.main_window.active_flight_track)
        
        self.main_window.create_new_flight_track()
        flight2_name = "new flight track (2)"
        with patch("mslib.msui.msui_mainwindow.sideview", autospec=True) as mock_sideview:
            mock_sideview.MSUISideViewWindow = lambda **kwargs: MockViewWindow(view_type="sideview", **kwargs)
            self.main_window.create_view("sideview", self.main_window.active_flight_track)

        # Simulate close to save settings
        with patch("PyQt5.QtWidgets.QMessageBox.warning", return_value=QtWidgets.QMessageBox.Yes):
            close_event = QtCore.QEvent(QtCore.QEvent.Close)
            self.main_window.closeEvent(close_event)

        # Create a new main window to simulate restart
        new_main_window = msui_mainwindow.MSUIMainWindow()
        new_main_window.create_new_flight_track()
        new_main_window.active_flight_track.name = flight1_name

        # Mock restore_view_settings to return saved settings
        def restore_side_effect(name):
            if name == flight1_name:
                return {
                    "global": {"flight_track_name": flight1_name, "waypoints": [{"location": "START"}]},
                    "views": [{"view_type": "topview", "view_id": f"view_topview_{flight1_name}", "settings": "topview_settings"}]
                }
            elif name == flight2_name:
                return {
                    "global": {"flight_track_name": flight2_name, "waypoints": [{"location": "START"}]},
                    "views": [{"view_type": "sideview", "view_id": f"view_sideview_{flight2_name}", "settings": "sideview_settings"}]
                }
            return {}

        self.mock_restore_view_settings.side_effect = restore_side_effect
        # Restore views for the first flight track
        with patch("mslib.msui.msui_mainwindow.topview", autospec=True) as mock_topview:
            mock_topview.MSUITopViewWindow = lambda **kwargs: MockViewWindow(view_type="topview", **kwargs)
            new_main_window.restore_views_for_active_flighttrack()

        # Verify that the view was restored
        self.assertEqual(new_main_window.listViews.count(), 1)
        self.assertEqual(new_main_window.listViews.item(0).window.view_type, "topview")

        # Switch to second flight track and restore
        new_main_window.create_new_flight_track()
        new_main_window.active_flight_track.name = flight2_name
        with patch("mslib.msui.msui_mainwindow.sideview", autospec=True) as mock_sideview:
            mock_sideview.MSUISideViewWindow = lambda **kwargs: MockViewWindow(view_type="sideview", **kwargs)
            new_main_window.restore_views_for_active_flighttrack()

        self.assertEqual(new_main_window.listViews.count(), 1)
        self.assertEqual(new_main_window.listViews.item(0).window.view_type, "sideview")
        self.assertEqual(new_main_window.listFlightTracks.count(), 2)