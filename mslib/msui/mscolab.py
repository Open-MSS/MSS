# -*- coding: utf-8 -*-
"""

    mslib.msui.mscolab
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Window to display authentication and operation details for mscolab


    To better understand of the code, look at the 'ships' example from
    chapter 14/16 of 'Rapid GUI Programming with Python and Qt: The
    Definitive Guide to PyQt Programming' (Mark Summerfield).

    This file is part of MSS.

    :copyright: Copyright 2019- Shivashis Padhi
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
import io
import sys
import json
import hashlib
import logging
import types
import fs
import functools
import requests
import re
import webbrowser
import mimetypes
import urllib.request
from urllib.parse import urljoin

from fs import open_fs
from PIL import Image, UnidentifiedImageError
from keyring.errors import NoKeyringError, PasswordSetError, InitError
import socketio

from mslib.msui import flighttrack as ft
from mslib.msui import mscolab_chat as mc
from mslib.msui import mscolab_admin_window as maw
from mslib.msui import mscolab_version_history as mvh
from mslib.msui import socket_control as sc
from mslib.msui.mscolab_exceptions import MSColabConnectionError

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap

from mslib.utils.auth import get_password_from_keyring, save_password_to_keyring
from mslib.utils.verify_user_token import verify_user_token as _verify_user_token
from mslib.utils.verify_waypoint_data import verify_waypoint_data
from mslib.utils.qt import get_open_filename, get_save_filename, dropEvent, dragEnterEvent, show_popup
from mslib.msui.qt5 import ui_mscolab_help_dialog as msc_help_dialog
from mslib.msui.qt5 import ui_add_operation_dialog as add_operation_ui
from mslib.msui.qt5 import ui_mscolab_merge_waypoints_dialog as merge_wp_ui
from mslib.msui.qt5 import ui_mscolab_connect_dialog as ui_conn
from mslib.msui.qt5 import ui_mscolab_profile_dialog as ui_profile
from mslib.msui.qt5 import ui_operation_archive as ui_opar
from mslib.msui import constants
from mslib.utils.config import config_loader, modify_config_file


def verify_user_token(func):
    if not hasattr(verify_user_token, "depth"):
        verify_user_token.depth = 0

    @functools.wraps(func)
    def wrapper(self, *args, **vargs):
        if self.mscolab_server_url is None:
            # in case of a forecd logout some QT events may still trigger MSCOLAB functions
            return
        verify_user_token.depth += 1
        try:
            if not _verify_user_token(self.mscolab_server_url, self.token):
                raise MSColabConnectionError("Your Connection is expired. New Login required!")
            assert self.mscolab_server_url is not None
            result = func(self, *args, **vargs)
            return result
        except (MSColabConnectionError, socketio.exceptions.SocketIOError) as ex:
            if verify_user_token.depth > 1:
                raise
            logging.error("%s %s", type(ex), ex)
            show_popup(self.ui, "Error", str(ex))
            self.logout()
        finally:
            verify_user_token.depth -= 1
    return wrapper


class MSColab_OperationArchiveBrowser(QDialog, ui_opar.Ui_OperationArchiveBrowser):
    def __init__(self, parent=None, mscolab=None):
        super().__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.mscolab = mscolab
        self.pbClose.clicked.connect(self.hide)
        self.pbUnarchiveOperation.setEnabled(False)
        self.pbUnarchiveOperation.clicked.connect(self.unarchive_operation)
        self.listArchivedOperations.itemClicked.connect(self.select_archived_operation)
        self.setModal(True)

    def select_archived_operation(self, item):
        logging.debug('select_inactive_operation')
        if item.access_level in ["creator", "admin"]:
            self.archived_op_id = item.op_id
            self.pbUnarchiveOperation.setEnabled(True)
        else:
            self.archived_op_id = None
            self.pbUnarchiveOperation.setEnabled(False)

    def unarchive_operation(self):
        if _verify_user_token(self.mscolab.mscolab_server_url, self.mscolab.token):
            logging.debug('unarchive_operation')
            try:
                res = self.mscolab.conn.request_post(
                    "update_operation",
                    {"op_id": self.archived_op_id,
                     "attribute": "active",
                     "value": "True"})
            except requests.exceptions.RequestException as e:
                logging.debug(e)
                show_popup(self.parent, "Error", "Some error occurred! Could not unarchive operation.")
                self.logout()
            else:
                if res.text == "True":
                    self.mscolab.reload_operations()
                else:
                    show_popup(self.parent, "Error", "Session expired, new login required")
                    self.mscolab.logout()
        else:
            show_popup(self.parent, "Error", "Your Connection is expired. New Login required!")
            self.mscolab.logout()


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
            msg = "⚠ " + msg
            self.statusLabel.setOpenExternalLinks(True)
            self.statusLabel.setStyleSheet("color: red;")
        elif _type == "Success":
            self.statusLabel.setStyleSheet("color: green;")
            msg = "✓ " + msg
        else:
            self.statusLabel.setStyleSheet("")
            msg = "ⓘ  " + msg
        self.statusLabel.setText(msg)
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
                urljoin(url, 'status'), timeout=tuple(tuple(config_loader(dataset="MSCOLAB_timeout"))))
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
                        modify_config_file({"default_MSCOLAB": url_list})

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
            response = requests.post(url_idp_login_auth, json=data, timeout=(2, 10))
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

                response = session.post(url, data=data, timeout=(2, 10))
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
        if password != re_password:
            self.set_status("Error", 'Your passwords don\'t match.')
            return

        data = {
            "email": emailid,
            "password": password,
            "username": username
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


class MSUIMscolab(QtCore.QObject):
    """
    Class for implementing MSColab functionalities
    """
    name = "Mscolab"

    signal_unarchive_operation = QtCore.pyqtSignal(int, name="signal_unarchive_operation")
    signal_operation_added = QtCore.pyqtSignal(int, str, name="signal_operation_added")
    signal_operation_removed = QtCore.pyqtSignal(int, name="signal_operation_removed")
    signal_login_mscolab = QtCore.pyqtSignal(str, str, name="signal_login_mscolab")
    signal_logout_mscolab = QtCore.pyqtSignal(name="signal_logout_mscolab")
    signal_listFlighttrack_doubleClicked = QtCore.pyqtSignal()
    signal_permission_revoked = QtCore.pyqtSignal(int)
    signal_render_new_permission = QtCore.pyqtSignal(int, str)

    def __init__(self, parent=None, local_operations_data=None):
        super().__init__(parent)
        self.ui = parent

        self.operation_archive_browser = MSColab_OperationArchiveBrowser(self.ui, self)
        self.operation_archive_browser.hide()
        self.ui.listInactiveOperationsMSC = self.operation_archive_browser.listArchivedOperations

        # connect mscolab help action from help menu
        self.ui.actionMSColabHelp.triggered.connect(self.open_help_dialog)
        self.ui.pbOpenOperationArchive.clicked.connect(self.open_operation_archive)

        # hide mscolab related widgets
        self.ui.usernameLabel.hide()
        self.ui.userOptionsTb.hide()
        self.ui.actionAddOperation.setEnabled(False)
        self.ui.activeOperationDesc.setHidden(True)
        self.hide_operation_options()

        # reset operation description label for flight tracks and open views
        self.ui.listFlightTracks.itemDoubleClicked.connect(self.listFlighttrack_itemDoubleClicked)
        self.ui.listViews.itemDoubleClicked.connect(
            lambda: self.ui.activeOperationDesc.setText("Select Operation to View Description."))

        # connect operation options menu actions
        self.ui.actionAddOperation.triggered.connect(self.add_operation_handler)
        self.ui.actionChat.triggered.connect(self.operation_options_handler)
        self.ui.actionVersionHistory.triggered.connect(self.operation_options_handler)
        self.ui.actionManageUsers.triggered.connect(self.operation_options_handler)
        self.ui.actionDeleteOperation.triggered.connect(self.operation_options_handler)
        self.ui.actionLeaveOperation.triggered.connect(self.operation_options_handler)
        self.ui.actionChangeCategory.triggered.connect(self.change_category_handler)
        self.ui.actionChangeDescription.triggered.connect(self.change_description_handler)
        self.ui.actionRenameOperation.triggered.connect(self.rename_operation_handler)
        self.ui.actionArchiveOperation.triggered.connect(self.archive_operation)
        self.ui.actionViewDescription.triggered.connect(self.view_description)

        self.ui.filterCategoryCb.currentIndexChanged.connect(self.operation_category_handler)
        # connect slot for handling operation options combobox
        self.ui.workLocallyCheckbox.stateChanged.connect(self.handle_work_locally_toggle)
        self.ui.serverOptionsCb.currentIndexChanged.connect(self.server_options_handler)

        # set up user menu and add to toolbutton
        self.user_menu = QtWidgets.QMenu()
        self.profile_action = self.user_menu.addAction("Profile", self.open_profile_window)
        self.user_menu.addSeparator()
        self.logout_action = self.user_menu.addAction("Logout", self.logout)
        self.ui.userOptionsTb.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.ui.userOptionsTb.setMenu(self.user_menu)
        # self.ui.userOptionsTb.setAutoRaise(True)
        # self.ui.userOptionsTb.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        # if token is None, not authorized, else authorized
        self.token = None
        # int to store new pid
        self.new_op_id = None
        # int to store active pid
        self.active_op_id = None
        # storing access_level to save network call
        self.access_level = None
        # storing operation_name to save network call
        self.active_operation_name = None
        # storing operation category to save network call
        self.active_operation_category = None
        # Storing operation list to pass to admin window
        self.operations = None
        # store active_flight_path here as object
        self.waypoints_model = None
        # Store active operation's file path
        self.local_ftml_file = None
        # Store active_operation_description
        self.active_operation_description = None
        # connection object to interact with sockets
        self.conn = None
        # operation window
        self.chat_window = None
        # Admin Window
        self.admin_window = None
        # Version History Window
        self.version_window = None
        # Merge waypoints dialog
        self.merge_dialog = None
        # Mscolab help dialog
        self.help_dialog = None
        # Profile dialog
        self.prof_diag = None
        # Mscolab Server URL
        self.mscolab_server_url = None
        # User email
        self.email = None
        # Display all categories by default
        self.selected_category = "*ANY*"
        # Gravatar image path
        self.gravatar = None

        # Service message text for flight-track changes (waypoints inserted, moved or deleted)
        self.lastChangeMessage = ""

        # set data dir, uri
        if local_operations_data is None:
            self.data_dir = config_loader(dataset="mss_dir")
        else:
            self.data_dir = local_operations_data
        self.create_dir()

    def _handle_font_bolding(self, item=None):
        font = QtGui.QFont()
        for i in range(self.ui.listOperationsMSC.count()):
            self.ui.listOperationsMSC.item(i).setFont(font)
        if item is not None:
            font.setBold(True)
            item.setFont(font)

    def _activate_first_local_flighttrack(self):
        self.ui.listFlightTracks.setCurrentRow(0)
        self.ui.activate_selected_flight_track()
        self.active_op_id = None

    @verify_user_token
    def view_description(self, _=None):
        try:
            response = self.conn.request_get(
                "creator_of_operation", {"op_id": self.active_op_id})
        except MSColabConnectionError:
            creator_name = "unknown"
        else:
            _json = response.json()
            creator_name = _json["username"]
        QMessageBox.information(
            self.ui, "Operation Description",
            f"<html>Creator: <b>{creator_name}</b><p>"
            f"Category: <b>{self.active_operation_category}</b><p>"
            "<p>"
            f"{self.active_operation_description}</html>")

    def open_operation_archive(self):
        self.operation_archive_browser.show()

    def create_dir(self):
        # ToDo this needs to be done earlier
        if '://' in self.data_dir:
            try:
                _ = fs.open_fs(self.data_dir)
            except fs.errors.CreateFailed:
                logging.error('Make sure that the FS url "%s" exists', self.data_dir)
                show_popup(self.ui, "Error", f'FS Url: "{self.data_dir}" does not exist!')
                sys.exit()
            except fs.opener.errors.UnsupportedProtocol:
                logging.error('FS url "%s" not supported', self.data_dir)
                show_popup(self.ui, "Error", f'FS Url: "{self.data_dir}" not supported!')
                sys.exit()
        else:
            _dir = os.path.expanduser(self.data_dir)
            if not os.path.exists(_dir):
                os.makedirs(_dir)

    def close_help_dialog(self):
        self.help_dialog = None

    def open_help_dialog(self):
        if self.help_dialog is not None:
            self.help_dialog.raise_()
            self.help_dialog.activateWindow()
        else:
            self.help_dialog = MscolabHelpDialog(self.ui)
            self.help_dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.help_dialog.destroyed.connect(self.close_help_dialog)
            self.help_dialog.show()

    def open_connect_window(self):
        self.connect_window = MSColab_ConnectDialog(parent=self.ui, mscolab=self)
        self.connect_window.setModal(True)
        self.connect_window.exec_()

    def after_login(self, emailid, url, response):
        logging.debug("after login %s %s", emailid, url)
        # emailid by direct call
        self.email = emailid
        self.connect_window.close()
        self.connect_window = None
        QtWidgets.QApplication.processEvents()
        # fill value of mscolab url if found in QSettings storage

        _json = response.json()
        self.token = _json["token"]
        self.user = _json["user"]
        self.mscolab_server_url = url

        if config_loader(dataset="MSCOLAB_skip_archived_operations"):
            self.ui.pbOpenOperationArchive.setEnabled(False)
            self.ui.pbOpenOperationArchive.setToolTip(
                "This button is disabled to the config option 'MSCOLAB_skip_archived_operations'")
        else:
            self.ui.pbOpenOperationArchive.setEnabled(True)
            self.ui.pbOpenOperationArchive.setToolTip("")

        # create socket connection here
        try:
            self.conn = sc.ConnectionManager(self.token, user=self.user, mscolab_server_url=self.mscolab_server_url)
        except Exception as ex:
            raise MSColabConnectionError("Couldn't create a socket connection. Maybe the MSColab server is too old."
                                         f"({ex}). New Login required!")
        else:
            self.conn.signal_operation_list_updated.connect(self.reload_operation_list)
            self.conn.signal_reload.connect(self.reload_window)
            self.conn.signal_new_permission.connect(self.render_new_permission)
            self.conn.signal_update_permission.connect(self.handle_update_permission)
            self.conn.signal_revoke_permission.connect(self.handle_revoke_permission)
            self.conn.signal_operation_deleted.connect(self.handle_operation_deleted)
            self.conn.signal_active_user_update.connect(self.update_active_user_label)

            self.ui.connectBtn.hide()
            self.ui.openOperationsGb.show()
            # display connection status
            transport_layer = self.conn.sio.transport()
            self.ui.mscStatusLabel.setText(self.ui.tr(
                f"Status: connected to '{self.mscolab_server_url}' by transport layer '{transport_layer}'"))
            # display username beside useroptions toolbutton
            self.ui.usernameLabel.setText(f"{self.user['username']}")
            self.ui.usernameLabel.show()
            self.ui.userOptionsTb.show()
            self.fetch_profile_image()
            # enable add operation menu action
            self.ui.actionAddOperation.setEnabled(True)

            # Populate open operations list
            ops = self.add_operations_to_ui()
            # Show category list
            self.show_categories_to_ui(ops)

            self.ui.activeOperationDesc.setHidden(False)
            self.ui.actionChangeCategory.setEnabled(False)
            self.ui.actionChangeDescription.setEnabled(False)
            self.ui.actionDeleteOperation.setEnabled(False)
            self.ui.filterCategoryCb.setEnabled(True)
            self.ui.actionViewDescription.setEnabled(False)

            self.signal_login_mscolab.emit(self.mscolab_server_url, self.token)

    def set_profile_pixmap(self, img_data):
        pixmap = QPixmap()
        pixmap.loadFromData(img_data)
        resized_pixmap = pixmap.scaled(64, 64)

        # ToDo : verify by a test if the condition can be simplified
        if (hasattr(self, 'profile_dialog') and self.profile_dialog is not None and
                hasattr(self.profile_dialog, 'gravatarLabel') and self.profile_dialog.gravatarLabel is not None):
            self.profile_dialog.gravatarLabel.setPixmap(resized_pixmap)

        icon = QtGui.QIcon()
        icon.addPixmap(resized_pixmap, QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.userOptionsTb.setIcon(icon)

    def fetch_profile_image(self, refresh=False):
        try:
            response = self.conn.request_get(
                "fetch_profile_image", {"user_id": str(self.user["id"])})
        except MSColabConnectionError:
            self.fetch_gravatar(refresh)
        else:
            self.set_profile_pixmap(response.content)

    def fetch_gravatar(self, refresh):
        # Display default gravatar if custom profile image is not set
        email_hash = hashlib.md5(bytes(self.email.encode('utf-8')).lower()).hexdigest()
        email_in_config = self.email in config_loader(dataset="gravatar_ids")
        gravatar_img_path = fs.path.join(constants.GRAVATAR_DIR_PATH, f"{email_hash}.png")
        config_fs = fs.open_fs(constants.MSUI_CONFIG_PATH)

        # refresh is used to fetch new gravatar associated with the email
        if refresh or email_in_config:
            # create directory to store cached gravatar images
            if not config_fs.exists("gravatars"):
                try:
                    config_fs.makedirs("gravatars")
                except fs.errors.CreateFailed:
                    logging.error('Creation of gravatar directory failed')
                    return
                except fs.opener.errors.UnsupportedProtocol:
                    logging.error('FS url not supported')
                    return

            # use cached image if refresh not requested
            if not refresh and email_in_config and \
                    config_fs.exists(fs.path.join("gravatars", f"{email_hash}.png")):
                self.set_gravatar(gravatar_img_path)
                return

            # fetch gravatar image
            gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}.png?s=80&d=404"
            try:
                urllib.request.urlretrieve(gravatar_url, gravatar_img_path)
                img = Image.open(gravatar_img_path)
                img.save(gravatar_img_path)
            except urllib.error.HTTPError:
                if refresh:
                    show_popup(self.prof_diag, "Error", "Gravatar not found")
                return
            except urllib.error.URLError:
                if refresh:
                    show_popup(self.prof_diag, "Error", "Could not fetch Gravatar")
                return

        if refresh and not email_in_config:
            show_popup(
                self.prof_diag,
                "Information",
                "Please add your email to the gravatar_ids section in your "
                "msui_settings.json to automatically fetch your gravatar",
                icon=1, )

        self.set_gravatar(gravatar_img_path)

    def set_gravatar(self, gravatar=None):
        self.gravatar = gravatar
        pixmap = QtGui.QPixmap(self.gravatar)
        # check if pixmap has correct image
        if pixmap.isNull():
            user_name = self.user["username"]
            try:
                # find the first alphabet in the user name to set appropriate gravatar
                first_alphabet = user_name[user_name.find(next(filter(str.isalpha, user_name)))].lower()
            except StopIteration:
                # fallback to default gravatar logo if no alphabets found in the user name
                first_alphabet = "default"
            pixmap = QtGui.QPixmap(f":/gravatars/default-gravatars/{first_alphabet}.png")
            self.gravatar = None
        icon = QtGui.QIcon()
        icon.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.Off)

        # set icon for user options toolbutton
        self.ui.userOptionsTb.setIcon(icon)

        # set icon for profile window
        if self.prof_diag is not None:
            self.profile_dialog.gravatarLabel.setPixmap(pixmap)

    def remove_gravatar(self):
        if self.gravatar is None:
            return

        # remove cached gravatar image if not found in config
        config_fs = fs.open_fs(constants.MSUI_CONFIG_PATH)
        if config_fs.exists("gravatars"):
            if fs.open_fs(constants.GRAVATAR_DIR_PATH).exists(fs.path.basename(self.gravatar)):
                fs.open_fs(constants.GRAVATAR_DIR_PATH).remove(fs.path.basename(self.gravatar))
                if self.email in config_loader(dataset="gravatar_ids"):
                    show_popup(
                        self.prof_diag,
                        "Information",
                        "Please remove your email from gravatar_ids section in your "
                        "msui_settings.json to not fetch gravatar automatically",
                        icon=1, )

        self.set_gravatar()

    def open_profile_window(self):
        def on_context_menu(point):
            self.gravatar_menu.exec_(self.profile_dialog.gravatarLabel.mapToGlobal(point))

        self.prof_diag = QDialog()
        self.profile_dialog = ui_profile.Ui_ProfileWindow()
        self.profile_dialog.setupUi(self.prof_diag)
        self.profile_dialog.buttonBox.accepted.connect(lambda: self.prof_diag.close())
        self.profile_dialog.usernameLabel_2.setText(self.user['username'])
        self.profile_dialog.mscolabURLLabel_2.setText(self.mscolab_server_url)
        self.profile_dialog.emailLabel_2.setText(self.email)
        self.profile_dialog.deleteAccountBtn.clicked.connect(self.delete_own_account)
        self.profile_dialog.uploadImageBtn.clicked.connect(self.upload_image)

        # add context menu for right click on image
        self.gravatar_menu = QtWidgets.QMenu()
        self.gravatar_menu.addAction('Fetch Gravatar', lambda: self.fetch_profile_image(refresh=True))
        self.gravatar_menu.addAction('Remove Gravatar', lambda: self.remove_gravatar())
        self.profile_dialog.gravatarLabel.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.profile_dialog.gravatarLabel.customContextMenuRequested.connect(on_context_menu)

        self.prof_diag.show()
        self.fetch_profile_image()

    @verify_user_token
    def upload_image(self, _=None):
        file_name, _ = QFileDialog.getOpenFileName(self.prof_diag, "Open Image", "",
                                                   "Image (*.png *.gif *.jpg *.jpeg *.bpm)")
        if file_name:
            # Determine the image format
            mime_type, _ = mimetypes.guess_type(file_name)
            file_format = mime_type.split('/')[1].upper()
            try:
                # Resize the image and set profile image pixmap
                image = Image.open(file_name)
                image = image.resize((64, 64), Image.LANCZOS)
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format=file_format)
                img_byte_arr.seek(0)
                self.set_profile_pixmap(img_byte_arr.getvalue())

                # Prepare the file data for upload
                try:
                    img_byte_arr.seek(0)  # Reset buffer position
                    response = self.conn.request_post(
                        "upload_profile_image",
                        {"user_id": str(self.user["id"])},
                        {'image': (os.path.basename(file_name), img_byte_arr, mime_type)})

                    # Check response status
                    if response.status_code == 200:
                        QMessageBox.information(self.prof_diag, "Success", "Image uploaded successfully")
                        self.fetch_profile_image(refresh=True)
                    else:
                        QMessageBox.critical(self.prof_diag, "Error", f"Failed to upload image: {response.text}")

                except requests.exceptions.RequestException as e:
                    QMessageBox.critical(self.prof_diag, "Error", f"Error occurred: {e}")

            except UnidentifiedImageError as e:
                QMessageBox.critical(self.prof_diag, "Error",
                                     f'Cannot identify image file. Please check the file format. Error : {e}')
            except OSError as e:
                QMessageBox.critical(self.prof_diag, "Error",
                                     f'Cannot identify image file. Please check the file format. Error: {e}')

    @verify_user_token
    def delete_own_account(self, _=None):
        reply = QMessageBox.question(
            self.ui, self.tr('Continue?'),
            self.tr("You're about to delete your account. You cannot undo this operation!"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        try:
            response = self.conn.request_post("delete_own_account")
        except requests.exceptions.RequestException as ex:
            raise MSColabConnectionError(f"Some error occurred ({ex})! Please reconnect.")
        else:
            if response.status_code == 200 and response.json()["success"] is True:
                self.logout()

    @verify_user_token
    def add_operation_handler(self, _=None):
        def check_and_enable_operation_accept():
            if (self.add_proj_dialog.path.text() != "" and
                    self.add_proj_dialog.description.toPlainText() != "" and
                    self.add_proj_dialog.category.text() != ""):
                self.add_proj_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
            else:
                self.add_proj_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        def browse():
            import_type = self.add_proj_dialog.cb_ImportType.currentText()
            file_type = ["Flight track (*.ftml)"]
            if import_type != 'FTML':
                file_type = [f"Flight track (*.{self.ui.import_plugins[import_type][1]})"]

            file_path = get_open_filename(
                self.ui, "Open Flighttrack file", "", ';;'.join(file_type))
            if file_path is not None:
                file_name = fs.path.basename(file_path)
                if file_path.endswith('ftml'):
                    with open_fs(fs.path.dirname(file_path)) as file_dir:
                        file_content = file_dir.readtext(file_name)
                else:
                    function = self.ui.import_plugins[import_type][0]
                    ft_name, waypoints = function(file_path)
                    model = ft.WaypointsTableModel(waypoints=waypoints)
                    xml_doc = model.get_xml_doc()
                    file_content = xml_doc.toprettyxml(indent="  ", newl="\n")
                self.add_proj_dialog.f_content = file_content
                self.add_proj_dialog.selectedFile.setText(file_name)

        self.proj_diag = QDialog()
        self.add_proj_dialog = add_operation_ui.Ui_addOperationDialog()
        self.add_proj_dialog.setupUi(self.proj_diag)
        self.add_proj_dialog.f_content = None
        self.add_proj_dialog.buttonBox.accepted.connect(self.add_operation)
        self.add_proj_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.add_proj_dialog.path.textChanged.connect(check_and_enable_operation_accept)
        self.add_proj_dialog.description.textChanged.connect(check_and_enable_operation_accept)
        self.add_proj_dialog.category.textChanged.connect(check_and_enable_operation_accept)
        self.add_proj_dialog.browse.clicked.connect(browse)
        self.add_proj_dialog.category.setText(config_loader(dataset="MSCOLAB_category"))

        # sets types from defined import menu
        import_menu = self.ui.menuImportFlightTrack
        for im_action in import_menu.actions():
            self.add_proj_dialog.cb_ImportType.addItem(im_action.text())
        self.proj_diag.show()

    @verify_user_token
    def add_operation(self):
        logging.debug("add_operation")
        path = self.add_proj_dialog.path.text()
        description = self.add_proj_dialog.description.toPlainText()
        category = self.add_proj_dialog.category.text()
        if not path:
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Path can\'t be empty')
            return
        elif not description:
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Description can\'t be empty')
            return
        # same regex as for path validation
        elif not re.match("^[a-zA-Z0-9_-]*$", category):
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Category can\'t contain spaces or special characters')
            return
        # regex checks if the whole path from beginning to end only contains alphanumerical characters or _ and -
        elif not re.match("^[a-zA-Z0-9_-]*$", path):
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Path can\'t contain spaces or special characters')
            return

        data = {"path": path,
                "description": description,
                "category": category}
        if self.add_proj_dialog.f_content is not None:
            data["content"] = self.add_proj_dialog.f_content
        try:
            response = self.conn.request_post("create_operation", data)
        except requests.exceptions.RequestException as ex:
            raise MSColabConnectionError(f"Some error occurred ({ex})! Please reconnect.")
        if response.text == "True":
            QMessageBox.information(
                self.ui, "Creation successful",
                "Your operation was created successfully.",
            )
            op_id = self.get_recent_op_id()
            self.new_op_id = op_id
            self.conn.handle_new_operation(op_id)
            self.signal_operation_added.emit(op_id, path)
        else:
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('The path already exists')

    @verify_user_token
    def get_recent_op_id(self):
        """
        get most recent operation's op_id
        """
        logging.debug('get_recent_op_id')
        skip_archived = config_loader(dataset="MSCOLAB_skip_archived_operations")
        response = self.conn.request_get("operations", {"skip_archived": skip_archived})
        if response.text == "False":
            raise MSColabConnectionError("Session expired, new login required")
        _json = response.json()
        operations = _json["operations"]
        op_id = None
        if operations:
            op_id = operations[-1]["op_id"]
        logging.debug("recent op_id %s", op_id)
        return op_id

    def operation_options_handler(self):
        if self.sender() == self.ui.actionChat:
            self.open_chat_window()
        elif self.sender() == self.ui.actionVersionHistory:
            self.open_version_history_window()
        elif self.sender() == self.ui.actionManageUsers:
            self.open_admin_window()
        elif self.sender() == self.ui.actionDeleteOperation:
            self.handle_delete_operation()
        elif self.sender() == self.ui.actionLeaveOperation:
            self.handle_leave_operation()

    @verify_user_token
    def open_chat_window(self):
        if self.active_op_id is None:
            return

        if self.chat_window is not None:
            self.chat_window.activateWindow()
            return

        self.chat_window = mc.MSColabChatWindow(
            self.token,
            self.active_op_id,
            self.user,
            self.active_operation_name,
            self.access_level,
            self.conn,
            mscolab_server_url=self.mscolab_server_url,
        )
        self.chat_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.chat_window.viewCloses.connect(self.close_chat_window)
        self.chat_window.reloadWindows.connect(self.reload_windows_slot)
        self.chat_window.show()

    def close_chat_window(self):
        self.chat_window.close()
        self.chat_window = None

    @verify_user_token
    def open_admin_window(self):
        if self.active_op_id is None:
            return

        if self.admin_window is not None:
            self.admin_window.activateWindow()
            return

        operations = [operation for operation in self.operations if operation["active"] is True]

        self.admin_window = maw.MSColabAdminWindow(
            self.token,
            self.active_op_id,
            self.user,
            self.active_operation_name,
            operations,
            self.conn,
            mscolab_server_url=self.mscolab_server_url,
        )
        self.admin_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.admin_window.viewCloses.connect(self.close_admin_window)
        self.admin_window.show()

    def close_admin_window(self):
        self.admin_window.close()
        self.admin_window = None

    @verify_user_token
    def open_version_history_window(self):
        if self.active_op_id is None:
            return

        if self.version_window is not None:
            self.version_window.activateWindow()
            return

        self.version_window = mvh.MSColabVersionHistory(self.token, self.active_op_id, self.user,
                                                        self.active_operation_name, self.conn,
                                                        mscolab_server_url=self.mscolab_server_url)
        self.version_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.version_window.viewCloses.connect(self.close_version_history_window)
        self.version_window.reloadWindows.connect(self.reload_windows_slot)
        self.version_window.show()

    def close_version_history_window(self):
        self.version_window.close()
        self.version_window = None

    def update_views(self):
        """
        used on permission revoke to update waypoint model to defaults
        """
        locations = config_loader(dataset="new_flighttrack_template")
        initial_waypoints = [ft.Waypoint(location=locations[0]), ft.Waypoint(location=locations[1])]
        waypoints_model = ft.WaypointsTableModel(name="", waypoints=initial_waypoints)
        self.waypoints_model = waypoints_model
        self.waypoints_model.changeMessageSignal.connect(self.handle_change_message)
        self.reload_view_windows()

    def close_external_windows(self):
        if self.prof_diag is not None:
            self.prof_diag.close()
            self.prof_diag = None
        if self.chat_window is not None:
            self.chat_window.close()
            self.chat_window = None
        if self.admin_window is not None:
            self.admin_window.close()
            self.admin_window = None
        if self.version_window is not None:
            self.version_window.close()
            self.version_window = None

    @verify_user_token
    def handle_delete_operation(self):
        logging.debug("handle_delete_operation")
        entered_operation_name, ok = QtWidgets.QInputDialog.getText(
            self.ui,
            self.ui.tr("Delete Operation"),
            self.ui.tr(
                f"You're about to delete the operation - '{self.active_operation_name}'. "
                f"Enter the operation name to confirm: "
            ),
        )
        if ok:
            if entered_operation_name == self.active_operation_name:
                try:
                    response = self.conn.request_post(
                        "delete_operation", {"op_id": self.active_op_id})
                except requests.exceptions.RequestException as ex:
                    raise MSColabConnectionError(f"Some error occurred ({ex})! Please reconnect.")
                else:
                    response.raise_for_status()
                    self.reload_operations()
                    self.signal_operation_removed.emit(self.active_op_id)
            else:
                show_popup(self.ui, "Error", "Entered operation name did not match!")

    @verify_user_token
    def handle_leave_operation(self):
        logging.debug("handle_leave_operation")
        reply = QMessageBox.question(
            self.ui, self.tr('Mission Support System'),
            self.tr("Do you want to leave this operation?"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                response = self.conn.request_post(
                    "delete_bulk_permissions",
                    {"op_id": self.active_op_id, "selected_userids": json.dumps([self.user["id"]])})
            except requests.exceptions.RequestException as ex:
                raise MSColabConnectionError(f"Some error occurred ({ex})! Please reconnect.")
            if response.text == "False":
                raise MSColabConnectionError("Your Connection is expired. New Login required!")
            response = response.json()
            if response["success"]:
                for window in self.ui.get_active_views():
                    window.handle_force_close()
                self.reload_operations()
            else:
                show_popup(self.ui, "Error", "Some error occurred! Could not leave operation.")

    def set_operation_desc_label(self, op_desc):
        self.active_operation_description = op_desc
        desc_count = len(str(self.active_operation_description))
        if desc_count < 95:
            self.ui.activeOperationDesc.setText(
                self.ui.tr(f"{self.active_operation_name}: {self.active_operation_description}"))
        else:
            self.ui.activeOperationDesc.setText(
                "Description is too long to show here, for long descriptions go "
                "to operations menu.")

    @verify_user_token
    def change_category_handler(self, _=None):
        logging.debug('change_category_handler')
        # only after login
        entered_operation_category, ok = QtWidgets.QInputDialog.getText(
            self.ui,
            self.ui.tr(f"{self.active_operation_name} - Change Category"),
            self.ui.tr(
                "You're about to change the operation category\n"
                "Enter new operation category: "
            ),
            text=self.active_operation_category
        )
        if ok:
            try:
                response = self.conn.request_post(
                    "update_operation",
                    {"op_id": self.active_op_id,
                     "attribute": 'category',
                     "value": entered_operation_category})
            except requests.exceptions.RequestException as ex:
                raise MSColabConnectionError(f"Some error occurred ({ex})! Please reconnect.")
            if response.text == "False":
                raise MSColabConnectionError("Your Connection is expired. New Login required!")
            self.active_operation_category = entered_operation_category
            self.reload_operation_list()
            QMessageBox.information(
                self.ui,
                "Update successful",
                "Category is updated successfully.",
            )

    @verify_user_token
    def change_description_handler(self, _=None):
        logging.debug('change_description_handler')
        # only after login
        entered_operation_desc, ok = QtWidgets.QInputDialog.getText(
            self.ui,
            self.ui.tr(f"{self.active_operation_name} - Change Description"),
            self.ui.tr(
                "You're about to change the operation description\n"
                "Enter new operation description: "
            ),
            text=self.active_operation_description
        )
        if ok:
            try:
                response = self.conn.request_post(
                    "update_operation",
                    {"op_id": self.active_op_id,
                     "attribute": 'description',
                     "value": entered_operation_desc})
            except requests.exceptions.RequestException as ex:
                raise MSColabConnectionError(f"Some error occurred ({ex})! Please reconnect.")
            if response.text == "False":
                raise MSColabConnectionError("Your Connection is expired. New Login required!")
            # Update active operation description label
            self.set_operation_desc_label(entered_operation_desc)

            self.reload_operation_list()
            QMessageBox.information(
                self.ui,
                "Update successful",
                "Description is updated successfully.",
            )

    @verify_user_token
    def rename_operation_handler(self, _=None):
        logging.debug('rename_operation_handler')
        # only after login
        entered_operation_name, ok = QtWidgets.QInputDialog.getText(
            self.ui,
            self.ui.tr("Rename Operation"),
            self.ui.tr(
                f"You're about to rename the operation - '{self.active_operation_name}' "
                f"Enter new operation name: "
            ),
            text=f"{self.active_operation_name}",
        )
        if ok:
            try:
                response = self.conn.request_post(
                    "update_operation",
                    {"op_id": self.active_op_id,
                     "attribute": 'path',
                     "value": entered_operation_name})
            except requests.exceptions.RequestException as ex:
                raise MSColabConnectionError(f"Some error occurred ({ex})! Please reconnect.")
            if response.text == "False":
                raise MSColabConnectionError("Your Connection is expired. New Login required!")
            # Update active operation name
            self.active_operation_name = entered_operation_name

            # Update active operation description
            self.set_operation_desc_label(self.active_operation_description)
            self.reload_operation_list()
            self.reload_windows_slot()
            # Update other user's operation list
            self.conn.signal_operation_list_updated.connect(self.reload_operation_list)

            QMessageBox.information(
                self.ui,
                "Rename successful",
                "Operation is renamed successfully.",
            )

    @verify_user_token
    def handle_work_locally_toggle(self, _=None):
        if self.ui.workLocallyCheckbox.isChecked():
            if self.version_window is not None:
                self.version_window.close()
            self.create_local_operation_file()
            self.local_ftml_file = fs.path.combine(
                self.data_dir,
                fs.path.join(
                    "local_colabdata", self.user["username"],
                    self.active_operation_name, "mscolab_operation.ftml"),
            )
            self.ui.workingStatusLabel.setText(
                self.ui.tr(
                    "Working Asynchronously.\nYour changes are only available to you. "
                    "Use the 'Server Options' drop-down menu below to Save to or Fetch from the server.")
            )
            self.ui.serverOptionsCb.show()
            self.reload_local_wp()
        else:
            self.local_ftml_file = None
            self.ui.workingStatusLabel.setText(
                self.ui.tr(
                    "Working Online.\nAll your changes will be shared with everyone. "
                    "You can work on the operation asynchronously by checking the 'Work Asynchronously' box.")
            )
            self.ui.serverOptionsCb.hide()
            self.waypoints_model = None
            self.load_wps_from_server()
        self.show_operation_options()
        self.reload_view_windows()

    def create_local_operation_file(self):
        with open_fs(self.data_dir) as mss_dir:
            rel_file_path = fs.path.join('local_colabdata', self.user['username'],
                                         self.active_operation_name, 'mscolab_operation.ftml')
            if mss_dir.exists(rel_file_path) is True:
                return
            mss_dir.makedirs(fs.path.dirname(rel_file_path))
            server_data = self.waypoints_model.get_xml_content()
            mss_dir.writetext(rel_file_path, server_data)

    def reload_local_wp(self):
        self.waypoints_model = ft.WaypointsTableModel(filename=self.local_ftml_file, data_dir=self.data_dir)
        self.waypoints_model.changeMessageSignal.connect(self.handle_change_message)
        self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)
        self.reload_view_windows()

    def operation_category_handler(self, update_operations=True):
        logging.debug('operation_category_handler')
        # only after_login
        if self.mscolab_server_url is not None:
            self.selected_category = self.ui.filterCategoryCb.currentText()
            if update_operations:
                self.add_operations_to_ui()
            if self.selected_category != "*ANY*":
                items = [self.ui.listOperationsMSC.item(i) for i in range(self.ui.listOperationsMSC.count())]
                row = 0
                for item in items:
                    if item.operation_category != self.selected_category:
                        self.ui.listOperationsMSC.takeItem(row)
                    else:
                        row += 1
            else:
                self.add_operations_to_ui()

    def server_options_handler(self, index):
        selected_option = self.ui.serverOptionsCb.currentText()
        self.ui.serverOptionsCb.blockSignals(True)
        self.ui.serverOptionsCb.setCurrentIndex(0)
        self.ui.serverOptionsCb.blockSignals(False)

        if selected_option == "Fetch From Server":
            self.fetch_wp_mscolab()
        elif selected_option == "Save To Server":
            self.save_wp_mscolab()

    @verify_user_token
    def fetch_wp_mscolab(self):
        server_xml = self.request_wps_from_server()
        server_waypoints_model = ft.WaypointsTableModel(xml_content=server_xml)
        self.merge_dialog = MscolabMergeWaypointsDialog(self.waypoints_model, server_waypoints_model, True, self.ui)
        self.merge_dialog.saveBtn.setDisabled(True)
        if self.merge_dialog.exec_():
            xml_content = self.merge_dialog.get_values()
            if xml_content is not None:
                self.waypoints_model = ft.WaypointsTableModel(xml_content=xml_content)
                self.waypoints_model.changeMessageSignal.connect(self.handle_change_message)
                self.waypoints_model.save_to_ftml(self.local_ftml_file)
                self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)
                self.reload_view_windows()
                show_popup(self.ui, "Success", "New Waypoints Fetched To Local File!", icon=1)
        self.merge_dialog.close()
        self.merge_dialog = None

    @verify_user_token
    def save_wp_mscolab(self, comment=None):
        server_xml = self.request_wps_from_server()
        server_waypoints_model = ft.WaypointsTableModel(xml_content=server_xml)
        self.merge_dialog = MscolabMergeWaypointsDialog(self.waypoints_model,
                                                        server_waypoints_model, parent=self.ui)
        self.merge_dialog.saveBtn.setDisabled(True)
        if self.merge_dialog.exec_():
            xml_content = self.merge_dialog.get_values()
            if xml_content is not None:
                self.conn.save_file(self.token, self.active_op_id, xml_content, comment=comment)
                self.waypoints_model = ft.WaypointsTableModel(xml_content=xml_content)
                self.waypoints_model.changeMessageSignal.connect(self.handle_change_message)
                self.waypoints_model.save_to_ftml(self.local_ftml_file)
                self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)
                self.reload_view_windows()
                show_popup(self.ui, "Success", "New Waypoints Saved To Server!", icon=1)
        self.merge_dialog.close()
        self.merge_dialog = None

    @verify_user_token
    def get_recent_operation(self):
        """
        get most recent operation
        """
        logging.debug('get_recent_operation')
        response = self.conn.request_get("operations")
        if response.text == "False":
            raise MSColabConnectionError("Session expired, new login required")
        response = response.json()
        operations = response["operations"]
        recent_operation = None
        if operations:
            recent_operation = operations[-1]
        return recent_operation

    @QtCore.pyqtSlot()
    def reload_operation_list(self):
        if self.mscolab_server_url is not None:
            self.reload_operations()

    @QtCore.pyqtSlot(int)
    def reload_window(self, value):
        if self.active_op_id != value or self.ui.workLocallyCheckbox.isChecked():
            return
        self.reload_wps_from_server()

    @QtCore.pyqtSlot()
    def reload_windows_slot(self):
        self.reload_window(self.active_op_id)

    @QtCore.pyqtSlot(int, int)
    def render_new_permission(self, op_id, u_id):
        """
        op_id: operation id
        u_id: user id

        to render new permission if added
        """
        logging.debug('render_new_permission')
        response = self.conn.request_get("user")
        if response.text != "False":
            response = response.json()
            if response['user']['id'] == u_id:
                operation = self.get_recent_operation()
                operation_desc = f'{operation["path"]} - {operation["access_level"]}'
                widgetItem = QtWidgets.QListWidgetItem(operation_desc, parent=self.ui.listOperationsMSC)
                widgetItem.op_id = operation["op_id"]
                widgetItem.operation_category = operation["category"]
                widgetItem.operation_path = operation["path"]
                widgetItem.access_level = operation["access_level"]
                widgetItem.active_operation_description = operation["description"]
                self.ui.listOperationsMSC.addItem(widgetItem)
                self.signal_render_new_permission.emit(operation["op_id"], operation["path"])
            if self.chat_window is not None:
                self.chat_window.load_users()
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    @QtCore.pyqtSlot(int, int, str)
    def handle_update_permission(self, op_id, u_id, access_level):
        """
        op_id: operation id
        u_id: user id
        access_level: updated access level

        function updates existing permissions and related control availability
        """
        logging.debug('handle_update_permission')
        if u_id == self.user["id"]:
            # update table of operations
            operation_name = None
            for i in range(self.ui.listOperationsMSC.count()):
                item = self.ui.listOperationsMSC.item(i)
                if item.op_id == op_id:
                    operation_name = item.operation_path
                    item.access_level = access_level
                    item.setText(f'{operation_name} - {item.access_level}')
                    break
            if operation_name is not None:
                show_popup(self.ui, "Permission Updated",
                           f"Your access level to operation - {operation_name} was updated to {access_level}!", 1)
            if op_id != self.active_op_id:
                return

            self.access_level = access_level
            # Close mscolab windows based on new access_level and update their buttons
            self.show_operation_options()

            # update view window nav elements if open
            for window in self.ui.get_active_views():
                if self.access_level == "viewer":
                    window.disable_navbar_action_buttons()
                else:
                    window.enable_navbar_action_buttons()

        # update chat window if open
        if self.chat_window is not None:
            self.chat_window.load_users()

    def delete_operation_from_list(self, op_id):
        logging.debug('delete operation op_id: %s and active_id is: %s' % (op_id, self.active_op_id))
        if self.active_op_id == op_id:
            logging.debug('delete_operation_from_list doing: %s' % op_id)
            self.update_views()
            self.active_op_id = None
            self.access_level = None
            self.active_operation_name = None
            # self.ui.workingStatusLabel.setEnabled(False)
            self.close_external_windows()
            self.hide_operation_options()
            # reset operation_description label text
            self.ui.activeOperationDesc.setText("Select Operation to View Description.")

        # Update operation list
        remove_item = None
        for i in range(self.ui.listOperationsMSC.count()):
            item = self.ui.listOperationsMSC.item(i)
            if item.op_id == op_id:
                remove_item = item
                break
        if remove_item is not None:
            logging.debug("remove_item: %s", remove_item)
            self.ui.listOperationsMSC.takeItem(self.ui.listOperationsMSC.row(remove_item))
            return remove_item.operation_path

    @QtCore.pyqtSlot(int, int)
    def handle_revoke_permission(self, op_id, u_id):
        logging.debug('handle_revoke_permission')
        if u_id == self.user["id"]:
            revoked_operation_currently_active = True if self.active_op_id == op_id else False
            operation_name = self.delete_operation_from_list(op_id)
            if operation_name is not None:
                if revoked_operation_currently_active:
                    self.ui.userCountLabel.hide()
                show_popup(self.ui, "Permission Revoked",
                           f'Your access to operation - "{operation_name}" was revoked!', icon=1)
                # on import permissions revoked name can not taken from the operation list,
                # because we update the list first by reloading it.
                show_popup(self.ui, "Permission Revoked", "Access to an operation was revoked")
                self.signal_permission_revoked.emit(op_id)

            if self.active_op_id == op_id:
                self._activate_first_local_flighttrack()

    @QtCore.pyqtSlot(int)
    def handle_operation_deleted(self, op_id):
        logging.debug('handle_operation_deleted %s %s', op_id, self.active_op_id)
        old_operation_name = self.active_operation_name
        old_active_id = self.active_op_id
        operation_name = self.delete_operation_from_list(op_id)
        if op_id == old_active_id:
            if operation_name is None:
                operation_name = old_operation_name
            show_popup(self.ui, "Information", f'Active operation "{operation_name}" is inaccessible!', icon=1)

    @QtCore.pyqtSlot(int, int)
    def update_active_user_label(self, op_id, count):
        # Update UI component which displays the number of active users
        if self.active_op_id == op_id:
            self.ui.userCountLabel.setText(f"Active Users: {count}")

    @QtCore.pyqtSlot(str)
    def handle_change_message(self, message):
        self.lastChangeMessage = message

    @verify_user_token
    def show_categories_to_ui(self, ops=None):
        """
        adds the list of operation categories to the UI
        """
        logging.debug('show_categories_to_ui')
        response = None
        if ops is not None:
            response = ops
        else:
            try:
                response = self.conn.request_get("operations")
            except requests.exceptions.MissingSchema:
                raise MSColabConnectionError("Session expired, new login required")
        if response is not None and response.text != "False":
            response = response.json()
            operations = response["operations"]
            self.ui.filterCategoryCb.currentIndexChanged.disconnect(self.operation_category_handler)
            self.ui.filterCategoryCb.clear()
            categories = set(["*ANY*"])
            for operation in operations:
                categories.add(operation["category"])
            categories.remove("*ANY*")
            categories = ["*ANY*"] + sorted(categories)
            category = config_loader(dataset="MSCOLAB_category")
            self.ui.filterCategoryCb.addItems(categories)
            if category in categories:
                index = categories.index(category)
                self.ui.filterCategoryCb.setCurrentIndex(index)
            self.operation_category_handler(update_operations=False)
            self.ui.filterCategoryCb.currentIndexChanged.connect(self.operation_category_handler)

    @verify_user_token
    def add_operations_to_ui(self):
        logging.debug('add_operations_to_ui')
        skip_archived = config_loader(dataset="MSCOLAB_skip_archived_operations")
        response = self.conn.request_get("operations", {"skip_archived": skip_archived})
        if response.text == "False":
            raise MSColabConnectionError("Session expired, new login required")

        _json = response.json()
        self.operations = _json["operations"]
        operations = sorted(self.operations, key=lambda k: k["path"].lower())
        self.ui.listOperationsMSC.clear()
        self.operation_archive_browser.listArchivedOperations.clear()
        new_operation = None
        active_operation = None
        for operation in operations:
            operation_desc = f'{operation["path"]} - {operation["access_level"]}'
            widgetItem = QtWidgets.QListWidgetItem(operation_desc)
            widgetItem.op_id = operation["op_id"]
            widgetItem.operation_category = operation["category"]
            widgetItem.operation_path = operation["path"]
            widgetItem.access_level = operation["access_level"]
            widgetItem.active_operation_description = operation["description"]
            try:
                # compatibility to 7.x
                # a newer server can distinguish older operations and move those into inactive state
                widgetItem.active = operation["active"]
            except KeyError:
                widgetItem.active = True
            if widgetItem.active:
                self.ui.listOperationsMSC.addItem(widgetItem)
                if widgetItem.op_id == self.active_op_id:
                    active_operation = widgetItem
                if widgetItem.op_id == self.new_op_id:
                    new_operation = widgetItem
            else:
                self.operation_archive_browser.listArchivedOperations.addItem(widgetItem)
        if new_operation is not None:
            logging.debug("%s %s %s", new_operation, self.new_op_id, self.active_op_id)
            self.ui.listOperationsMSC.itemActivated.emit(new_operation)
        elif active_operation is not None:
            logging.debug("%s %s %s", new_operation, self.new_op_id, self.active_op_id)
            self.ui.listOperationsMSC.itemActivated.emit(active_operation)
        elif self.active_op_id is not None:
            logging.debug("%s %s %s", new_operation, self.new_op_id, self.active_op_id)
            show_popup(self.ui, "Information",
                       f'Active operation "{self.active_operation_name}" is inaccessible!', icon=1)
            self._activate_first_local_flighttrack()

        self.ui.listOperationsMSC.itemActivated.connect(self.set_active_op_id)
        self.new_op_id = None
        return response

    def show_operation_options_in_inactivated_state(self, access_level):
        logging.debug('show_operation_options_in_inactivated_state')
        self.ui.actionUnarchiveOperation.setEnabled(False)
        if access_level in ["creator", "admin"]:
            self.ui.actionUnarchiveOperation.setEnabled(True)

    @verify_user_token
    def archive_operation(self, _):
        logging.debug("handle_archive_operation")
        ret = QMessageBox.warning(
            self.ui, self.tr("Mission Support System"),
            self.tr(f"Do you want to archive this operation '{self.active_operation_name}'?"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret == QMessageBox.Yes:
            try:
                response = self.conn.request_post(
                    "update_operation",
                    {"op_id": self.active_op_id,
                     "attribute": "active",
                     "value": "False"})
            except requests.exceptions.RequestException as ex:
                raise MSColabConnectionError(f"Some error occurred ({ex})! Could not archive operation.")
            response.raise_for_status()
            self.reload_operations()
            self.signal_operation_removed.emit(self.active_op_id)
            logging.debug("activate local")
            self._activate_first_local_flighttrack()

    @verify_user_token
    def set_active_op_id(self, item):
        logging.debug('set_active_op_id %s %s %s', item, item.op_id, self.active_op_id)
        if not self.ui.local_active and item.op_id == self.active_op_id:
            return

        # close all hanging window
        self.close_external_windows()
        self.hide_operation_options()

        # Turn off work locally toggle
        self.ui.workLocallyCheckbox.blockSignals(True)
        self.ui.workLocallyCheckbox.setChecked(False)
        self.ui.workLocallyCheckbox.blockSignals(False)

        # set active_op_id here
        self.active_op_id = item.op_id
        self.access_level = item.access_level
        self.active_operation_name = item.operation_path
        self.active_operation_description = item.active_operation_description
        self.active_operation_category = item.operation_category
        self.waypoints_model = None

        self.signal_unarchive_operation.emit(self.active_op_id)

        # Set active operation description
        self.set_operation_desc_label(self.active_operation_description)
        # set active flightpath here
        self.load_wps_from_server()
        # display working status
        self.ui.workingStatusLabel.setText(
            self.ui.tr(
                "Working Online.\nAll your changes will be shared with everyone. "
                "You can work on the operation asynchronously by checking the 'Work Asynchronously' box.")
        )
        # self.ui.workingStatusLabel.show()
        # enable access level specific widgets
        self.show_operation_options()

        # change font style for selected
        self._handle_font_bolding(item)

        # set new waypoints model to open views
        for window in self.ui.get_active_views():
            window.setFlightTrackModel(self.waypoints_model)
            if self.access_level == "viewer":
                window.disable_navbar_action_buttons()
            else:
                window.enable_navbar_action_buttons()

        self.ui.switch_to_mscolab()

        # Enable the active user count label
        self.ui.userCountLabel.show()

        # call select operation method from connection manager to emit signal
        self.conn.select_operation(item.op_id)

    def switch_to_local(self):
        logging.debug('switch_to_local')
        self.ui.local_active = True
        if self.active_op_id is not None:
            self._handle_font_bolding()

            # close all hanging operation option windows
            self.close_external_windows()
            self.hide_operation_options()
            self.ui.menu_handler()
        self.active_op_id = None

    def show_operation_options(self):
        self.ui.actionChat.setEnabled(False)
        self.ui.actionVersionHistory.setEnabled(False)
        self.ui.actionManageUsers.setEnabled(False)
        self.ui.actionRenameOperation.setEnabled(False)
        self.ui.actionLeaveOperation.setEnabled(True)
        self.ui.actionDeleteOperation.setEnabled(False)
        self.ui.actionChangeCategory.setEnabled(False)
        self.ui.actionChangeDescription.setEnabled(False)
        self.ui.actionArchiveOperation.setEnabled(False)
        self.ui.actionViewDescription.setEnabled(True)
        self.ui.menuProperties.setEnabled(True)

        if self.access_level == "viewer":
            self.ui.menuImportFlightTrack.setEnabled(False)
            return

        if self.access_level in ["creator", "admin", "collaborator"]:
            if self.ui.workLocallyCheckbox.isChecked():
                self.ui.actionChat.setEnabled(True)
            else:
                self.ui.actionChat.setEnabled(True)
                self.ui.actionVersionHistory.setEnabled(True)
            self.ui.workLocallyCheckbox.setEnabled(True)
        else:
            if self.version_window is not None:
                self.version_window.close()
            if self.chat_window is not None:
                self.chat_window.close()
            self.ui.workLocallyCheckbox.setEnabled(False)
            self.ui.serverOptionsCb.hide()

        if self.access_level in ["creator", "admin"]:
            self.ui.actionManageUsers.setEnabled(True)
            self.ui.actionChangeCategory.setEnabled(True)
            self.ui.actionChangeDescription.setEnabled(True)
            self.ui.filterCategoryCb.setEnabled(True)
            self.ui.actionRenameOperation.setEnabled(True)
            self.ui.actionArchiveOperation.setEnabled(True)
        else:
            if self.admin_window is not None:
                self.admin_window.close()

        if self.access_level in ["creator"]:
            self.ui.actionDeleteOperation.setEnabled(True)
            self.ui.actionLeaveOperation.setEnabled(False)

        self.ui.menuImportFlightTrack.setEnabled(True)

    def hide_operation_options(self):
        self.ui.actionChat.setEnabled(False)
        self.ui.actionVersionHistory.setEnabled(False)
        self.ui.actionManageUsers.setEnabled(False)
        self.ui.actionViewDescription.setEnabled(False)
        self.ui.actionLeaveOperation.setEnabled(False)
        self.ui.actionRenameOperation.setEnabled(False)
        self.ui.actionArchiveOperation.setEnabled(False)
        self.ui.actionChangeCategory.setEnabled(False)
        self.ui.actionChangeDescription.setEnabled(False)
        self.ui.actionDeleteOperation.setEnabled(False)
        self.ui.workLocallyCheckbox.setEnabled(False)
        self.ui.menuProperties.setEnabled(False)
        self.ui.serverOptionsCb.hide()
        # change working status label
        self.ui.workingStatusLabel.setText(self.ui.tr("\n\nNo Operation Selected"))

    @verify_user_token
    def request_wps_from_server(self):
        response = self.conn.request_get(
            "get_operation_by_id", {"op_id": self.active_op_id})
        if response.text != "False":
            xml_content = response.json()["content"]
            return xml_content
        else:
            raise MSColabConnectionError("Session expired, new login required")

    def load_wps_from_server(self):
        if self.ui.workLocallyCheckbox.isChecked():
            return
        xml_content = self.request_wps_from_server()
        if xml_content is not None:
            self.waypoints_model = ft.WaypointsTableModel(xml_content=xml_content)
            self.waypoints_model.changeMessageSignal.connect(self.handle_change_message)
            self.waypoints_model.name = self.active_operation_name
            self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)

    def reload_operations(self):
        logging.debug('reload_operations')
        ops = self.add_operations_to_ui()
        selected_category = self.ui.filterCategoryCb.currentText()
        self.show_categories_to_ui(ops)
        index = self.ui.filterCategoryCb.findText(selected_category, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.ui.filterCategoryCb.setCurrentIndex(index)

    def reload_wps_from_server(self):
        if self.active_op_id is None:
            return
        self.load_wps_from_server()
        self.reload_view_windows()

    @verify_user_token
    def handle_waypoints_changed(self, _1=None, _2=None, _3=None, version_name=None):
        logging.debug("handle_waypoints_changed")
        if self.ui.workLocallyCheckbox.isChecked():
            self.waypoints_model.save_to_ftml(self.local_ftml_file)
        else:
            xml_content = self.waypoints_model.get_xml_content()
            self.conn.save_file(self.token, self.active_op_id, xml_content, version_name=version_name, comment=None)
            # Reset the last change message to make sure that it is used only once
            self.lastChangeMessage = ""

    def reload_view_windows(self):
        logging.debug("reload_view_windows")
        if self.ui.local_active:
            return

        for window in self.ui.get_active_views():
            window.setFlightTrackModel(self.waypoints_model)
            if hasattr(window, 'mpl'):
                if window.name in ("Top View", "Table View"):
                    # Make Roundtrip Button
                    window.btRoundtrip.setEnabled(window.is_roundtrip_possible())
                try:
                    window.mpl.canvas.waypoints_interactor.redraw_figure()
                except AttributeError as err:
                    logging.error("%s" % err)

    @verify_user_token
    def handle_import_msc(self, file_path, extension, function, pickertype):
        logging.debug("handle_import_msc")
        if self.active_op_id is None:
            return
        if file_path is None:
            return
        dir_path, file_name = fs.path.split(file_path)
        file_name = fs.path.basename(file_path)
        if function is None:
            with open_fs(dir_path) as file_dir:
                xml_content = file_dir.readtext(file_name)
                if not verify_waypoint_data(xml_content):
                    show_popup(self.ui, "Import Failed", f"The file - {file_name}, does not contain valid XML")
                    return
            try:
                model = ft.WaypointsTableModel(xml_content=xml_content)
            except SyntaxError:
                show_popup(self.ui, "Import Failed", f"The file - {file_name}, does not contain valid XML")
                return
        else:
            # _function = self.ui.import_plugins[file_ext[1:]]
            _, new_waypoints = function(file_path)
            model = ft.WaypointsTableModel(waypoints=new_waypoints)
            xml_doc = self.waypoints_model.get_xml_doc()
            xml_content = xml_doc.toprettyxml(indent="  ", newl="\n")
        if not verify_waypoint_data(xml_content):
            show_popup(self.ui, "Import Failed", f"The file - {file_name}, was not imported!", 0)
            return
        self.waypoints_model.dataChanged.disconnect(self.handle_waypoints_changed)
        self.waypoints_model = model
        self.waypoints_model.changeMessageSignal.connect(self.handle_change_message)
        self.handle_waypoints_changed(version_name=file_name)
        self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)
        self.reload_view_windows()
        show_popup(self.ui, "Import Success", f"The file - {file_name}, was imported successfully!", 1)

    @verify_user_token
    def handle_export_msc(self, extension, function, pickertype):
        logging.debug("handle_export_msc")
        if self.active_op_id is None:
            return

        # Setting default filename path for filedialogue
        default_filename = f'{self.active_operation_name}.{extension}'
        file_name = get_save_filename(
            self.ui, "Export From Server",
            default_filename, f"Flight track (*.{extension})",
            pickertype=pickertype)
        if file_name is None:
            return
        if function is None:
            xml_doc = self.waypoints_model.get_xml_doc()
            dir_path, file_name = fs.path.split(file_name)
            with open_fs(dir_path).open(file_name, 'w') as file:
                xml_doc.writexml(file, indent="  ", addindent="  ", newl="\n", encoding="utf-8")
        else:
            name = fs.path.basename(file_name)
            function(file_name, name, self.waypoints_model.waypoints)
            show_popup(self.ui, "Export Success", f"The file - {file_name}, was exported successfully!", 1)

    def listFlighttrack_itemDoubleClicked(self):
        logging.debug("listFlighttrack_itemDoubleClicked")
        self.ui.activeOperationDesc.setText("Select Operation to View Description.")
        self.signal_listFlighttrack_doubleClicked.emit()

    def logout(self):
        logging.debug('logout')
        if self.mscolab_server_url is None:
            return
        self.ui.local_active = True
        self.ui.menu_handler()

        # disconnect socket
        if self.conn is not None:
            self.conn.disconnect()
            self.conn = None

        # close all hanging window
        self.close_external_windows()
        self.hide_operation_options()
        # delete token and show login widget-items
        self.token = None
        # delete active-operation-id
        self.active_op_id = None
        # delete active access_level
        self.access_level = None
        # delete active operation_name
        self.active_operation_name = None
        # delete local file name
        self.local_ftml_file = None
        # clear operation listing
        self.ui.listOperationsMSC.clear()
        # clear inactive operation listing
        self.operation_archive_browser.listArchivedOperations.clear()
        # clear mscolab url
        self.mscolab_server_url = None
        # clear operations list here
        self.ui.mscStatusLabel.setText(self.ui.tr("status: disconnected"))
        self.ui.usernameLabel.hide()
        self.ui.userOptionsTb.hide()
        self.ui.connectBtn.show()
        self.ui.connectBtn.setFocus()
        self.ui.openOperationsGb.hide()
        self.ui.actionAddOperation.setEnabled(False)
        # hide operation description
        self.ui.activeOperationDesc.setHidden(True)
        # reset description label text
        self.ui.activeOperationDesc.setText(self.ui.tr("Select Operation to View Description."))
        # set usernameLabel back to default
        self.ui.usernameLabel.setText("User")
        # Turn off work locally toggle
        self.ui.workLocallyCheckbox.blockSignals(True)
        self.ui.workLocallyCheckbox.setChecked(False)
        self.ui.workLocallyCheckbox.blockSignals(False)

        # remove temporary gravatar image
        config_fs = fs.open_fs(constants.MSUI_CONFIG_PATH)
        if config_fs.exists("gravatars") and self.gravatar is not None:
            if self.email not in config_loader(dataset="gravatar_ids") and \
                    fs.open_fs(constants.GRAVATAR_DIR_PATH).exists(fs.path.basename(self.gravatar)):
                fs.open_fs(constants.GRAVATAR_DIR_PATH).remove(fs.path.basename(self.gravatar))
        # clear gravatar image path
        self.gravatar = None
        # clear user email
        self.email = None

        # disable category change selector
        self.ui.filterCategoryCb.setEnabled(False)
        self.signal_logout_mscolab.emit()

        self.operation_archive_browser.hide()

        # reset profile image pixmap
        if hasattr(self, 'profile_dialog'):
            del self.profile_dialog
            self.profile_dialog = None

        # reset the user count label to 0
        self.ui.userCountLabel.setText("Active Users: 0")

        # activate first local flighttrack after logging out
        self._activate_first_local_flighttrack()


class MscolabMergeWaypointsDialog(QDialog, merge_wp_ui.Ui_MergeWaypointsDialog):
    def __init__(self, local_waypoints_model, server_waypoints_model, fetch=False, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.local_waypoints_model = local_waypoints_model
        self.server_waypoints_model = server_waypoints_model
        self.merge_waypoints_model = ft.WaypointsTableModel()
        self.localWaypointsTable.setModel(self.local_waypoints_model)
        self.serverWaypointsTable.setModel(self.server_waypoints_model)
        self.mergedWaypointsTable.setModel(self.merge_waypoints_model)
        self.mergedWaypointsTable.dropEvent = types.MethodType(dropEvent, self.mergedWaypointsTable)
        self.mergedWaypointsTable.dragEnterEvent = types.MethodType(dragEnterEvent, self.mergedWaypointsTable)

        self.xml_content = None
        self.local_waypoints_dict = {}
        self.server_waypoints_dict = {}
        self.merge_waypoints_list = []

        # Event Listeners
        self.overwriteBtn.clicked.connect(lambda: self.save_waypoints(self.local_waypoints_model))
        self.keepServerBtn.clicked.connect(lambda: self.save_waypoints(self.server_waypoints_model))
        self.saveBtn.clicked.connect(lambda: self.save_waypoints(self.merge_waypoints_model))
        self.localWaypointsTable.selectionModel().selectionChanged.connect(
            lambda selected, deselected:
            self.handle_selection(selected, deselected, self.local_waypoints_model, self.local_waypoints_dict)
        )
        self.serverWaypointsTable.selectionModel().selectionChanged.connect(
            lambda selected, deselected:
            self.handle_selection(selected, deselected, self.server_waypoints_model, self.server_waypoints_dict)
        )

        if fetch is True:
            self.setWindowTitle(self.tr("Fetch Waypoints From Server"))
            btn_size_policy = self.overwriteBtn.sizePolicy()
            btn_size_policy.setRetainSizeWhenHidden(True)
            self.overwriteBtn.setSizePolicy(btn_size_policy)
            self.overwriteBtn.setVisible(False)
            self.saveBtn.setText(self.tr("Save Waypoints To Local File"))

    def handle_selection(self, selected, deselected, wp_model, wp_dict):
        len_selected = len(selected.indexes())
        len_deselected = len(deselected.indexes())
        columns = self.localWaypointsTable.model().columnCount()

        for index in range(0, len_selected, columns):
            row = selected.indexes()[index].row()
            waypoint = wp_model.waypoint_data(row)
            wp_dict[row] = waypoint
            self.merge_waypoints_list.append(waypoint)

        for index in range(0, len_deselected, columns):
            row = deselected.indexes()[index].row()
            delete_waypoint = wp_dict[row]
            self.merge_waypoints_list.remove(delete_waypoint)
        if len(self.merge_waypoints_list) > 1:
            self.saveBtn.setDisabled(False)
        else:
            self.saveBtn.setDisabled(True)
        self.merge_waypoints_model = ft.WaypointsTableModel(waypoints=self.merge_waypoints_list)
        self.mergedWaypointsTable.setModel(self.merge_waypoints_model)

    def save_waypoints(self, waypoints_model):
        if waypoints_model.rowCount() == 0:
            return
        self.xml_content = waypoints_model.get_xml_content()
        self.accept()

    def get_values(self):
        return self.xml_content


class MscolabHelpDialog(QDialog, msc_help_dialog.Ui_mscolabHelpDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.okayBtn.clicked.connect(lambda: self.close())
