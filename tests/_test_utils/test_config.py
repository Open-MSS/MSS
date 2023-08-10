# -*- coding: utf-8 -*-
"""

    tests._test_utils.test_config
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to test mslib.utils.config

    This file is part of MSS.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2023 by the MSS team, see AUTHORS.
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
import logging
import mslib.utils.config as config
import os
import fs
import pytest

from mslib import utils
from mslib.utils.config import MSUIDefaultConfig as mss_default
from mslib.utils.config import config_loader, read_config_file, modify_config_file
from mslib.utils.config import merge_dict
from tests.constants import MSUI_CONFIG_PATH
from tests.utils import create_msui_settings_file

LOGGER = logging.getLogger(__name__)


class TestSettingsSave(object):
    """
    tests save_settings_qsettings and load_settings_qsettings from ./utils.py
    # TODO make sure do a clean setup, not inside the 'msui' config file.
    """
    tag = "test_automated"

    def test_save_settings(self):
        settings = {'foo': 'bar'}
        config.save_settings_qsettings(self.tag, settings, ignore_test=True)

    def test_load_settings(self):
        settings = {'foo': 'bar'}
        config.save_settings_qsettings(self.tag, settings, ignore_test=True)
        settings = config.load_settings_qsettings(self.tag, ignore_test=True)
        assert isinstance(settings, dict)
        assert settings["foo"] == "bar"


class TestConfigLoader(object):
    """
    tests config file for client
    """

    def setup_method(self):
        self.sample_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../data')

    def teardown_method(self):
        if fs.open_fs(MSUI_CONFIG_PATH).exists("msui_settings.json"):
            fs.open_fs(MSUI_CONFIG_PATH).remove("msui_settings.json")
        config_file = os.path.join(
            self.sample_path,
            'empty_msui_settings.json'
        )
        read_config_file(config_file)

    def test_option_types(self):
        # check if all config options are added to the appropriate type of options
        config_keys = set(config_loader(default=True).keys())
        option_types = set(mss_default.fixed_dict_options +
                           mss_default.key_value_options +
                           list(mss_default.dict_option_structure.keys()) +
                           list(mss_default.list_option_structure.keys()))
        assert config_keys == option_types

    def test_default_config(self):
        data = config_loader(default=True)
        assert isinstance(data, dict)
        assert data == config_loader(default=True)
        assert data["num_labels"] == 10
        assert data["num_interpolation_points"] == 201

    def test_default_config_dataset(self):
        default_data = config_loader(default=True)
        num_labels = config_loader(dataset="num_labels", default=True)
        assert num_labels == default_data["num_labels"]

    def test_default_config_wrong_file(self):
        # return default if no access to config file given
        with pytest.raises(FileNotFoundError):
            read_config_file(path="foo.json")

    def test_sample_config_file(self):
        config_file = os.path.join(
            self.sample_path,
            'msui_settings.json',
        )
        read_config_file(path=config_file)
        data = config_loader(dataset="new_flighttrack_flightlevel")
        assert data == 250
        with pytest.raises(KeyError):
            config_loader(dataset="UNDEFINED")
        with pytest.raises(KeyError):
            assert config_loader(dataset="UNDEFINED")

    def test_existing_empty_config_file(self):
        """
        on a user defined empty msui_settings_json this test should return the default value for num_labels
        """
        create_msui_settings_file('{ }')
        if not fs.open_fs(MSUI_CONFIG_PATH).exists("msui_settings.json"):
            pytest.skip('undefined test msui_settings.json')
        with fs.open_fs(MSUI_CONFIG_PATH) as file_dir:
            file_content = file_dir.readtext("msui_settings.json")
        assert ":" not in file_content
        default_data = config_loader(default=True)
        config_file = fs.path.combine(MSUI_CONFIG_PATH, "msui_settings.json")
        read_config_file(path=config_file)
        data = config_loader()
        assert data["num_labels"] == default_data["num_labels"]
        num_labels = config_loader(dataset="num_labels")
        assert num_labels == default_data["num_labels"]
        with pytest.raises(KeyError):
            config_loader(dataset="UNDEFINED")
        with pytest.raises(KeyError):
            assert config_loader(dataset="UNDEFINED")

    def test_existing_config_file_different_parameters(self):
        """
        on a user defined msui_settings_json without a defined num_labels this test should return its default value
        """
        create_msui_settings_file('{"num_interpolation_points": 20 }')
        if not fs.open_fs(MSUI_CONFIG_PATH).exists("msui_settings.json"):
            pytest.skip('undefined test msui_settings.json')
        with fs.open_fs(MSUI_CONFIG_PATH) as file_dir:
            file_content = file_dir.readtext("msui_settings.json")
        assert "num_labels" not in file_content
        default_data = config_loader(default=True)
        config_file = fs.path.combine(MSUI_CONFIG_PATH, "msui_settings.json")
        read_config_file(path=config_file)
        data = config_loader()
        assert data["num_labels"] == default_data["num_labels"]
        num_labels = config_loader(dataset="num_labels")
        assert num_labels == default_data["num_labels"]
        num_interpolation_points = config_loader(dataset="num_interpolation_points")
        assert num_interpolation_points == 20
        assert data["num_interpolation_points"] == 20
        with pytest.raises(KeyError):
            config_loader(dataset="UNDEFINED")
        with pytest.raises(KeyError):
            assert config_loader(dataset="UNDEFINED")

    def test_existing_config_file_defined_parameters(self):
        """
        on a user defined msui_settings_json without a defined num_labels this test should return its default value
        """
        create_msui_settings_file('{"num_interpolation_points": 201, "num_labels": 10 }')
        if not fs.open_fs(MSUI_CONFIG_PATH).exists("msui_settings.json"):
            pytest.skip('undefined test msui_settings.json')
        with fs.open_fs(MSUI_CONFIG_PATH) as file_dir:
            file_content = file_dir.readtext("msui_settings.json")
        assert "num_labels" in file_content
        config_file = fs.path.combine(MSUI_CONFIG_PATH, "msui_settings.json")
        read_config_file(path=config_file)
        num_labels = config_loader(dataset="num_labels")
        assert num_labels == 10
        with pytest.raises(KeyError):
            config_loader(dataset="UNDEFINED")
        with pytest.raises(KeyError):
            assert config_loader(dataset="UNDEFINED")

    def test_existing_config_file_invalid_parameters(self):
        """
        on a user defined msui_settings_json with duplicate and empty keys should raise FatalUserError
        """
        create_msui_settings_file('{"num_interpolation_points": 201, "num_interpolation_points": 10 }')
        if not fs.open_fs(MSUI_CONFIG_PATH).exists("msui_settings.json"):
            pytest.skip('undefined test msui_settings.json')
        with fs.open_fs(MSUI_CONFIG_PATH) as file_dir:
            file_content = file_dir.readtext("msui_settings.json")
        assert "num_interpolation_points" in file_content
        config_file = fs.path.combine(MSUI_CONFIG_PATH, "msui_settings.json")
        with pytest.raises(utils.FatalUserError):
            read_config_file(path=config_file)

        create_msui_settings_file('{"": 201, "num_labels": 10 }')
        if not fs.open_fs(MSUI_CONFIG_PATH).exists("msui_settings.json"):
            pytest.skip('undefined test msui_settings.json')
        with fs.open_fs(MSUI_CONFIG_PATH) as file_dir:
            file_content = file_dir.readtext("msui_settings.json")
        assert "num_labels" in file_content
        with pytest.raises(utils.FatalUserError):
            read_config_file(path=config_file)

    def test_modify_config_file_with_empty_parameters(self):
        """
        Test to check if modify_config_file properly stores a key-value pair in an empty config file
        """
        create_msui_settings_file('{ }')
        if not fs.open_fs(MSUI_CONFIG_PATH).exists("msui_settings.json"):
            pytest.skip('undefined test msui_settings.json')
        data_to_save_in_config_file = {
            "num_labels": 20
        }
        modify_config_file(data_to_save_in_config_file)
        config_file = fs.path.combine(MSUI_CONFIG_PATH, "msui_settings.json")
        read_config_file(path=config_file)
        data = config_loader()
        assert data["num_labels"] == 20

    def test_modify_config_file_with_existing_parameters(self):
        """
        Test to check if modify_config_file properly modifies a key-value pair in the config file
        """
        create_msui_settings_file('{"num_labels": 14}')
        if not fs.open_fs(MSUI_CONFIG_PATH).exists("msui_settings.json"):
            pytest.skip('undefined test msui_settings.json')
        data_to_save_in_config_file = {
            "num_labels": 20
        }
        modify_config_file(data_to_save_in_config_file)
        config_file = fs.path.combine(MSUI_CONFIG_PATH, "msui_settings.json")
        read_config_file(path=config_file)
        data = config_loader()
        assert data["num_labels"] == 20

    def test_modify_config_file_with_invalid_parameters(self):
        """
        Test to check if modify_config_file raises a KeyError when a key is empty
        """
        create_msui_settings_file('{ }')
        if not fs.open_fs(MSUI_CONFIG_PATH).exists("msui_settings.json"):
            pytest.skip('undefined test msui_settings.json')
        data_to_save_in_config_file = {
            "": "sree",
            "num_labels": "20"
        }
        with pytest.raises(KeyError):
            modify_config_file(data_to_save_in_config_file)


class TestMergeDict:
    """
    merge_dict can only merge keys which are predefined in the mss_default. All other have to be skipped
    """
    def setup_method(self):
        self.default_dict = dict(mss_default.__dict__)

    def test_no_differences(self):
        users_options_dict = self.default_dict
        assert merge_dict(self.default_dict, users_options_dict) == self.default_dict
        users_options_dict = {}
        assert merge_dict(self.default_dict, users_options_dict) == self.default_dict

    def test_user_option_changed(self):
        users_options_dict = {
            "new_flighttrack_template": ["Kona", "Anchorage"],
            "new_flighttrack_flightlevel": 350,
        }
        assert self.default_dict["num_interpolation_points"] == 201
        assert self.default_dict["new_flighttrack_template"] == ['Nagpur', 'Delhi']
        assert self.default_dict["new_flighttrack_flightlevel"] == 0
        changed_dict = merge_dict(self.default_dict, users_options_dict)
        assert changed_dict["num_interpolation_points"] == 201
        assert changed_dict["new_flighttrack_template"] == ["Kona", "Anchorage"]
        assert changed_dict["new_flighttrack_flightlevel"] == 350

    def test_user_unknown_option(self):
        users_options_dict = {"unknown_option": 1}
        changed_dict = merge_dict(self.default_dict, users_options_dict)
        assert changed_dict.get("num_interpolation_points") == 201
        assert changed_dict.get("unknown_option", None) is None

    def test_add_filepicker_default_to_plugins(self):
        users_options_dict = {"export_plugins": {"Text": ["txt", "mslib.plugins.io.text", "save_to_txt"]}}
        changed_dict = merge_dict(self.default_dict, users_options_dict)
        assert changed_dict["export_plugins"]["Text"] == ["txt", "mslib.plugins.io.text", "save_to_txt", "default"]
