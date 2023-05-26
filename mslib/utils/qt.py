# -*- coding: utf-8 -*-
"""

    mslib.utils.msui_qt
    ~~~~~~~~~~~~~~~~~

    This module helps with qt

    This file is part of MSS.

    :copyright: Copyright 2017-2018 Joern Ungermann, Reimar Bauer
    :copyright: Copyright 2017-2023 by the MSS team, see AUTHORS.
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

import logging
import os
import re
import platform
import sys
import subprocess
import traceback

from fslib.fs_filepicker import getSaveFileName, getOpenFileName, getExistingDirectory
from PyQt5 import QtCore, QtWidgets, QtGui  # noqa

from mslib.utils.config import config_loader
from mslib.utils import FatalUserError, subprocess_startupinfo


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
    _filename = QtWidgets.QFileDialog.getSaveFileName(*args)
    if isinstance(_filename, tuple):
        # ToDo when can this be only a str
        extension = re.sub(r'\w.*\(\*', '', _filename[1][:-1])
        filename = _filename[0]
        if not filename.endswith(extension):
            filename = f'{filename}{extension}'
        return filename
    return _filename


def get_existing_directory_qt(*args):
    dirname = QtWidgets.QFileDialog.getExistingDirectory(*args)
    return dirname[0] if isinstance(dirname, tuple) else str(dirname)


def get_pickertype(pickertype=None):
    if pickertype is None:
        return config_loader(dataset="filepicker_default")
    if pickertype not in ["qt", "default", "fs"]:
        raise FatalUserError(f"Unknown file picker type '{pickertype}'.")
    return pickertype


def get_open_filename(parent, title, dirname, filt, pickertype=None):
    pickertype = get_pickertype(pickertype)
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


def get_open_filenames(parent, title, dirname, filt, pickertype=None):
    """
    Opens multiple files simultaneously
    Currently implemented only in kmloverlay_dockwidget.py
    """
    pickertype = get_pickertype(pickertype)
    if pickertype in ["qt", "default"]:
        filename = get_open_filenames_qt(parent, title, os.path.expanduser(dirname), filt)
    else:
        raise FatalUserError(f"Unknown file picker type '{pickertype}'.")
    logging.debug("Selected '%s'", filename)
    if filename == []:
        filename = None
    return filename


def get_save_filename(parent, title, filename, filt, pickertype=None):
    pickertype = get_pickertype(pickertype)
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


def get_existing_directory(parent, title, defaultdir, pickertype=None):
    pickertype = get_pickertype(pickertype)
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


# to store config by QSettings
QtCore.QCoreApplication.setOrganizationName("msui")


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


def show_popup(parent, title, message, icon=0):
    """
        title: Title of message box
        message: Display Message
        icon: 0 = Error Icon, 1 = Information Icon
    """
    if icon == 0:
        QtWidgets.QMessageBox.critical(parent, title, message)
    elif icon == 1:
        QtWidgets.QMessageBox.information(parent, title, message)


# TableView drag and drop
def dropEvent(self, event):
    target_row = self.indexAt(event.pos()).row()
    if target_row == -1:
        target_row = self.model().rowCount() - 1
    source_row = event.source().currentIndex().row()
    wps = [self.model().waypoints[source_row]]
    if target_row > source_row:
        self.model().insertRows(target_row + 1, 1, waypoints=wps)
        self.model().removeRows(source_row)
    elif target_row < source_row:
        self.model().removeRows(source_row)
        self.model().insertRows(target_row, 1, waypoints=wps)
    event.accept()


def dragEnterEvent(self, event):
    event.accept()


class CheckableComboBox(QtWidgets.QComboBox):
    """
    Multiple Choice ComboBox taken from QGIS
    """

    # Subclass Delegate to increase item height
    class Delegate(QtWidgets.QStyledItemDelegate):
        def sizeHint(self, option, index):
            size = super().sizeHint(option, index)
            size.setHeight(20)
            return size

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make the combo editable to set a custom text, but readonly
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        # Make the lineedit the same color as QPushButton
        palette = QtWidgets.QApplication.palette()
        palette.setBrush(QtGui.QPalette.Base, palette.button())
        self.lineEdit().setPalette(palette)

        # Use custom delegate
        self.setItemDelegate(CheckableComboBox.Delegate())

        # Update the text when an item is toggled
        self.model().dataChanged.connect(self.updateText)

        # Hide and show popup when clicking the line edit
        self.lineEdit().installEventFilter(self)
        self.closeOnLineEditClick = False

        # Prevent popup from closing when clicking on an item
        self.view().viewport().installEventFilter(self)

        self.empty_text = ""

    def resizeEvent(self, event):
        # Recompute text to elide as needed
        self.updateText()
        super().resizeEvent(event)

    def eventFilter(self, object, event):
        if object == self.lineEdit():
            if event.type() == QtCore.QEvent.MouseButtonRelease:
                if self.closeOnLineEditClick:
                    self.hidePopup()
                else:
                    self.showPopup()
                return True
            return False

        if object == self.view().viewport():
            if event.type() == QtCore.QEvent.MouseButtonRelease:
                index = self.view().indexAt(event.pos())
                item = self.model().item(index.row())

                if item.checkState() == QtCore.Qt.Checked:
                    item.setCheckState(QtCore.Qt.Unchecked)
                else:
                    item.setCheckState(QtCore.Qt.Checked)
                return True
        return False

    def showPopup(self):
        super().showPopup()
        # When the popup is displayed, a click on the lineedit should close it
        self.closeOnLineEditClick = True

    def hidePopup(self):
        super().hidePopup()
        # Used to prevent immediate reopening when clicking on the lineEdit
        self.startTimer(100)
        # Refresh the display text when closing
        self.updateText()

    def timerEvent(self, event):
        # After timeout, kill timer, and reenable click on line edit
        self.killTimer(event.timerId())
        self.closeOnLineEditClick = False

    def updateText(self):
        texts = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == QtCore.Qt.Checked:
                texts.append(self.model().item(i).text())
        text = ", ".join(texts)
        if len(text) == 0:
            text = self.empty_text

        self.lineEdit().setText(text)

    def addItem(self, text, data=None):
        item = QtGui.QStandardItem()
        item.setText(text)
        if data is None:
            item.setData(text)
        else:
            item.setData(data)
        item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
        item.setData(QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)
        self.model().appendRow(item)

    def addItems(self, texts, datalist=None):
        for i, text in enumerate(texts):
            try:
                data = datalist[i]
            except (TypeError, IndexError):
                data = None
            self.addItem(text, data)

    def currentData(self):
        # Return the list of selected items data
        res = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == QtCore.Qt.Checked:
                res.append(self.model().item(i).data())
        return res


class NoLayersError(Exception):
    def __init__(self, message="No Layers found in WMS get capabilities"):
        self.message = message
        super().__init__(self.message)


class Worker(QtCore.QThread):
    """
    Can be used to run a function through a QThread without much struggle,
    and receive the return value or exception through signals.
    Beware not to modify the parents connections through the function.
    You may change the GUI, but it may sometimes not update until the Worker is done.
    """
    # Static set of all workers to avoid segfaults
    workers = set()
    finished = QtCore.pyqtSignal(object)
    failed = QtCore.pyqtSignal(Exception)

    def __init__(self, function):
        Worker.workers.add(self)
        super(Worker, self).__init__()
        self.function = function
        # pyqtSignals don't work without an application eventloop running
        if QtCore.QCoreApplication.startingUp():
            self.finished = NonQtCallback()
            self.failed = NonQtCallback()

        self.failed.connect(lambda e: self._update_gui())
        self.finished.connect(lambda x: self._update_gui())

    def run(self):
        try:
            result = self.function()
            # ToDo the capbilities worker member needs the possibility to terminate itselfs.
            # ToDo refactoring needed
            if "MSUIWebMapService" in repr(result) and not result.contents:
                raise NoLayersError
            else:
                self.finished.emit(result)
        except Exception as e:
            self.failed.emit(e)
        finally:
            try:
                Worker.workers.remove(self)
            except KeyError:
                pass

    @staticmethod
    def create(function, on_success=None, on_failure=None, start=True):
        """
        Create, connect and directly execute a Worker in a single line.
        Inspired by QThread.create only available in C++17.
        """
        worker = Worker(function)
        if on_success:
            worker.finished.connect(on_success)
        if on_failure:
            worker.failed.connect(on_failure)
        if start:
            worker.start()
        return worker

    @staticmethod
    def _update_gui():
        """
        Iterate through all windows and update them.
        Useful for when a thread modifies the GUI.
        Happens automatically at the end of a Worker.
        """
        for window in QtWidgets.QApplication.allWindows():
            window.requestUpdate()


class Updater(QtCore.QObject):
    """
    Checks for a newer versions of MSS and provide functions to install it asynchronously.
    Only works if conda is installed.
    """
    on_update_available = QtCore.pyqtSignal([str, str])
    on_update_finished = QtCore.pyqtSignal()
    on_log_update = QtCore.pyqtSignal([str])
    on_status_update = QtCore.pyqtSignal([str])

    def __init__(self, parent=None):
        super(Updater, self).__init__(parent)
        self.is_git_env = False
        self.new_version = None
        self.old_version = None
        # we are using the installer version of the env
        self.conda_prefix = os.getenv("CONDA_PREFIX")
        if self.conda_prefix is not None:
            self.command = os.path.join(self.conda_prefix, 'bin', "conda")
            mamba_cmd = os.path.join(self.conda_prefix, 'bin', 'mamba')
            # Check if mamba is installed in the env
            try:
                subprocess.run([mamba_cmd], startupinfo=subprocess_startupinfo(),
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                self.command = mamba_cmd
            except FileNotFoundError:
                pass
        else:
            self.command = "conda"

        # pyqtSignals don't work without an application eventloop running
        if QtCore.QCoreApplication.startingUp():
            self.on_update_available = NonQtCallback()
            self.on_update_finished = NonQtCallback()
            self.on_log_update = NonQtCallback()
            self.on_status_update = NonQtCallback()

    def run(self):
        """
        Starts the updater process
        """
        Worker.create(self._check_version)

    def _check_version(self):
        """
        Checks if conda search has a newer version of MSS
        """
        # Don't notify on updates if mss is in a git repo, as you are most likely a developer
        try:
            git = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                                 startupinfo=subprocess_startupinfo(),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, encoding="utf8")
            if "true" in git.stdout:
                self.is_git_env = True
        except FileNotFoundError:
            pass

        # Return if conda is not installed. conda is fallback of mamba
        try:
            subprocess.run([self.command], startupinfo=subprocess_startupinfo(),
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except FileNotFoundError:
            return

        self.on_status_update.emit("Checking for updates...")

        # Check if "search mss" yields a higher version than the currently running one
        search = self._execute_command(f"{self.command} search mss")
        self.new_version = search.split("\n")[-2].split()[1]
        c_list = self._execute_command(f"{self.command} list -f mss")
        self.old_version = c_list.split("\n")[-2].split()[1]
        if any(c.isdigit() for c in self.new_version):
            if self.new_version > self.old_version:
                self.on_status_update.emit("Your version of MSS is outdated!")
                self.on_update_available.emit(self.old_version, self.new_version)
            else:
                self.on_status_update.emit("Your MSS is up to date.")

    def _restart_msui(self):
        """
        Restart msui with all the same parameters, not entirely
        safe in case parameters change in higher versions, or while debugging
        """
        command = [sys.executable.split(os.sep)[-1]] + sys.argv
        if os.name == "nt" and not command[1].endswith(".py"):
            command[1] += "-script.py"
        os.execv(sys.executable, command)

    def _try_updating(self):
        """
        Execute 'conda/mamba install mss=newest python -y' and return if it worked or not
        """
        self.on_status_update.emit("Trying to update MSS...")
        self._execute_command(f"{self.command} install mss={self.new_version} python -y")
        if self._verify_newest_mss():
            return True

        return False

    def _update_mss(self):
        """
        Try to install MSS' newest version
        """
        if not self._try_updating():
            self.on_status_update.emit("Update failed. Please try it manually or by creating a new environment!")
        else:
            self.on_update_finished.emit()
            self.on_status_update.emit("Update successful. Please restart MSS.")

    def _verify_newest_mss(self):
        """
        Return if the newest mss exists in the environment or not
        """
        verify = self._execute_command(f"{self.command} list -f mss")
        if self.new_version in verify:
            return True

        return False

    def _execute_command(self, command):
        """
        Handles proper execution of conda subprocesses and logging
        """
        process = subprocess.Popen(command.split(),
                                   startupinfo=subprocess_startupinfo(),
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   encoding="utf8")
        self.on_log_update.emit(" ".join(process.args) + "\n")

        text = ""
        for line in process.stdout:
            self.on_log_update.emit(line)
            text += line

        # Happens e.g. on connection errors during installation attempts
        if "An unexpected error has occurred. Conda has prepared the above report" in text:
            raise RuntimeError("Something went wrong! Can't safely continue to update.")
        else:
            return text

    def update_mss(self):
        """
        Installs the newest mss version
        """
        def on_failure(e: Exception):
            self.on_status_update.emit("Update failed, please do it manually.")
            self.on_log_update.emit(str(e))

        Worker.create(self._update_mss, on_failure=on_failure)


class NonQtCallback:
    """
    Small mock of pyqtSignal to work without the QT eventloop.
    Callbacks are run on the same thread as the caller of emit, as opposed to the caller of connect.
    Keep in mind if this causes issues.
    """

    def __init__(self):
        self.callbacks = []

    def connect(self, function):
        self.callbacks.append(function)

    def emit(self, *args):
        for cb in self.callbacks:
            try:
                cb(*args)
            except Exception:
                pass


sys.excepthook = excepthook
