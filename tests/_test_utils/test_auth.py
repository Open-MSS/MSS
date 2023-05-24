# -*- coding: utf-8 -*-
"""

    tests._test_utils.test_auth
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to test mslib.utils.auth

    This file is part of MSS.

    :copyright: Copyright 2023 Reimar Bauer
    :copyright: Copyright 2023 by the MSS team, see AUTHORS.
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

from tests.utils import create_msui_settings_file
from mslib.utils import auth
from mslib.utils.config import read_config_file, config_loader
from mslib.msui import constants


def test_keyring():
    username = "something@something.org"
    password = "abcdef"
    auth.save_password_to_keyring(service_name="MSCOLAB", username=username, password=password)
    assert auth.get_password_from_keyring(
        service_name="MSCOLAB", username=username) == password
    password = "123456"
    auth.save_password_to_keyring(service_name="MSCOLAB", username=username, password=password)
    assert auth.get_password_from_keyring(
        service_name="MSCOLAB", username=username) == "123456"
    auth.del_password_from_keyring(service_name="MSCOLAB", username=username)
    # the testsetu returns the same string per definition
    assert auth.get_password_from_keyring(
        service_name="MSCOLAB", username=username) == "password from TestKeyring"


def test_get_auth_from_url_and_name():
    # empty http_auth definition
    server_url = "http://example.com"
    http_auth = config_loader(dataset="MSS_auth")
    assert http_auth == {}
    data = auth.get_auth_from_url_and_name(server_url, http_auth, overwrite_login_cache=False)
    assert data == (None, None)
    # auth username and url defined
    auth_username = 'mss'
    create_msui_settings_file(f'{{"MSS_auth": {{"http://example.com": "{auth_username}"}}}}')
    read_config_file()
    http_auth = config_loader(dataset="MSS_auth")
    assert http_auth == {"http://example.com": "mss"}
    data = auth.get_auth_from_url_and_name(server_url, http_auth, overwrite_login_cache=False)
    # no password yet
    assert data == (auth_username, None)
    # store a password
    auth.save_password_to_keyring(server_url, auth_username, "password")
    # return the test password
    assert auth.get_password_from_keyring(server_url, auth_username) == "password"
    assert constants.AUTH_LOGIN_CACHE == {}
    auth.get_auth_from_url_and_name(server_url, http_auth, overwrite_login_cache=False)
    # password is set but doesn't go into the login cache
    assert constants.AUTH_LOGIN_CACHE == {}
    # now we overwrite_login_cache=True
    data = auth.get_auth_from_url_and_name(server_url, http_auth, overwrite_login_cache=True)
    assert data == (auth_username, 'password')
    assert constants.AUTH_LOGIN_CACHE[server_url] == (auth_username, 'password')
    # restart and use a different url
    create_msui_settings_file(f'{{"MSS_auth": {{"http://example.com": "{auth_username}"}}}}')
    read_config_file()
    data = auth.get_auth_from_url_and_name("http://example.com/something", http_auth, overwrite_login_cache=False)
    assert data == (None, None)
    # check storage of MSCOLAB password
    auth.save_password_to_keyring('MSCOLAB', auth_username, "password")
    assert auth.get_password_from_keyring("MSCOLAB", auth_username) == 'password'
