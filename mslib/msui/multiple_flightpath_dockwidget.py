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
import copy
import logging
from PyQt5 import QtWidgets, QtGui, QtCore
from mslib.msui.qt5 import ui_multiple_flightpath_dockwidget as ui
from mslib.msui import flighttrack as ft
from mslib.msui import msui
import threading


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
                 listOperationsMSC=None, activeFlightTrack=None):
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
        self.color_change = None

        # Connect Signals and Slots
        self.listView.model().rowsInserted.connect(self.wait)
        self.listView.model().rowsRemoved.connect(self.flighttrackRemoved)
        self.ui.signal_activate_flighttrack1.connect(self.get_active)
        self.list_flighttrack.itemChanged.connect(self.flagop)
        self.pushButton_color.clicked.connect(self.select_color)

        # Load flighttracks
        for index in range(self.listView.count()):
            wp_model = self.listView.item(index).flighttrack_model
            listItem = self.create_list_item(wp_model, self.list_flighttrack)

        # for index in range(self.listOperationsMSC.count()):
        # wp_model = self.listOperationsMSC.item(index).waypoints_model
        # listItem = self.create_list_item(wp_model, self.listOperationsMSC)

        self.activate_flighttrack(self.active_flight_track)

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
            self.drawInactiveFlighttracks()

    def flighttrackAdded(self, parent, start, end):
        """
        Slot to add flighttrack.
        """
        wp_model = self.listView.item(start).flighttrack_model
        listItem = self.create_list_item(wp_model, self.list_flighttrack)
        self.activate_flighttrack(listItem)

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
        self.dict_flighttrack[wp_model]["color"] = 'blue'
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

    # def select_linewidth(self):
    #     """
    #     Change the line width of selected flighttrack.
    #     """

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

    def activate_flighttrack(self, item=None):
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
                listItem.setCheckState(QtCore.Qt.Checked)
                self.set_activate_flag()
                listItem.setFlags(listItem.flags() ^ QtCore.Qt.ItemIsUserCheckable)  # make activated track uncheckable
            else:
                font.setBold(False)
                listItem.setFlags(listItem.flags() | QtCore.Qt.ItemIsUserCheckable)
                if self.dict_flighttrack[listItem.flighttrack_model]["checkState"]:
                    listItem.setCheckState(QtCore.Qt.Checked)
            self.set_activate_flag()
            listItem.setFont(font)

    def drawInactiveFlighttracks(self):
        """
        Draw inactive flighttracks
        """
        for entry in self.dict_flighttrack.values():
            if entry["patch"] is not None:
                entry["patch"].remove()

        for index in range(self.list_flighttrack.count()):
            listItem = self.list_flighttrack.item(index)
            if hasattr(self.list_flighttrack.item(index), "checkState") and (
                    self.list_flighttrack.item(index).checkState() == QtCore.Qt.Checked):
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
