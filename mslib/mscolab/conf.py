# -*- coding: utf-8 -*-
"""

    mslib.mscolab.conf.py.example
    ~~~~~~~~~~~~~~~~~~~~

    config for mscolab.

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2024 by the MSS team, see AUTHORS.
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
import sys
import warnings
import yaml
from saml2 import SAMLError
from saml2.client import Saml2Client
from saml2.config import SPConfig
from urllib.parse import urlparse


class default_mscolab_settings:
    # expire token in seconds
    # EXPIRATION = 86400

    # In the unit days when Operations get archived because not used
    ARCHIVE_THRESHOLD = 30

    # To enable logging set to True or pass a logger object to use.
    SOCKETIO_LOGGER = False

    # To enable Engine.IO logging set to True or pass a logger object to use.
    ENGINEIO_LOGGER = False

    # Which origins are allowed to communicate with your server
    CORS_ORIGINS = ["*"]

    # dir where msui output files are stored
    BASE_DIR = os.path.expanduser("~")

    DATA_DIR = os.path.join(BASE_DIR, "colabdata")

    # mscolab data directory
    MSCOLAB_DATA_DIR = os.path.join(DATA_DIR, 'filedata')

    # MYSQL CONNECTION STRING: "mysql+pymysql://<username>:<password>@<host>:<port>/<db_name>?charset=utf8mb4"
    SQLALCHEMY_DB_URI = 'sqlite:///' + os.path.join(DATA_DIR, 'mscolab.db')

    # Set to True for testing and False for production
    SQLALCHEMY_ECHO = False

    # mscolab file upload settings
    UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
    MAX_UPLOAD_SIZE = 2 * 1024 * 1024  # 2MiB

    # mscolab user profile image and image chat attachment limit
    MAX_IMAGE_SIZE = 1 * 1024 * 1024  # 1MiB

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

    # looks for a given category forn a operation ending with GROUP_POSTFIX
    # e.g. category = Tex will look for TexGroup
    # all users in that Group are set to the operations of that category
    # having the roles in the TexGroup
    GROUP_POSTFIX = "Group"

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
    # filepath to md file with imprint
    IMPRINT = None
    # filepath to md file with gdpr
    GDPR = None

    # enable login by identity provider
    USE_SAML2 = False

    # accounts on a database on the server
    DIRECT_LOGIN = True

    # Enable SSL certificate verification during SSO between MSColab and IdP
    ENABLE_SSO_SSL_CERT_VERIFICATION = True

    # dir where mscolab single sign process files are stored
    MSCOLAB_SSO_DIR = os.path.join(DATA_DIR, 'datasso')


mscolab_settings = default_mscolab_settings()

try:
    import mscolab_settings as user_settings
    logging.info("Using user defined settings")
    mscolab_settings.__dict__.update(user_settings.__dict__)
except ImportError as ex:
    logging.warning(u"Couldn't import mscolab_settings (ImportError:'%s'), using dummy config.", ex)

try:
    from setup_saml2_backend import setup_saml2_backend
    logging.info("Using user defined saml2 settings")
except ImportError as ex:
    logging.warning(u"Couldn't import setup_saml2_backend (ImportError:'%s'), using dummy config.", ex)

    class setup_saml2_backend:
        # idp settings
        CONFIGURED_IDPS = [
            {
                'idp_identity_name': 'localhost_test_idp',
                'idp_data': {
                    'idp_name': 'Testing Identity Provider',
                }

            },
            # {
            #     'idp_identity_name': 'idp2',
            #     'idp_data': {
            #         'idp_name': '2nd Identity Provider',
            #     }
            # },
        ]
        if os.path.exists(f"{mscolab_settings.MSCOLAB_SSO_DIR}/mss_saml2_backend.yaml"):
            with open(f"{mscolab_settings.MSCOLAB_SSO_DIR}/mss_saml2_backend.yaml", encoding="utf-8") as fobj:
                yaml_data = yaml.safe_load(fobj)
            # go through configured IDPs and set conf file paths for particular files
            for configured_idp in CONFIGURED_IDPS:
                # set CRTs and metadata paths for the localhost_test_idp
                if 'localhost_test_idp' == configured_idp['idp_identity_name']:
                    yaml_data["config"]["localhost_test_idp"]["key_file"] = \
                        f'{mscolab_settings.MSCOLAB_SSO_DIR}/key_mscolab.key'
                    yaml_data["config"]["localhost_test_idp"]["cert_file"] = \
                        f'{mscolab_settings.MSCOLAB_SSO_DIR}/crt_mscolab.crt'
                    yaml_data["config"]["localhost_test_idp"]["metadata"]["local"][0] = \
                        f'{mscolab_settings.MSCOLAB_SSO_DIR}/idp.xml'

                    # configuration localhost_test_idp Saml2Client
                    try:
                        if not os.path.exists(yaml_data["config"]["localhost_test_idp"]["metadata"]["local"][0]):
                            yaml_data["config"]["localhost_test_idp"]["metadata"]["local"] = []
                            warnings.warn("idp.xml file does not exists !\
                                           Ignore this warning when you initializeing metadata.")

                        localhost_test_idp = SPConfig().load(yaml_data["config"]["localhost_test_idp"])
                        localhost_test_idp.verify_ssl_cert = mscolab_settings.ENABLE_SSO_SSL_CERT_VERIFICATION
                        sp_localhost_test_idp = Saml2Client(localhost_test_idp)

                        configured_idp['idp_data']['saml2client'] = sp_localhost_test_idp
                        for url_pair in (yaml_data["config"]["localhost_test_idp"]
                                         ["service"]["sp"]["endpoints"]["assertion_consumer_service"]):
                            saml_url, binding = url_pair
                            path = urlparse(saml_url).path
                            configured_idp['idp_data']['assertion_consumer_endpoints'] = \
                                configured_idp['idp_data'].get('assertion_consumer_endpoints', []) + [path]

                    except SAMLError:
                        warnings.warn("Invalid Saml2Client Config with localhost_test_idp ! Please configure with\
                                       valid CRTs metadata and try again.")
                        sys.exit()

                    # if multiple IdPs exists, development should need to implement accordingly below,
                    # make sure to set SSL certificates verification enablement.
                    """
                        if 'idp_2'== configured_idp['idp_identity_name']:
                            # rest of code
                            # set CRTs and metadata paths for the idp_2
                            # configuration idp_2 Saml2Client
                    """
