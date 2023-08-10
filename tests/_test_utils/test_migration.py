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
import pytest
import fs
from packaging import version

from mslib.utils import auth
from mslib.version import __version__
from mslib.msui.constants import MSUI_SETTINGS
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
        if version.parse(__version__) >= version.parse('8.0.0') and version.parse(__version__) < version.parse('9.0.0'):
            from mslib.utils.migration.update_json_file_to_version_eight import JsonConversion
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
            # store old configuration
            create_msui_settings_file(data)

            from mslib.utils.migration.config_before_eight import read_config_file as read_config_file_before_eight
            from mslib.utils.migration.config_before_eight import config_loader as config_loader_before_eight
            read_config_file_before_eight()

            wms_login = {'http://www.your-server.de/forecasts': ['youruser', 'yourpassword']}
            assert config_loader_before_eight(dataset="WMS_login") == wms_login
            msc_login = {'http://www.your-mscolab-server.de': ['youruser', 'yourpassword']}
            assert config_loader_before_eight(dataset="MSC_login") == msc_login
            assert config_loader_before_eight(dataset="MSCOLAB_password") == mail_password

            new_version = JsonConversion()
            # converting and storing
            new_version.change_parameters()
            filename = MSUI_SETTINGS.replace('\\', '/')
            dir_name, file_name = fs.path.split(filename)
            # check that we have a backup file
            bak_file = f"{file_name}.bak"
            _fs = fs.open_fs(dir_name)
            assert _fs.exists(bak_file)

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
            assert data == ("youruser", 'yourpassword')
            assert auth.get_password_from_keyring("MSCOLAB", "something@something.org") == mail_password

            # check removed old attributes
            with pytest.raises(KeyError):
                assert config_loader(dataset="WMS_login")
            with pytest.raises(KeyError):
                config_loader(dataset="MSC_login")
            with pytest.raises(KeyError):
                config_loader(dataset="MSCOLAB_password")

    def test_upgrade_json_file_to_version_nine(self):
        """
        The test checks on version 8 if an old msui_settings.json can become migrated
        It adds the new attributes and stores passwords in the keyring
        """
        if version.parse(__version__) >= version.parse('9.0.0') and\
                version.parse(__version__) < version.parse('10.0.0'):
            from mslib.utils.migration.update_json_file_to_version_nine import JsonConversion
            # old attributes
            mailid = 'something@something.org'
            auth = '"https://www.your-mscolab-server.de": "youruser"'
            default = '"https://www.your-mscolab-server.de"'
            data = f"""{{
            "MSCOLAB_mailid": "{mailid}",

            "MSS_auth": {{
                             {auth}
                         }},
            "default_MSCOLAB": [
                                   {default}
                               ]
            }}"""
            # store old configuration
            create_msui_settings_file(data)

            from mslib.utils.migration.config_before_nine import read_config_file as read_config_file_before_nine
            from mslib.utils.migration.config_before_nine import config_loader as config_loader_before_nine
            read_config_file_before_nine()

            result = dict()
            result[default] = mailid
            assert config_loader_before_nine(dataset="MSS_auth") == {"https://www.your-mscolab-server.de": "youruser"}
            all = config_loader_before_nine()
            # old version knows MSCOLAB_mailid
            assert "MSCOLAB_mailid" in all.keys()
            new_version = JsonConversion()
            # converting and storing
            new_version.change_parameters()
            filename = MSUI_SETTINGS.replace('\\', '/')
            dir_name, file_name = fs.path.split(filename)
            # check that we have a backup file
            bak_file = f"{file_name}.bak"
            _fs = fs.open_fs(dir_name)
            assert _fs.exists(bak_file)

            # using current configuration
            from mslib.utils.config import read_config_file, config_loader
            read_config_file()
            # added MSCOLAB_mailid to the url based on default_MSCOLAB
            mss_auth = config_loader(dataset="MSS_auth")
            assert mss_auth == {"https://www.your-mscolab-server.de": mailid}
            all = config_loader()
            # new version forgot about MSCOLAB_mailid
            assert "MSCOLAB_mailid" not in all.keys()
