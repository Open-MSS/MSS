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

import sys
from PyQt5 import QtCore

import copy
import json
import logging
import fs
import os
import tempfile

from mslib.utils import FatalUserError
from mslib.msui import constants
from mslib.support.qt_json_view.datatypes import match_type, UrlType, StrType


class MissionSupportSystemDefaultConfig(object):
    """Central configuration for the Mission Support System User Interface
       Application (mss).

    DESCRIPTION:
    ============

    This file includes configuration settings central to the entire
    Mission Support User Interface (mss). Among others, define
     -- available map projections
     -- vertical section interpolation options
     -- the lists of predefined web service URLs
     -- predefined waypoints for the table view
    in this file.

    Do not change any value for good reasons.
    Your values can be set in your personal mss_settings.json file
    """
    # Default for general filepicker. Pick "default", "qt", or "fs"
    filepicker_default = "default"

    # dir where mss output files are stored
    data_dir = "~/mssdata"

    # layout of different views, with immutable they can't resized
    layout = {"topview": [963, 702],
              "sideview": [913, 557],
              "linearview": [913, 557],
              "tableview": [1236, 424],
              "immutable": False}

    # Predefined map regions to be listed in the corresponding topview combobox
    predefined_map_sections = {
        "01 Europe (cyl)": {"CRS": "EPSG:4326",
                            "map": {"llcrnrlon": -15.0, "llcrnrlat": 35.0,
                                    "urcrnrlon": 30.0, "urcrnrlat": 65.0}},
        "02 Germany (cyl)": {"CRS": "EPSG:4326",
                             "map": {"llcrnrlon": 5.0, "llcrnrlat": 45.0,
                                     "urcrnrlon": 15.0, "urcrnrlat": 57.0}},
        "03 Global (cyl)": {"CRS": "EPSG:4326",
                            "map": {"llcrnrlon": -180.0, "llcrnrlat": -90.0,
                                    "urcrnrlon": 180.0, "urcrnrlat": 90.0}},
        "04 Northern Hemisphere (stereo)": {"CRS": "MSS:stere,0,90,90",
                                            "map": {"llcrnrlon": -45.0, "llcrnrlat": 0.0,
                                                    "urcrnrlon": 135.0, "urcrnrlat": 0.0}}
    }

    # Side View.
    # The following two parameters are passed to the WMS in the BBOX
    # argument when a vertical cross section is requested.

    # Number of interpolation points used to interpolate the flight track
    # to a great circle.
    num_interpolation_points = 201

    # Number of x-axis labels in the side view.
    num_labels = 10

    # Web Map Service Client.
    # Settings for the WMS client. Set the URLs of WMS servers that appear
    # by default in the WMS control (for examples, see
    # http://external.opengis.org/twiki_public/bin/view/MetOceanDWG/MetocWMS_Servers).
    # Also set the location of the image file cache and its size.

    # URLs of default WMS servers.
    default_WMS = [
        "http://localhost:8081/"
    ]

    default_VSEC_WMS = [
        "http://localhost:8081/"
    ]

    default_LSEC_WMS = [
        "http://localhost:8081/"
    ]

    # URLs of default mscolab servers
    default_MSCOLAB = [
        "http://localhost:8083",
    ]

    # mail address to sign in
    MSCOLAB_mailid = ""

    # password to sign in
    MSCOLAB_password = ""

    # dictionary of MSC servers {"http://www.your-mscolab-server.de" : ("youruser", "yourpassword")}
    MSC_login = {}

    # timeout of Url request
    WMS_request_timeout = 30

    WMS_preload = []

    # dictionary of WMS servers {"http://www.your-wms-server.de" : ("youruser", "yourpassword")}
    WMS_login = {}

    # WMS image cache settings:
    wms_cache = os.path.join(tempfile.gettempdir(), "msui_wms_cache")

    # Maximum size of the cache in bytes.
    wms_cache_max_size_bytes = 20 * 1024 * 1024

    # Maximum age of a cached file in seconds.
    wms_cache_max_age_seconds = 5 * 86400

    wms_prefetch = {
        "validtime_fwd": 0,
        "validtime_bck": 0,
        "level_up": 0,
        "level_down": 0
    }

    locations = {
        "EDMO": [48.08, 11.28],
        "Hannover": [52.37, 9.74],
        "Hamburg": [53.55, 9.99],
        "Juelich": [50.92, 6.36],
        "Leipzig": [51.34, 12.37],
        "Muenchen": [48.14, 11.57],
        "Stuttgart": [48.78, 9.18],
        "Wien": [48.20833, 16.373064],
        "Zugspitze": [47.42, 10.98],
        "Kiruna": [67.821, 20.336],
        "Ny-Alesund": [78.928, 11.986],
        "Zhukovsky": [55.6, 38.116],
        "Paphos": [34.775, 32.425],
        "Sharjah": [25.35, 55.65],
        "Brindisi": [40.658, 17.947],
        "Nagpur": [21.15, 79.083],
        "Mumbai": [19.089, 72.868],
        "Delhi": [28.566, 77.103],
    }

    # Main application: Template for new flight tracks
    # Flight track template that is used when a new flight track is
    # created. Specify a list of place names that can be found in the
    # "locations" dictionary defined above.
    new_flighttrack_template = ["Nagpur", "Delhi"]

    # This configures the flight level for waypoints inserted by the
    # flighttrack template
    new_flighttrack_flightlevel = 0

    # None is not wanted here
    proxies = {}

    # ToDo configurable later
    # mscolab server
    mscolab_server_url = "http://localhost:8083"
    # ToDo refactor to rename this to data_dir/mss_data_dir
    # mss dir
    mss_dir = "~/mss"

    # list of gravatar email ids to automatically fetch
    gravatar_ids = []

    # dictionary for export plugins, e.g.  {"Text": ["txt", "mslib.plugins.io.text", "save_to_txt"] }
    export_plugins = {}

    # dictionary for import plugins, e.g. { "FliteStar": ["txt", "mslib.plugins.io.flitestar", "load_from_flitestar"] }
    import_plugins = {}

    # dictionary to make title, label and ticklabel sizes for topview and sideview configurable.
    # You can put your default value here, whatever you want to give,it should be a number.
    topview = {"plot_title_size": 10,
               "axes_label_size": 10}

    sideview = {"plot_title_size": 10,
                "axes_label_size": 10}

    linearview = {"plot_title_size": 10,
                  "axes_label_size": 10}

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

    config_descriptions = {
        "filepicker_default": "Documentation Required",
        "data_dir": "Documentation Required",
        "predefined_map_sections": "Documentation Required",
        "num_interpolation_points": "Documentation Required",
        "num_labels": "Documentation Required",
        "default_WMS": "Documentation Required",
        "default_VSEC_WMS": "Documentation Required",
        "default_LSEC_WMS": "Documentation Required",
        "default_MSCOLAB": "Documentation Required",
        "MSCOLAB_mailid": "Documentation Required",
        "MSCOLAB_password": "Documentation Required",
        "MSC_login": "Documentation Required",
        "WMS_request_timeout": "Documentation Required",
        "WMS_preload": "Documentation Required",
        "WMS_login": "Documentation Required",
        "wms_cache": "Documentation Required",
        "wms_cache_max_size_bytes": "Documentation Required",
        "wms_cache_max_age_seconds": "Documentation Required",
        "wms_prefetch": "Documentation Required",
        "locations": "Documentation Required",
        "new_flighttrack_template": "Documentation Required",
        "new_flighttrack_flightlevel": "Documentation Required",
        "proxies": "Documentation Required",
        "mscolab_server_url": "Documentation Required",
        "mss_dir": "Documentation Required",
        "gravatar_ids": "Documentation Required",
        "export_plugins": "Documentation Required",
        "import_plugins": "Documentation Required",
        "layout": "Documentation Required",
        "topview": "Documentation Required",
        "sideview": "Documentation Required",
        "linearview": "Documentation Required",
    }


