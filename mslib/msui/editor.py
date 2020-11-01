# -*- coding: utf-8 -*-
"""

    mslib.msui.editor
    ~~~~~~~~~~~~~~~~~~~~~~

    config ediror for mss_settings.jscon.

    This file is part of mss.

    :copyright: Copyright 2019 Vaibhav Mehra <veb7vmehra@gmail.com>
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
import os
import fs

from mslib.msui.mss_qt import get_open_filename, get_save_filename
from mslib.msui.mss_qt import QtWidgets
from mslib.msui.mss_qt import QtGui
from mslib.msui.mss_qt import QtCore
from PyQt5 import QtPrintSupport
from mslib.msui import constants
from mslib.msui.constants import MSS_CONFIG_PATH
from mslib.msui.icons import icons


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        layout = QtWidgets.QVBoxLayout()
        self.editor = QtWidgets.QPlainTextEdit()  # Could also use a QTextEdit and set self.editor.setAcceptRichText(False)

        # Setup the QTextEdit editor configuration
        fixedfont = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        fixedfont.setPointSize(12)
        self.editor.setFont(fixedfont)

        # self.path holds the path of the currently open file.
        # If none, we haven't got a file open yet (or creating new).
        self.path = constants.MSS_CONFIG_PATH

        layout.addWidget(self.editor)

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)

        file_toolbar = QtWidgets.QToolBar("File")
        file_toolbar.setIconSize(QtCore.QSize(14, 14))
        self.addToolBar(file_toolbar)
        file_menu = self.menuBar().addMenu("&File")

        open_file_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor', 'Folder-new.svg')), "Open file...", self)
        open_file_action.setStatusTip("Open file")
        open_file_action.triggered.connect(self.file_open)
        file_menu.addAction(open_file_action)
        file_toolbar.addAction(open_file_action)

        save_file_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor', 'Document-save.svg')), "Save", self)
        save_file_action.setStatusTip("Save current page")
        save_file_action.triggered.connect(self.file_save)
        file_menu.addAction(save_file_action)
        file_toolbar.addAction(save_file_action)

        saveas_file_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor', 'Document-save-as.svg')), "Save As...", self)
        saveas_file_action.setStatusTip("Save current page to specified file")
        saveas_file_action.triggered.connect(self.file_saveas)
        file_menu.addAction(saveas_file_action)
        file_toolbar.addAction(saveas_file_action)

        print_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor', 'Document-print.svg')), "Print...", self)
        print_action.setStatusTip("Print current page")
        print_action.triggered.connect(self.file_print)
        file_menu.addAction(print_action)
        file_toolbar.addAction(print_action)

        edit_toolbar = QtWidgets.QToolBar("Edit")
        edit_toolbar.setIconSize(QtCore.QSize(16, 16))
        self.addToolBar(edit_toolbar)
        edit_menu = self.menuBar().addMenu("&Edit")

        undo_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor', 'Edit-undo.svg')), "Undo", self)
        undo_action.setStatusTip("Undo last change")
        undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_action)

        redo_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor', 'Edit-redo.svg')), "Redo", self)
        redo_action.setStatusTip("Redo last change")
        redo_action.triggered.connect(self.editor.redo)
        edit_toolbar.addAction(redo_action)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor', 'Edit-cut.svg')), "Cut", self)
        cut_action.setStatusTip("Cut selected text")
        cut_action.triggered.connect(self.editor.cut)
        edit_toolbar.addAction(cut_action)
        edit_menu.addAction(cut_action)

        copy_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor', 'Edit-copy.svg')), "Copy", self)
        copy_action.setStatusTip("Copy selected text")
        copy_action.triggered.connect(self.editor.copy)
        edit_toolbar.addAction(copy_action)
        edit_menu.addAction(copy_action)

        paste_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor', 'Edit-paste.svg')), "Paste", self)
        paste_action.setStatusTip("Paste from clipboard")
        paste_action.triggered.connect(self.editor.paste)
        edit_toolbar.addAction(paste_action)
        edit_menu.addAction(paste_action)

        select_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor', 'Edit-select-all.svg')), "Select all", self)
        select_action.setStatusTip("Select all text")
        select_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(select_action)

        edit_menu.addSeparator()

        wrap_action = QtWidgets.QAction(QtGui.QIcon(icons('config_editor', 'Go-next.svg')), "Wrap text to window", self)
        wrap_action.setStatusTip("Toggle wrap text to window")
        wrap_action.setCheckable(True)
        wrap_action.setChecked(True)
        wrap_action.triggered.connect(self.edit_toggle_wrap)
        edit_menu.addAction(wrap_action)
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
                file_content = file_dir.readtext(file_name)
                self.path = file_path
                self.editor.setPlainText(file_content)
                self.update_title()

    def file_save(self):
        if self.path is None:
            # If we do not have a path, we need to use Save As.
            return self.file_saveas()
        self._save_to_path(self.path)

    def file_saveas(self):
        default_filename = fs.path.join(MSS_CONFIG_PATH, "mss_settings" + ".json")
        path = get_save_filename(self, "Save file", default_filename, "Text documents (*.json)")
        if not path:
            # If dialog is cancelled, will return ''
            return
        self._save_to_path(path)

    def _save_to_path(self, path):
        text = self.editor.toPlainText()
        dir_name, file_name = fs.path.split(path)
        if file_name.endswith('.json'):
            with fs.open_fs(dir_name) as _fs:
                _fs.writetext(file_name, text)
        self.path = path
        self.update_title()

    def file_print(self):
        dlg = QtPrintSupport.QPrintDialog()
        if dlg.exec_():
            self.editor.print_(dlg.printer())

    def update_title(self):
        self.setWindowTitle("%s - Config-Settings" % (os.path.basename(self.path) if self.path else "Untitled"))

    def edit_toggle_wrap(self):
        self.editor.setLineWrapMode( 1 if self.editor.lineWrapMode() == 0 else 0 )

    def closeEvent(self, event):
        self.dialog_critical("If you changed the mss_settings.json please restart the gui")
