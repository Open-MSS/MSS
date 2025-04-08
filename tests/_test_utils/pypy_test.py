# -*- coding: utf-8 -*-
"""
    tests._test_utils.test_config
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    This module provides pytest functions to test mslib.utils.config.

    This file is part of MSS.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2025 by the MSS team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.
"""
import logging
import mslib.utils.config as config
import os
import fs
import pytest

from mslib import utils
from mslib.utils.config import (
    MSUIDefaultConfig as mss_default,
    config_loader, read_config_file, modify_config_file, merge_dict, compare_data
)
from tests.constants import MSUI_CONFIG_PATH
from tests.utils import create_msui_settings_file

LOGGER = logging.getLogger(__name__)


class TestConfigLoader:
    """Tests for the config file loader"""

    def setup_method(self):
        self.sample_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data")

    def teardown_method(self):
        if fs.open_fs(MSUI_CONFIG_PATH).exists("msui_settings.json"):
            fs.open_fs(MSUI_CONFIG_PATH).remove("msui_settings.json")

    def test_option_types(self):
        """Check if all config options are added to the appropriate type categories"""
        config_keys = set(config_loader(default=True).keys())
        option_types = set(
            mss_default.fixed_dict_options +
            mss_default.key_value_options +
            list(mss_default.dict_option_structure.keys()) +
            list(mss_default.list_option_structure.keys())
        )
        assert config_keys == option_types

    def test_default_config(self):
        """Ensure default config is loaded properly"""
        data = config_loader(default=True)
        assert isinstance(data, dict)
        assert data["num_labels"] == 10
        assert data["num_interpolation_points"] == 201

    def test_existing_config_file_different_parameters(self):
        """Ensure missing keys fallback to default values"""
        create_msui_settings_file('{"num_interpolation_points": 20}')
        read_config_file(path=os.path.join(MSUI_CONFIG_PATH, "msui_settings.json"))
        data = config_loader()

        assert data["num_labels"] == 10  # Default value
        assert data["num_interpolation_points"] == 20  # Updated from file

    def test_modify_config_file_with_empty_parameters(self):
        """Ensure modifying an empty config file properly stores values"""
        modify_config_file({"num_labels": 20})
        read_config_file(path=os.path.join(MSUI_CONFIG_PATH, "msui_settings.json"))
        data = config_loader()

        assert data["num_labels"] == 20

    def test_modify_config_file_with_existing_parameters(self):
        """Ensure modifying an existing config file updates the values correctly"""
        create_msui_settings_file('{"num_labels": 14}')
        modify_config_file({"num_labels": 20})
        read_config_file(path=os.path.join(MSUI_CONFIG_PATH, "msui_settings.json"))
        data = config_loader()

        assert data["num_labels"] == 20


class TestCompareData:
    """Tests for compare_data function"""

    def test_compare_data_update(self):
        """Test that compare_data detects a change in values"""
        assert compare_data(
            {"new_flighttrack_flightlevel": 250},
            {"new_flighttrack_flightlevel": 25}
        ) == ({"new_flighttrack_flightlevel": 25}, True)

    def test_compare_data_no_change(self):
        """Test that compare_data correctly identifies no change"""
        assert compare_data(
            {"new_flighttrack_flightlevel": 250},
            {"new_flighttrack_flightlevel": 250}
        ) == ({}, False)

    def test_compare_data_add_new_key(self):
        """Test that compare_data detects a new key"""
        assert compare_data(
            {"existing_key": 100},
            {"existing_key": 100, "new_key": 200}
        ) == ({"new_key": 200}, True)

    def test_compare_data_remove_key(self):
        """Test that compare_data detects a removed key"""
        assert compare_data(
            {"existing_key": 100, "removed_key": 50},
            {"existing_key": 100}
        ) == ({}, True)  # A removed key should still trigger a change

    def test_compare_data_fails_on_invalid_types(self):
        """Test that compare_data fails on invalid types"""
        with pytest.raises(TypeError):
            compare_data({"valid_key": 100}, "invalid_string")


class TestMergeDict:
    """Tests for merge_dict function"""

    def setup_method(self):
        self.default_dict = dict(mss_default.__dict__)

    def test_no_differences(self):
        """Ensure merge_dict correctly merges identical dictionaries"""
        users_options_dict = self.default_dict
        assert merge_dict(self.default_dict, users_options_dict) == self.default_dict
        assert merge_dict(self.default_dict, {}) == self.default_dict

    def test_user_option_changed(self):
        """Ensure merge_dict updates existing options correctly"""
        users_options_dict = {
            "new_flighttrack_template": ["Kona", "Anchorage"],
            "new_flighttrack_flightlevel": 350,
        }
        changed_dict = merge_dict(self.default_dict, users_options_dict)

        assert changed_dict["num_interpolation_points"] == 201  # Unchanged
        assert changed_dict["new_flighttrack_template"] == ["Kona", "Anchorage"]
        assert changed_dict["new_flighttrack_flightlevel"] == 350

    def test_user_unknown_option(self):
        """Ensure merge_dict skips unknown options"""
        users_options_dict = {"unknown_option": 1}
        changed_dict = merge_dict(self.default_dict, users_options_dict)

        assert "unknown_option" not in changed_dict  # Should be ignored
        assert changed_dict["num_interpolation_points"] == 201  # Unchanged

    def test_add_filepicker_default_to_plugins(self):
        """Ensure 'default' is added to export_plugins"""
        users_options_dict = {"export_plugins": {"Text": ["txt", "mslib.plugins.io.text", "save_to_txt"]}}
        changed_dict = merge_dict(self.default_dict, users_options_dict)

        assert changed_dict["export_plugins"]["Text"] == ["txt", "mslib.plugins.io.text", "save_to_txt", "default"]
