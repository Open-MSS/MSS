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
import shutil
import tempfile

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

    def __init__(self, parent=None):
        super(Updater, self).__init__(parent)
        self.environment = None
        self.is_git_env = False
        self.new_version = None
        self.old_version = __version__
        self.backup_dir = os.path.join(tempfile.gettempdir(), "updater_backup")

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
                                 stderr=subprocess.STDOUT, encoding="utf8")
            if "true" in git.stdout:
                self.is_git_env = True
                return
        except FileNotFoundError:
            pass

        # Return if conda is not installed
        try:
            subprocess.run(["conda"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except FileNotFoundError:
            return

        self.on_status_update.emit("Checking for updates...")

        # Check if "search mss" yields a higher version than the currently running one
        search = subprocess.run(["conda", "search", "mss"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                encoding="utf8")
        if search.returncode == 0:
            self.new_version = search.stdout.split("\n")[-2].split()[1]
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

    def _try_updating(self):
        command = "conda"
        try:
            subprocess.run(["mamba"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            command = "mamba"
        except FileNotFoundError:
            pass

        self.on_status_update.emit("Trying to update MSS...")
        # Try specifically installing newest mss and unlocking python version
        subprocess.run([command, "install", f"mss={self.new_version}", "python", "-y"])
        if self._verify_newest_mss(env=None, path=self.current_path):
            return True

        # Easy updating failed
        return False

    def _try_environment_replace(self):
        """
        Replace the current working environment with a fresh one containing the newest MSS
        Ideally this method is never called
        """
        self.on_progress_update.emit(0)
        self._execute_in_env("conda config --add channels conda-forge")

        self.on_status_update.emit("Creating temporary environment...")
        self._execute_in_env("conda create -n mss-tmp-env mamba -y")
        self.on_progress_update.emit(10)

        self.on_status_update.emit("Installing latest MSS...")
        self._execute_in_env(f"mamba install mss={self.new_version} python -y", "mss-tmp-env")
        self.on_progress_update.emit(45)

        if not self._verify_newest_mss():
            self._execute_in_env("conda remove -n mss-tmp-env --all -y")
            return False

        self.on_status_update.emit("Updating packages...")
        self._execute_in_env("mamba update --all -y", "mss-tmp-env")
        self.on_progress_update.emit(50)

        self.on_status_update.emit("Replacing environment, please don't close MSS!")
        # Backup current environment
        shutil.copytree(self.current_path, self.backup_dir, dirs_exist_ok=True)
        self._execute_in_env(f"conda create -p {self.current_path} --clone mss-tmp-env -y")
        self.on_progress_update.emit(95)
        if not self._verify_newest_mss(env=None, path=self.current_path):
            self._execute_in_env(f"conda remove -p {self.current_path} --all -y")
            self._execute_in_env("conda remove -n mss-tmp-env --all -y")
            shutil.move(self.backup_dir, self.current_path)
            return False

        self.on_status_update.emit("Deleting temporary environment...")
        shutil.rmtree(self.backup_dir, ignore_errors=True)
        self._execute_in_env("conda remove -n mss-tmp-env --all -y")

        return True

    def _update_mss(self):
        """
        Try to install MSS' newest version
        """
        self._set_base_env_path()

        if not self._try_updating() and not self._try_environment_replace():
            self.on_status_update.emit("Update failed, please do it manually.")
            self.on_update_failed.emit()
        else:
            self.on_progress_update.emit(100)
            self.on_status_update.emit("Update finished. Please restart MSS.")
            self.on_update_finished.emit()

    def _verify_newest_mss(self, env="mss-tmp-env", path=None):
        verify = self._execute_in_env("conda list mss", env=env, path=path)
        if self.new_version in verify.stdout:
            return True
        return False

    def _set_base_env_path(self):
        env_list = subprocess.run(["conda", "env", "list"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  encoding="utf8")
        self.base_path = next(line for line in env_list.stdout.split("\n") if "#" not in line).split()[-1]
        self.current_path = next(line for line in env_list.stdout.split("\n") if "*" in line).split()[-1]

    def _execute_in_env(self, command, env=None, path=None, silent=True):
        """
        Executes a subprocess from the base conda environment
        """
        conda_command = ["conda", "run", "--live-stream", "-p", self.base_path]
        if env is not None:
            conda_command.extend(["conda", "run", "--live-stream", "-n", env])
        elif path is not None:
            conda_command.extend(["conda", "run", "--live-stream", "-p", path])
        conda_command.extend(command.split())
        if silent:
            return subprocess.run(conda_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf8")
        else:
            return subprocess.run(conda_command, encoding="utf8")

    def update_mss(self):
        """
        Installs the newest mss version
        """
        def on_failure(e):
            self.on_status_update.emit("Update failed, please do it manually.")
            self.on_update_failed.emit()

        Worker.create(self._update_mss, on_failure=on_failure)
