#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    mslib.msui.msui
    ~~~~~~~~~~~~~~~

    Mission Support System Python/Qt User Interface
    Main window of the user interface application. Manages view and tool windows
    (the user can open multiple windows) and provides functionality to open, save,
    and switch between flight tracks.

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2023 by the MSS team, see AUTHORS.
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
import hashlib
import logging
import os
import platform
import shutil
import sys
import fs

from packaging import version
from mslib import __version__
from mslib.msui.msui_mainwindow import MSUIMainWindow
from mslib.msui import constants
from mslib.utils import setup_logging
from mslib.msui.icons import icons
from mslib.utils.qt import Worker, Updater
from mslib.utils.config import read_config_file
from PyQt5 import QtGui, QtCore, QtWidgets

# Add config path to PYTHONPATH so plugins located there may be found
sys.path.append(constants.MSUI_CONFIG_PATH)


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
                        default=os.path.join(constants.MSUI_CONFIG_PATH, "msui.log"))
    parser.add_argument("-m", "--menu", help="adds msui to menu", action="store_true", default=False)
    parser.add_argument("-d", "--deinstall", help="removes msui from menu", action="store_true", default=False)
    parser.add_argument("--update", help="Updates MSS to the newest version", action="store_true", default=False)

    args = parser.parse_args()

    if args.version:
        print("***********************************************************************")
        print("\n            Mission Support System (MSS)\n")
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
        # Experimental feature to get msui into application menu
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
                                     os.path.join(sys.prefix, "bin", "msui"),
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

    try:
        read_config_file()
    except (FileNotFoundError, fs.errors.CreateFailed, fs.errors.FileExpected) as ex:
        message = f'\n\nFix the setup of your "MSUI_SETTINGS" configuration.\n{ex}'
        logging.error(message)
        sys.exit()

    application = QtWidgets.QApplication(sys.argv)
    mainwindow = None

    # Trigger shortcuts/search dialog even on modal dialogs
    application.oldNotify = application.notify

    def notify(QObject, QEvent):
        if QEvent.type() == QtCore.QEvent.KeyPress and mainwindow:
            if QEvent.key() == QtCore.Qt.Key_S and QEvent.modifiers() == QtCore.Qt.AltModifier:
                mainwindow.show_shortcuts()
            elif QEvent.key() == QtCore.Qt.Key_F and QEvent.modifiers() == QtCore.Qt.ControlModifier:
                mainwindow.show_shortcuts(True)
        return application.oldNotify(QObject, QEvent)

    application.notify = notify

    application.setWindowIcon(QtGui.QIcon(icons('128x128')))
    application.setApplicationDisplayName("MSUI")
    application.setAttribute(QtCore.Qt.AA_DisableWindowContextHelpButton)
    mainwindow = MSUIMainWindow()
    if version.parse(__version__) >= version.parse('9.0.0') and version.parse(__version__) < version.parse('10.0.0'):
        from mslib.utils.migration.config_before_nine import read_config_file as read_config_file_before_nine
        from mslib.utils.migration.config_before_nine import config_loader as config_loader_before_nine
        read_config_file_before_nine()
        if config_loader_before_nine(dataset="MSCOLAB_mailid"):

            text = """We can update your msui_settings.json file \n
We add the new attributes for the MSColab login, see \n
https://mss.readthedocs.io/en/stable/usage.html#mscolab-login-and-www-authentication \n

A backup of the old file is stored.
"""

            ret = QtWidgets.QMessageBox.question(mainwindow, 'Update of msui_settings.json file',
                                                 text,
                                                 QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                 QtWidgets.QMessageBox.No)
            if ret == QtWidgets.QMessageBox.Yes:
                from mslib.utils.migration.update_json_file_to_version_nine import JsonConversion
                if version.parse(__version__) >= version.parse('9.0.0'):
                    new_version = JsonConversion()
                    new_version.change_parameters()
        read_config_file()

    mainwindow.setStyleSheet("QListWidget { border: 1px solid grey; }")
    mainwindow.create_new_flight_track()
    mainwindow.show()
    sys.exit(application.exec_())


if __name__ == "__main__":
    main()
