# -*- coding: utf-8 -*-
"""

    mslib.msui
    ~~~~~~~~~~

    This module provides the default configuration for the msui

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

import os
import tempfile


class MissionSupportSystemDefaultConfig(object):
    """Central configuration for the Mission Support System User Interface
       Application (mss).

    This file is part of the Mission Support System User Interface (mss).

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

    # dictionary of MSC servers {"http://www.your-mscolab-server.de" : ("youruser", "yourpassword")]
    MSC_login = {}

    # timeout of Url request
    WMS_request_timeout = 30

    WMS_preload = []

    # dictionary of WMS servers {"http://www.your-wms-server.de" : ("youruser", "yourpassword")]
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

    config_descriptions = {
        "filepicker_default": "General file picker to access locations on remote machines"
        "facilitating collaboration on campaigns. Possible Options: qt, fs",
        "data_dir": "Directory for storing MSS data",
        "predefined_map_sections": "",
        "num_interpolation_points": "",
        "num_labels": "",
        "default_WMS": "",
        "default_VSEC_WMS": "",
        "default_LSEC_WMS": "",
        "default_MSCOLAB": "",
        "MSCOLAB_mailid": "",
        "MSCOLAB_password": "",
        "MSC_login": "",
        "WMS_request_timeout": "",
        "WMS_preload": "",
        "WMS_login": "",
        "wms_cache": "",
        "wms_cache_max_size_bytes": "",
        "wms_cache_max_age_seconds": "",
        "wms_prefetch": "",
        "locations": "",
        "new_flighttrack_template": "",
        "new_flighttrack_flightlevel": "",
        "proxies": "",
        "mscolab_server_url": "",
        "mss_dir": "",
        "gravatar_ids": "",
        "export_plugins": "",
        "import_plugins": "",
        "topview": "",
        "sideview": "",
        "linearview": "",
    }
