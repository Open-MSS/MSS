# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_autoplot_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.autoplot_dockwidget

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

import os
import shutil

from mslib.msui import flighttrack as ft
from mslib.msui.autoplot_dockwidget import AutoplotDockWidget


class FakeView:
    """A view window, reduced to what the dockwidget reads from it."""
    def __init__(self, waypoints_model):
        self.waypoints_model = waypoints_model


class TestFlighttrackFilename:
    """
    mssautoplot only finds the flight track of an "automated_plotting_flights" entry
    when the entry carries the directory too, so the dockwidget stores path + file name.
    """
    def test_flighttrack_of_a_file(self, tmp_path):
        example = tmp_path / "example.ftml"
        shutil.copy(os.path.join(os.path.dirname(__file__), "..", "data", "example.ftml"), example)
        view = FakeView(ft.WaypointsTableModel(filename=str(example)))
        assert view.waypoints_model.name == "example"
        assert AutoplotDockWidget.flighttrack_filename(view, "example") == str(example)

    def test_flighttrack_without_a_file(self):
        view = FakeView(ft.WaypointsTableModel(name="flight1"))
        assert AutoplotDockWidget.flighttrack_filename(view, "flight1") == "flight1.ftml"


class TestRowToShow:
    """
    The tree widget shows the file name alone, the path stays in the configuration.
    """
    def test_path_is_hidden(self):
        row = ["flight1", "01 SADPAP (stereo)", "", "/home/mss/flights/example.ftml", "", ""]
        assert AutoplotDockWidget.flights_row_to_show(row) == [
            "flight1", "01 SADPAP (stereo)", "", "example.ftml", "", ""]
        # the entry itself keeps its path
        assert row[3] == "/home/mss/flights/example.ftml"

    def test_bare_filename_is_unchanged(self):
        row = ["flight1", "01 SADPAP (stereo)", "", "example.ftml", "", ""]
        assert AutoplotDockWidget.flights_row_to_show(row) == row

    def test_operation_is_unchanged(self):
        row = ["operation1", "01 SADPAP (stereo)", "", "operation1", "", ""]
        assert AutoplotDockWidget.flights_row_to_show(row) == row

    def test_empty_rows(self):
        assert AutoplotDockWidget.flights_row_to_show([]) == []
        assert AutoplotDockWidget.flights_row_to_show(["", "", "", "", "", ""]) == ["", "", "", "", "", ""]
