"""
    mslib.msui.multilayers
    ~~~~~~~~~~~~~~~~~~~

    This module handles detection of an outdated mss version and automatic updating.

    This file is part of mss.

    :copyright: Copyright 2021 May Bär
    :copyright: Copyright 2021 by the mss team, see AUTHORS.
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
import subprocess
import sys
import os

from mslib import __version__
from mslib.utils import Worker
from mslib.msui.mss_qt import ui_updater_dialog
from PyQt5 import QtCore, QtWidgets, QtGui


class Updater(QtWidgets.QDialog, ui_updater_dialog.Ui_Updater):
    """
    Checks for a newer versions of MSS and installs it.
    Only works if conda is installed and MSS isn't inside a git repo.
    """
    on_update_available = QtCore.pyqtSignal([str, str])
    on_log_update = QtCore.pyqtSignal([str])

    def __init__(self, parent=None):
        super(Updater, self).__init__(parent)
        self.setupUi(self)
        self.hide()
        self.environment = None
        self.is_git_env = False
        self.new_version = None
        monospace = QtGui.QFont("non-existent")
        monospace.setStyleHint(QtGui.QFont.Monospace)
        self.output.setFont(monospace)
        self.on_log_update.connect(lambda s: (self.output.insertPlainText(s),
                                              self.output.verticalScrollBar().setSliderPosition(
                                                  self.output.verticalScrollBar().maximum())))
        self.old_version = __version__
        self.btUpdate.clicked.connect(self.update_mss)
        self.btRestart.clicked.connect(self._restart_mss)

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
            git = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, encoding="utf8")
            if "true" in git.stdout:
                self.is_git_env = True
        except FileNotFoundError:
            pass

        # Return if conda is not installed
        try:
            subprocess.run(["conda"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except FileNotFoundError:
            return

        self.statusLabel.setText("Checking for updates...")

        # Check if "search mss" yields a higher version than the currently running one
        search = self._execute_command("conda search mss")
        self.new_version = search.split("\n")[-2].split()[1]
        self.labelVersion.setText(f"Newest Version: {self.new_version}")
        list = self._execute_command("conda list mss")
        self.old_version = list.split("\n")[-2].split()[1]
        if any(c.isdigit() for c in self.new_version):
            if self.new_version > self.old_version:
                self.statusLabel.setText("Your version of MSS is outdated!")
                self.btUpdate.setEnabled(True)
                if not self.is_git_env:
                    self.on_update_available.emit(self.old_version, self.new_version)
            else:
                self.statusLabel.setText("Your MSS is up to date.")

    def _restart_mss(self):
        """
        Restart mss with all the same parameters, not be entirely
        safe in case parameters change in higher versions, or while debugging
        """
        os.execv(sys.executable, [sys.executable.split(os.sep)[-1]] + sys.argv)

    def _try_updating(self):
        """
        Execute 'conda/mamba install mss=newest python -y' and return if it worked or not
        """
        command = "conda"
        try:
            subprocess.run(["mamba"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            command = "mamba"
        except FileNotFoundError:
            pass

        self.statusLabel.setText("Trying to update MSS...")
        self._execute_command(f"{command} install mss={self.new_version} python -y")
        if self._verify_newest_mss():
            return True

        return False

    def _update_mss(self):
        """
        Try to install MSS' newest version
        """
        if not self._try_updating():
            self.statusLabel.setText("Update failed. Please try it manually or by creating a new environment!")
        else:
            self.btRestart.setEnabled(True)
            self.statusLabel.setText("Update successful. Please restart MSS.")

    def _verify_newest_mss(self):
        """
        Return if the newest mss exists in the environment or not
        """
        verify = self._execute_command("conda list mss")
        if self.new_version in verify:
            return True

        return False

    def _execute_command(self, command):
        """
        Handles proper execution of conda subprocesses and logging
        """
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf8")
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
            self.statusLabel.setText("Update failed, please do it manually.")
            self.on_log_update.emit(str(e))

        Worker.create(self._update_mss, on_failure=on_failure)
        self.btUpdate.setEnabled(False)
