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

sp_settings = DefaultSPSettings()
