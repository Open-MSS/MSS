# -*- coding: utf-8 -*-
"""

    mslib.utils.verify_user_token
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Collection of unit conversion related routines for the Mission Support System.

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2024 by the MSS team, see AUTHORS.
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
import requests
from mslib.utils.config import config_loader
from urllib.parse import urljoin


def verify_user_token(mscolab_server_url, token):

    if config_loader(dataset="mscolab_skip_verify_user_token"):
        return True

    data = {
        "token": token
    }
    try:
        url = urljoin(mscolab_server_url, "test_authorized")
        r = requests.get(url, data=data, timeout=(2, 10))
    except requests.exceptions.SSLError:
        logging.debug("Certificate Verification Failed")
        return False
    except requests.exceptions.InvalidSchema:
        logging.debug("Invalid schema of url '%s'", url)
        return False
    except requests.exceptions.ConnectionError as ex:
        logging.error("unexpected error: %s %s", type(ex), ex)
        return False
    except requests.exceptions.MissingSchema as ex:
        # self.mscolab_server_url can be None??
        logging.error("unexpected error for url '%s': %s %s", url, type(ex), ex)
        return False
    return r.text == "True"
