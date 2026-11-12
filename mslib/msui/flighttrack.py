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

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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
import math
import os
from pathlib import Path

import xml.dom.minidom
import defusedxml.minidom
from defusedxml import DefusedXmlException

from PyQt5 import QtGui, QtCore, QtWidgets

from mslib import __version__
from mslib.utils.units import units
from mslib.utils.coordinate import path_points, get_distance
from mslib.msui.utils.find_location import find_location
from mslib.utils import thermolib
from mslib.utils.verify_waypoint_data import verify_waypoint_data
from mslib.msui.utils.config import config_loader, save_settings_qsettings, load_settings_qsettings
from mslib.msui.utils.qt import variant_to_string, variant_to_float
from mslib.msui.performance_settings import DEFAULT_PERFORMANCE

# Constants for identifying the table columns when the WaypointsTableModel is
# used with a QTableWidget.
LOCATION, LAT, LON, FLIGHTLEVEL, PRESSURE = list(range(5))
TIME_UTC = 9


def seconds_to_string(seconds):
    """
    Format a time given in seconds, rounded to full seconds, to a string
    HH:MM:SS. Used for the 'leg time/cum. time' columns of the table view.
    """
    hours, seconds = divmod(math.floor(seconds + 0.5), 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_utc_time(utc_time):
    """
    Format a waypoint time rounded to full seconds, as the leg times are.
    Times are computed from fractional leg durations, truncation would show
    e.g. 11:59:59 for a time the user entered as 12:00:00.
    """
    utc_time = (utc_time + datetime.timedelta(microseconds=500000)).replace(microsecond=0)
    return utc_time.strftime("%Y-%m-%d %H:%M:%S")


def qdatetime_fields(qdatetime):
    """
    Return the date and time fields of a QDateTime as naive datetime. All times
    in MSS are UTC by definition, whatever time spec the QDateTime carries:
    e.g. take off times stored by earlier versions have local spec, and their
    fields are what the user entered and saw as UTC. Converting with toUTC()
    would shift them by the offset of the local zone.
    """
    date, time = qdatetime.date(), qdatetime.time()
    return datetime.datetime(date.year(), date.month(), date.day(),
                             time.hour(), time.minute(), time.second(), time.msec() * 1000)


def utc_qdatetime(utc_time):
    """
    Convert a naive datetime holding UTC to a QDateTime in UTC. Going via
    local time (QDateTime(datetime), QDateTime.fromString) would give an
    invalid QDateTime for times in a daylight saving gap of the local zone.
    """
    return QtCore.QDateTime(
        QtCore.QDate(utc_time.year, utc_time.month, utc_time.day),
        QtCore.QTime(utc_time.hour, utc_time.minute, utc_time.second, utc_time.microsecond // 1000),
        QtCore.Qt.UTC)


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
    ("Time (UTC)", lambda waypoint: format_utc_time(waypoint.utc_time), True),
    ("Rem. fuel\n(lb)", lambda waypoint: f"{int(waypoint.rem_fuel):d}", False),
    ("Aircraft\nweight (lb)", lambda waypoint: f"{int(waypoint.weight):d}", False),
    ("Ceiling\naltitude (hft)", lambda waypoint: f"{waypoint.ceiling_alt:d}", False),
    ("Ascent rate\n(ft/minute)", lambda waypoint: f"{waypoint.ascent_rate:d}", False),
    ("Comments                        ", lambda waypoint: waypoint.comments, True),
]

# Number of the first table column that is filled with data retrieved by the
# linear view. All columns left of it are described by TABLE_FULL.
LINEAR_DATA_COLUMN = len(TABLE_FULL)


def changed_columns(index1, index2):
    """
    Return the set of columns covered by the range of a dataChanged() signal.
    """
    return set(range(min(index1.column(), index2.column()), max(index1.column(), index2.column()) + 1))


def values_at_waypoints(path_lats, path_lons, values, waypoints, tolerance=1e-6):
    """
    Pick those values of a linear section that belong to the given waypoints.

    A linear section is computed for interpolated points along the flight
    path, of which only a few coincide with a waypoint. The waypoints are
    matched in the order in which they appear along the path.

    Arguments:
    path_lats, path_lons -- coordinates of the interpolated points of the
                            linear section
    values -- one data value per interpolated point
    waypoints -- list of Waypoint objects the values are mapped onto
    tolerance -- maximum deviation of a coordinate that is still considered
                 to be the same point

    Returns a list with one entry per waypoint. Waypoints that are not part
    of the section, and waypoints where the data field is undefined (NaN),
    get None assigned.
    """
    result = [None] * len(waypoints)
    index = 0
    for i, (lat, lon) in enumerate(zip(path_lats, path_lons)):
        if index >= len(waypoints):
            break
        waypoint = waypoints[index]
        # The path is sent to the WMS server rounded to two decimals, hence
        # the returned coordinates have to be compared to rounded waypoints.
        if abs(lat - float(f"{waypoint.lat:.2f}")) < tolerance and \
                abs(lon - float(f"{waypoint.lon:.2f}")) < tolerance:
            if i < len(values) and not math.isnan(values[i]):
                result[index] = values[i]
            index += 1
    return result


def linear_data_columns(xmls, waypoints):
    """
    Convert the linear section responses of the WMS server into data columns
    at the positions of the given waypoints.

    Arguments:
    xmls -- list of XML elements as returned for a "LINE:1" request, see
            mslib.mswms.mpl_lsec
    waypoints -- list of Waypoint objects the values are mapped onto

    Returns a list of dictionaries with the keys "name", "unit" and "values",
    ready to be passed to WaypointsTableModel.set_linear_data().
    """
    columns = []
    names = set()
    for element in xmls:
        data = element.find("Data")
        lats = element.find("Latitude")
        lons = element.find("Longitude")
        if any(node is None or node.text is None for node in (data, lats, lons)):
            logging.debug("incomplete linear section data, skipping")
            continue
        title = element.find("Title")
        name = title.text if title is not None and title.text else "Data"
        # The name identifies the column, therefore it has to be unique.
        unique_name = name
        suffix = 1
        while unique_name in names:
            suffix += 1
            unique_name = f"{name} ({suffix})"
        names.add(unique_name)

        columns.append({
            "name": unique_name,
            "unit": data.attrib.get("unit", ""),
            "values": values_at_waypoints(
                [float(value) for value in lats.text.split(",")],
                [float(value) for value in lons.text.split(",")],
                [float(value) for value in data.text.split(",")],
                waypoints),
        })
    return columns


def load_from_xml_data(xml_content, name="Flight track"):
    try:
        doc = defusedxml.minidom.parseString(xml_content)
    except DefusedXmlException as ex:
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
            comments = ""

        waypoints_list.append(Waypoint(lat, lon, flightlevel,
                                       location=location,
                                       comments=comments))
    return waypoints_list


class Waypoint:
    """
    Represents a waypoint with position, altitude and further
    properties. Used internally by WaypointsTableModel.
    """

    def __init__(self, lat=0., lon=0., flightlevel=0., location="", comments=""):
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

        # Data values retrieved by the linear view for the position of this
        # waypoint (column name -> value).
        self.linear_data = {}

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

    # Signal emitted when a waypoint is moved, inserted or deleted
    changeMessageSignal = QtCore.pyqtSignal(str)
    # Signal emitted when the derived data of the waypoints (times, fuel,
    # weight) has changed while the flight plan has not, i.e. for a new take
    # off time or new performance settings.
    #
    # The signals of the model follow one contract, so that every change
    # triggers each costly redraw (WMS requests, MSColab uploads) at most once:
    # - dataChanged: a change of the flight plan itself (what get_xml_doc()
    #   writes), exactly one emit per setData() call, its range covers all
    #   changed columns of the row. The derived data of the waypoints is
    #   updated before, listeners recompute everything they need from it.
    # - rowsInserted/rowsRemoved/modelReset: structural changes, without an
    #   additional dataChanged.
    # - performanceDataChanged: derived data only, never in addition to the
    #   above.
    # - linearDataChanged: see below.
    performanceDataChanged = QtCore.pyqtSignal()
    # Signal emitted when the data columns filled by the linear view have
    # changed. This is deliberately not the dataChanged() signal, as the data
    # does not belong to the flight plan itself and must not trigger a redraw
    # of the flight path or an update of an MSColab operation.
    linearDataChanged = QtCore.pyqtSignal()

    def __init__(self, name="", filename=None, waypoints=None, mscolab_mode=False,
                 data_dir=None,
                 xml_content=None):
        super().__init__()
        self.name = name  # a name for this flight track
        self.filename = filename  # filename for store/load
        self.data_dir = data_dir
        self.modified = False  # for "save on exit"
        self.waypoints = []  # user-defined waypoints
        # file-save events are handled in a different manner
        self.mscolab_mode = mscolab_mode

        # Data columns filled by the linear view, a list of (name, unit)
        # tuples. The values themselves are stored per waypoint.
        self.linear_data_columns = []
        self.linear_data_visible = False

        # self.aircraft.setErrorHandling("permissive")
        self.settings_tag = "performance"
        self.load_settings()

        # If a filename is passed to the constructor, load data from this file.
        if filename is not None:
            self.load_from_ftml(filename)

        # If xml string is passed to constructor, load data from that
        elif xml_content is not None:
            self.load_from_xml_data(xml_content)

        if waypoints:
            self.replace_waypoints(waypoints)

    def load_settings(self):
        """
        Load settings from the file self.settingsfile.
        """
        # Copy, load_settings_qsettings updates the given defaults in place.
        settings = load_settings_qsettings(self.settings_tag, dict(DEFAULT_PERFORMANCE))
        # Performance is always shown, earlier versions stored a switch for it.
        settings.pop("visible", None)
        takeoff_time = settings["takeoff_time"]
        if not isinstance(takeoff_time, QtCore.QDateTime) or not takeoff_time.date().isValid():
            takeoff_time = DEFAULT_PERFORMANCE["takeoff_time"]
        # Earlier versions stored the take off time with local time spec.
        settings["takeoff_time"] = utc_qdatetime(qdatetime_fields(takeoff_time))
        self.performance_settings = settings

    def save_settings(self):
        """
        Save the current settings (map appearance) to the file
        self.settingsfile.
        """
        save_settings_qsettings(self.settings_tag, self.performance_settings)

    def set_performance_settings(self, settings):
        """
        Apply new performance settings, i.e. recompute times and fuel of all
        waypoints, and store them.
        """
        self.performance_settings = settings
        self.update_distances(0)
        self.save_settings()
        self.performanceDataChanged.emit()

    def flags(self, index):
        """
        Used to specify which table columns can be edited by the user;
        overrides the corresponding QAbstractTableModel method.
        """
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled
        column = index.column()
        # The data columns of the linear view are read only.
        if column < LINEAR_DATA_COLUMN and TABLE_FULL[column][2]:
            return QtCore.Qt.ItemFlags(
                int(QtCore.QAbstractTableModel.flags(self, index) |
                    QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsDragEnabled |
                    QtCore.Qt.ItemIsDropEnabled))
        else:
            return QtCore.Qt.ItemFlags(
                int(QtCore.QAbstractTableModel.flags(self, index) |
                    QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))

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
            if column >= LINEAR_DATA_COLUMN:
                return QtCore.QVariant(self.linear_data_value(waypoint, column))
            return QtCore.QVariant(TABLE_FULL[column][1](waypoint))
        elif role == QtCore.Qt.TextAlignmentRole:
            return QtCore.QVariant(int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter))
        elif role == QtCore.Qt.ForegroundRole and not self.flags(index) & QtCore.Qt.ItemIsEditable:
            # read-only cells, e.g. the computed performance data, in grey
            return QtCore.QVariant(QtWidgets.QApplication.palette().brush(QtGui.QPalette.Disabled, QtGui.QPalette.Text))
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
        return path_points(
            [wp.lat for wp in self.waypoints],
            [wp.lon for wp in self.waypoints],
            times=[wp.utc_time for wp in self.waypoints],
            numpoints=numpoints, connection=connection)

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
            if section >= LINEAR_DATA_COLUMN:
                columns = self.visible_linear_data_columns()
                if not 0 <= section - LINEAR_DATA_COLUMN < len(columns):
                    return QtCore.QVariant()
                name, unit = columns[section - LINEAR_DATA_COLUMN]
                return QtCore.QVariant(f"{name}\n({unit})" if unit else name)
            return QtCore.QVariant(TABLE_FULL[section][0])
        # Table rows (waypoints) are labelled with their number (= number of
        # waypoint).
        return QtCore.QVariant(int(section))

    def rowCount(self, index=QtCore.QModelIndex()):
        """
        Number of waypoints in the model.
        """
        return len(self.waypoints)

    def columnCount(self, index=QtCore.QModelIndex()):
        return LINEAR_DATA_COLUMN + len(self.visible_linear_data_columns())

    def visible_linear_data_columns(self):
        """
        Return the (name, unit) tuples of the data columns of the linear view
        that are currently appended to the table.
        """
        return self.linear_data_columns if self.linear_data_visible else []

    def linear_data_value(self, waypoint, column):
        """
        Return the value of the linear view data column <column> at the given
        waypoint, rounded to four significant digits. As for the other numeric
        columns this is the number itself, not a preformatted string, so that
        the table and the clipboard copy write it with the decimal point of
        the locale of the user. Waypoints without data (e.g. because the
        aircraft is on the ground) give an empty string.
        """
        columns = self.visible_linear_data_columns()
        if not 0 <= column - LINEAR_DATA_COLUMN < len(columns):
            return ""
        value = waypoint.linear_data.get(columns[column - LINEAR_DATA_COLUMN][0])
        return "" if value is None else float(f"{value:.2f}")

    def set_linear_data_visible(self, visible):
        """
        Show or hide the data columns filled by the linear view.
        """
        visible = bool(visible)
        if visible == self.linear_data_visible:
            return
        count = len(self.linear_data_columns)
        if count == 0:
            self.linear_data_visible = visible
        elif visible:
            self.beginInsertColumns(QtCore.QModelIndex(), LINEAR_DATA_COLUMN, LINEAR_DATA_COLUMN + count - 1)
            self.linear_data_visible = True
            self.endInsertColumns()
        else:
            self.beginRemoveColumns(QtCore.QModelIndex(), LINEAR_DATA_COLUMN, LINEAR_DATA_COLUMN + count - 1)
            self.linear_data_visible = False
            self.endRemoveColumns()
        self.linearDataChanged.emit()

    def set_linear_data(self, columns):
        """
        Store the data retrieved by the linear view.

        Arguments:
        columns -- list of dictionaries with the keys "name", "unit" and
                   "values", where "values" contains one value per waypoint
                   (None where no data is available). The names have to be
                   unique, they identify the columns. See
                   linear_data_columns().
        """
        for i, waypoint in enumerate(self.waypoints):
            waypoint.linear_data = {
                column["name"]: column["values"][i] for column in columns
                if i < len(column["values"]) and column["values"][i] is not None}
        self._set_linear_data_columns([(column["name"], column["unit"]) for column in columns])

    def set_linear_data_from_xml(self, xmls):
        """
        Store the linear section data of the given WMS responses, see
        linear_data_columns().
        """
        self.set_linear_data(linear_data_columns(xmls, self.waypoints))

    def clear_linear_data(self):
        """
        Drop all data retrieved by the linear view.
        """
        for waypoint in self.waypoints:
            waypoint.linear_data = {}
        self._set_linear_data_columns([])

    def _set_linear_data_columns(self, columns):
        """
        Adapt the table to the given list of (name, unit) data columns and
        notify the connected views.
        """
        previous = len(self.linear_data_columns)
        count = len(columns)
        if not self.linear_data_visible or previous == count:
            self.linear_data_columns = columns
        elif count > previous:
            self.beginInsertColumns(
                QtCore.QModelIndex(), LINEAR_DATA_COLUMN + previous, LINEAR_DATA_COLUMN + count - 1)
            self.linear_data_columns = columns
            self.endInsertColumns()
        else:
            self.beginRemoveColumns(
                QtCore.QModelIndex(), LINEAR_DATA_COLUMN + count, LINEAR_DATA_COLUMN + previous - 1)
            self.linear_data_columns = columns
            self.endRemoveColumns()
        if self.linear_data_visible and count > 0:
            self.headerDataChanged.emit(
                QtCore.Qt.Horizontal, LINEAR_DATA_COLUMN, LINEAR_DATA_COLUMN + count - 1)
        self.linearDataChanged.emit()

    def setData(self, index, value, role=QtCore.Qt.EditRole, update=True):
        """
        Change a data element of the flight track; overrides the
        corresponding QAbstractTableModel method.

        NOTE: Performance computations loose their validity if a change is made.
        """
        if index.isValid() and 0 <= index.row() < len(self.waypoints):
            waypoint = self.waypoints[index.row()]
            column = index.column()
            # In most cases only one field is being changed. Otherwise index
            # and index2 span all changed columns, left to right.
            index2 = index
            if column == LOCATION:
                if variant_to_string(value) == waypoint.location:
                    # e.g. a location picked in the table view, setting its
                    # coordinates has already set its name
                    return True
                waypoint.location = variant_to_string(value)
            elif column == LAT:
                try:
                    # The table fields accept basically any input.
                    # If the string cannot be converted to "float" (raises ValueError), the user input is discarded.
                    value = variant_to_float(value)
                    if not (-90 <= value <= 90):
                        raise ValueError
                except TypeError as ex:
                    logging.error("unexpected error: %s %s %s %s", type(ex), ex, type(value), value)
                    return False
                except ValueError as ex:
                    logging.error("%s %s '%s'", type(ex), ex, value)
                    return False
                else:
                    waypoint.lat = value
                    waypoint.location = ""
                    loc = find_location(waypoint.lat, waypoint.lon, 1e-3)
                    if loc is not None:
                        waypoint.lat, waypoint.lon = loc[0]
                        waypoint.location = loc[1]
                    # A change of position requires an update of the distances.
                    if update:
                        self.changeMessageSignal.emit(f'Moved waypoint {index.row()}')
                        self.update_distances(index.row())
                    # The location name has changed as well.
                    index = self.createIndex(index.row(), LOCATION)
                    index2 = self.createIndex(index.row(), LON)
            elif column == LON:
                try:
                    # The table fields accept basically any input.
                    # If the string cannot be converted to "float" (raises ValueError), the user input is discarded.
                    value = variant_to_float(value)
                    if not (-720 <= value <= 720):
                        raise ValueError
                except TypeError as ex:
                    logging.error("unexpected error: %s %s %s %s", type(ex), ex, type(value), value)
                    return False
                except ValueError as ex:
                    logging.error("%s %s '%s'", type(ex), ex, value)
                    return False
                else:
                    waypoint.lon = value
                    waypoint.location = ""
                    loc = find_location(waypoint.lat, waypoint.lon, 1e-3)
                    if loc is not None:
                        waypoint.lat, waypoint.lon = loc[0]
                        waypoint.location = loc[1]
                    if update:
                        self.changeMessageSignal.emit(f'Moved waypoint {index.row()}')
                        self.update_distances(index.row())
                    index = self.createIndex(index.row(), LOCATION)
                    index2 = self.createIndex(index.row(), LON)
            elif column == FLIGHTLEVEL:
                try:
                    # The table fields accept basically any input.
                    # If the string cannot be converted to "float" (raises ValueError), the user input is discarded.
                    flightlevel = variant_to_float(value)
                    pressure = float(thermolib.flightlevel2pressure(flightlevel * units.hft).magnitude)
                except TypeError as ex:
                    logging.error("unexpected error: %s %s %s %s", type(ex), ex, type(value), value)
                    return False
                except ValueError as ex:
                    logging.error("%s %s '%s'", type(ex), ex, value)
                    return False
                else:
                    waypoint.flightlevel = flightlevel
                    waypoint.pressure = pressure
                    if update:
                        self.changeMessageSignal.emit(f'Moved waypoint {index.row()}')
                        self.update_distances(index.row())
                    # The pressure has changed as well.
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
                    return False
                except ValueError as ex:
                    logging.error("%s", ex)
                    return False
                else:
                    waypoint.pressure = pressure
                    waypoint.flightlevel = flightlevel
                    if update:
                        self.changeMessageSignal.emit(f'Moved waypoint {index.row()}')
                        self.update_distances(index.row())
                    # The flight level has changed as well.
                    index = self.createIndex(index.row(), FLIGHTLEVEL)
                    index2 = self.createIndex(index.row(), PRESSURE)
            elif column == TIME_UTC:
                # Shift the whole flight so that this waypoint is reached at the given time.
                if isinstance(value, QtCore.QDateTime):
                    value = qdatetime_fields(value)
                try:
                    if not isinstance(value, datetime.datetime):
                        value = datetime.datetime.strptime(variant_to_string(value).strip(), "%Y-%m-%d %H:%M:%S")
                    # The table shows full seconds: leaving the editor unchanged
                    # must not shift the flight by the rounding difference.
                    if format_utc_time(value) == format_utc_time(waypoint.utc_time):
                        return True
                    takeoff = utc_qdatetime(value - datetime.timedelta(seconds=waypoint.cum_time))
                except (ValueError, OverflowError) as ex:
                    logging.error("%s %s '%s'", type(ex), ex, value)
                    return False
                self.performance_settings = dict(self.performance_settings, takeoff_time=takeoff)
                self.save_settings()
                # The leg times do not depend on the take off time.
                self._update_utc_times()
                # The flight plan itself is unchanged.
                self.performanceDataChanged.emit()
                return True
            else:
                if variant_to_string(value) == waypoint.comments:
                    return True
                waypoint.comments = variant_to_string(value)
            self.modified = True
            # Performance computations loose their validity if a change is made.
            if update:
                self.dataChanged.emit(index, index2)
            return True
        return False

    def insertRows(self, position, rows=1, index=QtCore.QModelIndex(),
                   waypoints=None, hexagonCreated=False, data_copied=False):
        """
        Insert waypoint; overrides the corresponding QAbstractTableModel
        method.
        """
        if not waypoints:
            waypoints = [Waypoint(0, 0, 0)] * rows

        assert len(waypoints) == rows, (waypoints, rows)

        savedChangeMessage = "Inserted a new waypoint."
        if hexagonCreated:
            savedChangeMessage = "Hexagon created."
        elif data_copied:
            savedChangeMessage = "Imported from another flight track"
        self.changeMessageSignal.emit(savedChangeMessage)

        self.beginInsertRows(QtCore.QModelIndex(), position,
                             position + rows - 1)
        for row, wp in enumerate(waypoints):
            self.waypoints.insert(position + row, wp)

        self.update_distances(position, rows=rows)
        self.endInsertRows()
        self.modified = True
        return True

    def removeRows(self, position, rows=1, index=QtCore.QModelIndex(), hexagonDeleted=False):
        """
        Remove waypoint; overrides the corresponding QAbstractTableModel
        method.
        """
        if hexagonDeleted:
            savedChangeMessage = f"Deleted waypoints {position}-{position + rows - 1}."
        else:
            savedChangeMessage = f"Deleted waypoint {position}."
        self.changeMessageSignal.emit(savedChangeMessage)

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
                wp1.weight = self.performance_settings["takeoff_weight"]
                wp1.leg_fuel = 0
                wp1.rem_fuel = self.performance_settings["takeoff_weight"] - self.performance_settings["empty_weight"]
                wp1.ascent_rate = 0
            else:
                wp0 = waypoints[pos - 1]
                wp1.distance_to_prev = get_distance(
                    wp0.lat, wp0.lon, wp1.lat, wp1.lon)

                last = (pos - 1 == rows)
                time, fuel = get_duration_fuel(
                    wp0.flightlevel, wp1.flightlevel, wp1.distance_to_prev, wp0.weight, lastleg=last)
                wp1.leg_time = time
                wp1.cum_time = wp0.cum_time + wp1.leg_time
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
            wp2.distance_to_prev = get_distance(
                wp1.lat, wp1.lon, wp2.lat, wp2.lon)
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
            wp1.leg_fuel = fuel
            wp1.rem_fuel = wp0.rem_fuel - wp1.leg_fuel
            wp1.weight = wp0.weight - wp1.leg_fuel
            wp1.ceiling_alt = aircraft.get_ceiling_altitude(wp1.weight)

        self._update_utc_times()

    def _update_utc_times(self):
        """
        Set the time of all waypoints from the take off time and their flight time.
        """
        takeoff_time = qdatetime_fields(self.performance_settings["takeoff_time"])
        for waypoint in self.waypoints:
            waypoint.utc_time = takeoff_time + datetime.timedelta(seconds=waypoint.cum_time)

    def invert_direction(self):
        self.beginResetModel()
        self.waypoints = self.waypoints[::-1]
        if len(self.waypoints) > 0:
            self.waypoints[0].distance_to_prev = 0
            self.waypoints[0].distance_total = 0
        for i in range(1, len(self.waypoints)):
            wp_comm = self.waypoints[i].comments
            if len(wp_comm) == 9 and wp_comm.startswith("Hexagon "):
                wp_comm = f"Hexagon {(8 - int(wp_comm[-1])):d}"
                self.waypoints[i].comments = wp_comm
        if len(self.waypoints) > 0:
            self.update_distances(position=0, rows=len(self.waypoints))
        self.endResetModel()
        self.modified = True

    def replace_waypoints(self, new_waypoints):
        self.changeMessageSignal.emit("Imported from another flight track")
        self.beginResetModel()
        self.waypoints = list(new_waypoints)
        if len(self.waypoints) > 0:
            self.update_distances(position=0, rows=len(self.waypoints))
        self.endResetModel()
        self.modified = True

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
        doc = self.get_xml_doc()
        with open(filename, "w") as file_object:
            doc.writexml(file_object, indent="  ", addindent="  ", newl="\n", encoding="utf-8")
        self.name = os.path.basename(self.filename).replace(".ftml", "").strip()

    def get_xml_doc(self):
        doc = xml.dom.minidom.Document()  # nosec, we take care of writing correct XML
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
        xml_content = Path(filename).read_text()
        name = Path(filename).stem.replace(".ftml", "").strip()
        self.load_from_xml_data(xml_content, name)

    def load_from_xml_data(self, xml_content, name="Flight track"):
        self.name = name
        if verify_waypoint_data(xml_content):
            _waypoints_list = load_from_xml_data(xml_content, name)
            self.replace_waypoints(_waypoints_list)
        else:
            raise SyntaxError(f"Invalid flight track filename: {name}")

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
        super().__init__(parent)

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
            adds = set(config_loader(dataset='locations'))
            if self.parent() is not None:
                for wp in self.parent().waypoints_model.all_waypoint_data():
                    if wp.location != "":
                        adds.add(wp.location)
            combobox.addItems(sorted(adds))
            combobox.setEditable(True)
            return combobox
        elif index.column() == TIME_UTC:
            editor = QtWidgets.QDateTimeEdit(parent)
            editor.setCalendarPopup(True)
            editor.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
            editor.setTimeSpec(QtCore.Qt.UTC)
            return editor
        else:
            # All other columns get the standard editor.
            return QtWidgets.QItemDelegate.createEditor(self, parent, option, index)

    def setEditorData(self, editor, index):
        value = index.model().data(index, QtCore.Qt.DisplayRole).value()
        if index.column() in (LOCATION,):
            i = editor.findText(value)
            if i == -1:
                i = 0
            editor.setCurrentIndex(i)
        elif index.column() == TIME_UTC:
            # Start from the displayed time, i.e. full seconds.
            editor.setDateTime(utc_qdatetime(datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")))
        else:
            editor.insert(str(value))

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
        elif index.column() == TIME_UTC:
            model.setData(index, editor.dateTime())
        else:
            QtWidgets.QItemDelegate.setModelData(self, editor, model, index)
