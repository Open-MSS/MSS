# -*- coding: utf-8 -*-
"""

    mslib.msui.editor
    ~~~~~~~~~~~~~~~~~~~~~~

    config editor for mss_settings.json.

    This file is part of mss.

    :copyright: Copyright 2020 Vaibhav Mehra <veb7vmehra@gmail.com>
    :copyright: Copyright 2020 by the mss team, see AUTHORS.
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
import fs
import logging

from mslib.msui.mss_qt import get_open_filename, get_save_filename
from PyQt5 import QtWidgets, QtGui, QtCore, QtPrintSupport
from mslib.msui import constants
from mslib.msui.constants import MSS_CONFIG_PATH
from mslib.msui.icons import icons


class EditorMainWindow(QtWidgets.QMainWindow):
    name = "MSSEditor"
    identifier = None

    def __init__(self, parent=None):
        super(EditorMainWindow, self).__init__(parent)
        self.path = None

        self.file_content = None
        self.layout = QtWidgets.QVBoxLayout()
        # Could also use a QTextEdit and set self.editor.setAcceptRichText(False)
        self.editor = QtWidgets.QPlainTextEdit()

        # Load mss_settings.json (if already exists)
        self.mss_path = fs.path.join(MSS_CONFIG_PATH, "mss_settings" + ".json")
        if fs.open_fs(MSS_CONFIG_PATH).exists("mss_settings.json"):
            file_name = fs.path.basename(self.mss_path)
            with fs.open_fs(fs.path.dirname(self.mss_path)) as file_dir:
                self.file_content = file_dir.readtext(file_name)
                self.editor.setPlainText(self.file_content)
                self.update_title()

        # Setup the QTextEdit editor configuration
        fixedfont = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        fixedfont.setPointSize(12)
        self.editor.setFont(fixedfont)

        # self.path holds the path of the currently open file.
        # If none, we haven't got a file open yet (or creating new).
        self.path = constants.MSS_CONFIG_PATH
        self.layout.addWidget(self.editor)

        self.container = QtWidgets.QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)

        self.file_toolbar = QtWidgets.QToolBar("File")
        self.file_toolbar.setIconSize(QtCore.QSize(14, 14))
        self.addToolBar(self.file_toolbar)
        self.file_menu = self.menuBar().addMenu("&File")

        self.open_file_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                                    'Folder-new.svg')), "Open file...", self)
        self.open_file_action.setStatusTip("Open file")
        self.open_file_action.triggered.connect(self.file_open)
        self.file_menu.addAction(self.open_file_action)
        self.file_toolbar.addAction(self.open_file_action)

        self.save_file_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                                    'Document-save.svg')), "Save", self)
        self.save_file_action.setStatusTip("Save current page")
        self.save_file_action.triggered.connect(self.file_save)
        self.file_menu.addAction(self.save_file_action)
        self.file_toolbar.addAction(self.save_file_action)

        self.saveas_file_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                                      'Document-save-as.svg')), "Save As...", self)
        self.saveas_file_action.setStatusTip("Save current page to specified file")
        self.saveas_file_action.triggered.connect(self.file_saveas)
        self.file_menu.addAction(self.saveas_file_action)
        self.file_toolbar.addAction(self.saveas_file_action)

        self.print_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                                'Document-print.svg')), "Print...", self)
        self.print_action.setStatusTip("Print current page")
        self.print_action.triggered.connect(self.file_print)
        self.file_menu.addAction(self.print_action)
        self.file_toolbar.addAction(self.print_action)

        self.edit_toolbar = QtWidgets.QToolBar("Edit")
        self.edit_toolbar.setIconSize(QtCore.QSize(16, 16))
        self.addToolBar(self.edit_toolbar)
        self.edit_menu = self.menuBar().addMenu("&Edit")

        self.undo_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                               'Edit-undo.svg')), "Undo", self)
        self.undo_action.setStatusTip("Undo last change")
        self.undo_action.triggered.connect(self.editor.undo)
        self.edit_menu.addAction(self.undo_action)

        self.redo_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                               'Edit-redo.svg')), "Redo", self)
        self.redo_action.setStatusTip("Redo last change")
        self.redo_action.triggered.connect(self.editor.redo)
        self.edit_toolbar.addAction(self.redo_action)
        self.edit_menu.addAction(self.redo_action)

        self.edit_menu.addSeparator()

        self.cut_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                              'Edit-cut.svg')), "Cut", self)
        self.cut_action.setStatusTip("Cut selected text")
        self.cut_action.triggered.connect(self.editor.cut)
        self.edit_toolbar.addAction(self.cut_action)
        self.edit_menu.addAction(self.cut_action)

        self.copy_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                               'Edit-copy.svg')), "Copy", self)
        self.copy_action.setStatusTip("Copy selected text")
        self.copy_action.triggered.connect(self.editor.copy)
        self.edit_toolbar.addAction(self.copy_action)
        self.edit_menu.addAction(self.copy_action)

        self.paste_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                                'Edit-paste.svg')), "Paste", self)
        self.paste_action.setStatusTip("Paste from clipboard")
        self.paste_action.triggered.connect(self.editor.paste)
        self.edit_toolbar.addAction(self.paste_action)
        self.edit_menu.addAction(self.paste_action)

        self.select_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                                 'Edit-select-all.svg')), "Select all", self)
        self.select_action.setStatusTip("Select all text")
        self.select_action.triggered.connect(self.editor.selectAll)
        self.edit_menu.addAction(self.select_action)

        self.edit_menu.addSeparator()

        self.wrap_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor',
                                                               'Go-next.svg')), "Wrap text to window", self)
        self.wrap_action.setStatusTip("Toggle wrap text to window")
        self.wrap_action.setCheckable(True)
        self.wrap_action.setChecked(True)
        self.wrap_action.triggered.connect(self.edit_toggle_wrap)
        self.edit_menu.addAction(self.wrap_action)
        self.update_title()
        self.show()

    def dialog_critical(self, s):
        dlg = QtWidgets.QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QtWidgets.QMessageBox.Critical)
        dlg.show()

    def file_open(self):
        file_path = get_open_filename(self, "Open file", MSS_CONFIG_PATH, "Text documents (*.json)")
        if file_path is not None:
            file_name = fs.path.basename(file_path)
            with fs.open_fs(fs.path.dirname(file_path)) as file_dir:
                self.file_content = file_dir.readtext(file_name)
                self.path = file_path
                self.editor.setPlainText(self.file_content)
                self.update_title()

    def file_save(self):
        if self.path is None:
            # If we do not have a path, we need to use Save As.
            return self.file_saveas()
        self._save_to_path()

    def file_saveas(self):
        default_filename = fs.path.join(MSS_CONFIG_PATH, "mss_settings" + ".json")
        self.path = get_save_filename(self, "Save file", default_filename, "Text documents (*.json)")
        if not self.path:
            # If dialog is cancelled, will return ''
            return
        self._save_to_path()

    def _save_to_path(self):
        logging.debug("save config file to: %s" % self.path)
        text = self.editor.toPlainText()
        dir_name, file_name = fs.path.split(self.path)
        if file_name.endswith('.json'):
            with fs.open_fs(dir_name) as _fs:
                _fs.writetext(file_name, text)
        self.update_title()

    def file_print(self):
        dlg = QtPrintSupport.QPrintDialog()
        if dlg.exec_():
            self.editor.print_(dlg.printer())

    def update_title(self):
        self.setWindowTitle("%s - Config-Settings" % (fs.path.basename(self.path) if self.path else "Untitled"))

    def edit_toggle_wrap(self):
        self.editor.setLineWrapMode(1 if self.editor.lineWrapMode() == 0 else 0)

    def closeEvent(self, event):
        ret = QtWidgets.QMessageBox.critical(
            self, self.tr("Save changes to mss_settings.json?"),
            self.tr("If you changed the mss_settings.json please restart the gui"),
            QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Ignore, QtWidgets.QMessageBox.Save)

        if ret == QtWidgets.QMessageBox.Save:
            self.file_save()
            event.accept()
        else:
            event.accept()
