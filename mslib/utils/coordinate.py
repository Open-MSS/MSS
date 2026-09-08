# -*- coding: utf-8 -*-
"""

    mslib.utils.coordinate
    ~~~~~~~~~~~~~~~~~~~~~~

    Collection of functions all around coordinates, locations and positions.

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

import netCDF4 as nc
import numpy as np
from pyproj import Geod
from scipy.interpolate import interp1d
from scipy.ndimage import map_coordinates

__PR = Geod(ellps='WGS84')


def get_distance(lat0, lon0, lat1, lon1):
    """
    Computes the distance between two points on the Earth surface
    Args:
        lat0: lat of first point
        lon0: lon of first point
        lat1: lat of second point
        lon1: lon of second point

    Returns:
        length of distance in km
    """
    return __PR.inv(lon0, lat0, lon1, lat1)[-1] / 1000.


def fix_angle(ang):
    """
    Normalizes an angle between -180 and 180 degree.
    """
    while ang > 360:
        ang -= 360
    while ang < 0:
        ang += 360
    return ang


def normalize_longitude(lons, lon_min, lon_max):
    """
    normalizes longitudes to a given range.
    The delta should fix longitudes of lines going
    across the boundaries, but will fail eventually.
    This is not cleanly fixable with basemap.
    """
    lons = np.asarray(lons)
    delta = (360 - (lon_max - lon_min)) * 0.5
    lons[lons < lon_min - delta] += 360
    lons[lons > lon_max + delta] -= 360
    return lons


def rotate_point(point, angle, origin=(0, 0)):
    """Rotates a point. Angle is in degrees.
    Rotation is counter-clockwise"""
    angle = np.deg2rad(angle)
    temp_point = ((point[0] - origin[0]) * np.cos(angle) -
                  (point[1] - origin[1]) * np.sin(angle) + origin[0],
                  (point[0] - origin[0]) * np.sin(angle) +
                  (point[1] - origin[1]) * np.cos(angle) + origin[1])
    return temp_point


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
        curtain[ml, :] = map_coordinates(data3D[ml, :, :].filled(np.nan), ind_coords, order=1)

    curtain[:, np.isnan(ind_lats) | np.isnan(ind_lons)] = np.nan
    return np.ma.masked_invalid(curtain)


def latlon_points(lat0, lon0, lat1, lon1, numpoints=100, connection='linear'):
    """
    Compute intermediate points between two given points.

    Arguments:
    p1, p2 -- points given as lat/lon pairs, i.e. p1, p2 = [lat, lon]
    numpoints -- number of intermediate points to be computed aloing the path
    connection -- method to compute the intermediate points. Can be
                  'linear' or 'greatcircle'

    Returns two arrays lats, lons with intermediate latitude and longitudes.
    """
    if connection == 'linear':
        lats = np.linspace(lat0, lat1, numpoints)
        lons = np.linspace(lon0, lon1, numpoints)
    elif connection == 'greatcircle':
        if numpoints > 2:
            pts = __PR.npts(lon0, lat0, lon1, lat1, numpoints - 2)
            lats = [lat0] + [_x[1] for _x in pts] + [lat1]
            lons = [lon0] + [_x[0] for _x in pts] + [lon1]
        else:
            lats = [lat0, lat1]
            lons = [lon0, lon1]

    return lats, lons


def path_points(lats, lons, numpoints=100, times=None, alts=None, connection='linear'):
    """
    Compute intermediate points of a path given by a list of points.

    Arguments:
    lats -- list of lats
    lons -- list of lons
    numpoints -- number of intermediate points to be computed along the path
    connection -- method to compute the intermediate points. Can be
                  'linear' or 'greatcircle'

    Returns two arrays lats, lons with intermediate latitude and longitudes.
    """
    if connection not in ['linear', 'greatcircle']:
        raise RuntimeError(f"Wrong connection type '{connection}'")
    if lats is None or lons is None:
        raise RuntimeError("Blub")
    assert len(lats) == len(lons)
    if len(lats) == 0:
        if times is not None and alts is not None:
            return None, None, None, None
        if times is not None or alts is not None:
            return None, None, None
        return None, None
    if times is not None:
        assert len(lats) == len(times)
        times = nc.date2num(times, "seconds since 2000-01-01")
    if alts is not None:
        assert len(lats) == len(alts)

    # First compute the lengths of the individual path segments, i.e.
    # the distances between the points.
    if connection == 'linear':
        lats, lons = np.asarray(lats), np.asarray(lons)
        distances = np.hypot(lats[:-1] - lats[1:], lons[:-1] - lons[1:])
    else:
        distances = [
            get_distance(lats[i], lons[i], lats[i + 1], lons[i + 1])
            for i in range(len(lats) - 1)]

    # Compute the total length of the path and the length of the point
    # segments to be computed.
    total_length = sum(distances)
    length_point_segment = total_length / (numpoints + len(lats) - 2)

    # If the total length of the path is zero, all given waypoints have the
    # same coordinates. Return arrays with numpoints points all having these
    # coordinate.
    if total_length == 0.:
        result = [np.repeat(lats[0], numpoints), np.repeat(lons[0], numpoints)]
        if times is not None:
            result.append(nc.num2date(np.repeat(times[0], numpoints), "seconds since 2000-01-01"))
        if alts is not None:
            result.append(np.repeat(alts[0], numpoints))
        return result

    # For each segment, determine the number of points to be computed
    # from the distance between the two bounding points and the
    # length of the point segments. Then compute the intermediate
    # points. Cut the first point from each segment other than the
    # first segment to avoid double points.
    r_lats, r_lons, r_times, r_alts = [], [], [], []
    startidx = 0
    for i in range(len(lats) - 1):
        segment_points = int(round(distances[i] / length_point_segment))
        # Enforce that a segment consists of at least two points
        # (otherwise latlon_points will throw an exception).
        segment_points = max(segment_points, 2)
        lats_, lons_ = latlon_points(
            lats[i], lons[i], lats[i + 1], lons[i + 1],
            numpoints=segment_points, connection=connection)
        r_lons.extend(lons_[startidx:])
        r_lats.extend(lats_[startidx:])
        if times is not None:
            r_times.extend(np.linspace(times[i], times[i + 1], segment_points)[startidx:])
        if alts is not None:
            r_alts.extend(np.linspace(alts[i], alts[i + 1], segment_points)[startidx:])
        startidx = 1

    result = [r_lats, r_lons]
    if times is not None:
        result.append(nc.num2date(r_times, "seconds since 2000-01-01"))
    if alts is not None:
        result.append(r_alts)
    return result
