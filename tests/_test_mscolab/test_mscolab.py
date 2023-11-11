# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_mscolab
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for mscolab functionalities

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
import os
import argparse
import pytest
import mock
from flask_testing import TestCase

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Operation, User, Permission
from mslib.mscolab.mscolab import (handle_db_reset, handle_db_seed, confirm_action, main,
                                   handle_mscolab_certificate_init, handle_local_idp_certificate_init,
                                   handle_mscolab_backend_yaml_init, handle_mscolab_metadata_init,
                                   handle_local_idp_metadata_init)
from mslib.mscolab.server import APP
from mslib.mscolab.seed import add_operation
from tests import constants

mscolab_settings.MSCOLAB_SSO_DIR = constants.MSCOLAB_SSO_DIR


def test_confirm_action():
    with mock.patch("mslib.mscolab.mscolab.input", return_value="n"):
        assert confirm_action("") is False
    with mock.patch("mslib.mscolab.mscolab.input", return_value=""):
        assert confirm_action("") is False
    with mock.patch("mslib.mscolab.mscolab.input", return_value="y"):
        assert confirm_action("") is True


def test_main():
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        with mock.patch("mslib.mscolab.mscolab.argparse.ArgumentParser.parse_args",
                        return_value=argparse.Namespace(version=True)):
            main()
        assert pytest_wrapped_e.typename == "SystemExit"

    with mock.patch("mslib.mscolab.mscolab.argparse.ArgumentParser.parse_args",
                    return_value=argparse.Namespace(version=False, update=False, action="db",
                                                    init=False, reset=False, seed=False, users_by_file=None,
                                                    default_operation=False, add_all_to_all_operation=False,
                                                    delete_users_by_file=False)):
        main()
        # currently only checking precedence of all args


