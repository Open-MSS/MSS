# -*- coding: utf-8 -*-

"""

    tests._test_msui.test_sideview
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.sideview

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
import types
from PyQt5 import QtTest, QtCore, QtGui, QtWidgets
from mslib.msui import flighttrack as ft
import mslib.msui.sideview as tv
from mslib.msui.msui import MSUIMainWindow
from mslib.msui.viewplotter import _DEFAULT_SETTINGS_SIDEVIEW
from mslib.utils.config import config_loader

WMS_REQUEST_TIMEOUT_MS = (config_loader(dataset="WMS_request_timeout") + 5) * 1000


class Test_MSS_SV_OptionsDialog:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.window = tv.MSUI_SV_OptionsDialog(settings=_DEFAULT_SETTINGS_SIDEVIEW)
        self.window.show()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        yield
        self.window.hide()

    def test_show(self):
        pass

    def test_get(self):
        self.window.get_settings()

    def test_addLevel(self):
        QtTest.QTest.mouseClick(self.window.btAdd, QtCore.Qt.LeftButton)

    def test_removeLevel(self):
        QtTest.QTest.mouseClick(self.window.btDelete, QtCore.Qt.LeftButton)

    def test_getFlightLevels(self):
        levels = self.window.get_flight_levels()
        assert all(x == y for x, y in zip(levels, [300, 320, 340]))
        QtTest.QTest.mouseClick(self.window.btAdd, QtCore.Qt.LeftButton)
        levels = self.window.get_flight_levels()
        assert all(x == y for x, y in zip(levels, [0, 300, 320, 340]))

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
        Test the thickness of the flighttrack
        """
        # Verify initial value
        assert self.window.line_thickness == _DEFAULT_SETTINGS_SIDEVIEW.get("line_thickness", 2)

        # Simulate changing line thickness
        new_thickness = 5.00
        self.window.sbLineThickness.setValue(new_thickness)

        settings = self.window.get_settings()
        assert settings['line_thickness'] == new_thickness

    def test_line_style_change(self):
        """
        Test the style of the flighttrack
        """
        assert self.window.line_style == _DEFAULT_SETTINGS_SIDEVIEW.get("line_style", "Solid")

        # Simulate changing line style
        new_style = "Dashed"
        self.window.cbLineStyle.setCurrentText(new_style)

        settings = self.window.get_settings()
        assert settings['line_style'] == new_style

    def test_line_transparency_change(self):
        """
        Test the transparency of the flighttrack
        """
        assert self.window.line_transparency == _DEFAULT_SETTINGS_SIDEVIEW.get("line_transparency", 1.0)

        # Simulate changing transparency
        new_transparency = 50  # == 0.5
        self.window.hsTransparencyControl.setValue(new_transparency)

        settings = self.window.get_settings()
        assert settings['line_transparency'] == new_transparency / 100


