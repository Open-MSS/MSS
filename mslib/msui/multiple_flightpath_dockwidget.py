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
from PyQt5 import QtWidgets, QtGui, QtCore
from mslib.msui.qt5 import ui_multiple_flightpath_dockwidget as ui
from mslib.msui import flighttrack as ft
from mslib.msui import msui
from mslib.utils.verify_user_token import verify_user_token
import threading
import requests
import json


class QMscolabOperationsListWidgetItem(QtWidgets.QListWidgetItem):
    """
    """
    def __init__(self, flighttrack_model, op_id: int, parent=None, type=QtWidgets.QListWidgetItem.UserType):
        view_name = flighttrack_model.name
        super(QMscolabOperationsListWidgetItem, self).__init__(
            view_name, parent, type
        )
        self.parent = parent
        self.flighttrack_model = flighttrack_model
        self.op_id = op_id


class MultipleFlightpath(object):
    """
    Represent a Multiple FLightpath
    """

    def __init__(self, mapcanvas, wp, linewidth=2, color='blue'):
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

    def __init__(self, parent=None, view=None, listView=None,
                 listOperationsMSC=None, activeFlightTrack=None, mscolab_server_url=None, token=None):
        super(MultipleFlightpathControlWidget, self).__init__(parent)
        self.listOperationsMSC = listOperationsMSC
        self.listView = listView
        self.ui = parent
        self.setupUi(self)
        self.view = view  # canvas
        self.flight_path = None  # flightpath object
        self.dict_flighttrack = {}  # Dictionary of flighttrack data: patch,color,wp_model
        self.active_flight_track = activeFlightTrack

        # Set flags
        self.flighttrack_added = False
        self.flighttrack_activated = False
        self.color_change = False
        self.change_linewidth = False
        self.dsbx_linewidth.setValue(2.0)

        # Connect Signals and Slots
        self.listView.model().rowsInserted.connect(self.wait)
        self.listView.model().rowsRemoved.connect(self.flighttrackRemoved)
        self.ui.signal_activate_flighttrack1.connect(self.get_active)
        self.list_flighttrack.itemChanged.connect(self.flagop)

        # self.get_wps_from_server()

        self.pushButton_color.clicked.connect(self.select_color)
        self.dsbx_linewidth.valueChanged.connect(self.set_linewidth)

        # Load flighttracks
        for index in range(self.listView.count()):
            wp_model = self.listView.item(index).flighttrack_model
            listItem = self.create_list_item(wp_model, self.list_flighttrack)

        if mscolab_server_url is not None:
            self.operations = MultipleFlightpathOperations(mscolab_server_url, token, self.list_operation_track,
                                                           self.listOperationsMSC, self.view)

            # Signal emitted, on activation of operation from MSUI
            self.ui.signal_activate_operation.connect(self.update_op_id)

        self.activate_flighttrack()

        # self.view.plot_multiple_flightpath(self)

    def update(self):
        for entry in self.dict_flighttrack.values():
            entry["patch"].update()

    def remove(self):
        for entry in self.dict_flighttrack.values():
            entry["patch"].remove()

    def wait(self, parent, start, end):
        self.flighttrack_added = True
        t1 = threading.Timer(0.5, self.flighttrackAdded, [parent, start, end])
        t1.start()

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
        wp_model = self.listView.item(start).flighttrack_model
        listItem = self.create_list_item(wp_model, self.list_flighttrack)
        self.activate_flighttrack()

    def save_waypoint_model_data(self, wp_model, listWidget):
        wp_data = [(wp.lat, wp.lon, wp.flightlevel, wp.location, wp.comments) for wp in wp_model.all_waypoint_data()]
        if self.dict_flighttrack[wp_model] is None:
            self.create_list_item(wp_model, listWidget)
        self.dict_flighttrack[wp_model]["wp_data"] = wp_data

    def create_list_item(self, wp_model, listWidget):
        """
        PyQt5 method : Add items in list and add checkbox functionality
        """
        # Create new key in dict
        self.dict_flighttrack[wp_model] = {}
        self.dict_flighttrack[wp_model]["patch"] = None
        self.dict_flighttrack[wp_model]["color"] = None
        self.dict_flighttrack[wp_model]["linewidth"] = 2
        self.dict_flighttrack[wp_model]["wp_data"] = []
        self.dict_flighttrack[wp_model]["checkState"] = False

        self.save_waypoint_model_data(wp_model, listWidget)

        listItem = msui.QFlightTrackListWidgetItem(wp_model, listWidget)
        listItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
        if not self.flighttrack_added:
            self.flighttrack_added = True
        listItem.setCheckState(QtCore.Qt.Unchecked)
        if not self.flighttrack_added:
            self.flighttrack_added = True

        return listItem

    def select_color(self):
        """
        Sets the color of selected flighttrack when Change Color is clicked.
        """
        if self.list_flighttrack.currentItem() is not None:
            if (hasattr(self.list_flighttrack.currentItem(), "checkState")) and (
                    self.list_flighttrack.currentItem().checkState() == QtCore.Qt.Checked):
                wp_model = self.list_flighttrack.currentItem().flighttrack_model
                color = QtWidgets.QColorDialog.getColor()
                if color.isValid():
                    self.dict_flighttrack[wp_model]["color"] = color.getRgbF()
                    self.color_change = True
                    self.list_flighttrack.currentItem().setIcon(self.show_color_icon(self.get_color(wp_model)))
                    self.dict_flighttrack[wp_model]["patch"].update(color=
                                                                    self.dict_flighttrack[wp_model]["color"])
            else:
                self.labelStatus.setText("Status: No flight track selected")
        else:
            self.labelStatus.setText("Status: No flight track selected")

    def get_color(self, wp_model):
        """
        Returns color of respective flighttrack.
        """
        return self.dict_flighttrack[wp_model]["color"]

    def show_color_icon(self, clr):
        """
        Creating object of QPixmap for displaying icon inside the listWidget.
        """
        pixmap = QtGui.QPixmap(20, 10)
        pixmap.fill(QtGui.QColor(int(clr[0] * 255), int(clr[1] * 255), int(clr[2] * 255)))
        return QtGui.QIcon(pixmap)

    def set_linewidth(self):
        """
        Change the line width of selected flighttrack.
        """
        if self.list_flighttrack.currentItem() is not None:
            if (hasattr(self.list_flighttrack.currentItem(), "checkState")) and (
                    self.list_flighttrack.currentItem().checkState() == QtCore.Qt.Checked):
                wp_model = self.list_flighttrack.currentItem().flighttrack_model
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

    @QtCore.Slot(ft.WaypointsTableModel)
    def get_active(self, active_flighttrack):
        self.update_last_flighttrack()
        self.active_flight_track = active_flighttrack
        self.activate_flighttrack()

    def update_last_flighttrack(self):
        """
        Update waypoint model for last activated flighttrack in dict_flighttrack.
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
                font.setBold(True)
                if self.dict_flighttrack[listItem.flighttrack_model]["patch"] is not None:
                    self.dict_flighttrack[listItem.flighttrack_model]["patch"].remove()
                if listItem.checkState() == QtCore.Qt.Unchecked:
                    listItem.setCheckState(QtCore.Qt.Checked)
                    self.set_activate_flag()
                listItem.setFlags(listItem.flags() ^ QtCore.Qt.ItemIsUserCheckable)  # make activated track uncheckable
            else:
                font.setBold(False)
                listItem.setFlags(listItem.flags() | QtCore.Qt.ItemIsUserCheckable)
                # if self.dict_flighttrack[listItem.flighttrack_model]["checkState"]:
                #     listItem.setCheckState(QtCore.Qt.Checked)
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

    @QtCore.Slot(int)
    def update_op_id(self, op_id):
        self.operations.get_op_id(op_id)


class MultipleFlightpathOperations:
    """
    This class provides the functions for plotting Multiple Flighttracks from mscolab server
    on the TopView canvas.
    """

    def __init__(self, mscolab_server_url, token, list_operation_track, listOperationsMSC, view):
        # Variables related to Mscolab Operations
        self.active_op_id = None
        self.mscolab_server_url = mscolab_server_url
        self.token = token
        self.dict_operations = {}
        self.list_operation_track = list_operation_track
        self.listOperationsMSC = listOperationsMSC
        self.active_flight_track = None
        self.view = view

        self.operation_added = False
        self.operation_removed = False
        self.operation_activated = False

        # Connect signals and slots
        self.list_operation_track.itemChanged.connect(self.set_flag)
        self.listOperationsMSC.model().rowsInserted.connect(self.wait2)
        self.listOperationsMSC.model().rowsRemoved.connect(self.operationRemoved)

        # Load operations from wps server
        server_operations = self.get_wps_from_server()

        for operations in server_operations:
            op_id = operations["op_id"]
            xml_content = self.request_wps_from_server(op_id)
            wp_model = ft.WaypointsTableModel(xml_content=xml_content)
            wp_model.name = operations["path"]
            self.create_operation(wp_model, op_id)

    def set_flag(self):
        if self.operation_added:
            self.operation_added = False
        elif self.operation_removed:
            self.operation_removed = False
        else:
            self.draw_inactive_operations()

    def get_wps_from_server(self):
        operations = {}
        data = {
            "token": self.token
        }
        r = requests.get(self.mscolab_server_url + "/operations", data=data)
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
            r = requests.get(self.mscolab_server_url + '/get_operation_by_id', data=data)
            if r.text != "False":
                xml_content = json.loads(r.text)["content"]
                return xml_content

    def load_wps_from_server(self, op_id):
        xml_content = self.request_wps_from_server(op_id)
        if xml_content is not None:
            waypoints_model = ft.WaypointsTableModel(xml_content=xml_content)
            return waypoints_model

    def save_operation_data(self, wp_model, op_id):
        wp_data = [(wp.lat, wp.lon, wp.flightlevel, wp.location, wp.comments) for wp in wp_model.all_waypoint_data()]
        if self.dict_operations[wp_model] is None:
            self.create_operation(wp_model, op_id)
        self.dict_operations[wp_model]["wp_data"] = wp_data
        self.dict_operations[wp_model]["op_id"] = op_id

    def create_operation(self, wp_model, op_id):
        """
        """
        self.dict_operations[wp_model] = {}
        self.dict_operations[wp_model]["patch"] = None
        self.dict_operations[wp_model]["op_id"] = None
        # self.sav

        self.save_operation_data(wp_model, op_id)

        listItem = QMscolabOperationsListWidgetItem(wp_model, op_id, self.list_operation_track)
        listItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)

        if not self.operation_added:
            self.operation_added = True
        listItem.setCheckState(QtCore.Qt.Unchecked)
        if not self.operation_added:
            self.operation_added = True

        return listItem

    def activate_operation(self):
        """
        Activate Mscolab Operation
        """
        font = QtGui.QFont()
        for i in range(self.list_operation_track.count()):
            listItem = self.list_operation_track.item(i)
            if self.active_op_id == listItem.op_id:  # active operation
                font.setBold(True)
                if self.dict_operations[listItem.flighttrack_model]["patch"] is not None:
                    self.dict_operations[listItem.flighttrack_model]["patch"].remove()
                if listItem.checkState() == QtCore.Qt.Unchecked:
                    listItem.setCheckState(QtCore.Qt.Checked)
                    self.set_activate_flag()
                listItem.setFlags(listItem.flags() ^ QtCore.Qt.ItemIsUserCheckable)  # make activated track uncheckable
            else:
                font.setBold(False)
                listItem.setFlags(listItem.flags() | QtCore.Qt.ItemIsUserCheckable)
            self.set_activate_flag()
            listItem.setFont(font)

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
                if listItem.flighttrack_model != self.active_flight_track:
                    patch = MultipleFlightpath(self.view.map,
                                               self.dict_operations[listItem.flighttrack_model][
                                                   "wp_data"])

                    self.dict_operations[listItem.flighttrack_model]["patch"] = patch
                    # self.dict_operations[listItem.flighttrack_model]["checkState"] = True
            else:
                pass
                # self.dict_operations[listItem.flighttrack_model]["checkState"] = False

    def get_op_id(self, op_id):
        self.active_op_id = op_id

    def wait2(self, parent, start, end):
        self.operation_added = True
        t2 = threading.Timer(0.5, self.operationsAdded, [parent, start, end])
        t2.start()

    def operationsAdded(self, parent, start, end):
        """
        Slot to add operation.
        """
        wp_model = self.list_operation_track.item(start).flighttrack_model
        listItem = self.create_operation(wp_model, self.list_operation_track)
        self.activate_operation()

    def operationRemoved(self, parent, start, end):
        """
        Slot to remove operation.
        """
        self.operation_removed = True
        if self.dict_operations[self.list_operation_track.item(start).flighttrack_model]["patch"] is None:
            del self.dict_operations[self.list_operation_track.item(start).flighttrack_model]
        else:
            self.dict_operations[self.list_operation_track.item(start).flighttrack_model]["patch"].remove()
        self.list_operation_track.takeItem(start)

    def set_activate_flag(self):
        if not self.operation_activated:
            self.operation_activated = True
