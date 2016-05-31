"""Collection of utility routines for the Mission Support System.

********************************************************************************

   Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

********************************************************************************

AUTHORS:
========

* Marc Rautenhaus (mr)

"""

# standard library imports
import collections
import datetime
from datetime import datetime as dt

# related third party imports
import numpy as np
from scipy.interpolate import RectBivariateSpline, UnivariateSpline, interp1d
from scipy.ndimage import map_coordinates
from mslib import greatcircle
from geopy import distance

# local application imports

###############################################################################
###             Tangent point / Hexagon / Solar Angle utilities             ###
###############################################################################

JSEC_START = datetime.datetime(2000, 1, 1)
R = 6371.
F = 1. / 298.257223563
E2 = (2. - F) * F


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


def computeHourOfDay(jsecs):
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


def compute_view_angles(lon0, lat0, h0, lon1, lat1, h1):
    mlat = (lat0 + lat1) / 2.
    lon0 *= np.cos(np.deg2rad(mlat))
    lon1 *= np.cos(np.deg2rad(mlat))
    dlon = lon1 - lon0
    dlat = lat1 - lat0
    obs_azi2 = fix_angle(90 + np.rad2deg(np.arctan2(dlon, dlat)))
    return obs_azi2, -1


def calc_view_rating(obs_azi, obs_ele, sol_azi, sol_ele, height):
    thresh = -np.rad2deg(np.arccos(R / (height + R))) - 3

    delta_azi = obs_azi - sol_azi
    delta_ele = obs_ele + sol_ele
    if sol_ele < thresh:
        delta_ele = 180
    return np.linalg.norm([delta_azi, delta_ele])


def compute_solar_angle(jsec, lon, lat):
    # The input to the Astronomer's almanach is the difference between
    # the Julian date and JD 2451545.0 (noon, 1 January 2000)
    time = jsec / (60. * 60. * 24.) - 0.5

    # Mean longitude
    mnlong = 280.460 + .9856474 * time
    mnlong %= 360.
    if mnlong < 0:
        mnlong += 360
        assert mnlong >= 0

    # Mean anomaly
    mnanom = 357.528 + .9856003 * time
    mnanom = np.deg2rad(mnanom % 360.)
    if mnanom < 0:
        mnanom += 2 * np.pi
        assert mnanom >= 0

    # Ecliptic longitude and obliquity of ecliptic
    eclong = mnlong + 1.915 * np.sin(mnanom) + 0.020 * np.sin(2 * mnanom)
    eclong = np.deg2rad(eclong % 360.)
    if (eclong < 0):
        eclong += 2 * np.pi
        assert(eclong >= 0)

    oblqec = np.deg2rad(23.439 - 0.0000004 * time)

    # Celestial coordinates
    # Right ascension and declination
    num = np.cos(oblqec) * np.sin(eclong)
    den = np.cos(eclong)
    ra = np.arctan(num / den)
    if den < 0:
        ra += np.pi
    elif den >= 0 and num < 0:
        ra += 2 * np.pi

    dec = np.arcsin(np.sin(oblqec) * np.sin(eclong))
    # Local coordinates
    # Greenwich mean sidereal time
    gmst = 6.697375 + .0657098242 * time + computeHourOfDay(jsec)

    gmst = gmst % 24.
    if gmst < 0:
        gmst += 24
        assert gmst >= 0

    # Local mean sidereal time
    if lon < 0:
        lon += 360
        assert 0 <= lon <= 360

    lmst = gmst + lon / 15.
    lmst = np.deg2rad(15. * (lmst % 24.))

    # Hour angle
    ha = lmst - ra;
    if ha < -np.pi:
        ha += 2 * np.pi

    if ha > np.pi:
        ha -= 2 * np.pi

    assert -np.pi < ha < 2 * np.pi

    # Latitude to radians
    lat = np.deg2rad(lat)

    # Azimuth and elevation
    zenithAngle = np.arccos(np.sin(lat) * np.sin(dec) + np.cos(lat) * np.cos(dec) * np.cos(ha))
    azimuthAngle = np.arccos((np.sin(lat) * np.cos(zenithAngle) - np.sin(dec)) /
                      (np.cos(lat) * np.sin(zenithAngle)))

    if ha > 0:
        azimuthAngle += np.pi
    else:
        azimuthAngle = 3 * np.pi - azimuthAngle % (2 * np.pi)

    if azimuthAngle > np.pi:
        azimuthAngle -= 2 * np.pi

    return np.rad2deg(azimuthAngle), 90 - np.rad2deg(zenithAngle)


def rotatePoint(point, angle, origin=(0, 0)):
    """Rotates a point. Angle is in degrees.
    Rotation is counter-clockwise"""
    angle = np.deg2rad(angle)
    temp_point = ((point[0] - origin[0]) * np.cos(angle) -
                  (point[1] - origin[1]) * np.sin(angle) + origin[0],
                  (point[0] - origin[0]) * np.sin(angle) +
                  (point[1] - origin[1]) * np.cos(angle) + origin[1])
    return temp_point