class Test_MSSSideViewWindow:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        mainwindow = MSUIMainWindow()
        initial_waypoints = [ft.Waypoint(40., 25., 300), ft.Waypoint(60., -10., 400), ft.Waypoint(40., 10, 300)]

        waypoints_model = ft.WaypointsTableModel("")
        waypoints_model.insertRows(
            0, rows=len(initial_waypoints), waypoints=initial_waypoints)

        self.window = tv.MSUISideViewWindow(model=waypoints_model, parent=mainwindow)
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
        model.insertRows(0, rows=1, waypoints=[ft.Waypoint(10.0, 20.0, 400)])
        assert os.path.exists(ftml)
        with open(ftml) as f:
            data = f.read()
            assert data.count("<Waypoint") == len(model.waypoints)
            assert '    <Waypoint location="" lat="10.0" lon="20.0" flightlevel="400">' in data.split('\n')

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

    def test_open_wms(self):
        self.window.cbTools.currentIndexChanged.emit(1)

    def test_mouse_over(self):
        # Test mouse over
        QtTest.QTest.mouseMove(self.window.mpl.canvas, QtCore.QPoint(782, 266), -1)
        QtTest.QTest.mouseMove(self.window.mpl.canvas, QtCore.QPoint(20, 20), -1)

    @mock.patch("mslib.msui.sideview.MSUI_SV_OptionsDialog")
    def test_options(self, mockdlg):
        QtTest.QTest.mouseClick(self.window.btOptions, QtCore.Qt.LeftButton)
        assert mockdlg.call_count == 1
        assert mockdlg.return_value.setModal.call_count == 1
        assert mockdlg.return_value.exec_.call_count == 1
        assert mockdlg.return_value.destroy.call_count == 1

    def test_insert_point(self):
        """
        Test inserting a point inside and outside the canvas
        """
        self.window.mpl.navbar._actions['insert_wp'].trigger()
        assert len(self.window.waypoints_model.waypoints) == 3
        point = self.window.mpl.canvas.rect().center()
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton, pos=point)
        assert len(self.window.waypoints_model.waypoints) == 4
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton, pos=QtCore.QPoint(1, 1))
        assert len(self.window.waypoints_model.waypoints) == 4
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        # click again on same position
        assert len(self.window.waypoints_model.waypoints) == 5

    def _wp_pixel(self, index):
        """Exact display-pixel position (mpl bottom-left origin) of waypoint <index>."""
        wpi = self.window.mpl.canvas.waypoints_interactor
        xy = wpi.plotter.pathpatch.get_path().vertices[index]
        return wpi.plotter.pathpatch.get_transform().transform(xy)

    def _to_qt_point(self, xt, yt):
        """Convert a display-pixel position to a Qt widget position (top-left origin)."""
        height = self.window.mpl.canvas.figure.bbox.height
        return QtCore.QPoint(int(round(xt)), int(round(height - yt)))

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question",
                return_value=QtWidgets.QMessageBox.Yes)
    def test_rubberband_delete_multiple_points(self, mockbox):
        """
        Dragging a rubber-band box in Delete mode over several waypoints
        removes all of them in one step, after a single confirmation.
        """
        # Insert a waypoint in the middle of the track (waypoints 0 and 3 --
        # the first and last -- always sit exactly on the axes edges in this
        # profile view, so a well-separated rubber-band box needs an
        # interior point on each side).
        self.window.waypoints_model.insertRows(2, rows=1, waypoints=[ft.Waypoint(50., 0., 350)])
        assert len(self.window.waypoints_model.waypoints) == 4

        wp1_px = self._wp_pixel(1)
        wp2_px = self._wp_pixel(2)
        margin = 20
        origin = self._to_qt_point(min(wp1_px[0], wp2_px[0]) - margin, min(wp1_px[1], wp2_px[1]) - margin)
        corner = self._to_qt_point(max(wp1_px[0], wp2_px[0]) + margin, max(wp1_px[1], wp2_px[1]) + margin)

        self.window.mpl.navbar._actions['delete_wp'].trigger()
        canvas = self.window.mpl.canvas
        QtTest.QTest.mousePress(canvas, QtCore.Qt.LeftButton, pos=origin)
        QtTest.QTest.mouseMove(canvas, pos=corner)
        QtTest.QTest.mouseRelease(canvas, QtCore.Qt.LeftButton, pos=corner)

        assert mockbox.call_count == 1
        remaining = self.window.waypoints_model.waypoints
        assert len(remaining) == 2
        remaining_locations = sorted((round(wp.lat), round(wp.lon)) for wp in remaining)
        assert remaining_locations == [(40, 10), (40, 25)]

    def test_rubberband_click_empty_space_clears_selection(self):
        """
        A rubber-band drag selects waypoints; a subsequent plain click on
        empty space (no drag) clears that selection again.
        """
        self.window.waypoints_model.insertRows(2, rows=1, waypoints=[ft.Waypoint(50., 0., 350)])

        wp1_px = self._wp_pixel(1)
        wp2_px = self._wp_pixel(2)
        margin = 20
        origin = self._to_qt_point(min(wp1_px[0], wp2_px[0]) - margin, min(wp1_px[1], wp2_px[1]) - margin)
        corner = self._to_qt_point(max(wp1_px[0], wp2_px[0]) + margin, max(wp1_px[1], wp2_px[1]) + margin)

        self.window.mpl.navbar._actions['move_wp'].trigger()
        canvas = self.window.mpl.canvas
        wpi = canvas.waypoints_interactor
        QtTest.QTest.mousePress(canvas, QtCore.Qt.LeftButton, pos=origin)
        QtTest.QTest.mouseMove(canvas, pos=corner)
        QtTest.QTest.mouseRelease(canvas, QtCore.Qt.LeftButton, pos=corner)
        assert wpi._selected == {1, 2}

        # A plain click (no drag), still inside the profile axes but far
        # away from any waypoint, clears the selection.
        empty_spot = self._to_qt_point(wp1_px[0] - 300, wp1_px[1] - 150)
        QtTest.QTest.mouseClick(canvas, QtCore.Qt.LeftButton, pos=empty_spot)
        assert wpi._selected == set()

    def test_rubberband_select_and_move_multiple_points(self):
        """
        Selecting several waypoints with a rubber-band box in Move mode and
        then dragging one of the selected waypoints (changing its pressure)
        moves the whole group by the same offset, leaving unselected
        waypoints untouched.
        """
        self.window.waypoints_model.insertRows(2, rows=1, waypoints=[ft.Waypoint(50., 0., 350)])
        assert len(self.window.waypoints_model.waypoints) == 4

        canvas = self.window.mpl.canvas
        wpi = canvas.waypoints_interactor

        orig_wp0 = self.window.waypoints_model.waypoint_data(0).pressure
        orig_wp1 = self.window.waypoints_model.waypoint_data(1).pressure
        orig_wp2 = self.window.waypoints_model.waypoint_data(2).pressure
        orig_wp3 = self.window.waypoints_model.waypoint_data(3).pressure

        wp1_px = self._wp_pixel(1)
        wp2_px = self._wp_pixel(2)
        margin = 20
        origin = self._to_qt_point(min(wp1_px[0], wp2_px[0]) - margin, min(wp1_px[1], wp2_px[1]) - margin)
        corner = self._to_qt_point(max(wp1_px[0], wp2_px[0]) + margin, max(wp1_px[1], wp2_px[1]) + margin)

        self.window.mpl.navbar._actions['move_wp'].trigger()

        # Rubber-band select waypoints 1 and 2 (waypoints 0 and 3 are well outside the box).
        QtTest.QTest.mousePress(canvas, QtCore.Qt.LeftButton, pos=origin)
        QtTest.QTest.mouseMove(canvas, pos=corner)
        QtTest.QTest.mouseRelease(canvas, QtCore.Qt.LeftButton, pos=corner)
        assert wpi._selected == {1, 2}

        # Press down on waypoint 1 (part of the selection) to start the drag.
        start = self._to_qt_point(*wp1_px)
        QtTest.QTest.mousePress(canvas, QtCore.Qt.LeftButton, pos=start)
        assert wpi._ind == 1

        # Headless Qt does not reliably deliver synthetic mouse-move events
        # while a button is held, so the drag step is driven directly with a
        # synthetic event, exercising the same motion_notify_callback() that
        # a real drag would call. Only the y (pressure) coordinate matters in
        # the side view -- the x position of a waypoint is locked.
        delta_pressure = 3000.0
        wpi.motion_notify_callback(types.SimpleNamespace(
            ydata=orig_wp1 + delta_pressure, inaxes=True, button=1, x=0, y=0))

        QtTest.QTest.mouseRelease(canvas, QtCore.Qt.LeftButton, pos=start)

        new_wp0 = self.window.waypoints_model.waypoint_data(0)
        new_wp1 = self.window.waypoints_model.waypoint_data(1)
        new_wp2 = self.window.waypoints_model.waypoint_data(2)
        new_wp3 = self.window.waypoints_model.waypoint_data(3)

        # The unselected (edge) waypoints must not have moved at all.
        assert new_wp0.pressure == pytest.approx(orig_wp0)
        assert new_wp3.pressure == pytest.approx(orig_wp3)

        # Both selected waypoints must have moved by (approximately) the same
        # amount -- setData() quantizes pressure to the nearest flight level,
        # so an exact match isn't expected.
        assert new_wp1.pressure == pytest.approx(orig_wp1 + delta_pressure, abs=200)
        assert new_wp2.pressure == pytest.approx(orig_wp2 + delta_pressure, abs=200)

    def test_switch_tool_after_move_does_not_crash(self):
        """
        Regression test: after moving waypoints in Move mode, switching to
        Delete (or Insert) mode must not raise and must uncheck the
        previous tool's button.

        This used to call VPathInteractor.redraw_path(), which only
        HPathInteractor defines (VPathInteractor only has redraw_figure()),
        raising an AttributeError that aborted the mode switch -- which is
        also why the previously active tool button stayed visibly checked.
        """
        self.window.mpl.navbar._actions['move_wp'].trigger()
        canvas = self.window.mpl.canvas
        wpi = canvas.waypoints_interactor
        point = self._to_qt_point(*self._wp_pixel(1))
        QtTest.QTest.mousePress(canvas, QtCore.Qt.LeftButton, pos=point)
        QtTest.QTest.mouseRelease(canvas, QtCore.Qt.LeftButton, pos=point)
        assert self.window.mpl.navbar._actions['move_wp'].isChecked()
        # A non-empty selection is required to exercise the crash this test guards against.
        assert wpi._selected

        self.window.mpl.navbar._actions['delete_wp'].trigger()

        assert not self.window.mpl.navbar._actions['move_wp'].isChecked()
        assert self.window.mpl.navbar._actions['delete_wp'].isChecked()

    def test_y_axes(self):
        self.window.getView().get_settings()["secondary_axis"] = "pressure altitude"
        self.window.getView().set_settings(self.window.getView().get_settings())
        self.window.getView().get_settings()["secondary_axis"] = "flight level"
        self.window.getView().set_settings(self.window.getView().get_settings())


class Test_SideViewWMS:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot, mswms_server, tmp_path):
        mainwindow = MSUIMainWindow()
        self.url = mswms_server
        self.tempdir = tmp_path
        if not os.path.exists(self.tempdir):
            os.mkdir(self.tempdir)

        initial_waypoints = [ft.Waypoint(40., 25., 0), ft.Waypoint(60., -10., 0), ft.Waypoint(40., 10, 0)]
        waypoints_model = ft.WaypointsTableModel("")
        waypoints_model.insertRows(
            0, rows=len(initial_waypoints), waypoints=initial_waypoints)
        self.window = tv.MSUISideViewWindow(model=waypoints_model, parent=mainwindow)
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
        assert self.window.getView().plotter.image is not None

        self.window.getView().plotter.clear_figure()
        assert self.window.getView().plotter.image is None
