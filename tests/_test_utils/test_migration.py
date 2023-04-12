# -*- coding: utf-8 -*-
"""

    tests._test_utils.test_migration
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests migrations

    This file is part of mss.

    :copyright: Copyright 2020 Reimar Bauer
    :copyright: Copyright 2020-2023 by the MSS team, see AUTHORS.
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
from mslib.utils.migration.update_json_file_to_version_eight import JsonConversion
from mslib.utils import auth
from mslib.version import __version__
from tests.utils import create_msui_settings_file


class TestMigration:
    """
    Test for migrations
    """
    def test_upgrade_json_file_to_version_eight(self):
        """
        The test checks on version 8 if an old msui_settings.json can become migrated
        It adds the new attributes and stores passwords in the keyring
        """
        if version.parse(__version__) >= version.parse('8.0.0'):
            # old attributes
            wms_def = '"http://www.your-server.de/forecasts": ["youruser", "yourpassword"]'
            msc_def = '"http://www.your-mscolab-server.de": ["youruser", "yourpassword"]'
            mail_password = "EitdmhrPWS3AHqxi1msY"
            data = f"""{{
            "WMS_login": {{ {wms_def}
                             }},
            "MSC_login": {{
                             {msc_def}
                         }},
            "MSCOLAB_mailid": "something@something.org",
            "MSCOLAB_password": "{mail_password}"
            }}"""
            create_msui_settings_file(data)
            new_version = JsonConversion()
            new_version.change_parameters()
            # using old configuration
            from mslib.utils.migration.config_before_eight import read_config_file as read_config_file_before_eight
            from mslib.utils.migration.config_before_eight import config_loader as config_loader_before_eight
            read_config_file_before_eight()
            wms_login = {'http://www.your-server.de/forecasts': ['youruser', 'yourpassword']}
            assert config_loader_before_eight(dataset="WMS_login") == wms_login
            msc_login = {'http://www.your-mscolab-server.de': ['youruser', 'yourpassword']}
            assert config_loader_before_eight(dataset="MSC_login") == msc_login
            assert config_loader_before_eight(dataset="MSCOLAB_password") == mail_password
            # using current configuration
            from mslib.utils.config import read_config_file, config_loader
            read_config_file()
            # converted WMS_login and MSC_login to MSS_auth attribute
            http_auth = config_loader(dataset="MSS_auth")
            assert http_auth == {
                "http://www.your-server.de/forecasts": "youruser",
                "http://www.your-mscolab-server.de": "youruser"
            }
            # verify keyring
            data = auth.get_auth_from_url_and_name("http://www.your-server.de/forecasts", http_auth)
            assert data == ("youruser", 'password from TestKeyring')
            assert auth.get_password_from_keyring("MSCOLAB", "something@something.org") == 'password from TestKeyring'
