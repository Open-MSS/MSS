# -*- coding: utf-8 -*-
"""

    mslib.msidp.conf
    ~~~~~~~~~~~~~~~f

    config for msidp.

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2024 by the MSS team, see AUTHORS.
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
import logging


class default_msidp_settings:
    # our default dir for mss content
    BASE_DIR = os.path.join(os.path.expanduser("~"), 'mss')

    DATA_DIR = os.path.join(BASE_DIR, "colabdata")

    # dir where mscolab single sign-on process files are stored
    SSO_DIR = os.path.join(DATA_DIR, 'datasso')


msidp_settings = default_msidp_settings()

try:
    import msidp_settings as user_settings
    logging.info("Using user defined settings")
    msidp_settings.__dict__.update(user_settings.__dict__)
except ImportError as ex:
    logging.warning(u"Couldn't import msidp_settings (ImportError:'%s'), using dummy config.", ex)
