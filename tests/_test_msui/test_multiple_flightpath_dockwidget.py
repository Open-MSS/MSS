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
from PyQt5 import QtWidgets, QtCore, QtGui, QtTest
from unittest import mock

from mslib.msui import msui
import mslib.msui.topview as tv


@pytest.fixture
def main_window(qtbot):
    # Start a MSUI window
    window = msui.MSUIMainWindow()
    window.show()
    qtbot.wait_exposed(window)

    # Create two flight tracks
    window.actionNewFlightTrack.trigger()
    window.actionNewFlightTrack.trigger()

    # Open a Top View window
    window.actionTopView.trigger()
    topview_window = window.listViews.currentItem().window

    # Switch to the Multiple Flightpath Widget
    topview_window.cbTools.setCurrentIndex(6)

    # Get a reference to the created MultipleFlightpathControlWidget
    multiple_flightpath_widget = topview_window.docks[tv.MULTIPLEFLIGHTPATH].widget()

    yield window, multiple_flightpath_widget

    window.hide()


def test_initialization(main_window):
    _, multiple_flightpath_widget = main_window

    # Ensure the MultipleFlightpathControlWidget is correctly initialized
    assert multiple_flightpath_widget is not None
    assert multiple_flightpath_widget.color == (0, 0, 1, 1)


def test_setColour(main_window):
    _, multiple_flightpath_widget = main_window
    color_button = multiple_flightpath_widget.pushButton_color

    # Mock the exec_ method and color_selected signal of the CustomColorDialog
    with mock.patch("mslib.utils.colordialog.CustomColorDialog.exec_",
                    return_value=QtWidgets.QDialog.Accepted) as mock_exec, \
            mock.patch("mslib.utils.colordialog.CustomColorDialog.color_selected",
                       new_callable=mock.Mock) as mock_color_selected:
        # Activate the first flight track
        activate_flight_track_at_index(main_window[0], 0)

        # Click on the second flight track in the docking widget
        click_on_flight_track_in_docking_widget_at_index(multiple_flightpath_widget, 1)

        # Simulate clicking the button to open the color dialog
        color_button.click()
        assert mock_exec.call_count == 1

        # Simulate a color being selected
        color = QtGui.QColor("#0000ff")  # Example color
        mock_color_selected.emit(color)

        # Ensure the color_selected signal was emitted
        mock_color_selected.emit.assert_called_with(color)


def activate_flight_track_at_index(main_window, index):
    # The main window must be on top
    main_window.activateWindow()
    # get the item by its index
    item = main_window.listFlightTracks.item(index)
    point = main_window.listFlightTracks.visualItemRect(item).center()
    QtTest.QTest.mouseClick(main_window.listFlightTracks.viewport(), QtCore.Qt.LeftButton, pos=point)
    QtTest.QTest.mouseDClick(main_window.listFlightTracks.viewport(), QtCore.Qt.LeftButton, pos=point)


def click_on_flight_track_in_docking_widget_at_index(multiple_flightpath_widget, index):
    # Activating the dock_widget window
    multiple_flightpath_widget.activateWindow()
    # Get the item by its index
    item = multiple_flightpath_widget.list_flighttrack.item(index)
    multiple_flightpath_widget.list_flighttrack.setCurrentItem(item)
    # Simulate selection of the flight track by single clicking the item
    point = multiple_flightpath_widget.list_flighttrack.visualItemRect(item).center()
    QtTest.QTest.mouseClick(multiple_flightpath_widget.list_flighttrack.viewport(), QtCore.Qt.LeftButton, pos=point)
