#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

    mslib.mscolab.demodata
    ~~~~~~~~~~~~~~~~~~~~~~

    dummydata for mscolab

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2020 by the mss team, see AUTHORS.
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

import argparse
import os
import shutil

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.seed import seed_data


def create_files():
    if not os.path.exists(mscolab_settings.MSCOLAB_DATA_DIR):
        os.makedirs(mscolab_settings.MSCOLAB_DATA_DIR)
    if not os.path.exists(mscolab_settings.UPLOAD_FOLDER):
        os.makedirs(mscolab_settings.UPLOAD_FOLDER)


def init_db():
    from mslib.mscolab.server import db, APP
    create_files()
    with APP.app_context():
        db.create_all()


def reset_db():
    from mslib.mscolab.server import db, APP
    if os.path.exists(mscolab_settings.DATA_DIR):
        shutil.rmtree(mscolab_settings.DATA_DIR)
    create_files()
    with APP.app_context():
        db.drop_all()
        db.create_all()


def seed_db():
    reset_db()
    seed_data(mscolab_settings.SQLALCHEMY_DB_URI)


def main():
    parser = argparse.ArgumentParser(description="Tool to setup data for usage of mscolab")
    parser.add_argument("--init", action="store_true", help="Setup database")
    parser.add_argument("--seed", action="store_true", help="Seed database")
    parser.add_argument("--reset", action="store_true", help="Reset database")
    args = parser.parse_args()
    if args.init:
        init_db()
    elif args.seed:
        seed_db()
    elif args.reset:
        reset_db()
    else:
        print("for help, use -h flag")


if __name__ == '__main__':
    main()
