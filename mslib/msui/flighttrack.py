# -*- coding: utf-8 -*-
"""

    mslib.msui.flighttrack
    ~~~~~~~~~~~~~~~~~~~~~~

    Data model representing a flight track. The model is derived from
    QAbstractTableModel, so that it can directly be connected to any Qt view.

    For better understanding of the code, compare to the 'ships' example
    from chapter 14/16 of 'Rapid GUI Programming with Python and Qt: The
    Definitive Guide to PyQt Programming' (Mark Summerfield).

    The model includes a method for computing the distance between waypoints
    and for the entire flight track.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2021 by the mss team, see AUTHORS.
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

import datetime
import logging
import os

import fs
import xml.dom.minidom
import xml.parsers.expat
from metpy.units import units

from mslib.msui.mss_qt import variant_to_string, variant_to_float
from PyQt5 import QtGui, QtCore, QtWidgets
from mslib import utils, __version__
from mslib import thermolib
from mslib.utils import config_loader, find_location, save_settings_qsettings, load_settings_qsettings
from mslib.msui.performance_settings import DEFAULT_PERFORMANCE
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default

from mslib.utils import writexml
xml.dom.minidom.Element.writexml = writexml
# Constants for identifying the table columns when the WaypointsTableModel is
# used with a QTableWidget.
LOCATION, LAT, LON, FLIGHTLEVEL, PRESSURE = list(range(5))
TIME_UTC = 9


def seconds_to_string(seconds):
    """
    Format a time given in seconds to a string HH:MM:SS. Used for the
    'leg time/cum. time' columns of the table view.
    """
    hours, seconds = divmod(int(seconds), 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


TABLE_FULL = [
    ("Location                   ", lambda waypoint: waypoint.location, True),
    ("Lat\n(+-90)", lambda waypoint: round(float(waypoint.lat), 2), True),
    ("Lon\n(+-180)", lambda waypoint: round(float(waypoint.lon), 2), True),
    ("Flightlevel", lambda waypoint: waypoint.flightlevel, True),
    ("Pressure\n(hPa)", lambda waypoint: QtCore.QLocale().toString(waypoint.pressure / 100., 'f', 2), True),
    ("Leg dist.\n(km [nm])", lambda waypoint: f"{int(waypoint.distance_to_prev):d} "
                                              f"[{int(waypoint.distance_to_prev / 1.852):d}]", False),
    ("Cum. dist.\n(km [nm])", lambda waypoint: f"{int(waypoint.distance_total):d} "
                                               f"[{int(waypoint.distance_total / 1.852):d}]", False),
    ("Leg time", lambda waypoint: seconds_to_string(waypoint.leg_time), False),
    ("Cum. time", lambda waypoint: seconds_to_string(waypoint.cum_time), False),
    ("Time (UTC)", lambda waypoint: waypoint.utc_time.strftime("%Y-%m-%d %H:%M:%S"), False),
    ("Rem. fuel\n(lb)", lambda waypoint: f"{int(waypoint.rem_fuel):d}", False),
    ("Aircraft\nweight (lb)", lambda waypoint: f"{int(waypoint.weight):d}", False),
    ("Ceiling\naltitude (hft)", lambda waypoint: f"{waypoint.ceiling_alt:d}", False),
    ("Ascent rate\n(ft/minute)", lambda waypoint: f"{waypoint.ascent_rate:d}", False),
    ("Comments                        ", lambda waypoint: waypoint.comments, True),
]

TABLE_SHORT = [TABLE_FULL[_i] for _i in range(7)] + [TABLE_FULL[-1]] + [("", lambda _: "", False)] * 8


class Waypoint(object):
    """
    Represents a waypoint with position, altitude and further
    properties. Used internally by WaypointsTableModel.
    """

    def __init__(self, lat=0, lon=0, flightlevel=0, location="", comments=""):
        self.location = location
        locations = config_loader(dataset='locations')
        if location in locations:
            self.lat, self.lon = locations[location]
        else:
            self.lat = lat
            self.lon = lon
        self.flightlevel = flightlevel
        self.pressure = thermolib.flightlevel2pressure(flightlevel * units.hft).magnitude
        self.distance_to_prev = 0.
        self.distance_total = 0.
        self.comments = comments

        # Performance fields (for values read from the flight performance
        # service).
        self.leg_time = None  # time from previous waypoint
        self.cum_time = None  # total time of flight
        self.utc_time = None  # time in UTC since given takeoff time
        self.leg_fuel = None  # fuel consumption since previous waypoint
        self.rem_fuel = None  # total fuel consumption
        self.weight = None  # aircraft gross weight
        self.ceiling_alt = None  # aircraft ceiling altitude
        self.ascent_rate = None  # aircraft ascent rate

        self.wpnumber_major = None
        self.wpnumber_minor = None

    def __str__(self):
        """
        String representation of the waypoint (e.g., when used with the print
        statement).
        """
        return f"WAYPOINT(LAT={self.lat:f}, LON={self.lon:f}, FL={self.flightlevel:f})"


class WaypointsTableModel(QtCore.QAbstractTableModel):
    """
    Qt-QAbstractTableModel-derived data structure representing a flight
    track composed of a number of waypoints.

    Objects of this class can be directly connected to any Qt view that is
    able to handle tables models.

    Provides methods to store and load the model to/from an XML file, to compute
    distances between the individual waypoints, and to interpret the results of
    flight performance calculations.
    """

    def __init__(self, name="", filename=None, waypoints=None, mscolab_mode=False, data_dir=mss_default.mss_dir,
                 xml_content=None):
        super(WaypointsTableModel, self).__init__()
        self.name = name  # a name for this flight track
        self.filename = filename  # filename for store/load
        self.data_dir = data_dir
        self.modified = False  # for "save on exit"
        self.waypoints = []  # user-defined waypoints
        # file-save events are handled in a different manner
        self.mscolab_mode = mscolab_mode

        # self.aircraft.setErrorHandling("permissive")
        self.settings_tag = "performance"
        self.load_settings()

        # If a filename is passed to the constructor, load data from this file.
        if filename is not None:
            if filename.endswith(".ftml"):
                self.load_from_ftml(filename)
            else:
                logging.debug("No known file extension! '%s'", filename)

        # If xml string is passed to constructor, load data from that
        elif xml_content is not None:
            self.load_from_xml_data(xml_content)

        if waypoints:
            self.replace_waypoints(waypoints)

    def load_settings(self):
        """
        Load settings from the file self.settingsfile.
        """
        self.performance_settings = load_settings_qsettings(self.settings_tag, DEFAULT_PERFORMANCE)

    def save_settings(self):
        """
        Save the current settings (map appearance) to the file
        self.settingsfile.
        """
        save_settings_qsettings(self.settings_tag, self.performance_settings)

    def flags(self, index):
        """
        Used to specify which table columns can be edited by the user;
        overrides the corresponding QAbstractTableModel method.
        """
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled
        column = index.column()
        table = TABLE_SHORT
        if self.performance_settings["visible"]:
            table = TABLE_FULL
        if table[column][2]:
            return QtCore.Qt.ItemFlags(
                QtCore.QAbstractTableModel.flags(self, index) |
                QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsDragEnabled |
                QtCore.Qt.ItemIsDropEnabled)
        else:
            return QtCore.Qt.ItemFlags(
                QtCore.QAbstractTableModel.flags(self, index) |
                QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """
        Return a data field at the given index (of type QModelIndex,
        specifying row and column); overrides the corresponding
        QAbstractTableModel method.

        NOTE: Other roles (e.g. for display appearance) could be specified in
        this method as well. Cf. the 'ships' example in chapter 14/16 of 'Rapid
        GUI Programming with Python and Qt: The Definitive Guide to PyQt
        Programming' (Mark Summerfield).
        """
        waypoints = self.waypoints

        if not index.isValid() or not (0 <= index.row() < len(waypoints)):
            return QtCore.QVariant()
        waypoint = waypoints[index.row()]
        column = index.column()
        if role == QtCore.Qt.DisplayRole:
            if self.performance_settings["visible"]:
                return QtCore.QVariant(TABLE_FULL[column][1](waypoint))
            else:
                return QtCore.QVariant(TABLE_SHORT[column][1](waypoint))
        elif role == QtCore.Qt.TextAlignmentRole:
            return QtCore.QVariant(int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter))
        return QtCore.QVariant()

    def waypoint_data(self, row):
        """
        Get the waypoint object defining the given row.
        """
        return self.waypoints[row]

    def all_waypoint_data(self):
        """
        Return the entire list of waypoints.
        """
        return self.waypoints

    def intermediate_points(self, numpoints=101, connection="greatcircle"):
        """
        Compute intermediate points between the waypoints.

        See mss_util.path_points() for additional arguments.

        Returns lats, lons.
        """
        path = [[wp.lat, wp.lon, wp.utc_time] for wp in self.waypoints]
        return utils.path_points(
            path, numpoints=numpoints, connection=connection)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """
        Return data describing the table header; overrides the
        corresponding QAbstractTableModel method.
        """
        if role == QtCore.Qt.TextAlignmentRole:
            if orientation == QtCore.Qt.Horizontal:
                return QtCore.QVariant(int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter))
            return QtCore.QVariant(int(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter))
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        # Return the names of the table columns.
        if orientation == QtCore.Qt.Horizontal:
            if self.performance_settings["visible"]:
                return QtCore.QVariant(TABLE_FULL[section][0])
            else:
                return QtCore.QVariant(TABLE_SHORT[section][0])
        # Table rows (waypoints) are labelled with their number (= number of
        # waypoint).
        return QtCore.QVariant(int(section))

    def rowCount(self, index=QtCore.QModelIndex()):
        """
        Number of waypoints in the model.
        """
        return len(self.waypoints)

    def columnCount(self, index=QtCore.QModelIndex()):
        return len(TABLE_FULL)

    def setData(self, index, value, role=QtCore.Qt.EditRole, update=True):
        """
        Change a data element of the flight track; overrides the
        corresponding QAbstractTableModel method.

        NOTE: Performance computations loose their validity if a change is made.
        """
        if index.isValid() and 0 <= index.row() < len(self.waypoints):
            waypoint = self.waypoints[index.row()]
            column = index.column()
            index2 = index  # in most cases only one field is being changed
            if column == LOCATION:
                waypoint.location = variant_to_string(value)
            elif column == LAT:
                try:
                    # The table fields accept basically any input.
                    # If the string cannot be converted to "float" (raises ValueError), the user input is discarded.
                    value = variant_to_float(value)
                except TypeError as ex:
                    logging.error("unexpected error: %s %s %s %s", type(ex), ex, type(value), value)
                except ValueError as ex:
                    logging.error("%s", ex)
                else:
                    waypoint.lat = value
                    waypoint.location = ""
                    loc = find_location(waypoint.lat, waypoint.lon, 1e-3)
                    if loc is not None:
                        waypoint.lat, waypoint.lon = loc[0]
                        waypoint.location = loc[1]
                    # A change of position requires an update of the distances.
                    if update:
                        self.update_distances(index.row())
                    # Notify the views that items between the edited item and
                    # the distance item of the corresponding waypoint have been
                    # changed.
                    # Delete the location name -- it won't be valid anymore
                    # after its coordinates have been changed.
                    index2 = self.createIndex(index.row(), LOCATION)
            elif column == LON:
                try:
                    # The table fields accept basically any input.
                    # If the string cannot be converted to "float" (raises ValueError), the user input is discarded.
                    value = variant_to_float(value)
                except TypeError as ex:
                    logging.error("unexpected error: %s %s %s %s", type(ex), ex, type(value), value)
                except ValueError as ex:
                    logging.error("%s", ex)
                else:
                    waypoint.lon = value
                    waypoint.location = ""
                    loc = find_location(waypoint.lat, waypoint.lon, 1e-3)
                    if loc is not None:
                        waypoint.lat, waypoint.lon = loc[0]
                        waypoint.location = loc[1]
                    if update:
                        self.update_distances(index.row())
                    index2 = self.createIndex(index.row(), LOCATION)
            elif column == FLIGHTLEVEL:
                try:
                    # The table fields accept basically any input.
                    # If the string cannot be converted to "float" (raises ValueError), the user input is discarded.
                    flightlevel = variant_to_float(value)
                    pressure = float(thermolib.flightlevel2pressure(flightlevel * units.hft).magnitude)
                except TypeError as ex:
                    logging.error("unexpected error: %s %s %s %s", type(ex), ex, type(value), value)
                except ValueError as ex:
                    logging.error("%s", ex)
                else:
                    waypoint.flightlevel = flightlevel
                    waypoint.pressure = pressure
                    if update:
                        self.update_distances(index.row())
                    # need to notify view of the second item that has been
                    # changed as well.
                    index2 = self.createIndex(index.row(), PRESSURE)
            elif column == PRESSURE:
                try:
                    # The table fields accept basically any input.
                    # If the string cannot be converted to "float" (raises ValueError), the user input is discarded.
                    pressure = variant_to_float(value) * 100  # convert hPa to Pa
                    if pressure > 200000:
                        raise ValueError
                    flightlevel = float(round(thermolib.pressure2flightlevel(pressure * units.Pa).magnitude))
                    pressure = float(thermolib.flightlevel2pressure(flightlevel * units.hft).magnitude)
                except TypeError as ex:
                    logging.error("unexpected error: %s %s %s %s", type(ex), ex, type(value), value)
                except ValueError as ex:
                    logging.error("%s", ex)
                else:
                    waypoint.pressure = pressure
                    waypoint.flightlevel = flightlevel
                    if update:
                        self.update_distances(index.row())
                    index2 = self.createIndex(index.row(), FLIGHTLEVEL)
            else:
                waypoint.comments = variant_to_string(value)
            self.modified = True
            # Performance computations loose their validity if a change is made.
            if update:
                self.dataChanged.emit(index, index2)
            return True
        return False

    def insertRows(self, position, rows=1, index=QtCore.QModelIndex(),
                   waypoints=None):
        """
        Insert waypoint; overrides the corresponding QAbstractTableModel
        method.
        """
        if not waypoints:
            waypoints = [Waypoint(0, 0, 0)] * rows

        assert len(waypoints) == rows, (waypoints, rows)

        self.beginInsertRows(QtCore.QModelIndex(), position,
                             position + rows - 1)
        for row, wp in enumerate(waypoints):
            self.waypoints.insert(position + row, wp)

        self.update_distances(position, rows=rows)
        self.endInsertRows()
        self.modified = True
        return True

    def removeRows(self, position, rows=1, index=QtCore.QModelIndex()):
        """
        Remove waypoint; overrides the corresponding QAbstractTableModel
        method.
        """
        # beginRemoveRows emits rowsAboutToBeRemoved(index, first, last).
        self.beginRemoveRows(QtCore.QModelIndex(), position,
                             position + rows - 1)
        self.waypoints = self.waypoints[:position] + self.waypoints[position + rows:]
        if position < len(self.waypoints):
            self.update_distances(position, rows=min(rows, len(self.waypoints) - position))

        # endRemoveRows emits rowsRemoved(index, first, last).
        self.endRemoveRows()
        self.modified = True
        return True

    def update_distances(self, position, rows=1):
        """
        Update all distances in a flight track that are affected by a
        waypoint change involving <rows> waypoints starting at index
        <position>.

        Distances are computed along great circles.

        If rows=1, the distance to the previous waypoint is updated for
        waypoints <position> and <position+1>. The total flight track distance
        is updated for all waypoint following <position>.

        If rows>1, the distances to the previous waypoints are updated
        according to the number of modified waypoints.
        """
        waypoints = self.waypoints
        aircraft = self.performance_settings["aircraft"]

        def get_duration_fuel(flightlevel0, flightlevel1, distance, weight, lastleg):
            if flightlevel0 == flightlevel1:
                tas, fuelflow = aircraft.get_cruise_performance(flightlevel0 * 100, weight)
                duration = 3600. * distance / (1.852 * tas)  # convert to s (tas is in nm/h)
                leg_fuel = duration * fuelflow / 3600.
                return duration, leg_fuel
            else:
                if flightlevel0 < flightlevel1:
                    duration0, dist0, fuel0 = aircraft.get_climb_performance(flightlevel0 * 100, weight)
                    duration1, dist1, fuel1 = aircraft.get_climb_performance(flightlevel1 * 100, weight)
                else:
                    duration0, dist0, fuel0 = aircraft.get_descent_performance(flightlevel0 * 100, weight)
                    duration1, dist1, fuel1 = aircraft.get_descent_performance(flightlevel1 * 100, weight)
                duration = (duration1 - duration0) * 60  # convert from min to s
                dist = (dist1 - dist0) * 1.852  # convert from nm to km
                fuel = fuel1 - fuel0
                if lastleg:
                    duration_p, fuel_p = get_duration_fuel(flightlevel0, flightlevel0, distance - dist, weight, False)
                else:
                    duration_p, fuel_p = get_duration_fuel(flightlevel1, flightlevel1, distance - dist, weight, False)
                return duration + duration_p, fuel + fuel_p

        pos = position
        for offset in range(rows):
            pos = position + offset
            wp1 = waypoints[pos]
            # The distance to the first waypoint is zero.
            if pos == 0:
                wp1.distance_to_prev = 0.
                wp1.distance_total = 0.

                wp1.leg_time = 0  # time from previous waypoint
                wp1.cum_time = 0  # total time of flight
                wp1.utc_time = self.performance_settings["takeoff_time"].toPyDateTime()
                wp1.weight = self.performance_settings["takeoff_weight"]
                wp1.leg_fuel = 0
                wp1.rem_fuel = self.performance_settings["takeoff_weight"] - self.performance_settings["empty_weight"]
                wp1.ascent_rate = 0
            else:
                wp0 = waypoints[pos - 1]
                wp1.distance_to_prev = utils.get_distance((wp0.lat, wp0.lon),
                                                          (wp1.lat, wp1.lon))

                last = (pos - 1 == rows)
                time, fuel = get_duration_fuel(
                    wp0.flightlevel, wp1.flightlevel, wp1.distance_to_prev, wp0.weight, lastleg=last)
                wp1.leg_time = time
                wp1.cum_time = wp0.cum_time + wp1.leg_time
                wp1.utc_time = wp0.utc_time + datetime.timedelta(seconds=wp1.leg_time)
                wp1.leg_fuel = fuel
                wp1.rem_fuel = wp0.rem_fuel - wp1.leg_fuel
                wp1.weight = wp0.weight - wp1.leg_fuel
                if wp1.leg_time != 0:
                    wp1.ascent_rate = int((wp1.flightlevel - wp0.flightlevel) * 100 / (wp1.leg_time / 60))
                else:
                    wp1.ascent_rate = 0
            wp1.ceiling_alt = aircraft.get_ceiling_altitude(wp1.weight)

        # Update the distance of the following waypoint as well.
        if pos < len(waypoints) - 1:
            wp2 = waypoints[pos + 1]
            wp2.distance_to_prev = utils.get_distance((wp1.lat, wp1.lon),
                                                      (wp2.lat, wp2.lon))
            if wp2.leg_time != 0:
                wp2.ascent_rate = int((wp2.flightlevel - wp1.flightlevel) * 100 / (wp2.leg_time / 60))
            else:
                wp2.ascent_rate = 0

        # Update total distances of waypoint at index position and all
        # following waypoints.
        for i in range(max(min(position, 1), 1), len(waypoints)):
            wp0 = waypoints[i - 1]
            wp1 = waypoints[i]
            wp1.distance_total = wp0.distance_total + wp1.distance_to_prev
            wp1.weight = wp0.weight - wp0.leg_fuel
            last = (i + 1 == len(waypoints))
            time, fuel = get_duration_fuel(
                wp0.flightlevel, wp1.flightlevel, wp1.distance_to_prev, wp0.weight, lastleg=last)

            wp1.leg_time = time
            wp1.cum_time = wp0.cum_time + wp1.leg_time
            wp1.utc_time = wp0.utc_time + datetime.timedelta(seconds=wp1.leg_time)
            wp1.leg_fuel = fuel
            wp1.rem_fuel = wp0.rem_fuel - wp1.leg_fuel
            wp1.weight = wp0.weight - wp1.leg_fuel
            wp1.ceiling_alt = aircraft.get_ceiling_altitude(wp1.weight)

        index1 = self.createIndex(0, TIME_UTC)
        self.dataChanged.emit(index1, index1)

    def invert_direction(self):
        self.waypoints = self.waypoints[::-1]
        if len(self.waypoints) > 0:
            self.waypoints[0].distance_to_prev = 0
            self.waypoints[0].distance_total = 0
        for i in range(1, len(self.waypoints)):
            wp_comm = self.waypoints[i].comments
            if len(wp_comm) == 9 and wp_comm.startswith("Hexagon "):
                wp_comm = f"Hexagon {(8 - int(wp_comm[-1])):d}"
                self.waypoints[i].comments = wp_comm
        self.update_distances(position=0, rows=len(self.waypoints))
        index = self.index(0, 0)

        self.layoutChanged.emit()
        self.dataChanged.emit(index, index)

    def replace_waypoints(self, new_waypoints):
        self.waypoints = []
        self.insertRows(0, rows=len(new_waypoints), waypoints=new_waypoints)

    def save_to_ftml(self, filename=None):
        """
        Save the flight track to an XML file.

        Arguments:
        filename -- complete path to the file to save. If None, a previously
                    specified filename will be used. If no filename has been
                    specified at all, a ValueError exception will be raised.
        """
        if not filename:
            raise ValueError("filename to save flight track cannot be None or empty")

        self.filename = filename
        self.name = fs.path.basename(filename.replace(".ftml", "").strip())
        doc = self.get_xml_doc()
        dirname, name = fs.path.split(self.filename)
        file_dir = fs.open_fs(dirname)
        with file_dir.open(name, 'w') as file_object:
            doc.writexml(file_object, indent="  ", addindent="  ", newl="\n", encoding="utf-8")
        file_dir.close()

    def get_xml_doc(self):
        doc = xml.dom.minidom.Document()
        ft_el = doc.createElement("FlightTrack")
        ft_el.setAttribute("version", __version__)
        doc.appendChild(ft_el)
        # The list of waypoint elements.
        wp_el = doc.createElement("ListOfWaypoints")
        ft_el.appendChild(wp_el)
        for wp in self.waypoints:
            element = doc.createElement("Waypoint")
            wp_el.appendChild(element)
            element.setAttribute("location", str(wp.location))
            element.setAttribute("lat", str(wp.lat))
            element.setAttribute("lon", str(wp.lon))
            element.setAttribute("flightlevel", str(wp.flightlevel))
            comments = doc.createElement("Comments")
            comments.appendChild(doc.createTextNode(str(wp.comments)))
            element.appendChild(comments)
        return doc

    def get_xml_content(self):
        doc = self.get_xml_doc()
        return doc.toprettyxml(indent="  ", newl="\n")

    def load_from_ftml(self, filename):
        """
        Load a flight track from an XML file at <filename>.
        """
        _dirname, _name = os.path.split(filename)
        _fs = fs.open_fs(_dirname)
        xml_content = _fs.readtext(_name)
        name = os.path.basename(filename.replace(".ftml", "").strip())
        self.load_from_xml_data(xml_content, name)

    def load_from_xml_data(self, xml_content, name="Flight track"):
        try:
            doc = xml.dom.minidom.parseString(xml_content)
        except xml.parsers.expat.ExpatError as ex:
            raise SyntaxError(str(ex))

        ft_el = doc.getElementsByTagName("FlightTrack")[0]

        self.name = name

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
                comments = str('')

            waypoints_list.append(Waypoint(lat, lon, flightlevel,
                                           location=location,
                                           comments=comments))
        self.replace_waypoints(waypoints_list)

    def get_filename(self):
        return self.filename


#
# CLASS  WaypointDelegate
#


class WaypointDelegate(QtWidgets.QItemDelegate):
    """
    Qt delegate class for the appearance of the table view. Based on the
    'ships' example in chapter 14/16 of 'Rapid GUI Programming with Python
    and Qt: The Definitive Guide to PyQt Programming' (Mark Summerfield).
    """

    def __init__(self, parent=None):
        super(WaypointDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        """
        Colors waypoints with a minor waypoint number (i.e. intermediate
        waypoints generated by the flight performance service) in red.
        """
        wpnumber_minor = index.model().waypoint_data(index.row()).wpnumber_minor
        if wpnumber_minor is not None and wpnumber_minor > 0:
            newpalette = QtGui.QPalette(option.palette)
            colour = QtGui.QColor(170, 0, 0)  # dark red
            newpalette.setColor(QtGui.QPalette.Text, colour)
            colour = QtGui.QColor(255, 255, 0)  # yellow
            newpalette.setColor(QtGui.QPalette.HighlightedText, colour)
            option.palette = newpalette
        QtWidgets.QItemDelegate.paint(self, painter, option, index)

    def createEditor(self, parent, option, index):
        """
        Create a combobox listing predefined locations in the LOCATION
        column.
        """
        if index.column() == LOCATION:
            combobox = QtWidgets.QComboBox(parent)
            locations = config_loader(dataset='locations')
            adds = list(locations.keys())
            if self.parent() is not None:
                for loc in [wp.location for wp in self.parent().waypoints_model.all_waypoint_data() if
                            wp.location != ""]:
                    if loc not in adds:
                        adds.append(loc)
            combobox.addItems(sorted(adds))

            combobox.setEditable(True)
            return combobox
        else:
            # All other columns get the standard editor.
            return QtWidgets.QItemDelegate.createEditor(self, parent, option, index)

    def setEditorData(self, editor, index):
        text = index.model().data(index, QtCore.Qt.DisplayRole).value()
        if index.column() in (LOCATION,):
            i = editor.findText(text)
            if i == -1:
                i = 0
            editor.setCurrentIndex(i)
        else:
            QtWidgets.QItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        """
        For the LOCATION column: If the user selects a location from the
        combobox, get the corresponding coordinates.
        """
        if index.column() == LOCATION:
            loc = editor.currentText()
            locations = config_loader(dataset='locations')
            if loc in locations:
                lat, lon = locations[loc]
                # Don't update distances and flight performance twice, hence
                # set update=False for LAT.
                model.setData(index.sibling(index.row(), LAT), QtCore.QVariant(lat), update=False)
                model.setData(index.sibling(index.row(), LON), QtCore.QVariant(lon))
            else:
                for wp in self.parent().waypoints_model.all_waypoint_data():
                    if loc == wp.location:
                        lat, lon = wp.lat, wp.lon
                        # Don't update distances and flight performance twice, hence
                        # set update=False for LAT.
                        model.setData(index.sibling(index.row(), LAT), QtCore.QVariant(lat), update=False)
                        model.setData(index.sibling(index.row(), LON), QtCore.QVariant(lon))

            model.setData(index, QtCore.QVariant(editor.currentText()))
        else:
            QtWidgets.QItemDelegate.setModelData(self, editor, model, index)
