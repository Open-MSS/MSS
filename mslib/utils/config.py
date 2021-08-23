# -*- coding: utf-8 -*-
"""

    mslib.utils.config
    ~~~~~~~~~~~~~~~~

    Collection of functions all around config handling.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
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


import json
import logging
import os
from fs import open_fs, errors
import sys
from PyQt5 import QtCore

from mslib.msui import constants, MissionSupportSystemDefaultConfig
from mslib.utils import FatalUserError


def read_config_file(config_file=None):
    """
    reads a config file

    Args:
        config_file: name of config file

    Returns: a dictionary
    """
    user_config = {}
    if config_file is not None:
        _dirname, _name = os.path.split(config_file)
        _fs = open_fs(_dirname)
        try:
            with _fs.open(_name, 'r') as source:
                user_config = json.load(source)
        except errors.ResourceNotFound:
            error_message = f"MSS config File '{config_file}' not found"
            raise FatalUserError(error_message)
        except ValueError as ex:
            error_message = f"MSS config File '{config_file}' has a syntax error:\n\n'{ex}'"
            raise FatalUserError(error_message)
    return user_config


def config_loader(config_file=None, dataset=None):
    """
    Function for loading json config data

    Args:
        config_file: json file, parameters for initializing mss,
        dataset: section to pull from json file

    Returns: a the dataset value or the config as dictionary

    """
    default_config = dict(MissionSupportSystemDefaultConfig.__dict__)
    if dataset is not None and dataset not in default_config:
        raise KeyError(f"requested dataset '{dataset}' not in defaults!")
    if config_file is None:
        config_file = constants.CACHED_CONFIG_FILE
    if config_file is None:
        logging.info(
            'Default MSS configuration in place, no user settings, see http://mss.rtfd.io/en/stable/usage.html')
        if dataset is None:
            return default_config
        else:
            return default_config[dataset]
    user_config = read_config_file(config_file)
    if dataset is not None:
        return user_config.get(dataset, default_config[dataset])
    else:
        default_config.update(user_config)
        return default_config


def save_settings_qsettings(tag, settings, ignore_test=False):
    """
    Saves a dictionary settings to disk.

    :param tag: string specifying the settings
    :param settings: dictionary of settings
    :return: None
    """
    assert isinstance(tag, str)
    assert isinstance(settings, dict)
    if not ignore_test and "pytest" in sys.modules:
        return settings

    q_settings = QtCore.QSettings("mss", "mss-core")
    file_path = q_settings.fileName()
    logging.debug("storing settings for %s to %s", tag, file_path)
    try:
        q_settings.setValue(tag, QtCore.QVariant(settings))
    except (OSError, IOError) as ex:
        logging.warning("Problems storing %s settings (%s: %s).", tag, type(ex), ex)
    return settings


def load_settings_qsettings(tag, default_settings=None, ignore_test=False):
    """
    Loads a dictionary of settings from disk. May supply a dictionary of default settings
    to return in case the settings file is not present or damaged. The default_settings one will
    be updated by the restored one so one may rely on all keys of the default_settings dictionary
    being present in the returned dictionary.

    :param tag: string specifying the settings
    :param default_settings: dictionary of settings or None
    :return: dictionary of settings
    """
    if default_settings is None:
        default_settings = {}
    assert isinstance(default_settings, dict)
    if not ignore_test and "pytest" in sys.modules:
        return default_settings

    settings = {}
    q_settings = QtCore.QSettings("mss", "mss-core")
    file_path = q_settings.fileName()
    logging.debug("loading settings for %s from %s", tag, file_path)
    try:
        settings = q_settings.value(tag)
    except Exception as ex:
        logging.error("Problems reloading stored %s settings (%s: %s). Switching to default",
                      tag, type(ex), ex)
    if isinstance(settings, dict):
        default_settings.update(settings)
    return default_settings
