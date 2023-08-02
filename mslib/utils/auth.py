# -*- coding: utf-8 -*-
"""

    mslib.utils.auth
    ~~~~~~~~~~~~~~~~

    handles passwords from the keyring for login and http_auuth


    To better understand of the code, look at the 'ships' example from
    chapter 14/16 of 'Rapid GUI Programming with Python and Qt: The
    Definitive Guide to PyQt Programming' (Mark Summerfield).

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

import logging
import keyring

from mslib.msui import constants


NAME = __name__


def del_password_from_keyring(service_name=NAME, username=""):
    """
    removes an entry by username and service_name from the keyring
    """
    if username.strip() != "":
        try:
            keyring.delete_password(service_name=service_name, username=username)
        except (keyring.errors.NoKeyringError, keyring.errors.PasswordDeleteError) as ex:
            logging.warning("Can't use Keyring on your system: %s" % ex)


def get_password_from_keyring(service_name=NAME, username=""):
    """
    When we request a username we use this function to fill in a form field with a password
    In this case by none existing credentials in the keyring we have to return an empty string
    """
    if username.strip() != "":
        try:
            cred = keyring.get_credential(service_name=service_name, username=username)
            if username is not None and cred is None:
                return ""
            elif cred is None:
                return None
            else:
                return cred.password
        except (keyring.errors.KeyringLocked, keyring.errors.InitError) as ex:
            logging.warn(ex)
            return None


def save_password_to_keyring(service_name=NAME, username="", password=""):
    """
    save a username and password for a given service_name
    """
    if "" not in (username.strip(), password.strip()):
        try:
            keyring.set_password(service_name=service_name, username=username, password=password)
        except keyring.errors.NoKeyringError as ex:
            logging.info("Can't use Keyring on your system: %s" % ex)


def get_auth_from_url_and_name(server_url, http_auth, overwrite_login_cache=True):
    """
    gets auth_username from http_auth and password from keyring for a given server_url
    """
    name = ""
    for url, auth_name in http_auth.items():
        if server_url == url:
            try:
                password = get_password_from_keyring(service_name=url, username=auth_name)
            except keyring.errors.NoKeyringError as ex:
                password = None
                logging.info("Can't use Keyring on your system: %s" % ex)
            if overwrite_login_cache and password is not None and password.strip() != "":
                constants.AUTH_LOGIN_CACHE[server_url] = (auth_name, password)
            name = auth_name
            break
    if name == "":
        name = None
    auth = constants.AUTH_LOGIN_CACHE.get(server_url, (name, None))
    return auth
