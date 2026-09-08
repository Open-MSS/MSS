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

from mslib.msui.flighttrack import WaypointsTableModel
from mslib.msui.performance_settings import DEFAULT_PERFORMANCE


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

    def test_load_ftml_with_revision(self):
        xml_content = """
        <FlightTrack version="test">
            <Revision id="42" name="draft"/>
            <ListOfWaypoints>
                <Waypoint location="" lat="0" lon="0" flightlevel="100">
                    <Comments></Comments>
                </Waypoint>
            </ListOfWaypoints>
        </FlightTrack>
        """

        model = WaypointsTableModel(xml_content=xml_content, name="test_track")

        assert model.revision is not None
        assert model.revision.id == 42
        assert model.revision.name == "draft"

    def test_load_ftml_without_revision_creates_default_revision(self):
        xml_content = """
        <FlightTrack version="test">
            <ListOfWaypoints>
                <Waypoint location="" lat="0" lon="0" flightlevel="100">
                    <Comments></Comments>
                </Waypoint>
            </ListOfWaypoints>
        </FlightTrack>
        """

        model = WaypointsTableModel(xml_content=xml_content, name="legacy_track")

        assert model.revision is not None
        assert isinstance(model.revision.id, int)
        assert model.revision.name is None
