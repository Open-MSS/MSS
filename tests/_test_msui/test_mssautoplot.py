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


import json
import os
from pathlib import Path

import pytest
import requests
from click.testing import CliRunner

from mslib.autoplot import (load_from_ftml, resolve_ftml_path, relocate_ftml_path, is_operation_entry,
                            flighttrack_file, flighttrack_entry, TopViewPlotting, SideViewPlotting, main,
                            download_summary)


class TestEntryKind:
    """
    An "automated_plotting_flights" entry names an operation, a flight track file or nothing.
    """
    @pytest.mark.parametrize("flight, filename, operation, file", [
        ("op1", "op1", True, None),
        ("example", "/home/mss/example.ftml", False, "/home/mss/example.ftml"),
        ("example", "example.ftml", False, "example.ftml"),
        ("example", "", False, None),
        ("", "", False, None),
        ("example", None, False, None),
    ])
    def test_kind(self, flight, filename, operation, file):
        assert is_operation_entry(flight, filename) is operation
        assert flighttrack_file(flight, filename) == file

    def test_row(self):
        assert flighttrack_entry(["example", "01 SADPAP", "", "/home/mss/example.ftml", "", ""]) == \
            "/home/mss/example.ftml"
        assert flighttrack_entry(["op1", "01 SADPAP", "", "op1", "", ""]) is None

    def test_short_row_names_no_file(self):
        assert flighttrack_entry(["example", "01 SADPAP", ""]) is None


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


def test_missing_first_flight_track_does_not_stop_the_run(tmp_path):
    """
    Setting up the plotter reads no entry, every entry is read when it is drawn. A missing
    file in the first entry skips only the plots of that entry, the next entry is still drawn.
    """
    example = os.path.join(os.path.dirname(__file__), "..", "data", "example.ftml")
    section = "00 global (cyl)"
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"automated_plotting_flights": [
        ["gone", section, "", str(tmp_path / "gone.ftml"), "", ""],
        ["example", section, "", example, "", ""]]}))
    view = TopViewPlotting(str(cfg), None, None, None, None, None)
    with pytest.raises(FileNotFoundError):
        view.load_row("gone", str(tmp_path / "gone.ftml"))
    assert view.load_row("example", example)
    view.redraw_flighttrack()
    assert len(view.wps) == 5


def test_side_view_draws_a_flight_track_file(tmp_path):
    """
    The side view sets up its waypoint indexes from the flight track it has just read,
    also for a file entry and after a missing first file.
    """
    example = os.path.join(os.path.dirname(__file__), "..", "data", "example.ftml")
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"automated_plotting_flights": [
        ["gone", "", "", str(tmp_path / "gone.ftml"), "", ""],
        ["example", "", "", example, "", ""]]}))
    view = SideViewPlotting(str(cfg), None, None, None, None, None)
    with pytest.raises(FileNotFoundError):
        view.load_row("gone", str(tmp_path / "gone.ftml"))
    assert view.load_row("example", example)
    view.redraw_flighttrack()
    assert len(view.intermediate_indexes) == len(view.wps) == 5


def test_row_without_flight_track_reads_nothing(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"automated_plotting_flights": [["", "00 global (cyl)", "", "", "", ""]]}))
    view = TopViewPlotting(str(cfg), None, None, None, None, None)
    assert not view.load_row("", "")
    assert not hasattr(view, "wps")


def test_failing_operation_is_reported(tmp_path, monkeypatch):
    """
    An operation which can't be loaded is fetched once and raises an error draw() in
    main() reports, instead of a TypeError.
    """
    calls = []

    def no_operation(*args, **kwargs):
        calls.append(args)

    monkeypatch.setattr("mslib.autoplot.load_from_operation", no_operation)
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"automated_plotting_flights": [["op", "00 global (cyl)", "", "op", "", ""]]}))
    view = TopViewPlotting(str(cfg), "http://127.0.0.1:9/", None, None, None, None)
    with pytest.raises(ConnectionError, match="Operation 'op' could not be loaded"):
        view.load_row("op", "op")
    assert len(calls) == 1