def get_default_config():
    default_options = dict(MissionSupportSystemDefaultConfig.__dict__)
    for key in [
        "__module__",
        "__doc__",
        "__dict__",
        "__weakref__",
        "fixed_dict_options",
        "dict_option_structure",
        "list_option_structure",
        "key_value_options",
        "config_descriptions",
    ]:
        del default_options[key]

    return default_options


# default options as dictionary
default_options = get_default_config()

# user options as dictionary
user_options = copy.deepcopy(default_options)


def read_config_file(path=constants.MSS_SETTINGS):
    """
    reads a config file and updates global user_options

    Args:
        path: path of config file

    Note:
        sole purpose of the path argument is to be able to test with example config files
    """
    path = path.replace("\\", "/")
    dir_name, file_name = fs.path.split(path)
    json_file_data = {}
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
            raise FileNotFoundError(error_message)

    global user_options
    if json_file_data:
        user_options = merge_data(copy.deepcopy(default_options), json_file_data)
        logging.debug("Merged default and user settings")
    else:
        user_options = copy.deepcopy(default_options)
        logging.debug("No user settings found, using default settings")


def config_loader(dataset=None, default=False):
    """
    Function for loading json config data

    Args:
        config_file: json file, parameters for initializing mss,
        dataset: section to pull from json file

    Returns: a the dataset value or the config as dictionary

    """
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


def merge_data(options, json_file_data):
    """
    Merge two dictionaries by comparing all the options from
    the MissionSupportSystemDefaultConfig class

    Arguments:
    options -- Dict to merge options into
    json_file_data -- Dict with new values
    """
    # Check if dictionary options with fixed key/value pairs match data types from default
    for key in MissionSupportSystemDefaultConfig.fixed_dict_options:
        if key in json_file_data:
            options[key] = compare_data(options[key], json_file_data[key])[0]

    # Check if dictionary options with predefined structure match data types from default
    dos = copy.deepcopy(MissionSupportSystemDefaultConfig.dict_option_structure)
    # adding plugin structure : ["extension", "module", "function"] to
    # recognize user plugin options that don't have the optional filepicker option set
    dos["import_plugins"]["plugin-name-a"] = dos["import_plugins"]["plugin-name"][:3]
    dos["export_plugins"]["plugin-name-a"] = dos["export_plugins"]["plugin-name"][:3]
    for key in dos:
        if key in json_file_data:
            temp_data = {}
            for option_key in json_file_data[key]:
                for dos_key_key in dos[key]:
                    data, match = compare_data(dos[key][dos_key_key], json_file_data[key][option_key])
                    if match:
                        temp_data[option_key] = json_file_data[key][option_key]
                        break
            if temp_data != {}:
                options[key] = temp_data

    # Check if list options with predefined structure match data types from default
    los = copy.deepcopy(MissionSupportSystemDefaultConfig.list_option_structure)
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
    for key in MissionSupportSystemDefaultConfig.key_value_options:
        if key in json_file_data:
            data, match = compare_data(options[key], json_file_data[key])
            if match:
                options[key] = data

    # add filepicker default to import and export plugins if missing
    for plugin_type in ["import_plugins", "export_plugins"]:
        if plugin_type in options:
            for plugin in options[plugin_type]:
                if len(options[plugin_type][plugin]) == 3:
                    options[plugin_type][plugin].append(options.get("filepicker_default", "default"))

    return options


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
