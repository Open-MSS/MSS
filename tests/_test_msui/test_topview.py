# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_topview
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.topview

    This file is part of MSS.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2026 by the MSS team, see AUTHORS.
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
import pytest
import mslib.msui.topview as tv
from PyQt5 import QtWidgets, QtCore, QtTest, QtGui
from mslib.msui import flighttrack as ft
from mslib.msui.msui import MSUIMainWindow
from mslib.msui.viewplotter import _DEFAULT_SETTINGS_TOPVIEW
from mslib.utils.config import config_loader

WMS_REQUEST_TIMEOUT_MS = (config_loader(dataset="WMS_request_timeout") + 5) * 1000


class Test_MSS_TV_MapAppearanceDialog:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.window = tv.MSUI_TV_MapAppearanceDialog(settings=_DEFAULT_SETTINGS_TOPVIEW)
        self.window.show()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        yield
        self.window.hide()

    def test_show(self):
        pass

    def test_get(self):
        self.window.get_settings()

    def test_setColour(self):
        """
        Test the setColour function to ensure the color dialog opens and the correct color is set.
        """
        # Simulate clicking the "Water" color button to open the color dialog
        self.window.setColour("ft_vertices")

        # Get a reference to the custom color dialog
        color_dialog = self.window.findChild(QtWidgets.QDialog)
        assert color_dialog is not None

        # Select the first color in the color dialog (assuming color_buttons is a list of buttons)
        color_dialog.color_buttons[0].click()

        # Get the selected color
        selected_color = QtGui.QColor(color_dialog.colors[0])

        # Verify that the button's color has been set correctly
        button_palette = self.window.btVerticesColour.palette()
        button_color = button_palette.button().color()
        assert button_color.getRgbF() == selected_color.getRgbF()

        # Verify that the correct color was set in the settings
        settings = self.window.get_settings()
        assert settings['colour_ft_vertices'] == selected_color.getRgbF()

    def test_line_thickness_change(self):
        """
        Test the thickness of flighttrack
        """
        # Verify initial value
        assert self.window.line_thickness == _DEFAULT_SETTINGS_TOPVIEW.get("line_thickness", 2)

        # Simulate changing line thickness
        new_thickness = 5.00
        self.window.sbLineThickness.setValue(new_thickness)

        settings = self.window.get_settings()
        assert settings['line_thickness'] == new_thickness

    def test_line_style_change(self):
        """
        Test the style of flighttrack
        """
        assert self.window.line_style == _DEFAULT_SETTINGS_TOPVIEW.get("line_style", "Solid")

        # Simulate changing line style
        new_style = "Dashed"
        self.window.cbLineStyle.setCurrentText(new_style)

        settings = self.window.get_settings()
        assert settings['line_style'] == new_style

    def test_line_transparency_change(self):
        """
        Test the transparency of flighttrack
        """
        assert self.window.line_transparency == _DEFAULT_SETTINGS_TOPVIEW.get("line_transparency", 1.0)

        # Simulate changing transparency
        new_transparency = 50  # == 0.5
        self.window.hsTransparencyControl.setValue(new_transparency)

        settings = self.window.get_settings()
        assert settings['line_transparency'] == new_transparency / 100


