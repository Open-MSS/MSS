# -*- coding: utf-8 -*-
"""

    mslib.multiple_flightpath_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Control Widget to configure multiple flightpath on topview.

    This file is part of MSS.

    :copyright: Copyright 2022 Jatin Jain
    :copyright: Copyright 2022 by the MSS team, see AUTHORS.
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

import requests
import json
from PyQt5 import QtWidgets, QtGui, QtCore
from mslib.msui.qt5 import ui_multiple_flightpath_dockwidget as ui
from mslib.msui import flighttrack as ft
import mslib.msui.msui_mainwindow as msui_mainwindow
from mslib.utils.verify_user_token import verify_user_token
from mslib.utils.qt import Worker


class QMscolabOperationsListWidgetItem(QtWidgets.QListWidgetItem):
    """
    """

    def __init__(self, flighttrack_model, op_id: int, parent=None, type=QtWidgets.QListWidgetItem.UserType):
        view_name = flighttrack_model.name
        super().__init__(
            view_name, parent, type
        )
        self.parent = parent
        self.flighttrack_model = flighttrack_model
        self.op_id = op_id


class MultipleFlightpath:
    """
    Represent a Multiple FLightpath
    """

    def __init__(self, mapcanvas, wp, linewidth=2.0, color='blue'):
        self.map = mapcanvas
        self.flightlevel = None
        self.comments = ''
        self.patches = []
        self.waypoints = wp
        self.linewidth = linewidth
        self.color = color
        self.draw()

    def draw_line(self, x, y):
        self.patches.append(self.map.plot(x, y, color=self.color, linewidth=self.linewidth))

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

    def update(self, linewidth=None, color=None):
        if linewidth is not None:
            self.linewidth = linewidth
        if color is not None:
            self.color = color
        self.remove()
        self.draw()

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

    signal_parent_closes = QtCore.Signal()

    def __init__(self, parent=None, view=None, listFlightTracks=None,
                 listOperationsMSC=None, activeFlightTrack=None, mscolab_server_url=None, token=None):
        super().__init__(parent)
        # ToDO: Remove all patches, on closing dockwidget.
        self.ui = parent
        self.setupUi(self)
        self.view = view  # canvas
        self.flight_path = None  # flightpath object
        self.dict_flighttrack = {}  # Dictionary of flighttrack data: patch,color,wp_model
        self.active_flight_track = activeFlightTrack
        self.listOperationsMSC = listOperationsMSC
        self.listFlightTracks = listFlightTracks
        self.mscolab_server_url = mscolab_server_url
        self.token = token
        if self.ui is not None:
            ft_settings_dict = self.ui.getView().get_settings()
            self.color = ft_settings_dict["colour_ft_vertices"]
        else:
            self.color = (0, 0, 1, 1)
        self.obb = []

        self.operation_list = False
        self.flighttrack_list = True

        # Set flags
        # ToDo: Use invented constants for initialization.
        self.flighttrack_added = False
        self.flighttrack_activated = False
        self.color_change = False
        self.change_linewidth = False
        self.dsbx_linewidth.setValue(2.0)

        # Connect Signals and Slots
        self.listFlightTracks.model().rowsInserted.connect(self.wait)
        self.listFlightTracks.model().rowsRemoved.connect(self.flighttrackRemoved)
        self.ui.signal_activate_flighttrack1.connect(self.get_active)
        self.list_flighttrack.itemChanged.connect(self.flagop)

        self.pushButton_color.clicked.connect(self.select_color)
        self.ui.signal_ft_vertices_color_change.connect(self.ft_vertices_color)
        self.dsbx_linewidth.valueChanged.connect(self.set_linewidth)
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

    @QtCore.Slot()
    def logout(self):
        self.operations.logout_mscolab()
        self.ui.signal_listFlighttrack_doubleClicked.disconnect()
        self.ui.signal_permission_revoked.disconnect()
        self.ui.signal_render_new_permission.disconnect()
        self.operations = None
        self.flighttrack_list = True
        self.operation_list = False
        for idx in range(len(self.obb)):
            del self.obb[idx]

    @QtCore.Slot(str, str)
    def login(self, url, token):
        self.mscolab_server_url = url
        self.token = token
        self.connect_mscolab_server()

    def connect_mscolab_server(self):
        self.operations = MultipleFlightpathOperations(self, self.mscolab_server_url, self.token,
                                                       self.list_operation_track,
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

    @QtCore.Slot(tuple)
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

    @QtCore.Slot(int, str)
    def add_operation_slot(self, op_id, path):
        self.operations.operationsAdded(op_id, path)

    @QtCore.Slot(int)
    def remove_operation_slot(self, op_id):
        self.operations.operationRemoved(op_id)

    @QtCore.Slot(int)
    def update_op_id(self, op_id):
        self.operations.get_op_id(op_id)

    @QtCore.Slot(ft.WaypointsTableModel)
    def get_active(self, active_flighttrack):
        self.update_last_flighttrack()
        self.active_flight_track = active_flighttrack
        self.activate_flighttrack()

    def save_waypoint_model_data(self, wp_model, listWidget):
        wp_data = [(wp.lat, wp.lon, wp.flightlevel, wp.location, wp.comments) for wp in wp_model.all_waypoint_data()]
        if self.dict_flighttrack[wp_model] is None:
            self.create_list_item(wp_model)
        self.dict_flighttrack[wp_model]["wp_data"] = wp_data

    def create_list_item(self, wp_model):
        """
        PyQt5 method : Add items in list and add checkbox functionality
        """
        # Create new key in dict
        self.dict_flighttrack[wp_model] = {}
        self.dict_flighttrack[wp_model]["patch"] = None
        self.dict_flighttrack[wp_model]["color"] = self.color
        self.dict_flighttrack[wp_model]["linewidth"] = 2.0
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

        return listItem

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
                    color = QtWidgets.QColorDialog.getColor()
                    if color.isValid():
                        self.dict_flighttrack[wp_model]["color"] = color.getRgbF()
                        self.color_change = True
                        self.list_flighttrack.currentItem().setIcon(self.show_color_icon(self.get_color(wp_model)))
                        self.dict_flighttrack[wp_model]["patch"].update(color=self.dict_flighttrack[wp_model]["color"])
            else:
                self.labelStatus.setText("Check Mark the flighttrack to change its color.")
        elif self.list_operation_track.currentItem() is not None:
            self.operations.select_color()
        else:
            self.labelStatus.setText("Status: No flight track selected")

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

                        self.dict_flighttrack[wp_model]["patch"].remove()
                        self.dict_flighttrack[wp_model]["patch"].update(
                            self.dict_flighttrack[wp_model]["linewidth"], self.dict_flighttrack[wp_model]["color"]
                        )
                        self.change_linewidth = True
                        self.dsbx_linewidth.setValue(self.dict_flighttrack[wp_model]["linewidth"])
            else:
                self.labelStatus.setText("Status: No flight track selected")
        elif self.list_operation_track.currentItem() is not None:
            self.operations.set_linewidth()
        else:
            self.labelStatus.setText("Status: No flight track selected")

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
        Activate flighttrack
        """
        font = QtGui.QFont()
        for i in range(self.list_flighttrack.count()):
            listItem = self.list_flighttrack.item(i)
            if self.active_flight_track == listItem.flighttrack_model:  # active flighttrack
                listItem.setIcon(self.show_color_icon(self.color))
                font.setBold(True)
                if self.dict_flighttrack[listItem.flighttrack_model]["patch"] is not None:
                    self.dict_flighttrack[listItem.flighttrack_model]["patch"].remove()
                if listItem.checkState() == QtCore.Qt.Unchecked:
                    listItem.setCheckState(QtCore.Qt.Checked)
                    self.set_activate_flag()
                listItem.setFlags(listItem.flags() & ~QtCore.Qt.ItemIsUserCheckable)  # make activated track uncheckable
            else:
                listItem.setIcon(self.show_color_icon(self.get_color(listItem.flighttrack_model)))
                font.setBold(False)
                listItem.setFlags(listItem.flags() | QtCore.Qt.ItemIsUserCheckable)
            self.set_activate_flag()
            listItem.setFont(font)

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
                                               color=self.dict_flighttrack[listItem.flighttrack_model]['color'])

                    self.dict_flighttrack[listItem.flighttrack_model]["patch"] = patch
                    self.dict_flighttrack[listItem.flighttrack_model]["checkState"] = True
            else:
                # pass
                self.dict_flighttrack[listItem.flighttrack_model]["checkState"] = False

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

            if listItem.flighttrack_model == self.active_flight_track:
                font = QtGui.QFont()
                font.setBold(False)
                listItem.setFont(font)

        self.active_flight_track = None

    def set_listControl(self, operation, flighttrack):
        self.operation_list = operation
        self.flighttrack_list = flighttrack

    def get_ft_vertices_color(self):
        return self.color

    def listFlighttrack_itemClicked(self):
        if self.list_operation_track.currentItem() is not None:
            self.list_operation_track.setCurrentItem(None)

        if self.list_flighttrack.currentItem() is not None:
            wp_model = self.list_flighttrack.currentItem().flighttrack_model
            self.dsbx_linewidth.setValue(self.dict_flighttrack[wp_model]["linewidth"])

            if self.list_flighttrack.currentItem().flighttrack_model == self.active_flight_track:
                self.frame.hide()
            else:
                self.frame.show()


