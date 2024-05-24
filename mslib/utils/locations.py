# -*- coding: utf-8 -*-
"""

    mslib.utils.locations
    ~~~~~~~~~~~~~~~~~~~~~

    Collection of functions all around locations.

    This file is part of MSS.

    :copyright: Copyright 2021 May Bär
    :copyright: Copyright 2021-2024 by the MSS team, see AUTHORS.
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


from mslib.utils.config import config_loader
from mslib.utils.coordinate import get_distance


def find_location(lat, lon, tolerance=5):
    """
    Checks if a location is present at given coordinates
    :param lat: latitude
    :param lon: longitude
    :param tolerance: maximum distance between location and coordinates in km
    :return: None or lat/lon, name
    """
    locations = config_loader(dataset='locations')
    distances = sorted([(get_distance(lat, lon, loc_lat, loc_lon), loc)
                        for loc, (loc_lat, loc_lon) in locations.items()])
    if len(distances) > 0 and distances[0][0] <= tolerance:
        return locations[distances[0][1]], distances[0][1]
    else:
        return None