class Test_Mscolab(TestCase):
    def create_app(self):
        app = APP
        app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config["TESTING"] = True
        app.config['LIVESERVER_TIMEOUT'] = 10
        app.config['LIVESERVER_PORT'] = 0
        return app

    def setUp(self):
        handle_db_reset()
        assert Operation.query.all() == []
        assert User.query.all() == []
        assert Permission.query.all() == []

    def test_handle_db_reset(self):
        assert os.path.isdir(mscolab_settings.UPLOAD_FOLDER)
        assert os.path.isdir(mscolab_settings.MSCOLAB_DATA_DIR)
        all_operations = Operation.query.all()
        assert all_operations == []
        operation_name = "Example"
        assert add_operation(operation_name, "Test Example")
        assert os.path.isdir(os.path.join(mscolab_settings.MSCOLAB_DATA_DIR, operation_name))
        operation = Operation.query.filter_by(path=operation_name).first()
        assert operation.description == "Test Example"
        all_operations = Operation.query.all()
        assert len(all_operations) == 1
        handle_db_reset()
        # check operation dir name removed
        assert os.path.isdir(os.path.join(mscolab_settings.MSCOLAB_DATA_DIR, operation_name)) is False
        assert os.path.isdir(mscolab_settings.MSCOLAB_DATA_DIR)
        assert os.path.isdir(mscolab_settings.UPLOAD_FOLDER)
        # query db for operation_name
        operation = Operation.query.filter_by(path=operation_name).first()
        assert operation is None
        all_operations = Operation.query.all()
        assert all_operations == []

    def test_handle_db_seed(self):
        all_operations = Operation.query.all()
        assert all_operations == []
        handle_db_seed()
        all_operations = Operation.query.all()
        assert len(all_operations) == 6
        assert all_operations[0].path == "one"
        all_users = User.query.all()
        assert len(all_users) == 10
        all_permissions = Permission.query.all()
        assert len(all_permissions) == 17

    def test_handle_mscolab_certificate_init(self):
        """
        Test the initialization of the MSColab server certificate files.
        This function tests the initialization process of the MSColab server certificate files
        by calling the initialization function and checking if the generated key and
        certificate files contain the expected content.
        """
        handle_mscolab_certificate_init()
        file_key = os.path.join(mscolab_settings.MSCOLAB_SSO_DIR, 'key_mscolab.key')
        key_content = ''
        with open(file_key, 'r', encoding='utf-8') as file:
            key_content = file.read()
        assert "-----BEGIN PRIVATE KEY-----" in key_content
        assert "-----END PRIVATE KEY-----" in key_content
        file_cert = os.path.join(mscolab_settings.MSCOLAB_SSO_DIR, 'crt_mscolab.crt')
        crt_content = ''
        with open(file_cert, 'r', encoding='utf-8') as file:
            crt_content = file.read()
        assert "-----BEGIN CERTIFICATE-----" in crt_content
        assert "-----END CERTIFICATE-----" in crt_content

    def test_handle_local_idp_certificate_init(self):
        """
        Test the initialization of the local Identity Provider (IDP) certificate files.
        This function tests the initialization process of the local IDP certificate files
        by calling the initialization function and checking if the generated key and
        certificate files contain the expected content.
        """

        handle_local_idp_certificate_init()
        file_key = os.path.join(mscolab_settings.MSCOLAB_SSO_DIR, 'key_local_idp.key')
        key_content = ''
        with open(file_key, 'r', encoding='utf-8') as file:
            key_content = file.read()
        assert "-----BEGIN PRIVATE KEY-----" in key_content
        assert "-----END PRIVATE KEY-----" in key_content
        file_crt = os.path.join(mscolab_settings.MSCOLAB_SSO_DIR, 'crt_local_idp.crt')
        crt_content = ''
        with open(file_crt, 'r', encoding='utf-8') as file:
            crt_content = file.read()
        assert "-----BEGIN CERTIFICATE-----" in crt_content
        assert "-----END CERTIFICATE-----" in crt_content

    def test_handle_mscolab_backend_yaml_init(self):
        """
        Test the initialization of MScolab backend YAML configuration.
        This function tests the initialization process of the MScolab backend YAML
        """

        handle_mscolab_backend_yaml_init()
        file_yaml = os.path.join(mscolab_settings.MSCOLAB_SSO_DIR, 'mss_saml2_backend.yaml')
        mss_saml2_backend_content = ''
        with open(file_yaml, 'r', encoding='utf-8') as file:
            mss_saml2_backend_content = file.read()
        assert "localhost_test_idp" in mss_saml2_backend_content
        assert "entityid_endpoint" in mss_saml2_backend_content

    def test_handle_mscolab_metadata_init(self):
        """
        Test the initialization of MSColab server metadata.
        This function tests the initialization process of MSColab server metadata
        by calling several initialization functions and checking if the expected
        content is present in the generated metadata XML file.
        """
        #  set TESTING_USE_SAML2 and MSCOLAB_SSO_DIRthrough envs
        os.environ['TESTING_MSCOLAB_SSO_DIR'] = mscolab_settings.MSCOLAB_SSO_DIR
        os.environ['TESTING_USE_SAML2'] = "True"

        handle_mscolab_certificate_init()
        handle_mscolab_backend_yaml_init()
        mscolab_settings.USE_SAML2 = True
        assert handle_mscolab_metadata_init(True) is True
        metadata_xml = os.path.join(mscolab_settings.MSCOLAB_SSO_DIR, 'metadata_sp.xml')
        metadata_content = ''
        with open(metadata_xml, 'r', encoding='utf-8') as file:
            metadata_content = file.read()
        assert "urn:oasis:names:tc:SAML:2.0:metadata" in metadata_content

    def test_handle_local_idp_metadata_init(self):
        """
        Test the initialization of local Identity Provider (IDP) metadata.
        This function tests the initialization process of local IDP metadata
        by calling several initialization functions and checking if the expected
        content is present in the generated metadata XML file.
        """
        #  set TESTING_USE_SAML2 and MSCOLAB_SSO_DIRthrough envs
        os.environ['TESTING_MSCOLAB_SSO_DIR'] = mscolab_settings.MSCOLAB_SSO_DIR
        os.environ['TESTING_USE_SAML2'] = "True"
        
        handle_local_idp_certificate_init()
        handle_mscolab_backend_yaml_init()
        handle_mscolab_certificate_init()
        mscolab_settings.USE_SAML2 = True
        handle_mscolab_metadata_init(True)
        assert handle_local_idp_metadata_init(True) is True
        idp_xml = os.path.join(mscolab_settings.MSCOLAB_SSO_DIR, 'metadata_sp.xml')
        idp_content = ''
        with open(idp_xml, 'r', encoding='utf-8') as file:
            idp_content = file.read()
        assert "urn:oasis:names:tc:SAML:2.0:metadata" in idp_content