class MultipleFlightpathOperations:
    """
    This class provides the functions for plotting Multiple Flighttracks from mscolab server
    on the TopView canvas.
    """

    def __init__(self, parent, mscolab_server_url, token, list_operation_track, listOperationsMSC, view):
        # Variables related to Mscolab Operations
        self.parent = parent
        self.active_op_id = None
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

        # Connect signals and slots
        self.list_operation_track.itemChanged.connect(self.set_flag)

        # Load operations from wps server
        server_operations = self.get_wps_from_server()
        sorted_server_operations = sorted(server_operations, key=lambda d: d["path"])

        for operations in sorted_server_operations:
            op_id = operations["op_id"]
            xml_content = self.request_wps_from_server(op_id)
            wp_model = ft.WaypointsTableModel(xml_content=xml_content)
            wp_model.name = operations["path"]
            self.create_operation(op_id, wp_model)

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
        data = {
            "token": self.token
        }
        r = requests.get(self.mscolab_server_url + "/operations", data=data, timeout=(2, 10))
        if r.text != "False":
            _json = json.loads(r.text)
            operations = _json["operations"]
        return operations

    def request_wps_from_server(self, op_id):
        if verify_user_token(self.mscolab_server_url, self.token):
            data = {
                "token": self.token,
                "op_id": op_id
            }
            r = requests.get(self.mscolab_server_url + '/get_operation_by_id', data=data, timeout=(2, 10))
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

        return listItem

    def activate_operation(self):
        """
        Activate Mscolab Operation
        """
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
                                               linewidth=self.dict_operations[listItem.op_id]["linewidth"])

                    self.dict_operations[listItem.op_id]["patch"] = patch

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

            # if listItem.op_id == self.active_op_id:
            self.set_activate_flag()
            font = QtGui.QFont()
            font.setBold(False)
            listItem.setFont(font)

        self.active_op_id = None

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
                    color = QtWidgets.QColorDialog.getColor()
                    if color.isValid():
                        self.dict_operations[op_id]["color"] = color.getRgbF()
                        self.color_change = True
                        self.list_operation_track.currentItem().setIcon(self.show_color_icon(self.get_color(op_id)))
                        self.dict_operations[op_id]["patch"].update(
                            color=self.dict_operations[op_id]["color"],
                            linewidth=self.dict_operations[op_id]["linewidth"])
            else:
                self.parent.labelStatus.setText("Check Mark the Operation to change color.")

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

        self.list_operation_track.itemChanged.disconnect()
        self.mscolab_server_url = None
        self.token = None
        self.dict_operations = {}

    @QtCore.Slot(int)
    def permission_revoked(self, op_id):
        self.operationRemoved(op_id)

    @QtCore.Slot(int, str)
    def render_permission(self, op_id, path):
        self.operationsAdded(op_id, path)

    def set_linewidth(self):
        if (hasattr(self.list_operation_track.currentItem(), "checkState")) and (
                self.list_operation_track.currentItem().checkState() == QtCore.Qt.Checked):
            op_id = self.list_operation_track.currentItem().op_id
            if op_id != self.active_op_id:
                self.parent.frame.show()
                if self.dict_operations[op_id]["linewidth"] != self.parent.dsbx_linewidth.value():
                    self.dict_operations[op_id]["linewidth"] = self.parent.dsbx_linewidth.value()

                    self.dict_operations[op_id]["patch"].remove()
                    self.dict_operations[op_id]["patch"].update(
                        self.dict_operations[op_id]["linewidth"], self.dict_operations[op_id]["color"]
                    )
                    self.change_linewidth = True
                    self.parent.dsbx_linewidth.setValue(self.dict_operations[op_id]["linewidth"])

    def listOperations_itemClicked(self):
        if self.parent.list_flighttrack.currentItem() is not None:
            self.parent.list_flighttrack.setCurrentItem(None)

        if self.list_operation_track.currentItem() is not None:
            op_id = self.list_operation_track.currentItem().op_id
            self.parent.dsbx_linewidth.setValue(self.dict_operations[op_id]["linewidth"])

            if self.list_operation_track.currentItem().op_id == self.active_op_id:
                self.parent.frame.hide()
            else:
                self.parent.frame.show()
