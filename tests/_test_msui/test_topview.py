# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_topview
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.topview

    This file is part of MSS.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2024 by the MSS team, see AUTHORS.
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
import shutil
import tempfile
import mslib.msui.topview as tv
from PyQt5 import QtWidgets, QtCore, QtTest
from mslib.msui import flighttrack as ft
from mslib.msui.msui import MSUIMainWindow
from mslib.msui.mpl_qtwidget import _DEFAULT_SETTINGS_TOPVIEW


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
    def setup(self, qtbot, mswms_server):
        self.url = mswms_server
        self.tempdir = tempfile.mkdtemp()
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
        shutil.rmtree(self.tempdir)

    def query_server(self, qtbot, url):
        QtTest.QTest.keyClicks(self.wms_control.multilayers.cbWMS_URL, url)
        with qtbot.wait_signal(self.wms_control.cpdlg.canceled):
            QtTest.QTest.mouseClick(self.wms_control.multilayers.btGetCapabilities, QtCore.Qt.LeftButton)

    def test_server_getmap(self, qtbot):
        """
        assert that a getmap call to a WMS server displays an image
        """
        self.query_server(qtbot, self.url)
        with qtbot.wait_signal(self.wms_control.image_displayed):
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
