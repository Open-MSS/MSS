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


class TestResolveFlightsPaths:
    """
    A configuration file can name the flight track relative to its own directory,
    the GUI is started from an arbitrary working directory and has to resolve it.
    """
    def test_bare_filename_next_to_the_config(self, tmp_path):
        flights = [["flight1", "01 SADPAP (stereo)", "", "example.ftml", "", ""]]
        assert AutoplotDockWidget.resolve_flights_paths(flights, tmp_path) == [
            ["flight1", "01 SADPAP (stereo)", "", str(tmp_path.resolve() / "example.ftml"), "", ""]]

    def test_relative_directory(self, tmp_path):
        flights = [["flight1", "", "", os.path.join("flights", "example.ftml"), "", ""]]
        assert AutoplotDockWidget.resolve_flights_paths(flights, tmp_path)[0][3] == \
            str(tmp_path.resolve() / "flights" / "example.ftml")

    def test_absolute_path_is_kept(self, tmp_path):
        flights = [["flight1", "", "", "/home/mss/flights/example.ftml", "", ""]]
        assert AutoplotDockWidget.resolve_flights_paths(flights, tmp_path)[0][3] == \
            "/home/mss/flights/example.ftml"

    def test_home_is_expanded(self, tmp_path):
        flights = [["flight1", "", "", os.path.join("~", "example.ftml"), "", ""]]
        assert AutoplotDockWidget.resolve_flights_paths(flights, tmp_path)[0][3] == \
            str(Path.home().resolve() / "example.ftml")

    def test_operation_is_unchanged(self, tmp_path):
        flights = [["operation1", "01 SADPAP (stereo)", "", "operation1", "", ""]]
        assert AutoplotDockWidget.resolve_flights_paths(flights, tmp_path) == flights

    def test_entries_without_a_flighttrack(self, tmp_path):
        flights = [["", "", "", "", "", ""], []]
        assert AutoplotDockWidget.resolve_flights_paths(flights, tmp_path) == flights

    def test_the_configuration_is_not_modified(self, tmp_path):
        flights = [["flight1", "", "", "example.ftml", "", ""]]
        AutoplotDockWidget.resolve_flights_paths(flights, tmp_path)
        assert flights == [["flight1", "", "", "example.ftml", "", ""]]


class TestMissingFlighttrack:
    """
    The download button stops on a flight track file which is not there, instead of
    letting mssautoplot leave through SystemExit.
    """
    def test_all_files_are_there(self, tmp_path):
        example = tmp_path / "example.ftml"
        shutil.copy(os.path.join(os.path.dirname(__file__), "..", "data", "example.ftml"), example)
        flights = [["flight1", "", "", str(example), "", ""]]
        assert AutoplotDockWidget.missing_flighttrack(flights) is None

    def test_missing_file(self, tmp_path):
        missing = tmp_path / "example.ftml"
        flights = [["flight1", "", "", str(missing), "", ""]]
        assert AutoplotDockWidget.missing_flighttrack(flights) == ("flight1", str(missing), missing)

    def test_flighttrack_which_was_never_saved(self, tmp_path, monkeypatch):
        # only the name of the track is stored, it is looked up in the working directory
        monkeypatch.chdir(tmp_path)
        flights = [["flight1", "", "", "flight1.ftml", "", ""]]
        assert AutoplotDockWidget.missing_flighttrack(flights) == (
            "flight1", "flight1.ftml", Path(tmp_path).resolve() / "flight1.ftml")

    def test_operation_and_empty_entries(self):
        flights = [["operation1", "", "", "operation1", "", ""], ["", "", "", "", "", ""], []]
        assert AutoplotDockWidget.missing_flighttrack(flights) is None


class TestMissingFlighttrackMessage:
    """
    The path a lookup fails at is rarely the one the user typed, so the message says
    where it comes from.
    """
    def test_relative_name_of_a_configuration(self):
        message = AutoplotDockWidget.missing_flighttrack_message(
            "flight1", "/home/mss/example.ftml", Path("/home/mss/example.ftml"),
            ("/home/mss/mssautoplot.json", "example.ftml"))
        assert message == (
            "The flight track file of 'flight1' does not exist:\n"
            "/home/mss/example.ftml\n"
            "\n"
            "The configuration /home/mss/mssautoplot.json names it 'example.ftml', "
            "without a directory, so it is looked up next to that file.\n"
            "Correct it there, or open the flight track in the MSUI, save it and add the row again.")

    def test_path_of_a_configuration(self):
        message = AutoplotDockWidget.missing_flighttrack_message(
            "flight1", "/home/mss/flights/example.ftml", Path("/home/mss/flights/example.ftml"),
            ("/home/mss/mssautoplot.json", "/home/mss/flights/example.ftml"))
        assert "This path is stored in the configuration /home/mss/mssautoplot.json." in message
        assert "names it" not in message

    def test_name_without_a_directory(self, tmp_path, monkeypatch):
        """
        Such an entry is either a flight track which was never saved, or a
        configuration which names the file without a directory. The entry does not
        tell which of the two, so the message names both remedies and does not
        claim the track was never saved.
        """
        monkeypatch.chdir(tmp_path)
        message = AutoplotDockWidget.missing_flighttrack_message(
            "flight1", "flight1.ftml", Path(tmp_path).resolve() / "flight1.ftml")
        assert "Only the name 'flight1.ftml' is stored, without a directory" in message
        assert f"working directory {Path(tmp_path).resolve()}" in message
        assert "Save the flight track in the MSUI and add the row again, or store the name " \
               "with its directory in the configuration file." in message
        assert "never saved" not in message

    def test_file_of_a_row_the_dockwidget_wrote(self):
        message = AutoplotDockWidget.missing_flighttrack_message(
            "flight1", "/home/mss/flights/example.ftml", Path("/home/mss/flights/example.ftml"))
        assert "The file was moved or deleted after the row was added." in message


class TestFlightsSources:
    """
    Which configuration file named a flight track, and how, is kept to explain a file
    which is not there.
    """
    def test_name_and_path_of_the_configuration(self, tmp_path):
        configured = [["flight1", "", "", "example.ftml", "", ""],
                      ["flight2", "", "", "/home/mss/other.ftml", "", ""]]
        resolved = AutoplotDockWidget.resolve_flights_paths(configured, tmp_path)
        sources = AutoplotDockWidget.flights_sources("/home/mss/mssautoplot.json", configured, resolved)
        assert sources == {
            str(tmp_path.resolve() / "example.ftml"): ("/home/mss/mssautoplot.json", "example.ftml"),
            "/home/mss/other.ftml": ("/home/mss/mssautoplot.json", "/home/mss/other.ftml")}

    def test_entries_without_a_flighttrack_file_are_skipped(self, tmp_path):
        configured = [["", "", "", "", "", ""], ["operation1", "", "", "operation1", "", ""], []]
        resolved = AutoplotDockWidget.resolve_flights_paths(configured, tmp_path)
        assert AutoplotDockWidget.flights_sources("mssautoplot.json", configured, resolved) == {}

    def test_two_entries_of_the_same_file(self, tmp_path):
        """
        The first entry wins, both explanations name the same missing file and the same
        configuration to correct it in.
        """
        configured = [["flight1", "", "", "example.ftml", "", ""],
                      ["flight2", "", "", str(tmp_path / "example.ftml"), "", ""]]
        resolved = AutoplotDockWidget.resolve_flights_paths(configured, tmp_path)
        sources = AutoplotDockWidget.flights_sources("mssautoplot.json", configured, resolved)
        assert sources == {str(tmp_path.resolve() / "example.ftml"): ("mssautoplot.json", "example.ftml")}


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
