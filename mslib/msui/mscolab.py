# -*- coding: utf-8 -*-
"""

    mslib.msui.mscolab
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Window to display authentication and project details for mscolab


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
import logging
import types
import fs
import requests
import re
import importlib
import functools
from fs import open_fs
from werkzeug.urls import url_join

from mslib.msui import flighttrack as ft
from mslib.msui import mscolab_project as mp
from mslib.msui import mscolab_admin_window as maw
from mslib.msui import mscolab_version_history as mvh
from mslib.msui import sideview, tableview, topview, linearview
from mslib.msui import socket_control as sc

from PyQt5 import QtCore, QtGui, QtWidgets
from mslib.msui.mss_qt import get_open_filename, get_save_filename
from mslib.msui.mss_qt import ui_mscolab_help_dialog as msc_help_dialog
from mslib.msui.mss_qt import ui_add_project_dialog as add_project_ui
from mslib.msui.mss_qt import ui_mscolab_merge_waypoints_dialog as merge_wp_ui
from mslib.msui.mss_qt import ui_mscolab_connect_dialog as ui_conn
from mslib.utils import load_settings_qsettings, save_settings_qsettings, dropEvent, dragEnterEvent, show_popup
from mslib.msui import constants
from mslib.utils import config_loader


class MscolabHelpDialog(QtWidgets.QDialog, msc_help_dialog.Ui_mscolabHelpDialog):

    viewCloses = QtCore.pyqtSignal(name="viewCloses")

    def __init__(self, parent=None):
        super(MscolabHelpDialog, self).__init__(parent)
        self.setupUi(self)
        self.okayBtn.clicked.connect(lambda: self.close())

    def closeEvent(self, event):
        self.viewCloses.emit()


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

        self.stackedWidget.setCurrentWidget(self.loginPage)

        # disable widgets in login frame
        self.loginEmailLe.setEnabled(False)
        self.loginPasswordLe.setEnabled(False)
        self.loginBtn.setEnabled(False)
        self.addUserBtn.setEnabled(False)

        self.urlCb.setEditable(True)
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

        # self.prev_index = 0
        self.resize(self.sizeHint())

        self.statusIconLabel.hide()

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
        self.resize(self.sizeHint())

        # self.prev_index = index

    def set_status(self, _type="Error", msg=""):
        if _type == "Error":
            msg = "⚠ " + msg
            self.statusLabel.setStyleSheet("color: red;")
        elif _type == "Success":
            self.statusLabel.setStyleSheet("color: green;")
            msg = "✓ " + msg
        else:
            self.statusLabel.setStyleSheet("color: white;")
            msg = "ⓘ  " + msg
        # self.pixmap = QtGui.QPixmap(self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton))
        # self.statusIconLabel.setPixmap(self.pixmap)
        # self.statusIconLabel.setAlignment(QtGui.Qt.AlignCenter)
        self.statusLabel.setText(msg)

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
        except requests.exceptions.ConnectionError:
            logging.debug("MSColab server isn't active")
            self.set_status("Error", "MSColab server isn't active")
        except requests.exceptions.InvalidSchema:
            logging.debug("invalid schema of url")
            self.set_status("Error", "Invalid Url Scheme!")
        except requests.exceptions.InvalidURL:
            logging.debug("invalid url")
            self.set_status("Error", "Invalid URL")
        except requests.exceptions.SSLError:
            logging.debug("Certificate Verification Failed")
            self.set_status("Error", "Certificate Verification Failed")
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
            self.set_status("Error", 'Failed to establish a new connection'
                                        f' to "{self.mscolab_server_url}". Try in a moment again.')
            self.disconnect_handler()
            return

        if r.text == "False":
            # popup that has wrong credentials
            self.set_status("Error", 'Oh no, your credentials were incorrect.')
        elif r.text == "Unauthorized Access":
            # Server auth required for logging in
            self.login_data = [data, r, url, auth]
            self.connectBtn.setEnabled(False)
            self.stackedWidget.setCurrentWidget(self.wmsAuthPage)
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
            self.set_status("Error", 'Failed to establish a new connection'
                                        f' to "{self.mscolab_server_url}". Try in a moment again.')
            self.disconnect_handler()
            return

        if r.status_code == 201:
            self.set_status("Success", 'You are registered, you can now log in.')
            self.stackedWidget.setCurrentWidget(self.loginPage)
        elif r.status_code == 401:
            self.newuser_data = [data, r, url]
            self.stackedWidget.setCurrentWidget(self.wmsAuthPage)
            self.httpBb.accepted.connect(self.newuser_server_auth)
            self.httpBb.rejected.connect(lambda: self.stackedWidget.setCurrentWidget(self.newuserPage))
        else:
            error_msg = json.loads(r.text)["message"]
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


def verify_user_token(func):
    @functools.wraps(func)
    def wrapper(ref, *args, **kwargs):
        data = {
            "token": ref.token
        }
        try:
            r = requests.get(f'{ref.mscolab_server_url}/test_authorized', data=data)
        except requests.exceptions.ConnectionError as ex:
            logging.error("unexpected error: %s %s", type(ex), ex)
            return False
        if r.text != "True":
            show_popup(ref, "Error", "Your Connection is expired. New Login required!")
            ref.logout()
        else:
            func(ref, *args, *kwargs)
    return wrapper


class MSSMscolab():
    """
    Class for implementing MSColab functionalities
    """
    name = "Mscolab"
    identifier = None
    viewCloses = QtCore.pyqtSignal(name="viewCloses")

    def __init__(self, ui=None, data_dir=None):
        self.ui = ui

        # hide online widgets
        self.ui.usernameLabel.hide()
        self.ui.userOptionsTb.hide()
        self.ui.addProjectBtn.hide()
        self.hide_project_options()

        # if token is None, not authorized, else authorized
        self.token = None
        # int to store active pid
        self.active_pid = None
        # storing access_level to save network call
        self.access_level = None
        # storing project_name to save network call
        self.active_project_name = None
        # Storing project list to pass to admin window
        self.projects = None
        # store active_flight_path here as object
        self.waypoints_model = None
        # Store active project's file path
        self.local_ftml_file = None
        # store a reference of window in class
        self.open_windows_mscolab = []
        # connection object to interact with sockets
        self.conn = None
        # store window instances
        self.active_windows = []
        # assign ids to view-window
        self.id_count = 0
        # project window
        self.chat_window = None
        # Admin Window
        self.admin_window = None
        # Version History Window
        self.version_window = None
        # Merge waypoints dialog
        self.merge_dialog = None
        # Mscolab help dialog
        self.help_dialog = None
        # MSColab Server URL
        self.mscolab_server_url = None

        # # set data dir, uri
        # if data_dir is None:
        #     self.data_dir = config_loader(dataset="mss_dir")
        # else:
        #     self.data_dir = data_dir
        # self.export_plugins = self.add_plugins(dataset="export_plugins")
        # self.import_plugins = self.add_plugins(dataset="import_plugins")
        # self.create_dir()

    def open_connect_window(self):
        self.connect_window = MSColab_ConnectDialog(parent=self.ui, mscolab=self)
        self.connect_window.setModal(True)
        self.connect_window.exec_()

    def after_login(self, emailid, url, r):
        self.connect_window.close()
        # fill value of mscolab url if found in QSettings storage
        self.settings = load_settings_qsettings(
            'mscolab', default_settings={'auth': {}, 'server_settings': {}})

        _json = json.loads(r.text)
        self.token = _json["token"]
        self.user = _json["user"]
        self.mscolab_server_url = url

        self.ui.connectBtn.hide()
        # display connection status
        self.ui.mscStatusLabel.setText(self.ui.tr(f"Connected to MSColab Server at {self.mscolab_server_url}"))
        # display username beside useroptions toolbutton
        self.ui.usernameLabel.setText(f"{self.user['username']}")
        self.ui.usernameLabel.show()
        # set up user menu and add to toolbutton
        self.user_menu = QtWidgets.QMenu()
        self.user_menu.addAction("Profile")
        self.user_menu.addAction("Help")
        self.user_menu.addAction("Logout", self.logout)
        self.ui.userOptionsTb.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.ui.userOptionsTb.setMenu(self.user_menu)
        self.ui.userOptionsTb.show()
        # self.pixmap = QtGui.QPixmap("msui_redesign/gravatar.jpg")
        # self.icon = QtGui.QIcon()
        # self.icon.addPixmap(self.pixmap, QtGui.QIcon.Normal, QtGui.QIcon.Off)
        # self.userOptionsTb.setIcon(self.icon)
        # show add project button here
        self.ui.addProjectBtn.show()
        # connect slot for handling project options combobox
        self.ui.projectOptionsCb.currentIndexChanged.connect(self.project_options_handler)

        # Populate open projects list
        self.add_projects_to_ui()

#         # create socket connection here
#         self.conn = sc.ConnectionManager(self.token, user=self.user, mscolab_server_url=self.mscolab_server_url)
#         self.conn.signal_reload.connect(self.reload_window)
#         self.conn.signal_new_permission.connect(self.render_new_permission)
#         self.conn.signal_update_permission.connect(self.handle_update_permission)
#         self.conn.signal_revoke_permission.connect(self.handle_revoke_permission)
#         self.conn.signal_project_deleted.connect(self.handle_project_deleted)

        # switch to share tab
        self.ui.tabWidget.setCurrentIndex(1)

    def project_options_handler(self, index):
        selected_option = self.ui.projectOptionsCb.currentText()
        self.ui.projectOptionsCb.blockSignals(True)
        self.ui.projectOptionsCb.setCurrentIndex(0)
        self.ui.projectOptionsCb.blockSignals(False)

        if selected_option == "Chat":
            self.open_chat_window()
        elif selected_option == "Version History":
            self.open_version_history_window()
        elif selected_option == "Manage Users":
            self.open_admin_window()
        elif selected_option == "Share Project":
            pass
        elif selected_option == "Delete Project":
            pass

    @verify_user_token
    def open_chat_window(self):
        if self.active_pid is None:
            return

        if self.chat_window is not None:
            self.chat_window.raise_()
            self.chat_window.activateWindow()
            return

        self.chat_window = mp.MSColabProjectWindow(self.token, self.active_pid, self.user, self.active_project_name,
                                                    self.access_level, self.conn,
                                                    mscolab_server_url=self.mscolab_server_url)
        self.chat_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.chat_window.viewCloses.connect(self.close_chat_window)
        self.chat_window.reloadWindows.connect(self.reload_windows_slot)
        self.chat_window.show()

    def close_chat_window(self):
        self.chat_window = None

    @verify_user_token
    def open_admin_window(self):
        if self.active_pid is None:
            return

        if self.admin_window is not None:
            self.admin_window.raise_()
            self.admin_window.activateWindow()
            return

        self.admin_window = maw.MSColabAdminWindow(self.token, self.active_pid, self.user,
                                                    self.active_project_name, self.projects, self.conn,
                                                    mscolab_server_url=self.mscolab_server_url)
        self.admin_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.admin_window.viewCloses.connect(self.close_admin_window)
        self.admin_window.show()

    def close_admin_window(self):
        self.admin_window = None

    @verify_user_token
    def open_version_history_window(self):
        if self.active_pid is None:
            return

        if self.version_window is not None:
            self.version_window.raise_()
            self.version_window.activateWindow()
            return

        self.version_window = mvh.MSColabVersionHistory(self.token, self.active_pid, self.user,
                                                        self.active_project_name, self.conn,
                                                        mscolab_server_url=self.mscolab_server_url)
        self.version_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.version_window.viewCloses.connect(self.close_version_history_window)
        self.version_window.reloadWindows.connect(self.reload_windows_slot)
        self.version_window.show()

    def close_version_history_window(self):
        self.version_window = None

    def close_external_windows(self):
        if self.chat_window is not None:
            self.chat_window.close()
        if self.admin_window is not None:
            self.admin_window.close()
        if self.version_window is not None:
            self.version_window.close()

    def get_recent_project(self):
        """
        get most recent project
        """
        if self.verify_user_token():
            data = {
                "token": self.token
            }
            r = requests.get(self.mscolab_server_url + '/projects', data=data)
            if r.text != "False":
                _json = json.loads(r.text)
                projects = _json["projects"]
                recent_project = None
                if projects:
                    recent_project = projects[-1]
                return recent_project
            else:
                show_popup(self, "Error", "Session expired, new login required")
        else:
            show_popup(self, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    @QtCore.Slot(int)
    def reload_window(self, value):
        if self.active_pid != value or self.workLocallyCheckBox.isChecked():
            return
        self.reload_wps_from_server()

    @QtCore.Slot(int, int)
    def render_new_permission(self, p_id, u_id):
        """
        p_id: project id
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
                project = self.get_recent_project()
                project_desc = f'{project["path"]} - {project["access_level"]}'
                widgetItem = QtWidgets.QListWidgetItem(project_desc, parent=self.ui.listProjectsMSC)
                widgetItem.p_id = project["p_id"]
                widgetItem.access_level = project["access_level"]
                self.ui.listProjectsMSC.addItem(widgetItem)
            if self.chat_window is not None:
                self.chat_window.load_users()
        else:
            show_popup(self, "Error", "Your Connection is expired. New Login required!")
            self.logout()

    @QtCore.Slot(int, int, str)
    def handle_update_permission(self, p_id, u_id, access_level):
        """
        p_id: project id
        u_id: user id
        access_level: updated access level

        function updates existing permissions and related control availability
        """
        if u_id == self.user["id"]:
            # update table of projects
            project_name = None
            for i in range(self.ui.listProjectsMSC.count()):
                item = self.ui.listProjectsMSC.item(i)
                if item.p_id == p_id:
                    desc = item.text().split(' - ')
                    project_name = desc[0]
                    desc[-1] = access_level
                    desc = ' - '.join(desc)
                    item.setText(desc)
                    item.access_level = access_level
                    break
            if project_name is not None:
                show_popup(self, "Permission Updated",
                           f"Your access level to project - {project_name} was updated to {access_level}!", 1)
            if p_id != self.active_pid:
                return

            self.access_level = access_level
            # Close mscolab windows based on new access_level and update their buttons
            self.show_project_options()

            # # update view window nav elements if open
            # for window in self.active_windows:
            #     _type = window.view_type
            #     if self.access_level == "viewer":
            #         self.disable_navbar_action_buttons(_type, window)
            #     else:
            #         self.enable_navbar_action_buttons(_type, window)

        # update chat window if open
        if self.chat_window is not None:
            self.chat_window.load_users()

    def delete_project_from_list(self, p_id):
        logging.debug('delete project p_id: %s and active_id is: %s' % (p_id, self.active_pid))
        if self.active_pid == p_id:
            logging.debug('delete_project_from_list doing: %s' % p_id)
            self.active_pid = None
            self.access_level = None
            self.active_project_name = None
            self.workingStatusLabel.hide()
            # self.force_close_view_windows()
            self.close_external_windows()
            self.hide_project_options()

        # Update project list
        remove_item = None
        for i in range(self.ui.listProjectsMSC.count()):
            item = self.ui.listProjectsMSC.item(i)
            if item.p_id == p_id:
                remove_item = item
        if remove_item is not None:
            logging.debug("remove_item: %s" % remove_item)
            self.ui.listProjectsMSC.takeItem(self.ui.listProjectsMSC.row(remove_item))
            return remove_item.text().split(' - ')[0]

    @QtCore.Slot(int, int)
    def handle_revoke_permission(self, p_id, u_id):
        if u_id == self.user["id"]:
            project_name = self.delete_project_from_list(p_id)
            show_popup(self, "Permission Revoked", f'Your access to project - "{project_name}" was revoked!', icon=1)

    @QtCore.Slot(int)
    def handle_project_deleted(self, p_id):
        project_name = self.delete_project_from_list(p_id)
        show_popup(self, "Success", f'Project "{project_name}" was deleted!', icon=1)

    @verify_user_token
    def add_projects_to_ui(self):
        data = {
            "token": self.token
        }
        r = requests.get(f'{self.mscolab_server_url}/projects', data=data)
        if r.text != "False":
            _json = json.loads(r.text)
            self.projects = _json["projects"]
            logging.debug("adding projects to ui")
            projects = sorted(self.projects, key=lambda k: k["path"].lower())
            self.ui.listProjectsMSC.clear()
            selectedProject = None
            for project in projects:
                project_desc = f'{project["path"]} - {project["access_level"]}'
                widgetItem = QtWidgets.QListWidgetItem(project_desc, parent=self.ui.listProjectsMSC)
                widgetItem.p_id = project["p_id"]
                widgetItem.access_level = project["access_level"]
                if widgetItem.p_id == self.active_pid:
                    selectedProject = widgetItem
                self.ui.listProjectsMSC.addItem(widgetItem)
            if selectedProject is not None:
                self.ui.listProjectsMSC.setCurrentItem(selectedProject)
                self.ui.listProjectsMSC.itemActivated.emit(selectedProject)
            self.ui.listProjectsMSC.itemActivated.connect(self.set_active_pid)
        else:
            show_popup(self, "Error", "Session expired, new login required")
            self.logout()

    @verify_user_token
    def set_active_pid(self, item):
        if item.p_id == self.active_pid:
            return
        # # close all hanging window
        # self.force_close_view_windows()
        self.close_external_windows()

        # Turn off work locally toggle
        self.ui.workLocallyCheckbox.blockSignals(True)
        self.ui.workLocallyCheckbox.setChecked(False)
        self.ui.workLocallyCheckbox.blockSignals(False)
        self.ui.sandboxOptionsCb.hide()

        # set active_pid here
        self.active_pid = item.p_id
        self.access_level = item.access_level
        self.active_project_name = item.text().split("-")[0].strip()
        self.waypoints_model = None

        # # set active flightpath here
        # self.load_wps_from_server()

        # display working status
        self.ui.workingStatusLabel.setText(self.ui.tr("Working On: Shared File."
                                             "All your changes will be shared with everyone."
                                             "Turn on work locally to work on local flight track file"))
        self.ui.workingStatusLabel.show()
        # enable access level specific buttons
        self.show_project_options()

        # change font style for selected
        font = QtGui.QFont()
        for i in range(self.ui.listProjectsMSC.count()):
            self.ui.listProjectsMSC.item(i).setFont(font)
        font.setBold(True)
        item.setFont(font)

    def show_project_options(self):
        project_opt_list = ['Project Options']
        allow_version_access = self.access_level in ["creator", "admin", "collaborator"]
        if allow_version_access:
            project_opt_list.extend(['Chat', 'Version History'])
            self.ui.workLocallyCheckbox.show()

        allow_version_access = self.access_level in ["creator", "admin"]
        if allow_version_access:
            project_opt_list.extend(['Manage Users'])

        allow_version_access = self.access_level in ["creator"]
        if allow_version_access:
            project_opt_list.extend(['Share Project', 'Delete Project'])

        self.ui.projectOptionsCb.clear()
        self.ui.projectOptionsCb.addItems(project_opt_list)
        self.ui.projectOptionsCb.show()

    def hide_project_options(self):
        self.ui.workingStatusLabel.hide()
        self.ui.projectOptionsCb.hide()
        self.ui.workLocallyCheckbox.hide()
        self.ui.sandboxOptionsCb.hide()

    @verify_user_token
    def request_wps_from_server(self):
        data = {
            "token": self.token,
            "p_id": self.active_pid
        }
        r = requests.get(self.mscolab_server_url + '/get_project_by_id', data=data)
        if r.text != "False":
            xml_content = json.loads(r.text)["content"]
            return xml_content
        else:
            show_popup(self, "Error", "Session expired, new login required")

    def load_wps_from_server(self):
        if self.workLocallyCheckBox.isChecked():
            return
        xml_content = self.request_wps_from_server()
        if xml_content is not None:
            self.waypoints_model = ft.WaypointsTableModel(xml_content=xml_content)
            self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)

    def reload_wps_from_server(self):
        if self.active_pid is None:
            return
        self.load_wps_from_server()
        self.reload_view_windows()

    @verify_user_token
    def create_view_msc(self, _type):
        if self.active_pid is None:
            return

        for active_window in self.active_windows:
            if active_window.view_type == _type:
                active_window.raise_()
                active_window.activateWindow()
                return

        self.waypoints_model.name = self.active_project_name
        if _type == "topview":
            view_window = topview.MSSTopViewWindow(model=self.waypoints_model,
                                                   parent=self.ui.listProjectsMSC,
                                                   _id=self.id_count)
        elif _type == "sideview":
            view_window = sideview.MSSSideViewWindow(model=self.waypoints_model,
                                                     parent=self.ui.listProjectsMSC,
                                                     _id=self.id_count)
        elif _type == "tableview":
            view_window = tableview.MSSTableViewWindow(model=self.waypoints_model,
                                                       parent=self.ui.listProjectsMSC,
                                                       _id=self.id_count)
        elif _type == "linearview":
            view_window = linearview.MSSLinearViewWindow(model=self.waypoints_model,
                                                         parent=self.ui.listProjectsMSC,
                                                         _id=self.id_count)
        view_window.view_type = _type

        if self.access_level == "viewer":
            self.disable_navbar_action_buttons(_type, view_window)

        view_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        view_window.setWindowTitle(f"{view_window.windowTitle()} - {self.active_project_name}")
        view_window.show()
        view_window.viewClosesId.connect(self.handle_view_close)
        self.active_windows.append(view_window)

        # increment id_count
        self.id_count += 1

    def force_close_view_windows(self):
        for window in self.active_windows[:]:
            window.handle_force_close()
        self.active_windows = []

    def logout(self):
        # switch to local tab
        self.ui.tabWidget.setCurrentIndex(0)
        # delete token and show login widget-items
        self.token = None
        # delete active-project-id
        self.active_pid = None
        # delete active access_level
        self.access_level = None
        # delete active project_name
        self.active_project_name = None
        # delete local file name
        self.local_ftml_file = None
        # clear project listing
        self.ui.listProjectsMSC.clear()
        # clear projects list here
        self.ui.mscStatusLabel.setText(self.ui.tr("status: Disconnected"))
        self.ui.usernameLabel.hide()
        self.ui.userOptionsTb.hide()
        self.ui.connectBtn.show()
        # # disconnect socket
        # if self.conn is not None:
        #     self.conn.disconnect()
        #     self.conn = None
        # # close all hanging window
        # self.force_close_view_windows()
        self.close_external_windows()
        self.ui.addProjectBtn.hide()
        self.hide_project_options()

        # # delete mscolab http_auth settings for the url
        # if self.mscolab_server_url in self.settings["auth"].keys():
        #     del self.settings["auth"][self.mscolab_server_url]
        # save_settings_qsettings('mscolab', self.settings)


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
            self.setWindowTitle(self.ui.tr("Fetch Waypoints From Server"))
            btn_size_policy = self.overwriteBtn.sizePolicy()
            btn_size_policy.setRetainSizeWhenHidden(True)
            self.overwriteBtn.setSizePolicy(btn_size_policy)
            self.overwriteBtn.setVisible(False)
            self.saveBtn.setText(self.ui.tr("Save Waypoints To Local File"))

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


