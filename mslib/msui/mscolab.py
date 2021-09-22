# -*- coding: utf-8 -*-
"""

    mslib.msui.mscolab
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Window to display authentication and operation details for mscolab


    To better understand of the code, look at the 'ships' example from
    chapter 14/16 of 'Rapid GUI Programming with Python and Qt: The
    Definitive Guide to PyQt Programming' (Mark Summerfield).

    This file is part of mss.

    :copyright: Copyright 2019- Shivashis Padhi
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
from fs import open_fs
from PIL import Image
from werkzeug.urls import url_join

from mslib.msui import flighttrack as ft
from mslib.msui import mscolab_operation as mp
from mslib.msui import mscolab_admin_window as maw
from mslib.msui import mscolab_version_history as mvh
from mslib.msui import socket_control as sc

from PyQt5 import QtCore, QtGui, QtWidgets
from mslib.msui.mss_qt import get_open_filename, get_save_filename, dropEvent, dragEnterEvent, show_popup
from mslib.msui.mss_qt import ui_mscolab_help_dialog as msc_help_dialog
from mslib.msui.mss_qt import ui_add_operation_dialog as add_operation_ui
from mslib.msui.mss_qt import ui_mscolab_merge_waypoints_dialog as merge_wp_ui
from mslib.msui.mss_qt import ui_mscolab_connect_dialog as ui_conn
from mslib.msui.mss_qt import ui_mscolab_profile_dialog as ui_profile
from mslib.msui import constants
from mslib.utils.config import config_loader, load_settings_qsettings, save_settings_qsettings


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
                self.loginPasswordLe.setText(config_loader(dataset="MSCOLAB_password"))
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
            r = s.post(url, data=data)
        return r

    def login_handler(self):
        for key, value in config_loader(dataset="MSC_login").items():
            if key not in constants.MSC_LOGIN_CACHE:
                constants.MSC_LOGIN_CACHE[key] = value
        auth = constants.MSC_LOGIN_CACHE.get(self.mscolab_server_url, (None, None))

        # get mscolab /token http auth credentials from cache
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
        try:
            r = s.post(url, data=data)
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
            self.set_status("Error", 'Oh no, your credentials were incorrect.')
        elif r.text == "Unauthorized Access":
            # Server auth required for logging in
            self.login_data = [data, r, url, auth]
            self.connectBtn.setEnabled(False)
            self.stackedWidget.setCurrentWidget(self.httpAuthPage)
            # ToDo disconnect functions already connected to httpBb buttonBox
            self.httpBb.accepted.connect(self.login_server_auth)
            self.httpBb.rejected.connect(lambda: self.stackedWidget.setCurrentWidget(self.loginPage))
        else:
            self.mscolab.after_login(emailid, self.mscolab_server_url, r)

    def login_server_auth(self):
        data, r, url, auth = self.login_data
        emailid = data['email']
        if r.status_code == 401:
            r = self.authenticate(data, r, url)
            if r.status_code == 200 and r.text not in ["False", "Unauthorized Access"]:
                constants.MSC_LOGIN_CACHE[self.mscolab_server_url] = (auth[0], auth[1])
                self.mscolab.after_login(emailid, self.mscolab_server_url, r)
            else:
                self.set_status("Error", 'Oh no, server authentication were incorrect.')
                self.stackedWidget.setCurrentWidget(self.loginPage)

    def new_user_handler(self):
        for key, value in config_loader(dataset="MSC_login").items():
            if key not in constants.MSC_LOGIN_CACHE:
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
            r = s.post(url, data=data)
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
            self.stackedWidget.setCurrentWidget(self.loginPage)
        elif r.status_code == 201:
            self.set_status("Success", 'You are registered')
            self.stackedWidget.setCurrentWidget(self.loginPage)
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
                logging.debug(f"Unexpected error occured {e}")
                error_msg = "Unexpected error occured. Please try again."
            self.set_status("Error", error_msg)

    def newuser_server_auth(self):
        data, r, url = self.newuser_data
        r = self.authenticate(data, r, url)
        if r.status_code == 201:
            constants.MSC_LOGIN_CACHE[self.mscolab_server_url] = (data['username'], data['password'])
            self.set_status("Success", "You are registered, you can now log in.")
            self.stackedWidget.setCurrentWidget(self.loginPage)
        else:
            self.set_status("Error", "Oh no, server authentication were incorrect.")
            self.stackedWidget.setCurrentWidget(self.newuserPage)


class MSSMscolab(QtCore.QObject):
    """
    Class for implementing MSColab functionalities
    """
    name = "Mscolab"

    def __init__(self, parent=None, data_dir=None):
        super(MSSMscolab, self).__init__(parent)
        self.ui = parent

        # connect mscolab help action from help menu
        self.ui.actionMSColabHelp.triggered.connect(self.open_help_dialog)

        # hide mscolab related widgets
        self.ui.usernameLabel.hide()
        self.ui.userOptionsTb.hide()
        self.ui.actionAddOperation.setEnabled(False)
        self.hide_operation_options()

        # connect operation options menu actions
        self.ui.actionAddOperation.triggered.connect(self.add_operation_handler)
        self.ui.actionChat.triggered.connect(self.operation_options_handler)
        self.ui.actionVersionHistory.triggered.connect(self.operation_options_handler)
        self.ui.actionManageUsers.triggered.connect(self.operation_options_handler)
        self.ui.actionDeleteOperation.triggered.connect(self.operation_options_handler)

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
        self.active_pid = None
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
        # connection object to interact with sockets
        self.conn = None
        # assign ids to view-window
        # self.view_id = 0
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
        self.selected_category = "ANY"

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
                logging.error(f'Make sure that the FS url "{self.data_dir}" exists')
                show_popup(self.ui, "Error", f'FS Url: "{self.data_dir}" does not exist!')
                sys.exit()
            except fs.opener.errors.UnsupportedProtocol:
                logging.error(f'FS url "{self.data_dir}" not supported')
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
            logging.debug(f"Couldn't create a socket connection: {ex}")
            show_popup(self.ui, "Error", "Couldn't create a socket connection. New Login required!")
            self.logout()
        self.conn.signal_reload.connect(self.reload_window)
        self.conn.signal_new_permission.connect(self.render_new_permission)
        self.conn.signal_update_permission.connect(self.handle_update_permission)
        self.conn.signal_revoke_permission.connect(self.handle_revoke_permission)
        self.conn.signal_operation_deleted.connect(self.handle_operation_deleted)

        self.ui.connectBtn.hide()
        # display connection status
        self.ui.mscStatusLabel.setText(self.ui.tr(f"Connected to MSColab Server at {self.mscolab_server_url}"))
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

    def verify_user_token(self):
        data = {
            "token": self.token
        }
        try:
            r = requests.get(f'{self.mscolab_server_url}/test_authorized', data=data)
        except requests.exceptions.SSLError:
            logging.debug("Certificate Verification Failed")
            return False
        except requests.exceptions.InvalidSchema:
            logging.debug("Invalid schema of url")
            return False
        except requests.exceptions.ConnectionError as ex:
            logging.error("unexpected error: %s %s", type(ex), ex)
            return False
        except requests.exceptions.MissingSchema as ex:
            # self.mscolab_server_url can be None??
            logging.error("unexpected error: %s %s", type(ex), ex)
            return False
        return r.text == "True"

    def fetch_gravatar(self, refresh=False):
        email_hash = hashlib.md5(bytes(self.email.encode('utf-8')).lower()).hexdigest()
        email_in_settings = self.email in config_loader(dataset="gravatar_ids")
        gravatar_path = os.path.join(constants.MSS_CONFIG_PATH, 'gravatars')
        gravatar = os.path.join(gravatar_path, f"{email_hash}.png")

        if refresh or email_in_settings:
            if not os.path.exists(gravatar_path):
                try:
                    os.makedirs(gravatar_path)
                except Exception as e:
                    logging.debug("Error %s", str(e))
                    show_popup(self.prof_diag, "Error", "Could not create gravatar folder in config folder")
                    return

            if not refresh and email_in_settings and os.path.exists(gravatar):
                self.set_gravatar(gravatar)

            gravatar = os.path.join(gravatar_path, f"{email_hash}.jpg")
            gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}?s=80&d=404"
            try:
                urllib.request.urlretrieve(gravatar_url, gravatar)
                img = Image.open(gravatar)
                img.save(gravatar.replace(".jpg", ".png"))
                os.remove(gravatar)
                gravatar = gravatar.replace(".jpg", ".png")
            except urllib.error.HTTPError:
                if refresh:
                    show_popup(self.prof_diag, "Error", "Gravatar not found")
                return
            except urllib.error.URLError:
                if refresh:
                    show_popup(self.prof_diag, "Error", "Could not fetch Gravatar")
                return

        if refresh and not email_in_settings:
            show_popup(
                self.prof_diag,
                "Information",
                "Please add your email to the gravatar_ids section in your "
                "mss_settings.json to automatically fetch your gravatar",
                icon=1,)

        self.set_gravatar(gravatar)

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

        if os.path.exists(self.gravatar):
            os.remove(self.gravatar)
            if self.email in config_loader(dataset="gravatar_ids"):
                show_popup(
                    self.prof_diag,
                    "Information",
                    "Please remove your email from gravatar_ids section in your "
                    "mss_settings.json to not fetch gravatar automatically",
                    icon=1,)

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
        if self.verify_user_token():
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
            requests.post(self.mscolab_server_url + '/delete_user', data=data)
        else:
            show_popup(self, "Error", "Your Connection is expired. New Login required!")
        self.logout()

    def add_operation_handler(self):
        if self.verify_user_token():
            def check_and_enable_operation_accept():
                if (self.add_proj_dialog.path.text() != "" and
                        self.add_proj_dialog.description.toPlainText() != "" and
                        self.add_proj_dialog.category.text() != ""):
                    self.add_proj_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
                else:
                    self.add_proj_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

            def browse():
                file_type = ["Flight track (*.ftml)"] + [
                    f"Flight track (*.{ext})" for ext in self.ui.import_plugins.keys()
                ]
                file_path = get_open_filename(
                    self.ui, "Open Flighttrack file", "", ';;'.join(file_type))
                if file_path is not None:
                    file_name = fs.path.basename(file_path)
                    if file_path.endswith('ftml'):
                        with open_fs(fs.path.dirname(file_path)) as file_dir:
                            file_content = file_dir.readtext(file_name)
                    else:
                        ext = fs.path.splitext(file_path)[-1][1:]
                        function = self.ui.import_plugins[ext]
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
        r = requests.post(f'{self.mscolab_server_url}/create_operation', data=data)
        if r.text == "True":
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Your operation was created successfully')
            self.add_operations_to_ui()
            selected_category = self.ui.filterCategoryCb.currentText()
            self.show_categories_to_ui()
            self.operation_category_handler()
            index = self.ui.filterCategoryCb.findText(selected_category, QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.filterCategoryCb.setCurrentIndex(index)
            op_id = self.get_recent_pid()
            self.conn.handle_new_room(op_id)
        else:
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('The path already exists')

    def get_recent_pid(self):
        if self.verify_user_token():
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

    def open_chat_window(self):
        if self.verify_user_token():
            if self.active_pid is None:
                return

            if self.chat_window is not None:
                self.chat_window.activateWindow()
                return

            self.chat_window = mp.MSColabOperationWindow(
                self.token,
                self.active_pid,
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
        if self.verify_user_token():
            if self.active_pid is None:
                return

            if self.admin_window is not None:
                self.admin_window.activateWindow()
                return

            self.admin_window = maw.MSColabAdminWindow(
                self.token,
                self.active_pid,
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
        if self.verify_user_token():
            if self.active_pid is None:
                return

            if self.version_window is not None:
                self.version_window.activateWindow()
                return

            self.version_window = mvh.MSColabVersionHistory(self.token, self.active_pid, self.user,
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
        if self.verify_user_token():
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
                        "op_id": self.active_pid
                    }
                    url = url_join(self.mscolab_server_url, 'delete_operation')
                    try:
                        res = requests.post(url, data=data)
                        res.raise_for_status()
                    except requests.exceptions.RequestException as e:
                        logging.debug(e)
                        show_popup(self.ui, "Error", "Some error occurred! Could not delete operation.")
                else:
                    show_popup(self.ui, "Error", "Entered operation name did not match!")
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def handle_work_locally_toggle(self):
        if self.verify_user_token():
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
        if self.verify_user_token():
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
        if self.verify_user_token():
            server_xml = self.request_wps_from_server()
            server_waypoints_model = ft.WaypointsTableModel(xml_content=server_xml)
            self.merge_dialog = MscolabMergeWaypointsDialog(self.waypoints_model,
                                                            server_waypoints_model, parent=self.ui)
            self.merge_dialog.saveBtn.setDisabled(True)
            if self.merge_dialog.exec_():
                xml_content = self.merge_dialog.get_values()
                if xml_content is not None:
                    self.conn.save_file(self.token, self.active_pid, xml_content, comment=comment)
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
        if self.verify_user_token():
            data = {
                "token": self.token
            }
            r = requests.get(self.mscolab_server_url + '/operations', data=data)
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

    @QtCore.Slot(int)
    def reload_window(self, value):
        if self.active_pid != value or self.ui.workLocallyCheckbox.isChecked():
            return
        self.reload_wps_from_server()

    @QtCore.Slot()
    def reload_windows_slot(self):
        self.reload_window(self.active_pid)

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
        r = requests.get(self.mscolab_server_url + '/user', data=data)
        if r.text != "False":
            _json = json.loads(r.text)
            if _json['user']['id'] == u_id:
                operation = self.get_recent_operation()
                operation_desc = f'{operation["path"]} - {operation["access_level"]}'
                widgetItem = QtWidgets.QListWidgetItem(operation_desc, parent=self.ui.listOperationsMSC)
                widgetItem.op_id = operation["op_id"]
                widgetItem.access_level = operation["access_level"]
                self.ui.listOperationsMSC.addItem(widgetItem)
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
            if op_id != self.active_pid:
                return

            self.access_level = access_level
            # Close mscolab windows based on new access_level and update their buttons
            self.show_operation_options()

            # update view window nav elements if open
            for window in self.ui.get_active_views():
                _type = window.view_type
                if self.access_level == "viewer":
                    self.disable_navbar_action_buttons(_type, window)
                else:
                    self.enable_navbar_action_buttons(_type, window)

        # update chat window if open
        if self.chat_window is not None:
            self.chat_window.load_users()

    def delete_operation_from_list(self, op_id):
        logging.debug('delete operation op_id: %s and active_id is: %s' % (op_id, self.active_pid))
        if self.active_pid == op_id:
            logging.debug('delete_operation_from_list doing: %s' % op_id)
            self.active_pid = None
            self.access_level = None
            self.active_operation_name = None
            # self.ui.workingStatusLabel.setEnabled(False)
            self.close_external_windows()
            self.hide_operation_options()

        # Update operation list
        remove_item = None
        for i in range(self.ui.listOperationsMSC.count()):
            item = self.ui.listOperationsMSC.item(i)
            if item.op_id == op_id:
                remove_item = item
                break
        if remove_item is not None:
            logging.debug(f"remove_item: {remove_item}")
            self.ui.listOperationsMSC.takeItem(self.ui.listOperationsMSC.row(remove_item))
            return remove_item.operation_path

    @QtCore.Slot(int, int)
    def handle_revoke_permission(self, op_id, u_id):
        if u_id == self.user["id"]:
            operation_name = self.delete_operation_from_list(op_id)
            show_popup(self.ui, "Permission Revoked",
                       f'Your access to operation - "{operation_name}" was revoked!', icon=1)

    @QtCore.Slot(int)
    def handle_operation_deleted(self, op_id):
        operation_name = self.delete_operation_from_list(op_id)
        show_popup(self.ui, "Success", f'Operation "{operation_name}" was deleted!', icon=1)

    def show_categories_to_ui(self):
        """
        adds the list of operation categories to the UI
        """
        if self.verify_user_token():
            data = {
                "token": self.token
            }
            r = requests.get(f'{self.mscolab_server_url}/operations', data=data)
            if r.text != "False":
                _json = json.loads(r.text)
                operations = _json["operations"]
                self.ui.filterCategoryCb.clear()
                categories = set(["ANY"])
                for operation in operations:
                    categories.add(operation["category"])
                categories.remove("ANY")
                categories = ["ANY"] + sorted(categories)
                self.ui.filterCategoryCb.addItems(categories)

    def add_operations_to_ui(self):
        if self.verify_user_token():
            data = {
                "token": self.token
            }
            r = requests.get(f'{self.mscolab_server_url}/operations', data=data)
            if r.text != "False":
                _json = json.loads(r.text)
                self.operations = _json["operations"]
                logging.debug("adding operations to ui")
                operations = sorted(self.operations, key=lambda k: k["path"].lower())
                self.ui.listOperationsMSC.clear()
                selectedOperation = None
                for operation in operations:
                    operation_desc = f'{operation["path"]} - {operation["access_level"]}'
                    widgetItem = QtWidgets.QListWidgetItem(operation_desc, parent=self.ui.listOperationsMSC)
                    widgetItem.op_id = operation["op_id"]
                    widgetItem.access_level = operation["access_level"]
                    widgetItem.operation_path = operation["path"]
                    widgetItem.operation_category = operation["category"]
                    if widgetItem.op_id == self.active_pid:
                        selectedOperation = widgetItem
                    self.ui.listOperationsMSC.addItem(widgetItem)
                if selectedOperation is not None:
                    self.ui.listOperationsMSC.setCurrentItem(selectedOperation)
                    self.ui.listOperationsMSC.itemActivated.emit(selectedOperation)
                self.ui.listOperationsMSC.itemActivated.connect(self.set_active_pid)
            else:
                show_popup(self.ui, "Error", "Session expired, new login required")
                self.logout()
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def set_active_pid(self, item):
        if self.verify_user_token():
            if not self.ui.local_active:
                if item.op_id == self.active_pid:
                    return

            # close all hanging window
            self.close_external_windows()
            self.hide_operation_options()

            # Turn off work locally toggle
            self.ui.workLocallyCheckbox.blockSignals(True)
            self.ui.workLocallyCheckbox.setChecked(False)
            self.ui.workLocallyCheckbox.blockSignals(False)

            # set active_pid here
            self.active_pid = item.op_id
            self.access_level = item.access_level
            self.active_operation_name = item.operation_path
            self.waypoints_model = None

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

            self.ui.switch_to_mscolab()
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def switch_to_local(self):
        self.ui.local_active = True
        if self.active_pid is not None:
            if self.verify_user_token():
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
        self.ui.menuProperties.setEnabled(False)
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
        else:
            if self.admin_window is not None:
                self.admin_window.close()

        if self.access_level in ["creator"]:
            self.ui.menuProperties.setEnabled(True)

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
        if self.verify_user_token():
            data = {
                "token": self.token,
                "op_id": self.active_pid
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

    def reload_wps_from_server(self):
        if self.active_pid is None:
            return
        self.load_wps_from_server()
        self.reload_view_windows()

    def handle_waypoints_changed(self):
        if self.verify_user_token():
            if self.ui.workLocallyCheckbox.isChecked():
                self.waypoints_model.save_to_ftml(self.local_ftml_file)
            else:
                xml_content = self.waypoints_model.get_xml_content()
                self.conn.save_file(self.token, self.active_pid, xml_content, comment=None)
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def reload_view_windows(self):
        for window in self.ui.get_active_views():
            window.setFlightTrackModel(self.waypoints_model)
            if hasattr(window, 'mpl'):
                try:
                    window.mpl.canvas.waypoints_interactor.redraw_figure()
                except AttributeError as err:
                    logging.error("%s" % err)

    def handle_import_msc(self, file_path, extension, function, pickertype):
        if self.verify_user_token():
            if self.active_pid is None:
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
                self.conn.save_file(self.token, self.active_pid, xml_content, comment=None)
                self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)
            self.reload_view_windows()
            show_popup(self.ui, "Import Success", f"The file - {file_name}, was imported successfully!", 1)
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def handle_export_msc(self, extension, function, pickertype):
        if self.verify_user_token():
            if self.active_pid is None:
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

    def create_view_msc(self, _type):
        if self.verify_user_token():
            if self.active_pid is None:
                return

            self.waypoints_model.name = self.active_operation_name
            view_window = self.ui.create_view(_type, self.waypoints_model)

            # disable navbar actions in the view for viewer
            if self.access_level == "viewer":
                self.disable_navbar_action_buttons(_type, view_window)
        else:
            show_popup(self.ui, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    def disable_navbar_action_buttons(self, _type, view_window):
        """
        _type: view type (topview, sideview, tableview)
        view_window: PyQt view window

        function disables some control, used if access_level is not appropriate
        """
        if _type == "topview" or _type == "sideview" or _type == "linearview":
            actions = view_window.mpl.navbar.actions()
            for action in actions:
                action_text = action.text()
                if action_text == "Ins WP" or action_text == "Del WP" or action_text == "Mv WP":
                    action.setEnabled(False)
        else:
            # _type == tableview
            view_window.btAddWayPointToFlightTrack.setEnabled(False)
            view_window.btCloneWaypoint.setEnabled(False)
            view_window.btDeleteWayPoint.setEnabled(False)
            view_window.btInvertDirection.setEnabled(False)
            view_window.btRoundtrip.setEnabled(False)
            view_window.cbTools.setEnabled(False)
            view_window.tableWayPoints.setEnabled(False)

    def enable_navbar_action_buttons(self, _type, view_window):
        """
        _type: view type (topview, sideview, tableview)
        view_window: PyQt view window

        function enables some control, used if access_level is appropriate
        """
        if _type == "topview" or _type == "sideview" or _type == "linearview":
            actions = view_window.mpl.navbar.actions()
            for action in actions:
                action_text = action.text()
                if action_text == "Ins WP" or action_text == "Del WP" or action_text == "Mv WP":
                    action.setEnabled(True)
        else:
            # _type == tableview
            view_window.btAddWayPointToFlightTrack.setEnabled(True)
            view_window.btCloneWaypoint.setEnabled(True)
            view_window.btDeleteWayPoint.setEnabled(True)
            view_window.btInvertDirection.setEnabled(True)
            view_window.btRoundtrip.setEnabled(True)
            view_window.cbTools.setEnabled(True)
            view_window.tableWayPoints.setEnabled(True)

    def logout(self):
        self.ui.local_active = True
        self.ui.menu_handler()
        # close all hanging window
        self.close_external_windows()
        self.hide_operation_options()
        # delete token and show login widget-items
        self.token = None
        # delete active-operation-id
        self.active_pid = None
        # delete active access_level
        self.access_level = None
        # delete active operation_name
        self.active_operation_name = None
        # delete local file name
        self.local_ftml_file = None
        # clear operation listing
        self.ui.listOperationsMSC.clear()
        # clear mscolab url
        self.mscolab_server_url = None
        # clear operations list here
        self.ui.mscStatusLabel.setText(self.ui.tr("status: Disconnected"))
        self.ui.usernameLabel.hide()
        self.ui.userOptionsTb.hide()
        self.ui.connectBtn.show()
        self.ui.actionAddOperation.setEnabled(False)
        # disconnect socket
        if self.conn is not None:
            self.conn.disconnect()
            self.conn = None
        # Turn off work locally toggle
        self.ui.workLocallyCheckbox.blockSignals(True)
        self.ui.workLocallyCheckbox.setChecked(False)
        self.ui.workLocallyCheckbox.blockSignals(False)

        # remove temporary gravatar image
        if self.gravatar is not None:
            if self.email not in config_loader(dataset="gravatar_ids") and os.path.exists(self.gravatar):
                try:
                    os.remove(self.gravatar)
                except Exception as e:
                    logging.debug(f"Error while removing gravatar cache... {e}")
        # clear gravatar image path
        self.gravatar = None
        # clear user email
        self.email = None

        # delete mscolab http_auth settings for the url
        if self.mscolab_server_url in self.settings["auth"].keys():
            del self.settings["auth"][self.mscolab_server_url]
        save_settings_qsettings('mscolab', self.settings)

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
