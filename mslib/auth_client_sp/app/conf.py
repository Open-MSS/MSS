# -*- coding: utf-8 -*-
"""

    mslib.auth_client_sp.app.conf.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    config for sp.

    This file is part of MSS.

    :copyright: Copyright 2023 Nilupul Manodya
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
import secrets
import os

def get_crt_key():
    """
    Retrieves the certificate key and XML file path based on the environment 
    variable TEST_CASES_ENABLED.
    """

    # Retrieve the variable from the environment
    TEST_CASES_ENABLED = os.environ.get('TEST_CASES_ENABLED')

    if TEST_CASES_ENABLED is not None:
        return ("mslib/auth_client_sp/test_key_sp.key",
                "mslib/auth_client_sp/test_crt_sp.crt",
                "mslib/auth_client_sp/test_idp.xml")
    else:
        return ("mslib/auth_client_sp/key_sp.key",
                "mslib/auth_client_sp/crt_sp.crt",
                "mslib/auth_client_sp/idp.xml")

class DefaultSPSettings:
    """
    Default settings for the SP (Service Provider) application.
    
    This class provides default configuration settings for the SP application.
    Modify these settings as needed for your specific application requirements.
    """
    # SQLite CONNECTION STRING:
    SQLALCHEMY_DB_URI = "sqlite:///db.sqlite"

    # used to generate and parse tokens
    SECRET_KEY = secrets.token_urlsafe(16)

    SP_KEY_FILE, SP_CRT_FILE, IDP_XML = get_crt_key()

sp_settings = DefaultSPSettings()
