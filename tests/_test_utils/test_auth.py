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
    password = "x-*\\M#.U<Ik<g}YYGZb}>6R(HPNW2}"
    auth.save_password_to_keyring(service_name="MSCOLAB", username=username, password=password)
    assert auth.get_password_from_keyring(service_name="MSCOLAB",
                                          username=username) == "password from TestKeyring"
    auth.del_password_from_keyring(service_name="MSCOLAB", username=username)
    # the testsetu returns the same string per definition
    assert auth.get_password_from_keyring(service_name="MSCOLAB",
                                          username=username) == "password from TestKeyring"


def test_get_auth_from_url_and_name():
    server_url = "http://example.com"
    http_auth = config_loader(dataset="MSS_auth")
    data = auth.get_auth_from_url_and_name(server_url, http_auth, overwrite_login_cache=False)
    assert data == (None, None)
    auth_username = 'mss'
    create_msui_settings_file(f'{{"MSS_auth": {{"http://example.com": "{auth_username}"}}}}')
    read_config_file()
    http_auth = config_loader(dataset="MSS_auth")
    data = auth.get_auth_from_url_and_name(server_url, http_auth, overwrite_login_cache=False)
    assert data == (auth_username, None)
    auth.save_password_to_keyring('MSCOLAB', auth_username, "password")
    data = auth.get_auth_from_url_and_name(server_url, http_auth, overwrite_login_cache=False)
    assert data == (auth_username, None)
    auth.save_password_to_keyring('MSCOLAB', auth_username, "password")
    # we get only access to the auth_password when we add it to constants.AUTH_LOGIN_CACHE
    data = auth.get_auth_from_url_and_name(server_url, http_auth, overwrite_login_cache=True)
    assert data == (auth_username, 'password from TestKeyring')
    assert constants.AUTH_LOGIN_CACHE[server_url] == (auth_username, 'password from TestKeyring')
    create_msui_settings_file(f'{{"MSS_auth": {{"http://example.com": "{auth_username}"}}}}')
    read_config_file()
    data = auth.get_auth_from_url_and_name("http://example.com/something", http_auth, overwrite_login_cache=False)
    assert data == (None, None)
