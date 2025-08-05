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


def set_global_data(flight_track=None):
    """
    Create the global section for view settings using waypoints from flight_track or topview.
    """
    if flight_track:
        flight_track_name = flight_track.name
    else:
        logging.warning("No flight track provided; using default flight track name")

    return {
        "mss_version": str(mss_version),
        "flight_track_name": str(flight_track_name)
    }


def serializer(obj):
    """
    Recursively serialize a list of settings dictionaries to make them JSON-serializable.
    """
    if hasattr(obj, '__dict__'):
        return {
            attr: getattr(obj, attr)
            for attr in dir(obj)
            if not attr.startswith('_') and isinstance(
                getattr(obj, attr), (str, int, float, bool, list, dict, type(None))
            )
        }
    elif isinstance(obj, QtCore.QDateTime):
        return obj.toString(QtCore.Qt.ISODate)
    elif isinstance(obj, QtGui.QColor):
        return list(obj.getRgb())
    elif isinstance(obj, tuple):
        return list(obj)
    else:
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def serialize_settings(settings_list):
    """
    Serialize settings to JSON string using a custom default serializer.
    """
    if isinstance(settings_list, dict):
        settings_list = [settings_list]
    try:
        return json.dumps(settings_list, default=serializer)
    except TypeError as e:
        logging.error("Serialization failed: %s", e)
        raise


def restore_view_settings(flight_track_name):
    """
    Restore view settings from the JSON file and adjust waypoints' flightlevel.
    """
    default_settings = {
        "global": {"mss_version": str(mss_version), "flight_track_name": "Unknown"},
        "views": []
    }

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

        views_data = setting_data.get("views", [])

        if isinstance(views_data, dict):
            setting_data["views"] = [views_data]
        elif not isinstance(views_data, list):
            logging.warning("Invalid views format for %s, converting to empty list", flight_track_name)
            setting_data["views"] = []

        return setting_data
    except Exception as e:
        logging.error("Failed to restore view settings for %s: %s", flight_track_name, str(e))
        return default_settings
