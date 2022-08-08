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
import logging
import os

import fs
from PyQt5 import QtWidgets, QtCore
from mslib.msui.qt5 import ui_multiple_flightpath_dockwidget as ui
from mslib.utils.qt import get_open_filenames
from mslib.utils.config import load_settings_qsettings, save_settings_qsettings
from fs import open_fs
import xml


class MultipleFlightpath(object):
    """
    Represent a Multiple FLightpath
    """

    def __init__(self, mapcanvas, wp):
        self.map = mapcanvas
        self.flightlevel = None
        self.comments = ''
        self.patches = []
        self.waypoints = wp
        self.draw()

    def draw_line(self, x, y):
        self.patches.append(self.map.plot(x, y, color='blue', linewidth='2'))

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

    def draw(self):
        lat, lon = self.get_lonlat()
        x, y = self.compute_xy(lat, lon)
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

    def __init__(self, parent=None, view=None):
        super(MultipleFlightpathControlWidget, self).__init__(parent)
        self.setupUi(self)
        self.view = view  # canvas
        self.flight_path = None  # flightpath object
        self.dict_files = {}  # Dictionary of files added; key: patch, waypoints
        self.waypoint_list = []  # List of waypoints parsed from FTML file

        # Connect Signals and Slots
        self.bt_addFile.clicked.connect(self.get_file)
        self.btRemove_file.clicked.connect(self.remove_item)

        self.settings_tag = "multipledock"
        settings = load_settings_qsettings(
            self.settings_tag, {"saved_files": {}})

        if parent is not None:
            parent.viewCloses.connect(self.save_settings)
        # Restore previously stored sessions
        if settings["saved_files"] is not None:
            delete_files = []
            self.dict_files = settings["saved_files"]
            for fn in self.dict_files:
                if os.path.isfile(fn) is True:
                    self.create_list_item(fn)
                else:
                    delete_files.append(fn)  # add non-existent files to list
                    logging.info("'%s' does not exist in the directory anymore.", fn)
            for fn in delete_files:
                del self.dict_files[fn]  # remove non-existent files from dictionary
            self.load_flighttrack()
        self.view.plot_multiple_flightpath(self)

    def checkListItem(self, filename):
        for item in self.list_flighttrack.findItems(filename, QtCore.Qt.MatchExactly):
            index = self.list_flighttrack.row(item)
            self.list_flighttrack.item(index).setCheckState(QtCore.Qt.Checked)

    def get_file(self):
        """
        Slot that open opens a file dialog to choose FTML file.
        """
        filenames = get_open_filenames(
            self, "Open FTML File", os.path.dirname(str(self.directory_location)), "FTML Files(*.ftml)")
        if not filenames:
            return
        self.select_file(filenames)

    def select_file(self, filenames):
        """
        Initializes selected file.
        """
        for filename in filenames:
            if filename is None:
                return
            text = filename
            if text not in self.dict_files:
                self.dict_files[text] = {}
                self.dict_files[text]["track"] = None
                self.create_list_item(text)
                self.load_flighttrack()
            else:
                logging.info("%s file already added", text)
        self.labelStatus.setText("Status: Files added successfully.")

    def parse_ftml(self, filename):
        """Load a flight track from an XML file at <filename>.
        """
        _dirname, _name = os.path.split(filename)
        _fs = open_fs(_dirname)
        datasource = _fs.open(_name)
        try:
            doc = xml.dom.minidom.parse(datasource)
        except xml.parsers.expat.ExpatError as ex:
            raise SyntaxError(str(ex))

        ft_el = doc.getElementsByTagName("FlightTrack")[0]

        waypoints_list = []
        for wp_el in ft_el.getElementsByTagName("Waypoint"):

            location = wp_el.getAttribute("location")
            lat = float(wp_el.getAttribute("lat"))
            lon = float(wp_el.getAttribute("lon"))
            flightlevel = float(wp_el.getAttribute("flightlevel"))
            comments = wp_el.getElementsByTagName("Comments")[0]
            # If num of comments is 0(null comment), then return ''
            if len(comments.childNodes):
                comments = comments.childNodes[0].data.strip()
            else:
                comments = ''

            waypoints_list.append((lat, lon, flightlevel, location, comments))
        # return waypoints_list
        return waypoints_list

    def save_settings(self):
        """
        Save Flighttrack settings after closing of view.
        """
        for entry in self.dict_files.values():
            entry["track"] = None
        settings = {
            "saved_files": self.dict_files
        }
        save_settings_qsettings(self.settings_tag, settings)

    def load_flighttrack(self):
        """
        Load Multiple Flighttracks simultaneously and construct corresponding
        flight patches on topview.
        """
        for index in range(self.list_flighttrack.count()):
            if self.list_flighttrack.item(index).text() in self.dict_files:
                if self.dict_files[self.list_flighttrack.item(index).text()]["track"] is None:
                    self.directory_location = str(self.list_flighttrack.item(index).text())
                    self.waypoint_list = self.parse_ftml(self.directory_location)
                    patch = MultipleFlightpath(self.view.map, self.waypoint_list)
                    self.dict_files[self.list_flighttrack.item(index).text()]["track"] = patch

    def create_list_item(self, text):
        """
        Add Flighttracks to list widget.
        """
        item = QtWidgets.QListWidgetItem(text)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        item.setCheckState(QtCore.Qt.Checked)
        self.list_flighttrack.addItem(item)

    def remove_item(self):
        """
        Remove FTML file from list widget.
        """
        for index in range(self.list_flighttrack.count()):
            if hasattr(self.list_flighttrack.item(index), "checkState") and \
                    (self.list_flighttrack.item(index).checkState() == QtCore.Qt.Checked):  # If item is checked
                if self.dict_files[self.list_flighttrack.item(index).text()]['track'] is not None:
                    self.dict_files[self.list_flighttrack.item(index).text()]['track'].remove()
                del self.dict_files[self.list_flighttrack.item(index).text()]
                self.list_flighttrack.takeItem(index)
                self.remove_item()
        self.labelStatus.setText("Status: FTML File is Removed")
