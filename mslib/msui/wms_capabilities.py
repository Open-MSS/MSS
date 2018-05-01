# -*- coding: utf-8 -*-
"""

    mslib.msui.wms_capabilities
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Widget to display a WMS (Web Map Service) capabilities document.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2018 by the mss team, see AUTHORS.
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

from mslib.msui.mss_qt import QtWidgets
from mslib.msui.mss_qt import ui_wms_capabilities as ui


class WMSCapabilitiesBrowser(QtWidgets.QDialog, ui.Ui_WMSCapabilitiesBrowser):
    """Dialog presenting an XML document to the user.
    """

    def __init__(self, parent=None, url=None, capabilities=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        capabilities_xml -- .
        """
        super(WMSCapabilitiesBrowser, self).__init__(parent)
        self.setupUi(self)

        if url is None:
            url = ""
        self.lblURL.setText(url)

        self.capabilities = capabilities

        self.update_text()
        self.cbFullView.stateChanged.connect(self.update_text)

    def update_text(self):
        if self.cbFullView.isChecked():
            self.txtCapabilities.setPlainText(self.capabilities.capabilities_document)
        else:
            text = (u"<b>Title:</b> {title}<p>"
                    u"<b>Service type:</b> {type} {version}<br>"
                    u"<b>Abstract:</b><br>{abstract}<br>"
                    u"<b>Contact:</b><br>"
                    u"    {name}<br>"
                    u"    {organization}<br>"
                    u"    {email}<br>"
                    u"    {address}<br>"
                    u"    {postcode} {city}<br>\n"
                    u"<b>Keywords:</b> {keywords}<br>\n"
                    u"<b>Access constraints:</b> {accessconstraints}<br>\n"
                    u"<b>Fees:</b> {fees}").format(
                url=self.capabilities.provider.url,
                type=self.capabilities.identification.type,
                version=self.capabilities.identification.version,
                title=self.capabilities.identification.title,
                abstract=self.capabilities.identification.abstract,
                name=self.capabilities.provider.contact.name,
                organization=self.capabilities.provider.contact.organization,
                email=self.capabilities.provider.contact.email,
                address=self.capabilities.provider.contact.address,
                postcode=self.capabilities.provider.contact.postcode,
                city=self.capabilities.provider.contact.city,
                keywords=self.capabilities.identification.keywords,
                accessconstraints=self.capabilities.identification.accessconstraints,
                fees=self.capabilities.identification.fees)
            self.txtCapabilities.setHtml(text)
