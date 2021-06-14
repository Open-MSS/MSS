#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    mslib.msui.mss_pyui
    ~~~~~~~~~~~~~~~~~~~

    Mission Support System Python/Qt User Interface
    Main window of the user interface application. Manages view and tool windows
    (the user can open multiple windows) and provides functionality to open, save,
    and switch between flight tracks.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2021 by the mss team, see AUTHORS.
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

import argparse
import copy
import functools
import hashlib
import importlib
import logging
import os
import platform
import re
import requests
import shutil
import sys
import types
import fs
import json
from fs import open_fs
from werkzeug.urls import url_join

from mslib import __version__
from mslib.msui.mss_qt import ui_mainwindow as ui
from mslib.msui.mss_qt import ui_mainwindow_new as ui_new
from mslib.msui.mss_qt import ui_mscolab_connect_window as ui_conn
from mslib.msui.mss_qt import ui_about_dialog as ui_ab
from mslib.msui.mss_qt import ui_shortcuts as ui_sh
from mslib.msui import flighttrack as ft
from mslib.msui import tableview, topview, sideview, linearview
from mslib.msui import editor
from mslib.msui import constants
from mslib.msui import wms_control
from mslib.msui import mscolab
from mslib.msui.updater import UpdaterUI
from mslib.utils import config_loader, setup_logging, Worker, Updater
from mslib.plugins.io.csv import load_from_csv, save_to_csv
from mslib.msui.icons import icons, python_powered
from mslib.msui.mss_qt import get_open_filename, get_save_filename
from PyQt5 import QtGui, QtCore, QtWidgets

from mslib.msui import mscolab_project as mp
from mslib.msui import mscolab_admin_window as maw
from mslib.msui import mscolab_version_history as mvh
from mslib.msui import socket_control as sc
from mslib.utils import load_settings_qsettings, save_settings_qsettings, dropEvent, dragEnterEvent, show_popup

# Add config path to PYTHONPATH so plugins located there may be found
sys.path.append(constants.MSS_CONFIG_PATH)


def clean_string(string):
    return re.sub(r'\W|^(?=\d)', '_', string)


class QActiveViewsListWidgetItem(QtWidgets.QListWidgetItem):
    """Subclass of QListWidgetItem, represents an open view in the list of
       open views. Keeps a reference to the view instance (i.e. the window) it
       represents in the list of open views.
    """

    # Class variable to assign a unique ID to each view.
    opened_views = 0

    def __init__(self, view_window, parent=None, viewsChanged=None,
                 type=QtWidgets.QListWidgetItem.UserType):
        """Add ID number to the title of the corresponding view window.
        """
        QActiveViewsListWidgetItem.opened_views += 1
        view_name = f"({QActiveViewsListWidgetItem.opened_views:d}) {view_window.name}"
        super(QActiveViewsListWidgetItem, self).__init__(view_name, parent, type)

        view_window.setWindowTitle(f"({QActiveViewsListWidgetItem.opened_views:d}) {view_window.windowTitle()} - "
                                   f"{view_window.waypoints_model.name}")
        view_window.setIdentifier(view_name)
        self.window = view_window
        self.parent = parent
        self.viewsChanged = viewsChanged

    def view_destroyed(self):
        """Slot that removes this QListWidgetItem from the parent (the
           QListWidget) if the corresponding view has been deleted.
        """
        if self.parent is not None:
            self.parent.takeItem(self.parent.row(self))
        if self.viewsChanged is not None:
            self.viewsChanged.emit()


class QFlightTrackListWidgetItem(QtWidgets.QListWidgetItem):
    """Subclass of QListWidgetItem, represents a flight track in the list of
       open flight tracks. Keeps a reference to the flight track instance
       (i.e. the instance of WaypointsTableModel).
    """

    def __init__(self, flighttrack_model, parent=None,
                 type=QtWidgets.QListWidgetItem.UserType):
        """Item class for the list widget that accommodates the open flight
           tracks.

        Arguments:
        flighttrack_model -- instance of a flight track model that is
                             associated with the item
        parent -- pointer to the QListWidgetItem that accommodates this item.
                  If not None, the itemChanged() signal of the parent is
                  connected to the nameChanged() slot of this class, reacting
                  to name changes of the item.
        """
        view_name = flighttrack_model.name
        super(QFlightTrackListWidgetItem, self).__init__(
            view_name, parent, type)

        self.parent = parent
        self.flighttrack_model = flighttrack_model


class MSS_ShortcutsDialog(QtWidgets.QDialog, ui_sh.Ui_ShortcutsDialog):
    """
    Dialog showing shortcuts for all currently open windows
    """

    def __init__(self):
        super(MSS_ShortcutsDialog, self).__init__(QtWidgets.QApplication.activeWindow())
        self.setupUi(self)
        self.current_shortcuts = self.get_shortcuts()
        self.fill_list()

    def fill_list(self):
        """
        Fills the treeWidget with all relevant windows as top level items and their shortcuts as children
        """
        for widget in self.current_shortcuts:
            name = widget.window().windowTitle()
            if len(name) == 0 or widget.window().isHidden():
                continue
            header = QtWidgets.QTreeWidgetItem(self.treeWidget)
            header.setText(0, name)
            if widget.window() == self.parent():
                header.setExpanded(True)
                header.setSelected(True)
                self.treeWidget.setCurrentItem(header)
            for description, shortcut in self.current_shortcuts[widget].items():
                item = QtWidgets.QTreeWidgetItem(header)
                item.setText(0, f"{description}: {shortcut}")
                header.addChild(item)

    def get_shortcuts(self):
        """
        Iterates through all top level widgets and puts their shortcuts in a dictionary
        """
        shortcuts = {}
        for qobject in QtWidgets.QApplication.topLevelWidgets():
            actions = [(qobject.window(), "Show Current Shortcuts", "Alt+S")]
            actions.extend([
                (action.parent().window(), action.toolTip(), ",".join(
                    [shortcut.toString() for shortcut in action.shortcuts()]))
                for action in qobject.findChildren(QtWidgets.QAction) if len(action.shortcuts()) > 0])
            actions.extend([(shortcut.parentWidget().window(), shortcut.whatsThis(), shortcut.key().toString())
                            for shortcut in qobject.findChildren(QtWidgets.QShortcut)])
            actions.extend([(button.window(), button.toolTip(), button.shortcut().toString())
                            for button in qobject.findChildren(QtWidgets.QAbstractButton) if button.shortcut()])
            for item in actions:
                if item[0] not in shortcuts:
                    shortcuts[item[0]] = {}
                shortcuts[item[0]][item[1].replace(f"({item[2]})", "").strip()] = item[2]

        return shortcuts


