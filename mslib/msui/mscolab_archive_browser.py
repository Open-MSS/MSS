# -*- coding: utf-8 -*-
"""

    mslib.msui.mscolab_archive_browser
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Window to display archived operations for mscolab

    This file is part of MSS.

    :copyright: Copyright 2019-2026 by the MSS team, see AUTHORS.
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
import requests
from PyQt5.QtWidgets import QDialog
from mslib.msui.qt5 import ui_operation_archive as ui_opar
from mslib.utils.config import config_loader
from mslib.utils.qt import show_popup
from mslib.mscolab.api import endpoints
from mslib.mscolab.api.schemas import UpdateOperationRequest, UpdateOperationResponse


class MSColab_OperationArchiveBrowser(QDialog, ui_opar.Ui_OperationArchiveBrowser):
    def __init__(self, parent=None, mscolab=None):
        super().__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.mscolab = mscolab
        self.pbClose.clicked.connect(self.hide)
        self.pbUnarchiveOperation.setEnabled(False)
        self.pbUnarchiveOperation.clicked.connect(self.unarchive_operation)
        self.listArchivedOperations.itemClicked.connect(self.select_archived_operation)
        self.setModal(True)

    def select_archived_operation(self, item):
        logging.debug('select_inactive_operation')
        if item.access_level in ["creator", "admin"]:
            self.archived_op_id = item.op_id
            self.pbUnarchiveOperation.setEnabled(True)
        else:
            self.archived_op_id = None
            self.pbUnarchiveOperation.setEnabled(False)

    def unarchive_operation(self):
        logging.debug('unarchive_operation')
        req = UpdateOperationRequest(op_id=self.archived_op_id, attribute="active", value="True")
        try:
            # NOTE: pre-existing bug, preserved as-is -- socket_control.ConnectionManager.request_post()
            # takes (self, api, data=None, files=None), no `timeout` parameter, so this call has always
            # raised TypeError (not caught by `except requests.exceptions.RequestException` below) the
            # moment the Unarchive button is used. Untested (no test file references
            # unarchive_operation/pbUnarchiveOperation), presumably why this has gone unnoticed.
            res = self.mscolab.conn.request_post(
                endpoints.UPDATE_OPERATION, req.to_form_data(),
                timeout=tuple(config_loader(dataset="MSCOLAB_timeout")))
        except requests.exceptions.RequestException as e:
            logging.debug(e)
            show_popup(self.parent, "Error", "Some error occurred! Could not unarchive operation.")
            self.mscolab.logout()
        else:
            if UpdateOperationResponse.from_text(res.text).success:
                self.mscolab.reload_operations()
            else:
                show_popup(self.parent, "Error", "Session expired, new login required")
                self.mscolab.logout()
