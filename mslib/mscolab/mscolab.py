# -*- coding: utf-8 -*-
"""

    mslib.mscolab.server
    ~~~~~~~~~~~~~~~~~~~~

    Server for mscolab module

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
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
import logging
import platform
import os
import shutil
import sys

from mslib import __version__
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.seed import seed_data
from mslib.mscolab.utils import create_files
from mslib.utils import setup_logging


def handle_start(args):
    from mslib.mscolab.server import APP, initialize_managers, start_server
    setup_logging(args)
    logging.info("MSS Version: %s", __version__)
    logging.info("Python Version: %s", sys.version)
    logging.info("Platform: %s (%s)", platform.platform(), platform.architecture())
    logging.info("Launching user interface...")

    app, sockio, cm, fm = initialize_managers(APP)
    start_server(app, sockio, cm, fm)


def confirm_action(confirmation_prompt):
    while True:
        confirmation = input(confirmation_prompt).lower()
        if confirmation == "n" or confirmation == "":
            return False
        elif confirmation == "y":
            return True
        else:
            print("Invalid input! Please select an option between y or n")


def handle_db_init():
    from mslib.mscolab.server import APP, db
    create_files()
    with APP.app_context():
        db.create_all()
    print("Database initialised successfully!")


def handle_db_reset(verbose=True):
    from mslib.mscolab.server import APP, db
    if os.path.exists(mscolab_settings.DATA_DIR):
        shutil.rmtree(mscolab_settings.DATA_DIR)
    create_files()
    with APP.app_context():
        db.drop_all()
        db.create_all()
    print("Database has been reset successfully!")


def handle_db_seed():
    handle_db_reset(verbose=False)
    seed_data()
    print("Database seeded successfully!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", help="show version", action="store_true", default=False)

    subparsers = parser.add_subparsers(help='Available actions', dest='action')

    server_parser = subparsers.add_parser("start", help="Start the mscolab server")
    server_parser.add_argument("--debug", help="show debugging log messages on console", action="store_true",
                               default=False)
    server_parser.add_argument("--logfile", help="If set to a name log output goes to that file", dest="logfile",
                               default=None)

    database_parser = subparsers.add_parser("db", help="Manage mscolab database")
    database_parser = database_parser.add_mutually_exclusive_group(required=True)
    database_parser.add_argument("--init", help="Initialise database", action="store_true")
    database_parser.add_argument("--reset", help="Reset database", action="store_true")
    database_parser.add_argument("--seed", help="Seed database", action="store_true")

    args = parser.parse_args()

    if args.version:
        print("***********************************************************************")
        print("\n            Mission Support System (mss)\n")
        print("***********************************************************************")
        print("Documentation: http://mss.rtfd.io")
        print("Version:", __version__)
        sys.exit()

    if args.action == "start":
        handle_start(args)

    elif args.action == "db":
        if args.init:
            handle_db_init()
        elif args.reset:
            confirmation = confirm_action("Are you sure you want to reset the database? This would delete "
                                          "all your data! (y/[n]):")
            if confirmation is True:
                handle_db_reset()
        elif args.seed:
            confirmation = confirm_action("Are you sure you want to seed the database? Seeding will delete all your "
                                          "existing data and replace it with seed data (y/[n]):")
            if confirmation is True:
                handle_db_seed()


if __name__ == '__main__':
    main()