class MSS_AboutDialog(QtWidgets.QDialog, ui_ab.Ui_AboutMSUIDialog):
    """Dialog showing information about MSUI. Most of the displayed text is
       defined in the QtDesigner file.
    """

    def __init__(self, parent=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        """
        super(MSS_AboutDialog, self).__init__(parent)
        self.setupUi(self)
        self.lblVersion.setText("Version: {}".format(__version__))
        self.milestone_url = f'https://github.com/Open-MSS/MSS/issues?q=is%3Aclosed+milestone%3A{__version__[:-1]}'
        self.lblChanges.setText(f'<a href="{self.milestone_url}">New Features and Changes</a>')
        blub = QtGui.QPixmap(python_powered())
        self.lblPython.setPixmap(blub)


class MSColab_ConnectWindow(QtWidgets.QMainWindow, ui_conn.Ui_MSColabConnectWindow):
    """MSColab connect window class. Provides user interface elements to connect/disconnect,
       login, add new user to an MSColab Server. Also implements HTTP Server Authentication prompt.
    """

    def __init__(self, parent=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        """
        super(MSColab_ConnectWindow, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent

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

    def page_switched(self, index):
        # clear all text in all input
        self.loginEmailLe.setText("")
        self.loginPasswordLe.setText("")

        self.newUsernameLe.setText("")
        self.newEmailLe.setText("")
        self.newPasswordLe.setText("")
        self.newConfirmPasswordLe.setText("")

        self.wmsUsernameLe.setText("")
        self.wmsPasswordLe.setText("")

        if index == 2:
            self.connectBtn.setEnabled(False)
        else:
            self.connectBtn.setEnabled(True)
        self.resize(self.sizeHint())

        # self.prev_index = index

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

    def authenticate(self, data, r, url):
        if r.status_code == 401:
            username, password = self.wmsUsernameLe.text(), self.wmsPasswordLe.text()
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
            # popup that Failed to establish a connection
            show_popup(self, "Error", 'Failed to establish a new connection'
                                        f' to "{self.mscolab_server_url}". Try in a moment again.')
            self.disconnect_handler()
            return

        if r.text == "False":
            # popup that has wrong credentials
            show_popup(self, "Error", "Oh no, your credentials were incorrect.")
        elif r.text == "Unauthorized Access":
            # Server auth required for logging in
            self.login_data = [data, r, url, auth]
            self.connectBtn.setEnabled(False)
            self.stackedWidget.setCurrentWidget(self.wmsAuthPage)
            self.wmsBb.accepted.connect(self.login_server_auth)
            self.wmsBb.rejected.connect(lambda: self.stackedWidget.setCurrentWidget(self.loginPage))
        else:
            self.parent.after_login(emailid, self.mscolab_server_url, r)

    def login_server_auth(self):
        data, r, url, auth = self.login_data
        emailid = data['email']
        if r.status_code == 401:
            r = self.authenticate(data, r, url)
            if r.status_code == 200 and r.text not in ["False", "Unauthorized Access"]:
                constants.MSC_LOGIN_CACHE[self.mscolab_server_url] = (auth[0], auth[1])
                self.parent.after_login(emailid, self.mscolab_server_url, r)
            else:
                show_popup(self, "Error", "Oh no, server authentication were incorrect.")
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
            show_popup(self, "Error", "Oh no, your passwords don\'t match")
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
            # popup that Failed to establish a connection
            show_popup(self, "Error", 'Failed to establish a new connection'
                                        f' to "{self.mscolab_server_url}". Try in a moment again.')
            self.disconnect_handler()
            return

        if r.status_code == 201:
            show_popup(self, "Success", "You are registered, you can now log in.", icon=1)
            self.stackedWidget.setCurrentWidget(self.loginPage)
        elif r.status_code == 401:
            self.newuser_data = [data, r, url]
            self.stackedWidget.setCurrentWidget(self.wmsAuthPage)
            self.wmsBb.accepted.connect(self.newuser_server_auth)
            self.wmsBb.rejected.connect(lambda: self.stackedWidget.setCurrentWidget(self.newuserPage))
        else:
            error_msg = json.loads(r.text)["message"]
            show_popup(self, "Error", error_msg)

    def newuser_server_auth(self):
        data, r, url = self.newuser_data
        r = self.authenticate(data, r, url)
        if r.status_code == 201:
            constants.MSC_LOGIN_CACHE[self.mscolab_server_url] = (data['username'], data['password'])
            show_popup(self, "Success", "You are registered, you can now log in.", icon=1)
            self.stackedWidget.setCurrentWidget(self.loginPage)
        else:
            show_popup(self, "Error", "Oh no, server authentication were incorrect.")
            self.stackedWidget.setCurrentWidget(self.newuserPage)

#     def closeEvent(self, event):
#         event.accept()


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


class MSSMainWindow(QtWidgets.QMainWindow, ui_new.Ui_MSSMainWindow_new):
    """MSUI new main window class. Provides user interface elements for managing
       flight tracks and views.
    """

    viewsChanged = QtCore.pyqtSignal(name="viewsChanged")

    def __init__(self, *args):
        super(MSSMainWindow, self).__init__(*args)
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(icons('32x32')))
        # This code is required in Windows 7 to use the icon set by setWindowIcon in taskbar
        # instead of the default Icon of python/pythonw
        try:
            import ctypes
            myappid = f"mss.mss_pyui.{__version__}"  # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except (ImportError, AttributeError) as error:
            logging.debug("AttributeError, ImportError Exception %s", error)

        self.tabWidget.setCurrentIndex(0)
        self.config_editor = None

        # Setting up Local Tab
        self.new_flight_track_counter = 0

        # Reference to the flight track that is currently displayed in the views.
        self.active_flight_track = None
        self.last_save_directory = config_loader(dataset="data_dir")

        # self.newFlightTrackBtn.clicked.connect(functools.partial(self.create_new_flight_track, None, None))

        # Flight Tracks.
        # self.listFlightTracks.itemActivated.connect(self.activate_flight_track)

        # Views.
        # self.listViews.itemActivated.connect(self.activate_sub_window)

        # Setting up MSColab Tab
        self.connectBtn.clicked.connect(self.open_connect_window)

        # hide online widgets
        self.usernameLabel.hide()
        self.userOptionsTb.hide()
        self.addProjectBtn.hide()
        self.workingStatusLabel.hide()
        self.workLocallyCheckbox.hide()
        self.sandboxOptionsCb.hide()
        self.projectOptionsCb.hide()

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
        # if data_dir is None:
        #     self.data_dir = config_loader(dataset="mss_dir")
        # else:
        #     self.data_dir = data_dir
        # self.create_dir()
        # self.export_plugins = self.add_plugins(dataset="export_plugins")
        # self.import_plugins = self.add_plugins(dataset="import_plugins")
        self.mscolab_server_url = None

        # fill value of mscolab url if found in QSettings storage
        self.settings = load_settings_qsettings(
            'mscolab', default_settings={'auth': {}, 'server_settings': {}})

    def create_view_local(self, index):
        """Method called when the user selects a new view to be opened. Creates
           a new instance of the view and adds a QActiveViewsListWidgetItem to
           the list of open views (self.listViews).
        """
        # Ignore create view option.
        if index == 0:
            return

        self.createViewCb.setCurrentIndex(0)
        layout = config_loader(dataset="layout")
        view_window = None
        if index == 1:
            # Top view.
            view_window = topview.MSSTopViewWindow(model=self.active_flight_track)
            view_window.mpl.resize(layout['topview'][0], layout['topview'][1])
            if layout["immutable"]:
                view_window.mpl.setFixedSize(layout['topview'][0], layout['topview'][1])
        elif index == 2:
            # Side view.
            view_window = sideview.MSSSideViewWindow(model=self.active_flight_track)
            view_window.mpl.resize(layout['sideview'][0], layout['sideview'][1])
            if layout["immutable"]:
                view_window.mpl.setFixedSize(layout['sideview'][0], layout['sideview'][1])
        elif index == 3:
            # Table view.
            view_window = tableview.MSSTableViewWindow(model=self.active_flight_track)
            view_window.centralwidget.resize(layout['tableview'][0], layout['tableview'][1])
        elif index == 4:
            # Linear view.
            view_window = linearview.MSSLinearViewWindow(model=self.active_flight_track)
            view_window.mpl.resize(layout['linearview'][0], layout['linearview'][1])
            if layout["immutable"]:
                view_window.mpl.setFixedSize(layout['linearview'][0], layout['linearview'][1])

        if view_window is not None:
            # Make sure view window will be deleted after being closed, not
            # just hidden (cf. Chapter 5 in PyQt4).
            view_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            # Open as a non-modal window.
            view_window.show()
            # Add an entry referencing the new view to the list of views.
            listitem = QActiveViewsListWidgetItem(view_window, self.listViews, self.viewsChanged)
            view_window.viewCloses.connect(listitem.view_destroyed)
            self.listViews.setCurrentItem(listitem)
            self.viewsChanged.emit()

    def open_connect_window(self):
        self.connect_window = MSColab_ConnectWindow(parent=self)
        self.connect_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.connect_window.setWindowTitle("Connect to MSColab")
        self.connect_window.show()

    def after_login(self, emailid, url, r):
        self.connect_window.close()
        _json = json.loads(r.text)
        self.token = _json["token"]
        self.user = _json["user"]
        self.mscolab_server_url = url

        self.connectBtn.hide()
        # display connection status
        self.mscStatusLabel.setText(self.tr(f"Connected to MSColab Server at {self.mscolab_server_url}"))
        # display username beside useroptions toolbutton
        self.usernameLabel.setText(self.tr(f"{self.user['username']}"))
        self.usernameLabel.show()
        # set up user menu and add to toolbutton
        self.user_menu = QtWidgets.QMenu()
        self.user_menu.addAction("Profile")
        self.user_menu.addAction("Help")
        self.user_menu.addAction("Logout")
        self.userOptionsTb.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.userOptionsTb.setMenu(self.user_menu)
        self.userOptionsTb.show()
        # self.pixmap = QtGui.QPixmap("msui_redesign/gravatar.jpg")
        # self.icon = QtGui.QIcon()
        # self.icon.addPixmap(self.pixmap, QtGui.QIcon.Normal, QtGui.QIcon.Off)
        # self.userOptionsTb.setIcon(self.icon)

        self.add_projects_to_ui()
        self.tabWidget.setCurrentIndex(1)

        # # create socket connection here
        # self.conn = sc.ConnectionManager(self.token, user=self.user, mscolab_server_url=self.mscolab_server_url)
        # self.conn.signal_reload.connect(self.reload_window)
        # self.conn.signal_new_permission.connect(self.render_new_permission)
        # self.conn.signal_update_permission.connect(self.handle_update_permission)
        # self.conn.signal_revoke_permission.connect(self.handle_revoke_permission)
        # self.conn.signal_project_deleted.connect(self.handle_project_deleted)

        # activate add project button here
        self.addProjectBtn.show()
        # save_settings_qsettings('mscolab', self.settings)

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
            self.listProjectsMSC.clear()
            selectedProject = None
            for project in projects:
                project_desc = f'{project["path"]} - {project["access_level"]}'
                widgetItem = QtWidgets.QListWidgetItem(project_desc, parent=self.listProjectsMSC)
                widgetItem.p_id = project["p_id"]
                widgetItem.access_level = project["access_level"]
                if widgetItem.p_id == self.active_pid:
                    selectedProject = widgetItem
                self.listProjectsMSC.addItem(widgetItem)
            if selectedProject is not None:
                self.listProjectsMSC.setCurrentItem(selectedProject)
                self.listProjectsMSC.itemActivated.emit(selectedProject)
            self.listProjectsMSC.itemActivated.connect(self.set_active_pid)
        else:
            show_popup(self, "Error", "Session expired, new login required")
            self.logout()

    @verify_user_token
    def set_active_pid(self, item):
        if item.p_id == self.active_pid:
            return
        # # close all hanging window
        # self.force_close_view_windows()
        # self.close_external_windows()
        # # Turn off work locally toggle
        self.workLocallyCheckbox.blockSignals(True)
        self.workLocallyCheckbox.setChecked(False)
        self.workLocallyCheckbox.blockSignals(False)
        self.sandboxOptionsCb.hide()

        # set active_pid here
        self.active_pid = item.p_id
        self.access_level = item.access_level
        self.active_project_name = item.text().split("-")[0].strip()
        self.waypoints_model = None

        # # set active flightpath here
        # self.load_wps_from_server()
        # enable project specific buttons
        self.workingStatusLabel.show()
        self.workingStatusLabel.setText(self.tr("Working On: Shared File."
                                             "All your changes will be shared with everyone."
                                             "Turn on work locally to work on local flight track file"))
        # enable access level specific buttons
        self.show_project_options()

        # change font style for selected
        font = QtGui.QFont()
        for i in range(self.listProjectsMSC.count()):
            self.listProjectsMSC.item(i).setFont(font)
        font.setBold(True)
        item.setFont(font)

    def reload_wps_from_server(self):
        if self.active_pid is None:
            return
        self.load_wps_from_server()
        self.reload_view_windows()

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

    def show_project_options(self):
        project_opt_list = ['Project Options']
        allow_version_access = self.access_level in ["creator", "admin", "collaborator"]
        if allow_version_access:
            project_opt_list.extend(['Chat', 'Version History'])
            self.workLocallyCheckbox.show()

        allow_version_access = self.access_level in ["creator", "admin"]
        if allow_version_access:
            project_opt_list.extend(['Manage Users'])

        allow_version_access = self.access_level in ["creator"]
        if allow_version_access:
            project_opt_list.extend(['Share Project', 'Delete Project'])

        self.projectOptionsCb.clear()
        self.projectOptionsCb.addItems(project_opt_list)
        self.projectOptionsCb.show()

    def hide_project_options(self):
        self.workingStatusLabel.hide()
        self.projectOptionsCb.hide()
        self.workLocallyCheckbox.hide()
        self.sandboxOptionsCb.hide()

    @verify_user_token
    def create_view_msc(self, index):
        if index == 0 or self.active_pid is None:
            return

        _type = ["topview", "sideview", "tableview", "linearview"][index-1]
        for active_window in self.active_windows:
            if active_window.view_type == _type:
                active_window.raise_()
                active_window.activateWindow()
                return

        self.waypoints_model.name = self.active_project_name
        if _type == "topview":
            view_window = topview.MSSTopViewWindow(model=self.waypoints_model,
                                                   parent=self.listProjectsMSC,
                                                   _id=self.id_count)
        elif _type == "sideview":
            view_window = sideview.MSSSideViewWindow(model=self.waypoints_model,
                                                     parent=self.listProjectsMSC,
                                                     _id=self.id_count)
        elif _type == "tableview":
            view_window = tableview.MSSTableViewWindow(model=self.waypoints_model,
                                                       parent=self.listProjectsMSC,
                                                       _id=self.id_count)
        else:
            view_window = linearview.MSSLinearViewWindow(model=self.waypoints_model,
                                                         parent=self.listProjectsMSC,
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


# class MSSMainWindow(QtWidgets.QMainWindow, ui.Ui_MSSMainWindow):
#     """MSUI main window class. Provides user interface elements for managing
#        flight tracks and views.
#     """

#     viewsChanged = QtCore.pyqtSignal(name="viewsChanged")

#     def __init__(self, *args):
#         super(MSSMainWindow, self).__init__(*args)
#         self.setupUi(self)
#         self.setWindowIcon(QtGui.QIcon(icons('32x32')))
#         # This code is required in Windows 7 to use the icon set by setWindowIcon in taskbar
#         # instead of the default Icon of python/pythonw
#         try:
#             import ctypes
#             myappid = f"mss.mss_pyui.{__version__}"  # arbitrary string
#             ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
#         except (ImportError, AttributeError) as error:
#             logging.debug("AttributeError, ImportError Exception %s", error)
#         # Reference to the flight track that is currently displayed in the
#         # views.
#         self.active_flight_track = None
#         self.last_save_directory = config_loader(dataset="data_dir")
#         self.mscolab_window = None
#         self.config_editor = None

#         # Connect Qt SIGNALs:
#         # ===================

#         # File menu.
#         self.actionNewFlightTrack.triggered.connect(functools.partial(self.create_new_flight_track, None, None))
#         self.actionOpenFlightTrack.triggered.connect(self.open_flight_track)
#         self.actionActivateSelectedFlightTrack.triggered.connect(self.activate_selected_flight_track)
#         self.actionCloseSelectedFlightTrack.triggered.connect(self.close_selected_flight_track)
#         self.actionSaveActiveFlightTrack.triggered.connect(self.save_flight_track)
#         self.actionSaveActiveFlightTrackAs.triggered.connect(self.save_flight_track_as)

#         # Views menu.
#         self.actionTopView.triggered.connect(self.create_new_view)
#         self.actionSideView.triggered.connect(self.create_new_view)
#         self.actionTableView.triggered.connect(self.create_new_view)
#         self.actionLinearView.triggered.connect(self.create_new_view)

#         # mscolab menu
#         self.actionMscolabProjects.triggered.connect(self.activate_mscolab_window)

#         # Help menu.
#         self.actionOnlineHelp.triggered.connect(self.show_online_help)
#         self.actionAboutMSUI.triggered.connect(self.show_about_dialog)
#         self.actionShortcuts.triggered.connect(self.show_shortcuts)
#         self.actionShortcuts.setShortcutContext(QtCore.Qt.ApplicationShortcut)

#         # Config
#         self.actionLoadConfigurationFile.triggered.connect(self.load_config_file)
#         self.actionConfigurationEditor.triggered.connect(self.open_config_editor)

#         # Flight Tracks.
#         self.listFlightTracks.itemActivated.connect(self.activate_flight_track)

#         # Views.
#         self.listViews.itemActivated.connect(self.activate_sub_window)

#         self.add_import_filter("CSV", "csv", load_from_csv, pickertag="filepicker_default")
#         self.add_export_filter("CSV", "csv", save_to_csv, pickertag="filepicker_default")

#         self._imported_plugins, self._exported_plugins = {}, {}
#         self.add_plugins()

#         preload_urls = config_loader(dataset="WMS_preload")
#         self.preload_wms(preload_urls)

#         # Status Bar
#         self.labelStatusbar.setText(self.status())

#         # Don't start the updater during a test run of mss_pyui
#         if "pytest" not in sys.modules:
#             self.updater = UpdaterUI(self)
#             self.actionUpdater.triggered.connect(self.updater.show)

#     @staticmethod
#     def preload_wms(urls):
#         """
#         This method accesses a list of WMS servers and load their capability documents.
#         :param urls: List of URLs
#         """
#         pdlg = QtWidgets.QProgressDialog("Preloading WMS servers...", "Cancel", 0, len(urls))
#         pdlg.reset()
#         pdlg.setValue(0)
#         pdlg.setModal(True)
#         pdlg.show()
#         QtWidgets.QApplication.processEvents()
#         for i, base_url in enumerate(urls):
#             pdlg.setValue(i)
#             QtWidgets.QApplication.processEvents()
#             # initialize login cache from config file, but do not overwrite existing keys
#             for key, value in config_loader(dataset="WMS_login").items():
#                 if key not in constants.WMS_LOGIN_CACHE:
#                     constants.WMS_LOGIN_CACHE[key] = value
#             username, password = constants.WMS_LOGIN_CACHE.get(base_url, (None, None))

#             try:
#                 request = requests.get(base_url)
#                 if pdlg.wasCanceled():
#                     break

#                 wms = wms_control.MSSWebMapService(request.url, version=None,
#                                                    username=username, password=password)
#                 wms_control.WMS_SERVICE_CACHE[wms.url] = wms
#                 logging.info("Stored WMS info for '%s'", wms.url)
#             except Exception as ex:
#                 logging.error("Error in preloading '%s': '%s'", type(ex), ex)
#             if pdlg.wasCanceled():
#                 break
#         logging.debug("Contents of WMS_SERVICE_CACHE: %s", wms_control.WMS_SERVICE_CACHE.keys())
#         pdlg.close()

#     def create_new_view(self):
#         """Method called when the user selects a new view to be opened. Creates
#            a new instance of the view and adds a QActiveViewsListWidgetItem to
#            the list of open views (self.listViews).
#         """
#         layout = config_loader(dataset="layout")
#         view_window = None
#         if self.sender() == self.actionTopView:
#             # Top view.
#             view_window = topview.MSSTopViewWindow(model=self.active_flight_track)
#             view_window.mpl.resize(layout['topview'][0], layout['topview'][1])
#             if layout["immutable"]:
#                 view_window.mpl.setFixedSize(layout['topview'][0], layout['topview'][1])
#         elif self.sender() == self.actionSideView:
#             # Side view.
#             view_window = sideview.MSSSideViewWindow(model=self.active_flight_track)
#             view_window.mpl.resize(layout['sideview'][0], layout['sideview'][1])
#             if layout["immutable"]:
#                 view_window.mpl.setFixedSize(layout['sideview'][0], layout['sideview'][1])
#         elif self.sender() == self.actionTableView:
#             # Table view.
#             view_window = tableview.MSSTableViewWindow(model=self.active_flight_track)
#             view_window.centralwidget.resize(layout['tableview'][0], layout['tableview'][1])
#         elif self.sender() == self.actionLinearView:
#             # Linear view.
#             view_window = linearview.MSSLinearViewWindow(model=self.active_flight_track)
#             view_window.mpl.resize(layout['linearview'][0], layout['linearview'][1])
#             if layout["immutable"]:
#                 view_window.mpl.setFixedSize(layout['linearview'][0], layout['linearview'][1])
#         if view_window is not None:
#             # Make sure view window will be deleted after being closed, not
#             # just hidden (cf. Chapter 5 in PyQt4).
#             view_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
#             # Open as a non-modal window.
#             view_window.show()
#             # Add an entry referencing the new view to the list of views.
#             listitem = QActiveViewsListWidgetItem(view_window, self.listViews, self.viewsChanged)
#             view_window.viewCloses.connect(listitem.view_destroyed)
#             self.listViews.setCurrentItem(listitem)
#             self.viewsChanged.emit()

#     def closeEvent(self, event):
#         """Ask user if he/she wants to close the application. If yes, also
#            close all views that are open.

#         Overloads QtGui.QMainWindow.closeEvent(). This method is called if
#         Qt receives a window close request for our application window.
#         """
#         ret = QtWidgets.QMessageBox.warning(
#             self, self.tr("Mission Support System"),
#             self.tr("Do you want to close the Mission Support System application?"),
#             QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

#         if ret == QtWidgets.QMessageBox.Yes:
#             # Table View stick around after MainWindow closes - maybe some dangling reference?
#             # This removes them for sure!
#             while self.listViews.count() > 0:
#                 self.listViews.item(0).window.handle_force_close()
#             self.listViews.clear()
#             self.listFlightTracks.clear()
#             # cleanup mscolab window
#             if self.mscolab_window is not None:
#                 self.mscolab_window.close()
#             if self.config_editor is not None:
#                 self.config_editor.close()
#             event.accept()
#         else:
#             event.ignore()

    def add_plugins(self):
        picker_default = config_loader(
            dataset="filepicker_default")

        self._imported_plugins = config_loader(dataset="import_plugins")
        for name in self._imported_plugins:
            extension, module, function = self._imported_plugins[name][:3]
            picker_type = picker_default
            if len(self._imported_plugins[name]) == 4:
                picker_type = self._imported_plugins[name][3]
            try:
                imported_module = importlib.import_module(module)
            # wildcard exception to be resilient against error introduced by user code
            except Exception as ex:
                logging.error("Error on import: %s: %s", type(ex), ex)
                QtWidgets.QMessageBox.critical(
                    self, self.tr("file io plugin error import plugins"),
                    self.tr(f"ERROR: Configuration\n\n{self._imported_plugins}\n\nthrows {type(ex)} error:\n{ex}"))
                continue
            try:
                self.add_import_filter(name, extension, getattr(imported_module, function), pickertype=picker_type)
            # wildcard exception to be resilient against error introduced by user code
            except Exception as ex:
                logging.error("Error on installing plugin: %s: %s", type(ex), ex)
                QtWidgets.QMessageBox.critical(
                    self, self.tr("file io plugin error import plugins"),
                    self.tr(f"ERROR: Configuration\n\n{self._imported_plugins}\n\nthrows {type(ex)} error:\n{ex}"))

                continue

        self._exported_plugins = config_loader(dataset="export_plugins")
        for name in self._exported_plugins:
            extension, module, function = self._exported_plugins[name][:3]
            picker_type = picker_default
            if len(self._exported_plugins[name]) == 4:
                picker_type = self._exported_plugins[name][3]
            try:
                imported_module = importlib.import_module(module)
            # wildcard exception to be resilient against error introduced by user code
            except Exception as ex:
                logging.error("Error on import: %s: %s", type(ex), ex)
                QtWidgets.QMessageBox.critical(
                    self, self.tr("file io plugin error import plugins"),
                    self.tr(f"ERROR: Configuration\n\n{self._exported_plugins,}\n\nthrows {type(ex)} error:\n{ex}"))
                continue
            try:
                self.add_export_filter(name, extension, getattr(imported_module, function), pickertype=picker_type)
            # wildcard exception to be resilient against error introduced by user code
            except Exception as ex:
                logging.error("Error on installing plugin: %s: %s", type(ex), ex)
                QtWidgets.QMessageBox.critical(
                    self, self.tr("file io plugin error"),
                    self.tr(f"ERROR: Configuration for export {self._exported_plugins} plugins\n\n{type(ex)}\n"
                            f"\nthrows error:\n{ex}"))
                continue

    def remove_plugins(self):
        for name in self._imported_plugins:
            full_name = "actionImportFlightTrack" + clean_string(name)
            actions = [_x for _x in self.menuImport_Flight_Track.actions()
                       if _x.objectName() == full_name]
            assert len(actions) == 1
            self.menuImport_Flight_Track.removeAction(actions[0])
            delattr(self, full_name)

        for name in self._exported_plugins:
            full_name = "actionExportFlightTrack" + clean_string(name)
            actions = [_x for _x in self.menuExport_Active_Flight_Track.actions()
                       if _x.objectName() == full_name]
            assert len(actions) == 1
            self.menuExport_Active_Flight_Track.removeAction(actions[0])
            delattr(self, full_name)

    def add_import_filter(self, name, extension, function, pickertag=None, pickertype=None):
        full_name = "actionImportFlightTrack" + clean_string(name)
        if hasattr(self, full_name):
            raise ValueError(f"'{full_name}' has already been set!")

        action = QtWidgets.QAction(self)
        action.setObjectName(full_name)
        action.setText(QtCore.QCoreApplication.translate("MSSMainWindow", name, None))
        self.menuImport_Flight_Track.addAction(action)

        def load_function_wrapper(self):
            filename = get_open_filename(
                self, "Import Flight Track", self.last_save_directory,
                "All Files (*." + extension + ")", pickertype=pickertype)
            if filename is not None:
                self.last_save_directory = fs.path.dirname(filename)
                try:
                    ft_name, new_waypoints = function(filename)
                # wildcard exception to be resilient against error introduced by user code
                except Exception as ex:
                    logging.error("file io plugin error: %s %s", type(ex), ex)
                    QtWidgets.QMessageBox.critical(
                        self, self.tr("file io plugin error"),
                        self.tr(f"ERROR: {type(ex)} {ex}"))
                else:
                    if not ft_name:
                        ft_name = filename
                    waypoints_model = ft.WaypointsTableModel(name=ft_name, waypoints=new_waypoints)

                    listitem = QFlightTrackListWidgetItem(waypoints_model, self.listFlightTracks)
                    listitem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                    self.listFlightTracks.setCurrentItem(listitem)
                    self.activate_flight_track(listitem)

        setattr(self, full_name, types.MethodType(load_function_wrapper, self))
        action.triggered.connect(getattr(self, full_name))

    def add_export_filter(self, name, extension, function, pickertag=None, pickertype=None):
        full_name = "actionExportFlightTrack" + clean_string(name)
        if hasattr(self, full_name):
            raise ValueError(f"'{full_name}' has already been set!")

        action = QtWidgets.QAction(self)
        action.setObjectName(full_name)
        action.setText(QtCore.QCoreApplication.translate("MSSMainWindow", name, None))
        self.menuExport_Active_Flight_Track.addAction(action)

        def save_function_wrapper(self):
            default_filename = os.path.join(self.last_save_directory, self.active_flight_track.name) + "." + extension
            filename = get_save_filename(
                self, "Export Flight Track", default_filename,
                name + " (*." + extension + ")", pickertype=pickertype)
            if filename is not None:
                self.last_save_directory = fs.path.dirname(filename)
                try:
                    function(filename, self.active_flight_track.name, self.active_flight_track.waypoints)
                # wildcard exception to be resilient against error introduced by user code
                except Exception as ex:
                    logging.error("file io plugin error: %s %s", type(ex), ex)
                    QtWidgets.QMessageBox.critical(
                        self, self.tr("file io plugin error"),
                        self.tr(f"ERROR: {type(ex)} {ex}"))

        setattr(self, full_name, types.MethodType(save_function_wrapper, self))
        action.triggered.connect(getattr(self, full_name))

    def create_new_flight_track(self, template=None, filename=None):
        """Creates a new flight track model from a template. Adds a new entry to
           the list of flight tracks. Called when the user selects the 'new/open
           flight track' menu entries.

        Arguments:
        template -- copy the specified template to the new flight track (so that
                    it is not empty).
        filename -- if not None, load the flight track in the specified file.
        """
        if template is None:
            template = []
            waypoints = config_loader(dataset="new_flighttrack_template")
            default_flightlevel = config_loader(dataset="new_flighttrack_flightlevel")
            for wp in waypoints:
                template.append(ft.Waypoint(flightlevel=default_flightlevel, location=wp))
            if len(template) < 2:
                QtWidgets.QMessageBox.critical(
                    self, self.tr("flighttrack template"),
                    self.tr("ERROR:Flighttrack template in configuration is too short. "
                            "Please add at least two valid locations."))

        if filename is not None:
            waypoints_model = ft.WaypointsTableModel(filename=filename)
        else:
            # Create a new flight track from the waypoints template.
            self.new_flight_track_counter += 1
            waypoints_model = ft.WaypointsTableModel(
                name=f"new flight track ({self.new_flight_track_counter:d})")
            # Make a copy of the template. Otherwise all new flight tracks would
            # use the same data structure in memory.
            template_copy = copy.deepcopy(template)
            waypoints_model.insertRows(0, rows=len(template_copy), waypoints=template_copy)

        # Create a new list entry for the flight track. Make the item name editable.
        listitem = QFlightTrackListWidgetItem(waypoints_model, self.listFlightTracks)
        listitem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

        # Activate new item
        self.activate_flight_track(listitem)

    def open_flight_track(self):
        """Slot for the 'Open Flight Track' menu entry. Opens a QFileDialog and
           passes the result to createNewFlightTrack().
        """
        filename = get_open_filename(
            self, "Open Flight Track", self.last_save_directory, "Flight Track Files (*.ftml)",
            pickertag="filepicker_default")
        if filename is not None:
            self.last_save_directory = fs.path.dirname(filename)
            try:
                if filename.endswith('.ftml'):
                    self.create_new_flight_track(filename=filename)
                else:
                    QtWidgets.QMessageBox.warning(self, "Open flight track",
                                                  f"No supported file extension recognized!\n{filename:}")

            except (SyntaxError, OSError, IOError) as ex:
                QtWidgets.QMessageBox.critical(
                    self, self.tr("Problem while opening flight track FTML:"),
                    self.tr(f"ERROR: {type(ex)} {ex}"))

    def activate_flight_track(self, item):
        """Set the currently selected flight track to be the active one, i.e.
           the one that is displayed in the views (only one flight track can be
           displayed at a time).
        """
        self.active_flight_track = item.flighttrack_model
        for i in range(self.listViews.count()):
            view_item = self.listViews.item(i)
            view_item.window.setFlightTrackModel(self.active_flight_track)
        font = QtGui.QFont()
        for i in range(self.listFlightTracks.count()):
            self.listFlightTracks.item(i).setFont(font)
        font.setBold(True)
        item.setFont(font)

    def activate_selected_flight_track(self):
        item = self.listFlightTracks.currentItem()
        self.activate_flight_track(item)

    def save_flight_track(self):
        """Slot for the 'Save Active Flight Track As' menu entry.
        """
        filename = self.active_flight_track.get_filename()
        if filename and filename.endswith('.ftml'):
            sel = QtWidgets.QMessageBox.question(self, "Save flight track",
                                                 f"Saving flight track to '{filename:s}'. Continue?",
                                                 QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if sel == QtWidgets.QMessageBox.Yes:
                try:
                    self.active_flight_track.save_to_ftml(filename)
                except (OSError, IOError) as ex:
                    QtWidgets.QMessageBox.critical(
                        self, self.tr("Problem while saving flight track to FTML:"),
                        self.tr(f"ERROR: {type(ex)} {ex}"))
        else:
            self.save_flight_track_as()

    def save_flight_track_as(self):
        """Slot for the 'Save Active Flight Track As' menu entry.
        """
        default_filename = os.path.join(self.last_save_directory, self.active_flight_track.name + ".ftml")
        filename = get_save_filename(
            self, "Save Flight Track", default_filename, "Flight Track (*.ftml)", pickertag="filepicker_default")
        logging.debug("filename : '%s'", filename)
        if filename:
            self.last_save_directory = fs.path.dirname(filename)
            if filename.endswith('.ftml'):
                try:
                    self.active_flight_track.save_to_ftml(filename)
                except (OSError, IOError) as ex:
                    QtWidgets.QMessageBox.critical(
                        self, self.tr("Problem while saving flight track to FTML:"),
                        self.tr(f"ERROR: {type(ex)} {ex}"))
                for idx in range(self.listFlightTracks.count()):
                    if self.listFlightTracks.item(idx).flighttrack_model == self.active_flight_track:
                        self.listFlightTracks.item(idx).setText(self.active_flight_track.name)
            else:
                QtWidgets.QMessageBox.warning(self, "Save flight track",
                                              f"File extension is not '.ftml'!\n{filename:}")

    def close_selected_flight_track(self):
        """Slot to close the currently selected flight track. Flight tracks can
           only be closed if at least one other flight track remains open. The
           currently active flight track cannot be closed.
        """
        if self.listFlightTracks.count() < 2:
            QtWidgets.QMessageBox.information(self, self.tr("Flight Track Management"),
                                              self.tr("At least one flight track has to be open."))
            return
        item = self.listFlightTracks.currentItem()
        if item.flighttrack_model == self.active_flight_track:
            QtWidgets.QMessageBox.information(self, self.tr("Flight Track Management"),
                                              self.tr("Cannot close currently active flight track."))
            return
        if item.flighttrack_model.modified:
            ret = QtWidgets.QMessageBox.warning(self, self.tr("Mission Support System"),
                                                self.tr("The flight track you are about to close has "
                                                        "been modified. Close anyway?"),
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                QtWidgets.QMessageBox.No)
            if ret == QtWidgets.QMessageBox.Yes:
                self.listFlightTracks.takeItem(self.listFlightTracks.currentRow())

    def activate_sub_window(self, item):
        """When the user clicks on one of the open view or tool windows, this
           window is brought to the front. This function implements the slot to
           activate a window if the user selects it in the list of views or
           tools.
        """
        # Restore the activated view and bring it to the front.
        item.window.showNormal()
        item.window.raise_()
        item.window.activateWindow()

    def close_mscolab_window(self):
        self.mscolab_window = None

    def activate_mscolab_window(self):
        # initiate mscolab window
        if self.mscolab_window is None:
            self.mscolab_window = mscolab.MSSMscolabWindow(parent=self)
            self.mscolab_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.mscolab_window.viewCloses.connect(self.close_mscolab_window)
            self.mscolab_window.show()
        else:
            self.mscolab_window.setWindowState(QtCore.Qt.WindowNoState)
            self.mscolab_window.raise_()
            self.mscolab_window.activateWindow()

    def restart_application(self):
        while self.listViews.count() > 0:
            self.listViews.item(0).window.handle_force_close()
        self.listViews.clear()
        self.remove_plugins()
        self.add_plugins()

    def load_config_file(self):
        """
        Loads a config file and potentially restarts the application
        """
        ret = QtWidgets.QMessageBox.warning(
            self, self.tr("Mission Support System"),
            self.tr("Opening a config file will reset application. Continue?"),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if ret == QtWidgets.QMessageBox.Yes:
            filename = get_open_filename(
                self, "Open Config file", constants.MSS_CONFIG_PATH, "Config Files (*.json)")
            if filename is not None:
                constants.CACHED_CONFIG_FILE = filename
                self.restart_application()

    def open_config_editor(self):
        """
        Opens up a JSON config editor
        """
        if self.config_editor is None:
            self.config_editor = editor.EditorMainWindow(parent=self)
            self.config_editor.viewCloses.connect(self.close_config_editor)
            self.config_editor.restartApplication.connect(self.restart_application)
        else:
            self.config_editor.showNormal()
            self.config_editor.activateWindow()

    def close_config_editor(self):
        self.config_editor = None

    def show_online_help(self):
        """Open Documentation in a browser"""
        QtGui.QDesktopServices.openUrl(
            QtCore.QUrl("http://mss.readthedocs.io/en/stable"))

    def show_about_dialog(self):
        """Show the 'About MSUI' dialog to the user.
        """
        dlg = MSS_AboutDialog(parent=self)
        dlg.setModal(True)
        dlg.exec_()

    def show_shortcuts(self):
        """Show the shortcuts dialog to the user.
        """
        dlg = MSS_ShortcutsDialog()
        dlg.setModal(True)
        dlg.exec_()

    def status(self):
        if constants.CACHED_CONFIG_FILE is None:
            return ("Status : System Configuration")
        else:
            filename = constants.CACHED_CONFIG_FILE
            head_filename, tail_filename = os.path.split(filename)
            return("Status : User Configuration '" + tail_filename + "' loaded")


def main():
    try:
        prefix = os.environ["CONDA_DEFAULT_ENV"]
    except KeyError:
        prefix = ""
    app_prefix = prefix
    if prefix:
        app_prefix = f"-{prefix}"
    icon_hash = hashlib.md5('.'.join([__version__, app_prefix]).encode('utf-8')).hexdigest()

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", help="show version", action="store_true", default=False)
    parser.add_argument("--debug", help="show debugging log messages on console", action="store_true", default=False)
    parser.add_argument("--logfile", help="Specify logfile location. Set to empty string to disable.", action="store",
                        default=os.path.join(constants.MSS_CONFIG_PATH, "mss_pyui.log"))
    parser.add_argument("-m", "--menu", help="adds mss to menu", action="store_true", default=False)
    parser.add_argument("-d", "--deinstall", help="removes mss from menu", action="store_true", default=False)
    parser.add_argument("--update", help="Updates MSS to the newest version", action="store_true", default=False)

    args = parser.parse_args()

    if args.version:
        print("***********************************************************************")
        print("\n            Mission Support System (mss)\n")
        print("***********************************************************************")
        print("Documentation: http://mss.rtfd.io")
        print("Version:", __version__)
        sys.exit()

    if args.update:
        updater = Updater()
        updater.on_update_available.connect(lambda old, new: updater.update_mss())
        updater.on_log_update.connect(lambda s: print(s.replace("\n", "")))
        updater.on_status_update.connect(lambda s: print(s.replace("\n", "")))
        updater.run()
        while Worker.workers:
            list(Worker.workers)[0].wait()
        sys.exit()

    setup_logging(args)

    if args.menu:
        # Experimental feature to get mss into application menu
        if platform.system() == "Linux":
            icon_size = '48x48'
            src_icon_path = icons(icon_size)
            icon_destination = constants.POSIX["icon_destination"].format(icon_size, icon_hash)
            dirname = os.path.dirname(icon_destination)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            shutil.copyfile(src_icon_path, icon_destination)
            desktop = constants.POSIX["desktop"]
            application_destination = constants.POSIX["application_destination"].format(app_prefix)
            dirname = os.path.dirname(application_destination)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            if prefix:
                prefix = f"({prefix})"
            desktop = desktop.format(prefix,
                                     os.path.join(sys.prefix, "bin", "mss"),
                                     icon_destination)
            with open(application_destination, 'w') as f:
                f.write(desktop)
            logging.info("menu entry created")
        sys.exit()
    if args.deinstall:
        application_destination = constants.POSIX["application_destination"].format(app_prefix)
        if os.path.exists(application_destination):
            os.remove(application_destination)
        icon_size = '48x48'
        icon_destination = constants.POSIX["icon_destination"].format(icon_size, icon_hash)
        if os.path.exists(icon_destination):
            os.remove(icon_destination)
        logging.info("menu entry removed")
        sys.exit()

    logging.info("MSS Version: %s", __version__)
    logging.info("Python Version: %s", sys.version)
    logging.info("Platform: %s (%s)", platform.platform(), platform.architecture())
    logging.info("Launching user interface...")

    application = QtWidgets.QApplication(sys.argv)
    application.setWindowIcon(QtGui.QIcon(icons('128x128')))
    application.setApplicationDisplayName("MSS")
    application.setAttribute(QtCore.Qt.AA_DisableWindowContextHelpButton)
    application.setStyleSheet("QFrame { border: 0; }")
    mainwindow = MSSMainWindow()
    # mainwindow.create_new_flight_track()
    mainwindow.show()
    sys.exit(application.exec_())


if __name__ == "__main__":
    main()
