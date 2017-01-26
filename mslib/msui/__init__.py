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
     -- batch products for the loop view
    in this file.

    Do not change any value for good reasons.
    Your values can be set in your personal mss_settings.json file
    """

    # Matplotlib Basemap Projection Parameters
    # The following parameters configure the map projections available in
    # the top view. Define EPSG codes you require in terms of Matplotlib
    # basemap parameters. Predefined map regions that should be selectable
    # by the user in the top view user interface can also be defined.

    # Table to translate CRS (coordinate reference system) codes to matplotlib
    # basemap projection parameters.
    crs_to_mpl_basemap_table = {
        "EPSG:4326": {"basemap": {"projection": "cyl"},
                      "bbox": "latlon"},
        "EPSG:9810": {"basemap": {"projection": "stere", "lat_0": 90., "lon_0": 0.},
                      "bbox": "metres"},
        "EPSG:77790000": {"basemap": {"projection": "stere", "lat_0": 90., "lon_0": 0.},
                          "bbox": "latlon"},
        "EPSG:77790010": {"basemap": {"projection": "stere", "lat_0": 90., "lon_0": 10.},
                          "bbox": "latlon"},
        "EPSG:77790335": {"basemap": {"projection": "stere", "lat_0": 90., "lon_0": -25.},
                          "bbox": "latlon"},
        "EPSG:77774020": {"basemap": {"projection": "stere", "lat_0": 74., "lon_0": 20.},
                          "bbox": "latlon"}
    }

    # Predefined map regions to be listed in the corresponding topview combobox.
    predefined_map_sections = {
        "01 Europe (cyl)": {"CRS": "EPSG:4326",
                            "map": {"llcrnrlon": -15.0, "llcrnrlat": 35.0,
                                    "urcrnrlon": 30.0, "urcrnrlat": 65.0}},
        "02 Germany (cyl)": {"CRS": "EPSG:4326",
                             "map": {"llcrnrlon": 5.0, "llcrnrlat": 45.0,
                                     "urcrnrlon": 15.0, "urcrnrlat": 57.0}},
        "03 Europe (stereo)": {"CRS": "EPSG:77790010",
                               "map": {"llcrnrlon": -22.5, "llcrnrlat": 27.5,
                                       "urcrnrlon": 55.0, "urcrnrlat": 62.5}},
        "04 Germany (stereo)": {"CRS": "EPSG:77790010",
                                "map": {"llcrnrlon": -4.0, "llcrnrlat": 45.5,
                                        "urcrnrlon": 20.0, "urcrnrlat": 57.0}},
        "05 Spitsbergen L (stereo)": {"CRS": "EPSG:77790000",
                                      "map": {"llcrnrlon": -39.0, "llcrnrlat": 51.0,
                                              "urcrnrlon": 82.0, "urcrnrlat": 73.5}},
        "06 Spitsbergen S (stereo)": {"CRS": "EPSG:77790000",
                                      "map": {"llcrnrlon": -22.0, "llcrnrlat": 73.0,
                                              "urcrnrlon": 66.0, "urcrnrlat": 79.5}},
        "07 Global (cyl)": {"CRS": "EPSG:4326",
                            "map": {"llcrnrlon": -180.0, "llcrnrlat": -90.0,
                                    "urcrnrlon": 180.0, "urcrnrlat": 90.0}},
        "08 Northern Hemisphere (stereo)": {"CRS": "EPSG:77790000",
                                            "map": {"llcrnrlon": -45.0, "llcrnrlat": 0.0,
                                                    "urcrnrlon": 135.0, "urcrnrlat": 0.0}},
        "09 Kiruna L (stereo)": {"CRS": "EPSG:77774020",
                                 "map": {"llcrnrlon": -30.0, "llcrnrlat": 45.0,
                                         "urcrnrlon": 120.0, "urcrnrlat": 65.0}},
        "10 Europe/N Africa (cyl)": {"CRS": "EPSG:4326",
                                            "map": {"llcrnrlon": -30.0, "llcrnrlat": 20.0,
                                                    "urcrnrlon": 25.0, "urcrnrlat": 65.0}},
        "11 INDIA": {"CRS": "EPSG:4326",
                     "map": {"llcrnrlon": 65.0, "llcrnrlat": 2.0,
                             "urcrnrlon": 96.0, "urcrnrlat": 36.0}}
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
    default_WMS = ["http://localhost:8081/",
                   ]

    default_VSEC_WMS = [
        "http://localhost:8081/"
    ]

    # WMS image cache settings:
    wms_cache = os.path.join(tempfile.gettempdir(), "msui_wms_cache")

    # Maximum size of the cache in bytes.
    wms_cache_max_size_bytes = 20 * 1024 * 1024
    # Maximum age of a cached file in seconds.
    wms_cache_max_age_seconds = 5 * 86400

    locations = {
        "EDMO": (48.08, 11.28),
        "Hannover": (52.37, 9.74),
        "Hamburg": (53.55, 9.99),
        "Juelich": (50.92, 6.36),
        "Leipzig": (51.34, 12.37),
        "Muenchen": (48.14, 11.57),
        "Stuttgart": (48.78, 9.18),
        "Wien": (48.20833, 16.373064),
        "Zugspitze": (47.42, 10.98),
        "Kiruna": (67.821, 20.336),
        "Ny-Alesund": (78.928, 11.986),
        "Zhukovsky": (55.6, 38.116),
        "Paphos": (34.775, 32.425),
        "Sharjah": (25.35, 55.65),
        "Brindisi": (40.658, 17.947),
        "Nagpur": (21.15, 79.083),
        "Mumbai": (19.089, 72.868),
        "Delhi": (28.566, 77.103),
    }

    # Main application: Template for new flight tracks
    # Flight track template that is used when a new flight track is
    # created. Specify a list of place names that can be found in the
    # "locations" dictionary defined above.
    new_flighttrack_template = ["Nagpur", "Delhi"]

    # This configures the flight level for waypoints inserted by the
    # flighttrack template
    new_flighttrack_flightlevel = 0

    # LoopView configuration: The products defined in the following
    # dictionary are displayed by the ProductChooserDialog in the
    # loopview.

    loop_configuration = {
        "ECMWF forecasts": {
            # URL to the Mission Support website at which the batch image
            # products are located.
            "url": "http://www.your-server.de/forecasts",
            # Initialisation times every init_timestep hours.
            "init_timestep": 12,
            # Products available on the webpage. Add new products here!
            # Each product listed here will be loaded as one group, so
            # that the defined times can be navigated with <wheel> and
            # the defined levels can be navigated with <shift+wheel>.
            # Times not found in the listed range of forecast_steps
            # are ignored, its hence save to define the entire forecast
            # range with the smalled available time step.
            "products": {
                "Geopotential and Wind": {
                    "abbrev": "geop",
                    "regions": {"Europe": "eur", "Germany": "de"},
                    "levels": [200, 250, 300, 500, 700, 850, 925],
                    "forecast_steps": range(0, 240, 3)},
                "Temperature": {
                    "abbrev": "temp",
                    "regions": {"Europe": "eur", "Germany": "de"},
                    "levels": [200, 250, 300, 500, 700, 850, 925],
                    "forecast_steps": range(0, 240, 3)},
                "Equivalent Potential Temperature": {
                    "abbrev": "eqpt",
                    "regions": {"Europe": "eur", "Germany": "de"},
                    "levels": [500, 700, 850, 925],
                    "forecast_steps": range(0, 240, 3)},
                "Relative Humidity": {
                    "abbrev": "rhu",
                    "regions": {"Europe": "eur", "Germany": "de"},
                    "levels": [200, 250, 300, 500, 700, 850, 925],
                    "forecast_steps": range(0, 243, 3)},
                "Vertical Velocity": {
                    "abbrev": "vert",
                    "regions": {"Europe": "eur", "Germany": "de"},
                    "levels": [200, 250, 300, 500, 700, 850, 925],
                    "forecast_steps": range(0, 243, 3)}
            }
        }
    }

    # Trajectory tool: When NASA Ames files are opened, the following
    # variables will be used for lon/lat/pressure:

    traj_nas_lon_identifier = ["GPS LON", "LONGITUDE"]
    traj_nas_lat_identifier = ["GPS LAT", "LATITUDE"]
    traj_nas_p_identifier = ["STATIC PRESSURE"]
