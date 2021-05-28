# -*- coding: utf-8 -*-
"""

    mslib.msui.mss_qt
    ~~~~~~~~~~~~~~~~~

    This module helps with qt

    This file is part of mss.

    :copyright: Copyright 2017-2018 Joern Ungermann, Reimar Bauer
    :copyright: Copyright 2017-2021 by the mss team, see AUTHORS.
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
from PyQt5 import QtCore, QtWidgets  # noqa

from mslib.utils import config_loader, FatalUserError


def get_open_filename_qt(*args):
    filename = QtWidgets.QFileDialog.getOpenFileName(*args)
    return filename[0] if isinstance(filename, tuple) else str(filename)


def get_open_filenames_qt(*args):
    """
    To select multiple files simultaneously
    """
    filenames = QtWidgets.QFileDialog.getOpenFileNames(*args)
    return filenames[0] if isinstance(filenames, tuple) else str(filenames)


def get_save_filename_qt(*args):
    filename = QtWidgets.QFileDialog.getSaveFileName(*args)
    return filename[0] if isinstance(filename, tuple) else str(filename)


def get_existing_directory_qt(*args):
    dirname = QtWidgets.QFileDialog.getExistingDirectory(*args)
    return dirname[0] if isinstance(dirname, tuple) else str(dirname)


def get_pickertype(tag, typ):
    default = config_loader(dataset="filepicker_default")
    if typ is None:
        if tag is None:
            typ = default
        else:
            typ = config_loader(dataset=tag)
    return typ


def get_open_filename(parent, title, dirname, filt, pickertag=None, pickertype=None):
    pickertype = get_pickertype(pickertag, pickertype)
    if pickertype == "fs":
        # fs filepicker takes file filters as a list
        if not isinstance(filt, list):
            filt = filt.split(';;')
        filename = getOpenFileName(parent, dirname, filt, title="Import Flight Track")
    elif pickertype in ["qt", "default"]:
        # qt filepicker takes file filters separated by ';;'
        filename = get_open_filename_qt(parent, title, os.path.expanduser(dirname), filt)
    else:
        raise FatalUserError(f"Unknown file picker type '{pickertype}'.")
    logging.debug("Selected '%s'", filename)
    if filename == "":
        filename = None
    return filename


def get_open_filenames(parent, title, dirname, filt, pickertag=None, pickertype=None):
    """
    Opens multiple files simultaneously
    Currently implemented only in kmloverlay_dockwidget.py
    """
    pickertype = get_pickertype(pickertag, pickertype)
    if pickertype in ["qt", "default"]:
        filename = get_open_filenames_qt(parent, title, os.path.expanduser(dirname), filt)
    else:
        raise FatalUserError(f"Unknown file picker type '{pickertype}'.")
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
        raise FatalUserError(f"Unknown file picker type '{pickertype}'.")
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
        raise FatalUserError(f"Unknown file picker type '{pickertype}'.")
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
        "ui_shortcuts",
        "ui_updater_dialog",
        "ui_hexagon_dockwidget",
        "ui_kmloverlay_dockwidget",
        "ui_customize_kml",
        "ui_mainwindow",
        "ui_performance_dockwidget",
        "ui_remotesensing_dockwidget",
        "ui_satellite_dockwidget",
        "ui_sideview_options",
        "ui_sideview_window",
        "ui_tableview_window",
        "ui_topview_mapappearance",
        "ui_topview_window",
        "ui_wms_capabilities",
        "ui_wms_dockwidget",
        "ui_wms_password_dialog",
        "ui_wms_multilayers"]:
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
            f"Fatal user error in MSS {mslib.__version__} on {platform.platform()}\n"
            f"Python {sys.version}\n"
            f"\n"
            f"{value}")
    else:
        QtWidgets.QMessageBox.critical(
            None, "fatal error",
            f"Fatal error in MSS {mslib.__version__} on {platform.platform()}\n"
            f"Python {sys.version}\n"
            f"\n"
            f"Please report bugs in MSS to https://github.com/Open-MSS/MSS\n"
            f"\n"
            f"Information about the fatal error:\n"
            f"\n"
            f"{tb}")


sys.excepthook = excepthook
