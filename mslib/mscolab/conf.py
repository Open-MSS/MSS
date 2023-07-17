# -*- coding: utf-8 -*-
"""

    mslib.mscolab.conf.py.example
    ~~~~~~~~~~~~~~~~~~~~

    config for mscolab.

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2023 by the MSS team, see AUTHORS.
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
import logging
import secrets


class default_mscolab_settings:
    # expire token in seconds
    # EXPIRATION = 86400

    # Which origins are allowed to communicate with your server
    CORS_ORIGINS = ["*"]

    # dir where msui output files are stored
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
    SECRET_KEY = secrets.token_urlsafe(16)

    # used to generate the password token
    SECURITY_PASSWORD_SALT = secrets.token_urlsafe(16)

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

    # enable verification by Mail
    MAIL_ENABLED = False

    # mail settings
    # MAIL_SERVER = 'localhost'
    # MAIL_PORT = 25
    # MAIL_USE_TLS = False
    # MAIL_USE_SSL = True

    # mail authentication
    # MAIL_USERNAME = os.environ.get('APP_MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('APP_MAIL_PASSWORD')

    # mail accounts
    # MAIL_DEFAULT_SENDER = 'MSS@localhost'

    # enable login by identity provider
    IDP_ENABLED = True

mscolab_settings = default_mscolab_settings()

try:
    import mscolab_settings as user_settings
    logging.info("Using user defined settings")
    mscolab_settings.__dict__.update(user_settings.__dict__)
except ImportError as ex:
    logging.warning(u"Couldn't import mscolab_settings (ImportError:'%s'), using dummy config.", ex)
