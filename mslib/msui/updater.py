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
import tempfile

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
        self.backup_dir = os.path.join(tempfile.gettempdir(), "updater_backup")
        self.btUpdate.clicked.connect(self.update_mss)
        self.btReplace.clicked.connect(lambda: self.update_mss(True))

    def run(self):
        """
        Starts the updater process
        """
        Worker.create(self._check_version)

    def _check_version(self, ignore_git=False):
        """
        Checks if conda search has a newer version of MSS
        """
        # Don't run updates if mss is in a git repo, as you are most likely a developer
        if not ignore_git:
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

        self.statusLabel.setText("Checking for updates...")

        # Check if "search mss" yields a higher version than the currently running one
        search = self._execute_command("conda search mss", local=True)
        self.new_version = search.split("\n")[-2].split()[1]
        list = self._execute_command("conda list mss", local=True)
        self.old_version = list.split("\n")[-2].split()[1]
        self.labelVersion.setText(f"Newest Version: {self.new_version}")
        if any(c.isdigit() for c in self.new_version):
            if self.new_version > self.old_version:
                self.statusLabel.setText("Your version of MSS is outdated!")
                self.btUpdate.setEnabled(True)
                self.on_update_available.emit(self.old_version, self.new_version)
            else:
                self.statusLabel.setText("Your MSS is up to date.")

    def _restart_mss(self):
        """
        Restart mss with all the same parameters, might not be entirely safe
        """
        QtCore.QCoreApplication.quit()
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
        self._execute_command(f"{command} install mss={self.new_version} python -y", local=True)
        if self._verify_newest_mss(env=None):
            return True

        return False

    def _try_environment_replace(self):
        """
        Replace the current working environment with a fresh one containing the newest MSS
        Ideally this method is never called
        """
        self._execute_command("conda config --add channels conda-forge")
        packages = {package.split()[0] for package in self._execute_command("conda list", local=True).split("\n")
                    if package != "" and package[0] != "#"}

        self.statusLabel.setText("Creating temporary environment...")
        self._execute_command("conda create -n mss-tmp-env mamba -y")

        self.statusLabel.setText("Installing latest MSS...")
        self._execute_command(f"mamba install mss={self.new_version} python -y", "mss-tmp-env")

        if not self._verify_newest_mss():
            self._execute_command("conda remove -n mss-tmp-env --all -y")
            return False

        self.statusLabel.setText("Installing additional packages...")
        tmp_packages = {package.split()[0] for package in self._execute_command("conda list", "mss-tmp-env").split("\n")
                        if package != "" and package[0] != "#"}
        to_install = packages.difference(tmp_packages)
        if len(to_install) > 0:
            self._execute_command(f"mamba install {' '.join(to_install)} -y", "mss-tmp-env")

        self.statusLabel.setText("Updating packages...")
        self._execute_command("mamba update --all -y", "mss-tmp-env")

        self.statusLabel.setText("Backing up environment, please don't close MSS!")
        self._move_environment()
        self.statusLabel.setText("Replacing environment, please don't close MSS!")
        self._execute_command(f"conda create -p {self.current_path} --clone mss-tmp-env -y")
        if not self._verify_newest_mss(env=None):
            self.statusLabel.setText("Restoring backup, please don't close MSS!")
            self._restore_environment()
            self._execute_command("conda remove -n mss-tmp-env --all -y")
            return False

        self.statusLabel.setText("Cleaning up, please don't close MSS!")
        self._delete_backup()
        self._execute_command("conda remove -n mss-tmp-env --all -y")
        return True

    def _update_mss(self, replace=False):
        """
        Try to install MSS' newest version
        """
        self._set_base_env_path()

        if not replace:
            if not self._try_updating():
                self.statusLabel.setText("Update failed. Please try it manually or try replacing the environment!")
                self.btReplace.setEnabled(True)
            else:
                self.statusLabel.setText("Update successful. Please restart MSS.")
        else:
            if not self._try_environment_replace():
                self.statusLabel.setText("Update failed. Please try it manually!")
            else:
                self.statusLabel.setText("Update successful. Please restart MSS.")

    def _verify_newest_mss(self, env="mss-tmp-env"):
        """
        Return if the newest mss exists in the environment or not
        """
        verify = self._execute_command("conda list mss", env=env, local=True if env is None else False)
        if self.new_version in verify:
            return True

        return False

    def _set_base_env_path(self):
        """
        Save the path of the base environment and current environment-
        The output of env list is masked for executed scripts to pretend the current environment is base
        """
        env_list = self._execute_command("conda env list", local=True)
        self.base_path = next(line for line in env_list.split("\n") if "#" not in line).split()[-1]
        self.current_path = next(line for line in env_list.split("\n") if "*" in line).split()[-1]

    def _execute_command(self, command, env=None, local=False, return_text=True):
        """
        Handles proper execution of conda subprocesses and logging
        """
        if not local:
            conda_command = ["conda", "run", "--no-capture-output", "-p", self.base_path]
            if env is not None:
                conda_command.extend(["conda", "run", "--no-capture-output", "-n", env])
            conda_command.extend(command.split())
            process = subprocess.Popen(conda_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf8")
        else:
            process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       encoding="utf8")
        self.on_log_update.emit(" ".join(process.args) + "\n")
        if not return_text:
            return process
        elif "install" in process.args or "update" in process.args:
            return self._update_download_progress(process)
        else:
            text = ""
            for line in process.stdout:
                self.on_log_update.emit(line)
                text += line
            return text

    def _move_environment(self):
        self._delete_backup()
        if os.name != "nt":
            self._execute_command(f"mv -v {self.current_path} {self.backup_dir}", local=True)
        else:
            self._execute_command(f"move {self.current_path} {self.backup_dir}", local=True)

    def _delete_backup(self):
        if os.name != "nt":
            self._execute_command(f"rm -r -v -f {self.backup_dir}", local=True)
        else:
            self._execute_command(f"rmdir {self.backup_dir} /s /q", local=True)

    def _restore_environment(self):
        self._execute_command(f"conda remove -p {self.current_path} --all -y")
        if os.name != "nt":
            self._execute_command(f"mv -v {self.backup_dir} {self.current_path}", local=True)
        else:
            self._execute_command(f"move {self.backup_dir} {self.current_path}", local=True)

    def _update_download_progress(self, process):
        """
        Updates the progress bar to reflect the progress of the update or install
        """
        self.progressBar.setValue(0)
        total_download = 0
        downloaded = 0
        output = ""
        for line in process.stdout:
            if line.startswith(""):
                continue
            output += line
            self.on_log_update.emit(line)
            line = line.replace("\n", "")
            info = line.split()
            if "Total download:" in line:
                factor = 10**3 if info[-1] == "KB" else 10**6 if info[-1] == "MB" else 10**9 if info[-1] == "GB" else 1
                total_download = int(float(info[-2]) * factor)
            elif "Finished" in line:
                factor = 10**3 if info[-3] == "KB" else 10**6 if info[-3] == "MB" else 10**9 if info[-3] == "GB" else 1
                downloaded += int(float(info[-4]) * factor)
                self.progressBar.setValue(int((downloaded / total_download) * 100))
        self.progressBar.setValue(100)
        return output

    def update_mss(self, replace=False):
        """
        Installs the newest mss version
        """
        def on_failure(e):
            self.statusLabel.setText("Update failed, please do it manually.")

        Worker.create(lambda: self._update_mss(replace), on_failure=on_failure)
        self.btUpdate.setEnabled(False)
        self.btReplace.setEnabled(False)
