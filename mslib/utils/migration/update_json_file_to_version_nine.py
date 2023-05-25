# -*- coding: utf-8 -*-
"""

    mslib.utils.update_json_file_to_version_nine
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

import fs
import json
import copy

from packaging import version
from mslib import __version__
from mslib.utils.migration.config_before_nine import read_config_file as read_config_file_before_nine
from mslib.utils.migration.config_before_nine import config_loader as config_loader_before_nine
from mslib.utils.config import modify_config_file
from mslib.utils.config import read_config_file, config_loader
from mslib.msui.constants import MSUI_SETTINGS


class JsonConversion:
    def __init__(self):
        read_config_file_before_nine()
        self.MSCOLAB_mailid = config_loader_before_nine(dataset="MSCOLAB_mailid")
        self.MSS_auth = config_loader_before_nine(dataset="MSS_auth")
        self.default_MSCOLAB = config_loader_before_nine(dataset="default_MSCOLAB")

    def change_parameters(self):
        """
        adds new parameters and store passwords in the keyring
        """
        if version.parse(__version__) > version.parse('8.0.0') and version.parse(__version__) < version.parse('10.0.0'):

            mss_auth = self.MSS_auth

            for url, username in self.MSS_auth.items():
                if url in self.default_MSCOLAB and mss_auth[url] != self.MSCOLAB_mailid:
                    mss_auth[url] = self.MSCOLAB_mailid

            data_to_save_in_config_file = {
                "MSS_auth": mss_auth
            }

            filename = MSUI_SETTINGS.replace('\\', '/')
            dir_name, file_name = fs.path.split(filename)
            # create the backup file
            with fs.open_fs(dir_name) as _fs:
                fs.copy.copy_file(_fs, file_name, _fs, f"{file_name}.bak")
            # add the modification
            modify_config_file(data_to_save_in_config_file)
            # read new file
            read_config_file()
            # Todo move this to a seperate function to utils
            # get all defaults
            default_options = config_loader(default=True)
            # get the data from the local file
            json_data = config_loader()
            save_data = copy.deepcopy(json_data)

            # remove everything we have as defaults
            for key in json_data:
                if json_data[key] == default_options[key] or json_data[key] == {} or json_data[key] == []:
                    del save_data[key]

            # write new data
            with fs.open_fs(dir_name) as _fs:
                _fs.writetext(file_name, json.dumps(save_data, indent=4))


if __name__ == "__main__":
    if version.parse(__version__) >= version.parse('9.0.0'):
        new_version = JsonConversion()
        new_version.change_parameters()
