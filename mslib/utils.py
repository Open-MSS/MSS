# -*- coding: utf-8 -*-
"""

    mslib.mss_util
    ~~~~~~~~~~~~~~

    Collection of utility routines for the Mission Support System.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2017 by the mss team, see AUTHORS.
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
import json
import logging
import os
import pickle

import numpy as np
import paste.util.multidict
from scipy.interpolate import RectBivariateSpline, interp1d
from scipy.ndimage import map_coordinates

try:
    import mpl_toolkits.basemap.pyproj as pyproj
except ImportError:
    import pyproj

from mslib.msui import constants


class FatalUserError(Exception):
    pass


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
    try:
        with open(os.path.join(config_file)) as source:
            data = json.load(source)
    except (AttributeError, IOError, TypeError), ex:
        logging.error(u"MSS config File error '{:}' - '{:}' - '{:}'".format(config_file, type(ex), ex))
        if default is not None:
            return default
        raise IOError("MSS config File not found")
    except ValueError, ex:
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
    pr = pyproj.Geod(ellps='WGS84')
    return pr.inv(coord0[1], coord0[0], coord1[1], coord1[0])[-1] / 1000.


def save_settings_pickle(tag, settings):
    """
    Saves a dictionary settings to disk.

    :param tag: string specifying the settings
    :param settings: dictionary of settings
    :return: None
    """
    assert isinstance(tag, basestring)
    assert isinstance(settings, dict)
    settingsfile = os.path.join(constants.MSS_CONFIG_PATH, "mss.{}.cfg".format(tag))
    logging.debug("storing settings for %s to %s", tag, settingsfile)
    try:
        with open(settingsfile, "w") as fileobj:
            pickle.dump(settings, fileobj)
    except (OSError, IOError), ex:
        logging.warn("Problems storing %s settings (%s: %s).", tag, type(ex), ex)


def load_settings_pickle(tag, default_settings=None):
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
    settingsfile = os.path.join(constants.MSS_CONFIG_PATH, "mss.{}.cfg".format(tag))
    logging.debug("loading settings for %s from %s", tag, settingsfile)
    try:
        with open(settingsfile, "r") as fileobj:
            settings = pickle.load(fileobj)
    except (pickle.UnpicklingError, KeyError, OSError, IOError, ImportError), ex:
        logging.warn("Problems reloading stored %s settings (%s: %s). Switching to default",
                     tag, type(ex), ex)
        settings = {}
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
    return date.hour + date.minute / 60. + date.second / 3600.


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


def get_projection_params(epsg):
    if epsg.startswith("EPSG:"):
        epsg = epsg[5:]
    proj_params = None
    if epsg == "4326":
        proj_params = {"basemap": {"projection": "cyl"}, "bbox": "latlon"}
    elif epsg == "9810":
        proj_params = {"basemap": {"projection": "stere", "lat_0": 90.0, "lon_0": 0.0}, "bbox": "metres"}
    elif epsg.startswith("777") and len(epsg) == 8:
        lat_0, lon_0 = int(epsg[3:5]), int(epsg[5:])
        proj_params = {"basemap": {"projection": "stere", "lat_0": lat_0, "lon_0": lon_0}, "bbox": "latlon"}
    elif epsg.startswith("778") and len(epsg) == 8:
        lat_0, lon_0 = int(epsg[3:5]), int(epsg[5:])
        proj_params = {"basemap": {"projection": "stere", "lat_0": -lat_0, "lon_0": lon_0}, "bbox": "latlon"}
    return proj_params


def interpolate_vertsec(data3D, data3D_lats, data3D_lons, lats, lons):
    """
    Interpolate curtain[z,pos] (curtain[level,pos]) from data3D[z,y,x]
    (data3D[level,lat,lon]).

    This method is based on scipy.interpolate.RectBivariateSpline().

    data3D has to be on a regular lat/lon grid, coordinates given by lats, lons.
    lats, lons have to be strictly INCREASING, they do not have to be uniform,
    though.
    """
    # Create an empty field to accomodate the curtain.
    curtain = np.zeros([data3D.shape[0], len(lats)])

    # One horizontal interpolation for each model level.
    for ml in range(data3D.shape[0]):
        data = data3D[ml, :, :]
        # Initialise a SciPy interpolation object. RectBivariateSpline is the
        # only class that can handle 2D input fields.
        interpolator = RectBivariateSpline(data3D_lats,
                                           data3D_lons,
                                           data, kx=1, ky=1)
        # RectBivariateSpline returns a full mesh of lat/lon interpolated
        # values.. use diagonal to only get the values at lat/lon pairs.
        curtain[ml, :] = interpolator(lats, lons).diagonal()

    return curtain


def interpolate_vertsec2(data3D, data3D_lats, data3D_lons, lats, lons):
    """
    Interpolate curtain[z,pos] (curtain[level,pos]) from data3D[z,y,x]
    (data3D[level,lat,lon]).

    This method is based on scipy.ndimage.map_coordinates().

    data3D has to be on a regular lat/lon grid, coordinates given by lats, lons.
    The lats, lons arrays can have arbitrary order, they do not have to be uniform.
    """
    # Create an empty field to accomodate the curtain.
    curtain = np.zeros([data3D.shape[0], len(lats)])

    # Transform lat/lon values to array index space. This is necessary to use
    # scipy.ndimage.map_coordinates(). See the comments on
    #      http://old.nabble.com/2D-Interpolation-td18161034.html
    # (2D Interpolation; Ryan May Jun 27, 2008) and the examples on
    #      http://www.scipy.org/Cookbook/Interpolation
    dlat = data3D_lats[1] - data3D_lats[0]
    dlon = data3D_lons[1] - data3D_lons[0]
    ind_lats = (lats - data3D_lats[0]) / dlat
    ind_lons = (lons - data3D_lons[0]) / dlon
    ind_coords = np.array([ind_lats, ind_lons])

    # One horizontal interpolation for each model level. The order
    # parameter controls the degree of the splines used, i.e. order=1
    # stands for linear interpolation.
    for ml in range(data3D.shape[0]):
        data = data3D[ml, :, :]
        curtain[ml, :] = map_coordinates(data, ind_coords, order=1)

    return curtain


def interpolate_vertsec3(data3D, data3D_lats, data3D_lons, lats, lons):
    """
    Interpolate curtain[z,pos] (curtain[level,pos]) from data3D[z,y,x]
    (data3D[level,lat,lon]).

    This method is based on scipy.ndimage.map_coordinates().

    data3D can be on an IRREGULAR lat/lon grid, coordinates given by lats, lons.
    The lats, lons arrays can have arbitrary order, they do not have to be uniform.
    """
    # Create an empty field to accomodate the curtain.
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
    if connection == 'linear':
        if p2[LAT] - p1[LAT] == 0:
            lats = np.ones(numpoints) * p1[LAT]
        else:
            lat_step = float(p2[LAT] - p1[LAT]) / (numpoints - 1)
            lats = np.arange(p1[LAT], p2[LAT] + lat_step / 2, lat_step)
        if p2[LON] - p1[LON] == 0:
            lons = np.ones(numpoints) * p1[LON]
        else:
            lon_step = float(p2[LON] - p1[LON]) / (numpoints - 1)
            lons = np.arange(p1[LON], p2[LON] + lon_step / 2, lon_step)
        return lats, lons
    elif connection == 'greatcircle':
        gc = pyproj.Geod(ellps="WGS84")
        pts = gc.npts(p1[LON], p1[LAT], p2[LON], p2[LAT], numpoints)
        return (np.asarray([p1[LAT]] + [_x[1] for _x in pts] + [p2[LAT]]),
                np.asarray([p1[LON]] + [_x[0] for _x in pts] + [p2[LON]]))
    else:
        return None, None


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
        lons = np.ones(numpoints) * points[0][LON]
        lats = np.ones(numpoints) * points[0][LAT]
        return lats, lons

    # For each segment, determine the number of points to be computed
    # from the distance between the two bounding points and the
    # length of the point segments. Then compute the intermediate
    # points. Cut the first point from each segment other than the
    # first segment to avoid double points.
    lons = []
    lats = []
    for i in range(len(points) - 1):
        segment_points = int(round(distances[i] / length_point_segment))
        # Enforce that a segment consists of at least two points
        # (otherwise latlon_points will throw an exception).
        segment_points = max(segment_points, 2)
        # print segment_points
        lats_, lons_ = latlon_points(points[i], points[i + 1],
                                     numpoints=segment_points,
                                     connection=connection)
        if i == 0:
            lons.extend(lons_)
            lats.extend(lats_)
        else:
            lons.extend(lons_[1:])
            lats.extend(lats_[1:])
    lons = np.asarray(lons)
    lats = np.asarray(lats)
    return lats, lons


class CaseInsensitiveMultiDict(paste.util.multidict.MultiDict):
    """Extension to paste.util.multidict.MultiDict that makes the MultiDict
       case-insensitive.

    The only overridden method is __getitem__(), which converts string keys
    to lower case before carrying out comparisons.

    See ../paste/util/multidict.py as well as
      http://stackoverflow.com/questions/2082152/case-insensitive-dictionary
    """

    def __getitem__(self, key):
        if hasattr(key, 'lower'):
            key = key.lower()
        for k, v in self._items:
            if hasattr(k, 'lower'):
                k = k.lower()
            if k == key:
                return v
        raise KeyError(repr(key))
