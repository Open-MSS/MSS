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
import sys
import json
import hashlib
import logging
import types
import fs
import requests
import re
import urllib.request
import keyring

from fs import open_fs
from PIL import Image
from werkzeug.urls import url_join

from mslib.msui import flighttrack as ft
from mslib.msui import mscolab_chat as mc
from mslib.msui import mscolab_admin_window as maw
from mslib.msui import mscolab_version_history as mvh
from mslib.msui import socket_control as sc

from PyQt5 import QtCore, QtGui, QtWidgets
from mslib.utils.verify_user_token import verify_user_token
from mslib.utils.qt import get_open_filename, get_save_filename, dropEvent, dragEnterEvent, show_popup
from mslib.utils.qt import ui_mscolab_help_dialog as msc_help_dialog
from mslib.utils.qt import ui_add_operation_dialog as add_operation_ui
from mslib.utils.qt import ui_mscolab_merge_waypoints_dialog as merge_wp_ui
from mslib.utils.qt import ui_mscolab_connect_dialog as ui_conn
from mslib.utils.qt import ui_mscolab_profile_dialog as ui_profile
from mslib.msui import constants
from mslib.utils.config import config_loader, load_settings_qsettings, save_settings_qsettings, modify_config_file


def del_password_from_keyring(username):
    try:
        keyring.delete_password(service_name=__name__, username=username)
    except keyring.errors.PasswordDeleteError:
        pass
    except keyring.errors.NoKeyringError as e:
        logging.error(e)


def get_password_from_keyring(username=None):
    """
    When we request a username we use this function to fill in a form field with a password
    In this case by none existing credentials in the keyring we have to return an empty string
    """
    cred = keyring.get_credential(service_name=__name__, username=username)
    if username is not None and cred is None:
        return ""
    elif cred is None:
        return None
    else:
        return cred.password


def save_password_to_keyring(username="", password=""):
    if "" not in (username.strip(), password.strip()):
        keyring.set_password(service_name=__name__, username=username, password=password)


