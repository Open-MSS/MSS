# -*- coding: utf-8 -*-
"""

    mslib.msui.mscolab_connect_dialog
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Window to display authentication details for mscolab

    This file is part of MSS.

    :copyright: Copyright 2019-2026 by the MSS team, see AUTHORS.
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

import json
import logging
import requests
import webbrowser
from urllib.parse import urljoin

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QMessageBox

from mslib.msui.qt5 import ui_mscolab_connect_dialog as ui_conn
from mslib.utils.config import config_loader, modify_config_file
from mslib.utils.auth import get_password_from_keyring, save_password_to_keyring
from keyring.errors import NoKeyringError, PasswordSetError, InitError


class MSColab_ConnectDialog(QDialog, ui_conn.Ui_MSColabConnectDialog):
    """MSColab connect window class. Provides user interface elements to connect/disconnect,
       login, add new user to an MSColab Server. Also implements HTTP Server Authentication prompt.
    """

    def __init__(self, parent=None, mscolab=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        """
        super().__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.mscolab = mscolab

        # initialize server url as none
        self.mscolab_server_url = None
        self.auth = None

        self.setFixedSize(self.size())
        self.stackedWidget.setCurrentWidget(self.httpAuthPage)

        # disable widgets in login frame
        self.loginEmailLe.setEnabled(False)
        self.loginPasswordLe.setEnabled(False)
        self.loginBtn.setEnabled(False)
        self.addUserBtn.setEnabled(False)

        # add urls from settings to the combobox
        self.add_mscolab_urls()
        self.mscolab_url_changed(self.urlCb.currentText())

        # connect login, adduser, connect, login with idp, auth token submit buttons
        self.connectBtn.clicked.connect(self.connect_handler)
        self.connectBtn.setFocus()
        self.disconnectBtn.clicked.connect(self.disconnect_handler)
        self.disconnectBtn.hide()
        self.loginBtn.clicked.connect(self.login_handler)
        self.loginWithIDPBtn.clicked.connect(self.idp_login_handler)
        self.idpAuthTokenSubmitBtn.clicked.connect(self.idp_auth_token_submit_handler)
        self.addUserBtn.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.newuserPage))

        # enable login button only if email and password are entered
        self.loginEmailLe.textChanged[str].connect(self.mscolab_login_changed)
        self.loginPasswordLe.textChanged[str].connect(self.enable_login_btn)

        self.urlCb.editTextChanged.connect(self.mscolab_url_changed)

        # connect new user dialogbutton
        self.newUserBb.accepted.connect(self.new_user_handler)
        self.newUserBb.rejected.connect(lambda: self.stackedWidget.setCurrentWidget(self.loginPage))

        # connecting slot to clear all input widgets while switching tabs
        self.stackedWidget.currentChanged.connect(self.page_switched)

    def mscolab_url_changed(self, text):
        self.httpPasswordLe.setText(
            get_password_from_keyring("MSCOLAB_AUTH_" + text, config_loader(dataset="MSCOLAB_auth_user_name")))

    def mscolab_login_changed(self, text):
        self.loginPasswordLe.setText(
            get_password_from_keyring(self.mscolab_server_url, text))

    def page_switched(self, index):
        # clear all text in add user widget
        self.newUsernameLe.setText("")
        self.newEmailLe.setText("")
        self.newPasswordLe.setText("")
        self.newConfirmPasswordLe.setText("")

    def set_status(self, _type="Error", msg=""):
        if _type == "Error":
            _msg = f"⚠ {msg}"
            self.statusLabel.setOpenExternalLinks(True)
            self.statusLabel.setStyleSheet("color: red;")
        elif _type == "Success":
            self.statusLabel.setStyleSheet("color: green;")
            _msg = f"✓ {msg}"
        else:
            self.statusLabel.setStyleSheet("")
            _msg = f"ⓘ {msg}"
        self.statusLabel.setText(_msg)
        # windows can have a cp1252 encoding, don't use special chars
        logging.debug("set_status: %s", msg)
        QtWidgets.QApplication.processEvents()

    def add_mscolab_urls(self):
        url_list = config_loader(dataset="default_MSCOLAB")
        combo_box_urls = [self.urlCb.itemText(_i) for _i in range(self.urlCb.count())]
        for url in (_url for _url in url_list if _url not in combo_box_urls):
            self.urlCb.addItem(url)

    def enable_login_btn(self):
        self.loginBtn.setEnabled(self.loginEmailLe.text() != "" and self.loginPasswordLe.text() != "")

    def connect_handler(self):
        try:
            url = str(self.urlCb.currentText())
            auth = config_loader(dataset="MSCOLAB_auth_user_name"), self.httpPasswordLe.text()
            session = requests.Session()
            session.auth = auth
            session.headers.update({'x-test': 'true'})
            response = session.get(
                urljoin(url, 'status'), timeout=tuple(config_loader(dataset="MSCOLAB_timeout")))
            if response.status_code == 401:
                self.set_status("Error", 'Server authentication data were incorrect.')
            elif response.status_code == 200:
                self.stackedWidget.setCurrentWidget(self.loginPage)
                self.set_status("Success", "Successfully connected to MSColab server.")
                # disable url input
                self.urlCb.setEnabled(False)

                # enable/disable appropriate widgets in login frame
                self.loginBtn.setEnabled(False)
                self.addUserBtn.setEnabled(True)
                self.loginEmailLe.setEnabled(True)
                self.loginPasswordLe.setEnabled(True)

                try:
                    idp_enabled = json.loads(response.text)["use_saml2"]
                except (json.decoder.JSONDecodeError, KeyError):
                    idp_enabled = False

                try:
                    direct_login = json.loads(response.text)["direct_login"]
                except (json.decoder.JSONDecodeError, KeyError):
                    direct_login = True

                if not direct_login:
                    # Hide user creation when this is disabled on the server
                    self.addUserBtn.setHidden(True)
                    self.clickNewUserLabel.setHidden(True)

                if not idp_enabled:
                    # Hide login by identity provider if IDP login disabled
                    self.loginWithIDPBtn.setHidden(True)

                self.mscolab_server_url = url
                self.auth = auth
                save_password_to_keyring("MSCOLAB_AUTH_" + url, auth[0], auth[1])

                url_list = config_loader(dataset="default_MSCOLAB")
                if self.mscolab_server_url not in url_list:
                    ret = QMessageBox.question(
                        self, self.tr("Update Server List"),
                        self.tr("You are using a new MSColab server. "
                                "Should your settings file be updated by adding the new server?"),
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if ret == QMessageBox.Yes:
                        url_list = [self.mscolab_server_url] + url_list
                        modify_config_file({"default_MSCOLAB": url_list,
                                            "mscolab_server_url": self.mscolab_server_url})

                # Fill Email and Password fields from config
                self.loginEmailLe.setText(
                    config_loader(dataset="MSS_auth").get(self.mscolab_server_url))
                self.mscolab_login_changed(self.loginEmailLe.text())
                self.enable_login_btn()
                self.loginBtn.setFocus()

                # Change connect button text and connect disconnect handler
                self.connectBtn.hide()
                self.disconnectBtn.show()
            else:
                logging.error("Error %s", response)
                self.set_status("Error", "Some unexpected error occurred. Please try again.")
        except requests.exceptions.SSLError:
            logging.debug("Certificate Verification Failed")
            self.set_status("Error", "Certificate Verification Failed.")
        except requests.exceptions.InvalidSchema:
            logging.debug("invalid schema of url")
            self.set_status("Error", "Invalid Url Scheme.")
        except requests.exceptions.InvalidURL:
            logging.debug("invalid url")
            self.set_status("Error", "Invalid URL.")
        except requests.exceptions.ConnectionError:
            logging.debug("MSColab server isn't active")
            self.set_status("Error", "MSColab server isn't active.")
        except Exception as ex:
            logging.error("Error %s %s", type(ex), str(ex))
            self.set_status("Error", "Some unexpected error occurred. Please try again.")

    def disconnect_handler(self):
        self.mscolab.close_external_windows()
        self.urlCb.setEnabled(True)

        # enable/disable appropriate widgets in login frame
        self.loginBtn.setEnabled(False)
        self.addUserBtn.setEnabled(False)
        self.loginEmailLe.setEnabled(False)
        self.loginPasswordLe.setEnabled(False)

        # clear text
        self.stackedWidget.setCurrentWidget(self.httpAuthPage)

        self.mscolab_server_url = None
        self.auth = None

        self.connectBtn.show()
        self.connectBtn.setFocus()
        self.disconnectBtn.hide()
        self.set_status("Info", 'Disconnected from server.')

    def login_handler(self):
        self.loginBtn.setEnabled(False)
        data = {
            "email": self.loginEmailLe.text(),
            "password": self.loginPasswordLe.text()
        }
        session = requests.Session()
        session.auth = self.auth
        session.headers.update({'x-test': 'true'})
        url = urljoin(self.mscolab_server_url, "token")
        url_recover_password = urljoin(self.mscolab_server_url, "reset_request")
        try:
            response = session.post(url, data=data, timeout=tuple(config_loader(dataset="MSCOLAB_timeout")))
            response.raise_for_status()
        except requests.exceptions.RequestException as ex:
            logging.error("unexpected error: %s %s %s", type(ex), url, ex)
            self.set_status(
                "Error",
                f'Failed to establish a new connection to "{self.mscolab_server_url}". Try again in a moment.',
            )
            self.disconnect_handler()
        else:
            if response.text == "False":
                # show status indicating about wrong credentials
                self.set_status("Error", 'Invalid credentials. Fix them, create a new user, or '
                                f'<a href="{url_recover_password}">recover your password</a>.')
                self.loginBtn.setEnabled(True)
            else:
                self.save_user_credentials_to_config_file(data["email"], data["password"])
                self.mscolab.after_login(data["email"], self.mscolab_server_url, response)

    def idp_login_handler(self):
        """Handle IDP login Button"""
        url_idp_login = urljoin(self.mscolab_server_url, "available_idps")
        webbrowser.open(url_idp_login, new=2)
        self.stackedWidget.setCurrentWidget(self.idpAuthPage)

    def idp_auth_token_submit_handler(self):
        """Handle IDP authentication token submission"""
        url_idp_login_auth = urljoin(self.mscolab_server_url, "idp_login_auth")
        user_token = self.idpAuthPasswordLe.text()

        try:
            data = {'token': user_token}
            response = requests.post(url_idp_login_auth, json=data,
                                     timeout=tuple(config_loader(dataset="MSCOLAB_timeout")))
            if response.status_code == 401:
                self.set_status("Error", 'Invalid token or token expired. Please try again')
                self.stackedWidget.setCurrentWidget(self.loginPage)

            elif response.status_code == 200:
                _json = response.json()
                token = _json["token"]
                user = _json["user"]

                data = {
                    "email": user["emailid"],
                    "password": token,
                }

                session = requests.Session()
                session.auth = self.auth
                session.headers.update({'x-test': 'true'})
                url = urljoin(self.mscolab_server_url, "token")

                response = session.post(url, data=data, timeout=tuple(config_loader(dataset="MSCOLAB_timeout")))
                response.raise_for_status()
                if response.text == "False":
                    # show status indicating about wrong credentials
                    self.set_status("Error", 'Invalid token. Please enter correct token')
                else:
                    self.mscolab.after_login(data["email"], self.mscolab_server_url, response)
                    self.set_status("Success", 'Succesfully logged into mscolab server')

        except requests.exceptions.RequestException as error:
            logging.error("unexpected error: %s %s %s", type(error), url, error)

    def save_user_credentials_to_config_file(self, emailid, password):
        try:
            save_password_to_keyring(service_name=self.mscolab_server_url, username=emailid, password=password)
        except (NoKeyringError, PasswordSetError, InitError) as ex:
            logging.warning("Can't use Keyring on your system:  %s" % ex)
        mss_auth = config_loader(dataset="MSS_auth")
        if mss_auth.get(self.mscolab_server_url) != emailid:
            ret = QMessageBox.question(
                self, self.tr("Update Credentials"),
                self.tr("You are using new credentials. "
                        "Should your settings file be updated with the new credentials?"),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ret == QMessageBox.Yes:
                mss_auth[self.mscolab_server_url] = emailid
                modify_config_file({"MSS_auth": mss_auth})

    def new_user_handler(self):
        # get mscolab /token http auth credentials from cache
        emailid = self.newEmailLe.text()
        password = self.newPasswordLe.text()
        re_password = self.newConfirmPasswordLe.text()
        username = self.newUsernameLe.text()
        fullname = self.newFullnameLe.text()
        if password != re_password:
            self.set_status("Error", 'Your passwords don\'t match.')
            return

        data = {
            "email": emailid,
            "password": password,
            "username": username,
            "fullname": fullname
        }
        session = requests.Session()
        session.auth = self.auth
        session.headers.update({'x-test': 'true'})
        url = urljoin(self.mscolab_server_url, "register")
        try:
            response = session.post(url, data=data, timeout=tuple(config_loader(dataset="MSCOLAB_timeout")))
        except requests.exceptions.RequestException as ex:
            logging.error("unexpected error: %s %s %s", type(ex), url, ex)
            self.set_status(
                "Error",
                f'Failed to establish a new connection to "{self.mscolab_server_url}". Try again in a moment.',
            )
            self.disconnect_handler()
            return

        if response.status_code == 204:
            self.set_status("Success", 'You are registered, confirm your email before logging in.')
            self.save_user_credentials_to_config_file(emailid, password)
            self.stackedWidget.setCurrentWidget(self.loginPage)
            self.loginEmailLe.setText(emailid)
            self.loginPasswordLe.setText(password)
        elif response.status_code == 201:
            self.set_status("Success", 'You are registered.')
            self.save_user_credentials_to_config_file(emailid, password)
            self.loginEmailLe.setText(emailid)
            self.loginPasswordLe.setText(password)
            self.login_handler()
        else:
            try:
                error_msg = response.json()["message"]
            except Exception as e:
                logging.debug("Unexpected error occurred %s", e)
                error_msg = "Unexpected error occurred. Please try again."
            self.set_status("Error", error_msg)