def test_missing_flight_track_is_reported_as_missing(tmp_path):
    """
    A missing flight track is reported as missing, even when its path contains "times".
    """
    missing = tmp_path / "times" / "gone.ftml"
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({
        "automated_plotting_flights": [["gone", "00 global (cyl)", "", str(missing), "", ""]],
        "automated_plotting_hsecs": [["http://127.0.0.1:9/", "L", "", ""]]}))
    result = CliRunner().invoke(main, ["--cpath", str(cfg), "--view", "top"])
    assert result.exit_code == 0
    assert "doesn't exist" in result.output
    assert "Invalid times" not in result.output


def test_unreadable_flight_track_is_reported_as_such(tmp_path):
    """
    A flight track which can't be read, here a directory, is reported with its own error,
    even when its path contains "times".
    """
    directory = tmp_path / "times" / "dir.ftml"
    directory.mkdir(parents=True)
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({
        "automated_plotting_flights": [["dir", "00 global (cyl)", "", str(directory), "", ""]],
        "automated_plotting_hsecs": [["http://127.0.0.1:9/", "L", "", ""]]}))
    result = CliRunner().invoke(main, ["--cpath", str(cfg), "--view", "top"])
    assert result.exit_code == 0
    assert "Invalid times" not in result.output
    assert str(directory) in result.output


def test_wms_http_error_is_reported_as_invalid_style_or_url(tmp_path, monkeypatch):
    """
    The errors of requests are OSErrors too, a failing WMS request is still reported
    as such and not with the raw error of the request.
    """
    def not_found(*args, **kwargs):
        raise requests.exceptions.HTTPError("404 Client Error: NOT FOUND for url: http://127.0.0.1:9/")

    monkeypatch.setattr(TopViewPlotting, "draw", not_found)
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({
        "automated_plotting_flights": [["", "00 global (cyl)", "", "", "", ""]],
        "automated_plotting_hsecs": [["http://127.0.0.1:9/", "L", "", ""]]}))
    result = CliRunner().invoke(main, ["--cpath", str(cfg), "--view", "top"])
    assert result.exit_code == 0
    assert "Invalid STYLE and/or URL requested" in result.output


def test_missing_flight_track_keeps_the_progress_dialog_open(tmp_path):
    """
    The run goes on with the next entry after a missing file, so the progress dialog
    stays open, main() closes it at the end of the run.
    """
    class FakeDialog:
        closed = False

        def close(self):
            self.closed = True

    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"automated_plotting_flights": [
        ["gone", "00 global (cyl)", "", "gone.ftml", "", ""]]}))
    pdlg = FakeDialog()
    view = TopViewPlotting(str(cfg), None, None, None, None, pdlg)
    with pytest.raises(FileNotFoundError):
        view.load_row("gone", "gone.ftml")
    assert not pdlg.closed


def test_relative_flight_track_is_found_next_to_the_configuration(tmp_path, monkeypatch):
    """
    mssautoplot looks up a relative entry next to the configuration file, as the dockwidget
    does, not in the working directory it is started in.
    """
    (tmp_path / "cfg" / "flights").mkdir(parents=True)
    example = os.path.join(os.path.dirname(__file__), "..", "data", "example.ftml")
    Path(tmp_path / "cfg" / "flights" / "example.ftml").write_text(Path(example).read_text())
    cfg = tmp_path / "cfg" / "mssautoplot.json"
    cfg.write_text(json.dumps({"automated_plotting_flights": [
        ["example", "00 global (cyl)", "", os.path.join("flights", "example.ftml"), "", ""]]}))
    monkeypatch.chdir(tmp_path)
    view = TopViewPlotting(str(cfg), None, None, None, None, None)
    assert view.load_row("example", os.path.join("flights", "example.ftml"))
    assert len(view.wps) == 5


def test_relative_flight_track_is_found_in_the_working_directory(tmp_path, monkeypatch):
    """
    A relative entry which is not next to the configuration file is still found in the
    working directory, as before, e.g. "cd ~/flights && mssautoplot --cpath ~/.config/...".
    """
    example = os.path.join(os.path.dirname(__file__), "..", "data", "example.ftml")
    (tmp_path / "config").mkdir()
    (tmp_path / "flights").mkdir()
    Path(tmp_path / "flights" / "flight1.ftml").write_text(Path(example).read_text())
    cfg = tmp_path / "config" / "mssautoplot.json"
    cfg.write_text(json.dumps({"automated_plotting_flights": [
        ["flight1", "00 global (cyl)", "", "flight1.ftml", "", ""]]}))
    monkeypatch.chdir(tmp_path / "flights")
    view = TopViewPlotting(str(cfg), None, None, None, None, None)
    assert view.ftml_file("flight1.ftml") == resolve_ftml_path("flight1.ftml")
    assert view.load_row("flight1", "flight1.ftml")
    assert len(view.wps) == 5


