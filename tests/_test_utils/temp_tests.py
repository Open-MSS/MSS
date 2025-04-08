# -*- coding: utf-8 -*-
"""
    tests._test_utils.test_config
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to test mslib.utils.config

    This file is part of MSS.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2025 by the MSS team, see AUTHORS.
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
import json
from mslib import utils
from mslib.utils.config import MSUIDefaultConfig as mss_default
from mslib.utils.config import config_loader, read_config_file, modify_config_file
from mslib.utils.config import merge_dict
from tests.constants import MSUI_CONFIG_PATH
from tests.utils import create_msui_settings_file

LOGGER = logging.getLogger(__name__)

@pytest.fixture
def temp_config_file(tmp_path):
    """Fixture to create a temporary config file for testing."""
    temp_file = tmp_path / "msui_settings.json"
    temp_file.write_text(json.dumps({"num_labels": 10}))  # Initial test value
    return str(temp_file)

def test_modify_config_file_with_existing_parameters(temp_config_file):
    """Test modifying an existing parameter in the config file."""
    data_to_save = {"num_labels": 20}
    
    modify_config_file(data_to_save, path=temp_config_file)
    
    read_config_file(temp_config_file)
    
    with fs.open_fs(str(temp_config_file).replace("/msui_settings.json", "")) as _fs:
        file_content = json.loads(_fs.readtext("msui_settings.json"))
    
    assert file_content["num_labels"] == 20, "Config file should update num_labels to 20"

def test_modify_config_file_with_empty_parameters(temp_config_file):
    """Test adding a new parameter when the config file is empty."""
    data_to_save = {"new_param": 42}
    
    modify_config_file(data_to_save, path=temp_config_file)
    
    read_config_file(temp_config_file)
    
    with fs.open_fs(str(temp_config_file).replace("/msui_settings.json", "")) as _fs:
        file_content = json.loads(_fs.readtext("msui_settings.json"))
    
    assert file_content["new_param"] == 42, "Config file should contain new_param with value 42"

def test_modify_config_file_with_invalid_parameters():
    """Test to check if modify_config_file raises a KeyError when a key is empty."""
    data_to_save = {"": "invalid", "num_labels": 20}
    with pytest.raises(KeyError):
        modify_config_file(data_to_save)

def test_existing_config_file_different_parameters():
    """Test handling of config files with different parameters."""
    create_msui_settings_file('{"num_interpolation_points": 20 }')
    read_config_file()
    data = config_loader()
    assert data["num_labels"] == mss_default.__dict__["num_labels"]
    assert data["num_interpolation_points"] == 20

def test_merge_dict_user_option_changed():
    """Test merge_dict function with user-modified options."""
    users_options_dict = {
        "new_flighttrack_template": ["Kona", "Anchorage"],
        "new_flighttrack_flightlevel": 350,
    }
    default_dict = dict(mss_default.__dict__)
    changed_dict = merge_dict(default_dict, users_options_dict)
    assert changed_dict["new_flighttrack_template"] == ["Kona", "Anchorage"]
    assert changed_dict["new_flighttrack_flightlevel"] == 350
