# -*- coding: utf-8 -*-
"""

    mslib.mscolab.server
    ~~~~~~~~~~~~~~~~~~~~

    Server for mscolab module

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2023 by the MSS team, see AUTHORS.
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
import subprocess
import time

from mslib import __version__
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.seed import seed_data, add_user, add_all_users_default_operation,\
    add_all_users_to_all_operations, delete_user
from mslib.mscolab.utils import create_files
from mslib.utils import setup_logging
from mslib.utils.qt import Worker, Updater


def handle_start(args):
    from mslib.mscolab.server import APP, initialize_managers, start_server
    setup_logging(args)
    logging.info("MSS Version: %s", __version__)
    logging.info("Python Version: %s", sys.version)
    logging.info("Platform: %s (%s)", platform.platform(), platform.architecture())
    logging.info("Launching MSColab Server")

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
    from mslib.mscolab.models import db
    from mslib.mscolab.server import APP
    create_files()
    with APP.app_context():
        db.create_all()
    print("Database initialised successfully!")


def handle_db_reset(verbose=True):
    from mslib.mscolab.models import db
    from mslib.mscolab.server import APP
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

def handle_mscolab_certificate_init():
    print('generating CRTs for the mscolab server......')
    cmd = f"openssl req -newkey rsa:4096 -keyout {mscolab_settings.MSCOLAB_SSO_DIR}/key_mscolab.key -nodes -x509 -days 365 -batch -subj '/CN=localhost' -out {mscolab_settings.MSCOLAB_SSO_DIR}/crt_mscolab.crt"
    os.system(cmd)
    print('CRTs generated successfully for the mscolab server......')

def handle_local_idp_certificate_init():
    print('generating CRTs for the local identity provider......')
    cmd = f"openssl req -newkey rsa:4096 -keyout {mscolab_settings.MSCOLAB_SSO_DIR}/key_local_idp.key -nodes -x509 -days 365 -batch -subj '/CN=localhost' -out {mscolab_settings.MSCOLAB_SSO_DIR}/crt_local_idp.crt"
    os.system(cmd)
    print('crts generated successfully for the mscolab local identity provider......')

def handle_mscolab_metadata_init():
    '''
        This will generate necessary metada data file for sso in mscolab through localhost idp

        Before running this function:
        - Ensure that IDP_ENABLED is set to True.
        - Generate the necessary keys and certificates and configure them in the .yaml 
        file for the local IDP.
    '''
    print('generating metadata file for the mscolab server')

    cmd ="python mslib/mscolab/mscolab.py start"
    subprocess.Popen(["python", "mslib/mscolab/mscolab.py", "start"])

    # Add a small delay to allow the server to start up
    time.sleep(10)

    cmd_curl = f"curl http://localhost:8083/metadata/ -o {mscolab_settings.MSCOLAB_SSO_DIR}/metadata_sp.xml"
    os.system(cmd_curl)

    print('mscolab metadata file generated succesfully')


def handle_local_idp_metadata_init():
    print('generating metadata for localhost identity provider')

    cmd = f"make_metadata mslib/idp/idp_conf.py > {mscolab_settings.MSCOLAB_SSO_DIR}/idp.xml"
    os.system(cmd)

    print('idp metadata file generated succesfully')

def handle_sso_crts_init():
    """
        This will generate necessary CRTs files for sso in mscolab through localhost idp
    """
    print("mscolab sso conf initiating......")
    create_files()
    handle_mscolab_certificate_init()
    handle_local_idp_certificate_init()
    print('CRTs generated successfully')


def handle_sso_metadata_init():
    print('generating metadata files.......')
    handle_mscolab_metadata_init()
    handle_local_idp_metadata_init()
    print("ALl necessary metadata file generated successfully")

    # Get the process group ID of the current process
    pgid = os.getpgid(0)

    # Kill the whole terminal by sending a SIGKILL signal to the process group
    os.killpg(pgid, 9)


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
    database_parser.add_argument("--default_operation", help="adds all users into a default TEMPLATE operation",
                                 action="store_true")
    database_parser.add_argument("--add_all_to_all_operation", help="adds all users into all other operations",
                                 action="store_true")
    sso_conf_parser = subparsers.add_parser("sso_conf", help="single sign on process configurations")
    sso_conf_parser = sso_conf_parser.add_mutually_exclusive_group(required=True)
    sso_conf_parser.add_argument("--init_sso_crts",help="Generate all the essential CRTs required for the Single Sign-On process using the local Identity Provider",
                                 action="store_true")
    sso_conf_parser.add_argument("--init_sso_metadata",help="Generate all the essential metadata files required for the Single Sign-On process using the local Identity Provider",
                                 action="store_true")

    args = parser.parse_args()

    if args.version:
        print("***********************************************************************")
        print("\n            Mission Support System (MSS)\n")
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
        elif args.default_operation:
            confirmation = confirm_action(
                "Are you sure you want to add users to the default TEMPLATE operation? (y/[n]):")
            if confirmation is True:
                # adds all users as collaborator on the operation TEMPLATE if not added, command can be repeated
                add_all_users_default_operation(access_level='admin')
        elif args.add_all_to_all_operation:
            confirmation = confirm_action(
                "Are you sure you want to add users to the ALL operations? (y/[n]):")
            if confirmation is True:
                # adds all users to all Operations
                add_all_users_to_all_operations()
        elif args.delete_users_by_file:
            confirmation = confirm_action(
                "Are you sure you want to delete a user? (y/[n]):")
            if confirmation is True:
                # deletes users from the db
                for email in args.delete_users_by_file.readlines():
                    delete_user(email.strip())

    elif args.action == "sso_conf":
        if args.init_sso_crts:
            handle_sso_crts_init()
        if args.init_sso_metadata:
            confirmation = confirm_action(
                "Are you sure you executed --init_sso_crts before running this? (y/[n]):")
            if confirmation is True:
                confirmation = confirm_action(
                """
                This will generate necessary metada data file for sso in mscolab through localhost idp

                Before running this function:
                - Ensure that IDP_ENABLED is set to True.
                - Generate the necessary keys and certificates and configure them in the .yaml 
                file for the local IDP.
                
                Are you sure you set all correctly as per the documentation? (y/[n]):""")
                if confirmation is True:
                    handle_sso_metadata_init()

if __name__ == '__main__':
    main()
