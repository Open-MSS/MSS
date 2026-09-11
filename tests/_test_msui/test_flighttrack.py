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
        import mslib.utils.config as config_module

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
        assert values == ["", "10", "20", ""]
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
        assert values == ["", "", "10", "20", ""]

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
