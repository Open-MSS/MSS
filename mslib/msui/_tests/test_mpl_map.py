# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mpl_map
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to test the functionality of mpl_map.py

    This file is part of mss.

    :copyright: Copyright 2021 May Bär
    :copyright: Copyright 2021 by the mss team, see AUTHORS.
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
from matplotlib import pyplot as plt
from mslib.msui.mpl_map import MapCanvas


class Test_MapCanvas:
    def setup(self):
        kwargs = {'resolution': 'l', 'area_thresh': 1000.0, 'ax': plt.gca(), 'llcrnrlon': -15.0, 'llcrnrlat': 35.0,
                  'urcrnrlon': 30.0, 'urcrnrlat': 65.0, 'epsg': '4326'}
        self.map = MapCanvas(**kwargs)

    def test_no_coastsegs(self):
        """
        Assert rendering areas without a coastline does not cause an error
        """
        # On land
        self.map.ax.set_xlim([2, 3])
        self.map.ax.set_ylim([48, 49])
        self.map.update_with_coordinate_change()

        # On water
        self.map.ax.set_xlim([1, 2])
        self.map.ax.set_ylim([62, 63])
        self.map.update_with_coordinate_change()
