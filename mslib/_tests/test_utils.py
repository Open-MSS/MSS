# -*- coding: utf-8 -*-
"""

    mslib._tests.test_utils
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mslib.mss_util

    This file is part of mss.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2020 by the mss team, see AUTHORS.
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
import pytest
import os
import datetime
from mslib import utils
import multidict
import werkzeug
from mslib.utils import get_projection_params as get_proj
import pyproj
import numpy


class TestParseTime(object):
    def test_parse_iso_datetime(self):
        assert utils.parse_iso_datetime("2009-05-28T16:15:00") == datetime.datetime(2009, 5, 28, 16, 15)

    def test_parse_iso_duration(self):
        assert utils.parse_iso_duration('P01W') == datetime.timedelta(days=7)


class TestSettingsSave(object):
    """
    tests save_settings_qsettings and load_settings_qsettings from ./utils.py
    # TODO make sure do a clean setup, not inside the 'mss' config file.
    """
    tag = "test_automated"

    def test_save_settings(self):
        settings = {'foo': 'bar'}
        utils.save_settings_qsettings(self.tag, settings)

    def test_load_settings(self):
        settings = utils.load_settings_qsettings(self.tag)
        assert isinstance(settings, dict)
        assert settings["foo"] == "bar"


class TestConfigLoader(object):
    """
    tests config file for client
    """

    def test_default_config(self):
        data = utils.config_loader()
        assert isinstance(data, dict)
        assert data["num_labels"] == 10
        assert data["num_interpolation_points"] == 201

    def test_default_config_dataset(self):
        data = utils.config_loader(dataset="num_labels")
        assert data == 10
        # defined value and not a default one
        data = utils.config_loader(dataset="num_labels", default=5)
        assert data == 10
        # default for non existing entry
        data = utils.config_loader(dataset="foobar", default=5)
        assert data == 5

    def test_default_config_wrong_file(self):
        # return default if no access to config file given
        data = utils.config_loader(config_file="foo.json", default={"foo": "123"})
        assert data == {"foo": "123"}

    def test_sample_config_file(self):
        utils_path = os.path.dirname(os.path.abspath(utils.__file__))
        config_file = os.path.join(utils_path, '../', 'docs', 'samples', 'config', 'mss', 'mss_settings.json.sample')
        data = utils.config_loader(config_file=config_file, dataset="new_flighttrack_flightlevel")
        assert data == 250
        with pytest.raises(KeyError):
            utils.config_loader(config_file=config_file, dataset="UNDEFINED")
        assert utils.config_loader(config_file=config_file, dataset="UNDEFINED", default=9) == 9
        with pytest.raises(IOError):
            config_file = os.path.join(utils_path, '../', 'docs', 'samples', 'config', 'mss',
                                       'not_existing_mss_settings.json.sample')
            _ = utils.config_loader(config_file=config_file)


class TestGetDistance(object):
    """
    tests for distance based calculations
    """
    # we don't test the utils method here, may be that method should me refactored off

    def test_get_distance(self):
        coordinates_distance = [((50.355136, 7.566077), (50.353968, 4.577915), 212),
                                ((-5.135943, -42.792442), (4.606085, 120.028077), 18130)]
        for coord1, coord2, distance in coordinates_distance:
            assert int(utils.get_distance(coord1, coord2)) == distance

    def test_find_location(self):
        assert utils.find_location(50.92, 6.36) == ((50.92, 6.36), 'Juelich')
        assert utils.find_location(50.9200002, 6.36) == ((50.92, 6.36), 'Juelich')


class TestProjections(object):
    def test_get_projection_params(self):
        assert utils.get_projection_params("epsg:4839") == {'basemap': {'epsg': '4839'}, 'bbox': 'meter(10.5,51)'}
        with pytest.raises(ValueError):
            utils.get_projection_params('auto2:42005')
        with pytest.raises(ValueError):
            utils.get_projection_params('auto:42001')
        with pytest.raises(ValueError):
            utils.get_projection_params('crs:84')


class TestTimes(object):
    """
    tests about times
    """

    def test_datetime_to_jsec(self):
        assert utils.datetime_to_jsec(datetime.datetime(2000, 2, 1, 0, 0, 0, 0)) == 2678400.0
        assert utils.datetime_to_jsec(datetime.datetime(2000, 1, 1, 0, 0, 0, 0)) == 0
        assert utils.datetime_to_jsec(datetime.datetime(1995, 1, 1, 0, 0, 0, 0)) == -157766400.0

    def test_jsec_to_datetime(self):
        assert utils.jsec_to_datetime(0) == datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
        assert utils.jsec_to_datetime(3600) == datetime.datetime(2000, 1, 1, 1, 0, 0, 0)
        assert utils.jsec_to_datetime(-157766400.0) == datetime.datetime(1995, 1, 1, 0, 0, 0, 0)

    def test_compute_hour_of_day(self):
        assert utils.compute_hour_of_day(0) == 0
        assert utils.compute_hour_of_day(86400) == 0
        assert utils.compute_hour_of_day(3600) == 1
        assert utils.compute_hour_of_day(82800) == 23


class TestAngles(object):
    """
    tests about angles
    """

    def test_normalize_angle(self):
        assert utils.fix_angle(0) == 0
        assert utils.fix_angle(180) == 180
        assert utils.fix_angle(270) == 270
        assert utils.fix_angle(-90) == 270
        assert utils.fix_angle(-180) == 180
        assert utils.fix_angle(-181) == 179
        assert utils.fix_angle(420) == 60

    def test_rotate_point(self):
        assert utils.rotate_point([0, 0], 0) == (0.0, 0.0)
        assert utils.rotate_point([0, 0], 180) == (0.0, 0.0)
        assert utils.rotate_point([1, 0], 0) == (1.0, 0.0)
        assert utils.rotate_point([100, 90], 90) == (-90, 100)


class TestConverter(object):
    def test_convert_pressure_to_altitude(self):
        assert utils.convertHPAToKM(1013.25) == 0
        assert int(utils.convertHPAToKM(25) * 1000) == 22415

    def test_convert_pressure_to_vertical_axis_measure(self):
        assert utils.convert_pressure_to_vertical_axis_measure('pressure', 10000) == 100
        assert utils.convert_pressure_to_vertical_axis_measure('flightlevel', 400) == 400
        assert utils.convert_pressure_to_vertical_axis_measure('pressure altitude', 75000) == 2.4668986099864068


class TestLatLonPoints(object):
    def test_linear(self):
        ref_times = [datetime.datetime(2012, 7, 12, 10, 30), datetime.datetime(2012, 7, 12, 10, 35)]
        ref_lats = [0, 10]
        ref_lons = [0, 0]

        lats, lons, times = utils.latlon_points([ref_lats[0], ref_lons[0], ref_times[0]],
                                                [ref_lats[1], ref_lons[1], ref_times[1]],
                                                numpoints=2, connection="linear")
        assert len(lats) == len(ref_lats)
        assert all(lats == ref_lats)
        assert len(lons) == len(ref_lons)
        assert all(lons == ref_lons)
        assert len(times) == len(ref_times)
        assert all(times == ref_times)

        lats, lons, times = utils.latlon_points([ref_lats[0], ref_lons[0], ref_times[0]],
                                                [ref_lats[1], ref_lons[1], ref_times[1]],
                                                numpoints=3, connection="linear")
        assert len(lats) == 3
        assert len(lons) == 3
        assert len(times) == 3
        assert all(lats == [0, 5, 10])

        ref_lats = [0, 0]
        ref_lons = [0, 10]
        lats, lons, times = utils.latlon_points([ref_lats[0], ref_lons[0], ref_times[0]],
                                                [ref_lats[1], ref_lons[1], ref_times[1]],
                                                numpoints=3, connection="linear")
        assert len(lats) == 3
        assert len(lons) == 3
        assert len(times) == 3
        assert all(lons == [0, 5, 10])
        assert times[1] - times[0] == times[2] - times[1]

        ref_times = [datetime.datetime(2012, 7, 12, 10, 30), datetime.datetime(2012, 7, 12, 10, 30)]
        lats, lons, times = utils.latlon_points([ref_lats[0], ref_lons[0], ref_times[0]],
                                                [ref_lats[1], ref_lons[1], ref_times[1]],
                                                numpoints=3, connection="linear")
        assert len(lats) == 3
        assert len(lons) == 3
        assert len(times) == 3
        assert all(lons == [0, 5, 10])
        assert times[0] == times[1]
        assert times[1] == times[2]

    def test_greatcircle(self):
        ref_times = [datetime.datetime(2012, 7, 12, 10, 30), datetime.datetime(2012, 7, 12, 10, 35)]
        ref_lats = [0, 10]
        ref_lons = [0, 0]

        lats, lons, times = utils.latlon_points([ref_lats[0], ref_lons[0], ref_times[0]],
                                                [ref_lats[1], ref_lons[1], ref_times[1]],
                                                numpoints=2, connection="greatcircle")
        assert len(lats) == len(ref_lats)
        assert all(lats == ref_lats)
        assert len(lons) == len(ref_lons)
        assert all(lons == ref_lons)
        assert len(times) == len(ref_times)
        assert all(times == ref_times)

        lats, lons, times = utils.latlon_points([ref_lats[0], ref_lons[0], ref_times[0]],
                                                [ref_lats[1], ref_lons[1], ref_times[1]],
                                                numpoints=3, connection="linear")
        assert len(lats) == 3
        assert len(lons) == 3
        assert len(times) == 3
        assert all(lats == [0, 5, 10])

        ref_lats = [0, 0]
        ref_lons = [0, 10]
        lats, lons, times = utils.latlon_points([ref_lats[0], ref_lons[0], ref_times[0]],
                                                [ref_lats[1], ref_lons[1], ref_times[1]],
                                                numpoints=3, connection="linear")
        assert len(lats) == 3
        assert len(lons) == 3
        assert len(times) == 3
        assert all(lons == [0, 5, 10])
        assert(times[1] - times[0] == times[2] - times[1])

    def test_ntps_cartopy(self):
        boston = [42. + (15. / 60.), -71. - (7. / 60.)]
        portland = [45. + (31. / 60.), -123. - (41. / 60.)]
        gc = pyproj.Geod(ellps="WGS84")
        pts_pyproj = gc.npts(boston[0], boston[1], portland[0], portland[1], 10)
        pts_cartopy = utils.npts_cartopy((boston[1], boston[0]), (portland[1], portland[0]), 10)
        pts_pyproj = numpy.around(pts_pyproj, 2)
        pts_cartopy = numpy.around(pts_cartopy, 2)
        assert pts_cartopy.all() == pts_pyproj.all()


def test_pathpoints():
    p1 = [0, 0, datetime.datetime(2012, 7, 1, 10, 30)]
    p2 = [10, 10, datetime.datetime(2012, 7, 1, 10, 40)]
    p3 = [-20, 20, datetime.datetime(2012, 7, 1, 10, 40)]

    result = utils.path_points([p1, p1], 100, "linear")
    assert all(len(_x) == 100 for _x in result)
    assert all(result[i][0] == p1[i] for i in range(3))
    assert all(result[i][-1] == p1[i] for i in range(3))

    result = utils.path_points([p1, p1], 100, "greatcircle")
    assert all(len(_x) == 100 for _x in result)
    assert all(result[i][0] == p1[i] for i in range(3))
    assert all(result[i][-1] == p1[i] for i in range(3))

    result = utils.path_points([p1, p2], 200, "linear")
    assert all(len(_x) == 200 for _x in result)
    assert all(result[i][0] == p1[i] for i in range(3))
    assert all(result[i][-1] == p2[i] for i in range(3))

    result = utils.path_points([p1, p2], 200, "greatcircle")
    assert all(len(_x) == 200 for _x in result)
    assert all(result[i][0] == p1[i] for i in range(3))
    assert all(result[i][-1] == p2[i] for i in range(3))

    result = utils.path_points([p1, p2, p3], 100, "linear")
    assert all(len(_x) == 100 for _x in result)
    assert all(result[i][0] == p1[i] for i in range(3))
    assert all(result[i][-1] == p3[i] for i in range(3))

    result = utils.path_points([p1, p2, p3], 100, "greatcircle")
    assert all(len(_x) == 100 for _x in result)
    assert all(result[i][0] == p1[i] for i in range(3))
    assert all(result[i][-1] == p3[i] for i in range(3))


class TestCIMultiDict(object):

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

    def test_multidict(object):
        dict = TestCIMultiDict.CaseInsensitiveMultiDict([('title', 'MSS')])
        dict_multidict = multidict.CIMultiDict([('title', 'MSS')])
        assert 'title' in dict_multidict
        assert 'tiTLE' in dict_multidict
        assert dict_multidict['Title'] == dict['tITLE']


def test_get_projection_params():
    epsg_stere = [2036, 2171, 2172, 2173, 2174, 2200, 2290, 2291, 2292,
                  2953, 2954, 2985, 2986, 3031, 3032, 3120, 3275, 3276,
                  3277, 3278, 3279, 3280, 3281, 3282, 3283, 3284, 3285,
                  3286, 3287, 3288, 3289, 3290, 3291, 3292, 3293, 3328,
                  3411, 3412, 3413, 3844, 3995, 3996, 7415, 22780, 28991,
                  28992, 31600, 31700, 32661, 32761]
    for epsg in epsg_stere:
        if epsg in [2985, 2986, 7415]:
            pytest.skip("EPSG not supported by Cartopy module")
        else:
            get_proj(f"EPSG:{epsg}")
