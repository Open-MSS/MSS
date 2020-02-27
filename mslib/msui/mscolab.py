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

from mslib.msui.mss_qt import QtGui, QtWidgets, QtCore, get_save_filename, get_open_filename
from mslib.msui.mss_qt import ui_mscolab_window as ui
from mslib.msui.mss_qt import ui_add_user_dialog as add_user_ui
from mslib.msui.mss_qt import ui_add_project_dialog as add_project_ui
from mslib.msui.mss_qt import ui_wms_password_dialog as ui_pw
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default
from mslib.msui.icons import icons
from mslib.msui import flighttrack as ft
from mslib.msui import topview, sideview, tableview
from mslib.msui import socket_control as sc
from mslib.msui import mscolab_project as mp
from mslib.utils import load_settings_qsettings, save_settings_qsettings
from mslib.utils import config_loader

import logging
import requests
from requests.auth import HTTPBasicAuth
import json
import fs
from fs import path, open_fs

MSCOLAB_URL_LIST = QtGui.QStandardItemModel()


def add_mscolab_urls(combo_box, url_list):
    combo_box_urls = [combo_box.itemText(_i) for _i in range(combo_box.count())]
    for url in (_url for _url in url_list if _url not in combo_box_urls):
        combo_box.addItem(url)


class MSSMscolabWindow(QtWidgets.QMainWindow, ui.Ui_MSSMscolabWindow):
    """PyQt window implementing mscolab window
    """
    name = "Mscolab"
    identifier = None
    viewCloses = QtCore.pyqtSignal(name="viewCloses")

    def __init__(self, parent=None, data_dir=mss_default.mss_dir, mscolab_server_url=mss_default.mscolab_server_url):
        """Set up user interface
        """
        super(MSSMscolabWindow, self).__init__(parent)
        self.setupUi(self)
        self.loggedInWidget.hide()
        self.setWindowIcon(QtGui.QIcon(icons('64x64')))
        # if token is None, not authorized, else authorized
        self.token = None
        self.loginButton.clicked.connect(self.authorize)
        self.logoutButton.clicked.connect(self.logout)
        self.topview.clicked.connect(self.open_topview)
        self.sideview.clicked.connect(self.open_sideview)
        self.tableview.clicked.connect(self.open_tableview)
        self.save_ft.clicked.connect(self.save_wp_mscolab)
        self.fetch_ft.clicked.connect(self.reload_wps_from_server)
        self.autoSave.stateChanged.connect(self.autosave_emit)
        self.projWindow.clicked.connect(self.open_project_window)
        self.addProject.clicked.connect(self.add_project_handler)
        self.addUser.clicked.connect(self.add_user_handler)
        self.export_2.clicked.connect(self.handle_export)
        self.connectMscolab.clicked.connect(self.connect_handler)
        self.disconnectMscolab.clicked.connect(self.disconnect_handler)

        # int to store active pid
        self.active_pid = None
        # storing access_level to save network call
        self.access_level = None
        # store active_flight_path here as object
        self.waypoints_model = None
        # store a reference of window in class
        self.open_windows_mscolab = []
        # connection object to interact with sockets
        self.conn = None
        # to store tempfile name
        self.fname_temp = ""
        # store window instances
        self.active_windows = []
        # assign ids to view-window
        self.id_count = 0
        # project window
        self.project_window = None
        self.disable_action_buttons()
        # set data dir, uri
        self.data_dir = data_dir
        self.mscolab_server_url = None
        # autosave status
        self.autosave_status = None

        # disabling login, add user button. they are enabled when url is connected
        self.loginButton.setEnabled(False)
        self.addUser.setEnabled(False)
        self.disconnectMscolab.setEnabled(False)

        self.url.setEditable(True)
        self.url.setModel(MSCOLAB_URL_LIST)
        # fill value of mscolab url from config
        default_MSCOLAB = config_loader(
            dataset="default_MSCOLAB", default=mss_default.default_MSCOLAB)
        add_mscolab_urls(self.url, default_MSCOLAB)

        self.emailid.setText(config_loader(dataset="MSCOLAB_mailid", default=""))
        self.password.setText(config_loader(dataset="MSCOLAB_password", default=""))

        # fill value of mscolab url if found in QSettings storage
        self.settings = load_settings_qsettings('mscolab', default_settings={'mscolab_url': None, 'auth': {}})
        if self.settings['mscolab_url'] is not None:
            add_mscolab_urls(self.url, [self.settings['mscolab_url']])

    def disconnect_handler(self):
        self.logout()
        # enable and disable right buttons
        self.disconnectMscolab.setEnabled(False)
        self.loginButton.setEnabled(False)
        self.addUser.setEnabled(False)
        self.connectMscolab.setEnabled(True)
        # set mscolab_server_url to None
        self.mscolab_server_url = None

    def show_info(self, text):
        self.error_dialog = QtWidgets.QErrorMessage()
        self.error_dialog.showMessage(text)

    def connect_handler(self):
        try:
            url = str(self.url.currentText())
            r = requests.get(url)
            if r.text == "Mscolab server":
                # delete mscolab http_auth settings for the url
                if self.mscolab_server_url in self.settings["auth"].keys():
                    del self.settings["auth"][self.mscolab_server_url]
                save_settings_qsettings('mscolab', self.settings)
                # assign new url to self.mscolab_server_url
                self.mscolab_server_url = url
                self.status.setText("Status: connected")
                # enable and disable right buttons
                self.loginButton.setEnabled(True)
                self.addUser.setEnabled(True)
                self.disconnectMscolab.setEnabled(True)
                self.connectMscolab.setEnabled(False)
                self.settings["mscolab_url"] = url
                save_settings_qsettings('mscolab', self.settings)
                return
        except requests.exceptions.ConnectionError:
            logging.debug("mscolab server isn't active")
        except requests.exceptions.InvalidSchema:
            logging.debug("invalid schema of url")
        except requests.exceptions.InvalidURL:
            logging.debug("invalid url")
        except Exception as e:
            logging.debug("Error {}".format(str(e)))
        # inform user that url is invalid
        self.show_info("Invalid url, please try again!")

    def handle_export(self):
        # ToDo when autosave mode gets upgraded, have to fetch from remote
        file_path = get_save_filename(
            self, "Save fight track", "", "Flight Track Files (*.ftml)")
        if file_path is not None:
            f_name = path.basename(file_path)
            f_dir = open_fs(path.dirname(file_path))
            temp_name = 'tempfile_mscolab.ftml'
            temp_dir = open_fs(self.data_dir)
            fs.copy.copy_file(temp_dir, temp_name, f_dir, f_name)

    def disable_action_buttons(self):
        # disable some buttons to be activated after successful login or project activate
        self.addProject.setEnabled(False)
        self.save_ft.setEnabled(False)
        self.fetch_ft.setEnabled(False)
        self.topview.setEnabled(False)
        self.sideview.setEnabled(False)
        self.tableview.setEnabled(False)
        self.projWindow.setEnabled(False)
        self.autoSave.setEnabled(False)
        self.export_2.setEnabled(False)

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
        # enable accepted only if path and description are not none
        self.add_proj_dialog.buttonBox.setEnabled(False)
        self.add_proj_dialog.path.textChanged.connect(self.check_and_enable_project_accept)
        self.add_proj_dialog.description.textChanged.connect(self.check_and_enable_project_accept)
        self.add_proj_dialog.browse.clicked.connect(self.set_exported_file)
        self.proj_diag.show()

    def check_and_enable_project_accept(self):
        if(self.add_proj_dialog.path.text() != "" and self.add_proj_dialog.description.toPlainText() != ""):
            self.add_proj_dialog.buttonBox.setEnabled(True)

    def set_exported_file(self):
        file_path = get_open_filename(
            self, "Open ftml file", "", "Flight Track Files (*.ftml)")
        if file_path is not None:
            f_name = path.basename(file_path)
            f_dir = open_fs(path.dirname(file_path))
            f_content = f_dir.readtext(f_name)
            self.add_proj_dialog.f_content = f_content
            self.add_proj_dialog.selectedFile.setText(f_name)

    def add_project(self):
        path = self.add_proj_dialog.path.text()
        description = self.add_proj_dialog.description.toPlainText()
        # ToDo if path and description is null alert user
        if not path:
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Path can\'t be empty')
            return
        elif not description:
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Description can\'t be empty')
            return

        data = {
            "token": self.token,
            "path": path,
            "description": description
        }
        if self.add_proj_dialog.f_content is not None:
            data["content"] = self.add_proj_dialog.f_content
        r = requests.post('{}/create_project'.format(self.mscolab_server_url), data=data)
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
            r = requests.post('{}/register'.format(self.mscolab_server_url), data=data)
            if r.text == "True":
                self.error_dialog = QtWidgets.QErrorMessage()
                self.error_dialog.showMessage('You are registered, you can now log in.')
            else:
                self.error_dialog = QtWidgets.QErrorMessage()
                self.error_dialog.showMessage('Oh no, your emailid is either invalid or taken')
        else:
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Oh no, your passwords don\'t match')

    def open_project_window(self):
        if self.active_pid is None:
            return
        if self.project_window is not None:
            return
        view_window = mp.MSColabProjectWindow(self.token, self.active_pid, self.conn,
                                              self.access_level, parent=self.projWindow,
                                              mscolab_server_url=self.mscolab_server_url)
        view_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        view_window.viewCloses.connect(self.close_project_window)
        view_window.reloadWindows.connect(self.reload_windows_slot)
        self.project_window = view_window
        self.project_window.show()

    def close_project_window(self):
        self.project_window = None

    def autosave_emit(self):
        # emit signal to server to enable or disable
        if self.active_pid is None:
            return

        # ToDo replace checkbox by text if normal user
        # ToDo save file as backup before loading what's in admin

        logging.debug(self.autoSave.isChecked())
        if self.autoSave.isChecked():
            self.conn.emit_autosave(self.token, self.active_pid, 1)
        else:
            self.conn.emit_autosave(self.token, self.active_pid, 0)

    def authorize(self):
        auth = ('', '')
        self.settings = load_settings_qsettings('mscolab', default_settings={'auth': {}})
        if (self.settings["auth"] is not None) and (self.mscolab_server_url in self.settings["auth"].keys()):
            auth = self.settings["auth"][self.mscolab_server_url]
        # get mscolab /token http auth credentials from cache
        emailid = self.emailid.text()
        password = self.password.text()
        data = {
            "email": emailid,
            "password": password
        }
        r = requests.post(self.mscolab_server_url + '/token', data=data, auth=HTTPBasicAuth(auth[0], auth[1]))
        if r.status_code == 401:
            dlg = MSCOLAB_AuthenticationDialog(parent=self)
            dlg.setModal(True)
            if dlg.exec_() == QtWidgets.QDialog.Accepted:
                username, password = dlg.getAuthInfo()
                self.settings["auth"][self.mscolab_server_url] = (username, password)
                # save to cache
                save_settings_qsettings('mscolab', self.settings)
        elif r.text == "False":
            # popup that has wrong credentials
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Oh no, your credentials were incorrect.')
            pass
        else:
            # remove the login modal and put text there
            print(r.text)
            _json = json.loads(r.text)
            self.token = _json["token"]
            self.user = _json["user"]
            self.label.setText("logged in as: " + _json["user"]["username"])
            self.loggedInWidget.show()
            self.loginWidget.hide()

            self.add_projects()

            # create socket connection here
            self.conn = sc.ConnectionManager(self.token, user=self.user, mscolab_server_url=self.mscolab_server_url)
            self.conn.signal_reload.connect(self.reload_window)
            self.conn.signal_autosave.connect(self.autosave_toggle)
            self.conn.signal_new_permission.connect(self.render_new_permission)
            self.conn.signal_update_permission.connect(self.handle_update_permission)
            # activate add project button here
            self.addProject.setEnabled(True)

    def add_projects(self):
        # add projects
        data = {
            "token": self.token
        }
        r = requests.get(self.mscolab_server_url + '/projects', data=data)
        _json = json.loads(r.text)
        projects = _json["projects"]
        self.add_projects_to_ui(projects)

    def get_recent_pid(self):
        """
        get most recent project's p_id
        # ToDo can be merged with get_recent_project
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
        for project in projects:
            project_desc = '{} - {}'.format(project['path'], project["access_level"])
            widgetItem = QtWidgets.QListWidgetItem(project_desc, parent=self.listProjects)
            widgetItem.p_id = project["p_id"]
            widgetItem.access_level = project["access_level"]
            self.listProjects.addItem(widgetItem)
        self.listProjects.itemActivated.connect(self.set_active_pid)

    def set_active_pid(self, item):
        # remove all windows if the current active_pid is not selected p_id
        if item.p_id != self.active_pid:
            # close all hanging window
            for window in self.active_windows:
                window.close()
            # show autosave button, and empty autosaveStatus
            self.autoSave.setVisible(True)
            self.autosaveStatus.setText("")
        # set active_pid here
        self.active_pid = item.p_id
        self.access_level = item.access_level
        # set active flightpath here
        self.load_wps_from_server()

        # enable project specific buttons
        self.save_ft.setEnabled(True)
        self.fetch_ft.setEnabled(True)
        self.topview.setEnabled(True)
        self.sideview.setEnabled(True)
        self.tableview.setEnabled(True)
        self.projWindow.setEnabled(True)
        self.autoSave.setEnabled(True)
        self.export_2.setEnabled(True)
        # configuring autosave button
        data = {
            "token": self.token,
            "p_id": self.active_pid
        }
        r = requests.get(self.mscolab_server_url + '/project_details', data=data)
        _json = json.loads(r.text)

        if _json["autosave"] is True:
            # one time activate
            self.autoSave.blockSignals(True)
            self.autoSave.setChecked(True)
            self.autoSave.blockSignals(False)
            self.save_ft.setEnabled(False)
            self.fetch_ft.setEnabled(False)
            # connect data change to handler
            self.waypoints_model.dataChanged.connect(self.handle_data_change)
            # enable autosave
            self.autosave_status = True
        else:
            self.autoSave.blockSignals(True)
            self.autoSave.setChecked(False)
            self.autoSave.blockSignals(False)
            self.autosave_status = False

        # hide autosave button if access_level is non-admin
        if self.access_level == "viewer" or self.access_level == "collaborator":
            self.autoSave.setVisible(False)
            # set autosave status
            if _json["autosave"]:
                self.autosaveStatus.setText("Autosave is enabled")
            else:
                self.autosaveStatus.setText("Autosave is disabled")
        else:
            self.autosaveStatus.setText("")
            self.autoSave.setVisible(True)

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
        for window in self.active_windows:
            # set active flight track
            window.setFlightTrackModel(self.waypoints_model)
            # redraw figure *only for canvas based window, not tableview*
            if hasattr(window, 'mpl'):
                window.mpl.canvas.waypoints_interactor.redraw_figure()

    def load_wps_from_server(self):
        data = {
            "token": self.token,
            "p_id": self.active_pid
        }
        r = requests.get(self.mscolab_server_url + '/get_project', data=data)
        ftml = json.loads(r.text)["content"]

        try:
            data_dir = open_fs(self.data_dir)
            data_dir.makedirs(self.user['username'])
        # ToDo Remove exception when deleting of a temporary directory is implemented.
        except fs.errors.DirectoryExists as e:
            logging.debug(e)
            data_dir = open_fs(self.data_dir)
        data_dir.writetext(path.combine(self.user['username'], 'tempfile_mscolab.ftml'), ftml)
        fname_temp = path.combine(self.data_dir, path.combine(self.user['username'], 'tempfile_mscolab.ftml'))
        self.fname_temp = fname_temp
        self.waypoints_model = ft.WaypointsTableModel(filename=fname_temp)

        # connect change events viewwindow HERE to emit file-save
        self.waypoints_model.dataChanged.connect(self.handle_data_change)

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
        view_window = None
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
        # check if autosave is enabled
        # ToDo for non-admins who will get autosave hidden
        self.w = QtWidgets.QWidget()
        if (not self.autoSave.isChecked()) and (self.active_pid is not None):
            qm = QtWidgets.QMessageBox
            reply = qm.question(self.w, 'Continue?',
                                'Autosave is disabled, save your changes locally before continuing!',
                                qm.Yes,
                                qm.No)
            if reply == QtWidgets.QMessageBox.No:
                return
        # delete token and show login widget-items
        self.token = None
        # delete active-project-id
        self.active_pid = None
        # delete active access_level
        self.access_level = None
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
        for window in self.active_windows:
            window.close()
        # close project window if active
        if self.project_window is not None:
            self.project_window.close()
        # show autosave button, and empty autosaveStatus
        self.autoSave.setVisible(True)
        self.autosaveStatus.setText("")

        self.disable_action_buttons()

        # delete mscolab http_auth settings for the url
        if self.mscolab_server_url in self.settings["auth"].keys():
            del self.settings["auth"][self.mscolab_server_url]
        save_settings_qsettings('mscolab', self.settings)

    def save_wp_mscolab(self, comment=None):
        if self.active_pid is not None:
            # to save to temp file
            xml_text = self.waypoints_model.save_to_mscolab(self.user["username"])
            # to emit to mscolab
            self.conn.save_file(self.token, self.active_pid, xml_text, comment=comment)

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
            for i in range(self.listProjects.count()):
                item = self.listProjects.item(i)
                if item.p_id == p_id:
                    desc = item.text().split('-')
                    desc[-1] = access_level
                    desc = ''.join(desc)
                    item.setText(desc)
                    item.p_id = p_id
                    item.access_level = access_level
            if p_id != self.active_pid:
                return
            self.access_level = access_level
            # update project window's control if open
            if self.project_window is not None:
                self.project_window.check_permission_and_render_control(self.access_level)
            # update view window nav elements if open
            for window in self.active_windows:
                _type = window.view_type
                if self.access_level == "viewer":
                    self.disable_navbar_action_buttons(_type, window)
                else:
                    self.enable_navbar_action_buttons(_type, window)
            # update autosave stats
            if self.access_level == "admin" or self.access_level == "creator":
                # enable autosave set it to checked status
                self.autoSave.setVisible(True)
                if self.autosave_status is True:
                    self.autoSave.blockSignals(True)
                    self.autoSave.setChecked(True)
                    self.autoSave.blockSignals(False)
                else:
                    self.autoSave.blockSignals(True)
                    self.autoSave.setChecked(False)
                    self.autoSave.blockSignals(False)
                self.autosaveStatus.setText("")
            else:
                # disable autosave, set status text
                self.autoSave.setVisible(False)
                if self.autosave_status is True:
                    self.autosaveStatus.setText("Autosave is enabled!")
                else:
                    self.autosaveStatus.setText("Autosave is enabled!")

        # update project window if open
        if self.project_window is not None:
            self.project_window.load_users()

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
            project_desc = '{} - {}'.format(project['path'], project["access_level"])
            widgetItem = QtWidgets.QListWidgetItem(project_desc, parent=self.listProjects)
            widgetItem.p_id = project["p_id"]
            widgetItem.access_level = project["access_level"]
            self.listProjects.addItem(widgetItem)
        if self.project_window is not None:
            self.project_window.load_users()

    @QtCore.Slot(int)
    def reload_window(self, value):
        if self.active_pid != value or self.autosave_status is False:
            return
        logging.debug("reloading window")
        # ask the user in dialog if he wants the change, only for autosave mode
        # toDo preview of the change
        self.reload_wps_from_server()
        # reload changes in project window if it exists
        if self.project_window is not None:
            self.project_window.load_all_changes()
            self.project_window.load_all_messages()

    @QtCore.Slot(int)
    def handle_view_close(self, value):
        logging.debug("removing stale window")
        for index, window in enumerate(self.active_windows):
            if window._id == value:
                del self.active_windows[index]

    @QtCore.Slot(QtCore.QModelIndex, QtCore.QModelIndex)
    def handle_data_change(self, index1, index2):
        # if autosave isn't checked, don't save. (in future, this might be hidden # ToDo)
        if self.autoSave.isChecked():
            self.save_wp_mscolab()

    @QtCore.Slot(int, int)
    def autosave_toggle(self, enable, p_id):
        # return if it's for a different process
        if p_id != self.active_pid:
            return
        if enable:
            # enable autosave, disable save button
            self.autosave_status = True
            self.save_ft.setEnabled(False)
            self.fetch_ft.setEnabled(False)
            # reload window
            self.reload_wps_from_server()
            self.waypoints_model.dataChanged.connect(self.handle_data_change)
            self.autosaveStatus.setText("Autosave is enabled")

        else:
            self.autosave_status = False
            # disable autosave, enable save button
            self.save_ft.setEnabled(True)
            self.fetch_ft.setEnabled(True)
            # connect change events viewwindow HERE to emit file-save
            # ToDo - remove hack to disconnect this handler
            self.waypoints_model.dataChanged.disconnect(self.handle_data_change)
            self.autosaveStatus.setText("Autosave is disabled")

    def setIdentifier(self, identifier):
        self.identifier = identifier

    def closeEvent(self, event):
        if self.conn:
            self.conn.disconnect()


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
        """Return the entered username and password.
        """
        return (self.leUsername.text(),
                self.lePassword.text())
