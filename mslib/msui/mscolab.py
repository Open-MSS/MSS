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

from mslib.msui.mss_qt import QtGui, QtWidgets, QtCore
from mslib.msui.mss_qt import ui_mscolab_window as ui
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default
from mslib.msui.icons import icons
from mslib.msui import flighttrack as ft
from mslib.msui import topview, sideview, tableview
from mslib.msui import socket_control as sc
from mslib.msui import mscolab_project as mp

import logging
import requests
import json
import fs


class MSSMscolabWindow(QtWidgets.QMainWindow, ui.Ui_MSSMscolabWindow):
    """PyQt window implementing mscolab window
    """
    name = "Mscolab"
    identifier = None
    viewCloses = QtCore.pyqtSignal(name="viewCloses")

    def __init__(self, parent=None):
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

        # int to store active pid
        self.active_pid = None
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

    def open_project_window(self):
        if self.active_pid is None:
            return
        view_window = mp.MSColabProjectWindow(self.token, self.active_pid, self.conn, parent=self.projWindow)
        view_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        view_window.viewCloses.connect(self.close_project_window)
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
        emailid = self.emailid.text()
        password = self.password.text()
        data = {
            "email": emailid,
            "password": password
        }
        r = requests.post(mss_default.mscolab_server_url + '/token', data=data)
        if r.text == "False":
            # popup that has wrong credentials
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Oh no, your credentials were incorrect.')
            pass
        else:
            # remove the login modal and put text there
            _json = json.loads(r.text)
            self.token = _json["token"]
            self.user = _json["user"]
            self.label.setText("logged in as: " + _json["user"]["username"])
            self.loggedInWidget.show()
            self.loginWidget.hide()

            # add projects
            data = {
                "token": self.token
            }
            r = requests.get(mss_default.mscolab_server_url + '/projects', data=data)
            _json = json.loads(r.text)
            projects = _json["projects"]
            self.add_projects_to_ui(projects)

            # create socket connection here
            self.conn = sc.ConnectionManager(self.token, user=self.user)
            self.conn.signal_reload.connect(self.reload_window)
            self.conn.signal_autosave.connect(self.autosave_toggle)

    def add_projects_to_ui(self, projects):
        logging.debug("adding projects to ui")
        for project in projects:
            project_desc = '{} - {}'.format(project['path'], project["access_level"])
            widgetItem = QtWidgets.QListWidgetItem(project_desc, parent=self.listProjects)
            widgetItem.p_id = project["p_id"]
            self.listProjects.addItem(widgetItem)
        self.listProjects.itemActivated.connect(self.set_active_pid)

    def set_active_pid(self, item):
        # set active_pid here
        self.active_pid = item.p_id

        # set active flightpath here
        self.load_wps_from_server()
        # configuring autosave button
        data = {
            "token": self.token,
            "p_id": self.active_pid
        }
        r = requests.get(mss_default.mscolab_server_url + '/project_details', data=data)
        _json = json.loads(r.text)
        if _json["autosave"] is True:
            # one time activate
            self.autoSave.blockSignals(True)
            self.autoSave.setChecked(True)
            self.autoSave.blockSignals(False)
            self.save_ft.setEnabled(False)
            self.fetch_ft.setEnabled(False)
        # change font style for selected
        font = QtGui.QFont()
        for i in range(self.listProjects.count()):
            self.listProjects.item(i).setFont(font)
        font.setBold(True)
        item.setFont(font)

    def reload_wps_from_server(self):
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
        r = requests.get(mss_default.mscolab_server_url + '/get_project', data=data)
        ftml = json.loads(r.text)["content"]
        data_dir = fs.open_fs(mss_default.mss_dir)
        data_dir.writetext('tempfile_mscolab.ftml', ftml)
        fname_temp = fs.path.combine(mss_default.mss_dir, 'tempfile_mscolab.ftml')
        self.fname_temp = fname_temp
        self.waypoints_model = ft.WaypointsTableModel(filename=fname_temp)

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
        elif _type == "sideview":
            view_window = sideview.MSSSideViewWindow(model=self.waypoints_model,
                                                     parent=self.listProjects,
                                                     _id=self.id_count)
        else:
            view_window = tableview.MSSTableViewWindow(model=self.waypoints_model,
                                                       parent=self.listProjects,
                                                       _id=self.id_count)
        view_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        view_window.show()
        view_window.viewClosesId.connect(self.handle_view_close)
        self.active_windows.append(view_window)

        # increment id_count
        self.id_count += 1

    def logout(self):
        # delete token and show login widget-items
        self.token = None
        # delete active-project-id
        self.active_pid = None
        # clear projects list here
        self.loggedInWidget.hide()
        self.loginWidget.show()
        # clear project listing
        self.listProjects.clear()
        # disconnect socket
        if self.conn is not None:
            self.conn.disconnect()
            self.conn = None

    def save_wp_mscolab(self, comment=None):
        if self.active_pid is not None:
            # to save to temp file
            xml_text = self.waypoints_model.save_to_mscolab()
            # to emit to mscolab
            self.conn.save_file(self.token, self.active_pid, xml_text, comment=comment)

    @QtCore.Slot(int)
    def reload_window(self, value):
        if self.active_pid != value:
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
        if self.autoSave.isChecked():
            self.save_wp_mscolab()

    @QtCore.Slot(int, int)
    def autosave_toggle(self, enable, p_id):
        # return if it's for a different process
        if p_id != self.active_pid:
            return
        if enable:
            # enable autosave, disable save button
            self.save_ft.setEnabled(False)
            self.fetch_ft.setEnabled(False)
            # reload window
            self.reload_wps_from_server()
            # connect change events viewwindow HERE to emit file-save
            self.waypoints_model.dataChanged.connect(self.handle_data_change)
        else:
            # disable autosave, enable save button
            self.save_ft.setEnabled(True)
            self.fetch_ft.setEnabled(True)
            # connect change events viewwindow HERE to emit file-save
            # ToDo - remove hack to disconnect this handler
            self.waypoints_model.dataChanged.connect(self.handle_data_change)
            self.waypoints_model.dataChanged.disconnect()

    def setIdentifier(self, identifier):
        self.identifier = identifier

    def closeEvent(self, event):
        if self.conn:
            self.conn.disconnect()
