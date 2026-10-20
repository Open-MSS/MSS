# -*- coding: utf-8 -*-
"""

    tests._test_plugins.test_io_samples
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module loads the flight track samples of docs/samples, which the
    documentation shows, with the import plugins.

    This file is part of MSS.

    :copyright: Copyright 2026 by the MSS team, see AUTHORS.
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
import pathlib

import pytest

from mslib.plugins.io.csv import load_from_csv
from mslib.plugins.io.flitestar import load_from_flitestar
from mslib.plugins.io.text import load_from_txt
from mslib.utils.verify_waypoint_data import verify_waypoint_data

FLIGHT_TRACKS = pathlib.Path(__file__).parent.parent.parent / "docs" / "samples" / "flight-tracks"


@pytest.mark.parametrize("filename, load, count", [
    ("example.csv", load_from_csv, 5),
    ("example.txt", load_from_txt, 5),
    ("flitestar.txt", load_from_flitestar, 10),
])
def test_flight_track_sample(filename, load, count):
    _, waypoints = load(str(FLIGHT_TRACKS / filename))
    assert len(waypoints) == count


def test_ftml_sample():
    assert verify_waypoint_data((FLIGHT_TRACKS / "example.ftml").read_text(encoding="utf-8"))
