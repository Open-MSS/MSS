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
from PyQt5 import QtCore, QtWidgets


class Updater(QtCore.QObject):
    on_update_available = QtCore.pyqtSignal([str, str])
    on_progress_update = QtCore.pyqtSignal([int])
    on_update_finished = QtCore.pyqtSignal()
    on_status_update = QtCore.pyqtSignal([str])

    def __init__(self, parent):
        super(Updater, self).__init__()
        self.parent = parent
        self.updater_worker = None
        self.environment = None
        self.command = None
        self.new_version = None
        self.old_version = __version__
        self.version_checker = Worker.create(self.check_version)

    def check_version(self):
        """
        Checks if conda search has a newer version of MSS
        """
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

        search = subprocess.run([self.command, "search", "mss"], stdout=subprocess.PIPE)
        if search.returncode == 0:
            self.new_version = str(search.stdout, "utf-8").split("\n")[-2].split()[1]
            if any(c.isdigit() for c in self.new_version):
                if self.new_version > self.old_version:
                    self.on_update_available.emit(self.old_version, self.new_version)

    def restart_mss(self):
        """
        Restart mss with all the same parameters
        """
        QtCore.QCoreApplication.quit()
        os.execv(sys.executable, [sys.executable.split(os.sep)[-1]] + sys.argv)

    def update_info(self, updater):
        """
        Iterates through a conda command downloading things, and updates on the progress
        """
        total_download = 0
        downloaded = 0
        download_start = False
        for line in updater.stdout:
            line = line.replace("\n", "")
            info = line.split()
            print(line)
            if "Total download:" in line:
                print("Total Download info", info)
                factor = 0.001 if info[-1] == "KB" else 1000 if info[-1] == "GB" else 1
                total_download = int(float(info[-2]) * factor)
                download_start = True
            elif "Finished" in line:
                print("Download info", info)
                factor = 0.001 if info[-3] == "KB" else 1000 if info[-3] == "GB" else 1
                downloaded += int(float(info[-4]) * factor)
                self.on_progress_update.emit(int((downloaded / total_download) * 100))

    def install_and_update(self):
        """
        Create a temporary new conda environment containing the newest mss
        """
        subprocess.run([self.command, "config", "--add", "channels", "conda-forge"])

        self.on_status_update.emit("Installing latest MSS...")
        updater = subprocess.Popen([self.command, "install", f"mss={self.new_version}", "-y"],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
        self.update_info(updater)

        self.on_status_update.emit("Updating packages...")
        updater = subprocess.Popen([self.command, "update", "--all", "-y"],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
        self.update_info(updater)

        verify = subprocess.run([self.command, "list", "mss"], stdout=subprocess.PIPE,
                                encoding="utf-8")
        if self.new_version in verify:
            self.on_update_finished.emit()
        else:
            self.on_status_update.emit("Updating failed...")

    def update_mss(self):
        """
        Installs the newest mss version
        """
        self.updater_worker = Worker.create(self.install_and_update)
