# -*- coding: utf-8 -*-
"""

    _tests._test_msui.test_multiple_flightpath_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tesst for the MultipleFlightpathControlWidget

    This file is part of MSS.

    :copyright: Copyright 2023 Reimar Bauer
    :copyright: Copyright 2023-2024 by the MSS team, see AUTHORS.
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
import pytest
from PyQt5 import QtTest, QtWidgets, QtCore, QtGui
from mock import mock

from mslib.msui import msui
# from mslib.msui.multiple_flightpath_dockwidget import MultipleFlightpathControlWidget
# from mslib.msui import flighttrack as ft
import mslib.msui.topview as tv


class Test_MultipleFlightpathControlWidget:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        # Start a MSUI window
        self.main_window = msui.MSUIMainWindow()
        self.main_window.show()
        qtbot.wait_exposed(self.main_window)

        # Create two flight tracks
        self.main_window.actionNewFlightTrack.trigger()
        self.main_window.actionNewFlightTrack.trigger()

        # Open a Top View window
        self.main_window.actionTopView.trigger()
        self.topview_window = self.main_window.listViews.currentItem().window

        # Switch to the Multiple Flightpath Widget
        self.topview_window.cbTools.setCurrentIndex(6)

        # Get a reference to the created MultipleFlightpathControlWidget
        self.multiple_flightpath_widget = self.topview_window.docks[tv.MULTIPLEFLIGHTPATH].widget()

        yield
        self.main_window.hide()

    def test_initialization(self):
        # Ensure the MultipleFlightpathControlWidget is correctly initialized
        assert self.multiple_flightpath_widget is not None
        assert self.multiple_flightpath_widget.color == (0, 0, 1, 1)

    @mock.patch("mslib.utils.colordialog.CustomColorDialog.exec_", return_value=QtWidgets.QDialog.Accepted)
    @mock.patch("mslib.utils.colordialog.CustomColorDialog.color_selected", new_callable=mock.Mock)
    def test_setColour(self, mock_color_selected, mockdlg):
        color_button = self.multiple_flightpath_widget.pushButton_color

        self._activate_flight_track_at_index(0)
        self.click_on_flight_track_in_docking_widget_at_index(1)

        # Simulate clicking the button to open the color dialog
        QtTest.QTest.mouseClick(color_button, QtCore.Qt.LeftButton)
        assert mockdlg.call_count == 1

        # Simulate a color being selected
        color = QtGui.QColor("#0000ff")  # Example color
        mock_color_selected.emit(color)

        # Ensure the color_selected signal was emitted
        mock_color_selected.emit.assert_called_with(color)

    def _activate_flight_track_at_index(self, index):
        # The main window must be on top
        self.main_window.activateWindow()
        # get the item by its index
        item = self.main_window.listFlightTracks.item(index)
        point = self.main_window.listFlightTracks.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.main_window.listFlightTracks.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtTest.QTest.mouseDClick(self.main_window.listFlightTracks.viewport(), QtCore.Qt.LeftButton, pos=point)

    def click_on_flight_track_in_docking_widget_at_index(self, index):
        # Activating the dock_widget window
        self.multiple_flightpath_widget.activateWindow()
        # get the item by its index
        item = self.multiple_flightpath_widget.list_flighttrack.item(index)
        point = self.multiple_flightpath_widget.list_flighttrack.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.multiple_flightpath_widget.list_flighttrack.viewport(),
                                QtCore.Qt.LeftButton, pos=point)
