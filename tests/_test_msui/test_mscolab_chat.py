# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_mscolab_chat
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module tests how chat messages are rendered and how their links are opened.

    This file is part of MSS.

    :copyright: Copyright 2026 Reimar Bauer
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
import types

import mock
import pytest
from markdown import Markdown
from PyQt5 import QtCore, QtGui, QtWidgets

from mslib.mscolab.api.message_type import MessageType
from mslib.msui.mscolab_chat import (
    ChatTextBrowser, DeregisterSyntax, MessageItem, MessageTextEdit, chat_link_target, open_chat_link,
)


@pytest.fixture
def markdown():
    return Markdown(extensions=['nl2br', 'sane_lists', DeregisterSyntax()])


@pytest.mark.parametrize("text", [
    '<div><a href="file:///C:/Windows/System32/calc.exe">Agenda</a></div>',
    '<div><img src="file:////attacker.example/share/x.png"></div>',
    '<p onclick="x">text</p>',
    '<script>alert(1)</script>',
    '<!-- hidden -->',
    'inline <a href="file:///x">a</a> <img src="file:///x">',
])
def test_raw_html_is_escaped(markdown, text):
    html = markdown.convert(text)
    assert "<a " not in html
    assert "<img" not in html
    assert "<div" not in html
    assert "<script" not in html
    assert "<!--" not in html
    assert "&lt;" in html


def test_markdown_still_rendered(markdown):
    html = markdown.convert("**bold** *em* [MSS](https://open-mss.github.io) <https://example.org>\n\n- item")
    assert "<strong>bold</strong>" in html
    assert "<em>em</em>" in html
    assert '<a href="https://open-mss.github.io">MSS</a>' in html
    assert '<a href="https://example.org">https://example.org</a>' in html
    assert "<li>item</li>" in html


def _exec_answering(answer, shown):
    def exec_(box):
        shown.append((box.textFormat(), box.text()))
        return answer
    return exec_


@pytest.mark.parametrize("link", [
    "file:///C:/Windows/System32/calc.exe",
    "file://attacker.example/share/minutes.exe",
    "smb://attacker.example/share",
    "ms-msdt:/id PCWDiagnostic",
    "search-ms:query=x&crumb=location:\\\\attacker.example\\share",
    "FILE:///etc/passwd",
])
def test_open_chat_link_refuses_other_schemes(qtbot, link):
    shown = []
    with mock.patch.object(QtWidgets.QMessageBox, "exec_", _exec_answering(QtWidgets.QMessageBox.Ok, shown)), \
            mock.patch("PyQt5.QtGui.QDesktopServices.openUrl") as open_url:
        open_chat_link(None, QtCore.QUrl(link))
    open_url.assert_not_called()
    assert len(shown) == 1
    assert shown[0][0] == QtCore.Qt.PlainText


@pytest.mark.parametrize("answer, opened", [
    (QtWidgets.QMessageBox.Yes, True),
    (QtWidgets.QMessageBox.No, False),
])
def test_open_chat_link_asks_before_opening(qtbot, answer, opened):
    shown = []
    url = QtCore.QUrl("https://example.org/<b>agenda</b>")
    with mock.patch.object(QtWidgets.QMessageBox, "exec_", _exec_answering(answer, shown)), \
            mock.patch("PyQt5.QtGui.QDesktopServices.openUrl") as open_url:
        open_chat_link(None, url)
    assert open_url.called is opened
    text_format, text = shown[0]
    # the real target is shown as plain text, not interpreted as markup
    assert text_format == QtCore.Qt.PlainText
    assert "https://example.org/%3Cb%3Eagenda%3C/b%3E" in text
    assert "Host: example.org" in text


@pytest.mark.parametrize("link, target", [
    ("https://example.org/agenda", "https://example.org/agenda"),
    ("HTTP://Example.org", "http://example.org"),
    ("//example.org/agenda", "https://example.org/agenda"),
    ("www.example.org/agenda?day=1#top", "https://www.example.org/agenda?day=1#top"),
    # user info can make another host look like a trusted one
    ("https://open-mss.github.io@evil.example/agenda", None),
    ("https://user:secret@example.org", None),
    # relative or garbage, a browser would guess what is meant
    ("foo", None),
    ("http:foo", None),
    ("https:///path", None),
    ("%66ile:///x", None),
    (" file:///x", None),
    ("ftp://data.example/file.nc", None),
    ("mailto:someone@example.org", None),
    ("javascript:alert(1)", None),
])
def test_chat_link_target(link, target):
    url = chat_link_target(link)
    assert (url and url.toString(QtCore.QUrl.FullyEncoded)) == target


