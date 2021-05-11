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
from fs import open_fs
from werkzeug.urls import url_join

from mslib.msui import flighttrack as ft
from mslib.msui import mscolab_admin_window as maw
from mslib.msui import mscolab_project as mp
from mslib.msui import mscolab_version_history as mvh
from mslib.msui import sideview, tableview, topview
from mslib.msui import socket_control as sc

from PyQt5 import QtCore, QtGui, QtWidgets
from mslib.msui.mss_qt import get_open_filename, get_save_filename
from mslib.msui.qt5 import ui_mscolab_help_dialog as msc_help_dialog
from mslib.msui.qt5 import ui_add_project_dialog as add_project_ui
from mslib.msui.qt5 import ui_add_user_dialog as add_user_ui
from mslib.msui.qt5 import ui_mscolab_window as ui
from mslib.msui.qt5 import ui_wms_password_dialog as ui_pw
from mslib.msui.qt5 import ui_mscolab_merge_waypoints_dialog
from mslib.utils import load_settings_qsettings, save_settings_qsettings, dropEvent, dragEnterEvent, show_popup
from mslib.msui import constants
from mslib.utils import config_loader

MSCOLAB_URL_LIST = QtGui.QStandardItemModel()


def add_mscolab_urls(combo_box, url_list):
    combo_box_urls = [combo_box.itemText(_i) for _i in range(combo_box.count())]
    for url in (_url for _url in url_list if _url not in combo_box_urls):
        combo_box.addItem(url)


