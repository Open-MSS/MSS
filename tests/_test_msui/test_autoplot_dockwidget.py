# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_autoplot_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.autoplot_dockwidget

    This file is part of MSS.

    :copyright: Copyright 2026 Jan Eisermann
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
from pathlib import Path

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


class TestConfigToWrite:
    """
    The names of a selected configuration stay as they are, a written configuration gets
    a relative name rewritten relative to its own directory.
    """
    def test_same_directory_keeps_the_names(self, tmp_path):
        config = {"automated_plotting_flights": [["flight1", "", "", "example.ftml", "", ""],
                                                 ["flight2", "", "", os.path.join("flights", "b.ftml"), "", ""]]}
        assert AutoplotDockWidget.config_to_write(config, tmp_path, tmp_path) == config

    def test_relative_name_follows_the_new_location(self, tmp_path):
        source, target = tmp_path / "campaign", tmp_path / "saved"
        config = {"automated_plotting_flights": [["flight1", "", "", os.path.join("flights", "a.ftml"), "", ""]]}
        written = AutoplotDockWidget.config_to_write(config, source, target)
        assert written["automated_plotting_flights"][0][3] == os.path.join("..", "campaign", "flights", "a.ftml")
        # both names lead to the same file
        assert (target / written["automated_plotting_flights"][0][3]).resolve() == \
            (source / "flights" / "a.ftml").resolve()

    def test_absolute_and_home_paths_are_kept(self, tmp_path):
        absolute = str(tmp_path / "flights" / "a.ftml")
        home = os.path.join("~", "a.ftml")
        config = {"automated_plotting_flights": [["flight1", "", "", absolute, "", ""],
                                                 ["flight2", "", "", home, "", ""]]}
        written = AutoplotDockWidget.config_to_write(config, tmp_path / "x", tmp_path / "y")
        assert [row[3] for row in written["automated_plotting_flights"]] == [absolute, home]

    def test_operations_and_empty_entries_are_kept(self, tmp_path):
        flights = [["operation1", "", "", "operation1", "", ""], ["", "", "", "", "", ""], []]
        config = {"automated_plotting_flights": flights}
        assert AutoplotDockWidget.config_to_write(config, tmp_path / "x", tmp_path / "y") == config

    def test_settings_keep_their_names(self, tmp_path):
        config = {"automated_plotting_flights": [["flight1", "", "", "example.ftml", "", ""]],
                  "automated_plotting_hsecs": [["url", "layer", "", ""]]}
        written = AutoplotDockWidget.config_to_write(config, tmp_path / "x", tmp_path / "y")
        assert config["automated_plotting_flights"] == [["flight1", "", "", "example.ftml", "", ""]]
        assert written["automated_plotting_hsecs"] == config["automated_plotting_hsecs"]


class TestMissingFlighttrack:
    """
    The download button stops on a flight track file which is not there, instead of
    letting mssautoplot leave through SystemExit.
    """
    def test_all_files_are_there(self, tmp_path):
        example = tmp_path / "example.ftml"
        shutil.copy(os.path.join(os.path.dirname(__file__), "..", "data", "example.ftml"), example)
        flights = [["flight1", "", "", str(example), "", ""]]
        assert AutoplotDockWidget.missing_flighttrack(flights, tmp_path) is None

    def test_relative_name_is_found_next_to_the_configuration(self, tmp_path, monkeypatch):
        shutil.copy(os.path.join(os.path.dirname(__file__), "..", "data", "example.ftml"), tmp_path)
        monkeypatch.chdir(Path.home())
        flights = [["flight1", "", "", "example.ftml", "", ""]]
        assert AutoplotDockWidget.missing_flighttrack(flights, tmp_path) is None

    def test_missing_file(self, tmp_path):
        missing = tmp_path / "example.ftml"
        flights = [["flight1", "", "", str(missing), "", ""]]
        assert AutoplotDockWidget.missing_flighttrack(flights, tmp_path) == (
            "flight1", str(missing), missing.resolve())

    def test_flighttrack_which_was_never_saved(self, tmp_path):
        # only the name of the track is stored, it is looked up next to the configuration
        flights = [["flight1", "", "", "flight1.ftml", "", ""]]
        assert AutoplotDockWidget.missing_flighttrack(flights, tmp_path) == (
            "flight1", "flight1.ftml", tmp_path.resolve() / "flight1.ftml")

    def test_operation_and_empty_entries(self, tmp_path):
        flights = [["operation1", "", "", "operation1", "", ""], ["", "", "", "", "", ""], []]
        assert AutoplotDockWidget.missing_flighttrack(flights, tmp_path) is None


class TestMissingFlighttrackMessage:
    """
    The path a lookup fails at is not always the one the user typed, so the message says
    where it comes from.
    """
    def test_name_without_a_directory(self, tmp_path):
        """
        Such an entry is either a flight track which was never saved, or a
        configuration which names the file without a directory. The entry does not
        tell which of the two, so the message names both remedies and does not
        claim the track was never saved.
        """
        message = AutoplotDockWidget.missing_flighttrack_message(
            "flight1", "flight1.ftml", tmp_path / "flight1.ftml", tmp_path)
        assert message == (
            "The flight track file of 'flight1' does not exist:\n"
            f"{tmp_path / 'flight1.ftml'}\n"
            "\n"
            "Only the name 'flight1.ftml' is stored, without a directory, so the file is looked up "
            f"next to the configuration file, in {tmp_path}.\n"
            "Save the flight track in the MSUI and add the row again, or store the name with its "
            "directory in the configuration file.")
        assert "never saved" not in message

    def test_relative_directory(self, tmp_path):
        entry = os.path.join("flights", "example.ftml")
        message = AutoplotDockWidget.missing_flighttrack_message(
            "flight1", entry, tmp_path / entry, tmp_path)
        assert f"The name '{entry}' is relative to the directory of the configuration file, {tmp_path}." \
            in message

    def test_absolute_path(self, tmp_path):
        missing = tmp_path / "flights" / "example.ftml"
        message = AutoplotDockWidget.missing_flighttrack_message("flight1", str(missing), missing, tmp_path)
        assert "The file was moved or deleted after it was stored." in message
        assert str(tmp_path) + "." not in message


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
