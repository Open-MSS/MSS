# -*- coding: utf-8 -*-
"""

    mslib.utils.config
    ~~~~~~~~~~~~~~

    Collection of utility routines for the Mission Support System.

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

import copy
import json
import logging
import fs

from mslib.utils import FatalUserError
from mslib.msui import constants, MissionSupportSystemDefaultConfig
from mslib.support.qt_json_view.datatypes import match_type, UrlType, StrType


# system default options as dictionary
default_options = dict(MissionSupportSystemDefaultConfig.__dict__)
for key in ["__module__", "__doc__", "__dict__", "__weakref__", "config_descriptions"]:
    del default_options[key]

# user options as dictionary
user_options = copy.deepcopy(default_options)

# Dictionary options with fixed key/value pairs
fixed_dict_options = ["layout", "wms_prefetch", "topview", "sideview", "linearview"]

# Fixed key/value pair options
key_value_options = [
    'filepicker_default',
    'mss_dir',
    'data_dir',
    'num_labels',
    'num_interpolation_points',
    'new_flighttrack_flightlevel',
    'MSCOLAB_mailid',
    'MSCOLAB_password',
    'mscolab_server_url',
    'wms_cache',
    'wms_cache_max_size_bytes',
    'wms_cache_max_age_seconds',
    'WMS_request_timeout',
]

# Dictionary options with predefined structure
dict_option_structure = {
    "predefined_map_sections": {
        "new_map_section": {
            "CRS": "crs_value",
            "map": {
                "llcrnrlon": 0.0,
                "llcrnrlat": 0.0,
                "urcrnrlon": 0.0,
                "urcrnrlat": 0.0,
            },
        }
    },
    "MSC_login": {
        "http://www.your-mscolab-server.de": ["yourusername", "yourpassword"],
    },
    "WMS_login": {
        "http://www.your-wms-server.de": ["yourusername", "yourpassword"],
    },
    "locations": {
        "new-location": [0.0, 0.0],
    },
    "export_plugins": {
        "plugin-name": ["extension", "module", "function", "default"],
    },
    "import_plugins": {
        "plugin-name": ["extension", "module", "function", "default"],
    },
    "proxies": {
        "https": "https://proxy.com",
    },
}

# List options with predefined structure
list_option_structure = {
    "default_WMS": ["https://wms-server-url.com"],
    "default_VSEC_WMS": ["https://vsec-wms-server-url.com"],
    "default_LSEC_WMS": ["https://lsec-wms-server-url.com"],
    "default_MSCOLAB": ["https://mscolab-server-url.com"],
    "new_flighttrack_template": ["new-location"],
    "gravatar_ids": ["example@email.com"],
    "WMS_preload": ["https://wms-preload-url.com"],
}


def dict_raise_on_duplicates_empty(ordered_pairs):
    """Reject duplicate and empty keys."""
    accepted = {}
    for key, value in ordered_pairs:
        if key in accepted:
            raise ValueError(f"duplicate key found: {key}")
        elif key == "":
            raise ValueError("empty key found")
        else:
            accepted[key] = value
    return accepted


def read_config_file(path=constants.MSS_SETTINGS):
    """
    reads a config file

    Args:
        config_file: name of config file

    Returns: a dictionary
    """
    # path = constants.MSS_SETTINGS
    path = path.replace("\\", "/")
    dir_name, file_name = fs.path.split(path)
    json_file_data = {}
    error_message = ""
    with fs.open_fs(dir_name) as _fs:
        if _fs.exists(file_name):
            file_content = _fs.readtext(file_name)
            try:
                json_file_data = json.loads(file_content, object_pairs_hook=dict_raise_on_duplicates_empty)
            except json.JSONDecodeError as e:
                logging.error(f"Error while loading json file {e}")
                error_message = f"Unexpected error while loading config\n{e}"
                raise FatalUserError(error_message)
            except ValueError as e:
                logging.error(f"Error while loading json file {e}")
                error_message = f"Invalid keys detected in config\n{e}"
                raise FatalUserError(error_message)
        else:
            error_message = f"MSS config File '{path}' not found"
            raise FatalUserError(error_message)

    global user_options
    if json_file_data:
        user_options = merge_data(copy.deepcopy(user_options), json_file_data)
        logging.info("Merged default and user settings")
    else:
        user_options = copy.deepcopy(user_options)
        logging.info("No user settings found, using default settings")


def config_loader(dataset=None, default=False):
    """
    Function for loading json config data

    Args:
        config_file: json file, parameters for initializing mss,
        dataset: section to pull from json file

    Returns: a the dataset value or the config as dictionary

    """
    global user_options
    if dataset is not None and dataset not in user_options:
        raise KeyError(f"requested dataset '{dataset}' not in defaults!")
    if dataset is not None:
        if default:
            return default_options[dataset]
        return user_options[dataset]
    else:
        if default:
            return default_options
        return user_options


def compare_data(default, user_data):
    """
    Recursively compares two dictionaries based on qt_json_view datatypes
    and returns default or user_data appropriately.

    Arguments:
    default -- Dict to return if datatype not matching
    user_data -- Dict to return if datatype is matching
    """
    # If data is neither list not dict type, compare individual type
    if not isinstance(default, dict) and not isinstance(default, list):
        if isinstance(default, float) and isinstance(user_data, int):
            user_data = float(default)
        if isinstance(match_type(default), UrlType) and isinstance(match_type(user_data), StrType):
            return user_data, True
        if isinstance(match_type(default), type(match_type(user_data))):
            return user_data, True
        else:
            return default, False

    data = copy.deepcopy(default)
    trues = []
    # If data is list type, compare all values in list
    if isinstance(default, list):
        if isinstance(user_data, list):
            if len(default) == len(user_data):
                for i in range(len(default)):
                    data[i], match = compare_data(default[i], user_data[i])
                    trues.append(match)
            else:
                return default, False
        else:
            return default, False

    # If data is dict type, goes through the dict and update
    elif isinstance(default, dict):
        for key in default:
            if key in user_data:
                data[key], match = compare_data(default[key], user_data[key])
                trues.append(match)
            else:
                trues.append(False)

    return data, all(trues)


def merge_data(options, json_file_data):
    """
    Merge two dictionaries by comparing all the options from
    the MissionSupportSystemDefaultConfig class

    Arguments:
    options -- Dict to merge options into
    json_file_data -- Dict with new values
    """
    # Check if dictionary options with fixed key/value pairs match data types from default
    for key in fixed_dict_options:
        if key in json_file_data:
            options[key] = compare_data(options[key], json_file_data[key])[0]

    # Check if dictionary options with predefined structure match data types from default
    dos = copy.deepcopy(dict_option_structure)
    # adding plugin structure : ["extension", "module", "function"] to
    # recognize user plugin options that don't have the optional filepicker option set
    dos["import_plugins"]["plugin-name-a"] = dos["import_plugins"]["plugin-name"][:3]
    dos["export_plugins"]["plugin-name-a"] = dos["export_plugins"]["plugin-name"][:3]
    for key in dos:
        if key in json_file_data:
            temp_data = {}
            for option_key in json_file_data[key]:
                for dos_key_key in dos[key]:
                    # if isinstance(match_type(option_key), type(match_type(dos_key_key))):
                    data, match = compare_data(dos[key][dos_key_key], json_file_data[key][option_key])
                    if match:
                        temp_data[option_key] = json_file_data[key][option_key]
                        break
            if temp_data != {}:
                options[key] = temp_data

    # add filepicker default to import plugins if missing
    for plugin in options["import_plugins"]:
        if len(options["import_plugins"][plugin]) == 3:
            options["import_plugins"][plugin].append("default")

    # add filepicker default to export plugins if missing
    for plugin in options["export_plugins"]:
        if len(options["export_plugins"][plugin]) == 3:
            options["export_plugins"][plugin].append("default")

    # Check if list options with predefined structure match data types from default
    los = copy.deepcopy(list_option_structure)
    for key in los:
        if key in json_file_data:
            temp_data = []
            for i in range(len(json_file_data[key])):
                for los_key_item in los[key]:
                    data, match = compare_data(los_key_item, json_file_data[key][i])
                    if match:
                        temp_data.append(data)
                        break
            if temp_data != []:
                options[key] = temp_data

    # Check if options with fixed key/value pair structure match data types from default
    for key in key_value_options:
        if key in json_file_data:
            data, match = compare_data(options[key], json_file_data[key])
            if match:
                options[key] = data

    return options
