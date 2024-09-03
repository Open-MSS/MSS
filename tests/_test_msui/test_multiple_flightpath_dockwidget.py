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
    """
    Set-up for the docking widget
    """
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
    """
    test for conforming docking widget has initialized
    """
    _, multiple_flightpath_widget = main_window

    # Ensure the MultipleFlightpathControlWidget is correctly initialized
    assert multiple_flightpath_widget is not None
    assert multiple_flightpath_widget.color == (0, 0, 1, 1)


def test_setColour(main_window):
    """
    test for the filghttrack colour
    """
    main_window, multiple_flightpath_widget = main_window
    color_button = multiple_flightpath_widget.pushButton_color

    # Activate the first flight track
    activate_flight_track_at_index(main_window, 0)

    # Click on the second flight track in the docking widget
    click_on_flight_track_in_docking_widget_at_index(multiple_flightpath_widget, 1)

    # Simulate clicking the button to open the color dialog
    color_button.click()

    # Get a reference to the custom color dialog
    color_dialog = multiple_flightpath_widget.findChild(QtWidgets.QDialog)
    assert color_dialog is not None

    # Select the first color
    color = QtGui.QColor(color_dialog.colors[0])
    color_dialog.color_buttons[0].click()

    # Verify that the flight track data structure was updated with the new color
    wp_model = multiple_flightpath_widget.list_flighttrack.currentItem().flighttrack_model
    applied_color_rgba = multiple_flightpath_widget.get_color(wp_model)

    # Convert the applied_color_rgba to a QColor object
    applied_color = QtGui.QColor.fromRgbF(*applied_color_rgba)

    assert applied_color == color


def test_set_linewidth(main_window):
    """
    test for the filghttrack line width
    """
    main_window, multiple_flightpath_widget = main_window

    activate_flight_track_at_index(main_window, 0)
    click_on_flight_track_in_docking_widget_at_index(multiple_flightpath_widget, 1)

    # Ensure the current item is checked
    item = multiple_flightpath_widget.list_flighttrack.currentItem()
    item.setCheckState(QtCore.Qt.Checked)

    # mock update_flighttrack_patch method to check if it gets called
    with mock.patch.object(multiple_flightpath_widget, "update_flighttrack_patch") as mock_update_patch:
        # s.et the line width
        multiple_flightpath_widget.dsbx_linewidth.setValue(3.0)
        mock_update_patch.assert_called_once_with(item.flighttrack_model)

    # Verify the line width has been updated in dict_flighttrack
    wp_model = item.flighttrack_model
    assert multiple_flightpath_widget.dict_flighttrack[wp_model]["linewidth"] == 3.0
    assert multiple_flightpath_widget.change_linewidth is True


def test_set_transparency(main_window):
    """
    test for the filghttrack line transparency
    """
    main_window, multiple_flightpath_widget = main_window

    activate_flight_track_at_index(main_window, 0)
    click_on_flight_track_in_docking_widget_at_index(multiple_flightpath_widget, 1)

    item = multiple_flightpath_widget.list_flighttrack.currentItem()
    item.setCheckState(QtCore.Qt.Checked)

    # Mock the update_flighttrack_patch method
    with mock.patch.object(multiple_flightpath_widget, "update_flighttrack_patch") as mock_update_patch:

        multiple_flightpath_widget.hsTransparencyControl.setValue(50)
        mock_update_patch.assert_called_once_with(item.flighttrack_model)

    # Verify the transparency has been updated in dict_flighttrack
    wp_model = item.flighttrack_model
    assert multiple_flightpath_widget.dict_flighttrack[wp_model]["line_transparency"] == (50 / 100)
    assert multiple_flightpath_widget.change_line_transparency is True


