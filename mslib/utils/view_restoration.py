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
from PyQt5 import QtGui
from mslib.msui import constants
from mslib import __version__ as mss_version


def save_view_settings(settings, global_data, flight_track_name):
    """
    Save view settings (for top, side, linear, and table views) to a JSON file.
    """
    if not isinstance(settings, list):
        raise TypeError("Settings must be a list of dictionaries")
    for setting in settings:
        if not isinstance(setting, dict) or "view_type" not in setting:
            raise ValueError("Each setting must be a dictionary with a 'view_type' key")
    if not isinstance(global_data, dict):
        logging.warning("Invalid global_data; using empty dictionary")
        global_data = {}
    if not isinstance(flight_track_name, str):
        logging.warning("Invalid flight_track_name '%s'; converting to string", flight_track_name)
        flight_track_name = str(flight_track_name)

    try:
        config_path = Path(constants.MSUI_CONFIG_PATH)
        config_path.mkdir(parents=True, exist_ok=True)
        settings_file = config_path / "view_settings.json"
        settings_data = {}
        if settings_file.exists():
                try:
                    with settings_file.open("r", encoding="utf-8") as f:
                        settings_data = json.load(f)
                except json.JSONDecodeError:
                    logging.warning("Corrupted view_settings.json, initializing new file")

        settings_data[flight_track_name] = {
                "global": global_data,
                "views": settings
            }
            
        with settings_file.open("w", encoding="utf-8") as f:
            json.dump(settings_data, f, indent=2)
        return True
    except Exception as e:
        logging.error("Failed to save view settings for %s: %s", flight_track_name, str(e))
        return False


def set_global_data(topview, flight_track=None):
    """
    Create the global section for view settings using waypoints from flight_track or topview.
    """
    if flight_track:
        waypoints = flight_track.get_waypoints_data()
        source_name = flight_track.name
        logging.debug("Retrieved %d waypoints from flight track '%s'", len(waypoints), source_name)
    else:
        waypoints, source_name = topview.get_waypoints() if topview else ([], "Default")
        logging.warning("Using topview waypoints or default; flight_track not provided")
    
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


def serialize_settings(settings_list):
    """
    Recursively serialize a list of settings dictionaries to make them JSON-serializable.
    """
    if isinstance(settings_list, dict):
        settings_list = [settings_list]  # Handle single dict case
    serialized_list = []
    for settings in settings_list:
        if not isinstance(settings, dict):
            logging.warning("Invalid settings entry skipped: %s", settings)
            continue
        serialized = {}
        for key, value in settings.items():
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
                serialized[key] = serialize_settings([value])[0]
            elif isinstance(value, list):
                serialized[key] = serialize_settings(value)
            elif isinstance(value, (tuple, QtGui.QColor)):
                serialized[key] = list(value)
            else:
                serialized[key] = value
        serialized_list.append(serialized)
    return serialized_list if isinstance(settings_list, list) else serialized_list[0]


def restore_view_settings(flight_track_name):
    """
    Restore view settings from the JSON file and adjust waypoints' flightlevel.
    """
    default_settings = {
        "global": {"mss_version": str(mss_version), "waypoints_source": "Default", "waypoints": []},
        "views": []
    }

    if not isinstance(flight_track_name, str):
        logging.warning("Invalid flight_track_name '%s'; converting to string", flight_track_name)
        flight_track_name = str(flight_track_name)

    config_path = Path(constants.MSUI_CONFIG_PATH)
    save_path = config_path / "view_settings.json"
    if not save_path.exists():
        logging.info("No view settings file found at %s", save_path)
        return default_settings

    try:
        with save_path.open("r", encoding="utf-8") as f:
            settings = json.load(f)

        setting_data = settings.get(flight_track_name, default_settings)
        if not isinstance(setting_data, dict):
            logging.warning("Invalid settings data for %s; returning default", flight_track_name)
            return default_settings
    

        global_settings = setting_data["global"]
        waypoints = global_settings.get("waypoints", [])
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
        setting_data["global"]["waypoints"] = adjusted_waypoints

        views_data = setting_data.get("views")

        if isinstance(views_data, dict):
            setting_data["views"] = [views_data]
        elif not isinstance(views_data, list):
            logging.warning("Invalid views format for %s, converting to empty list", flight_track_name)
            setting_data["views"] = []

        return setting_data
    except Exception as e:
        logging.error("Failed to restore view settings for %s: %s", flight_track_name, str(e))
        return default_settings
