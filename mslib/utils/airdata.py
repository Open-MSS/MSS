# -*- coding: utf-8 -*-
"""

    mslib.utils.airdata
    ~~~~~~~~~~~~~~~~

    Functions for getting and downloading airspaces and airports.

    This file is part of MSS.

    :copyright: Copyright 2021 May Bär
    :copyright: Copyright 2021-2023 by the MSS team, see AUTHORS.
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


import csv
import humanfriendly
import os
import fs
import requests
import re as regex
from PyQt5 import QtWidgets
import logging
import time

import defusedxml.ElementTree as etree
from mslib.msui.constants import MSUI_CONFIG_PATH

OSDIR = fs.open_fs(MSUI_CONFIG_PATH).root_path
if not os.path.exists(os.path.join(OSDIR, "downloads", "aip")):
    os.makedirs(os.path.join(OSDIR, "downloads", "aip"))


class Airspace:
    """
    This class provides airspaces/airports URLs and variables
    """
    airports = []

    airports_mtime = 0

    data = []

    data_mtime = {}

    data_url = "https://storage.googleapis.com/29f98e10-a489-4c82-ae5e-489dbcd4912f"

    data_download_url = "https://storage.googleapis.com/storage/v1/b/29f98e10-a489-4c82-ae5e-489dbcd4912f/o/" \
                        "{}_asp.xml?alt=media"

    data_cache = [('ad_asp.xml', '377'), ('ae_asp.xml', '110238'), ('af_asp.xml', '377'), ('ag_asp.xml', '377'),
                  ('ai_asp.xml', '377'), ('al_asp.xml', '11360'), ('am_asp.xml', '377'), ('ao_asp.xml', '377'),
                  ('aq_asp.xml', '377'), ('ar_asp.xml', '975402'), ('as_asp.xml', '377'),
                  ('at_asp.xml', '1059077'),
                  ('au_asp.xml', '9667669'), ('aw_asp.xml', '377'), ('ax_asp.xml', '377'), ('az_asp.xml', '377'),
                  ('ba_asp.xml', '76717'), ('bb_asp.xml', '377'), ('bd_asp.xml', '377'), ('be_asp.xml', '462667'),
                  ('bf_asp.xml', '377'), ('bg_asp.xml', '440690'), ('bh_asp.xml', '68519'), ('bi_asp.xml', '377'),
                  ('bj_asp.xml', '377'), ('bl_asp.xml', '377')
                ]


def download_progress(file_path, url, progress_callback=lambda f: logging.info("%sKB Downloaded", int(f))):
    """
    Downloads the file at the given url to file_path and keeps track of the progress
    """
    try:
        with open(file_path, "wb+") as file:
            logging.info("Downloading to %s. This might take a while.", file_path)
            response = requests.get(url, stream=True, timeout=5)
            length = response.headers.get("content-length")
            if length is None:  # no content length header
                file.write(response.content)
            else:
                dl = 0
                for data in response.iter_content(chunk_size=1024 * 1024):
                    dl += len(data)
                    file.write(data)
                    progress_callback(dl / 1024)
    except requests.exceptions.RequestException:
        os.remove(file_path)
        QtWidgets.QMessageBox.information(None, "Download failed", f"{url} was unreachable, please try again later.")


def get_airports(force_download=False, url=None):
    """
    Gets or downloads the airports.csv in ~/.config/msui/downloads/aip and returns all airports within
    """
    _airports = Airspace().airports
    _airports_mtime = Airspace().airports_mtime

    if url is None:
        url = "https://ourairports.com/data/airports.csv"

    file_exists = os.path.exists(os.path.join(OSDIR, "downloads", "aip", "airports.csv"))

    if _airports and file_exists and \
            os.path.getmtime(os.path.join(OSDIR, "downloads", "aip", "airports.csv")) == _airports_mtime:
        return _airports

    time_outdated = 60 * 60 * 24 * 30  # 30 days
    is_outdated = file_exists and (time.time() - os.path.getmtime(os.path.join(OSDIR, "downloads", "aip",
                                                                               "airports.csv"))) > time_outdated

    if (force_download or is_outdated or not file_exists) \
            and QtWidgets.QMessageBox.question(None, "Allow download", f"You selected airports to be "
                                               f"{'drawn' if not force_download else 'downloaded (~10 MB)'}." +
                                               ("\nThe airports file first needs to be downloaded or updated (~10 MB)."
                                                if not force_download else "") + "\nIs now a good time?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.Yes) \
            == QtWidgets.QMessageBox.Yes:
        download_progress(os.path.join(OSDIR, "downloads", "aip", "airports.csv"), url)

    if os.path.exists(os.path.join(OSDIR, "downloads", "aip", "airports.csv")):
        with open(os.path.join(OSDIR, "downloads", "aip", "airports.csv"), "r", encoding="utf8") as file:
            _airports_mtime = os.path.getmtime(os.path.join(OSDIR, "downloads", "aip", "airports.csv"))
            return list(csv.DictReader(file, delimiter=","))

    else:
        return []


def get_available_airspaces():
    """
    Gets and returns all available airspaces and their sizes from openaip
    """
    try:
        directory = requests.get(Airspace.data_url, timeout=5)
        if directory.status_code == 404:
            return Airspace.data_cache
        airspaces = regex.findall(r">(.._asp\.xml)<", directory.text)
        sizes = regex.findall(r".._asp.xml.*?<Size>([0-9]+)<\/Size", directory.text)
        airspaces = [airspace for airspace in zip(airspaces, sizes) if airspace[-1] != "0"]
        return airspaces
    except requests.exceptions.RequestException:
        return Airspace.data_cache


def update_airspace(force_download=False, countries=None):
    """
    Downloads the requested airspaces from their respective country code if it is over a month old
    """
    if countries is None:
        countries = ["de"]

    for country in countries:
        location = os.path.join(OSDIR, "downloads", "aip", f"{country}_asp.xml")
        url = Airspace.data_download_url.format(country)
        available = get_available_airspaces()
        try:
            data = [airspace for airspace in available if airspace[0].startswith(country)][0]
        except IndexError:
            logging.info("countries: %s not exists", ' '.join(countries))
            continue
        file_exists = os.path.exists(location)

        is_outdated = file_exists and (time.time() - os.path.getmtime(location)) > 60 * 60 * 24 * 30

        if (force_download or is_outdated or not file_exists) \
                and QtWidgets.QMessageBox.question(
                    None, "Allow download",
                    f"The selected {country} airspace needs to be downloaded "
                    f"({humanfriendly.format_size(int(data[-1]))})\nIs now a good time?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.Yes) \
                == QtWidgets.QMessageBox.Yes:
            download_progress(location, url)


def get_airspaces(countries=None):
    """
    Gets the .xml files in ~/.config/msui/downloads/aip and returns all airspaces within
    """
    if countries is None:
        countries = []
    _airspaces = Airspace().data
    _airspaces_mtime = Airspace().data_mtime

    reload = False
    files = [f"{country}_asp.xml" for country in countries]
    update_airspace(countries=countries)
    files = [file for file in files if os.path.exists(os.path.join(OSDIR, "downloads", "aip", file))]

    if _airspaces and len(files) == len(_airspaces_mtime):
        for file in files:
            if file not in _airspaces_mtime or \
                    os.path.getmtime(os.path.join(OSDIR, "downloads", "aip", file)) != _airspaces_mtime[file]:
                reload = True
                break
        if not reload:
            return _airspaces

    _airspaces_mtime = {}
    _airspaces = []
    for file in files:
        fpath = os.path.join(OSDIR, "downloads", "aip", file)
        root = etree.parse(fpath).getroot()
        valid_file = len(set([elem.tag for elem in root.iter()])) == 12
        if valid_file:
            airspaces = (root.find('{https://www.openaip.net}AIRSPACES'))
            names = [dat.text for dat in airspaces.findall(".//{https://www.openaip.net}NAME")]
            polygons = [dat.text for dat in airspaces.findall(".//{https://www.openaip.net}POLYGON")]
            countries = [dat.text for dat in airspaces.findall(".//{https://www.openaip.net}COUNTRY")]
            tops = []
            top_units = []
            for dat in airspaces.findall(".//{https://www.openaip.net}ALTLIMIT_TOP"):
                unit = dat[0]
                top_units.append(unit.get("UNIT"))
                _, data = dat.iter()
                tops.append(float(data.text))
            bottoms = []
            bottom_units = []
            for dat in airspaces.findall(".//{https://www.openaip.net}ALTLIMIT_BOTTOM"):
                unit = dat[0]
                bottom_units.append(unit.get("UNIT"))
                _, data = dat.iter()
                bottoms.append(float(data.text))

            for index, value in enumerate(names):
                airspace_data = {
                    "name": names[index],
                    "polygon": polygons[index],
                    "top": tops[index],
                    "top_unit": top_units[index],
                    "bottom": bottoms[index],
                    "bottom_unit": bottom_units[index],
                    "country": countries[index]
                }

                # Convert to kilometers
                airspace_data["top"] /= 3281 if airspace_data["top_unit"] == "F" else 32.81
                airspace_data["bottom"] /= 3281 if airspace_data["bottom_unit"] == "F" else 32.81
                airspace_data["top"] = round(airspace_data["top"], 2)
                airspace_data["bottom"] = round(airspace_data["bottom"], 2)
                airspace_data.pop("top_unit")
                airspace_data.pop("bottom_unit")

                airspace_data["polygon"] = [(float(data.split()[0]), float(data.split()[-1]))
                                            for data in airspace_data["polygon"].split(",")]
                _airspaces.append(airspace_data)
                _airspaces_mtime[file] = os.path.getmtime(os.path.join(OSDIR, "downloads", "aip", file))
            else:
                QtWidgets.QMessageBox.information(None, "No Airspaces data in file:", f"{file}")

    return _airspaces