def test_set_linestyle(main_window):
    """
    test for the filghttrack line style
    """
    main_window, multiple_flightpath_widget = main_window

    activate_flight_track_at_index(main_window, 0)
    click_on_flight_track_in_docking_widget_at_index(multiple_flightpath_widget, 1)

    item = multiple_flightpath_widget.list_flighttrack.currentItem()
    item.setCheckState(QtCore.Qt.Checked)

    # Mock the cbLineStyle setCurrentText and the update_flighttrack_patch method
    with mock.patch.object(multiple_flightpath_widget, "update_flighttrack_patch") as mock_update_patch:

        multiple_flightpath_widget.cbLineStyle.setCurrentText('Dashed')
        mock_update_patch.assert_called_once_with(item.flighttrack_model)

    # Verify the line style has been updated in dict_flighttrack
    wp_model = item.flighttrack_model
    expected_style = '--'
    assert multiple_flightpath_widget.dict_flighttrack[wp_model]["line_style"] == expected_style
    assert multiple_flightpath_widget.change_line_style is True
    mock_update_patch.assert_called_once_with(wp_model)


def test_selectAll(main_window):
    """
    Test the selectAll method by interacting with the UI directly.
    """
    main_window, multiple_flightpath_widget = main_window

    # Activate the first flight track
    activate_flight_track_at_index(main_window, 0)

    # Retrieve the index of the active flight track
    active_item = main_window.listFlightTracks.currentItem()
    active_index = main_window.listFlightTracks.row(active_item)

    # Check the "Select All" checkbox
    select_all_checkbox = multiple_flightpath_widget.cbSlectAll1
    select_all_checkbox.setCheckState(QtCore.Qt.Checked)

    # Verify that all items in the list are checked
    for i in range(multiple_flightpath_widget.list_flighttrack.count()):
        item = multiple_flightpath_widget.list_flighttrack.item(i)
        assert item.checkState() == QtCore.Qt.Checked

    # Uncheck the "Select All" checkbox
    select_all_checkbox.setCheckState(QtCore.Qt.Unchecked)

    # Verify that all items except the active one are unchecked
    for i in range(multiple_flightpath_widget.list_flighttrack.count()):
        item = multiple_flightpath_widget.list_flighttrack.item(i)
        if i == active_index:
            assert item.checkState() == QtCore.Qt.Checked  # Active item should remain checked
        else:
            assert item.checkState() == QtCore.Qt.Unchecked


def test_random_custom_color_selection(main_window):
    """
    Test that a random custom color is selected automatically each time
    and ensure that it is different from the previous selections.
    """
    _, multiple_flightpath_widget = main_window

    # Select random colors multiple times
    selected_colors = set()
    for _ in range(10):  # Test with 10 random selections
        color = multiple_flightpath_widget.get_random_color()
        normalized_color = tuple(int(c * 255) for c in color)
        assert normalized_color not in selected_colors, "Duplicate color selected!"
        selected_colors.add(normalized_color)

    # Check that all selected colors are from the custom_colors list
    for color in selected_colors:
        assert color in multiple_flightpath_widget.custom_colors


def test_update_flightpath_legend(main_window):
    """
    Test update_flightpath_legend to ensure only checked flight tracks
    are included in the legend with correct name, color, and style.
    """
    main_window, multiple_flightpath_widget = main_window

    # Activate the first flight track
    activate_flight_track_at_index(main_window, 0)

    # Set the first flight track as checked and the second as unchecked
    first_item = multiple_flightpath_widget.list_flighttrack.item(0)
    second_item = multiple_flightpath_widget.list_flighttrack.item(1)
    first_item.setCheckState(QtCore.Qt.Checked)
    second_item.setCheckState(QtCore.Qt.Unchecked)

    # Define color and style for the first flight track
    multiple_flightpath_widget.dict_flighttrack[first_item.flighttrack_model] = {
        "color": "#FF0000",
        "line_style": "--"
    }

    # Calling the method
    multiple_flightpath_widget.update_flightpath_legend()

    # Verify that only the checked flight track is included in the legend
    assert first_item.flighttrack_model.name in multiple_flightpath_widget.flightpath_dict
    assert second_item.flighttrack_model.name not in multiple_flightpath_widget.flightpath_dict

    # Verify that the color and style in the legend match the first flight track
    legend_color, legend_style = multiple_flightpath_widget.flightpath_dict[first_item.flighttrack_model.name]
    assert legend_color == "#FF0000"
    assert legend_style == "--"


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