class MSSMscolabWindow(QtWidgets.QMainWindow, ui.Ui_MSSMscolabWindow):
    """
    PyQt window implementing mscolab window
    """
    name = "Mscolab"
    identifier = None
    viewCloses = QtCore.pyqtSignal(name="viewCloses")

    # ToDo refactor tests, mscolab_server_url not used
    def __init__(self, parent=None, data_dir=None, mscolab_server_url=None):
        """
        Set up user interface
        """
        super(MSSMscolabWindow, self).__init__(parent)
        self.setupUi(self)
        self.loggedInWidget.hide()
        # if token is None, not authorized, else authorized
        self.token = None
        # User related signals
        self.toggleConnectionBtn.clicked.connect(self.connect_handler)
        self.addUser.clicked.connect(self.add_user_handler)
        self.loginButton.clicked.connect(self.authorize)
        self.logoutButton.clicked.connect(self.logout)
        self.deleteAccountButton.clicked.connect(self.delete_account)
        self.helpBtn.clicked.connect(self.open_help_dialog)
        # Project related signals
        self.addProject.clicked.connect(self.add_project_handler)
        self.importBtn.clicked.connect(self.handle_import)
        self.exportBtn.clicked.connect(self.handle_export)
        self.workLocallyCheckBox.stateChanged.connect(self.handle_work_locally_toggle)
        self.save_ft.clicked.connect(self.save_wp_mscolab)
        self.fetch_ft.clicked.connect(self.fetch_wp_mscolab)
        self.chatWindowBtn.clicked.connect(self.open_chat_window)
        self.adminWindowBtn.clicked.connect(self.open_admin_window)
        self.versionHistoryBtn.clicked.connect(self.open_version_history_window)
        self.deleteProjectBtn.clicked.connect(self.handle_delete_project)
        # View related signals
        self.topview.clicked.connect(self.open_topview)
        self.sideview.clicked.connect(self.open_sideview)
        self.tableview.clicked.connect(self.open_tableview)
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
        # set data dir, uri
        if data_dir is None:
            self.data_dir = config_loader(dataset="mss_dir")
        else:
            self.data_dir = data_dir
        self.create_dir()
        self.mscolab_server_url = None
        self.disable_action_buttons()
        # disabling login, add user button. they are enabled when url is connected
        self.loginButton.setEnabled(False)
        self.addUser.setEnabled(False)
        self.url.setEditable(True)
        self.url.setModel(MSCOLAB_URL_LIST)
        # fill value of mscolab url from config
        default_MSCOLAB = config_loader(
            dataset="default_MSCOLAB")
        add_mscolab_urls(self.url, default_MSCOLAB)
        self.emailid.setEnabled(False)
        self.password.setEnabled(False)

        # fill value of mscolab url if found in QSettings storage
        self.settings = \
            load_settings_qsettings('mscolab',
                                    default_settings={'recent_mscolab_urls': [], 'auth': {}, 'server_settings': {}})
        if len(self.settings['recent_mscolab_urls']) > 0:
            add_mscolab_urls(self.url, self.settings['recent_mscolab_urls'])

    def create_dir(self):
        # ToDo this needs to be done earlier
        if '://' in self.data_dir:
            try:
                _ = fs.open_fs(self.data_dir)
            except fs.errors.CreateFailed:
                logging.error(f'Make sure that the FS url "{self.data_dir}" exists')
                show_popup(self, "Error", f'FS Url: "{self.data_dir}" does not exist!')
                sys.exit()
            except fs.opener.errors.UnsupportedProtocol:
                logging.error(f'FS url "{self.data_dir}" not supported')
                show_popup(self, "Error", f'FS Url: "{self.data_dir}" not supported!')
                sys.exit()
        else:
            _dir = os.path.expanduser(self.data_dir)
            if not os.path.exists(_dir):
                os.makedirs(_dir)

    def disconnect_handler(self):
        self.logout()
        self.status.setText("Status: disconnected")
        self.emailid.setEnabled(False)
        self.password.setEnabled(False)
        # enable and disable right buttons
        self.loginButton.setEnabled(False)
        self.addUser.setEnabled(False)
        self.emailid.setEnabled(False)
        self.password.setEnabled(False)
        self.emailid.textChanged[str].disconnect(self.text_changed)
        self.password.textChanged[str].disconnect(self.text_changed)
        # toggle to connect button
        self.toggleConnectionBtn.setText('Connect')
        self.toggleConnectionBtn.clicked.disconnect(self.disconnect_handler)
        self.toggleConnectionBtn.clicked.connect(self.connect_handler)
        self.url.setEnabled(True)
        # set mscolab_server_url to None
        self.mscolab_server_url = None

    def show_info(self, text):
        self.error_dialog = QtWidgets.QErrorMessage()
        self.error_dialog.showMessage(text)

    def connect_handler(self):
        try:
            url = str(self.url.currentText())
            r = requests.get(url_join(url, 'status'))
            if r.text == "Mscolab server":
                # delete mscolab http_auth settings for the url
                if url not in self.settings["recent_mscolab_urls"]:
                    self.settings["recent_mscolab_urls"].append(url)
                if self.mscolab_server_url in self.settings["auth"].keys():
                    del self.settings["auth"][self.mscolab_server_url]
                # assign new url to self.mscolab_server_url
                self.mscolab_server_url = url
                self.status.setText("Status: connected")
                # enable and disable right buttons
                self.loginButton.setEnabled(False)
                self.addUser.setEnabled(True)
                self.emailid.setEnabled(True)
                self.password.setEnabled(True)
                # activate login button after email and password are entered
                self.emailid.textChanged[str].connect(self.text_changed)
                self.password.textChanged[str].connect(self.text_changed)
                # toggle to disconnect button
                self.toggleConnectionBtn.setText('Disconnect')
                self.toggleConnectionBtn.clicked.disconnect(self.connect_handler)
                self.toggleConnectionBtn.clicked.connect(self.disconnect_handler)
                self.url.setEnabled(False)
                if self.mscolab_server_url not in self.settings["server_settings"].keys():
                    self.settings["server_settings"].update({self.mscolab_server_url: {}})
                save_settings_qsettings('mscolab', self.settings)
                self.emailid.setEnabled(True)
                self.password.setEnabled(True)
                emailid = config_loader(dataset="MSCOLAB_mailid")
                self.emailid.setText(emailid)
                password = config_loader(dataset="MSCOLAB_password")
                self.password.setText(password)
                if len(emailid) > 0 and len(password) > 0:
                    self.loginButton.setEnabled(True)
            else:
                show_popup(self, "Error", "Some unexpected error occurred. Please try again.")
        except requests.exceptions.ConnectionError:
            logging.debug("MSColab server isn't active")
            show_popup(self, "Error", "MSColab server isn't active")
        except requests.exceptions.InvalidSchema:
            logging.debug("invalid schema of url")
            show_popup(self, "Error", "Invalid Url Scheme!")
        except requests.exceptions.InvalidURL:
            logging.debug("invalid url")
            show_popup(self, "Error", "Invalid URL")
        except requests.exceptions.SSLError:
            logging.debug("Certificate Verification Failed")
            show_popup(self, "Error", "Certificate Verification Failed")
        except Exception as e:
            logging.debug("Error %s", str(e))
            show_popup(self, "Error", "Some unexpected error occurred. Please try again.")

    def text_changed(self):
        self.loginButton.setEnabled(self.emailid.text() != "" and self.password.text() != "")

    def handle_import(self):
        file_path = get_open_filename(self, "Select a file", "", "Flight track (*.ftml)")
        if file_path is None:
            return
        dir_path, file_name = fs.path.split(file_path)
        with open_fs(dir_path) as file_dir:
            xml_content = file_dir.readtext(file_name)
        try:
            model = ft.WaypointsTableModel(xml_content=xml_content)
        except SyntaxError:
            show_popup(self, "Import Failed", f"The file - {file_name}, does not contain valid XML")
            return
        self.waypoints_model = model
        if self.workLocallyCheckBox.isChecked():
            self.waypoints_model.save_to_ftml(self.local_ftml_file)
            self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)
        else:
            self.conn.save_file(self.token, self.active_pid, xml_content, comment=None)
            self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)
        self.reload_view_windows()
        show_popup(self, "Import Success", f"The file - {file_name}, was imported successfully!", 1)

    def handle_export(self):
        # Setting default filename path for filedialogue
        default_filename = self.active_project_name + ".ftml"
        file_path = get_save_filename(self, "Save Flight track", default_filename, "Flight track (*.ftml)")
        if file_path is None:
            return
        xml_doc = self.waypoints_model.get_xml_doc()
        dir_path, file_name = fs.path.split(file_path)
        with open_fs(dir_path).open(file_name, 'w') as file:
            xml_doc.writexml(file, indent="  ", addindent="  ", newl="\n", encoding="utf-8")

    def disable_project_buttons(self):
        self.save_ft.setEnabled(False)
        self.fetch_ft.setEnabled(False)
        self.topview.setEnabled(False)
        self.sideview.setEnabled(False)
        self.tableview.setEnabled(False)
        self.workLocallyCheckBox.setEnabled(False)
        self.importBtn.setEnabled(False)
        self.exportBtn.setEnabled(False)
        self.chatWindowBtn.setEnabled(False)
        self.adminWindowBtn.setEnabled(False)
        self.versionHistoryBtn.setEnabled(False)
        self.deleteProjectBtn.setEnabled(False)
        self.helperTextLabel.setVisible(False)
        self.emailid.setEnabled(False)
        self.password.setEnabled(False)

    def disable_action_buttons(self):
        # disable some buttons to be activated after successful login or project activate
        self.addProject.setEnabled(False)
        self.disable_project_buttons()

    def authenticate(self, data, r, url):
        if r.status_code == 401:
            dlg = MSCOLAB_AuthenticationDialog(parent=self)
            dlg.setModal(True)
            if dlg.exec_() == QtWidgets.QDialog.Accepted:
                username, password = dlg.getAuthInfo()
                self.settings["auth"][self.mscolab_server_url] = (username, password)
                # save to cache
                save_settings_qsettings('mscolab', self.settings)
                s = requests.Session()
                s.auth = (username, password)
                s.headers.update({'x-test': 'true'})
                r = s.post(url, data=data)
        return r

    def add_project_handler(self):
        if self.token is None:
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Please login to use this feature')
            return
        else:
            logging.debug(self.token)
        self.proj_diag = QtWidgets.QDialog()
        self.add_proj_dialog = add_project_ui.Ui_addProjectDialog()
        self.add_proj_dialog.setupUi(self.proj_diag)
        self.add_proj_dialog.f_content = None
        self.add_proj_dialog.buttonBox.accepted.connect(self.add_project)
        self.add_proj_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.add_proj_dialog.path.textChanged.connect(self.check_and_enable_project_accept)
        self.add_proj_dialog.description.textChanged.connect(self.check_and_enable_project_accept)
        self.add_proj_dialog.browse.clicked.connect(self.set_exported_file)
        self.proj_diag.show()

    def check_and_enable_project_accept(self):
        if self.add_proj_dialog.path.text() != "" and self.add_proj_dialog.description.toPlainText() != "":
            self.add_proj_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.add_proj_dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

    def set_exported_file(self):
        file_path = get_open_filename(
            self, "Open ftml file", "", "Flight Track Files (*.ftml)")
        if file_path is not None:
            file_name = fs.path.basename(file_path)
            with open_fs(fs.path.dirname(file_path)) as file_dir:
                file_content = file_dir.readtext(file_name)
            self.add_proj_dialog.f_content = file_content
            self.add_proj_dialog.selectedFile.setText(file_name)

    def add_project(self):
        path = self.add_proj_dialog.path.text()
        description = self.add_proj_dialog.description.toPlainText()
        if not path:
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Path can\'t be empty')
            return
        elif not description:
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Description can\'t be empty')
            return
        # regex checks if the whole path from beginning to end only contains alphanumerical characters or _ and -
        elif not re.match("^[a-zA-Z0-9_-]*$", path):
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Path can\'t contain spaces or special characters')
            return

        data = {
            "token": self.token,
            "path": path,
            "description": description
        }
        if self.add_proj_dialog.f_content is not None:
            data["content"] = self.add_proj_dialog.f_content
        r = requests.post(f'{self.mscolab_server_url}/create_project', data=data)
        if r.text == "True":
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Your project was created successfully')
            self.add_projects()
            p_id = self.get_recent_pid()
            self.conn.handle_new_room(p_id)
        else:
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('The path already exists')

    def add_user_handler(self):
        self.user_diag = QtWidgets.QDialog()
        self.add_user_dialog = add_user_ui.Ui_addUserDialog()
        self.add_user_dialog.setupUi(self.user_diag)
        self.add_user_dialog.buttonBox.accepted.connect(self.add_user)
        self.user_diag.show()

    def add_user(self):
        for key, value in config_loader(dataset="MSC_login").items():
            if key not in constants.MSC_LOGIN_CACHE:
                constants.MSC_LOGIN_CACHE[key] = value
        auth = constants.MSC_LOGIN_CACHE.get(self.mscolab_server_url, (None, None))

        emailid = self.add_user_dialog.emailid.text()
        password = self.add_user_dialog.password.text()
        re_password = self.add_user_dialog.rePassword.text()
        username = self.add_user_dialog.username.text()
        if password == re_password:
            data = {
                "email": emailid,
                "password": password,
                "username": username
            }
            s = requests.Session()
            s.auth = (auth[0], auth[1])
            s.headers.update({'x-test': 'true'})
            url = f'{self.mscolab_server_url}/register'
            r = s.post(url, data=data)
            if r.status_code == 401:
                r = self.authenticate(data, r, url)
                if r.status_code == 201:
                    constants.MSC_LOGIN_CACHE[self.mscolab_server_url] = (username, password)
            if r.status_code == 201:
                self.error_dialog = QtWidgets.QErrorMessage()
                self.error_dialog.showMessage('You are registered, you can now log in.')
            else:
                self.error_dialog = QtWidgets.QErrorMessage()
                self.error_dialog.showMessage(r.json()["message"])
        else:
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Oh no, your passwords don\'t match')

    def close_help_dialog(self):
        self.help_dialog = None

    def open_help_dialog(self):
        if self.help_dialog is not None:
            self.help_dialog.raise_()
            self.help_dialog.activateWindow()
        else:
            self.help_dialog = MscolabHelpDialog(self)
            self.help_dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.help_dialog.viewCloses.connect(self.close_help_dialog)
            self.help_dialog.show()

    def handle_delete_project(self):
        entered_project_name, ok = QtWidgets.QInputDialog.getText(
            self,
            self.tr('Delete Project'),
            self.tr(f"You're about to delete the project - '{self.active_project_name}'. "
                    f"Enter the project name to confirm: "))
        if ok:
            if entered_project_name == self.active_project_name:
                data = {
                    "token": self.token,
                    "p_id": self.active_pid
                }
                url = url_join(self.mscolab_server_url, 'delete_project')
                try:
                    res = requests.post(url, data=data)
                    res.raise_for_status()
                except requests.exceptions.RequestException as e:
                    logging.debug(e)
                    show_popup(self, "Error", "Some error occurred! Could not delete project.")
            else:
                show_popup(self, "Error", "Entered project name did not match!")

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

    def create_local_project_file(self):
        with open_fs(self.data_dir) as mss_dir:
            rel_file_path = fs.path.join('local_mscolab_data', self.user['username'],
                                         self.active_project_name, 'mscolab_project.ftml')
            if mss_dir.exists(rel_file_path) is True:
                return
            mss_dir.makedirs(fs.path.dirname(rel_file_path))
            server_data = self.waypoints_model.get_xml_content()
            mss_dir.writetext(rel_file_path, server_data)

    def handle_work_locally_toggle(self):
        if self.workLocallyCheckBox.isChecked():
            if self.version_window is not None:
                self.version_window.close()
            self.create_local_project_file()
            self.local_ftml_file = fs.path.combine(self.data_dir,
                                                   fs.path.join('local_mscolab_data',
                                                                self.user['username'], self.active_project_name,
                                                                'mscolab_project.ftml'))
            self.helperTextLabel.setText(
                self.tr("Working On: Local File. Your changes are only available to you."
                        "To save your changes with everyone, use the \"Save to Server\" button."))
            self.save_ft.setEnabled(True)
            self.fetch_ft.setEnabled(True)
            self.versionHistoryBtn.setEnabled(False)
            self.reload_local_wp()

        else:
            self.local_ftml_file = None
            self.helperTextLabel.setText(
                self.tr("Working On: Shared File. All your changes will be shared with everyone."
                        "Turn on work locally to work on local flight track file"))
            self.save_ft.setEnabled(False)
            self.fetch_ft.setEnabled(False)
            if self.access_level == "admin" or self.access_level == "creator":
                self.versionHistoryBtn.setEnabled(True)
            self.waypoints_model = None
            self.load_wps_from_server()
        self.reload_view_windows()

    def authorize(self):
        for key, value in config_loader(dataset="MSC_login").items():
            if key not in constants.MSC_LOGIN_CACHE:
                constants.MSC_LOGIN_CACHE[key] = value
        auth = constants.MSC_LOGIN_CACHE.get(self.mscolab_server_url, (None, None))
        # get mscolab /token http auth credentials from cache
        emailid = self.emailid.text()
        password = self.password.text()
        data = {
            "email": emailid,
            "password": password
        }
        s = requests.Session()
        s.auth = (auth[0], auth[1])
        s.headers.update({'x-test': 'true'})
        url = self.mscolab_server_url + '/token'
        try:
            r = s.post(url, data=data)
        except requests.exceptions.ConnectionError as ex:
            logging.error("unexpected error: %s %s %s", type(ex), url, ex)
            # popup that Failed to establish a connection
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Failed to establish a new connection'
                                          f' to "{self.mscolab_server_url}". Try in a moment again.')
            return
        if r.status_code == 401:
            r = self.authenticate(data, r, url)
            if r.status_code == 200 and not r.text == "False":
                constants.MSC_LOGIN_CACHE[self.mscolab_server_url] = (auth[0], auth[1])
            else:
                self.error_dialog = QtWidgets.QErrorMessage()
                self.error_dialog.showMessage('Oh no, server authentication were incorrect.')
        if r.text == "False" or r.text == "Unauthorized Access":
            # popup that has wrong credentials
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Oh no, your credentials were incorrect.')
        else:
            # remove the login modal and put text there
            self.after_authorize(emailid, r)

    def after_authorize(self, emailid, r):
        _json = json.loads(r.text)
        self.token = _json["token"]
        self.user = _json["user"]
        self.label.setText(self.tr(f"Welcome, {self.user['username']}"))
        self.loggedInWidget.show()
        self.loginWidget.hide()
        self.add_projects()
        # create socket connection here
        self.conn = sc.ConnectionManager(self.token, user=self.user, mscolab_server_url=self.mscolab_server_url)
        self.conn.signal_reload.connect(self.reload_window)
        self.conn.signal_new_permission.connect(self.render_new_permission)
        self.conn.signal_update_permission.connect(self.handle_update_permission)
        self.conn.signal_revoke_permission.connect(self.handle_revoke_permission)
        self.conn.signal_project_deleted.connect(self.handle_project_deleted)
        # activate add project button here
        self.addProject.setEnabled(True)
        save_settings_qsettings('mscolab', self.settings)

    def add_projects(self):
        # add projects
        data = {
            "token": self.token
        }
        r = requests.get(self.mscolab_server_url + '/projects', data=data)
        _json = json.loads(r.text)
        self.projects = _json["projects"]
        self.add_projects_to_ui(self.projects)

    def get_recent_pid(self):
        """
        get most recent project's p_id
        """
        data = {
            "token": self.token
        }
        r = requests.get(self.mscolab_server_url + '/projects', data=data)
        _json = json.loads(r.text)
        projects = _json["projects"]
        return projects[-1]["p_id"]

    def get_recent_project(self):
        """
        get most recent project
        """
        data = {
            "token": self.token
        }
        r = requests.get(self.mscolab_server_url + '/projects', data=data)
        _json = json.loads(r.text)
        projects = _json["projects"]
        return projects[-1]

    def add_projects_to_ui(self, projects):
        logging.debug("adding projects to ui")
        self.listProjects.clear()
        selectedProject = None
        for project in projects:
            project_desc = f'{project["path"]} - {project["access_level"]}'
            widgetItem = QtWidgets.QListWidgetItem(project_desc, parent=self.listProjects)
            widgetItem.p_id = project["p_id"]
            widgetItem.access_level = project["access_level"]
            if widgetItem.p_id == self.active_pid:
                selectedProject = widgetItem
            self.listProjects.addItem(widgetItem)
        if selectedProject is not None:
            self.listProjects.setCurrentItem(selectedProject)
            self.listProjects.itemActivated.emit(selectedProject)
        self.listProjects.itemActivated.connect(self.set_active_pid)

    def force_close_view_windows(self):
        for window in self.active_windows[:]:
            window.handle_force_close()
        self.active_windows = []

    def set_active_pid(self, item):
        if item.p_id == self.active_pid:
            return
            # close all hanging window
        self.force_close_view_windows()
        self.close_external_windows()
        # Turn off work locally toggle
        self.workLocallyCheckBox.blockSignals(True)
        self.workLocallyCheckBox.setChecked(False)
        self.workLocallyCheckBox.blockSignals(False)
        self.save_ft.setEnabled(False)
        self.fetch_ft.setEnabled(False)

        # set active_pid here
        self.active_pid = item.p_id
        self.access_level = item.access_level
        self.active_project_name = item.text().split("-")[0].strip()
        self.waypoints_model = None
        # set active flightpath here
        self.load_wps_from_server()
        # enable project specific buttons
        self.helperTextLabel.setVisible(True)
        self.helperTextLabel.setText(self.tr("Working On: Shared File. All your changes will be shared with everyone."
                                             "Turn on work locally to work on local flight track file"))
        self.importBtn.setEnabled(True)
        self.exportBtn.setEnabled(True)
        self.topview.setEnabled(True)
        self.sideview.setEnabled(True)
        self.tableview.setEnabled(True)
        self.workLocallyCheckBox.setEnabled(True)

        if self.access_level == "viewer" or self.access_level == "collaborator":
            if self.access_level == "viewer":
                self.workLocallyCheckBox.setEnabled(False)
                self.importBtn.setEnabled(False)
                self.chatWindowBtn.setEnabled(False)
            else:
                self.chatWindowBtn.setEnabled(True)
            self.adminWindowBtn.setEnabled(False)
            self.versionHistoryBtn.setEnabled(False)
        else:
            self.adminWindowBtn.setEnabled(True)
            self.chatWindowBtn.setEnabled(True)
            self.versionHistoryBtn.setEnabled(True)
        if self.access_level == "creator":
            self.deleteProjectBtn.setEnabled(True)
        else:
            self.deleteProjectBtn.setEnabled(False)
        # change font style for selected
        font = QtGui.QFont()
        for i in range(self.listProjects.count()):
            self.listProjects.item(i).setFont(font)
        font.setBold(True)
        item.setFont(font)

    def reload_wps_from_server(self):
        if self.active_pid is None:
            return
        self.load_wps_from_server()
        self.reload_view_windows()

    def request_wps_from_server(self):
        data = {
            "token": self.token,
            "p_id": self.active_pid
        }
        r = requests.get(self.mscolab_server_url + '/get_project_by_id', data=data)
        xml_content = json.loads(r.text)["content"]
        return xml_content

    def load_wps_from_server(self):
        if self.workLocallyCheckBox.isChecked():
            return
        xml_content = self.request_wps_from_server()
        self.waypoints_model = ft.WaypointsTableModel(xml_content=xml_content)
        self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)

    def open_topview(self):
        # showing dummy info dialog
        if self.active_pid is None:
            return
        self.create_view_window("topview")

    def open_sideview(self):
        # showing dummy info dialog
        if self.active_pid is None:
            return
        self.create_view_window("sideview")

    def open_tableview(self):
        # showing dummy info dialog
        if self.active_pid is None:
            return
        self.create_view_window("tableview")

    def create_view_window(self, _type):
        for active_window in self.active_windows:
            if active_window.view_type == _type:
                active_window.raise_()
                active_window.activateWindow()
                return

        if _type == "topview":
            view_window = topview.MSSTopViewWindow(model=self.waypoints_model,
                                                   parent=self.listProjects,
                                                   _id=self.id_count)
            view_window.view_type = "topview"
        elif _type == "sideview":
            view_window = sideview.MSSSideViewWindow(model=self.waypoints_model,
                                                     parent=self.listProjects,
                                                     _id=self.id_count)
            view_window.view_type = "sideview"
        else:
            view_window = tableview.MSSTableViewWindow(model=self.waypoints_model,
                                                       parent=self.listProjects,
                                                       _id=self.id_count)
            view_window.view_type = "tableview"
        if self.access_level == "viewer":
            self.disable_navbar_action_buttons(_type, view_window)

        view_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        view_window.show()
        view_window.viewClosesId.connect(self.handle_view_close)
        self.active_windows.append(view_window)

        # increment id_count
        self.id_count += 1

    def disable_navbar_action_buttons(self, _type, view_window):
        """
        _type: view type (topview, sideview, tableview)
        view_window: PyQt view window

        function disables some control, used if access_level is not appropriate
        """
        if _type == "topview" or _type == "sideview":
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

    def enable_navbar_action_buttons(self, _type, view_window):
        """
        _type: view type (topview, sideview, tableview)
        view_window: PyQt view window

        function enables some control, used if access_level is appropriate
        """
        if _type == "topview" or _type == "sideview":
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

    def logout(self):
        self.clean_up_window()
        self.emailid.setEnabled(True)
        self.password.setEnabled(True)

    def delete_account(self):
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
        self.clean_up_window()

    def close_external_windows(self):
        if self.chat_window is not None:
            self.chat_window.close()
        if self.admin_window is not None:
            self.admin_window.close()
        if self.version_window is not None:
            self.version_window.close()

    def clean_up_window(self):
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
        # clear projects list here
        self.loggedInWidget.hide()
        self.loginWidget.show()
        # clear project listing
        self.listProjects.clear()
        # disconnect socket
        if self.conn is not None:
            self.conn.disconnect()
            self.conn = None
        # close all hanging window
        self.force_close_view_windows()
        self.close_external_windows()
        self.disable_action_buttons()

        # delete mscolab http_auth settings for the url
        if self.mscolab_server_url in self.settings["auth"].keys():
            del self.settings["auth"][self.mscolab_server_url]
        save_settings_qsettings('mscolab', self.settings)

    def save_wp_mscolab(self, comment=None):
        server_xml = self.request_wps_from_server()
        server_waypoints_model = ft.WaypointsTableModel(xml_content=server_xml)
        self.merge_dialog = MscolabMergeWaypointsDialog(self.waypoints_model, server_waypoints_model, parent=self)
        self.merge_dialog.saveBtn.setDisabled(True)
        if self.merge_dialog.exec_():
            xml_content = self.merge_dialog.get_values()
            if xml_content is not None:
                self.conn.save_file(self.token, self.active_pid, xml_content, comment=comment)
                self.waypoints_model = ft.WaypointsTableModel(xml_content=xml_content)
                self.waypoints_model.save_to_ftml(self.local_ftml_file)
                self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)
                self.reload_view_windows()
                show_popup(self, "Success", "New Waypoints Saved To Server!", icon=1)
        self.merge_dialog = None

    def handle_waypoints_changed(self):
        if self.workLocallyCheckBox.isChecked():
            self.waypoints_model.save_to_ftml(self.local_ftml_file)
        else:
            xml_content = self.waypoints_model.get_xml_content()
            self.conn.save_file(self.token, self.active_pid, xml_content, comment=None)

    def reload_view_windows(self):
        for window in self.active_windows:
            window.setFlightTrackModel(self.waypoints_model)
            if hasattr(window, 'mpl'):
                window.mpl.canvas.waypoints_interactor.redraw_figure()

    def reload_local_wp(self):
        self.waypoints_model = ft.WaypointsTableModel(filename=self.local_ftml_file, data_dir=self.data_dir)
        self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)
        self.reload_view_windows()

    def fetch_wp_mscolab(self):
        server_xml = self.request_wps_from_server()
        server_waypoints_model = ft.WaypointsTableModel(xml_content=server_xml)
        self.merge_dialog = MscolabMergeWaypointsDialog(self.waypoints_model, server_waypoints_model, True, self)
        self.merge_dialog.saveBtn.setDisabled(True)
        if self.merge_dialog.exec_():
            xml_content = self.merge_dialog.get_values()
            if xml_content is not None:
                self.waypoints_model = ft.WaypointsTableModel(xml_content=xml_content)
                self.waypoints_model.save_to_ftml(self.local_ftml_file)
                self.waypoints_model.dataChanged.connect(self.handle_waypoints_changed)
                self.reload_view_windows()
                show_popup(self, "Success", "New Waypoints Fetched To Local File!", icon=1)
        self.merge_dialog = None

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
            for i in range(self.listProjects.count()):
                item = self.listProjects.item(i)
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
            if self.access_level == "collaborator" or self.access_level == "viewer":
                self.adminWindowBtn.setEnabled(False)
                self.versionHistoryBtn.setEnabled(False)
                if self.admin_window is not None:
                    self.admin_window.close()
                if self.version_window is not None:
                    self.version_window.close()
            else:
                self.adminWindowBtn.setEnabled(True)
                self.versionHistoryBtn.setEnabled(True)

            if self.access_level == "viewer":
                self.chatWindowBtn.setEnabled(False)
                if self.chat_window is not None:
                    self.chat_window.close()
            else:
                self.chatWindowBtn.setEnabled(True)
            # update view window nav elements if open
            for window in self.active_windows:
                _type = window.view_type
                if self.access_level == "viewer":
                    self.disable_navbar_action_buttons(_type, window)
                else:
                    self.enable_navbar_action_buttons(_type, window)

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
            self.helperTextLabel.setVisible(False)
            self.force_close_view_windows()
            self.close_external_windows()
            self.disable_project_buttons()

        # Update project list
        remove_item = None
        for i in range(self.listProjects.count()):
            item = self.listProjects.item(i)
            if item.p_id == p_id:
                remove_item = item
        if remove_item is not None:
            logging.debug("remove_item: %s" % remove_item)
            self.listProjects.takeItem(self.listProjects.row(remove_item))
            return remove_item.text().split(' - ')[0]

    @QtCore.Slot(int, int)
    def handle_revoke_permission(self, p_id, u_id):
        if u_id == self.user["id"]:
            project_name = self.delete_project_from_list(p_id)
            show_popup(self, "Permission Revoked", f'Your access to project - "{project_name}" was revoked!', icon=1)

    @QtCore.Slot()
    def reload_windows_slot(self):
        self.reload_window(self.active_pid)

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
        _json = json.loads(r.text)
        if _json['user']['id'] == u_id:
            project = self.get_recent_project()
            project_desc = f'{project["path"]} - {project["access_level"]}'
            widgetItem = QtWidgets.QListWidgetItem(project_desc, parent=self.listProjects)
            widgetItem.p_id = project["p_id"]
            widgetItem.access_level = project["access_level"]
            self.listProjects.addItem(widgetItem)
        if self.chat_window is not None:
            self.chat_window.load_users()

    @QtCore.Slot(int)
    def handle_project_deleted(self, p_id):
        project_name = self.delete_project_from_list(p_id)
        show_popup(self, "Success", f'Project "{project_name}" was deleted!', icon=1)

    @QtCore.Slot(int)
    def reload_window(self, value):
        if self.active_pid != value or self.workLocallyCheckBox.isChecked():
            return
        self.reload_wps_from_server()

    @QtCore.Slot(int)
    def handle_view_close(self, value):
        logging.debug("removing stale window")
        for index, window in enumerate(self.active_windows):
            if window._id == value:
                del self.active_windows[index]

    def setIdentifier(self, identifier):
        self.identifier = identifier

    def closeEvent(self, event):
        if self.help_dialog is not None:
            self.help_dialog.close()
        self.clean_up_window()
        self.viewCloses.emit()


class MscolabMergeWaypointsDialog(QtWidgets.QDialog, ui_mscolab_merge_waypoints_dialog.Ui_MergeWaypointsDialog):
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


class MSCOLAB_AuthenticationDialog(QtWidgets.QDialog, ui_pw.Ui_WMSAuthenticationDialog):
    """Dialog to ask the user for username/password should this be
       required by a WMS server.
    """

    def __init__(self, parent=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        """
        super(MSCOLAB_AuthenticationDialog, self).__init__(parent)
        self.setupUi(self)

    def getAuthInfo(self):
        """
        Return the entered username and password.
        """
        return (self.leUsername.text(),
                self.lePassword.text())


class MscolabHelpDialog(QtWidgets.QDialog, msc_help_dialog.Ui_mscolabHelpDialog):

    viewCloses = QtCore.pyqtSignal(name="viewCloses")

    def __init__(self, parent=None):
        super(MscolabHelpDialog, self).__init__(parent)
        self.setupUi(self)
        self.okayBtn.clicked.connect(lambda: self.close())

    def closeEvent(self, event):
        self.viewCloses.emit()