class Test_MSSTopViewWindow:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        mainwindow = MSUIMainWindow()
        initial_waypoints = [ft.Waypoint(40., 25., 0), ft.Waypoint(60., -10., 0), ft.Waypoint(40., 10, 0)]
        waypoints_model = ft.WaypointsTableModel("")
        waypoints_model.insertRows(
            0, rows=len(initial_waypoints), waypoints=initial_waypoints)
        self.window = tv.MSUITopViewWindow(model=waypoints_model, mainwindow=mainwindow, parent=mainwindow)
        self.window.show()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        yield
        self.window.hide()

    def test_tutorial_mode_mirrors_flighttrack_to_ftml(self):
        """
        In tutorial mode the displayed flight track is silently written to a
        fixed FTML, and the file is rewritten when the model changes.
        """
        from mslib.utils import constants
        ftml = os.path.join(constants.MSUI_CONFIG_PATH, "tutorial_flighttrack.ftml")
        if os.path.exists(ftml):
            os.remove(ftml)
        self.window.tutorial_mode = True
        model = self.window.waypoints_model
        # setting the model connects the change signals and writes the file
        self.window.setFlightTrackModel(model)
        assert os.path.exists(ftml)
        content = open(ftml).read()
        assert "<FlightTrack" in content
        assert content.count("<Waypoint") == len(model.waypoints)
        # a model change triggers a rewrite
        os.remove(ftml)
        model.insertRows(0, rows=1, waypoints=[ft.Waypoint(10.0, 20.0, 0)])
        assert os.path.exists(ftml)
        with open(ftml) as f:
            data = f.read()
            assert data.count("<Waypoint") == len(model.waypoints)
            assert '    <Waypoint location="" lat="10.0" lon="20.0" flightlevel="0">' in data.split('\n')

    def test_tutorial_mode_enable_save_writes_initial_ftml(self):
        """
        Views get their model via the constructor (bypassing setFlightTrackModel),
        so the creator calls enable_tutorial_flighttrack_save to write the initial
        FTML and start tracking (mscolab).
        """
        from mslib.utils import constants
        ftml = os.path.join(constants.MSUI_CONFIG_PATH, "tutorial_flighttrack.ftml")
        if os.path.exists(ftml):
            os.remove(ftml)
        self.window.tutorial_mode = True
        self.window.enable_tutorial_flighttrack_save()
        assert os.path.exists(ftml)
        with open(ftml) as f:
            data = f.read()
            assert data.count("<Waypoint") == len(self.window.waypoints_model.waypoints)

    def test_tutorial_screen_settings_records_canvas(self):
        """
        In tutorial mode the view persists the figure canvas rectangle so
        coordinate-based tutorials can map plot pixels to screen points.
        """
        settings = self.window._tutorial_screen_settings()
        assert "os_screen_region" in settings
        assert "canvas_screen_region" in settings
        _, _, win_w, win_h = settings["os_screen_region"]
        _, _, canvas_w, canvas_h = settings["canvas_screen_region"]
        # the canvas is a sub-widget of the window (smaller, never larger)
        assert 0 < canvas_w <= win_w
        assert 0 < canvas_h <= win_h

    def test_open_wms(self):
        self.window.cbTools.currentIndexChanged.emit(1)

    def test_open_sat(self):
        self.window.cbTools.currentIndexChanged.emit(2)

    def test_open_rs(self):
        self.window.cbTools.currentIndexChanged.emit(3)
        rsdock = self.window.docks[2].widget()
        QtTest.QTest.mouseClick(rsdock.cbDrawTangents, QtCore.Qt.LeftButton)
        rsdock.dsbTangentHeight.setValue(6)
        rsdock.dsbObsAngleAzimuth.setValue(70)
        QtTest.QTest.mouseClick(rsdock.cbDrawTangents, QtCore.Qt.LeftButton)
        rsdock.cbShowSolarAngle.setChecked(True)

    def test_open_kml(self):
        self.window.cbTools.currentIndexChanged.emit(4)

    def test_insert_point(self):
        """
        Test inserting a point inside and outside the canvas
        """
        self.window.mpl.navbar._actions['insert_wp'].trigger()
        assert len(self.window.waypoints_model.waypoints) == 3
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        assert len(self.window.waypoints_model.waypoints) == 4
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton, pos=QtCore.QPoint(1, 1))
        assert len(self.window.waypoints_model.waypoints) == 4
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        # click again on same position
        assert len(self.window.waypoints_model.waypoints) == 5

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question",
                return_value=QtWidgets.QMessageBox.Yes)
    def test_remove_point_yes(self, mockbox):
        self.window.mpl.navbar._actions['insert_wp'].trigger()
        assert len(self.window.waypoints_model.waypoints) == 3
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        assert len(self.window.waypoints_model.waypoints) == 4
        self.window.mpl.navbar._actions['delete_wp'].trigger()
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        assert len(self.window.waypoints_model.waypoints) == 3
        assert mockbox.call_count == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question",
                return_value=QtWidgets.QMessageBox.No)
    def test_remove_point_no(self, mockbox):
        self.window.mpl.navbar._actions['insert_wp'].trigger()
        assert len(self.window.waypoints_model.waypoints) == 3
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        assert len(self.window.waypoints_model.waypoints) == 4
        self.window.mpl.navbar._actions['delete_wp'].trigger()
        QtTest.QTest.mousePress(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        QtTest.QTest.mouseRelease(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        assert mockbox.call_count == 1
        assert len(self.window.waypoints_model.waypoints) == 4

    def test_move_point(self):
        self.window.mpl.navbar._actions['insert_wp'].trigger()
        assert len(self.window.waypoints_model.waypoints) == 3
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        assert len(self.window.waypoints_model.waypoints) == 4
        self.window.mpl.navbar._actions['move_wp'].trigger()
        QtTest.QTest.mousePress(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        point = QtCore.QPoint((self.window.width() // 3), self.window.height() // 2)
        QtTest.QTest.mouseMove(
            self.window.mpl.canvas, pos=point)
        QtTest.QTest.mouseRelease(
            self.window.mpl.canvas, QtCore.Qt.LeftButton, pos=point)
        assert len(self.window.waypoints_model.waypoints) == 4

    def test_roundtrip(self):
        """
        Test connecting the last and first point
        Test connecting the first point to itself
        """
        count = len(self.window.waypoints_model.waypoints)

        # Test if the last waypoint connects to the first
        self.window.update_roundtrip_enabled()
        assert self.window.is_roundtrip_possible()
        self.window.make_roundtrip()
        assert len(self.window.waypoints_model.waypoints) == count + 1
        first = self.window.waypoints_model.waypoints[0]
        dupe = self.window.waypoints_model.waypoints[-1]
        assert first.lat == dupe.lat and first.lon == dupe.lon

        # Check if roundtrip is disabled if the last and first point are equal
        self.window.update_roundtrip_enabled()
        assert not self.window.is_roundtrip_possible()
        assert not self.window.btRoundtrip.isEnabled()
        self.window.make_roundtrip()
        assert len(self.window.waypoints_model.waypoints) == count + 1

        # Remove connection
        self.window.waypoints_model.removeRows(count, 1)
        assert len(self.window.waypoints_model.waypoints) == count

    def test_map_options(self):
        self.window.mpl.canvas.map.set_graticule_visible(True)
        self.window.mpl.canvas.map.set_graticule_visible(False)
        self.window.mpl.canvas.map.set_fillcontinents_visible(False)
        self.window.mpl.canvas.map.set_fillcontinents_visible(True)
        self.window.mpl.canvas.map.set_coastlines_visible(False)
        self.window.mpl.canvas.map.set_coastlines_visible(True)

        with mock.patch("mslib.msui.mpl_map.get_airports", return_value=[{"type": "small_airport", "name": "Test",
                                                                          "latitude_deg": 52, "longitude_deg": 13,
                                                                          "elevation_ft": 0}]):
            self.window.mpl.canvas.map.set_draw_airports(True)
        with mock.patch("mslib.msui.mpl_map.get_airports", return_value=[]):
            self.window.mpl.canvas.map.set_draw_airports(True)
        with mock.patch("mslib.msui.mpl_map.get_airports", return_value=[{"type": "small_airport", "name": "Test",
                                                                          "latitude_deg": -52, "longitude_deg": -13,
                                                                          "elevation_ft": 0}]):
            self.window.mpl.canvas.map.set_draw_airports(True)

        with mock.patch("mslib.msui.mpl_map.get_airspaces", return_value=[{"name": "Test", "top": 1, "bottom": 0,
                                                                           "polygon": [(13, 52), (14, 53), (13, 52)],
                                                                           "country": "DE"}]):
            self.window.mpl.canvas.map.set_draw_airspaces(True)
        with mock.patch("mslib.msui.mpl_map.get_airspaces", return_value=[]):
            self.window.mpl.canvas.map.set_draw_airspaces(True)
        with mock.patch("mslib.msui.mpl_map.get_airspaces", return_value=[{"name": "Test", "top": 1, "bottom": 0,
                                                                           "polygon": [(-13, -52), (-14, -53),
                                                                                       (-13, -52)],
                                                                           "country": "DE"}]):
            self.window.mpl.canvas.map.set_draw_airspaces(True)


class Test_TopViewWMS:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot, mswms_server, tmp_path):
        self.url = mswms_server
        self.tempdir = tmp_path
        if not os.path.exists(self.tempdir):
            os.mkdir(self.tempdir)

        initial_waypoints = [ft.Waypoint(40., 25., 0), ft.Waypoint(60., -10., 0), ft.Waypoint(40., 10, 0)]
        waypoints_model = ft.WaypointsTableModel("")
        waypoints_model.insertRows(
            0, rows=len(initial_waypoints), waypoints=initial_waypoints)

        mainwindow = MSUIMainWindow()
        self.window = tv.MSUITopViewWindow(model=waypoints_model, mainwindow=mainwindow, parent=mainwindow)
        self.window.show()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        self.window.cbTools.currentIndexChanged.emit(1)
        self.wms_control = self.window.docks[0].widget()
        self.wms_control.multilayers.cbWMS_URL.setEditText("")
        yield
        self.window.hide()

    def query_server(self, qtbot, url):
        QtTest.QTest.keyClicks(self.wms_control.multilayers.cbWMS_URL, url)
        with qtbot.wait_signal(self.wms_control.cpdlg.canceled, timeout=WMS_REQUEST_TIMEOUT_MS):
            QtTest.QTest.mouseClick(self.wms_control.multilayers.btGetCapabilities, QtCore.Qt.LeftButton)

    def test_server_getmap(self, qtbot):
        """
        assert that a getmap call to a WMS server displays an image
        """
        self.query_server(qtbot, self.url)
        with qtbot.wait_signal(self.wms_control.image_displayed, timeout=WMS_REQUEST_TIMEOUT_MS):
            QtTest.QTest.mouseClick(self.wms_control.btGetMap, QtCore.Qt.LeftButton)
        assert self.window.getView().map.image is not None
        self.window.getView().set_settings({})
        self.window.getView().clear_figure()
        assert self.window.getView().map.image is None
        self.window.mpl.canvas.redraw_map()


class Test_MSUITopViewWindow:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        pass

    def test_kwargs_update_does_not_harm(self):
        initial_waypoints = [ft.Waypoint(40., 25., 0), ft.Waypoint(60., -10., 0), ft.Waypoint(40., 10, 0)]
        waypoints_model = ft.WaypointsTableModel("")
        waypoints_model.insertRows(0, rows=len(initial_waypoints), waypoints=initial_waypoints)
        mainwindow = MSUIMainWindow()
        self.window = tv.MSUITopViewWindow(model=waypoints_model, mainwindow=mainwindow, parent=mainwindow)

        # user_options is a global var
        from mslib.utils.config import user_options

        assert user_options['predefined_map_sections']['07 Europe (cyl)']['map'] == {'llcrnrlat': 35.0,
                                                                                     'llcrnrlon': -15.0,
                                                                                     'urcrnrlat': 65.0,
                                                                                     'urcrnrlon': 30.0}
