# -*- coding: utf-8 -*-
"""

    mslib.multiple_flightpath_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Control Widget to configure multiple flightpath on topview.

    This file is part of MSS.

    :copyright: Copyright 2022 Jatin Jain
    :copyright: Copyright 2022-2024 by the MSS team, see AUTHORS.
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
import random
import requests
import json
from PyQt5 import QtWidgets, QtGui, QtCore
from mslib.msui.qt5 import ui_multiple_flightpath_dockwidget as ui
from mslib.msui import flighttrack as ft
import mslib.msui.msui_mainwindow as msui_mainwindow
from mslib.utils.verify_user_token import verify_user_token
from mslib.utils.qt import Worker
from mslib.utils.config import config_loader
from urllib.parse import urljoin
from mslib.utils.colordialog import CustomColorDialog


class QMscolabOperationsListWidgetItem(QtWidgets.QListWidgetItem):
    """
    """

    def __init__(self, flighttrack_model, op_id: int, parent=None, user_type=QtWidgets.QListWidgetItem.UserType):
        view_name = flighttrack_model.name
        super().__init__(
            view_name, parent, user_type
        )
        self.parent = parent
        self.flighttrack_model = flighttrack_model
        self.op_id = op_id


class MultipleFlightpath:
    """
    Represent a Multiple FLightpath
    """

    def __init__(self, mapcanvas, wp, linewidth=2.0, color='blue', line_transparency=1.0, line_style="solid"):
        self.map = mapcanvas
        self.flightlevel = None
        self.comments = ''
        self.patches = []
        self.waypoints = wp
        self.linewidth = linewidth
        self.line_transparency = line_transparency
        self.line_style = line_style
        self.color = color
        self.draw()

    def draw_line(self, x, y):
        self.patches.append(self.map.plot(x, y, color=self.color, linewidth=self.linewidth,
                                          alpha=self.line_transparency, linestyle=self.line_style))

    def compute_xy(self, lon, lat):
        x, y = self.map.gcpoints_path(lon, lat)
        return x, y

    def get_lonlat(self):
        lon = []
        lat = []
        for i in range(len(self.waypoints)):
            lat.append(self.waypoints[i][0])
            lon.append(self.waypoints[i][1])
        return lat, lon

    def update(self, linewidth=None, color=None, line_transparency=None, line_style=None):
        if linewidth is not None:
            self.linewidth = linewidth
        if color is not None:
            self.color = color
        if line_transparency is not None:
            self.line_transparency = line_transparency
        if line_style is not None:
            self.line_style = line_style

        for patch in self.patches:  # allows dynamic updating of the flight path's appearance without needing to
            # remove and redraw the entire path
            for elem in patch:
                elem.set_linewidth(self.linewidth)
                elem.set_color(self.color)
                elem.set_alpha(self.line_transparency)
                elem.set_linestyle(self.line_style)
        self.map.ax.figure.canvas.draw()

    def draw(self):
        lat, lon = self.get_lonlat()
        x, y = self.compute_xy(lon, lat)
        self.draw_line(x, y)
        self.map.ax.figure.canvas.draw()

    def remove(self):
        for patch in self.patches:
            for elem in patch:
                elem.remove()
        self.patches = []
        self.map.ax.figure.canvas.draw()


class MultipleFlightpathControlWidget(QtWidgets.QWidget, ui.Ui_MultipleViewWidget):
    """
    This class provides the interface for plotting Multiple Flighttracks
    on the TopView canvas.
    """

    # ToDO: Make a new parent class with all the functions in this class and inherit them
    #  in MultipleFlightpathControlWidget and MultipleFlightpathOperations classes.

    signal_parent_closes = QtCore.pyqtSignal()

    custom_colors = [
        (128, 0, 0), (195, 31, 89), (245, 151, 87), (253, 228, 66), (0, 0, 255),
        (96, 195, 110), (101, 216, 242), (164, 70, 190), (241, 90, 234), (185, 186, 187),
        (230, 25, 75), (210, 207, 148), (53, 110, 51), (245, 130, 49), (44, 44, 44),
        (0, 0, 117), (154, 99, 36), (128, 128, 0), (0, 0, 0)
        # Add more colors as needed
    ]

    # Define the mapping from combo box text to line style codes
    line_styles = {
        "Solid": '-',
        "Dashed": '--',
        "Dotted": ':',
        "Dash-dot": '-.'
    }

    # Reverse dictionary
    line_styles_reverse = {v: k for k, v in line_styles.items()}

    def __init__(self, parent=None, view=None, listFlightTracks=None,
                 listOperationsMSC=None, category=None, activeFlightTrack=None, active_op_id=None,
                 mscolab_server_url=None, token=None):
        super().__init__(parent)
        # ToDO: Remove all patches, on closing dockwidget.
        self.ui = parent
        self.setupUi(self)
        self.view = view  # canvas
        self.flight_path = None  # flightpath object
        self.dict_flighttrack = {}  # Dictionary of flighttrack data: patch,color,wp_model
        self.used_colors = []  # Instance variable to track used colors
        self.active_flight_track = activeFlightTrack
        self.active_op_id = active_op_id
        self.msc_category = category  # object of active category
        self.listOperationsMSC = listOperationsMSC
        self.listFlightTracks = listFlightTracks
        self.mscolab_server_url = mscolab_server_url
        self.token = token
        self.flightpath_dict = {}
        if self.ui is not None:
            ft_settings_dict = self.ui.getView().get_settings()
            self.color = ft_settings_dict["colour_ft_vertices"]
        else:
            self.color = self.get_random_color()
        self.obb = []

        self.operations = None
        self.operation_list = False
        self.flighttrack_list = True

        # Set flags
        # ToDo: Use invented constants for initialization.
        self.flighttrack_added = False
        self.flighttrack_activated = False
        self.color_change = False
        self.change_linewidth = False
        self.change_line_transparency = False
        self.change_line_style = False
        self.dsbx_linewidth.setValue(2.0)
        self.hsTransparencyControl.setValue(100)
        self.cbLineStyle.addItems(["Solid", "Dashed", "Dotted", "Dash-dot"])  # Item added in the list
        self.cbLineStyle.setCurrentText("Solid")

        # Disable the buttons initially
        self.pushButton_color.setEnabled(False)
        self.dsbx_linewidth.setEnabled(False)
        self.hsTransparencyControl.setEnabled(False)
        self.cbLineStyle.setEnabled(False)
        self.labelStatus.setText("Status: Select a flighttrack/operation")

        # Connect Signals and Slots
        self.listFlightTracks.model().rowsInserted.connect(self.wait)
        self.listFlightTracks.model().rowsRemoved.connect(self.flighttrackRemoved)
        self.ui.signal_activate_flighttrack1.connect(self.get_active)
        self.list_flighttrack.itemChanged.connect(self.flagop)

        self.pushButton_color.clicked.connect(self.select_color)
        self.ui.signal_ft_vertices_color_change.connect(self.ft_vertices_color)
        self.dsbx_linewidth.valueChanged.connect(self.set_linewidth)
        self.hsTransparencyControl.valueChanged.connect(self.set_transparency)
        self.cbLineStyle.currentTextChanged.connect(self.set_linestyle)
        self.cbSlectAll1.stateChanged.connect(self.selectAll)
        self.ui.signal_login_mscolab.connect(self.login)

        self.colorPixmap.setPixmap(self.show_color_pixmap(self.color))

        self.list_flighttrack.itemClicked.connect(self.listFlighttrack_itemClicked)

        if self.mscolab_server_url is not None:
            self.connect_mscolab_server()

        if parent is not None:
            parent.viewCloses.connect(lambda: self.signal_parent_closes.emit())

        # Load flighttracks
        for index in range(self.listFlightTracks.count()):
            wp_model = self.listFlightTracks.item(index).flighttrack_model
            self.create_list_item(wp_model)

        self.activate_flighttrack()
        self.multipleflightrack_worker = Worker(None)

    @QtCore.pyqtSlot()
    def logout(self):
        if self.operations is not None:
            self.operations.logout_mscolab()
            self.ui.signal_listFlighttrack_doubleClicked.disconnect()
            self.ui.signal_permission_revoked.disconnect()
            self.ui.signal_render_new_permission.disconnect()
            self.operations = None
            self.flighttrack_list = True
            self.operation_list = False
            for idx in range(len(self.obb)):
                del self.obb[idx]

    @QtCore.pyqtSlot(str, str)
    def login(self, url, token):
        self.mscolab_server_url = url
        self.token = token
        self.connect_mscolab_server()

    def connect_mscolab_server(self):
        if self.active_op_id is not None:
            self.deactivate_all_flighttracks()
        self.operations = MultipleFlightpathOperations(self, self.mscolab_server_url, self.token,
                                                       self.list_operation_track,
                                                       self.active_op_id,
                                                       self.listOperationsMSC, self.view)
        self.obb.append(self.operations)

        self.ui.signal_permission_revoked.connect(lambda op_id: self.operations.permission_revoked(op_id))
        self.ui.signal_render_new_permission.connect(lambda op_id, path: self.operations.render_permission(op_id, path))
        # Signal emitted, on activation of operation from MSUI
        self.ui.signal_activate_operation.connect(self.update_op_id)
        self.ui.signal_operation_added.connect(self.add_operation_slot)
        self.ui.signal_operation_removed.connect(self.remove_operation_slot)

        # deactivate vice versa selection of Operation or Flight Track
        self.list_operation_track.itemClicked.connect(self.operations.listOperations_itemClicked)

        # deactivate operation or flighttrack
        self.listOperationsMSC.itemDoubleClicked.connect(self.deactivate_all_flighttracks)
        self.ui.signal_listFlighttrack_doubleClicked.connect(self.operations.deactivate_all_operations)

        # Mscolab Server logout
        self.ui.signal_logout_mscolab.connect(self.logout)

    def update(self):
        for entry in self.dict_flighttrack.values():
            entry["patch"].update()

    def remove(self):
        for entry in self.dict_flighttrack.values():
            entry["patch"].remove()

    def wait(self, parent, start, end):
        """
        Adding of flighttrack takes time we use a worker new thread(it avoid freezing of UI).
        """
        self.multipleflightrack_worker.function = lambda: self.flighttrackAdded(parent, start, end)
        self.multipleflightrack_worker.start()
        self.flighttrack_added = True

    def flagop(self):
        if self.flighttrack_added:
            self.flighttrack_added = False
        elif self.flighttrack_activated:
            self.flighttrack_activated = False
        elif self.color_change:
            self.color_change = False
        else:
            self.drawInactiveFlighttracks(self.list_flighttrack)

    def flighttrackAdded(self, parent, start, end):
        """
        Slot to add flighttrack.
        """
        wp_model = self.listFlightTracks.item(start).flighttrack_model
        self.create_list_item(wp_model)
        if self.mscolab_server_url is not None:
            self.operations.deactivate_all_operations()
        self.activate_flighttrack()

    @QtCore.pyqtSlot(tuple)
    def ft_vertices_color(self, color):
        self.color = color
        self.colorPixmap.setPixmap(self.show_color_pixmap(color))

        if self.flighttrack_list:
            self.dict_flighttrack[self.active_flight_track]["color"] = color
            for index in range(self.list_flighttrack.count()):
                if self.list_flighttrack.item(index).flighttrack_model == self.active_flight_track:
                    self.list_flighttrack.item(index).setIcon(
                        self.show_color_icon(self.get_color(self.active_flight_track)))
                    break
        elif self.operation_list:
            self.operations.ft_color_update(color)

    @QtCore.pyqtSlot(int, str)
    def add_operation_slot(self, op_id, path):
        self.operations.operationsAdded(op_id, path)

    @QtCore.pyqtSlot(int)
    def remove_operation_slot(self, op_id):
        self.operations.operationRemoved(op_id)

    @QtCore.pyqtSlot(int)
    def update_op_id(self, op_id):
        self.operations.get_op_id(op_id)

    @QtCore.pyqtSlot(ft.WaypointsTableModel)
    def get_active(self, active_flighttrack):
        self.update_last_flighttrack()
        self.active_flight_track = active_flighttrack
        self.activate_flighttrack()

    def save_waypoint_model_data(self, wp_model, listWidget):
        wp_data = [(wp.lat, wp.lon, wp.flightlevel, wp.location, wp.comments) for wp in wp_model.all_waypoint_data()]
        if self.dict_flighttrack[wp_model] is None:
            self.create_list_item(wp_model)
        self.dict_flighttrack[wp_model]["wp_data"] = wp_data

    def normalize_rgb(self, rgb):
        return tuple(channel / 255 for channel in rgb)

    def get_random_color(self):
        """
        Get a random color from custom colors ensuring no repeats.
        """
        available_colors = [color for color in self.custom_colors if color not in self.used_colors]
        if not available_colors:
            # Reset the used colors if all colors have been used
            self.used_colors = []
            available_colors = self.custom_colors.copy()

        selected_color = random.choice(available_colors)
        self.used_colors.append(selected_color)
        return self.normalize_rgb(selected_color)

    def create_list_item(self, wp_model):
        """
        PyQt5 method : Add items in list and add checkbox functionality
        """
        # Create new key in dict
        self.dict_flighttrack[wp_model] = {}
        self.dict_flighttrack[wp_model]["patch"] = None
        self.dict_flighttrack[wp_model]["color"] = self.get_random_color()
        self.dict_flighttrack[wp_model]["linewidth"] = 2.0
        self.dict_flighttrack[wp_model]["line_transparency"] = 1.0
        self.dict_flighttrack[wp_model]["line_style"] = "solid"
        self.dict_flighttrack[wp_model]["wp_data"] = []
        self.dict_flighttrack[wp_model]["checkState"] = False

        self.save_waypoint_model_data(wp_model, self.list_flighttrack)

        listItem = msui_mainwindow.QFlightTrackListWidgetItem(wp_model, self.list_flighttrack)
        listItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
        if not self.flighttrack_added:
            self.flighttrack_added = True
        listItem.setCheckState(QtCore.Qt.Unchecked)
        if not self.flighttrack_added:
            self.flighttrack_added = True

        # Show flighttrack color icon
        listItem.setIcon(self.show_color_icon(self.get_color(wp_model)))
        self.update_flightpath_legend()

        return listItem

    def selectAll(self, state):
        """
        Select/deselect local operations
        """
        for i in range(self.list_flighttrack.count()):
            item = self.list_flighttrack.item(i)
            if self.active_flight_track is not None and item.flighttrack_model == self.active_flight_track:
                item.setCheckState(QtCore.Qt.Checked)  # Ensure the active flight track remains checked
            else:
                item.setCheckState(state)

    def select_color(self):
        """
        Sets the color of selected flighttrack when Change Color is clicked.
        """
        # ToDO: Use color defined in options for initial color of active flight path.
        #  afterwards deactivate the color change button in options and it needs also
        #  the check mark for enabled, but can't be changed (disabled). At the moment
        #  the dockingwidget is closed the button and checkmark has to become activated again.

        if self.list_flighttrack.currentItem() is not None:
            if (hasattr(self.list_flighttrack.currentItem(), "checkState")) and (
                    self.list_flighttrack.currentItem().checkState() == QtCore.Qt.Checked):
                wp_model = self.list_flighttrack.currentItem().flighttrack_model
                if wp_model == self.active_flight_track:
                    self.error_dialog = QtWidgets.QErrorMessage()
                    self.error_dialog.showMessage('Use "options" to change color of an activated flighttrack.')
                else:
                    color_dialog = CustomColorDialog(self)
                    color_dialog.color_selected.connect(lambda color: self.apply_color(wp_model, color))
                    color_dialog.show()
            else:
                self.labelStatus.setText("Status: Check Mark the flighttrack to change its color.")
        elif self.list_operation_track.currentItem() is not None:
            self.operations.select_color()
        else:
            self.labelStatus.setText("Status: No flighttrack selected")

    def apply_color(self, wp_model, color):
        if color.isValid():
            self.dict_flighttrack[wp_model]["color"] = color.getRgbF()
            self.color_change = True
            self.list_flighttrack.currentItem().setIcon(self.show_color_icon(self.get_color(wp_model)))
            self.dict_flighttrack[wp_model]["patch"].update(
                color=self.dict_flighttrack[wp_model]["color"])
            self.update_flightpath_legend()

    def get_color(self, wp_model):
        """
        Returns color of respective flighttrack.
        """
        return self.dict_flighttrack[wp_model]["color"]

    def show_color_pixmap(self, clr):
        pixmap = QtGui.QPixmap(20, 10)
        pixmap.fill(QtGui.QColor(int(clr[0] * 255), int(clr[1] * 255), int(clr[2] * 255)))
        return pixmap

    def show_color_icon(self, clr):
        """
        Creating object of QPixmap for displaying icon inside the listWidget.
        """
        pixmap = self.show_color_pixmap(clr)
        return QtGui.QIcon(pixmap)

    def set_linewidth(self):
        """
        Change the line width of selected flighttrack.
        """
        if self.list_flighttrack.currentItem() is not None:
            if (hasattr(self.list_flighttrack.currentItem(), "checkState")) and (
                    self.list_flighttrack.currentItem().checkState() == QtCore.Qt.Checked):
                wp_model = self.list_flighttrack.currentItem().flighttrack_model
                if wp_model != self.active_flight_track:
                    if self.dict_flighttrack[wp_model]["linewidth"] != self.dsbx_linewidth.value():
                        self.dict_flighttrack[wp_model]["linewidth"] = self.dsbx_linewidth.value()
                        self.update_flighttrack_patch(wp_model)
                        self.change_linewidth = True
                        self.dsbx_linewidth.setValue(self.dict_flighttrack[wp_model]["linewidth"])
            else:
                item = self.list_flighttrack.currentItem()
                self.dsbx_linewidth.setEnabled(item is not None and item.checkState() == QtCore.Qt.Checked)
                self.labelStatus.setText("Status: Check Mark the flighttrack to change its line width.")
        elif self.list_operation_track.currentItem() is not None:
            self.operations.set_linewidth()
        else:
            self.labelStatus.setText("Status: No flighttrack selected")

    def set_transparency(self):
        """
        Change the line transparency of the selected flight track.
        """
        if self.list_flighttrack.currentItem() is not None:
            if (hasattr(self.list_flighttrack.currentItem(), "checkState")) and (
                    self.list_flighttrack.currentItem().checkState() == QtCore.Qt.Checked):
                wp_model = self.list_flighttrack.currentItem().flighttrack_model
                if wp_model != self.active_flight_track:
                    new_transparency = self.hsTransparencyControl.value() / 100.0
                    if self.dict_flighttrack[wp_model]["line_transparency"] != new_transparency:
                        self.dict_flighttrack[wp_model]["line_transparency"] = new_transparency
                        self.update_flighttrack_patch(wp_model)
                        self.change_line_transparency = True
                        self.hsTransparencyControl.setValue(
                            int(self.dict_flighttrack[wp_model]["line_transparency"] * 100))
            else:
                item = self.list_flighttrack.currentItem()
                self.hsTransparencyControl.setEnabled(item is not None and item.checkState() == QtCore.Qt.Checked)
                self.labelStatus.setText("Status: Check Mark the flighttrack to change its transparency.")
        elif self.list_operation_track.currentItem() is not None:
            self.operations.set_transparency()
        else:
            self.labelStatus.setText("Status: No flighttrack selected")

    def set_linestyle(self):
        """
        Change the line style of the selected flight track.
        """

        if self.list_flighttrack.currentItem() is not None:
            if (hasattr(self.list_flighttrack.currentItem(), "checkState")) and (
                    self.list_flighttrack.currentItem().checkState() == QtCore.Qt.Checked):
                wp_model = self.list_flighttrack.currentItem().flighttrack_model
                if wp_model != self.active_flight_track:
                    selected_style = self.cbLineStyle.currentText()
                    new_linestyle = self.line_styles.get(selected_style, '-')  # Default to 'solid'

                    if self.dict_flighttrack[wp_model]["line_style"] != new_linestyle:
                        self.dict_flighttrack[wp_model]["line_style"] = new_linestyle
                        self.update_flighttrack_patch(wp_model)
                        self.change_line_style = True
                        self.cbLineStyle.setCurrentText(self.dict_flighttrack[wp_model]["line_style"])
            else:
                item = self.list_flighttrack.currentItem()
                self.cbLineStyle.setEnabled(item is not None and item.checkState() == QtCore.Qt.Checked)
                self.labelStatus.setText("Status: Check Mark the flighttrack to change its line style.")
        elif self.list_operation_track.currentItem() is not None:
            self.operations.set_linestyle()
        else:
            self.labelStatus.setText("Status: No flighttrack selected")

    def update_flighttrack_patch(self, wp_model):
        """
        Update the flighttrack patch with the latest attributes.
        """
        if self.dict_flighttrack[wp_model]["patch"] is not None:
            self.dict_flighttrack[wp_model]["patch"].remove()
        self.dict_flighttrack[wp_model]["patch"] = MultipleFlightpath(
            self.view.map,
            self.dict_flighttrack[wp_model]["wp_data"],
            color=self.dict_flighttrack[wp_model]["color"],
            linewidth=self.dict_flighttrack[wp_model]["linewidth"],
            line_transparency=self.dict_flighttrack[wp_model]["line_transparency"],
            line_style=self.dict_flighttrack[wp_model]["line_style"]
        )
        self.update_flightpath_legend()

    def update_flightpath_legend(self):
        """
        Collects flight path data and updates the legend in the TopView.
        Only checked flight tracks will be included in the legend.
        Unchecked flight tracks will be removed from the flightpath_dict.
        """
        # Iterate over all items in the list_flighttrack
        for i in range(self.list_flighttrack.count()):
            listItem = self.list_flighttrack.item(i)
            wp_model = listItem.flighttrack_model

            # If the flight track is checked, add/update it in the dictionary
            if listItem.checkState() == QtCore.Qt.Checked:
                name = wp_model.name if hasattr(wp_model, 'name') else 'Unnamed flighttrack'
                color = self.dict_flighttrack[wp_model].get('color', '#000000')  # Default to black
                linestyle = self.dict_flighttrack[wp_model].get('line_style', '-')  # Default to solid line
                self.flightpath_dict[name] = (color, linestyle)
            # If the flight track is unchecked, ensure it is removed from the dictionary
            else:
                name = wp_model.name if hasattr(wp_model, 'name') else 'Unnamed flighttrack'
                if name in self.flightpath_dict:
                    del self.flightpath_dict[name]

        # Update the legend in the view with the filtered flightpath_dict
        self.view.update_flightpath_legend(self.flightpath_dict)

    def flighttrackRemoved(self, parent, start, end):
        """
        Slot to remove flighttrack.
        """
        # ToDo: Add try..catch block
        if self.dict_flighttrack[self.list_flighttrack.item(start).flighttrack_model]["patch"] is None:
            del self.dict_flighttrack[self.list_flighttrack.item(start).flighttrack_model]
        else:
            self.dict_flighttrack[self.list_flighttrack.item(start).flighttrack_model]["patch"].remove()
        self.list_flighttrack.takeItem(start)
        self.update_flightpath_legend()

    def update_last_flighttrack(self):
        """
        Update waypoint model for most recently activated flighttrack in dict_flighttrack.
        """
        if self.active_flight_track is not None:
            self.save_waypoint_model_data(
                self.active_flight_track,
                self.list_flighttrack)  # Before activating new flighttrack, update waypoints of previous flighttrack

    def activate_flighttrack(self):
        """
        Activate the selected flighttrack and ensure its visual properties are correctly set.
        """
        font = QtGui.QFont()
        for i in range(self.list_flighttrack.count()):
            listItem = self.list_flighttrack.item(i)
            wp_model = listItem.flighttrack_model

            if self.active_flight_track == wp_model:  # active flighttrack
                listItem.setIcon(self.show_color_icon(self.color))
                font.setBold(True)

                # Ensure the patch is updated with the correct attributes
                if self.dict_flighttrack[wp_model]["patch"] is not None:
                    self.dict_flighttrack[wp_model]["patch"].remove()

                if listItem.checkState() == QtCore.Qt.Unchecked:
                    listItem.setCheckState(QtCore.Qt.Checked)
                    self.set_activate_flag()
                listItem.setFlags(listItem.flags() & ~QtCore.Qt.ItemIsUserCheckable)  # make activated track uncheckable
            else:
                listItem.setIcon(self.show_color_icon(self.get_color(wp_model)))
                font.setBold(False)
                listItem.setFlags(listItem.flags() | QtCore.Qt.ItemIsUserCheckable)
            self.set_activate_flag()
            listItem.setFont(font)
        self.update_line_properties_state()
        self.flagop()
        if self.operations is not None:
            self.operations.set_flag()

    def update_line_properties_state(self):
        """
        Check if there is an active flight track selected. If there is an active flight track selected in the
        list widget, disable these UI elements else enable
        """
        if self.list_flighttrack.currentItem() is not None:
            wp_model = self.list_flighttrack.currentItem().flighttrack_model
            self.enable_disable_line_style_buttons(wp_model != self.active_flight_track)

    def enable_disable_line_style_buttons(self, enable):
        self.pushButton_color.setEnabled(enable)
        self.dsbx_linewidth.setEnabled(enable)
        self.hsTransparencyControl.setEnabled(enable)
        self.cbLineStyle.setEnabled(enable)
        if enable:
            self.labelStatus.setText("Status: ✔ flight track selected")
        else:
            self.labelStatus.setText(
                "Status: You can change line attributes of the active flighttrack through options only.")

    def drawInactiveFlighttracks(self, list_widget):
        """
        Draw inactive flighttracks
        """
        for entry in self.dict_flighttrack.values():
            if entry["patch"] is not None:
                entry["patch"].remove()

        for index in range(list_widget.count()):
            listItem = list_widget.item(index)
            if hasattr(list_widget.item(index), "checkState") and (
                    list_widget.item(index).checkState() == QtCore.Qt.Checked):
                if listItem.flighttrack_model != self.active_flight_track:
                    patch = MultipleFlightpath(self.view.map,
                                               self.dict_flighttrack[listItem.flighttrack_model][
                                                   "wp_data"],
                                               color=self.dict_flighttrack[listItem.flighttrack_model]["color"],
                                               linewidth=self.dict_flighttrack[listItem.flighttrack_model]["linewidth"],
                                               line_transparency=self.dict_flighttrack[listItem.flighttrack_model][
                                                   "line_transparency"],
                                               line_style=self.dict_flighttrack[listItem.flighttrack_model][
                                                   "line_style"])

                    self.dict_flighttrack[listItem.flighttrack_model]["patch"] = patch
                    self.dict_flighttrack[listItem.flighttrack_model]["checkState"] = True
            else:
                # pass
                self.dict_flighttrack[listItem.flighttrack_model]["checkState"] = False

        # Update the legend after drawing the flight tracks
        self.update_flightpath_legend()

    def set_activate_flag(self):
        if not self.flighttrack_added:
            self.flighttrack_activated = True

    def deactivate_all_flighttracks(self):
        """
        Remove all flighttrack patches from topview canvas and make flighttracks userCheckable.
        """
        for index in range(self.list_flighttrack.count()):
            listItem = self.list_flighttrack.item(index)

            self.set_listControl(True, False)

            self.set_activate_flag()
            listItem.setFlags(listItem.flags() | QtCore.Qt.ItemIsUserCheckable)
            listItem.setIcon(self.show_color_icon(self.get_color(listItem.flighttrack_model)))

            if listItem.flighttrack_model == self.active_flight_track:
                font = QtGui.QFont()
                font.setBold(False)
                listItem.setFont(font)

        self.active_flight_track = None

    def set_listControl(self, operation, flighttrack):
        self.operation_list = operation
        self.flighttrack_list = flighttrack

    def get_ft_vertices_color(self):
        return self.get_random_color()

    def listFlighttrack_itemClicked(self):
        """
        reflect the linewidth, transparency, line_style of the selected flight track
        and toggles the visibility of the groupBox.
        """
        if self.list_operation_track.currentItem() is not None:
            self.list_operation_track.setCurrentItem(None)

        if self.list_flighttrack.currentItem() is not None:
            wp_model = self.list_flighttrack.currentItem().flighttrack_model

            linewidth = self.dict_flighttrack[wp_model]["linewidth"]
            line_transparency = self.dict_flighttrack[wp_model]["line_transparency"]
            line_style = self.dict_flighttrack[wp_model]["line_style"]

            self.dsbx_linewidth.setValue(linewidth)
            self.hsTransparencyControl.setValue(int(line_transparency * 100))
            # Use the reverse dictionary to set the current text of the combo box
            if line_style in self.line_styles_reverse:
                self.cbLineStyle.setCurrentText(self.line_styles_reverse[line_style])
            else:
                self.cbLineStyle.setCurrentText("Solid")

            print(wp_model != self.active_flight_track,
                  self.list_flighttrack.currentItem().checkState() != QtCore.Qt.Checked)
            self.enable_disable_line_style_buttons(
                wp_model != self.active_flight_track and self.list_flighttrack.currentItem().
                checkState() == QtCore.Qt.Checked)
            # Update the legend
            self.update_flightpath_legend()


class MultipleFlightpathOperations:
    """
    This class provides the functions for plotting Multiple Flighttracks from mscolab server
    on the TopView canvas.
    """

    def __init__(self, parent, mscolab_server_url, token, list_operation_track, active_op_id, listOperationsMSC, view):
        # Variables related to Mscolab Operations
        self.parent = parent
        self.active_op_id = active_op_id
        self.mscolab_server_url = mscolab_server_url
        self.token = token
        self.view = view
        self.dict_operations = {}
        self.list_operation_track = list_operation_track
        self.listOperationsMSC = listOperationsMSC

        self.operation_added = False
        self.operation_removed = False
        self.operation_activated = False
        self.color_change = False

        # Load operations from wps server
        server_operations = self.get_wps_from_server()
        sorted_server_operations = sorted(server_operations, key=lambda d: d["path"])

        for operations in sorted_server_operations:
            op_id = operations["op_id"]
            xml_content = self.request_wps_from_server(op_id)
            wp_model = ft.WaypointsTableModel(xml_content=xml_content)
            wp_model.name = operations["path"]
            self.create_operation(op_id, wp_model)

        # This needs to be done after operations are loaded
        # Connect signals and slots
        self.list_operation_track.itemChanged.connect(self.set_flag)
        self.parent.cbSlectAll2.stateChanged.connect(self.selectAll)

    def set_flag(self):
        if self.operation_added:
            self.operation_added = False
        elif self.operation_removed:
            self.operation_removed = False
        elif self.color_change:
            self.color_change = False
        else:
            self.draw_inactive_operations()

    def get_wps_from_server(self):
        operations = {}
        skip_archived = config_loader(dataset="MSCOLAB_skip_archived_operations")
        data = {
            "token": self.token,
            "skip_archived": skip_archived
        }
        url = urljoin(self.mscolab_server_url, "operations")
        r = requests.get(url, data=data, timeout=(2, 10))
        if r.text != "False":
            _json = json.loads(r.text)
            operations = _json["operations"]
        selected_category = self.parent.msc_category.currentText()
        if selected_category != "*ANY*":
            operations = [op for op in operations if op['category'] == selected_category]
        return operations

    def request_wps_from_server(self, op_id):
        if verify_user_token(self.mscolab_server_url, self.token):
            data = {
                "token": self.token,
                "op_id": op_id
            }
            url = urljoin(self.mscolab_server_url, "get_operation_by_id")
            r = requests.get(url, data=data, timeout=(2, 10))
            if r.text != "False":
                xml_content = json.loads(r.text)["content"]
                return xml_content

    def load_wps_from_server(self, op_id):
        xml_content = self.request_wps_from_server(op_id)
        if xml_content is not None:
            waypoints_model = ft.WaypointsTableModel(xml_content=xml_content)
            return waypoints_model

    def save_operation_data(self, op_id, wp_model):
        wp_data = [(wp.lat, wp.lon, wp.flightlevel, wp.location, wp.comments) for wp in wp_model.all_waypoint_data()]
        if self.dict_operations[op_id] is None:
            self.create_operation(op_id, wp_model)
        self.dict_operations[op_id]["wp_data"] = wp_data

    def create_operation(self, op_id, wp_model):
        """
        """
        self.dict_operations[op_id] = {}
        self.dict_operations[op_id]["patch"] = None
        self.dict_operations[op_id]["wp_data"] = None
        self.dict_operations[op_id]["linewidth"] = 2.0
        self.dict_operations[op_id]["line_transparency"] = 1.0
        self.dict_operations[op_id]["line_style"] = 'solid'
        self.dict_operations[op_id]["color"] = self.parent.get_ft_vertices_color()

        self.save_operation_data(op_id, wp_model)

        listItem = QMscolabOperationsListWidgetItem(wp_model, op_id, self.list_operation_track)
        listItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)

        if not self.operation_added:
            self.operation_added = True
        listItem.setCheckState(QtCore.Qt.Unchecked)
        if not self.operation_added:
            self.operation_added = True

        # Show operations color icon
        listItem.setIcon(self.show_color_icon(self.get_color(op_id)))
        self.update_operation_legend()

        return listItem

    def activate_operation(self):
        """
        Activate Mscolab Operation
        """
        # disconnect itemChanged during activation loop
        self.list_operation_track.itemChanged.disconnect(self.set_flag)
        font = QtGui.QFont()
        for i in range(self.list_operation_track.count()):
            listItem = self.list_operation_track.item(i)
            if self.active_op_id == listItem.op_id:  # active operation
                listItem.setIcon(self.show_color_icon(self.parent.color))
                font.setBold(True)
                if self.dict_operations[listItem.op_id]["patch"] is not None:
                    self.dict_operations[listItem.op_id]["patch"].remove()
                if listItem.checkState() == QtCore.Qt.Unchecked:
                    listItem.setCheckState(QtCore.Qt.Checked)
                    self.set_activate_flag()
                listItem.setFlags(listItem.flags() & ~QtCore.Qt.ItemIsUserCheckable)  # make activated track uncheckable
            else:
                listItem.setIcon(self.show_color_icon(self.get_color(listItem.op_id)))
                font.setBold(False)
                listItem.setFlags(listItem.flags() | QtCore.Qt.ItemIsUserCheckable)
            self.set_activate_flag()
            listItem.setFont(font)
        # connect itemChanged after everything setup, otherwise it will be triggered on each entry
        self.list_operation_track.itemChanged.connect(self.set_flag)
        self.update_line_properties_state()
        self.set_flag()
        self.parent.flagop()

    def update_line_properties_state(self):
        """
        Check if there is an active flight track selected. If there is an active flight track selected in the
        list widget, disable these UI elements else enable
        """
        if self.list_operation_track.currentItem() is not None:
            op_id = self.list_operation_track.currentItem().op_id
            self.enable_disable_line_style_buttons(op_id != self.active_op_id)

    def enable_disable_line_style_buttons(self, enable):
        self.parent.pushButton_color.setEnabled(enable)
        self.parent.dsbx_linewidth.setEnabled(enable)
        self.parent.hsTransparencyControl.setEnabled(enable)
        self.parent.cbLineStyle.setEnabled(enable)
        if enable:
            self.parent.labelStatus.setText("Status: ✔ flight track selected")
        else:
            self.parent.labelStatus.setText(
                "Status: You can change line attributes of the active flighttrack through options only.")

    def save_last_used_operation(self, op_id):
        if self.active_op_id is not None:
            self.save_operation_data(op_id, self.load_wps_from_server(self.active_op_id))

    def draw_inactive_operations(self):
        """
        Draw flighttracks of inactive operations.
        """
        for entry in self.dict_operations.values():
            if entry is not None:
                if entry["patch"] is not None:
                    entry["patch"].remove()

        for index in range(self.list_operation_track.count()):
            listItem = self.list_operation_track.item(index)
            if hasattr(listItem, "checkState") and (
                    listItem.checkState() == QtCore.Qt.Checked):
                if listItem.op_id != self.active_op_id:
                    patch = MultipleFlightpath(self.view.map,
                                               self.dict_operations[listItem.op_id][
                                                   "wp_data"],
                                               color=self.dict_operations[listItem.op_id]["color"],
                                               linewidth=self.dict_operations[listItem.op_id]["linewidth"],
                                               line_transparency=self.dict_operations[listItem.op_id][
                                                   "line_transparency"],
                                               line_style=self.dict_operations[listItem.op_id][
                                                   "line_style"])

                    self.dict_operations[listItem.op_id]["patch"] = patch
        self.update_operation_legend()

    def get_op_id(self, op_id):
        if self.active_op_id is not None:
            tmp = self.active_op_id
            self.save_last_used_operation(tmp)
        self.active_op_id = op_id
        self.activate_operation()

    def operationsAdded(self, op_id, path):
        """
        Slot to add operation.
        """
        wp_model = self.load_wps_from_server(op_id)
        wp_model.name = path
        self.create_operation(op_id, wp_model)

    def operationRemoved(self, op_id):
        """
        Slot to remove operation.
        """
        self.list_operation_track.itemChanged.disconnect(self.set_flag)
        self.operation_removed = True
        for index in range(self.list_operation_track.count()):
            if self.list_operation_track.item(index).op_id == op_id:
                if self.dict_operations[self.list_operation_track.item(index).op_id]["patch"] is None:
                    del self.dict_operations[self.list_operation_track.item(index).op_id]
                else:
                    self.dict_operations[self.list_operation_track.item(index).op_id]["patch"].remove()
                self.list_operation_track.takeItem(index)
                self.active_op_id = None
                break
        self.list_operation_track.itemChanged.connect(self.set_flag)

    def set_activate_flag(self):
        if not self.operation_activated:
            self.operation_activated = True

    def deactivate_all_operations(self):
        """
        Removes all operations patches from topview canvas and make flighttracks userCheckable
        """
        for index in range(self.listOperationsMSC.count()):
            listItem = self.list_operation_track.item(index)

            self.parent.set_listControl(False, True)

            self.set_activate_flag()
            listItem.setFlags(listItem.flags() | QtCore.Qt.ItemIsUserCheckable)
            listItem.setIcon(self.show_color_icon(self.get_color(listItem.op_id)))

            # if listItem.op_id == self.active_op_id:
            self.set_activate_flag()
            font = QtGui.QFont()
            font.setBold(False)
            listItem.setFont(font)

        self.active_op_id = None

    def selectAll(self, state):
        """
        select/deselect mscolab operations
        """
        for i in range(self.list_operation_track.count()):
            item = self.list_operation_track.item(i)
            if self.active_op_id is not None and item.op_id == self.active_op_id:
                item.setCheckState(QtCore.Qt.Checked)  # Ensure the active flight track remains checked
            else:
                item.setCheckState(state)

    def select_color(self):
        """
        Sets the color of selected operation when change Color is clicked.
        """
        if self.list_operation_track.currentItem() is not None:
            if (hasattr(self.list_operation_track.currentItem(), "checkState")) and (
                    self.list_operation_track.currentItem().checkState() == QtCore.Qt.Checked):
                op_id = self.list_operation_track.currentItem().op_id
                if self.list_operation_track.currentItem().op_id == self.active_op_id:
                    self.error_dialog = QtWidgets.QErrorMessage()
                    self.error_dialog.showMessage('Use "options" to change color of an activated operation.')
                else:
                    color_dialog = CustomColorDialog(self.parent)
                    color_dialog.color_selected.connect(lambda color: self.apply_color(op_id, color))
                    color_dialog.show()
            else:
                self.parent.labelStatus.setText("Status: Check Mark the flighttrack to change its color.")

    def apply_color(self, op_id, color):
        if color.isValid():
            self.dict_operations[op_id]["color"] = color.getRgbF()
            self.color_change = True
            self.list_operation_track.currentItem().setIcon(self.show_color_icon(self.get_color(op_id)))
            self.dict_operations[op_id]["patch"].update(
                color=self.dict_operations[op_id]["color"],
                linewidth=self.dict_operations[op_id]["linewidth"])
            self.update_operation_legend()

    def get_color(self, op_id):
        """
        Returns color of respective operation.
        """
        return self.dict_operations[op_id]["color"]

    def show_color_icon(self, clr):
        """
        """
        pixmap = self.parent.show_color_pixmap(clr)
        return QtGui.QIcon(pixmap)

    def ft_color_update(self, color):
        self.color = color
        self.dict_operations[self.active_op_id]["color"] = color

        for index in range(self.list_operation_track.count()):
            if self.list_operation_track.item(index).op_id == self.active_op_id:
                self.list_operation_track.item(index).setIcon(
                    self.show_color_icon(self.get_color(self.active_op_id)))
                break

    def logout_mscolab(self):
        a = self.list_operation_track.count() - 1
        while a >= 0:
            if self.dict_operations[self.list_operation_track.item(0).op_id]['patch'] is None:
                del self.dict_operations[self.list_operation_track.item(0).op_id]
            else:
                self.dict_operations[self.list_operation_track.item(0).op_id]['patch'].remove()
            self.list_operation_track.takeItem(0)
            a -= 1

        # Remove only the operations from flightpath_dict without affecting flight tracks
        self.parent.flightpath_dict.clear()

        # Uncheck the "Select All" checkbox
        self.parent.cbSlectAll2.setChecked(False)
        self.parent.labelStatus.setText("Status: Select a flighttrack/operation")

        self.list_operation_track.itemChanged.disconnect()
        self.mscolab_server_url = None
        self.token = None
        self.dict_operations = {}

    @QtCore.pyqtSlot(int)
    def permission_revoked(self, op_id):
        self.operationRemoved(op_id)

    @QtCore.pyqtSlot(int, str)
    def render_permission(self, op_id, path):
        self.operationsAdded(op_id, path)

    def set_linewidth(self):
        """
        Change the line width of the selected operation track.
        """
        item = self.list_operation_track.currentItem()
        if hasattr(item, "checkState") and item.checkState() == QtCore.Qt.Checked:
            op_id = item.op_id
            if op_id != self.active_op_id:
                self.parent.groupBox.show()
                if self.dict_operations[op_id]["linewidth"] != self.parent.dsbx_linewidth.value():
                    self.dict_operations[op_id]["linewidth"] = self.parent.dsbx_linewidth.value()
                    self.update_flighttrack_patch(op_id)
                    self.parent.change_linewidth = True
                    self.parent.dsbx_linewidth.setValue(self.dict_operations[op_id]["linewidth"])
        else:
            self.parent.dsbx_linewidth.setEnabled(item is not None and item.checkState() == QtCore.Qt.Checked)
            self.parent.labelStatus.setText("Status: Check Mark the flighttrack to change its line width.")

    def set_transparency(self):
        """
        Change the line transparency of the selected operation track.
        """
        item = self.list_operation_track.currentItem()
        if hasattr(item, "checkState") and item.checkState() == QtCore.Qt.Checked:
            op_id = item.op_id
            if op_id != self.active_op_id:
                self.parent.groupBox.show()
                new_transparency = self.parent.hsTransparencyControl.value() / 100.0
                if self.dict_operations[op_id]["line_transparency"] != new_transparency:
                    self.dict_operations[op_id]["line_transparency"] = new_transparency
                    self.update_flighttrack_patch(op_id)
                    self.parent.change_line_transparency = True
                    self.parent.hsTransparencyControl.setValue(
                        int(self.dict_operations[op_id]["line_transparency"] * 100))
        else:
            self.parent.hsTransparencyControl.setEnabled(item is not None and item.checkState() == QtCore.Qt.Checked)
            self.parent.labelStatus.setText("Status: Check Mark the flighttrack to change its transparency.")

    def set_linestyle(self):
        """
        Change the line style of the selected operation track.
        """
        item = self.list_operation_track.currentItem()
        if hasattr(item, "checkState") and item.checkState() == QtCore.Qt.Checked:
            op_id = item.op_id
            if op_id != self.active_op_id:
                self.parent.groupBox.show()
            selected_style = self.parent.cbLineStyle.currentText()
            new_linestyle = self.parent.line_styles.get(selected_style, '-')  # Default to 'solid'

            if self.dict_operations[op_id]["line_style"] != new_linestyle:
                self.dict_operations[op_id]["line_style"] = new_linestyle
                self.update_flighttrack_patch(op_id)
                self.parent.change_line_style = True
                self.parent.cbLineStyle.setCurrentText(self.dict_operations[op_id]["line_style"])
        else:
            self.parent.cbLineStyle.setEnabled(item is not None and item.checkState() == QtCore.Qt.Checked)
            self.parent.labelStatus.setText("Status: Check Mark the flighttrack to change its line style.")

    def update_flighttrack_patch(self, op_id):
        """
        Update the flighttrack patch with the latest attributes.
        """
        if self.dict_operations[op_id]["patch"] is not None:
            self.dict_operations[op_id]["patch"].remove()
        self.dict_operations[op_id]["patch"] = MultipleFlightpath(
            self.view.map,
            self.dict_operations[op_id]["wp_data"],
            color=self.dict_operations[op_id]["color"],
            linewidth=self.dict_operations[op_id]["linewidth"],
            line_transparency=self.dict_operations[op_id]["line_transparency"],
            line_style=self.dict_operations[op_id]["line_style"]
        )
        self.update_operation_legend()

    def update_operation_legend(self):
        """
        Collects operation data and updates the legend in the TopView.
        Only checked operations will be included in the legend.
        Unchecked operations will be removed from the flightpath_dict.
        """
        # Iterate over all items in the list_operation_track
        for i in range(self.list_operation_track.count()):
            listItem = self.list_operation_track.item(i)

            # If the operation is checked, add/update it in the dictionary
            if listItem.checkState() == QtCore.Qt.Checked:
                wp_model = listItem.flighttrack_model
                name = wp_model.name if hasattr(wp_model, 'name') else 'Unnamed operation'
                op_id = listItem.op_id
                color = self.dict_operations[op_id].get('color', '#000000')  # Default to black
                linestyle = self.dict_operations[op_id].get('line_style', '-')  # Default to solid line
                self.parent.flightpath_dict[name] = (color, linestyle)
            # If the flight track is unchecked, ensure it is removed from the dictionary
            else:
                wp_model = listItem.flighttrack_model
                name = wp_model.name if hasattr(wp_model, 'name') else 'Unnamed flighttrack'
                if name in self.parent.flightpath_dict:
                    del self.parent.flightpath_dict[name]

        # Update the legend in the view with the filtered flightpath_dict
        self.view.update_flightpath_legend(self.parent.flightpath_dict)

    def listOperations_itemClicked(self):
        """
        reflect the linewidth, transparency, line_style of the selected flight track
        and toggles the visibility of the groupBox.
        """
        if self.parent.list_flighttrack.currentItem() is not None:
            self.parent.list_flighttrack.setCurrentItem(None)

        if self.list_operation_track.currentItem() is not None:
            op_id = self.list_operation_track.currentItem().op_id

            linewidth = self.dict_operations[op_id]["linewidth"]
            line_transparency = self.dict_operations[op_id]["line_transparency"]
            line_style = self.dict_operations[op_id]["line_style"]

            self.parent.dsbx_linewidth.setValue(linewidth)
            self.parent.hsTransparencyControl.setValue(int(line_transparency * 100))
            # Use the reverse dictionary to set the current text of the combo box
            if line_style in self.parent.line_styles_reverse:
                self.parent.cbLineStyle.setCurrentText(self.parent.line_styles_reverse[line_style])
            else:
                self.parent.cbLineStyle.setCurrentText("Solid")

            self.enable_disable_line_style_buttons(op_id != self.active_op_id and self.list_operation_track.
                                                   currentItem().checkState() == QtCore.Qt.Checked)
            self.update_operation_legend()
