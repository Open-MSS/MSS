# -*- coding: utf-8 -*-
"""

    mslib.utils._tests.test_config
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to test mslib.utils.config

    This file is part of mss.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2021 by the mss team, see AUTHORS.
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
from mslib.utils.config import config_loader, get_default_config, read_config_file
from mslib._tests.constants import MSS_CONFIG_PATH
from mslib._tests.utils import create_mss_settings_file

LOGGER = logging.getLogger(__name__)


class TestSettingsSave(object):
    """
    tests save_settings_qsettings and load_settings_qsettings from ./utils.py
    # TODO make sure do a clean setup, not inside the 'mss' config file.
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

    def teardown(self):
        if fs.open_fs(MSS_CONFIG_PATH).exists("mss_settings.json"):
            fs.open_fs(MSS_CONFIG_PATH).remove("mss_settings.json")

    def test_default_config(self):
        data = config_loader(default=True)
        assert isinstance(data, dict)
        assert data == get_default_config()
        assert data["num_labels"] == 10
        assert data["num_interpolation_points"] == 201

    def test_default_config_dataset(self):
        default_data = get_default_config()
        num_labels = config_loader(dataset="num_labels", default=True)
        assert num_labels == default_data["num_labels"]

    def test_default_config_wrong_file(self):
        # return default if no access to config file given
        with pytest.raises(utils.FatalUserError):
            read_config_file(path="foo.json")

    def test_sample_config_file(self):
        utils_path = os.path.dirname(os.path.abspath(utils.__file__))
        config_file = os.path.join(
            utils_path,
            '../',
            '../',
            'docs',
            'samples',
            'config',
            'mss',
            'mss_settings.json.sample',
        )
        read_config_file(path=config_file)
        data = config_loader(dataset="new_flighttrack_flightlevel")
        assert data == 250
        with pytest.raises(KeyError):
            config_loader(dataset="UNDEFINED")
        with pytest.raises(KeyError):
            assert config_loader(dataset="UNDEFINED")
        with pytest.raises(utils.FatalUserError):
            config_file = os.path.join(
                utils_path,
                '../',
                '../',
                'docs',
                'samples',
                'config',
                'mss',
                'non_existent_mss_settings.json.sample',
            )
            read_config_file(config_file)

    def test_existing_empty_config_file(self):
        """
        on a user defined empty mss_settings_json this test should return the default value for num_labels
        """
        create_mss_settings_file('{ }')
        if not fs.open_fs(MSS_CONFIG_PATH).exists("mss_settings.json"):
            pytest.skip('undefined test mss_settings.json')
        with fs.open_fs(MSS_CONFIG_PATH) as file_dir:
            file_content = file_dir.readtext("mss_settings.json")
        assert ":" not in file_content
        default_data = get_default_config()
        config_file = fs.path.combine(MSS_CONFIG_PATH, "mss_settings.json")
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
        on a user defined mss_settings_json without a defined num_labels this test should return its default value
        """
        create_mss_settings_file('{"num_interpolation_points": 20 }')
        if not fs.open_fs(MSS_CONFIG_PATH).exists("mss_settings.json"):
            pytest.skip('undefined test mss_settings.json')
        with fs.open_fs(MSS_CONFIG_PATH) as file_dir:
            file_content = file_dir.readtext("mss_settings.json")
        assert "num_labels" not in file_content
        default_data = get_default_config()
        config_file = fs.path.combine(MSS_CONFIG_PATH, "mss_settings.json")
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
        on a user defined mss_settings_json without a defined num_labels this test should return its default value
        """
        create_mss_settings_file('{"num_interpolation_points": 201, "num_labels": 10 }')
        if not fs.open_fs(MSS_CONFIG_PATH).exists("mss_settings.json"):
            pytest.skip('undefined test mss_settings.json')
        with fs.open_fs(MSS_CONFIG_PATH) as file_dir:
            file_content = file_dir.readtext("mss_settings.json")
        assert "num_labels" in file_content
        config_file = fs.path.combine(MSS_CONFIG_PATH, "mss_settings.json")
        read_config_file(path=config_file)
        num_labels = config_loader(dataset="num_labels")
        assert num_labels == 10
        with pytest.raises(KeyError):
            config_loader(dataset="UNDEFINED")
        with pytest.raises(KeyError):
            assert config_loader(dataset="UNDEFINED")

    def test_existing_config_file_invalid_parameters(self):
        """
        on a user defined mss_settings_json with duplicate and empty keys should raise FatalUserError
        """
        create_mss_settings_file('{"num_interpolation_points": 201, "num_interpolation_points": 10 }')
        if not fs.open_fs(MSS_CONFIG_PATH).exists("mss_settings.json"):
            pytest.skip('undefined test mss_settings.json')
        with fs.open_fs(MSS_CONFIG_PATH) as file_dir:
            file_content = file_dir.readtext("mss_settings.json")
        assert "num_interpolation_points" in file_content
        config_file = fs.path.combine(MSS_CONFIG_PATH, "mss_settings.json")
        with pytest.raises(utils.FatalUserError):
            read_config_file(path=config_file)

        create_mss_settings_file('{"": 201, "num_labels": 10 }')
        if not fs.open_fs(MSS_CONFIG_PATH).exists("mss_settings.json"):
            pytest.skip('undefined test mss_settings.json')
        with fs.open_fs(MSS_CONFIG_PATH) as file_dir:
            file_content = file_dir.readtext("mss_settings.json")
        assert "num_labels" in file_content
        with pytest.raises(utils.FatalUserError):
            read_config_file(path=config_file)
