# -*- coding: utf-8 -*-
"""

    mslib.utils.get_projection_params
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Transfers a projection string into a dictionary of projection parameters

    This file is part of MSS.

    :copyright: Copyright 2021 May Bär
    :copyright: Copyright 2021-2025 by the MSS team, see AUTHORS.
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


def get_projection_params(proj):
    proj = proj.lower()
    if proj.startswith("crs:"):
        projid = proj[4:]
        if projid == "84":
            proj_params = {
                "basemap": {"projection": "cyl"},
                "bbox": "degree"}
        else:
            raise ValueError("Only CRS code 84 is supported: '%s' given", proj)

    elif proj.startswith("auto:"):
        raise ValueError("AUTO not supported")

        projid, unitsid, lon0, lat0 = proj[5:].split(",")
        if projid == "42001":
            proj_params = {
                "basemap": {"projection": "tmerc", "lon_0": lon0, "lat_0": lat0},
                "bbox": f"meter({lon0},{lat0})"}
        elif projid == "42002":
            proj_params = {
                "basemap": {"projection": "tmerc", "lon_0": lon0, "lat_0": lat0},
                "bbox": f"meter({lon0},{lat0})"}
        elif projid == "42003":
            proj_params = {
                "basemap": {"projection": "ortho", "lon_0": lon0, "lat_0": lat0},
                "bbox": f"meter({lon0},{lat0})"}
        else:
            raise ValueError("unspecified AUTO code: '%s'", proj)

    elif proj.startswith("auto2:"):
        raise ValueError("AUTO2 not supported")

        projid, factor, lon0, lat0 = proj[6:].split(",")
        if projid == "42001":
            proj_params = {
                "basemap": {"projection": "tmerc", "lon_0": lon0, "lat_0": lat0},
                "bbox": f"meter({lon0},{lat0})"}
        elif projid == "42002":
            proj_params = {
                "basemap": {"projection": "tmerc", "lon_0": lon0, "lat_0": lat0},
                "bbox": f"meter({lon0},{lat0})"}
        elif projid == "42003":
            proj_params = {
                "basemap": {"projection": "ortho", "lon_0": lon0, "lat_0": lat0},
                "bbox": f"meter({lon0},{lat0})"}
        elif projid == "42004":
            proj_params = {
                "basemap": {"projection": "cyl"},
                "bbox": f"meter({lon0},{lat0})"}
        elif projid == "42005":
            proj_params = {
                "basemap": {"projection": "moll", "lon_0": lon0, "lat_0": lat0},
                "bbox": "meter???"}
        else:
            raise ValueError("unspecified AUTO2 code: '%s'", proj)

    elif proj.startswith("epsg:"):
        epsg = proj[5:]
        if epsg.startswith("777") and len(epsg) == 8:  # user defined MSS code. deprecated.
            logging.warning("Using deprecated MSS-specific EPSG code. Switch to 'MSS:stere' instead.")
            lat_0, lon_0 = int(epsg[3:5]), int(epsg[5:])
            proj_params = {
                "basemap": {"projection": "stere", "lat_0": lat_0, "lon_0": lon_0},
                "bbox": "degree"}
        elif epsg.startswith("778") and len(epsg) == 8:  # user defined MSS code. deprecated.
            logging.warning("Using deprecated MSS-specific EPSG code. Switch to 'MSS:stere' instead.")
            lat_0, lon_0 = int(epsg[3:5]), int(epsg[5:])
            proj_params = {
                "basemap": {"projection": "stere", "lat_0": -lat_0, "lon_0": lon_0},
                "bbox": "degree"}
        elif epsg in ("4258", "4326"):
            proj_params = {"basemap": {"epsg": epsg}, "bbox": "degree"}
        elif epsg in ("3031", "3412"):
            proj_params = {"basemap": {"epsg": epsg}, "bbox": "meter(0,-90)"}
        elif epsg in ("3411", "3413", "3575", "3995"):
            proj_params = {"basemap": {"epsg": epsg}, "bbox": "meter(0,90)"}
        elif epsg in ("3395", "3857"):
            proj_params = {"basemap": {"epsg": epsg}, "bbox": "meter(0,0)"}
        elif epsg in ("4839"):
            proj_params = {"basemap": {"epsg": epsg}, "bbox": "meter(10.5,51)"}
        elif epsg in ("31467"):
            proj_params = {"basemap": {"epsg": epsg}, "bbox": "meter(-20.9631343,0.0037502)"}
        elif epsg in ("31468"):
            proj_params = {"basemap": {"epsg": epsg}, "bbox": "meter(-25.4097892,0.0037466)"}
        else:
            raise ValueError("EPSG code not supported by basemap module: '%s'", proj)

    elif proj.startswith("mss:"):
        # some MSS-specific codes
        params = proj[4:].split(",")
        name = params[0]
        if name == "stere":
            lon0, lat0, lat_ts = params[1:]
            proj_params = {
                "basemap": {"projection": name, "lat_0": lat0, "lon_0": lon0, "lat_ts": lat_ts},
                "bbox": "degree"}
        elif name == "cass":
            lon0, lat0 = params[1:]
            proj_params = {
                "basemap": {"projection": name, "lon_0": lon0, "lat_0": lat0},
                "bbox": "degree"}
        elif name == "lcc":
            lon0, lat0, lat1, lat2 = params[1:]
            proj_params = {
                "basemap": {"projection": name, "lon_0": lon0, "lat_0": lat0, "lat_1": lat1, "lat_2": lat2},
                "bbox": "degree"}
        elif name == "merc":
            lat_ts = params[1]
            proj_params = {
                "basemap": {"projection": name, "lat_ts": lat_ts},
                "bbox": "degree"}
        else:
            raise ValueError("unknown MSS projection: '%s'", proj)

    else:
        raise ValueError("unknown projection: '%s'", proj)
    logging.debug("Identified CRS '%s' as '%s'", proj, proj_params)
    return proj_params
