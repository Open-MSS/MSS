# -*- coding: utf-8 -*-
"""

    mslib.utils.update_json_file_to_version_eight
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    updates the old attributes to the new attributes and creates credentials in keyring

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2023 by the MSS team, see AUTHORS.
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

from packaging import version
from mslib import __version__
from mslib.utils.auth import save_password_to_keyring
from mslib.utils.migration.config_before_eight import read_config_file as read_config_file_before_eight
from mslib.utils.migration.config_before_eight import config_loader as config_loader_before_eight
from mslib.utils.config import modify_config_file


class JsonConversion:
    def __init__(self):
        read_config_file_before_eight()
        self.wms_login = config_loader_before_eight(dataset="WMS_login")
        self.msc_login = config_loader_before_eight(dataset="MSC_login")
        self.MSCOLAB_mailid = config_loader_before_eight(dataset="MSCOLAB_mailid")
        self.MSCOLAB_password = config_loader_before_eight(dataset="MSCOLAB_password")

    def change_parameters(self):
        """
        adds new parameters and store passwords in the keyring
        """
        if version.parse(__version__) > version.parse('7.1.0') and version.parse(__version__) < version.parse('9.0.0'):
            http_auth_login_data = {}
            for url in self.wms_login.keys():
                auth_username, auth_password = self.wms_login[url]
                http_auth_login_data[url] = auth_username
                save_password_to_keyring(url, auth_username, auth_password)

            for url in self.msc_login.keys():
                auth_username, auth_password = self.msc_login[url]
                http_auth_login_data[url] = auth_username
                save_password_to_keyring(url, auth_username, auth_password)

            data_to_save_in_config_file = {
                "MSS_auth": http_auth_login_data
            }
            save_password_to_keyring(service_name="MSCOLAB",
                                     username=self.MSCOLAB_mailid, password=self.MSCOLAB_password)
            modify_config_file(data_to_save_in_config_file)


if __name__ == "__main__":
    if version.parse(__version__) >= version.parse('8.0.0'):
        new_version = JsonConversion()
        new_version.change_parameters()
