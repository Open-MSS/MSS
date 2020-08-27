# -*- coding: utf-8 -*-
"""

    mslib.mscolab.conf.py.example
    ~~~~~~~~~~~~~~~~~~~~

    config for mscolab.

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2020 by the mss team, see AUTHORS.
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
try:
    from mscolab_settings import mscolab_settings
    logging.info("Using user defined settings")
except ImportError as ex:
    logging.warning(u"Couldn't import mscolab_settings (ImportError:'%s'), using dummy config.", ex)

    class mscolab_settings(object):
        import os
        import logging

        # dir where mss output files are stored
        BASE_DIR = os.path.expanduser("~")

        DATA_DIR = os.path.join(BASE_DIR, "colabdata")

        # mscolab data directory
        MSCOLAB_DATA_DIR = os.path.join(DATA_DIR, 'filedata')

        # MYSQL CONNECTION STRING: "mysql+pymysql://<username>:<password>@<host>:<port>/<db_name>?charset=utf8mb4"
        SQLALCHEMY_DB_URI = 'sqlite:///' + os.path.join(DATA_DIR, 'mscolab.db')

        # mscolab file upload settings
        UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
        MAX_UPLOAD_SIZE = 2 * 1024 * 1024  # 2MB

        # used to generate and parse tokens
        SECRET_KEY = 'MySecretKey'

        STUB_CODE = """<?xml version="1.0" encoding="utf-8"?>
        <FlightTrack version="1.7.6">
          <ListOfWaypoints>
            <Waypoint flightlevel="250" lat="67.821" location="Kiruna" lon="20.336">
              <Comments></Comments>
            </Waypoint>
            <Waypoint flightlevel="250" lat="78.928" location="Ny-Alesund" lon="11.986">
              <Comments></Comments>
            </Waypoint>
          </ListOfWaypoints>
        </FlightTrack>
        """
        enable_basic_http_authentication = False