def createHexagon(center_lat, center_lon, radius, angle=0.):
    coords_0 = (radius, 0.)
    CoordsCart_0 = [rotatePoint(coords_0, angle=0. + angle),
                    rotatePoint(coords_0, angle=60. + angle),
                    rotatePoint(coords_0, angle=120. + angle),
                    rotatePoint(coords_0, angle=180. + angle),
                    rotatePoint(coords_0, angle=240. + angle),
                    rotatePoint(coords_0, angle=300. + angle),
                    rotatePoint(coords_0, angle=360. + angle)]
    CoordsSphere_rot = [(center_lat + vec[0] / 110.,
                         center_lon + vec[1] / (110. *
                         np.cos(np.deg2rad(vec[0] / 110. + center_lat))))
                         for vec in CoordsCart_0]
    return CoordsSphere_rot


def convertHPAToKM(press):
    return (288.15 / 0.0065) * (1. - (press / 1013.25)**(1. / 5.255)) / 1000.


def tangent_point_coordinates(lon_lin, lat_lin, flight_alt=14, cut_height=12):
    lon_lin2 = np.array(lon_lin)*np.cos(np.deg2rad(np.array(lat_lin)))
    lins = zip(lon_lin2[0:-1], lon_lin2[1:], lat_lin[0:-1], lat_lin[1:])
    direction = [(x1 - x0, y1 - y0) for x0, x1, y0, y1 in lins]
    direction = [(_x/np.hypot(_x,_y), _y/np.hypot(_x,_y))
                 for _x, _y in direction]
    los = [rotatePoint(point,-90.) for point in direction]
    los.append(los[-1])

    if isinstance(flight_alt, (collections.Sequence, np.ndarray)):
        dist = [np.sqrt(max((R + a) ** 2 - (R + cut_height) ** 2, 0)) / 110. for a in flight_alt[:-1]]
        dist.append(dist[-1])
    else:
        dist = np.sqrt((R + flight_alt) ** 2 - (R + cut_height) ** 2) / 110.

    tp_dir = (np.array(los).T * dist).T

    tps = [(x0 + tp_x, y0 + tp_y) for
           ((x0, x1, y0, y1), (tp_x, tp_y)) in zip(lins, tp_dir)]
    tps = [(x0 / np.cos(np.deg2rad(y0)), y0) for
            (x0, y0) in tps]
    return tps


###############################################################################
###         Utility functions for interpolating vertical sections.          ###
###############################################################################

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
    #print data3D_lats, data3D_lons, lats, lons, ind_lats, ind_lons
    
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
    #print data3D_lats, lats, ind_lats  
    interp_lon = interp1d(data3D_lons, np.arange(len(data3D_lons)), bounds_error=False)
    ind_lons = interp_lon(lons)
    #print data3D_lons, lons, ind_lons
    ind_coords = np.array([ind_lats, ind_lons])
    
    # One horizontal interpolation for each model level. The order
    # parameter controls the degree of the splines used, i.e. order=1
    # stands for linear interpolation.
    for ml in range(data3D.shape[0]):
        data = data3D[ml, :, :]
        curtain[ml, :] = map_coordinates(data, ind_coords, order=1)

    return curtain


def latlon_points(p1, p2, numpoints=100, connection='linear'):
    """Compute intermediate points between two given points.

    Arguments:
    p1, p2 -- points given as lat/lon pairs, i.e. p1, p2 = [lat, lon]
    numpoints -- number of intermediate points to be computed aloing the path
    connection -- method to compute the intermediate points. Can be
                  'linear' or 'greatcircle'

    Returns two arrays lats, lons with intermediate latitude and longitudes.
    """
    LAT = 0; LON = 1
    if connection == 'linear':
        if p2[LAT]-p1[LAT] == 0:
            lats = np.ones(numpoints) * p1[LAT]
        else:
            lat_step = float(p2[LAT]-p1[LAT])/(numpoints-1)
            lats = np.arange(p1[LAT], p2[LAT]+lat_step/2, lat_step)
        if p2[LON]-p1[LON] == 0:
            lons = np.ones(numpoints) * p1[LON]
        else:
            lon_step = float(p2[LON]-p1[LON])/(numpoints-1)
            lons = np.arange(p1[LON], p2[LON]+lon_step/2, lon_step)
        return lats, lons
    elif connection == 'greatcircle':
        # Compute great circle points using the WGS84 ellipsoid. Compare to
        # the comments in greatcircle.py.
        a = 6378137.0
        b = 6356752.3142
        gc = greatcircle.GreatCircle(a, b, p1[LON], p1[LAT], p2[LON], p2[LAT])
        lons, lats = gc.points(numpoints)
        return np.array(lats), np.array(lons)
    else:
        return None, None


