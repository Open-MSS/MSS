# -*- coding: utf-8 -*-
"""

    mslib.thermolib
    ~~~~~~~~~~~~~~~~

    Collection of thermodynamic functions.

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
import requests
import json
import os
import time
import csv


def get_endpoint(endpoint):
    if os.path.exists(f"{endpoint}.json") and (time.time() - os.path.getmtime(f"{endpoint}.json")) < 60 * 60 * 24 * 60:
        with open(f"{endpoint}.json", "r") as file:
            return json.load(file)["items"]
    else:
        print(f"Downloading endpoint /{endpoint}")
        url = f"https://api.core.openaip.net/api/{endpoint}?page=1&limit=1000"
        response = requests.get(url).json()
        pages = response["totalPages"]
        for page in range(2, pages + 1):
            url.replace(f"page={page - 1}", f"page={page}")
            response["items"].extend(requests.get(url).json()["items"])
        with open(f"{endpoint}.json", "w+") as file:
            json.dump(response, file)
        return response["items"]


def get_airports():
    return get_endpoint("airports")


def get_openflights_airports():
    if os.path.exists("airports.csv") and (time.time() - os.path.getmtime("airports.csv")) < 60 * 60 * 24 * 60:
        with open("airports.csv", "r") as file:
            return list(csv.reader(file, delimiter=","))
    else:
        url = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
        with open("airports.csv", "w+") as file:
            airports = requests.get(url).text
            file.write(airports)
        return list(csv.reader(airports.splitlines(), delimiter=","))


def get_airspaces():
    return get_endpoint("airspaces")
