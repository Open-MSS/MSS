"""
    mslib.msui.updater
    ~~~~~~~~~~~~~~~~~~~

    This UI interface for the updater util, handles detection of an outdated mss version and automatic updating.

    This file is part of MSS.

    :copyright: Copyright 2021 May Bär
    :copyright: Copyright 2021-2023 by the MSS team, see AUTHORS.
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

from PyQt5 import QtCore, QtWidgets, QtGui

from mslib.utils.qt import Updater
from mslib.msui.qt5 import ui_updater_dialog
from mslib import __version__


class UpdaterUI(QtWidgets.QDialog, ui_updater_dialog.Ui_Updater):
    """
    Checks for a newer versions of MSS and installs it.
    Only works if conda is installed and MSS isn't inside a git repo.
    """
    on_update_available = QtCore.pyqtSignal([str, str])

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.hide()
        self.labelVersion.setText(f"Newest Version: {__version__}")
        self.updater = None
        try:
            self.updater = Updater()
        except ModuleNotFoundError as ex:
            # https://github.com/Open-MSS/MSS/issues/1409#issuecomment-1200946622
            logging.error("unexpected error in updater: %s %s in version: %s", type(ex), ex, __version__)

        if self.updater is not None:
            monospace = QtGui.QFont("non-existent")
            monospace.setStyleHint(QtGui.QFont.Monospace)
            self.output.setFont(monospace)
            self.updater.on_log_update.connect(lambda s: (self.output.insertPlainText(s),
                                                          self.output.verticalScrollBar().setSliderPosition(
                                                              self.output.verticalScrollBar().maximum())))
            self.updater.on_status_update.connect(self.statusLabel.setText)
            self.updater.on_update_available.connect(self.notify_on_update)
            self.updater.on_update_finished.connect(lambda: self.btRestart.setEnabled(True))
            self.btUpdate.clicked.connect(lambda: (self.updater.update_mss(), self.btUpdate.setEnabled(False)))
            self.btRestart.clicked.connect(self.updater._restart_msui)
            self.updater.run()

    def notify_on_update(self, old, new):
        """
        Asks the user if they want to update MSS
        """
        self.btUpdate.setEnabled(True)
        self.labelVersion.setText(f"Newest Version: {new}")
        if not self.updater.is_git_env:
            ret = QtWidgets.QMessageBox.information(
                self, "Mission Support System",
                f"MSS can be updated from {old} to {new}\nDo you want to update?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No)
            if ret == QtWidgets.QMessageBox.Yes:
                self.show()
                self.btUpdate.click()
