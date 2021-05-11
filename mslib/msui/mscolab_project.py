# -*- coding: utf-8 -*-
"""

    mslib.msui.mscolab_project
    ~~~~~~~~~~~~~~~~~~~~~

    Mscolab project window, to display chat, file change

    This file is part of mss.

    :copyright: 2019 Shivashis Padhi
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
import datetime
import json

import fs
import requests
from markdown import Markdown
from markdown.extensions import Extension
from werkzeug.urls import url_join

from mslib.mscolab.models import MessageType
from PyQt5 import Qt, QtCore, QtGui, QtWidgets
from mslib.msui.mss_qt import get_open_filename, get_save_filename
from mslib.msui.qt5 import ui_mscolab_project_window as ui
from mslib.utils import config_loader, show_popup


# We need to override the KeyPressEvent in QTextEdit to disable the default behaviour of enter key.
class MessageTextEdit(QtWidgets.QTextEdit):
    def keyPressEvent(self, event):
        # Shift + Enter for new line
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter) and event.modifiers() & QtCore.Qt.ShiftModifier:
            cursor = self.textCursor()
            cursor.insertText("\n")
            self.setTextCursor(cursor)
            return
        # Only Enter for send/edit message
        elif event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            chat_window = self.parent().parent().parent()
            if chat_window.active_edit_id is None:
                chat_window.send_message()
            else:
                chat_window.edit_message()
            return
        super().keyPressEvent(event)


class MSColabProjectWindow(QtWidgets.QMainWindow, ui.Ui_MscolabProject):
    """Derives QMainWindow to provide some common functionality to all
       MSUI view windows.
    """
    name = "MSColab Project Window"
    identifier = None

    viewCloses = QtCore.pyqtSignal(name="viewCloses")
    reloadWindows = QtCore.pyqtSignal(name="reloadWindows")

    def __init__(self, token, p_id, user, project_name, access_level, conn, parent=None,
                 mscolab_server_url=config_loader(dataset="default_MSCOLAB")):
        """
        token: access_token
        p_id: project id
        user: logged in user
        project_name: active project name,
        access_level: access level of user logged in
        conn: to send messages, recv messages, if a direct slot-signal can't be setup
            to be connected at parents'
        parent: widget parent
        mscolab_server_url: server url for mscolab
        """
        super(MSColabProjectWindow, self).__init__(parent)
        self.setupUi(self)

        self.mscolab_server_url = mscolab_server_url
        self.token = token
        self.user = user
        self.p_id = p_id
        self.project_name = project_name
        self.conn = conn
        self.access_level = access_level
        self.text = ""
        self.attachment = None
        self.attachment_type = None
        self.active_edit_id = None
        self.active_message_reply = None
        self.current_search_index = None
        self.markdown = Markdown(extensions=['nl2br', 'sane_lists', DeregisterSyntax()])
        self.messageText = MessageTextEdit(self.centralwidget)
        self.setup_message_text()
        # Signals
        self.searchMessageLineEdit.textChanged.connect(self.handle_search_text_changed)
        self.searchPrevBtn.clicked.connect(self.handle_prev_message_search)
        self.searchNextBtn.clicked.connect(self.handle_next_message_search)
        self.previewBtn.clicked.connect(self.toggle_preview)
        self.sendMessageBtn.clicked.connect(self.send_message)
        self.uploadBtn.clicked.connect(self.handle_upload)
        self.editMessageBtn.clicked.connect(self.edit_message)
        self.cancelBtn.clicked.connect(self.send_message_state)
        # Socket Connection handlers
        self.conn.signal_project_permissions_updated.connect(self.handle_permissions_updated)
        self.conn.signal_message_receive.connect(self.handle_incoming_message)
        self.conn.signal_message_reply_receive.connect(self.handle_incoming_message_reply)
        self.conn.signal_message_edited.connect(self.handle_message_edited)
        self.conn.signal_message_deleted.connect(self.handle_deleted_message)
        # Set Label text
        self.set_label_text()
        # Hide Edit Message section
        self.send_message_state()
        # load all users
        self.load_users()
        # load messages
        self.load_all_messages()
        if access_level == "viewer":
            self.messageText.setEnabled(False)
            self.previewBtn.setEnabled(False)
            self.uploadBtn.setEnabled(False)
            self.sendMessageBtn.setEnabled(False)

    # UI SET UP METHODS
    def setup_message_text(self):
        self.messageText.setAcceptRichText(False)
        self.messageText.setTextInteractionFlags(
            QtCore.Qt.LinksAccessibleByKeyboard | QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextBrowserInteraction |
            QtCore.Qt.TextEditable | QtCore.Qt.TextEditorInteraction | QtCore.Qt.TextSelectableByKeyboard |
            QtCore.Qt.TextSelectableByMouse)
        self.messageText.setPlaceholderText("Enter message here.\nPress enter to send.\nShift+Enter to add a new line.")
        self.messageText.setObjectName("messageText")
        vbox_layout = QtWidgets.QVBoxLayout()
        vbox_layout.addWidget(self.messageText)
        vbox_layout.setSpacing(0)
        vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.messageTextContainer.setLayout(vbox_layout)

    def set_label_text(self):
        self.user_info.setText(f"Logged in: {self.user['username']}")
        self.proj_info.setText(f"Project: {self.project_name}")

    def get_img_dimensions(self, image):
        # TODO: CHECK WHY SCROLL BAR COMES?
        max_height = self.messageText.size().height()
        height = max_height - 4
        width = image.width() * height / image.height()
        return width, height

    def display_uploaded_img(self, file_path):
        self.messageText.clear()
        image_uri = QtCore.QUrl(f"file://{file_path}")
        image = QtGui.QImage(QtGui.QImageReader(file_path).read())
        self.messageText.document().addResource(
            QtGui.QTextDocument.ImageResource,
            image_uri,
            QtCore.QVariant(image)
        )
        img_width, img_height = self.get_img_dimensions(image)
        image_format = QtGui.QTextImageFormat()
        image_format.setWidth(img_width)
        image_format.setHeight(img_height)
        image_format.setName(image_uri.toString())
        cursor = self.messageText.textCursor()
        cursor.movePosition(
            QtGui.QTextCursor.End,
            QtGui.QTextCursor.MoveAnchor
        )
        cursor.insertImage(image_format)
        self.messageText.setReadOnly(True)

    def display_uploaded_document(self, file_path):
        self.messageText.clear()
        self.messageText.setText(f"File Selected: {file_path}")
        self.messageText.setReadOnly(True)

    # Signal Slots
    def handle_search_text_changed(self):
        self.current_search_index = None

    def handle_prev_message_search(self):
        if self.current_search_index is None:
            self.handle_message_search(self.messageList.count() - 1, -1, -1)
        else:
            self.handle_message_search(self.current_search_index - 1, -1, -1)

    def handle_next_message_search(self):
        if self.current_search_index is None:
            self.handle_message_search(self.messageList.count() - 1, -1, -1)
        else:
            self.handle_message_search(self.current_search_index + 1, self.messageList.count())

    def handle_message_search(self, start_index, end_index, step=1):
        text = self.searchMessageLineEdit.text()
        if text == "":
            return
        for row in range(start_index, end_index, step):
            item = self.messageList.item(row)
            message_widget = self.messageList.itemWidget(item)
            if message_widget.message_type in (MessageType.TEXT, MessageType.DOCUMENT):
                if text.lower() in message_widget.message_text.lower():
                    self.messageList.scrollToItem(item, QtWidgets.QAbstractItemView.PositionAtCenter)
                    item.setSelected(True)
                    self.current_search_index = row
                    return
        if self.current_search_index is None:
            show_popup(self, "Alert", "No message found!", 1)

    def toggle_preview(self):
        # Go Back to text box
        if self.messageText.isReadOnly():
            self.messageText.setHtml("")
            self.messageText.setText(self.text)
            self.messageText.moveCursor(QtGui.QTextCursor.End)
            self.messageText.setReadOnly(False)
            self.messageText.setStyleSheet("")
            self.previewBtn.setDefault(False)
            self.previewBtn.setText("Preview")
        # Show preview
        else:
            self.text = self.messageText.toPlainText()
            html = self.markdown.convert(self.text)
            self.messageText.setHtml(html)
            self.messageText.setReadOnly(True)
            self.messageText.setStyleSheet("background: #eff0f1")
            self.previewBtn.setDefault(True)
            self.previewBtn.setText("Write")

    def handle_upload(self):
        img_type = "Image (*.png *.gif *.jpg *jpeg *.bmp)"
        doc_type = "Document (*.*)"
        file_filter = f'{img_type};;{doc_type}'
        file_path = get_open_filename(self, "Select a file", "", file_filter)
        if file_path is None or file_path == "":
            return
        file_type = file_path.split('.')[-1]
        self.attachment = file_path
        if file_type in ['png', 'gif', 'jpg', 'jpeg', 'bmp']:
            self.attachment_type = MessageType.IMAGE
            self.display_uploaded_img(file_path)
        else:
            self.attachment_type = MessageType.DOCUMENT
            self.display_uploaded_document(file_path)
        self.uploadBtn.setVisible(False)
        self.cancelBtn.setVisible(True)
        self.previewBtn.setVisible(False)

    def send_message(self):
        """
        send message through connection
        """
        if self.attachment is None:
            reply_id = -1
            if self.active_message_reply is not None:
                reply_id = self.active_message_reply.id
            message_text = self.messageText.toPlainText()
            if message_text == "":
                return
            message_text = message_text.strip()
            self.conn.send_message(message_text, self.p_id, reply_id)
        else:
            files = {"file": open(self.attachment, 'rb')}
            data = {
                "token": self.token,
                "p_id": self.p_id,
                "message_type": int(self.attachment_type)
            }
            url = url_join(self.mscolab_server_url, 'message_attachment')
            try:
                requests.post(url, data=data, files=files)
            except requests.exceptions.ConnectionError:
                show_popup(self, "Error", "File size too large")
        self.send_message_state()

    def start_message_reply(self, message_item):
        self.send_message_state()
        self.active_message_reply = message_item
        self.active_message_reply.set_selected(True)
        self.uploadBtn.setVisible(False)
        self.cancelBtn.setVisible(True)

    def start_message_edit(self, message_text, message_id):
        self.send_message_state()
        self.active_edit_id = message_id
        self.messageText.setText(message_text)
        self.messageText.setFocus()
        self.messageText.moveCursor(Qt.QTextCursor.End)
        self.editMessageBtn.setVisible(True)
        self.cancelBtn.setVisible(True)
        self.sendMessageBtn.setVisible(False)
        self.uploadBtn.setVisible(False)

    def send_message_state(self):
        self.active_edit_id = None
        self.attachment = None
        if self.active_message_reply is not None:
            self.active_message_reply.set_selected(False)
            self.active_message_reply = None
        self.messageText.clear()
        self.messageText.setReadOnly(False)
        self.messageText.setFocus()
        self.editMessageBtn.setVisible(False)
        self.cancelBtn.setVisible(False)
        self.sendMessageBtn.setVisible(True)
        self.previewBtn.setVisible(True)
        self.uploadBtn.setVisible(True)

    def edit_message(self):
        new_message_text = self.messageText.toPlainText()
        if new_message_text == "":
            self.conn.delete_message(self.active_edit_id, self.p_id)
        else:
            new_message_text = new_message_text.strip()
            self.conn.edit_message(self.active_edit_id, new_message_text, self.p_id)
        self.send_message_state()

    # API REQUESTS
    def load_users(self):
        # load users to side-tab here
        # make request to get users
        data = {
            "token": self.token,
            "p_id": self.p_id
        }
        url = url_join(self.mscolab_server_url, 'authorized_users')
        r = requests.get(url, data=data)
        if r.text == "False":
            show_popup(self, "Error", "Some error occurred while fetching users!")
        else:
            self.collaboratorsList.clear()
            users = r.json()["users"]
            for user in users:
                item = QtWidgets.QListWidgetItem(f'{user["username"]} - {user["access_level"]}',
                                                 parent=self.collaboratorsList)
                self.collaboratorsList.addItem(item)

    def load_all_messages(self):
        # empty messages and reload from server
        data = {
            "token": self.token,
            "p_id": self.p_id,
            "timestamp": datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d, %H:%M:%S")
        }
        # returns an array of messages
        url = url_join(self.mscolab_server_url, "messages")
        res = requests.get(url, data=data).json()
        messages = res["messages"]
        # clear message box
        for message in messages:
            self.render_new_message(message, scroll=False)
        self.messageList.scrollToBottom()

    def render_new_message(self, message, scroll=True):
        message_item = MessageItem(message, self)
        list_widget_item = QtWidgets.QListWidgetItem(self.messageList)
        list_widget_item.setSizeHint(message_item.sizeHint())
        self.messageList.addItem(list_widget_item)
        self.messageList.setItemWidget(list_widget_item, message_item)
        if scroll:
            self.messageList.scrollToBottom()

    # SOCKET HANDLERS
    @QtCore.Slot(int)
    def handle_permissions_updated(self, _):
        self.load_users()

    @QtCore.Slot(str)
    def handle_incoming_message(self, message):
        message = json.loads(message)
        self.render_new_message(message)

    @QtCore.Slot(str)
    def handle_incoming_message_reply(self, reply):
        reply = json.loads(reply)
        for i in range(self.messageList.count() - 1, -1, -1):
            item = self.messageList.item(i)
            message_widget = self.messageList.itemWidget(item)
            if message_widget.id == reply["reply_id"]:
                # TODO: Hacky Approach. Add UI update function in the widget later instead of creating a new widget
                message_widget.replies.append(reply)
                message = {
                    "id": message_widget.id,
                    "u_id": message_widget.u_id,
                    "username": message_widget.username,
                    "replies": message_widget.replies,
                    "message_type": message_widget.message_type,
                    "time": message_widget.time
                }
                if message_widget.message_type in (MessageType.TEXT, MessageType.SYSTEM_MESSAGE):
                    message["text"] = message_widget.message_text
                else:
                    message["text"] = message_widget.attachment_path
                new_message_item = MessageItem(message, self)
                item.setSizeHint(new_message_item.sizeHint())
                self.messageList.setItemWidget(item, new_message_item)
                break

    @QtCore.Slot(str)
    def handle_message_edited(self, message):
        message = json.loads(message)
        message_id = message["message_id"]
        new_message_text = message["new_message_text"]
        # Loop backwards because it's more likely the message is new than old
        for i in range(self.messageList.count() - 1, -1, -1):
            item = self.messageList.item(i)
            message_widget = self.messageList.itemWidget(item)
            if message_widget.id == message_id:
                message_widget.update_text(new_message_text)
                item.setSizeHint(message_widget.sizeHint())
                break

    @QtCore.Slot(str)
    def handle_deleted_message(self, message):
        message = json.loads(message)
        message_id = message["message_id"]
        # Loop backwards because it's more likely the message is new than old
        for i in range(self.messageList.count() - 1, -1, -1):
            item = self.messageList.item(i)
            message_widget = self.messageList.itemWidget(item)
            if message_widget.id == message_id:
                self.messageList.takeItem(i)
                break

    def closeEvent(self, event):
        self.viewCloses.emit()


class MessageItem(QtWidgets.QWidget):
    def __init__(self, message, chat_window):
        super(MessageItem, self).__init__()
        self.id = message["id"]
        self.u_id = message["u_id"]
        self.username = message["username"]
        self.message_type = message["message_type"]
        self.replies = message["replies"]
        self.time = message["time"]
        self.chat_window = chat_window
        self.message_text = None
        self.attachment_path = None
        self.message_image = None
        self.messageBox = None
        if self.message_type in (MessageType.TEXT, MessageType.SYSTEM_MESSAGE):
            self.message_text = message["text"]
        else:
            self.attachment_path = message["text"]
        self.context_menu = QtWidgets.QMenu(self)
        self.textArea = QtWidgets.QWidget()
        self.replyArea = None
        self.replyScroll = QtWidgets.QScrollArea()
        self.setup_message_box()
        self.setup_message_box_layout()
        self.setup_context_menu()

    def setup_image_message_box(self):
        MAX_WIDTH = MAX_HEIGHT = 300
        self.messageBox = QtWidgets.QLabel()
        img_url = url_join(self.chat_window.mscolab_server_url, self.attachment_path)
        data = requests.get(img_url).content
        image = QtGui.QImage()
        image.loadFromData(data)
        self.message_image = image
        width, height = image.size().width(), image.size().height()
        if width > height and width > MAX_WIDTH:
            image = image.scaledToWidth(MAX_WIDTH)
        elif height > width and height > MAX_HEIGHT:
            image = image.scaledToHeight(MAX_HEIGHT)
        self.messageBox.setPixmap(QtGui.QPixmap(image))
        self.messageBox.setContentsMargins(0, 5, 0, 5)
        self.messageBox.show()

    def get_text_browser(self, text):
        text_browser = QtWidgets.QTextBrowser()
        html = self.chat_window.markdown.convert(text)
        text_browser.setHtml(html)
        text_browser.setOpenLinks(False)
        text_browser.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        text_browser.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        text_browser.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        text_browser.setAttribute(103)
        text_browser.anchorClicked.connect(self.on_link_click)
        text_browser.show()
        text_browser.setFixedHeight(
            text_browser.document().size().height() + text_browser.contentsMargins().top() * 2
        )
        return text_browser

    def setup_text_message_box(self):
        if self.message_type == MessageType.DOCUMENT:
            doc_url = url_join(self.chat_window.mscolab_server_url, self.attachment_path)
            file_name = fs.path.basename(self.attachment_path)
            self.message_text = f"Document: [{file_name}]({doc_url})"
        self.messageBox = self.get_text_browser(self.message_text)

    def setup_message_box(self):
        if self.message_type == MessageType.IMAGE:
            self.setup_image_message_box()
        else:
            self.setup_text_message_box()
        self.messageBox.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.messageBox.customContextMenuRequested.connect(self.open_context_menu)

    def setup_message_box_layout(self):
        container_layout = QtWidgets.QHBoxLayout()
        text_area_layout = QtWidgets.QVBoxLayout()
        if self.chat_window.user["username"] == self.username:
            text_area_layout.addWidget(self.messageBox)
            self.textArea.setLayout(text_area_layout)
            container_layout.addStretch()
            container_layout.addWidget(self.textArea)
        else:
            username_label = QtWidgets.QLabel(f"{self.username}")
            username_label.setContentsMargins(5, 5, 5, 0)
            label_font = QtGui.QFont()
            label_font.setBold(True)
            username_label.setFont(label_font)
            text_area_layout.addWidget(username_label)
            text_area_layout.addWidget(self.messageBox)
            self.textArea.setLayout(text_area_layout)
            container_layout.addWidget(self.textArea)
            container_layout.addStretch()
        for reply in self.replies:
            self.add_message_reply(reply)
        self.textArea.layout().setSpacing(0)
        self.textArea.layout().setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.setContentsMargins(5, 5, 5, 5)
        self.set_message_style()
        self.setLayout(container_layout)

    def set_message_style(self, selected=False):
        sent_msg_color = "#dcf8c6"
        recv_msg_color = "#eff0f1"
        system_msg_color = "#a9d3e0"
        message_selected = "#70bbed"
        if self.chat_window.user["username"] == self.username:
            border = "border-top-left-radius: 5px; border-bottom-left-radius: 5px; border-bottom-right-radius: 5px"
            color = sent_msg_color
        else:
            border = "border-top-right-radius: 5px; border-bottom-left-radius: 5px; border-bottom-right-radius: 5px"
            color = recv_msg_color
        if self.message_type == MessageType.SYSTEM_MESSAGE:
            color = system_msg_color
        if selected is True:
            color = message_selected
        self.messageBox.setStyleSheet("background: transparent; border: none;")
        self.textArea.setStyleSheet(f"background: {color}; {border}")

    def insert_reply_area(self):
        self.replyArea = QtWidgets.QGroupBox()
        reply_area_layout = QtWidgets.QFormLayout()
        reply_area_layout.setSpacing(0)
        reply_area_layout.setContentsMargins(5, 0, 0, 0)
        self.replyArea.setLayout(reply_area_layout)
        self.replyScroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.replyScroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.replyScroll.setMaximumHeight(150)
        self.replyScroll.setWidgetResizable(True)
        self.replyScroll.setWidget(self.replyArea)
        self.replyScroll.setContentsMargins(0, 0, 0, 0)
        self.textArea.layout().addWidget(self.replyScroll)
        if self.username == self.chat_window.user["username"]:
            color = "#c3f39e"
        else:
            color = "#e2e3e5"
        self.messageBox.setStyleSheet("background: transparent; border-bottom: 1px solid black;")
        self.replyScroll.setStyleSheet(f"background: {color}")

    def add_message_reply(self, reply):
        if self.replyArea is None:
            self.insert_reply_area()
        reply_username_label = QtWidgets.QLabel(f'{reply["username"]}:')
        label_font = QtGui.QFont()
        label_font.setBold(True)
        reply_username_label.setFont(label_font)
        reply_message_box = self.get_text_browser(reply["text"])
        self.replyArea.layout().addRow(reply_username_label, reply_message_box)

    def setup_context_menu(self):
        download_action = self.context_menu.addAction("Download")
        copy_action = self.context_menu.addAction("Copy")
        reply_action = self.context_menu.addAction("Reply")
        edit_action = self.context_menu.addAction("Edit")
        delete_action = self.context_menu.addAction("Delete")
        download_action.triggered.connect(self.handle_download_action)
        copy_action.triggered.connect(self.handle_copy_action)
        reply_action.triggered.connect(self.handle_reply_action)
        edit_action.triggered.connect(self.handle_edit_action)
        delete_action.triggered.connect(self.handle_delete_action)
        # Enabling/Disabling actions based on who sent the message
        if self.username != self.chat_window.user["username"]:
            edit_action.setVisible(False)
            delete_action.setVisible(False)
        # Enabling/Disabling actions based on the type of message
        if self.message_type == MessageType.SYSTEM_MESSAGE:
            download_action.setVisible(False)
            copy_action.setVisible(False)
            reply_action.setVisible(False)
            edit_action.setVisible(False)
            delete_action.setVisible(False)
        elif self.message_type == MessageType.TEXT:
            download_action.setVisible(False)
        elif self.message_type == MessageType.IMAGE or self.message_type == MessageType.DOCUMENT:
            copy_action.setVisible(False)
            edit_action.setVisible(False)

    def open_context_menu(self, pos):
        self.context_menu.exec_(self.messageBox.mapToGlobal(pos))

    def handle_copy_action(self):
        Qt.QApplication.clipboard().setText(self.message_text)

    def handle_download_action(self):
        file_name = fs.path.basename(self.attachment_path)
        file_name, file_ext = fs.path.splitext(file_name)
        # fs.file_picker cannot take filenames that contain dots
        default_filename = file_name.replace('.', '_') + file_ext
        if self.message_type == MessageType.DOCUMENT:
            file_path = get_save_filename(self, "Save Document", default_filename, f"Document (*{file_ext})")
            if file_path is not None:
                file_content = requests.get(url_join(self.chat_window.mscolab_server_url, self.attachment_path)).content
                with open(file_path, "wb") as f:
                    f.write(file_content)
        else:
            file_path = get_save_filename(self, "Save Image", default_filename, f"Image (*{file_ext})")
            if file_path is not None:
                self.message_image.save(file_path)

    def handle_reply_action(self):
        self.chat_window.start_message_reply(self)

    def handle_edit_action(self):
        self.chat_window.start_message_edit(self.message_text, self.id)

    def handle_delete_action(self):
        # disable edit message section if it's active before deleting
        self.chat_window.send_message_state()
        self.chat_window.conn.delete_message(self.id, self.chat_window.p_id)

    def update_text(self, message_text):
        self.message_text = message_text
        html = self.chat_window.markdown.convert(self.message_text)
        self.messageBox.setHtml(html)
        self.messageBox.setFixedHeight(
            self.messageBox.document().size().height() + self.messageBox.contentsMargins().top() * 2
        )
        self.textArea.adjustSize()

    def set_selected(self, selected):
        if selected is True:
            self.set_message_style(selected=True)
        else:
            self.set_message_style()

    def on_link_click(self, url):
        if url.scheme() == "":
            url.setScheme("http")
        Qt.QDesktopServices.openUrl(url)


# Deregister all the syntax that we don't want to allow
# Can't find any part in documentation where all the syntax names are mentioned
# For future reference to syntax name refer to:
# https://github.com/Python-Markdown/markdown/blob/a06659b62209de98cbc23715addb2b768a245788/markdown/core.py#L100
class DeregisterSyntax(Extension):
    """
    Current Supported syntax:
    *text* : emphasis
    **text** : bold
    - text : unordered list
    1. text : ordered list
    # text : Heading
    [text](link) : link
    <link> : clickable link
    """

    def extendMarkdown(self, md):
        # Deregister block syntax
        md.parser.blockprocessors.deregister('setextheader')
        md.parser.blockprocessors.deregister('hr')
        md.parser.blockprocessors.deregister('quote')

        # Deregister inline syntax
        md.inlinePatterns.deregister('reference')
        md.inlinePatterns.deregister('image_link')
        md.inlinePatterns.deregister('image_reference')
        md.inlinePatterns.deregister('short_reference')
        md.inlinePatterns.deregister('automail')
        md.inlinePatterns.deregister('linebreak')
        md.inlinePatterns.deregister('html')
        md.inlinePatterns.deregister('entity')