def test_only_openable_links_are_rendered_as_links(markdown):
    html = markdown.convert("[a](ftp://data.example) <ftp://data.example/f.nc> [b](mailto:x@example.org) "
                            "[c](foo) <https://u@example.org> [d](www.example.org)")
    assert html.count("<a ") == 1
    assert '<a href="https://www.example.org">d</a>' in html
    assert "<span>a</span>" in html
    assert "<span>ftp://data.example/f.nc</span>" in html


@pytest.mark.parametrize("widget_class", [ChatTextBrowser, MessageTextEdit])
def test_no_resources_are_loaded(qtbot, tmp_path, widget_class):
    image = tmp_path / "x.png"
    QtGui.QImage(4, 4, QtGui.QImage.Format_RGB32).save(str(image))
    url = QtCore.QUrl.fromLocalFile(str(image))
    html = f'<img src="{url.toString()}">'

    loading = QtWidgets.QTextBrowser()
    loading.setHtml(html)
    # without the protection the image is loaded from any URL a message contains
    assert loading.document().resource(QtGui.QTextDocument.ImageResource, url).size() == QtCore.QSize(4, 4)

    widget = widget_class()
    widget.setHtml(html)
    # an empty placeholder, Qt does not fall back to loading the file itself
    assert widget.document().resource(QtGui.QTextDocument.ImageResource, url).size() == QtCore.QSize(1, 1)


@pytest.fixture
def chat_window(markdown):
    return types.SimpleNamespace(markdown=markdown, user={"username": "reader"},
                                 mscolab_server_url="http://localhost:8083", token="token")


def _message_item(chat_window, message_type, text, replies=()):
    return MessageItem({
        "id": 1, "u_id": 2, "username": '<img src="file://attacker.example/s/x.png">',
        "message_type": message_type, "text": text, "time": "2026-10-02 10:00:00",
        "replies": [{"username": '<img src="file://attacker.example/s/y.png">', "text": reply} for reply in replies],
    }, chat_window)


def test_usernames_are_plain_text(qtbot, chat_window):
    item = _message_item(chat_window, MessageType.TEXT, "hello", replies=["hi"])
    labels = [label for label in item.findChildren(QtWidgets.QLabel) if "<img" in label.text()]
    assert len(labels) == 2
    assert all(label.textFormat() == QtCore.Qt.PlainText for label in labels)


@pytest.mark.parametrize("link", ["file:///C:/Windows/System32/calc.exe", "foo", "https://u@evil.example"])
def test_message_link_click_is_checked(qtbot, chat_window, link):
    item = _message_item(chat_window, MessageType.TEXT, "see the agenda")
    shown = []
    with mock.patch.object(QtWidgets.QMessageBox, "exec_", _exec_answering(QtWidgets.QMessageBox.Yes, shown)), \
            mock.patch("PyQt5.QtGui.QDesktopServices.openUrl") as open_url:
        item.messageBox.anchorClicked.emit(QtCore.QUrl(link))
    open_url.assert_not_called()
    assert len(shown) == 1


def test_reply_link_of_document_is_opened_not_downloaded(qtbot, chat_window):
    item = _message_item(chat_window, MessageType.DOCUMENT, "uploads/1/notes.pdf",
                         replies=["see [agenda](https://example.org/agenda)"])
    reply_box, = item.replyArea.findChildren(ChatTextBrowser)
    shown = []
    with mock.patch.object(MessageItem, "handle_download_action") as download, \
            mock.patch.object(QtWidgets.QMessageBox, "exec_", _exec_answering(QtWidgets.QMessageBox.Yes, shown)), \
            mock.patch("PyQt5.QtGui.QDesktopServices.openUrl") as open_url:
        reply_box.anchorClicked.emit(QtCore.QUrl("https://example.org/agenda"))
        download.assert_not_called()
        open_url.assert_called_once_with(QtCore.QUrl("https://example.org/agenda"))
        # the document itself is still downloaded with the token
        item.messageBox.anchorClicked.emit(QtCore.QUrl(item.attachment_url()))
        download.assert_called_once()
