# -*- coding: utf-8 -*-
"""

    mslib.msui.msui_web_browser.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    MSUIWebBrowser can be used for localhost usage and testing purposes.

    This file is part of MSS.

    :copyright: Copyright 2023 Nilupul Manodya
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
import sys

from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtWidgets import QMainWindow, QPushButton, QToolBar, QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile

from mslib.msui.constants import MSUI_CONFIG_PATH


class MSUIWebBrowser(QMainWindow):
    def __init__(self, url: str):
        super().__init__()

        self.web_view = QWebEngineView(self)
        self.setCentralWidget(self.web_view)

        self._url = url
        self.profile = QWebEngineProfile().defaultProfile()
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        self.browser_storage_folder = os.path.join(MSUI_CONFIG_PATH, 'webbrowser', '.cookies')
        self.profile.setPersistentStoragePath(self.browser_storage_folder)

        self.back_button = QPushButton("← Back", self)
        self.forward_button = QPushButton("→ Forward", self)
        self.refresh_button = QPushButton("🔄 Refresh", self)

        self.back_button.clicked.connect(self.web_view.back)
        self.forward_button.clicked.connect(self.web_view.forward)
        self.refresh_button.clicked.connect(self.web_view.reload)

        toolbar = QToolBar()
        toolbar.addWidget(self.back_button)
        toolbar.addWidget(self.forward_button)
        toolbar.addWidget(self.refresh_button)
        self.addToolBar(toolbar)

        self.web_view.load(QUrl(self._url))
        self.setWindowTitle("MSS Web Browser")
        self.resize(800, 600)
        self.show()

    def closeEvent(self, event):
        '''
            Delete all cookies when closing the web browser
        '''
        self.profile.cookieStore().deleteAllCookies()


if __name__ == "__main__":
    '''
        This function will be moved to handle accordingly the test cases.
        The 'connection' variable determines when the web browser should be
        closed, typically after the user logged in and establishes a connection
    '''

    CONNECTION = False

    def close_qtwebengine():
        '''
            Close the main window
        '''
        main.close()

    def check_connection():
        '''
            Schedule the close_qtwebengine function to be called asynchronously
        '''
        if CONNECTION:
            QTimer.singleShot(0, close_qtwebengine)

    # app = QApplication(sys.argv)
    app = QApplication(['', '--no-sandbox'])
    WEB_URL = "https://www.google.com/"
    main = MSUIWebBrowser(WEB_URL)

    QTimer.singleShot(0, check_connection)

    sys.exit(app.exec_())
