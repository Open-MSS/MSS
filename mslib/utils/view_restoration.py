# -*- coding: utf-8 -*-
"""
    mslib/utils/view_restoration.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This file is part of MSS.

    :copyright: Copyright 2025 Annapurna Gupta.
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
from PyQt5 import QtCore
from pathlib import Path
from mslib.msui import constants


def save_view_settings(settings, global_data):
    """
    Save view settings (for top, side, linear, and table views) to a JSON file.

    Args:
        settings: A list of dictionaries containing settings for view windows.
                 Each dictionary must have a 'view_type' key ('topview', 'sideview', 'linearview', 'tableview').
        global_data: Dictionary containing global settings, including waypoints.

    Returns:
        bool: True if settings were saved successfully, False otherwise.
    """
    if not isinstance(settings, list):
        raise TypeError("Settings must be a list of dictionaries")
    for setting in settings:
        if not isinstance(setting, dict) or "view_type" not in setting:
            raise ValueError("Each setting must be a dictionary with a 'view_type' key")
    if not isinstance(global_data, dict):
        logging.warning("Invalid global_data; using empty dictionary")
        global_data = {}

    all_settings = {
        "global": global_data,
        "views": {setting["view_type"]: setting for setting in settings}
    }

    config_path = Path(constants.MSUI_CONFIG_PATH)
    config_path.mkdir(parents=True, exist_ok=True)
    save_path = config_path / "view_settings.json"

    try:
        with open(save_path, "w") as f:
            json.dump(all_settings, f, indent=4)
        logging.info("Saved view settings to %s", save_path)
        return True
    except Exception as e:
        logging.error("Failed to save view settings to %s: %s", save_path, str(e))
        return False


def set_global_data(topview):
    """
    Create the global section for view settings using waypoints from Top View.

    Args:
        topview: Instance of MSUITopViewWindow to retrieve waypoints.

    Returns:
        dict: Global section with mss_version, waypoints_source, and waypoints.
    """
    from mslib import __version__ as mss_version
    waypoints, source_name = topview.get_waypoints() if topview else ([], "Flight Track")
    adjusted_waypoints = []
    for wp in waypoints:
        lat = wp.get("lat", 0)
        lon = wp.get("lon", 0)
        flightlevel = wp.get("flightlevel", 0)
        if (isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and
                -90 <= lat <= 90 and -180 <= lon <= 180 and
                isinstance(flightlevel, (int, float))):
            adjusted_waypoints.append({
                "lat": float(lat),
                "lon": float(lon),
                "flightlevel": float(flightlevel),
                "location": wp.get("location", ""),
                "comments": wp.get("comments", "")
            })
        else:
            logging.warning("Invalid waypoint skipped in set_global_data: %s", wp)

    return {
        "mss_version": str(mss_version),
        "waypoints_source": str(source_name),
        "waypoints": adjusted_waypoints
    }


def serialize_settings(raw_dict):
    """
    Recursively serialize a settings dict to make it JSON-serializable.
    - Converts custom objects (with __dict__) to dicts of their public, simple attributes.
    - Converts QDateTime to ISO string.
        """
    serialized = {}

    for key, value in raw_dict.items():
        if hasattr(value, '__dict__'):
            serialized[key] = {
                attr: getattr(value, attr)
                for attr in dir(value)
                if not attr.startswith('_') and isinstance(
                    getattr(value, attr), (str, int, float, bool, list, dict, type(None))
                )
            }
        elif isinstance(value, QtCore.QDateTime):
            serialized[key] = value.toString(QtCore.Qt.ISODate)
        elif isinstance(value, dict):
            serialized[key] = serialize_settings(value)
        else:
            serialized[key] = value

    return serialized


def restore_view_settings():
    """
    Restore view settings from the JSON file and adjust waypoints' flightlevel.

    Returns:
        dict: Settings dictionary with adjusted waypoints, or default settings if file not found.
    """
    config_path = Path(constants.MSUI_CONFIG_PATH)
    save_path = config_path / "view_settings.json"
    default_settings = {
        "global": {
            "mss_version": "10.1.0",
            "waypoints_source": "Flight Track",
            "waypoints": [
                {"lat": 21.15, "lon": 79.083, "flightlevel": 300.0, "location": "Nagpur", "comments": ""},
                {"lat": 28.566, "lon": 77.103, "flightlevel": 300.0, "location": "Delhi", "comments": ""}
            ]
        },
        "views": {
            "topview": {"wms": {}},
            "sideview": {"wms": {}},
            "linearview": {"wms": {}},
            "tableview": {}
        }
    }
    if not save_path.exists():
        logging.info("No view setting file found at %s, using default settings", save_path)
        return default_settings
    try:
        with open(save_path, "r") as f:
            settings = json.load(f)
        global_settings = settings.get("global", default_settings["global"])
        waypoints = global_settings.get("waypoints", default_settings["global"]["waypoints"])
        adjusted_waypoints = []
        for wp in waypoints:
            lat = wp.get("lat")
            lon = wp.get("lon")
            flightlevel = wp.get("flightlevel", 0)
            if (isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and
                    -90 <= lat <= 90 and -180 <= lon <= 180 and
                    isinstance(flightlevel, (int, float))):
                adjusted_waypoints.append({
                    "lat": float(lat),
                    "lon": float(lon),
                    "flightlevel": float(flightlevel),
                    "location": wp.get("location", ""),
                    "comments": wp.get("comments", "")
                })
                logging.debug("Restored waypoint: lat=%s, lon=%s, flightlevel=%s", lat, lon, flightlevel)
            else:
                logging.warning("Invalid waypoint skipped in restore_view_settings: %s", wp)
        settings["global"]["waypoints"] = (
            adjusted_waypoints
            if adjusted_waypoints
            else default_settings["global"]["waypoints"]
        )

        # Ensure views is a dict
        if isinstance(settings.get("views"), list):
            settings["views"] = {s["view_type"]: s for s in settings["views"] if "view_type" in s}
        return settings
    except Exception as e:
        logging.error("Failed to restore view settings from %s: %s", save_path, str(e))
        return default_settings
