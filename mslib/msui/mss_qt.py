# -*- coding: utf-8 -*-
"""

    mslib.msui.mss_qt
    ~~~~~~~~~~~~~~~~~

    This module helps with qt

    This file is part of mss.

    :copyright: Copyright 2017-2018 Joern Ungermann, Reimar Bauer
    :copyright: Copyright 2017-2020 by the mss team, see AUTHORS.
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

import importlib
import logging
import os
import platform
import sys
import traceback

from fslib.fs_filepicker import getSaveFileName, getOpenFileName, getExistingDirectory

from PyQt5 import QtGui, QtCore, QtWidgets, QtTest

from mslib.utils import config_loader, FatalUserError
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default


def get_open_filename_qt(*args):
    filename = QtWidgets.QFileDialog.getOpenFileName(*args)
    return filename[0] if isinstance(filename, tuple) else str(filename)


def get_save_filename_qt(*args):
    filename = QtWidgets.QFileDialog.getSaveFileName(*args)
    return filename[0] if isinstance(filename, tuple) else str(filename)


def get_existing_directory_qt(*args):
    dirname = QtWidgets.QFileDialog.getExistingDirectory(*args)
    return dirname[0] if isinstance(dirname, tuple) else str(dirname)


def get_pickertype(tag, typ):
    default = config_loader(dataset="filepicker_default", default=mss_default.filepicker_default)
    if typ is None:
        if tag is None:
            typ = default
        else:
            typ = config_loader(dataset=tag, default=default)
    return typ


def get_open_filename(parent, title, dirname, filt, pickertag=None, pickertype=None):
    pickertype = get_pickertype(pickertag, pickertype)
    if pickertype == "fs":
        filename = getOpenFileName(parent, dirname, filt, title="Import Flight Track")
    elif pickertype in ["qt", "default"]:
        filename = get_open_filename_qt(parent, title, os.path.expanduser(dirname), filt)
    else:
        raise FatalUserError("Unknown file picker type '%s'.", pickertype)
    logging.debug("Selected '%s'", filename)
    if filename == "":
        filename = None
    return filename


def get_save_filename(parent, title, filename, filt, pickertag=None, pickertype=None):
    pickertype = get_pickertype(pickertag, pickertype)
    if pickertype == "fs":
        dirname, filename = os.path.split(filename)
        filename = getSaveFileName(
            parent, dirname, filt, title=title, default_filename=filename, show_save_action=True)
    elif pickertype in ["qt", "default"]:
        filename = get_save_filename_qt(parent, title, os.path.expanduser(filename), filt)
    else:
        raise FatalUserError("Unknown file picker type '%s'.", pickertype)
    logging.debug("Selected '%s'", filename)
    if filename == "":
        filename = None
    return filename


def get_existing_directory(parent, title, defaultdir, pickertag=None, pickertype=None):
    pickertype = get_pickertype(pickertag, pickertype)
    if pickertype == "fs":
        dirname = getExistingDirectory(parent, title=title, fs_url=defaultdir)[0]
    elif pickertype in ["qt", "default"]:
        dirname = get_existing_directory_qt(parent, title, defaultdir)
    else:
        raise FatalUserError("Unknown file picker type '%s'.", pickertype)
    logging.debug("Selected '%s'", dirname)
    if dirname == "":
        dirname = None
    return dirname


def variant_to_string(variant):
    if isinstance(variant, QtCore.QVariant):
        return str(variant.value())
    return str(variant)


def variant_to_float(variant, locale=QtCore.QLocale()):
    if isinstance(variant, QtCore.QVariant):
        value = variant.value()
    else:
        value = variant

    if isinstance(value, (int, float)):
        return value
    try:
        float_value, ok = locale.toDouble(value)
        if not ok:
            raise ValueError
    except TypeError:  # neither float nor string, try Python conversion
        logging.error("Unexpected type in float conversion: %s=%s",
                      type(value), value)
        float_value = float(value)
    return float_value


# Import all Dialogues from the proper module directory.
for mod in [
        "ui_about_dialog",
        "ui_hexagon_dockwidget",
        "ui_kmloverlay_dockwidget",
        "ui_mainwindow",
        "ui_performance_settings",
        "ui_remotesensing_dockwidget",
        "ui_satellite_dockwidget",
        "ui_sideview_options",
        "ui_sideview_window",
        "ui_tableview_window",
        "ui_timeseriesview_window",
        "ui_topview_mapappearance",
        "ui_topview_window",
        "ui_trajectories_window",
        "ui_wms_capabilities",
        "ui_wms_dockwidget",
        "ui_wms_password_dialog",
        "ui_mscolab_window",
        "ui_mscolab_project_window",
        "ui_add_project_dialog",
        "ui_add_user_dialog"]:
    globals()[mod] = importlib.import_module("mslib.msui.qt5." + mod)

# to store config by QSettings
QtCore.QCoreApplication.setOrganizationName("mss")


# PyQt5 silently aborts on a Python Exception
def excepthook(type_, value, traceback_):
    """
    This dumps the error to console, logging (i.e. logfile), and tries to open a MessageBox for GUI users.
    """
    import mslib
    import mslib.utils
    tb = "".join(traceback.format_exception(type_, value, traceback_))
    traceback.print_exception(type_, value, traceback_)
    logging.critical("MSS Version: %s", mslib.__version__)
    logging.critical("Python Version: %s", sys.version)
    logging.critical("Platform: %s (%s)", platform.platform(), platform.architecture())
    logging.critical("Fatal error: %s", tb)

    if type_ is mslib.utils.FatalUserError:
        QtWidgets.QMessageBox.critical(
            None, "fatal error",
            "Fatal user error in MSS {} on {}\n"
            "Python {}\n"
            "\n"
            "{}".format(mslib.__version__, platform.platform(), sys.version, value))
    else:
        QtWidgets.QMessageBox.critical(
            None, "fatal error",
            "Fatal error in MSS {} on {}\n"
            "Python {}\n"
            "\n"
            "Please report bugs in MSS to https://bitbucket.org/wxmetvis/mss\n"
            "\n"
            "Information about the fatal error:\n"
            "\n"
            "{}".format(mslib.__version__, platform.platform(), sys.version, tb))


sys.excepthook = excepthook