def test_flight_track_next_to_the_configuration_comes_first(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "flights").mkdir()
    for directory in ("config", "flights"):
        Path(tmp_path / directory / "flight1.ftml").write_text("")
    cfg = tmp_path / "config" / "mssautoplot.json"
    cfg.write_text(json.dumps({"automated_plotting_flights": [
        ["flight1", "00 global (cyl)", "", "flight1.ftml", "", ""]]}))
    monkeypatch.chdir(tmp_path / "flights")
    view = TopViewPlotting(str(cfg), None, None, None, None, None)
    assert view.ftml_file("flight1.ftml") == resolve_ftml_path("flight1.ftml", directory=tmp_path / "config")


def test_missing_relative_flight_track_names_both_directories(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "flights").mkdir()
    cfg = tmp_path / "config" / "mssautoplot.json"
    cfg.write_text(json.dumps({"automated_plotting_flights": [
        ["flight1", "00 global (cyl)", "", "flight1.ftml", "", ""]]}))
    monkeypatch.chdir(tmp_path / "flights")
    view = TopViewPlotting(str(cfg), None, None, None, None, None)
    with pytest.raises(FileNotFoundError) as excinfo:
        view.ftml_file("flight1.ftml")
    message = str(excinfo.value)
    assert str(resolve_ftml_path("flight1.ftml", directory=tmp_path / "config")) in message
    assert str(resolve_ftml_path("flight1.ftml")) in message
    assert "--fpath" in message


def test_fpath_is_not_combined_with_the_working_directory(tmp_path, monkeypatch):
    """
    --fpath replaces the directory of the entries, a file in the working directory is
    not read instead.
    """
    (tmp_path / "flights").mkdir()
    Path(tmp_path / "flights" / "flight1.ftml").write_text("")
    cfg = tmp_path / "mssautoplot.json"
    cfg.write_text(json.dumps({"automated_plotting_flights": [
        ["flight1", "00 global (cyl)", "", "flight1.ftml", "", ""]]}))
    monkeypatch.chdir(tmp_path / "flights")
    view = TopViewPlotting(str(cfg), None, None, None, None, None, fpath=str(tmp_path / "elsewhere"))
    with pytest.raises(FileNotFoundError) as excinfo:
        view.ftml_file("flight1.ftml")
    assert "working directory" not in str(excinfo.value)


class TestRelocateFtmlPath:
    """
    A configuration saved in another directory names a relative flight track relative to
    its own directory, so it finds the same file.
    """
    def test_same_directory(self, tmp_path):
        assert relocate_ftml_path("example.ftml", tmp_path, tmp_path) == "example.ftml"

    def test_other_directory(self, tmp_path):
        relocated = relocate_ftml_path(os.path.join("flights", "example.ftml"), tmp_path / "a", tmp_path / "b")
        assert relocated == os.path.join("..", "a", "flights", "example.ftml")

    def test_subdirectory(self, tmp_path):
        assert relocate_ftml_path("example.ftml", tmp_path / "a", tmp_path) == os.path.join("a", "example.ftml")

    def test_absolute_path_is_kept(self, tmp_path):
        absolute = str(tmp_path / "example.ftml")
        assert relocate_ftml_path(absolute, tmp_path / "a", tmp_path / "b") == absolute

    def test_home_is_kept(self, tmp_path):
        home = os.path.join("~", "example.ftml")
        assert relocate_ftml_path(home, tmp_path / "a", tmp_path / "b") == home

    def test_same_directory_keeps_a_name_through_a_link(self, tmp_path):
        data = link_to_store(tmp_path)
        name = os.path.join(data.name, "x.ftml")
        assert relocate_ftml_path(name, tmp_path, tmp_path) == name
        assert relocate_ftml_path(name, tmp_path, os.path.join(tmp_path, "sub", "..")) == name

    def test_other_directory_keeps_the_link(self, tmp_path):
        data = link_to_store(tmp_path)
        relocated = relocate_ftml_path(os.path.join(data.name, "x.ftml"), tmp_path, tmp_path / "saved")
        assert relocated == os.path.join("..", data.name, "x.ftml")


