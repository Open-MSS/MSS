# -*- coding: utf-8 -*-
"""

    tests._test_plugins.test_io_flitestar
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to test mslib.plugins.io.flitestar

    This file is part of MSS.

    :copyright: Copyright 2022-2022 Reimar Bauer
    :copyright: Copyright 2022-2024 by the MSS team, see AUTHORS.
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
import os

from tests.constants import ROOT_DIR
from mslib.plugins.io import flitestar


def test_load_from_flitestar():
    data = ["# FliteStar/FliteMap generated flight plan. \n",
            "WPT S  WP1A N 49 06.00 W  22 54.00 \n",
            "\n",
            "FPL 00 \n",
            "FWP p v KFV   N 63 58.97 W  22 36.91 47000 \n",
            "FWP u s WP1A  N 49 06.00 W  22 54.00 47000 \n",
            "FWP p i DINIM N 51 00.00 W  15 00.00 47000 \n",
            "FWP p i 4730N N 47 00.00 W  30 00.00 47000 \n",
            "FWP p i H4929 N 49 30.00 W  29 00.00 47000 \n",
            "FWP p i H5128 N 51 30.00 W  28 00.00 47000 \n",
            "FWP p i H5327 N 53 30.00 W  27 00.00 47000 \n",
            "FWP p i H5825 N 58 30.00 W  25 00.00 47000 \n",
            "FWP p i H6024 N 60 30.00 W  24 00.00 47000 \n",
            "FWP p v KFV   N 63 58.97 W  22 36.91 179"
            ]

    filename = os.path.join(ROOT_DIR, "testreaddata.flt")
    with open(filename, 'w') as f:
        f.writelines(data)
    name, wp = flitestar.load_from_flitestar(filename)
    assert name == "testreaddata"
    assert wp[0].location == "KFV"
    assert wp[0].comments == ""
    assert wp[1].location == "WP1A"
    assert wp[1].comments == ""
    assert wp[5].lat == 51.5
    assert wp[5].lon == -28
    assert wp[5].flightlevel == 470.0
