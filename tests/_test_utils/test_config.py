# -*- coding: utf-8 -*-
"""

    tests._test_utils.test_config
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to test mslib.utils.config

    This file is part of MSS.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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

import pytest
from pathlib import Path

from mslib import utils
from mslib.utils import constants
from mslib.utils.config import MSUIDefaultConfig as mss_default
from mslib.utils.config import config_loader, read_config_file, modify_config_file
from mslib.utils.config import merge_dict
from tests.constants import MSUI_CONFIG_PATH, MSUI_CONFIG_FILE_PATH
from tests.utils import create_msui_settings_file

LOGGER = logging.getLogger(__name__)


class TestSettingsSave:
    """
    tests save_settings_qsettings and load_settings_qsettings from ./utils.py
    # TODO make sure do a clean setup, not inside the 'msui' config file.
    """
    tag = "test_automated"

    def test_save_settings(self):
        settings = {'foo': 'bar'}
        config.save_settings_qsettings(self.tag, settings)

    def test_load_settings(self):
        settings = {'foo': 'bar'}
        config.save_settings_qsettings(self.tag, settings)
        settings = config.load_settings_qsettings(self.tag)
        assert isinstance(settings, dict)
        assert settings["foo"] == "bar"


class TestConfigLoader:
    """
    tests config file for client
    """

    def setup_method(self):
        self.sample_path = Path(__file__).parent.parent / 'data'

    def teardown_method(self):
        if MSUI_CONFIG_FILE_PATH.exists():
            MSUI_CONFIG_FILE_PATH.unlink()

        config_file = MSUI_CONFIG_PATH / 'empty_msui_settings.json'
        if config_file.exists() is False:
            config_file.write_text("{}")
        read_config_file(str(config_file))

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
        config_file = self.sample_path / 'msui_settings.json'
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
        file_content = MSUI_CONFIG_FILE_PATH.read_text()
        assert ":" not in file_content
        default_data = config_loader(default=True)
        read_config_file(path=str(MSUI_CONFIG_FILE_PATH))
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
        file_content = MSUI_CONFIG_FILE_PATH.read_text()
        assert "num_labels" not in file_content
        default_data = config_loader(default=True)
        config_file = MSUI_CONFIG_FILE_PATH
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
        file_content = MSUI_CONFIG_FILE_PATH.read_text()
        assert "num_labels" in file_content
        config_file = MSUI_CONFIG_FILE_PATH
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
        file_content = MSUI_CONFIG_FILE_PATH.read_text()
        assert "num_interpolation_points" in file_content
        config_file = MSUI_CONFIG_FILE_PATH
        with pytest.raises(utils.FatalUserError):
            read_config_file(path=config_file)

        create_msui_settings_file('{"": 201, "num_labels": 10 }')
        file_content = MSUI_CONFIG_FILE_PATH.read_text()
        assert "num_labels" in file_content
        with pytest.raises(utils.FatalUserError):
            read_config_file(path=config_file)

    def test_deprecated_mss_dir_key_is_migrated(self):
        """
        an old msui_settings.json using the removed 'mss_dir' key gets migrated to
        'mscolab_local_data_dir', with the original file kept as a .bak backup
        """
        create_msui_settings_file('{"mss_dir": "/tmp/legacy_dir"}')
        config_file = MSUI_CONFIG_FILE_PATH
        read_config_file(path=config_file)
        assert config_loader(dataset="mscolab_local_data_dir") == "/tmp/legacy_dir"
        file_content = config_file.read_text()
        assert '"mss_dir"' not in file_content
        backup = config_file.with_suffix(".bak")
        assert backup.exists()
        assert '"mss_dir": "/tmp/legacy_dir"' in backup.read_text()
        backup.unlink()

    def test_deprecated_mss_dir_key_does_not_override_new_key(self):
        """
        if both the old and new key are present, the explicit new key wins
        """
        create_msui_settings_file(
            '{"mss_dir": "/tmp/legacy_dir", "mscolab_local_data_dir": "/tmp/new_dir"}')
        config_file = MSUI_CONFIG_FILE_PATH
        read_config_file(path=config_file)
        assert config_loader(dataset="mscolab_local_data_dir") == "/tmp/new_dir"
        config_file.with_suffix(".bak").unlink()

    def test_modify_config_file_with_empty_parameters(self):
        """
        Test to check if modify_config_file properly stores a key-value pair in an empty config file
        """
        data_to_save_in_config_file = {
            "num_labels": 20
        }
        modify_config_file(data_to_save_in_config_file)
        config_file = MSUI_CONFIG_FILE_PATH
        read_config_file(path=config_file)
        data = config_loader()
        assert data["num_labels"] == 20

    def test_modify_config_file_with_existing_parameters(self):
        """
        Test to check if modify_config_file properly modifies a key-value pair in the config file
        """
        create_msui_settings_file('{"num_labels": 14}')
        data_to_save_in_config_file = {
            "num_labels": 20
        }
        modify_config_file(data_to_save_in_config_file)
        config_file = MSUI_CONFIG_FILE_PATH
        read_config_file(path=config_file)
        data = config_loader()
        assert data["num_labels"] == 20

    def test_modify_config_file_with_invalid_parameters(self):
        """
        Test to check if modify_config_file raises a KeyError when a key is empty
        """
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

    def test_user_option_with_path(self):
        """
        An option whose default is a plain string takes any string, a path included.
        The flight track of an "automated_plotting_flights" entry is stored as path
        + file name, its default is "".
        """
        users_options_dict = {
            "automated_plotting_flights": [["flight1", "01 SADPAP (stereo)", "", "/home/mss/example.ftml", "", ""]],
        }
        changed_dict = merge_dict(self.default_dict, users_options_dict)
        assert changed_dict["automated_plotting_flights"] == [
            ["flight1", "01 SADPAP (stereo)", "", "/home/mss/example.ftml", "", ""]]

    def test_path_option_needs_a_path(self):
        """
        An option whose default is a path keeps requiring one, a relative directory
        is not taken over.
        """
        assert self.default_dict["data_dir"] == str(constants.MSUI_DOCUMENTS_PATH)
        users_options_dict = {"data_dir": "/home/mss/mssdata", "wms_cache": "wms_cache"}
        changed_dict = merge_dict(self.default_dict, users_options_dict)
        assert changed_dict["data_dir"] == "/home/mss/mssdata"
        assert changed_dict["wms_cache"] == str(constants.MSUI_CACHE_PATH / "wms_cache")

    def test_url_option_needs_a_url(self):
        """
        An option whose default is a url keeps requiring one, a path is not taken over.
        A plain string stays accepted, e.g. a server which is named without a scheme.
        """
        users_options_dict = {"default_WMS": ["/home/mss/wms"], "default_VSEC_WMS": ["localhost:8081"]}
        changed_dict = merge_dict(self.default_dict, users_options_dict)
        assert changed_dict["default_WMS"] == self.default_dict["default_WMS"]
        assert changed_dict["default_VSEC_WMS"] == ["localhost:8081"]