def link_to_store(tmp_path):
    """A directory "data" which is a link to the directory "store"."""
    (tmp_path / "store").mkdir()
    data = tmp_path / "data"
    try:
        data.symlink_to(tmp_path / "store", target_is_directory=True)
    except OSError:
        pytest.skip("symbolic links can't be created here")
    return data


class TestResolveFtmlPath:
    """
    The flight track of an "automated_plotting_flights" entry is stored as path + file name,
    --fpath overrides the directory of that entry.
    """
    def test_absolute_path_is_kept(self, tmp_path):
        absolute = tmp_path / "flights" / "example.ftml"
        assert resolve_ftml_path(str(absolute)) == absolute

    def test_bare_filename_relative_to_working_directory(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert resolve_ftml_path("example.ftml") == tmp_path / "example.ftml"

    def test_relative_path_relative_to_working_directory(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert resolve_ftml_path(os.path.join("flights", "example.ftml")) == \
            tmp_path / "flights" / "example.ftml"

    def test_user_directory_is_expanded(self):
        resolved = resolve_ftml_path(os.path.join("~", "example.ftml"))
        assert resolved == Path.home() / "example.ftml"

    def test_fpath_overrides_directory(self, tmp_path):
        assert resolve_ftml_path(str(tmp_path / "flights" / "example.ftml"), str(tmp_path / "campaign")) == \
            tmp_path / "campaign" / "example.ftml"

    def test_fpath_overrides_bare_filename(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert resolve_ftml_path("example.ftml", str(tmp_path / "campaign")) == \
            tmp_path / "campaign" / "example.ftml"

    def test_empty_fpath_is_ignored(self, tmp_path):
        absolute = tmp_path / "flights" / "example.ftml"
        assert resolve_ftml_path(str(absolute), "") == absolute

    def test_directory_anchors_a_relative_name(self, tmp_path, monkeypatch):
        # the directory of the configuration file which named the flight track,
        # not the working directory
        monkeypatch.chdir(tmp_path)
        assert resolve_ftml_path("example.ftml", directory=str(tmp_path / "flights")) == \
            tmp_path / "flights" / "example.ftml"

    def test_directory_does_not_touch_an_absolute_path(self, tmp_path):
        absolute = tmp_path / "flights" / "example.ftml"
        assert resolve_ftml_path(str(absolute), directory=str(tmp_path / "campaign")) == absolute

    def test_fpath_wins_over_directory(self, tmp_path):
        assert resolve_ftml_path("example.ftml", fpath=str(tmp_path / "campaign"),
                                 directory=str(tmp_path / "flights")) == \
            tmp_path / "campaign" / "example.ftml"

    def test_link_is_kept(self, tmp_path):
        data = link_to_store(tmp_path)
        assert resolve_ftml_path(os.path.join(data.name, "x.ftml"), directory=tmp_path) == data / "x.ftml"

    def test_configuration_directory_keeps_its_link(self, tmp_path):
        """
        A configuration reached through a link names its flight tracks relative to the
        link, as the dockwidget does.
        """
        data = link_to_store(tmp_path)
        cfg = tmp_path / "store" / "mssautoplot.json"
        cfg.write_text(json.dumps({"automated_plotting_flights": [
            ["flight1", "00 global (cyl)", "", "flight1.ftml", "", ""]]}))
        view = TopViewPlotting(str(data / "mssautoplot.json"), None, None, None, None, None)
        assert view.config_dir == data


class TestDownloadSummary:
    """
    The dialog at the end of a download sums up the whole run, not its last plot.
    """
    def test_all_drawn(self):
        assert download_summary(3, 0) == ("SUCCESS", "Plots downloaded successfully.")

    def test_nothing_drawn(self):
        assert download_summary(0, 2, ["Filename x doesn't exist"]) == \
            ("FAILURE", "Plots could not be downloaded.\n\nFilename x doesn't exist")

    def test_nothing_to_draw(self):
        assert download_summary(0, 0)[0] == "FAILURE"

    @pytest.mark.parametrize("results", [[False, True], [True, False]])
    def test_missing_track_first_or_last(self, results):
        title, text = download_summary(results.count(True), results.count(False), ["gone"])
        assert title == "WARNING"
        assert text.startswith("1 of 2 plots downloaded, 1 failed.")