def path_points(points, numpoints=100, connection='linear'):
    """Compute intermediate points of a path given by a list of points.

    Arguments:
    points -- list of lat/lon pairs, i.e. [[lat1,lon1], [lat2,lon2], ...]
    numpoints -- number of intermediate points to be computed along the path
    connection -- method to compute the intermediate points. Can be
                  'linear' or 'greatcircle'

    Returns two arrays lats, lons with intermediate latitude and longitudes.
    """
    if connection not in ['linear', 'greatcircle']:
        return None, None
    LAT = 0; LON = 1

    # First compute the lengths of the individual path segments, i.e.
    # the distances between the points.
    distances = []
    for i in range(len(points)-1):
        if connection == 'linear':
            # Use Euclidean distance in lat/lon space.
            d = np.sqrt((points[i][LAT] - points[i+1][LAT])**2 +
                        (points[i][LON] - points[i+1][LON])**2)
        elif connection == 'greatcircle':
            # Use Vincenty distance provided by the geopy module.
            d = distance.distance(points[i], points[i+1]).km
        distances.append(d)
    distances = np.array(distances)

    # Compute the total length of the path and the length of the point
    # segments to be computed.
    total_length = distances.sum()
    length_point_segment = total_length/(numpoints + len(points) - 2)
    #print points
    #print distances, total_length, length_point_segment

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
    for i in range(len(points)-1):
        segment_points = int(round(distances[i] / length_point_segment))
        # Enforce that a segment consists of at least two points
        # (otherwise latlon_points will throw an exception).
        segment_points = max(segment_points, 2)
        #print segment_points
        lats_, lons_ = latlon_points(points[i], points[i+1],
                                     numpoints=segment_points,
                                     connection=connection)
        if i == 0:
            lons.extend(lons_)
            lats.extend(lats_)
        else:
            lons.extend(lons_[1:])
            lats.extend(lats_[1:])
    lons = np.array(lons)
    lats = np.array(lats)
    return lats, lons



###############################################################################
###                     Satellite Track Predictions                         ###
###############################################################################


def read_nasa_satellite_prediction(fname):
    """Read a text file as downloaded from the NASA satellite prediction tool.

    This method reads satellite overpass predictions in ASCII format as
    downloaded from http://www-air.larc.nasa.gov/tools/predict.htm.

    Returns a list of dictionaries with keys
      -- utc: Nx1 array with utc times as datetime objects
      -- satpos: Nx2 array with lon/lat (x/y) of satellite positions
      -- heading: Nx1 array with satellite headings in degrees
      -- swath_left: Nx2 array with lon/lat of left swath boundary
      -- swath_right: Nx2 array with lon/lat of right swath boundary
    Each dictionary represents a separate overpass.

    All arrays are masked arrays, note that missing values are common. Filter
    out missing values with numpy.ma.compress_rows().

    NOTE: ****** LON in the 'predict' files seems to be wrong --> needs to be
                 multiplied by -1. ******
    """
    # Read the file into a list of strings.
    satfile = open(fname, 'r')
    satlines = satfile.readlines()
    satfile.close()

    # Determine the date from the first line.
    date = dt.strptime(satlines[0].split()[0], "%Y/%m/%d")
    basedate = dt.strptime("", "")

    # "result" will store the individual overpass segments.
    result = []
    segment = {"utc": [], "satpos": [], "heading": [],
               "swath_left": [], "swath_right": []}

    # Define a time difference that specifies when to start a new segment.
    # If the time between to subsequent points in the file is larger than
    # this time, a new segment will be started.
    seg_diff_time = datetime.timedelta(minutes=10)

    # Loop over data lines. Either append point to current segment or start
    # new segment. Before storing segments to the "result" list, convert
    # to masked arrays.
    for line in satlines[2:]:
        values = line.split()
        time = date+(dt.strptime(values[0], "%H:%M:%S")-basedate)

        if len(segment["utc"]) == 0 or (time-segment["utc"][-1]) < seg_diff_time:
            segment["utc"].append(time)
            segment["satpos"].append([-1.*float(values[2]), float(values[1])])
            segment["heading"].append(float(values[3]))
            if len(values) == 8:
                segment["swath_left"].append([-1.*float(values[5]), float(values[4])])
                segment["swath_right"].append([-1.*float(values[7]), float(values[6])])
            else:
#TODO 20100504: workaround for instruments without swath                
                segment["swath_left"].append([-1.*float(values[2]), float(values[1])])
                segment["swath_right"].append([-1.*float(values[2]), float(values[1])])
                
                
        else:
            segment["utc"] = np.array(segment["utc"])
            segment["satpos"] = np.ma.masked_equal(segment["satpos"], -999.)
            segment["heading"] = np.ma.masked_equal(segment["heading"], -999.)
            segment["swath_left"] = np.ma.masked_equal(segment["swath_left"], -999.)
            segment["swath_right"] = np.ma.masked_equal(segment["swath_right"], -999.)
            result.append(segment)
            segment = {"utc": [], "satpos": [], "heading": [],
                       "swath_left": [], "swath_right": []}

    return result

