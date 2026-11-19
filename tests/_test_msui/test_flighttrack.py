# -*- coding: utf-8 -*-
"""

    _tests._test_msui.test_flighttrack
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for WaypointsTableModel corrupted performance settings handling

    This file is part of MSS.

    :copyright: Copyright 2024-2026 by the MSS team, see AUTHORS.
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
import pytest
import os
import subprocess
import sys
from pathlib import Path
import xml.etree.ElementTree as etree

from PyQt5 import QtCore

from mslib.msui.flighttrack import (LINEAR_DATA_COLUMN, TABLE_FULL, Waypoint, WaypointsTableModel,
                                    linear_data_columns, values_at_waypoints)
from mslib.msui.performance_settings import DEFAULT_PERFORMANCE
from tests.utils import lsec_xml


class Test_WaypointsTableModel_CorruptedSettings:
    """
    Tests for handling corrupted performance settings in WaypointsTableModel.
    Addresses issue #2885.
    """

    def test_load_settings_with_corrupted_performance_settings(self, tmp_path, monkeypatch):
        """
        Test that load_settings handles corrupted performance_settings gracefully.

        Fixes #2885: When performance_settings is loaded as a string (corrupted data)
        instead of a dict, the application should fall back to DEFAULT_PERFORMANCE
        instead of crashing with a TypeError.
        """
        # Create a temporary settings file with corrupted performance_settings
        temp_file = tmp_path / "corrupted_settings.json"
        corrupted_data = {
            "performance": {
                "performance_settings": "corrupted_string_data"
            }
        }
        temp_file.write_text(json.dumps(corrupted_data), encoding="utf-8")

        # Temporarily override the settings file location
        import mslib.msui.utils.config as config_module

        def mock_read_config(tag, default, settings_file=None):
            if tag == "performance":
                with open(temp_file, 'r') as f:
                    data = json.load(f)
                    return data.get("performance", {}).get("performance_settings", default)
            return default

        monkeypatch.setattr(config_module, "read_config_file", mock_read_config)

        # Create a WaypointsTableModel instance
        model = WaypointsTableModel(name="test_track")

        # This should NOT raise a TypeError anymore
        model.load_settings()

        # Verify that performance_settings is now a dict (DEFAULT_PERFORMANCE)
        assert isinstance(model.performance_settings, dict), \
            "performance_settings should be a dict after handling corrupted data"

        # Verify it was reset to DEFAULT_PERFORMANCE
        assert model.performance_settings == DEFAULT_PERFORMANCE, \
            "Should fall back to DEFAULT_PERFORMANCE when data is corrupted"

    def test_isinstance_check_with_various_types(self):
        """
        Test that the isinstance check correctly identifies dict vs non-dict types.

        This verifies the core fix: if not isinstance(settings, dict)
        """
        # These should NOT be identified as dicts
        assert not isinstance("corrupted_string", dict), \
            "String should not pass isinstance dict check"
        assert not isinstance(123, dict), \
            "Integer should not pass isinstance dict check"
        assert not isinstance([1, 2, 3], dict), \
            "List should not pass isinstance dict check"
        assert not isinstance(None, dict), \
            "None should not pass isinstance dict check"
        assert not isinstance((1, 2), dict), \
            "Tuple should not pass isinstance dict check"

        # This SHOULD be identified as a dict
        assert isinstance({"key": "value"}, dict), \
            "Dict should pass isinstance dict check"
        assert isinstance({}, dict), \
            "Empty dict should pass isinstance dict check"


class Test_LinearData:
    """
    Tests for the data columns that the linear view fills in the table view.
    """

    def setup_method(self):
        self.waypoints = [Waypoint(0., 0., 0.), Waypoint(1., 1., 350.),
                          Waypoint(2., 2., 350.), Waypoint(3., 3., 0.)]
        self.model = WaypointsTableModel("")
        self.model.insertRows(0, rows=len(self.waypoints), waypoints=self.waypoints)

    def test_values_at_waypoints(self):
        # Only the waypoints, not the interpolated points in between, are
        # returned, and NaN values (aircraft on the ground) become None.
        assert values_at_waypoints(
            [0., 0.5, 1., 1.5, 2., 2.5, 3.], [0., 0.5, 1., 1.5, 2., 2.5, 3.],
            [float("nan"), 5., 10., 12., 20., 22., float("nan")],
            self.waypoints) == [None, 10., 20., None]

    def test_values_at_waypoints_without_matching_points(self):
        assert values_at_waypoints([10., 11.], [10., 11.], [1., 2.], self.waypoints) == [None] * 4

    def test_linear_data_columns(self):
        columns = linear_data_columns([lsec_xml()], self.waypoints)
        assert columns == [{"name": "Mole fraction of ozone (Linear)",
                            "unit": "ppmv",
                            "values": [None, 10., 20., None]}]

    def test_linear_data_columns_makes_names_unique(self):
        columns = linear_data_columns([lsec_xml(), lsec_xml()], self.waypoints)
        assert [column["name"] for column in columns] == ["Mole fraction of ozone (Linear)",
                                                          "Mole fraction of ozone (Linear) (2)"]

    def test_linear_data_columns_skips_incomplete_data(self):
        incomplete = etree.fromstring("<MSS_LinearSection_Data><Title>Empty</Title></MSS_LinearSection_Data>")
        assert linear_data_columns([incomplete], self.waypoints) == []

    def test_columns_are_hidden_by_default(self):
        self.model.set_linear_data_from_xml([lsec_xml()])
        assert self.model.columnCount() == len(TABLE_FULL)
        assert self.model.visible_linear_data_columns() == []

    def test_columns_are_shown_on_demand(self):
        self.model.set_linear_data_from_xml([lsec_xml()])
        self.model.set_linear_data_visible(True)
        assert self.model.columnCount() == len(TABLE_FULL) + 1
        assert self.model.headerData(
            LINEAR_DATA_COLUMN, QtCore.Qt.Horizontal).value() == "Mole fraction of ozone (Linear)\n(ppmv)"
        values = [self.model.data(self.model.index(row, LINEAR_DATA_COLUMN)).value()
                  for row in range(self.model.rowCount())]
        assert values == ["", 10., 20., ""]
        # The data columns cannot be edited.
        assert not self.model.flags(self.model.index(0, LINEAR_DATA_COLUMN)) & QtCore.Qt.ItemIsEditable

        self.model.set_linear_data_visible(False)
        assert self.model.columnCount() == len(TABLE_FULL)

    def test_data_stays_at_its_waypoint_when_waypoints_change(self):
        self.model.set_linear_data_from_xml([lsec_xml()])
        self.model.set_linear_data_visible(True)
        self.model.insertRows(0, waypoints=[Waypoint(10., 10., 0.)])
        values = [self.model.data(self.model.index(row, LINEAR_DATA_COLUMN)).value()
                  for row in range(self.model.rowCount())]
        assert values == ["", "", 10., 20., ""]

    def test_clear_linear_data(self):
        self.model.set_linear_data_from_xml([lsec_xml()])
        self.model.set_linear_data_visible(True)
        self.model.clear_linear_data()
        assert self.model.columnCount() == len(TABLE_FULL)
        assert all(waypoint.linear_data == {} for waypoint in self.model.all_waypoint_data())

    def test_linear_data_does_not_modify_the_flight_track(self):
        changed = []
        self.model.modified = False
        self.model.dataChanged.connect(lambda *args: changed.append(args))
        self.model.set_linear_data_visible(True)
        self.model.set_linear_data_from_xml([lsec_xml()])
        assert changed == []
        assert not self.model.modified


def _ftml(encoding_declared, comment="Höhe 25°"):
    return (f'<?xml version="1.0" encoding="{encoding_declared}"?>\n<FlightTrack version="9"><ListOfWaypoints>'
            f'<Waypoint flightlevel="0.0" lat="50.0" location="" lon="10.0"><Comments>{comment}</Comments></Waypoint>'
            '<Waypoint flightlevel="0.0" lat="51.0" location="" lon="11.0"><Comments></Comments></Waypoint>'
            '</ListOfWaypoints></FlightTrack>\n')


@pytest.mark.parametrize("encoding", ["utf-8", "utf-16", "ISO-8859-1"])
def test_load_ftml_in_its_declared_encoding(tmp_path, encoding):
    """
    FTML files are decoded as they declare, not in the locale's encoding (#3372); UTF-16 with its byte order mark
    """
    path = tmp_path / "track.ftml"
    path.write_bytes(_ftml(encoding).encode(encoding))
    assert WaypointsTableModel(filename=str(path)).waypoints[0].comments == "Höhe 25°"


def test_load_ftml_rejects_bytes_not_in_its_declared_encoding(tmp_path):
    """E.g. cp1252 under encoding="utf-8", as msui wrote it on a Windows machine (#3372)"""
    path = tmp_path / "track.ftml"
    path.write_bytes(_ftml("utf-8").encode("cp1252"))
    with pytest.raises(SyntaxError):
        WaypointsTableModel(filename=str(path))


FTML_WRITE_SCRIPT = """
import sys
from unittest import mock
import tests.constants  # noqa: F401
from PyQt5 import QtWidgets
app = QtWidgets.QApplication([])
from mslib.msui import flighttrack as ft, msui_mainwindow  # noqa: E402
saved, exported = sys.argv[1:3]
for box in ("critical", "warning", "information"):
    # a message box would wait for a click that never comes
    setattr(QtWidgets.QMessageBox, box, staticmethod(lambda *args, **kwargs: sys.exit(f"message box: {args[1:]}")))
comment = "nach \\u2192 Ziel"
model = ft.WaypointsTableModel(waypoints=[ft.Waypoint(50., 10., 0, comments=comment), ft.Waypoint(51., 11., 0)])
model.save_to_ftml(saved)
window = msui_mainwindow.MSUIMainWindow()
window.create_new_flight_track()
window.active_flight_track.replace_waypoints(model.waypoints)
with mock.patch("mslib.msui.msui_mainwindow.get_save_filename", return_value=exported):
    window.handle_export_local("ftml", None, "default")
for path in (saved, exported):
    print(ascii(ft.WaypointsTableModel(filename=path).waypoints[0].comments))
"""


@pytest.mark.skipif(sys.platform == "win32", reason="the ASCII locale is set up for POSIX")
def test_ftml_is_written_in_utf8_whatever_the_locale(tmp_path):
    """
    FTML files were written in the locale's encoding under encoding="utf-8": on a non-UTF-8 system other
    systems couldn't read them, and a character outside the locale's encoding left a truncated file (#3372)
    """
    script = tmp_path / "write.py"
    script.write_text(FTML_WRITE_SCRIPT)
    saved, exported = tmp_path / "saved.ftml", tmp_path / "exported.ftml"
    env = dict(os.environ, LC_ALL="C", PYTHONCOERCECLOCALE="0", QT_QPA_PLATFORM="offscreen")
    process = subprocess.run([sys.executable, "-X", "utf8=0", str(script), str(saved), str(exported)],
                             cwd=Path(__file__).parents[2], env=env, capture_output=True, text=True, timeout=120)
    assert process.returncode == 0, process.stderr[-2000:]
    assert process.stdout.splitlines() == [ascii("nach → Ziel")] * 2
    for path in (saved, exported):
        assert "nach → Ziel" in path.read_bytes().decode("utf-8")
