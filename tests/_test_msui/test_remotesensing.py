# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_remotesensing
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.remotesensing module

    This file is part of MSS.

    :copyright: Copyright 2017 Reimar Bauer, Joern Ungermann
    :copyright: Copyright 2017-2023 by the MSS team, see AUTHORS.
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
import sys

from mock import Mock
from matplotlib.collections import LineCollection
from PyQt5 import QtWidgets
import pytest
import skyfield_data
from mslib.msui.remotesensing_dockwidget import RemoteSensingControlWidget
from mslib.msui import mpl_qtwidget as qt


def test_skyfield_data_expiration(recwarn):
    skyfield_data.check_expirations()
    assert len(recwarn) == 0, [_x.message for _x in recwarn]


class Test_RemoteSensingControlWidget(object):
    """
    Tests about RemoteSensingControlWidget
    """
    def setup_method(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.view = Mock()
        self.map = qt.TopViewPlotter()
        self.map.init_map()
        self.bmap = self.map.map
        self.result_test_direction_coordinates = [([79.08, 79.06, 79.03, 79.01, 78.99, 78.97, 78.95,
                                                    78.93, 78.9, 78.88, 78.86, 78.84, 78.82,
                                                    78.73, 78.7, 78.68, 78.66, 78.64, 78.62,
                                                    78.59, 78.57, 78.55, 78.79, 78.77, 78.75,
                                                    78.53, 78.50, 78.48, 78.46, 78.44, 78.41,
                                                    78.39, 78.37, 78.35, 78.32, 78.30, 78.28,
                                                    78.25, 78.23, 78.21, 78.19, 78.16, 78.14,
                                                    78.12, 78.09, 78.07, 78.05, 78.03, 78.00,
                                                    77.98, 77.96, 77.93, 77.91, 77.89, 77.86,
                                                    77.84, 77.82, 77.79, 77.77, 77.75, 77.72,
                                                    77.70, 77.68, 77.65, 77.63, 77.60, 77.58,
                                                    77.56, 77.53, 77.51, 77.49, 77.46, 77.44,
                                                    77.41, 77.39, 77.37, 77.34, 77.32, 77.29,
                                                    77.27, 77.24, 77.22, 77.20, 77.17, 77.15,
                                                    77.12, 77.1], [21.15, 21.23, 21.32, 21.40, 21.49, 21.58,
                                                   22.166, 22.75, 21.84, 22.92, 22.84, 23,
                                                   23.36, 23.12, 23.58, 24.44, 24.52, 24.82,
                                                   25.74, 25.28, 25.84, 25.57, 25.98, 26.06,
                                                   26.15, 26.24, 26.32, 26.41, 26.49, 26.58,
                                                   26.67, 26.75, 26.84, 26.93, 27.01, 27.1,
                                                   27.18, 27.27, 27.36, 27.44, 27.53, 27.61,
                                                   27.7, 27.79, 27.87, 27.96, 28.04, 28.13,
                                                   28.22, 28.30, 28.39, 28.47, 28.56])]

        self.lon_lin = [79.08, 79.06, 79.04, 79.02, 78.99, 78.97, 78.95, 78.93,
                        78.91, 78.89, 78.86, 78.84, 78.82, 78.80, 78.78, 78.75,
                        78.75, 78.71, 78.69, 78.67, 78.64, 78.62, 78.60, 78.58,
                        78.56, 78.53, 78.51, 78.49, 78.46, 78.44, 78.42, 78.40,
                        78.37, 78.35, 78.33, 78.31, 78.28, 78.26, 78.24, 78.21,
                        78.19, 78.17, 78.15, 78.12, 78.10, 78.08, 78.05, 78.05,
                        78.03, 77.98, 77.96, 77.94, 77.91, 77.89, 77.87, 77.84,
                        77.82, 77.80, 77.77, 77.75, 77.73, 77.70, 77.68, 77.66,
                        77.61, 77.59, 77.58, 77.54, 77.51, 77.49, 77.47, 77.44,
                        77.42, 77.39, 77.37, 77.34, 77.32, 77.30, 77.27, 77.25,
                        77.20, 77.18, 77.16, 77.15, 77.13]

        self.lat_lin = [21.15, 21.23, 21.32, 21.4, 21.495, 21.58, 21.66, 21.75,
                        21.84, 21.92, 22.01, 22.1, 22.186, 22.27, 22.35, 22.44,
                        22.53, 22.61, 22.7, 22.79, 22.87, 22.96, 23.05, 23.13,
                        23.22, 23.30, 23.39, 23.48, 23.56, 23.65, 23.74, 23.82,
                        23.91, 23.99, 24.08, 24.17, 24.25, 24.34, 24.43, 24.51,
                        24.60, 24.68, 24.77, 24.86, 24.94, 25.03, 25.12, 25.20,
                        25.29, 25.37, 25.46, 25.55, 25.63, 25.72, 25.81, 25.89,
                        25.98, 26.06, 26.15, 26.24, 26.32, 26.41, 26.49, 26.58,
                        26.67, 26.75, 26.84, 26.93, 27.01, 27.10, 27.18, 27.27,
                        27.36, 27.44, 27.53, 27.61, 27.70, 27.79, 27.87, 27.96,
                        28.04, 28.13, 28.22, 28.30, 28.39, 28.47, 28.56]

        self.cut_height = 10.0
        self.result_test_tangent_point_coordinates = [(81.2, 21.62), (81.19, 21.65), (81.17, 21.79),
                                                      (81.11, 21.98), (81.12, 21.93), (81.1, 22.05),
                                                      (81.09, 22.08), (81.07, 22.17), (81.04, 22.3),
                                                      (80.98, 22.53), (81.01, 22.42), (80.98, 22.53),
                                                      (80.96, 22.63), (80.94, 22.73), (80.88, 22.96),
                                                      (80.95, 22.44), (80.75, 23.39), (80.86, 23.02),
                                                      (80.85, 23.11), (80.75, 23.46), (80.8, 23.28),
                                                      (80.78, 23.37), (80.75, 23.51), (80.74, 23.54),
                                                      (80.65, 23.89), (80.69, 23.71), (80.68, 23.8),
                                                      (80.58, 24.15), (80.63, 23.97), (80.61, 24.06),
                                                      (80.58, 24.2), (80.52, 24.42), (80.54, 24.37),
                                                      (80.53, 24.4), (80.51, 24.49), (80.42, 24.83),
                                                      (80.46, 24.66), (80.44, 24.75), (80.35, 25.09),
                                                      (80.39, 24.92), (80.37, 25.06), (80.36, 25.09),
                                                      (80.29, 25.36), (80.3, 25.31), (80.29, 25.35),
                                                      (80.22, 25.62), (80.29, 25.12), (80.25, 25.6),
                                                      (79.98, 26.3), (80.18, 25.77), (80.16, 25.86),
                                                      (80.07, 26.21), (80.11, 26.03), (80.1, 26.12),
                                                      (80.01, 26.47), (80.05, 26.29), (80.02, 26.43),
                                                      (79.96, 26.65), (79.98, 26.55), (79.96, 26.69),
                                                      (79.9, 26.91), (79.91, 26.86), (79.9, 26.89),
                                                      (79.69, 27.49), (79.83, 27.12), (79.85, 26.95),
                                                      (79.69, 27.6), (79.7, 27.58), (79.74, 27.41),
                                                      (79.71, 27.55), (79.65, 27.76), (79.68, 27.67),
                                                      (79.59, 28.01), (79.63, 27.84), (79.54, 28.18),
                                                      (79.58, 28.01), (79.56, 28.1), (79.48, 28.44),
                                                      (79.52, 28.27), (79.26, 28.95), (79.45, 28.44),
                                                      (79.43, 28.52), (79.45, 28.44), (79.41, 28.69)]

        self.wp_vertices = [(0, 0), (1, 4)]
        self.wp_heights = [0, 1000]
        self.coordinates = [[79.083, 21.15], [77.103, 28.566]]
        self.heights = [0.0, 0.0]
        self.times = [datetime.datetime(2023, 4, 15, 10, 9, 59, 174000),
                      datetime.datetime(2023, 4, 15, 11, 18, 27, 735581)]
        self.solar_type = ('sun', 'total (horizon)')
        self.remote_widget = RemoteSensingControlWidget(view=self.view)

    @pytest.mark.parametrize(
        "lon0, lat0, h0, lon1, lat1, h1, obs_azi, expected",
        [
            (0, 0, 0, 1, 0, 0, 0, (90.0, -1)),
            (0, 0, 0, -1, 0, 0, 0, (270.0, -1)),
            (0, 0, 0, 1, 0, 0, 90, (180.0, -1)),
            (0, 0, 0, 0, 1, 0, 0, (0.0, -1)),
            (0, 0, 0, 0, -1, 0, 0, (180.0, -1)),
        ],
    )
    def test_view_angles(self, lon0, lat0, h0, lon1, lat1, h1, obs_azi, expected):
        compute_view_angles = self.remote_widget.compute_view_angles
        angle = compute_view_angles(lon0, lat0, h0, lon1, lat1, h1, obs_azi, -1)
        assert angle[0] == expected[0]
        assert angle[1] == expected[1]

    @pytest.mark.parametrize("body, lat, lon, alt, expected_angle", [
        ("sun", 73.56, 78.01, 25.27, (106.71, -20.28)),
        ("sun", 73.07, 77.78, 26.07, (106.35, -20.71)),
        ("sun", 73.58, 77.56, 26.92, (105.96, -21.13)),
        ("sun", 73.08, 77.33, 27.74, (105.57, -21.55)),
        ("sun", 73.56, 78.01, 25.27, (106.71, -20.28))
    ])
    def test_body_angle(self, body, lat, lon, alt, expected_angle):
        compute_body_angle = self.remote_widget.compute_body_angle
        angle = compute_body_angle(body, lat, lon, alt)
        assert angle[0] == pytest.approx(expected_angle[0], rel=1e-3)
        assert angle[1] == pytest.approx(expected_angle[1], rel=1e-3)

    def test_direction_coordinates(self):
        compute_direction_coordinates = self.remote_widget.direction_coordinates
        coordinates = compute_direction_coordinates(self.result_test_direction_coordinates)
        result = [[(round(x, 2), round(y, 2)) for x, y in inner_list] for inner_list in coordinates]
        assert result == [[(78.1, 27.83), (79.18, 28.14)]]

    def test_compute_tangent_lines(self):
        result = self.remote_widget.compute_tangent_lines(self.bmap,
                                                          self.wp_vertices, self.wp_heights)
        assert isinstance(result, LineCollection)
        assert len(result.get_segments()) == len(self.wp_heights)

    def test_compute_solar_lines(self):
        result = self.remote_widget
        result = result.compute_solar_lines(self.bmap, self.coordinates, self.heights, self.times, self.solar_type)
        assert isinstance(result, LineCollection)

    def test_tangent_point_coordinates(self):
        tangent_point_coordinates = self.remote_widget.tangent_point_coordinates
        coordinates = tangent_point_coordinates(lon_lin=self.lon_lin, lat_lin=self.lat_lin, cut_height=self.cut_height)
        result = [(round(x, 2), round(y, 2)) for x, y in coordinates]
        assert result == self.result_test_tangent_point_coordinates

    @pytest.mark.parametrize("obs_azi, obs_ele, sol_azi, sol_ele, expected_rating", [
        (76.00, -1.0, 240.70, 58.33, 175.06),
        (76.11, -1.0, 239.90, 60.03, 174.79),
        (76.50, -1.0, 236.15, 66.92, 173.5),
    ])
    def test_calc_view_rating(self, obs_azi, obs_ele, sol_azi, sol_ele, expected_rating):
        height = 0.0
        difftype = "total (horizon)"
        calc_view_rating = self.remote_widget.calc_view_rating
        view_rating = calc_view_rating(obs_azi=obs_azi, obs_ele=obs_ele, sol_azi=sol_azi,
                                       sol_ele=sol_ele, height=height, difftype=difftype)
        assert round(view_rating, 2) == pytest.approx(expected_rating, rel=1e-3)
