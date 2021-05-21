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
from PyQt5 import QtCore


class Updater(QtCore.QObject):
    """
    Checks for a newer versions of MSS and installs it.
    Only works if conda is installed and MSS isn't inside a git repo.
    """
    on_update_available = QtCore.pyqtSignal([str, str])
    on_progress_update = QtCore.pyqtSignal([int])
    on_update_finished = QtCore.pyqtSignal()
    on_update_failed = QtCore.pyqtSignal()
    on_status_update = QtCore.pyqtSignal([str])

    def __init__(self, parent):
        super(Updater, self).__init__()
        self.parent = parent
        self.updater_worker = None
        self.environment = None
        self.command = None
        self.is_git_env = False
        self.new_version = None
        self.old_version = __version__
        self.worker = None

    def run(self):
        """
        Starts the updater process
        """
        Worker.create(self._check_version)

    def _check_version(self):
        """
        Checks if conda search has a newer version of MSS
        """
        # Don't run updates if mss is in a git repo, as you are most likely a developer
        try:
            git = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], stdout=subprocess.PIPE,
                                 encoding="utf8")
            if "true" in git.stdout:
                self.is_git_env = True
                return
        except FileNotFoundError:
            pass

        # Determine if mamba or conda should be used initially
        try:
            subprocess.run(["mamba"], stdout=subprocess.PIPE)
            self.command = "mamba"
        except FileNotFoundError:
            try:
                subprocess.run(["conda"], stdout=subprocess.PIPE)
                self.command = "conda"
            except FileNotFoundError:
                return

        self.on_status_update.emit("Checking for updates...")

        # Check if "search mss" yields a higher version than the currently running one
        search = subprocess.run([self.command, "search", "mss"], stdout=subprocess.PIPE)
        if search.returncode == 0:
            self.new_version = str(search.stdout, "utf-8").split("\n")[-2].split()[1]
            if any(c.isdigit() for c in self.new_version):
                if self.new_version > self.old_version:
                    self.on_status_update.emit("Your version of MSS is outdated!")
                    self.on_update_available.emit(self.old_version, self.new_version)
                else:
                    self.on_status_update.emit("Your MSS is up to date.")

    def _restart_mss(self):
        """
        Restart mss with all the same parameters, might not be entirely safe
        """
        QtCore.QCoreApplication.quit()
        os.execv(sys.executable, [sys.executable.split(os.sep)[-1]] + sys.argv)

    def _update_info(self, updater):
        """
        Iterates through a conda/mamba download, and updates on the total progress
        """
        total_download = 0
        downloaded = 0
        for line in updater.stdout:
            line = line.replace("\n", "")
            info = line.split()
            print(line)
            if "Total download:" in line:
                print("Total Download info", info)
                factor = 0.001 if info[-1] == "KB" else 1000 if info[-1] == "GB" else 1
                total_download = int(float(info[-2]) * factor)
            elif "Finished" in line:
                print("Download info", info)
                factor = 0.001 if info[-3] == "KB" else 1000 if info[-3] == "GB" else 1
                downloaded += int(float(info[-4]) * factor)
                self.on_progress_update.emit(int((downloaded / total_download) * 100))

    def _install_and_update(self):
        """
        Try to install MSS' newest version and update all packages
        """
        subprocess.run([self.command, "config", "--add", "channels", "conda-forge"])

        self.on_status_update.emit("Installing latest MSS...")
        updater = subprocess.Popen([self.command, "install", f"mss={self.new_version}", "-y"],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
        self.update_info(updater)

        # Try again with conda instead of mamba, if installing the newest MSS failed
        if not self.verify_newest_mss():
            if self.command == "mamba":
                self.on_status_update.emit("Installing latest MSS...")
                updater = subprocess.Popen(["conda", "install", f"mss={self.new_version}", "-y"],
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
                self.update_info(updater)

                if not self.verify_newest_mss():
                    self.failed()
            else:
                self.failed()

        self.on_status_update.emit("Updating packages...")
        updater = subprocess.Popen([self.command, "update", "--all", "-y"],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
        self.update_info(updater)

        self.on_status_update.emit("Update finished. Please restart MSS.")
        self.on_update_finished.emit()

    def _verify_newest_mss(self):
        verify = subprocess.run([self.command, "list", "mss"], stdout=subprocess.PIPE, encoding="utf-8")
        if self.new_version in verify.stdout:
            return True
        return False

    def _failed(self):
        self.on_status_update.emit("Auto-Updating failed, please follow the steps provided here "
                                   "https://mss.readthedocs.io/en/stable/installation.html#conda-forge-channel")
        self.on_update_failed.emit()

    def update_mss(self):
        """
        Installs the newest mss version
        """
        Worker.create(self.install_and_update)
