# -*- coding: utf-8 -*-
"""

    mslib.mss_util
    ~~~~~~~~~~~~~~

    Collection of utility routines for the Mission Support System.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2019 by the mss team, see AUTHORS.
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

from __future__ import division

from past.builtins import basestring


import datetime
from fs import open_fs, errors
import json
import logging
import netCDF4 as nc
import numpy as np
import os
from scipy.interpolate import interp1d
from scipy.ndimage import map_coordinates
import werkzeug.datastructures
import cartopy.geodesic as gd
import cartopy.crs as ccrs


from mslib.msui import constants, MissionSupportSystemDefaultConfig
from mslib.thermolib import pressure2flightlevel
from PyQt5 import QtCore


class FatalUserError(Exception):
    def __init__(self, error_string):
        logging.debug("{}".format(error_string))


def config_loader(config_file=None, dataset=None, default=None):
    """
    Function for loading json config data

    Args:
        config_file: json file, parameters for initializing mss,
        dataset: section to pull from json file
        default: values to return if dataset was requested and don't exist or config_file is not given

    Returns: a dictionary

    """
    if config_file is None:
        config_file = constants.CACHED_CONFIG_FILE
    if config_file is None:
        logging.info(
            'Default MSS configuration in place, no user settings, see http://mss.rtfd.io/en/stable/usage.html')
        default_config = dict(MissionSupportSystemDefaultConfig.__dict__)
        if dataset is None:
            return default_config
        else:
            try:
                return default_config[dataset]
            except KeyError:
                return default
    _dirname, _name = os.path.split(config_file)
    _fs = open_fs(_dirname)
    try:
        with _fs.open(_name, 'r') as source:
            data = json.load(source)
    except (AttributeError, IOError, TypeError, errors.ResourceNotFound) as ex:
        logging.error(u"MSS config File error '{:}' - '{:}' - '{:}'".format(config_file, type(ex), ex))
        if default is not None:
            return default
        raise IOError("MSS config File not found")
    except ValueError as ex:
        error_message = u"MSS config File '{:}' has a syntax error:\n\n'{}'".format(config_file, ex)
        raise FatalUserError(error_message)
    if dataset:
        try:
            return data[dataset]
        except KeyError:
            logging.debug(u"Config File used: '{:}'".format(config_file))
            logging.debug(u"Key not defined in config_file! '{:}'".format(dataset))
            if default is not None:
                return default
            raise KeyError("default value for key not set")

    return data


def get_distance(coord0, coord1):
    """
    Computes the distance between two points on the Earth surface
    Args:
        coord0: coordinate(lat/lon) of first point
        coord1: coordinate(lat/lon) of second point

    Returns:
        length of distance in km
    """
    pr = gd.Geodesic()
    return (pr.inverse([coord0[1], coord0[0]], [coord1[1], coord1[0]]).base[0, 0] / 1000.)


def find_location(lat, lon, tolerance=5):
    """
    Checks if a location is present at given coordinates
    :param lat: latitude
    :param lon: longitude
    :param tolerance: maximum distance between location and coordinates in km
    :return: None or lat/lon, name
    """
    locations = config_loader(dataset='locations', default=MissionSupportSystemDefaultConfig.locations)
    distances = sorted([(get_distance((lat, lon), (loc_lat, loc_lon)), loc)
                        for loc, (loc_lat, loc_lon) in locations.items()])
    if len(distances) > 0 and distances[0][0] <= tolerance:
        return locations[distances[0][1]], distances[0][1]
    else:
        return None


def save_settings_qsettings(tag, settings):
    """
    Saves a dictionary settings to disk.

    :param tag: string specifying the settings
    :param settings: dictionary of settings
    :return: None
    """
    assert isinstance(tag, basestring)
    assert isinstance(settings, dict)
    q_settings = QtCore.QSettings("mss", "mss-core")
    file_path = q_settings.fileName()
    logging.debug("storing settings for %s to %s", tag, file_path)
    try:
        q_settings.setValue(tag, QtCore.QVariant(settings))
    except (OSError, IOError) as ex:
        logging.warning("Problems storing %s settings (%s: %s).", tag, type(ex), ex)
    return settings


def load_settings_qsettings(tag, default_settings=None):
    """
    Loads a dictionary of settings from disk. May supply a dictionary of default settings
    to return in case the settings file is not present or damaged. The default_settings one will
    be updated by the restored one so one may rely on all keys of the default_settings dictionary
    being present in the returned dictionary.

    :param tag: string specifying the settings
    :param default_settings: dictionary of settings or None
    :return: dictionary of settings
    """
    if default_settings is None:
        default_settings = {}
    assert isinstance(default_settings, dict)
    settings = {}
    q_settings = QtCore.QSettings("mss", "mss-core")
    file_path = q_settings.fileName()
    logging.debug(u"loading settings for %s from %s", tag, file_path)
    try:
        settings = q_settings.value(tag)
    except Exception as ex:
        logging.error("Problems reloading stored %s settings (%s: %s). Switching to default",
                      tag, type(ex), ex)
    if isinstance(settings, dict):
        default_settings.update(settings)
    return default_settings


JSEC_START = datetime.datetime(2000, 1, 1)


def datetime_to_jsec(dt):
    """
    Calculate seconds since Jan 01 2000.
    """
    delta = dt - JSEC_START
    total = delta.days * 3600 * 24
    total += delta.seconds
    total += delta.microseconds * 1e-6
    return total


def jsec_to_datetime(jsecs):
    """
    Get the datetime from seconds since Jan 01 2000.
    """
    return JSEC_START + datetime.timedelta(seconds=jsecs)


def compute_hour_of_day(jsecs):
    date = JSEC_START + datetime.timedelta(seconds=jsecs)
    return date.hour + (date.minute / 60.) + (date.second / 3600.)


def fix_angle(ang):
    """
    Normalizes an angle between -180 and 180 degree.
    """
    while ang > 360:
        ang -= 360
    while ang < 0:
        ang += 360
    return ang


def rotate_point(point, angle, origin=(0, 0)):
    """Rotates a point. Angle is in degrees.
    Rotation is counter-clockwise"""
    angle = np.deg2rad(angle)
    temp_point = ((point[0] - origin[0]) * np.cos(angle) -
                  (point[1] - origin[1]) * np.sin(angle) + origin[0],
                  (point[0] - origin[0]) * np.sin(angle) +
                  (point[1] - origin[1]) * np.cos(angle) + origin[1])
    return temp_point


def convertHPAToKM(press):
    return (288.15 / 0.0065) * (1. - (press / 1013.25) ** (1. / 5.255)) / 1000.


def get_projection_params(proj):
    proj = proj.lower()
    if proj.startswith("crs:"):
        raise ValueError("CRS not supported")

        projid = proj[4:]
        if projid == "84":
            proj_params = {
                "basemap": {"projection": ccrs.PlateCarree()},
                "bbox": "degree"}
        else:
            raise ValueError("unsupported CRS code: '%s'", proj)

    elif proj.startswith("auto:"):
        raise ValueError("AUTO not supported")

        projid, unitsid, lon0, lat0 = proj[5:].split(",")
        if projid == "42001":
            proj_params = {
                "basemap": {"projection": ccrs.UTM()},
                "bbox": "meter({},{})".format(lon0, lat0)}
        elif projid == "42002":
            proj_params = {
                "basemap": {"projection": ccrs.TransverseMercator(central_longitude=lon0, central_latitude=lat0)},
                "bbox": "meter({},{})".format(lon0, lat0)}
        elif projid == "42003":
            proj_params = {
                "basemap": {"projection": ccrs.Orthographic(central_longitude=lon0, central_latitude=lat0)},
                "bbox": "meter({},{})".format(lon0, lat0)}
        else:
            raise ValueError("unspecified AUTO code: '%s'", proj)

    elif proj.startswith("auto2:"):
        raise ValueError("AUTO2 not supported")

        projid, factor, lon0, lat0 = proj[6:].split(",")
        if projid == "42001":
            proj_params = {
                "basemap": {"projection": ccrs.UTM()},
                "bbox": "meter({},{})".format(lon0, lat0)}
        elif projid == "42002":
            proj_params = {
                "basemap": {"projection": ccrs.TransverseMercator(central_longitude=lon0, central_latitude=lat0)},
                "bbox": "meter({},{})".format(lon0, lat0)}
        elif projid == "42003":
            proj_params = {
                "basemap": {"projection": ccrs.Orthographic(central_longitude=lon0, central_latitude=lat0)},
                "bbox": "meter({},{})".format(lon0, lat0)}
        elif projid == "42004":
            proj_params = {
                "basemap": {"projection": ccrs.PlateCarree(central_longitude=lon0)},
                "bbox": "meter({},{})".format(lon0, lat0)}
        elif projid == "42005":
            proj_params = {
                "basemap": {"projection": ccrs.Mollweide(central_longitude=lon0)},
                "bbox": "meter???"}
        else:
            raise ValueError("unspecified AUTO2 code: '%s'", proj)

    elif proj.startswith("epsg:"):
        epsg = proj[5:]
        if epsg.startswith("777") and len(epsg) == 8:  # user defined MSS code. deprecated.
            logging.warning("Using deprecated MSS-specific EPSG code. Switch to 'MSS:stere' instead.")
            lat_0, lon_0 = int(epsg[3:5]), int(epsg[5:])
            proj_params = {
                "basemap": {"projection": ccrs.Stereographic(central_latitude=lat_0, central_longitude=lon_0)},
                "bbox": "degree"}
        elif epsg.startswith("778") and len(epsg) == 8:  # user defined MSS code. deprecated.
            logging.warning("Using deprecated MSS-specific EPSG code. Switch to 'MSS:stere' instead.")
            lat_0, lon_0 = int(epsg[3:5]), int(epsg[5:])
            proj_params = {
                "basemap": {"projection": ccrs.Stereographic(central_latitude=-lat_0, central_longitude=lon_0)},
                "bbox": "degree"}
        elif epsg in ("4326"):
            proj_params = {"basemap": {"projection": ccrs.PlateCarree()}, "bbox": "degree"}
        elif epsg in ("4258"):
            proj_params = {"basemap": {"projection": ccrs.epsg(epsg)}, "bbox": "degree"}
        elif epsg in ("3031", "3412"):
            proj_params = {"basemap": {"projection": ccrs.epsg(epsg)}, "bbox": "meter(0,-90)"}
        elif epsg in ("3411", "3413", "3575", "3995"):
            proj_params = {"basemap": {"projection": ccrs.epsg(epsg)}, "bbox": "meter(0,90)"}
        elif epsg in ("3395", "3857"):
            proj_params = {"basemap": {"projection": ccrs.epsg(epsg)}, "bbox": "meter(0,0)"}
        elif epsg in ("4839"):
            proj_params = {"basemap": {"projection": ccrs.epsg(epsg)}, "bbox": "meter(10.5,51)"}
        elif epsg in ("31467"):
            proj_params = {"basemap": {"projection": ccrs.epsg(epsg)}, "bbox": "meter(-20.9631343,0.0037502)"}
        elif epsg in ("31468"):
            proj_params = {"basemap": {"projection": ccrs.epsg(epsg)}, "bbox": "meter(-25.4097892,0.0037466)"}
        else:
            raise ValueError("EPSG code not supported by basemap module: '%s'", proj)

    elif proj.startswith("mss:"):
        # some MSS-specific codes
        params = proj[4:].split(",")
        name = params[0]
        if name == "stere":
            lon0, lat0, lat_ts = params[1:]
            proj_params = {
                "basemap": {"projection": ccrs.Stereographic(central_longitude=lon0, central_latitude=lat0, true_scale_latitude=lat_ts)},
                "bbox": "degree"}
        elif name == "lcc":
            lon0, lat0, lat1, lat2 = params[1:]
            proj_params = {
                "basemap": {"projection": ccrs.LambertConformal(standard_parallels=(float(lat1), float(lat2)))},
                "bbox": "degree"}
        elif name == "merc":
            lat_ts = params[1]
            proj_params = {
                "basemap": {"projection": ccrs.Mercator(latitude_true_scale=lat_ts)},
                "bbox": "degree"}
        else:
            raise ValueError("unknown MSS projection: '%s'", proj)

    else:
        raise ValueError("unknown projection: '%s'", proj)
    logging.debug("Identified CRS '%s' as '%s'", proj, proj_params)
    return proj_params


def interpolate_vertsec(data3D, data3D_lats, data3D_lons, lats, lons):
    """
    Interpolate curtain[z,pos] (curtain[level,pos]) from data3D[z,y,x]
    (data3D[level,lat,lon]).

    This method is based on scipy.ndimage.map_coordinates().

    data3D can be on an IRREGULAR lat/lon grid, coordinates given by lats, lons.
    The lats, lons arrays can have arbitrary order, they do not have to be uniform.
    """
    # Create an empty field to accommodate the curtain.
    curtain = np.zeros([data3D.shape[0], len(lats)])

    # Transform lat/lon values to array index space. This is necessary to use
    # scipy.ndimage.map_coordinates().
    interp_lat = interp1d(data3D_lats, np.arange(len(data3D_lats)), bounds_error=False)
    ind_lats = interp_lat(lats)
    interp_lon = interp1d(data3D_lons, np.arange(len(data3D_lons)), bounds_error=False)
    ind_lons = interp_lon(lons)
    ind_coords = np.array([ind_lats, ind_lons])

    # One horizontal interpolation for each model level. The order
    # parameter controls the degree of the splines used, i.e. order=1
    # stands for linear interpolation.
    for ml in range(data3D.shape[0]):
        data = data3D[ml, :, :]
        curtain[ml, :] = map_coordinates(data, ind_coords, order=1)

    curtain[:, np.isnan(ind_lats) | np.isnan(ind_lons)] = np.nan
    return np.ma.masked_invalid(curtain)


def latlon_points(p1, p2, numpoints=100, connection='linear'):
    """
    Compute intermediate points between two given points.

    Arguments:
    p1, p2 -- points given as lat/lon pairs, i.e. p1, p2 = [lat, lon]
    numpoints -- number of intermediate points to be computed aloing the path
    connection -- method to compute the intermediate points. Can be
                  'linear' or 'greatcircle'

    Returns two arrays lats, lons with intermediate latitude and longitudes.
    """
    LAT = 0
    LON = 1
    TIME = 2
    lats, lons, times = None, None, None

    if connection == 'linear':
        lats = np.linspace(p1[LAT], p2[LAT], numpoints)
        lons = np.linspace(p1[LON], p2[LON], numpoints)
    elif connection == 'greatcircle':
        if numpoints > 2:
            pts = npts_cartopy((p1[LON], p1[LAT]), (p2[LON], p2[LAT]), numpoints - 2)
            lats = np.asarray([p1[LAT]] + [_x[1] for _x in pts] + [p2[LAT]])
            lons = np.asarray([p1[LON]] + [_x[0] for _x in pts] + [p2[LON]])
        else:
            lats = np.asarray([p1[LAT], p2[LAT]])
            lons = np.asarray([p1[LON], p2[LON]])

    p1_time, p2_time = nc.date2num([p1[TIME], p2[TIME]], "seconds since 2000-01-01")
    times = np.linspace(p1_time, p2_time, numpoints)

    return lats, lons, nc.num2date(times, "seconds since 2000-01-01")


def path_points(points, numpoints=100, connection='linear'):
    """
    Compute intermediate points of a path given by a list of points.

    Arguments:
    points -- list of lat/lon pairs, i.e. [[lat1,lon1], [lat2,lon2], ...]
    numpoints -- number of intermediate points to be computed along the path
    connection -- method to compute the intermediate points. Can be
                  'linear' or 'greatcircle'

    Returns two arrays lats, lons with intermediate latitude and longitudes.
    """
    if connection not in ['linear', 'greatcircle']:
        return None, None
    LAT = 0
    LON = 1
    TIME = 2

    # First compute the lengths of the individual path segments, i.e.
    # the distances between the points.
    distances = []
    for i in range(len(points) - 1):
        if connection == 'linear':
            # Use Euclidean distance in lat/lon space.
            d = np.hypot(points[i][LAT] - points[i + 1][LAT],
                         points[i][LON] - points[i + 1][LON])
        elif connection == 'greatcircle':
            # Use Vincenty distance provided by the geopy module.
            d = get_distance(points[i], points[i + 1])
        distances.append(d)
    distances = np.asarray(distances)

    # Compute the total length of the path and the length of the point
    # segments to be computed.
    total_length = distances.sum()
    length_point_segment = total_length / (numpoints + len(points) - 2)

    # If the total length of the path is zero, all given waypoints have the
    # same coordinates. Return arrays with numpoints points all having these
    # coordinate.
    if total_length == 0.:
        lons = np.repeat(points[0][LON], numpoints)
        lats = np.repeat(points[0][LAT], numpoints)
        times = np.repeat(points[0][TIME], numpoints)
        return lats, lons, times

    # For each segment, determine the number of points to be computed
    # from the distance between the two bounding points and the
    # length of the point segments. Then compute the intermediate
    # points. Cut the first point from each segment other than the
    # first segment to avoid double points.
    lons = []
    lats = []
    times = []
    for i in range(len(points) - 1):
        segment_points = int(round(distances[i] / length_point_segment))
        # Enforce that a segment consists of at least two points
        # (otherwise latlon_points will throw an exception).
        segment_points = max(segment_points, 2)
        # print segment_points
        lats_, lons_, times_ = latlon_points(
            points[i], points[i + 1],
            numpoints=segment_points, connection=connection)
        startidx = 0 if i == 0 else 1
        lons.extend(lons_[startidx:])
        lats.extend(lats_[startidx:])
        times.extend(times_[startidx:])
    return [np.asarray(_x) for _x in (lats, lons, times)]


def convert_pressure_to_vertical_axis_measure(vertical_axis, pressure):
    """
    vertical_axis can take following values
    - pressure altitude
    - flight level
    - pressure
    """
    if vertical_axis == "pressure":
        return float(pressure / 100)
    elif vertical_axis == "flight level":
        return pressure2flightlevel(pressure)
    elif vertical_axis == "pressure altitude":
        return pressure2flightlevel(pressure) / 32.8
    else:
        return pressure


class CaseInsensitiveMultiDict(werkzeug.datastructures.ImmutableMultiDict):
    """Extension to werkzeug.datastructures.ImmutableMultiDict
    that makes the MultiDict case-insensitive.

    The only overridden method is __getitem__(), which converts string keys
    to lower case before carrying out comparisons.

    See ../paste/util/multidict.py as well as
      http://stackoverflow.com/questions/2082152/case-insensitive-dictionary
    """

    def __getitem__(self, key):
        if hasattr(key, 'lower'):
            key = key.lower()
        for k, v in self.items():
            if hasattr(k, 'lower'):
                k = k.lower()
            if k == key:
                return v
        raise KeyError(repr(key))


def setup_logging(args):
    logger = logging.getLogger()
    # this is necessary as "someone" has already initialized logging, preventing basicConfig from doing stuff
    for ch in logger.handlers:
        logger.removeHandler(ch)

    debug_formatter = logging.Formatter("%(asctime)s (%(module)s.%(funcName)s:%(lineno)s): %(message)s")
    default_formatter = logging.Formatter("%(levelname)s: %(message)s")

    # Console handler (suppress DEBUG by default)
    ch = logging.StreamHandler()
    if args.debug:
        logger.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(debug_formatter)
    else:
        logger.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)
        ch.setFormatter(default_formatter)
    logger.addHandler(ch)
    # File handler (always on DEBUG level)
    # TODO: Change this to write to a rotating log handler (so that the file size
    # is kept constant). (mr, 2011-02-25)
    if args.logfile:
        logfile = args.logfile
        try:
            fh = logging.FileHandler(logfile, "w")
        except (OSError, IOError) as ex:
            logger.error("Could not open logfile '%s': %s %s", logfile, type(ex), ex)
        else:
            logger.setLevel(logging.DEBUG)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(debug_formatter)
            logger.addHandler(fh)


# modified Version from minidom, https://github.com/python/cpython/blob/2.7/Lib/xml/dom/minidom.py
# MSS needed to change all writings as unicode not str
from xml.dom.minidom import _write_data, Node
# Copyright © 2001-2018 Python Software Foundation. All rights reserved.
# Copyright © 2000 BeOpen.com. All rights reserved.


def writexml(self, writer, indent=u"", addindent=u"", newl=u""):
    # indent = current indentation
    # addindent = indentation to add to higher levels
    # newl = newline string
    writer.write(indent + u"<" + self.tagName)

    attrs = self._get_attributes()

    for a_name in sorted(attrs.keys()):
        writer.write(u" %s=\"" % a_name)
        _write_data(writer, attrs[a_name].value)
        writer.write(u"\"")
    if self.childNodes:
        writer.write(u">")
        if (len(self.childNodes) == 1 and self.childNodes[0].nodeType == Node.TEXT_NODE):
            self.childNodes[0].writexml(writer, '', '', '')
        else:
            writer.write(newl)
            for node in self.childNodes:
                node.writexml(writer, indent + addindent, addindent, newl)
            writer.write(indent)
        writer.write(u"</%s>%s" % (self.tagName, newl))
    else:
        writer.write(u"/>%s" % (newl))


def npts_cartopy(coord1, coord2, numpoints):
    distance = get_distance(coord1, coord2) / (numpoints + 1)
    new_geo = gd.Geodesic()
    all_distance = [distance * i * 1000 for i in range(1, numpoints + 1)]
    initial_azimuth = new_geo.inverse(coord1, coord2).base[0, 1]
    coords = new_geo.direct(coord1, initial_azimuth, all_distance)
    points = list(zip(coords[:, 0], coords[:, 1]))
    return points