class MSColab_ConnectDialog(QtWidgets.QDialog, ui_conn.Ui_MSColabConnectDialog):
    """MSColab connect window class. Provides user interface elements to connect/disconnect,
       login, add new user to an MSColab Server. Also implements HTTP Server Authentication prompt.
    """

    def __init__(self, parent=None, mscolab=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        """
        super(MSColab_ConnectDialog, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.mscolab = mscolab

        # initialize server url as none
        self.mscolab_server_url = None

        self.setFixedSize(self.size())
        self.stackedWidget.setCurrentWidget(self.loginPage)

        # disable widgets in login frame
        self.loginEmailLe.setEnabled(False)
        self.loginPasswordLe.setEnabled(False)
        self.loginBtn.setEnabled(False)
        self.addUserBtn.setEnabled(False)

        # add urls from settings to the combobox
        self.add_mscolab_urls()

        # connect login, adduser, connect buttons
        self.connectBtn.clicked.connect(self.connect_handler)
        self.loginBtn.clicked.connect(self.login_handler)
        self.addUserBtn.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.newuserPage))

        # enable login button only if email and password are entered
        self.loginEmailLe.textChanged[str].connect(self.enable_login_btn)
        self.loginPasswordLe.textChanged[str].connect(self.enable_login_btn)

        # connect new user dialogbutton
        self.newUserBb.accepted.connect(self.new_user_handler)
        self.newUserBb.rejected.connect(lambda: self.stackedWidget.setCurrentWidget(self.loginPage))

        # connecting slot to clear all input widgets while switching tabs
        self.stackedWidget.currentChanged.connect(self.page_switched)

        # fill value of mscolab url if found in QSettings storage
        self.settings = load_settings_qsettings('mscolab', default_settings={'auth': {}, 'server_settings': {}})

    def page_switched(self, index):
        # clear all text in all input
        self.loginEmailLe.setText("")
        self.loginPasswordLe.setText("")

        self.newUsernameLe.setText("")
        self.newEmailLe.setText("")
        self.newPasswordLe.setText("")
        self.newConfirmPasswordLe.setText("")

        self.httpUsernameLe.setText("")
        self.httpPasswordLe.setText("")

        if index == 2:
            self.connectBtn.setEnabled(False)
        else:
            self.connectBtn.setEnabled(True)

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
            r = requests.get(url_join(url, 'status'))
            if r.text == "Mscolab server":
                self.set_status("Success", "Successfully connected to MSColab Server")
                # disable url input
                self.urlCb.setEnabled(False)

                # enable/disable appropriate widgets in login frame
                self.loginBtn.setEnabled(False)
                self.addUserBtn.setEnabled(True)
                self.loginEmailLe.setEnabled(True)
                self.loginPasswordLe.setEnabled(True)

                self.mscolab_server_url = url
                # delete mscolab http_auth settings for the url
                if self.mscolab_server_url in self.settings["auth"].keys():
                    del self.settings["auth"][self.mscolab_server_url]

                if self.mscolab_server_url not in self.settings["server_settings"].keys():
                    self.settings["server_settings"].update({self.mscolab_server_url: {}})
                save_settings_qsettings('mscolab', self.settings)

                # Fill Email and Password fields from config
                self.loginEmailLe.setText(config_loader(dataset="MSCOLAB_mailid"))
                self.loginPasswordLe.setText(get_password_from_keyring(
                    username=config_loader(dataset="MSCOLAB_mailid")))
                self.enable_login_btn()

                # Change connect button text and connect disconnect handler
                self.connectBtn.setText('Disconnect')
                self.connectBtn.clicked.disconnect(self.connect_handler)
                self.connectBtn.clicked.connect(self.disconnect_handler)
            else:
                self.set_status("Error", "Some unexpected error occurred. Please try again.")
        except requests.exceptions.SSLError:
            logging.debug("Certificate Verification Failed")
            self.set_status("Error", "Certificate Verification Failed")
        except requests.exceptions.InvalidSchema:
            logging.debug("invalid schema of url")
            self.set_status("Error", "Invalid Url Scheme!")
        except requests.exceptions.InvalidURL:
            logging.debug("invalid url")
            self.set_status("Error", "Invalid URL")
        except requests.exceptions.ConnectionError:
            logging.debug("MSColab server isn't active")
            self.set_status("Error", "MSColab server isn't active")
        except Exception as e:
            logging.debug("Error %s", str(e))
            self.set_status("Error", "Some unexpected error occurred. Please try again.")

    def disconnect_handler(self):
        self.urlCb.setEnabled(True)

        # enable/disable appropriate widgets in login frame
        self.loginBtn.setEnabled(False)
        self.addUserBtn.setEnabled(False)
        self.loginEmailLe.setEnabled(False)
        self.loginPasswordLe.setEnabled(False)

        # clear text
        self.stackedWidget.setCurrentWidget(self.loginPage)

        # delete mscolab http_auth settings for the url
        if self.mscolab_server_url in self.settings["auth"].keys():
            del self.settings["auth"][self.mscolab_server_url]
        save_settings_qsettings('mscolab', self.settings)
        self.mscolab_server_url = None

        self.connectBtn.setText('Connect')
        self.connectBtn.clicked.disconnect(self.disconnect_handler)
        self.connectBtn.clicked.connect(self.connect_handler)
        self.set_status("Info", 'Disconnected from server')

    def authenticate(self, data, r, url):
        if r.status_code == 401:
            username, password = self.httpUsernameLe.text(), self.httpPasswordLe.text()
            self.settings["auth"][self.mscolab_server_url] = (username, password)
            save_settings_qsettings('mscolab', self.settings)
            s = requests.Session()
            s.auth = (username, password)
            s.headers.update({'x-test': 'true'})
            r = s.post(url, data=data, timeout=(2, 10))
        return r

    def login_handler(self):
        # get mscolab /token http auth credentials from cache
        for key, value in config_loader(dataset="MSC_login").items():
            if key not in constants.MSC_LOGIN_CACHE or constants.MSC_LOGIN_CACHE[key] != value:
                constants.MSC_LOGIN_CACHE[key] = value
        auth = constants.MSC_LOGIN_CACHE.get(self.mscolab_server_url, (None, None))

        emailid = self.loginEmailLe.text()
        password = self.loginPasswordLe.text()
        data = {
            "email": emailid,
            "password": password
        }
        s = requests.Session()
        s.auth = (auth[0], auth[1])
        s.headers.update({'x-test': 'true'})
        url = f'{self.mscolab_server_url}/token'
        url_recover_password = f'{self.mscolab_server_url}/reset_request'
        try:
            r = s.post(url, data=data, timeout=(2, 10))
        except requests.exceptions.ConnectionError as ex:
            logging.error("unexpected error: %s %s %s", type(ex), url, ex)
            self.set_status(
                "Error",
                "Failed to establish a new connection" f' to "{self.mscolab_server_url}". Try in a moment again.',
            )
            self.disconnect_handler()
            return

        if r.text == "False":
            # show status indicating about wrong credentials
            self.set_status("Error", 'Oh no, you need to add a user account or '
                            f'<a href="{url_recover_password}">Recover Your Password</a>')
        elif r.text == "Unauthorized Access":
            # Server auth required for logging in
            self.login_data = [data, r, url]
            self.connectBtn.setEnabled(False)
            self.stackedWidget.setCurrentWidget(self.httpAuthPage)
            # ToDo disconnect functions already connected to httpBb buttonBox
            self.httpBb.accepted.connect(self.login_server_auth)
            self.httpBb.rejected.connect(lambda: self.stackedWidget.setCurrentWidget(self.loginPage))
        else:
            self.mscolab.after_login(emailid, self.mscolab_server_url, r)

    def save_user_credentials_to_config_file(self, emailid, password):
        data_to_save_in_config_file = {
            "MSCOLAB_mailid": emailid
        }
        save_password_to_keyring(username=emailid, password=password)

        if config_loader(dataset="MSCOLAB_mailid") != "" and get_password_from_keyring(username=emailid) != "":
            ret = QtWidgets.QMessageBox.question(
                self, self.tr("Update Credentials"),
                self.tr("You are using new credentials. "
                        "Should your settings file be updated with the new credentials?"),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if ret == QtWidgets.QMessageBox.Yes:
                modify_config_file(data_to_save_in_config_file)
        else:
            modify_config_file(data_to_save_in_config_file)

    def login_server_auth(self):
        data, r, url = self.login_data
        emailid = data['email']
        if r.status_code == 401:
            r = self.authenticate(data, r, url)
            if r.status_code == 200 and r.text not in ["False", "Unauthorized Access"]:
                self.save_auth_credentials_to_config_file()
                self.mscolab.after_login(emailid, self.mscolab_server_url, r)
            else:
                self.set_status("Error", 'Oh no, server authentication were incorrect.')
                self.stackedWidget.setCurrentWidget(self.loginPage)

    def new_user_handler(self):
        # get mscolab /token http auth credentials from cache
        for key, value in config_loader(dataset="MSC_login").items():
            if key not in constants.MSC_LOGIN_CACHE or constants.MSC_LOGIN_CACHE[key] != value:
                constants.MSC_LOGIN_CACHE[key] = value
        auth = constants.MSC_LOGIN_CACHE.get(self.mscolab_server_url, (None, None))

        emailid = self.newEmailLe.text()
        password = self.newPasswordLe.text()
        re_password = self.newConfirmPasswordLe.text()
        username = self.newUsernameLe.text()
        if password != re_password:
            self.set_status("Error", 'Oh no, your passwords don\'t match')
            return

        data = {
            "email": emailid,
            "password": password,
            "username": username
        }
        s = requests.Session()
        s.auth = (auth[0], auth[1])
        s.headers.update({'x-test': 'true'})
        url = f'{self.mscolab_server_url}/register'
        try:
            r = s.post(url, data=data, timeout=(2, 10))
        except requests.exceptions.ConnectionError as ex:
            logging.error("unexpected error: %s %s %s", type(ex), url, ex)
            self.set_status(
                "Error",
                "Failed to establish a new connection" f' to "{self.mscolab_server_url}". Try in a moment again.',
            )
            self.disconnect_handler()
            return

        if r.status_code == 204:
            self.set_status("Success", 'You are registered, confirm your email to log in.')
            self.save_user_credentials_to_config_file(emailid, password)
            self.stackedWidget.setCurrentWidget(self.loginPage)
            self.loginEmailLe.setText(emailid)
            self.loginPasswordLe.setText(password)
        elif r.status_code == 201:
            self.set_status("Success", 'You are registered.')
            self.save_user_credentials_to_config_file(emailid, password)
            self.loginEmailLe.setText(emailid)
            self.loginPasswordLe.setText(password)
            self.login_handler()
        elif r.status_code == 401:
            self.newuser_data = [data, r, url]
            self.stackedWidget.setCurrentWidget(self.httpAuthPage)
            # ToDo disconnect functions already connected to httpBb buttonBox
            self.httpBb.accepted.connect(self.newuser_server_auth)
            self.httpBb.rejected.connect(lambda: self.stackedWidget.setCurrentWidget(self.newuserPage))
        else:
            try:
                error_msg = json.loads(r.text)["message"]
            except Exception as e:
                logging.debug("Unexpected error occured %s", e)
                error_msg = "Unexpected error occured. Please try again."
            self.set_status("Error", error_msg)

    def save_auth_credentials_to_config_file(self):
        msc_login_data = config_loader(dataset="MSC_login")
        msc_login_data[self.mscolab_server_url] = (
            self.settings["auth"][self.mscolab_server_url][0],
            self.settings["auth"][self.mscolab_server_url][1]
        )
        data_to_save_in_config_file = {
            "MSC_login": msc_login_data
        }
        modify_config_file(data_to_save_in_config_file)

    def newuser_server_auth(self):
        data, r, url = self.newuser_data
        r = self.authenticate(data, r, url)
        if r.status_code == 201:
            self.save_auth_credentials_to_config_file()
            self.set_status("Success", "You are registered.")
            self.save_user_credentials_to_config_file(data['email'], data['password'])
            self.loginEmailLe.setText(data['email'])
            self.loginPasswordLe.setText(data['password'])
            self.login_handler()
        elif r.status_code == 200:
            try:
                error_msg = json.loads(r.text)["message"]
            except Exception as e:
                logging.debug("Unexpected error occured %s", e)
                error_msg = "Unexpected error occured. Please try again."
            self.set_status("Error", error_msg)
        elif r.status_code == 204:
            self.save_auth_credentials_to_config_file()
            self.set_status("Success", 'You are registered, confirm your email to log in.')
            self.save_user_credentials_to_config_file(data['email'], data['password'])
            self.stackedWidget.setCurrentWidget(self.loginPage)
            self.loginEmailLe.setText(data['email'])
            self.loginPasswordLe.setText(data['password'])
        else:
            self.set_status("Error", "Oh no, server authentication were incorrect.")
            self.stackedWidget.setCurrentWidget(self.newuserPage)


class MSUIMscolab(QtCore.QObject):
    """
    Class for implementing MSColab functionalities
    """
    name = "Mscolab"

    signal_activate_operation = QtCore.Signal(int, name="signal_activate_operation")
    signal_operation_added = QtCore.Signal(int, str, name="signal_operation_added")
    signal_operation_removed = QtCore.Signal(int, name="signal_operation_removed")
    signal_login_mscolab = QtCore.Signal(str, str, name="signal_login_mscolab")
    signal_logout_mscolab = QtCore.Signal(name="signal_logout_mscolab")
    signal_listFlighttrack_doubleClicked = QtCore.Signal()
    signal_permission_revoked = QtCore.Signal(int)
    signal_render_new_permission = QtCore.Signal(int, str)

    def __init__(self, parent=None, data_dir=None):
        super(MSUIMscolab, self).__init__(parent)
        self.ui = parent

        # connect mscolab help action from help menu
        self.ui.actionMSColabHelp.triggered.connect(self.open_help_dialog)

        # hide mscolab related widgets
        self.ui.usernameLabel.hide()
        self.ui.userOptionsTb.hide()
        self.ui.actionAddOperation.setEnabled(False)
        self.hide_operation_options()
        self.ui.activeOperationDesc.setHidden(True)

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
        self.ui.actionUpdateOperationDesc.triggered.connect(self.update_description_handler)
        self.ui.actionRenameOperation.triggered.connect(self.rename_operation_handler)
        self.ui.actionActivateOperation.triggered.connect(self.activate_operation)
        self.ui.actionDescription.triggered.connect(
            lambda: QtWidgets.QMessageBox.information(None,
                                                      "Operation Description",
                                                      f"{self.active_operation_desc}"))

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
        # int to store active pid
        self.active_op_id = None
        # int to store selected inactive op_id
        self.inactive_op_id = None
        # storing access_level to save network call
        self.access_level = None
        # storing operation_name to save network call
        self.active_operation_name = None
        # Storing operation list to pass to admin window
        self.operations = None
        # store active_flight_path here as object
        self.waypoints_model = None
        # Store active operation's file path
        self.local_ftml_file = None
        # Store active_operation_description
        self.active_operation_desc = None
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
        self.selected_category = "ANY"
        # Gravatar image path
        self.gravatar = None

        # set data dir, uri
        if data_dir is None:
            self.data_dir = config_loader(dataset="mss_dir")
        else:
            self.data_dir = data_dir
        self.create_dir()

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

    def after_login(self, emailid, url, r):
        # emailid by direct call
        self.email = emailid
        self.connect_window.close()
        self.connect_window = None
        QtWidgets.QApplication.processEvents()
        # fill value of mscolab url if found in QSettings storage
        self.settings = load_settings_qsettings('mscolab', default_settings={'auth': {}, 'server_settings': {}})

        _json = json.loads(r.text)
        self.token = _json["token"]
        self.user = _json["user"]
        self.mscolab_server_url = url

        # create socket connection here
        try:
            self.conn = sc.ConnectionManager(self.token, user=self.user, mscolab_server_url=self.mscolab_server_url)
        except Exception as ex:
            logging.debug("Couldn't create a socket connection: %s", ex)
            show_popup(self.ui, "Error", "Couldn't create a socket connection. Maybe the mscolab server is too old."
                                         "New Login required!")
            self.logout()
        else:
            # Update Last Used
            data = {
                "token": self.token
            }
            r = requests.post(f"{self.mscolab_server_url}/update_last_used", data=data, timeout=(2, 10))
            self.conn.signal_operation_list_updated.connect(self.reload_operation_list)
            self.conn.signal_reload.connect(self.reload_window)
            self.conn.signal_new_permission.connect(self.render_new_permission)
            self.conn.signal_update_permission.connect(self.handle_update_permission)
            self.conn.signal_revoke_permission.connect(self.handle_revoke_permission)
            self.conn.signal_operation_deleted.connect(self.handle_operation_deleted)

            self.ui.connectBtn.hide()
            self.ui.openOperationsGb.show()
            # display connection status
            self.ui.mscStatusLabel.setText(self.ui.tr(f"Status: connected to '{self.mscolab_server_url}'"))
            # display username beside useroptions toolbutton
            self.ui.usernameLabel.setText(f"{self.user['username']}")
            self.ui.usernameLabel.show()
            self.ui.userOptionsTb.show()
            self.fetch_gravatar()
            # enable add operation menu action
            self.ui.actionAddOperation.setEnabled(True)

            # Populate open operations list
            self.add_operations_to_ui()

            # Show category list
            self.show_categories_to_ui()

            # show operation_description
            self.ui.activeOperationDesc.setHidden(False)
            # disable update operation description button
            self.ui.actionUpdateOperationDesc.setEnabled(False)
            # disable delete operation button
            self.ui.actionDeleteOperation.setEnabled(False)
            # disable category change selector
            self.ui.filterCategoryCb.setEnabled(True)
            # disable activate operation button
            self.ui.actionActivateOperation.setEnabled(False)

            self.signal_login_mscolab.emit(self.mscolab_server_url, self.token)

    def fetch_gravatar(self, refresh=False):
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

        self.prof_diag = QtWidgets.QDialog()
        self.profile_dialog = ui_profile.Ui_ProfileWindow()
        self.profile_dialog.setupUi(self.prof_diag)
        self.profile_dialog.buttonBox.accepted.connect(lambda: self.prof_diag.close())
        self.profile_dialog.usernameLabel_2.setText(self.user['username'])
        self.profile_dialog.mscolabURLLabel_2.setText(self.mscolab_server_url)
        self.profile_dialog.emailLabel_2.setText(self.email)
        self.profile_dialog.deleteAccountBtn.clicked.connect(self.delete_account)

        # add context menu for right click on image
        self.gravatar_menu = QtWidgets.QMenu()
        self.gravatar_menu.addAction('Fetch Gravatar', lambda: self.fetch_gravatar(refresh=True))
        self.gravatar_menu.addAction('Remove Gravatar', lambda: self.remove_gravatar())
        self.profile_dialog.gravatarLabel.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.profile_dialog.gravatarLabel.customContextMenuRequested.connect(on_context_menu)

        self.prof_diag.show()
        self.fetch_gravatar()

    def delete_account(self):
        if verify_user_token(self.mscolab_server_url, self.token):
            w = QtWidgets.QWidget()
            qm = QtWidgets.QMessageBox
            reply = qm.question(w, self.tr('Continue?'),
                                self.tr("You're about to delete your account. You cannot undo this operation!"),
                                qm.Yes, qm.No)
            if reply == QtWidgets.QMessageBox.No:
                return
            data = {
                "token": self.token
            }

            res = requests.post(self.mscolab_server_url + '/delete_user', data=data, timeout=(2, 10))
            if res.status_code == 200 and json.loads(res.text)["success"] is True:
                self.logout()
        else:
            show_popup(self, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def add_operation_handler(self):
        if verify_user_token(self.mscolab_server_url, self.token):
            def check_and_enable_operation_accept():
                if (self.add_proj_dialog.path.text() != "" and
                        self.add_proj_dialog.description.toPlainText() != "" and
                        self.add_proj_dialog.category.text() != ""):
                    self.add_proj_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
                else:
                    self.add_proj_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

            def browse():
                type = self.add_proj_dialog.cb_ImportType.currentText()
                file_type = ["Flight track (*.ftml)"]
                if type != 'FTML':
                    file_type = [f"Flight track (*.{self.ui.import_plugins[type][1]})"]

                file_path = get_open_filename(
                    self.ui, "Open Flighttrack file", "", ';;'.join(file_type))
                if file_path is not None:
                    file_name = fs.path.basename(file_path)
                    if file_path.endswith('ftml'):
                        with open_fs(fs.path.dirname(file_path)) as file_dir:
                            file_content = file_dir.readtext(file_name)
                    else:
                        function = self.ui.import_plugins[type][0]
                        ft_name, waypoints = function(file_path)
                        model = ft.WaypointsTableModel(waypoints=waypoints)
                        xml_doc = model.get_xml_doc()
                        file_content = xml_doc.toprettyxml(indent="  ", newl="\n")
                    self.add_proj_dialog.f_content = file_content
                    self.add_proj_dialog.selectedFile.setText(file_name)

            self.proj_diag = QtWidgets.QDialog()
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
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def add_operation(self):
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

        data = {
            "token": self.token,
            "path": path,
            "description": description,
            "category": category
        }
        if self.add_proj_dialog.f_content is not None:
            data["content"] = self.add_proj_dialog.f_content
        r = requests.post(f'{self.mscolab_server_url}/create_operation', data=data, timeout=(2, 10))
        if r.text == "True":
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Your operation was created successfully')
            op_id = self.get_recent_op_id()
            self.conn.handle_new_operation(op_id)
            self.signal_operation_added.emit(op_id, path)
        else:
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('The path already exists')

    def get_recent_op_id(self):
        if verify_user_token(self.mscolab_server_url, self.token):
            """
            get most recent operation's op_id
            """
            data = {
                "token": self.token
            }
            r = requests.get(self.mscolab_server_url + '/operations', data=data)
            if r.text != "False":
                _json = json.loads(r.text)
                operations = _json["operations"]
                op_id = None
                if operations:
                    op_id = operations[-1]["op_id"]
                return op_id
            else:
                show_popup(self.ui, "Error", "Session expired, new login required")
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

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

    def open_chat_window(self):
        if verify_user_token(self.mscolab_server_url, self.token):
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
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def close_chat_window(self):
        self.chat_window.close()
        self.chat_window = None

    def open_admin_window(self):
        if verify_user_token(self.mscolab_server_url, self.token):
            if self.active_op_id is None:
                return

            if self.admin_window is not None:
                self.admin_window.activateWindow()
                return

            self.admin_window = maw.MSColabAdminWindow(
                self.token,
                self.active_op_id,
                self.user,
                self.active_operation_name,
                self.operations,
                self.conn,
                mscolab_server_url=self.mscolab_server_url,
            )
            self.admin_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.admin_window.viewCloses.connect(self.close_admin_window)
            self.admin_window.show()
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def close_admin_window(self):
        self.admin_window.close()
        self.admin_window = None

    def open_version_history_window(self):
        if verify_user_token(self.mscolab_server_url, self.token):
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
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

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

    def handle_delete_operation(self):
        if verify_user_token(self.mscolab_server_url, self.token):
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
                    data = {
                        "token": self.token,
                        "op_id": self.active_op_id
                    }
                    url = url_join(self.mscolab_server_url, 'delete_operation')
                    try:
                        res = requests.post(url, data=data, timeout=(2, 10))
                    except requests.exceptions.RequestException as e:
                        logging.debug(e)
                        show_popup(self.ui, "Error", "Some error occurred! Could not delete operation.")
                    else:
                        res.raise_for_status()
                        self.reload_operations()
                        self.signal_operation_removed.emit(self.active_op_id)
                else:
                    show_popup(self.ui, "Error", "Entered operation name did not match!")
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def handle_leave_operation(self):
        w = QtWidgets.QWidget()
        qm = QtWidgets.QMessageBox
        reply = qm.question(w, self.tr('Mission Support System'),
                            self.tr("Do you want to leave this operation?"),
                            qm.Yes, qm.No)
        if reply == QtWidgets.QMessageBox.Yes:
            if verify_user_token(self.mscolab_server_url, self.token):
                data = {
                    "token": self.token,
                    "op_id": self.active_op_id,
                    "selected_userids": json.dumps([self.user["id"]])
                }
                url = url_join(self.mscolab_server_url, "delete_bulk_permissions")
                res = requests.post(url, data=data, timeout=(2, 10))
                if res.text != "False":
                    res = res.json()
                    if res["success"]:
                        for window in self.ui.get_active_views():
                            window.handle_force_close()
                        self.reload_operations()
                    else:
                        show_popup(self.ui, "Error", "Some error occurred! Could not leave operation.")
                else:
                    show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
                    self.logout()
            else:
                show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
                self.logout()

    def set_operation_desc_label(self, op_desc):
        self.active_operation_desc = op_desc
        desc_count = len(str(self.active_operation_desc))
        if desc_count < 95:
            self.ui.activeOperationDesc.setText(
                self.ui.tr(f"{self.active_operation_name}: {self.active_operation_desc}"))
        else:
            self.ui.activeOperationDesc.setText(
                "Description is too long to show here, for long descriptions go "
                "to operations menu.")

    def update_description_handler(self):
        # only after login
        if verify_user_token(self.mscolab_server_url, self.token):
            entered_operation_desc, ok = QtWidgets.QInputDialog.getText(
                self.ui,
                self.ui.tr(f"{self.active_operation_name} - Update Description"),
                self.ui.tr(
                    "You're about to update the operation description"
                    "\nEnter new operation description: "
                ),
                text=self.active_operation_desc
            )
            if ok:
                data = {
                    "token": self.token,
                    "op_id": self.active_op_id,
                    "attribute": 'description',
                    "value": entered_operation_desc
                }
                url = url_join(self.mscolab_server_url, 'update_operation')
                r = requests.post(url, data=data, timeout=(2, 10))
                if r.text == "True":
                    # Update active operation description label
                    self.set_operation_desc_label(entered_operation_desc)

                    self.reload_operation_list()
                    self.error_dialog = QtWidgets.QErrorMessage()
                    self.error_dialog.showMessage("Description is updated successfully.")
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def rename_operation_handler(self):
        # only after login
        if verify_user_token(self.mscolab_server_url, self.token):
            entered_operation_name, ok = QtWidgets.QInputDialog.getText(
                self.ui,
                self.ui.tr("Rename Operation"),
                self.ui.tr(
                    f"You're about to rename the operation - '{self.active_operation_name}' "
                    f"Enter new operation name: "
                ),
            )
            if ok:
                data = {
                    "token": self.token,
                    "op_id": self.active_op_id,
                    "attribute": 'path',
                    "value": entered_operation_name
                }
                url = url_join(self.mscolab_server_url, 'update_operation')
                r = requests.post(url, data=data, timeout=(2, 10))
                if r.text == "True":
                    # Update active operation name
                    self.active_operation_name = entered_operation_name

                    # Update active operation description
                    self.set_operation_desc_label(self.active_operation_desc)
                    self.reload_operation_list()
                    self.reload_windows_slot()
                    # Update other user's operation list
                    self.conn.signal_operation_list_updated.connect(self.reload_operation_list)

                    self.error_dialog = QtWidgets.QErrorMessage()
                    self.error_dialog.showMessage("Operation is renamed successfully.")
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def handle_work_locally_toggle(self):
        if verify_user_token(self.mscolab_server_url, self.token):
            if self.ui.workLocallyCheckbox.isChecked():
                if self.version_window is not None:
                    self.version_window.close()
                self.create_local_operation_file()
                self.local_ftml_file = fs.path.combine(
                    self.data_dir,
                    fs.path.join(
                        "local_mscolab_data", self.user["username"],
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
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def create_local_operation_file(self):
        with open_fs(self.data_dir) as mss_dir:
            rel_file_path = fs.path.join('local_mscolab_data', self.user['username'],
                                         self.active_operation_name, 'mscolab_operation.ftml')
            if mss_dir.exists(rel_file_path) is True:
                return
            mss_dir.makedirs(fs.path.dirname(rel_file_path))
            server_data = self.waypoints_model.get_xml_content()
            mss_dir.writetext(rel_file_path, server_data)

    def reload_local_wp(self):
        self.waypoints_model = ft.WaypointsTableModel(filename=self.local_ftml_file, data_dir=self.data_dir)
        self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)
        self.reload_view_windows()

    def operation_category_handler(self):
        # only after_login
        if self.mscolab_server_url is not None:
            self.selected_category = self.ui.filterCategoryCb.currentText()
            if self.selected_category != "ANY":
                self.add_operations_to_ui()
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

    def fetch_wp_mscolab(self):
        if verify_user_token(self.mscolab_server_url, self.token):
            server_xml = self.request_wps_from_server()
            server_waypoints_model = ft.WaypointsTableModel(xml_content=server_xml)
            self.merge_dialog = MscolabMergeWaypointsDialog(self.waypoints_model, server_waypoints_model, True, self.ui)
            self.merge_dialog.saveBtn.setDisabled(True)
            if self.merge_dialog.exec_():
                xml_content = self.merge_dialog.get_values()
                if xml_content is not None:
                    self.waypoints_model = ft.WaypointsTableModel(xml_content=xml_content)
                    self.waypoints_model.save_to_ftml(self.local_ftml_file)
                    self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)
                    self.reload_view_windows()
                    show_popup(self.ui, "Success", "New Waypoints Fetched To Local File!", icon=1)
            self.merge_dialog.close()
            self.merge_dialog = None
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def save_wp_mscolab(self, comment=None):
        if verify_user_token(self.mscolab_server_url, self.token):
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
                    self.waypoints_model.save_to_ftml(self.local_ftml_file)
                    self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)
                    self.reload_view_windows()
                    show_popup(self.ui, "Success", "New Waypoints Saved To Server!", icon=1)
            self.merge_dialog.close()
            self.merge_dialog = None
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def get_recent_operation(self):
        """
        get most recent operation
        """
        if verify_user_token(self.mscolab_server_url, self.token):
            data = {
                "token": self.token
            }
            r = requests.get(self.mscolab_server_url + '/operations', data=data, timeout=(2, 10))
            if r.text != "False":
                _json = json.loads(r.text)
                operations = _json["operations"]
                recent_operation = None
                if operations:
                    recent_operation = operations[-1]
                return recent_operation
            else:
                show_popup(self.ui, "Error", "Session expired, new login required")
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    @QtCore.Slot()
    def reload_operation_list(self):
        if self.mscolab_server_url is not None:
            self.reload_operations()

    @QtCore.Slot(int)
    def reload_window(self, value):
        if self.active_op_id != value or self.ui.workLocallyCheckbox.isChecked():
            return
        self.reload_wps_from_server()

    @QtCore.Slot()
    def reload_windows_slot(self):
        self.reload_window(self.active_op_id)

    @QtCore.Slot(int, int)
    def render_new_permission(self, op_id, u_id):
        """
        op_id: operation id
        u_id: user id

        to render new permission if added
        """
        data = {
            'token': self.token
        }
        r = requests.get(self.mscolab_server_url + '/user', data=data, timeout=(2, 10))
        if r.text != "False":
            _json = json.loads(r.text)
            if _json['user']['id'] == u_id:
                operation = self.get_recent_operation()
                operation_desc = f'{operation["path"]} - {operation["access_level"]}'
                widgetItem = QtWidgets.QListWidgetItem(operation_desc, parent=self.ui.listOperationsMSC)
                widgetItem.op_id = operation["op_id"]
                widgetItem.catgegory = operation["category"]
                widgetItem.operation_path = operation["path"]
                widgetItem.access_level = operation["access_level"]
                widgetItem.active_operation_desc = operation["description"]
                self.ui.listOperationsMSC.addItem(widgetItem)
                self.signal_render_new_permission.emit(operation["op_id"], operation["path"])
            if self.chat_window is not None:
                self.chat_window.load_users()
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    @QtCore.Slot(int, int, str)
    def handle_update_permission(self, op_id, u_id, access_level):
        """
        op_id: operation id
        u_id: user id
        access_level: updated access level

        function updates existing permissions and related control availability
        """
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

    @QtCore.Slot(int, int)
    def handle_revoke_permission(self, op_id, u_id):
        if u_id == self.user["id"]:
            operation_name = self.delete_operation_from_list(op_id)
            if operation_name is not None:
                show_popup(self.ui, "Permission Revoked",
                           f'Your access to operation - "{operation_name}" was revoked!', icon=1)
                # on import permissions revoked name can not taken from the operation list,
                # because we update the list first by reloading it.
                show_popup(self.ui, "Permission Revoked", "Access to an operation was revoked")
                self.signal_permission_revoked.emit(op_id)

    @QtCore.Slot(int)
    def handle_operation_deleted(self, op_id):
        operation_name = self.delete_operation_from_list(op_id)
        show_popup(self.ui, "Success", f'Operation "{operation_name}" was deleted!', icon=1)

    def show_categories_to_ui(self):
        """
        adds the list of operation categories to the UI
        """
        if verify_user_token(self.mscolab_server_url, self.token):
            data = {
                "token": self.token
            }
            r = requests.get(f'{self.mscolab_server_url}/operations', data=data, timeout=(2, 10))
            if r.text != "False":
                _json = json.loads(r.text)
                operations = _json["operations"]
                self.ui.filterCategoryCb.clear()
                categories = set(["ANY"])
                for operation in operations:
                    categories.add(operation["category"])
                categories.remove("ANY")
                categories = ["ANY"] + sorted(categories)
                category = config_loader(dataset="MSCOLAB_category")
                self.ui.filterCategoryCb.addItems(categories)
                if category in categories:
                    index = categories.index(category)
                    self.ui.filterCategoryCb.setCurrentIndex(index)

    def add_operations_to_ui(self):
        if verify_user_token(self.mscolab_server_url, self.token):
            data = {
                "token": self.token
            }
            r = requests.get(f'{self.mscolab_server_url}/operations', data=data, timeout=(2, 10))
            if r.text != "False":
                _json = json.loads(r.text)
                self.operations = _json["operations"]
                logging.debug("adding operations to ui")
                operations = sorted(self.operations, key=lambda k: k["path"].lower())
                self.ui.listOperationsMSC.clear()
                self.ui.listInactiveOperationsMSC.clear()
                selectedOperation = None
                for operation in operations:
                    operation_desc = f'{operation["path"]} - {operation["access_level"]}'
                    widgetItem = QtWidgets.QListWidgetItem(operation_desc)
                    widgetItem.active_operation_desc = operation["description"]
                    widgetItem.op_id = operation["op_id"]
                    widgetItem.access_level = operation["access_level"]
                    widgetItem.operation_path = operation["path"]
                    widgetItem.operation_category = operation["category"]
                    try:
                        # compatibility to 7.x
                        # a newer server can distinguish older operations and move those into inactive state
                        widgetItem.active = operation["active"]
                    except KeyError:
                        widgetItem.active = True
                    if widgetItem.op_id == self.active_op_id:
                        selectedOperation = widgetItem
                    if widgetItem.active:
                        self.ui.listOperationsMSC.addItem(widgetItem)
                    else:
                        self.ui.listInactiveOperationsMSC.addItem(widgetItem)
                if selectedOperation is not None:
                    self.ui.listOperationsMSC.setCurrentItem(selectedOperation)
                    self.ui.listOperationsMSC.itemActivated.emit(selectedOperation)
                self.ui.listOperationsMSC.itemActivated.connect(self.set_active_op_id)
                self.ui.listInactiveOperationsMSC.itemActivated.connect(self.select_inactive_operation)
            else:
                show_popup(self.ui, "Error", "Session expired, new login required")
                self.logout()
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def select_inactive_operation(self, item):
        self.inactive_op_id = item.op_id
        self.active_op_id = None
        font = QtGui.QFont()
        for i in range(self.ui.listInactiveOperationsMSC.count()):
            self.ui.listInactiveOperationsMSC.item(i).setFont(font)
        font.setBold(True)
        item.setFont(font)
        self.show_operation_options_in_inactivated_state(item.access_level)

    def show_operation_options_in_inactivated_state(self, access_level):
        self.ui.actionChat.setEnabled(False)
        self.ui.actionVersionHistory.setEnabled(False)
        self.ui.actionManageUsers.setEnabled(False)
        self.ui.menuProperties.setEnabled(False)
        self.ui.actionRenameOperation.setEnabled(False)
        self.ui.actionLeaveOperation.setEnabled(False)
        self.ui.actionDeleteOperation.setEnabled(False)
        self.ui.actionUpdateOperationDesc.setEnabled(False)
        self.ui.actionActivateOperation.setEnabled(False)
        if access_level == "creator":
            self.ui.actionActivateOperation.setEnabled(True)

    def activate_operation(self):
        if verify_user_token(self.mscolab_server_url, self.token):
            # set last used date for operation
            data = {
                "token": self.token,
                "op_id": self.inactive_op_id,
            }
            res = requests.post(f'{self.mscolab_server_url}/set_last_used', data=data, timeout=(2, 10))
            if res.text != "False":
                res = res.json()
                if res["success"]:
                    self.reload_operations()
                else:
                    show_popup(self.ui, "Error", "Some error occurred! Could not activate operation")
            else:
                show_popup(self.ui, "Error", "Session expired, new login required")
                self.logout()
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def set_active_op_id(self, item):
        if verify_user_token(self.mscolab_server_url, self.token):
            if not self.ui.local_active:
                if item.op_id == self.active_op_id:
                    return

            # close all hanging window
            self.close_external_windows()
            self.hide_operation_options()

            # Turn off work locally toggle
            self.ui.workLocallyCheckbox.blockSignals(True)
            self.ui.workLocallyCheckbox.setChecked(False)
            self.ui.workLocallyCheckbox.blockSignals(False)

            # Disable Activate Operation Button
            self.ui.actionActivateOperation.setEnabled(False)

            # set last used date for operation
            data = {
                "token": self.token,
                "op_id": item.op_id,
            }
            requests.post(f'{self.mscolab_server_url}/set_last_used', data=data, timeout=(2, 10))

            # set active_op_id here
            self.active_op_id = item.op_id
            self.access_level = item.access_level
            self.active_operation_name = item.operation_path
            self.active_operation_desc = item.active_operation_desc
            self.waypoints_model = None

            self.signal_activate_operation.emit(self.active_op_id)

            self.inactive_op_id = None
            font = QtGui.QFont()
            for i in range(self.ui.listOperationsMSC.count()):
                self.ui.listOperationsMSC.item(i).setFont(font)
            font.setBold(False)

            # Set active operation description
            self.set_operation_desc_label(self.active_operation_desc)
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
            font = QtGui.QFont()
            for i in range(self.ui.listOperationsMSC.count()):
                self.ui.listOperationsMSC.item(i).setFont(font)
            font.setBold(True)
            item.setFont(font)

            # set new waypoints model to open views
            for window in self.ui.get_active_views():
                window.setFlightTrackModel(self.waypoints_model)
                if self.access_level == "viewer":
                    window.disable_navbar_action_buttons()
                else:
                    window.enable_navbar_action_buttons()

            self.ui.switch_to_mscolab()
        else:
            if self.mscolab_server_url is not None:
                show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
                self.logout()

    def switch_to_local(self):
        self.ui.local_active = True
        if self.active_op_id is not None:
            if verify_user_token(self.mscolab_server_url, self.token):
                # change font style for selected
                font = QtGui.QFont()

                for i in range(self.ui.listOperationsMSC.count()):
                    self.ui.listOperationsMSC.item(i).setFont(font)

                # close all hanging operation option windows
                self.close_external_windows()
                self.hide_operation_options()
                self.ui.menu_handler()
            else:
                show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
                self.logout()

    def show_operation_options(self):
        self.ui.actionChat.setEnabled(False)
        self.ui.actionVersionHistory.setEnabled(False)
        self.ui.actionManageUsers.setEnabled(False)
        self.ui.menuProperties.setEnabled(True)
        self.ui.actionRenameOperation.setEnabled(False)
        self.ui.actionLeaveOperation.setEnabled(True)
        self.ui.actionDeleteOperation.setEnabled(False)
        self.ui.actionUpdateOperationDesc.setEnabled(False)
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
            self.ui.actionUpdateOperationDesc.setEnabled(True)
            self.ui.filterCategoryCb.setEnabled(True)
        else:
            if self.admin_window is not None:
                self.admin_window.close()

        if self.access_level in ["creator"]:
            self.ui.actionDeleteOperation.setEnabled(True)
            self.ui.actionRenameOperation.setEnabled(True)
            self.ui.actionLeaveOperation.setEnabled(False)

        self.ui.menuImportFlightTrack.setEnabled(True)

    def hide_operation_options(self):
        self.ui.actionChat.setEnabled(False)
        self.ui.actionVersionHistory.setEnabled(False)
        self.ui.actionManageUsers.setEnabled(False)
        self.ui.menuProperties.setEnabled(False)
        self.ui.workLocallyCheckbox.setEnabled(False)
        self.ui.serverOptionsCb.hide()
        # change working status label
        self.ui.workingStatusLabel.setText(self.ui.tr("\n\nNo Operation Selected"))

    def request_wps_from_server(self):
        if verify_user_token(self.mscolab_server_url, self.token):
            data = {
                "token": self.token,
                "op_id": self.active_op_id
            }
            r = requests.get(self.mscolab_server_url + '/get_operation_by_id', data=data)
            if r.text != "False":
                xml_content = json.loads(r.text)["content"]
                return xml_content
            else:
                show_popup(self.ui, "Error", "Session expired, new login required")
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def load_wps_from_server(self):
        if self.ui.workLocallyCheckbox.isChecked():
            return
        xml_content = self.request_wps_from_server()
        if xml_content is not None:
            self.waypoints_model = ft.WaypointsTableModel(xml_content=xml_content)
            self.waypoints_model.name = self.active_operation_name
            self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)

    def reload_operations(self):
        self.add_operations_to_ui()
        selected_category = self.ui.filterCategoryCb.currentText()
        self.show_categories_to_ui()
        index = self.ui.filterCategoryCb.findText(selected_category, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.ui.filterCategoryCb.setCurrentIndex(index)

    def reload_wps_from_server(self):
        if self.active_op_id is None:
            return
        self.load_wps_from_server()
        self.reload_view_windows()

    def handle_waypoints_changed(self):
        if verify_user_token(self.mscolab_server_url, self.token):
            if self.ui.workLocallyCheckbox.isChecked():
                self.waypoints_model.save_to_ftml(self.local_ftml_file)
            else:
                xml_content = self.waypoints_model.get_xml_content()
                self.conn.save_file(self.token, self.active_op_id, xml_content, comment=None)
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def reload_view_windows(self):
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

    def handle_import_msc(self, file_path, extension, function, pickertype):
        if verify_user_token(self.mscolab_server_url, self.token):
            if self.active_op_id is None:
                return
            if file_path is None:
                return
            dir_path, file_name = fs.path.split(file_path)
            file_name = fs.path.basename(file_path)
            name, file_ext = fs.path.splitext(file_name)
            if function is None:
                with open_fs(dir_path) as file_dir:
                    xml_content = file_dir.readtext(file_name)
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
                self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)
            self.waypoints_model = model
            if self.ui.workLocallyCheckbox.isChecked():
                self.waypoints_model.save_to_ftml(self.local_ftml_file)
                self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)
            else:
                self.conn.save_file(self.token, self.active_op_id, xml_content, comment=None)
                self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)
            self.reload_view_windows()
            show_popup(self.ui, "Import Success", f"The file - {file_name}, was imported successfully!", 1)
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def handle_export_msc(self, extension, function, pickertype):
        if verify_user_token(self.mscolab_server_url, self.token):
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
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def listFlighttrack_itemDoubleClicked(self):
        self.ui.activeOperationDesc.setText("Select Operation to View Description.")
        self.signal_listFlighttrack_doubleClicked.emit()

    def logout(self):
        if self.mscolab_server_url is None:
            return
        self.ui.local_active = True
        self.ui.menu_handler()
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
        self.ui.listInactiveOperationsMSC.clear()
        # clear mscolab url
        self.mscolab_server_url = None
        # clear operations list here
        self.ui.mscStatusLabel.setText(self.ui.tr("status: disconnected"))
        self.ui.usernameLabel.hide()
        self.ui.userOptionsTb.hide()
        self.ui.connectBtn.show()
        self.ui.openOperationsGb.hide()
        self.ui.actionAddOperation.setEnabled(False)
        # hide operation description
        self.ui.activeOperationDesc.setHidden(True)
        # reset description label text
        self.ui.activeOperationDesc.setText(self.ui.tr("Select Operation to View Description."))
        # set usernameLabel back to default
        self.ui.usernameLabel.setText("User")
        # disconnect socket
        if self.conn is not None:
            self.conn.disconnect()
            self.conn = None
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

        # delete mscolab http_auth settings for the url
        if self.mscolab_server_url in self.settings["auth"].keys():
            del self.settings["auth"][self.mscolab_server_url]
        save_settings_qsettings('mscolab', self.settings)

        # disable category change selector
        self.ui.filterCategoryCb.setEnabled(False)
        self.signal_logout_mscolab.emit()

        # Don't try to activate local flighttrack while testing
        if "pytest" not in sys.modules:
            # activate first local flighttrack after logging out
            self.ui.listFlightTracks.setCurrentRow(0)
            self.ui.activate_selected_flight_track()


class MscolabMergeWaypointsDialog(QtWidgets.QDialog, merge_wp_ui.Ui_MergeWaypointsDialog):
    def __init__(self, local_waypoints_model, server_waypoints_model, fetch=False, parent=None):
        super(MscolabMergeWaypointsDialog, self).__init__(parent)
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


class MscolabHelpDialog(QtWidgets.QDialog, msc_help_dialog.Ui_mscolabHelpDialog):

    def __init__(self, parent=None):
        super(MscolabHelpDialog, self).__init__(parent)
        self.setupUi(self)
        self.okayBtn.clicked.connect(lambda: self.close())
