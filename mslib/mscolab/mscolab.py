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
import secrets

from mslib import __version__
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.seed import seed_data, add_user, add_all_users_default_project,\
    add_all_users_to_all_projects, delete_user
from mslib.mscolab.utils import create_files
from mslib.utils import setup_logging
from mslib.msui.mss_qt import Worker, Updater


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
    if verbose is True:
        print("Database has been reset successfully!")


def handle_db_seed():
    handle_db_reset(verbose=False)
    seed_data()
    print("Database seeded successfully!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", help="show version", action="store_true", default=False)
    parser.add_argument("--update", help="Updates MSS to the newest version", action="store_true", default=False)

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
    database_parser.add_argument("--users_by_file", type=argparse.FileType('r'),
                                 help="adds users into database, fileformat: suggested_username  name   <email>")
    database_parser.add_argument("--delete_users_by_file", type=argparse.FileType('r'),
                                 help="removes users from the database, fileformat: email")
    database_parser.add_argument("--default_project", help="adds all users into a default TEMPLATE project",
                                 action="store_true")
    database_parser.add_argument("--add_all_to_all_project", help="adds all users into all other projects",
                                 action="store_true")

    args = parser.parse_args()

    if args.version:
        print("***********************************************************************")
        print("\n            Mission Support System (mss)\n")
        print("***********************************************************************")
        print("Documentation: http://mss.rtfd.io")
        print("Version:", __version__)
        sys.exit()

    updater = Updater()
    if args.update:
        updater.on_update_available.connect(lambda old, new: updater.update_mss())
        updater.on_log_update.connect(lambda s: print(s.replace("\n", "")))
        updater.on_status_update.connect(lambda s: print(s.replace("\n", "")))
        updater.run()
        while Worker.workers:
            list(Worker.workers)[0].wait()
        sys.exit()

    updater.on_update_available.connect(lambda old, new: logging.info(f"MSS can be updated from {old} to {new}.\nRun"
                                                                      " the --update argument to update the server."))
    updater.run()

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
        elif args.users_by_file is not None:
            # fileformat: suggested_username  name   <email>
            confirmation = confirm_action("Are you sure you want to add users to the database? (y/[n]):")
            if confirmation is True:
                for line in args.users_by_file.readlines():
                    info = line.split()
                    username = info[0]
                    emailid = info[-1][1:-1]
                    password = secrets.token_hex(8)
                    add_user(emailid, username, password)
        elif args.default_project:
            confirmation = confirm_action(
                "Are you sure you want to add users to the default TEMPLATE project? (y/[n]):")
            if confirmation is True:
                # adds all users as collaborator on the project TEMPLATE if not added, command can be repeated
                add_all_users_default_project(access_level='admin')
        elif args.add_all_to_all_project:
            confirmation = confirm_action(
                "Are you sure you want to add users to the ALL projects? (y/[n]):")
            if confirmation is True:
                # adds all users to all Projects
                add_all_users_to_all_projects()
        elif args.delete_users_by_file:
            confirmation = confirm_action(
                "Are you sure you want to delete a user? (y/[n]):")
            if confirmation is True:
                # deletes users from the db
                for email in args.delete_users_by_file.readlines():
                    delete_user(email.strip())


if __name__ == '__main__':
    main()
