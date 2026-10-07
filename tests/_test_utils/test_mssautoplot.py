# -*- coding: utf-8 -*-
"""

    tests._test_utils.test_mssautoplot
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mslib.autoplot

    This file is part of MSS.

    :copyright: Copyright 2023 Harsh Khilawala
    :copyright: Copyright 2023-2026 by the MSS team, see AUTHORS.
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
from pathlib import Path

from mslib.autoplot import load_from_ftml, resolve_ftml_path


def test_load_from_ftml():
    sample_path = os.path.join(os.path.dirname(__file__), "..", "data")
    example_file = os.path.join(sample_path, "example.ftml")
    assert load_from_ftml(example_file) is not None
    data_list, wp_list = load_from_ftml(example_file)
    assert data_list == [(55.15, -23.74, 0.0, 'B', 'Takeoff'),
                         (42.99, -12.1, 350.0, 'A', ''),
                         (52.785, -8.925, 380.0, 'Shannon', 'Dive'),
                         (48.08, 11.28, 400.0, 'EDMO', ''),
                         (63.74, 1.73, 0.0, 'C', 'Landing')]
    assert len(wp_list) == 5
    assert type(wp_list[0]).__name__ == 'Waypoint'


class TestResolveFtmlPath:
    """
    The flight track of an "automated_plotting_flights" entry is stored as path + file name,
    --fpath overrides the directory of that entry.
    """
    def test_absolute_path_is_kept(self):
        assert resolve_ftml_path("/home/mss/flights/example.ftml") == Path("/home/mss/flights/example.ftml")

    def test_bare_filename_relative_to_working_directory(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert resolve_ftml_path("example.ftml") == Path(tmp_path).resolve() / "example.ftml"

    def test_relative_path_relative_to_working_directory(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert resolve_ftml_path(os.path.join("flights", "example.ftml")) == \
            Path(tmp_path).resolve() / "flights" / "example.ftml"

    def test_user_directory_is_expanded(self):
        resolved = resolve_ftml_path(os.path.join("~", "example.ftml"))
        assert resolved == Path.home().resolve() / "example.ftml"

    def test_fpath_overrides_directory(self):
        assert resolve_ftml_path("/home/mss/flights/example.ftml", "/data/campaign") == \
            Path("/data/campaign/example.ftml")

    def test_fpath_overrides_bare_filename(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert resolve_ftml_path("example.ftml", "/data/campaign") == Path("/data/campaign/example.ftml")

    def test_empty_fpath_is_ignored(self):
        assert resolve_ftml_path("/home/mss/flights/example.ftml", "") == Path("/home/mss/flights/example.ftml")

    def test_directory_anchors_a_relative_name(self, tmp_path, monkeypatch):
        # the directory of the configuration file which named the flight track,
        # not the working directory
        monkeypatch.chdir(tmp_path)
        assert resolve_ftml_path("example.ftml", directory="/home/mss/flights") == \
            Path("/home/mss/flights/example.ftml")

    def test_directory_does_not_touch_an_absolute_path(self):
        assert resolve_ftml_path("/home/mss/example.ftml", directory="/data/campaign") == \
            Path("/home/mss/example.ftml")

    def test_fpath_wins_over_directory(self):
        assert resolve_ftml_path("example.ftml", fpath="/data/campaign", directory="/home/mss/flights") == \
            Path("/data/campaign/example.ftml")
