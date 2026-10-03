# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_server
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for server functionalities

    This file is part of MSS.

    :copyright: Copyright 2020 Reimar Bauer
    :copyright: Copyright 2020-2026 by the MSS team, see AUTHORS.
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
import datetime

import pytest
import json
import io
import os

import mock

from PIL import Image
from flask import current_app

from mslib.mscolab.auth import register_user, check_login
from mslib.mscolab.api.message_type import MessageType
from mslib.mscolab.models import db, User, Operation
from mslib.mscolab.utils import ATTACHMENTS_URL_PREFIX

from mslib.mscolab.file_manager import FileManager
from mslib.mscolab.seed import add_user, get_user, add_user_to_operation
from tests.utils import XML_CONTENT1, XML_CONTENT2
from mslib.mscolab.seed import XML_CONTENT_INIT


class Test_Server:
    @pytest.fixture(autouse=True)
    def setup(self, mscolab_app, mscolab_managers):
        self.app = mscolab_app
        self.sockio, _, self.fm = mscolab_managers
        self.userdata = 'UV10@uv10.de', 'UV10', 'uv10.de', 'User UV'
        with self.app.app_context():
            yield

    def test_initialized_managers(self, mscolab_managers):
        sockio, cm, fm = mscolab_managers
        assert self.app.config['OPERATIONS_DATA'] == current_app.config['OPERATIONS_DATA']
        assert 'Create a Flask-SocketIO server.' in sockio.__doc__
        assert 'Class with handler functions for chat related functionalities' in cm.__doc__
        assert 'Class with handler functions for file related functionalities' in fm.__doc__

    def test_home(self):
        # we switched templates off
        with self.app.test_client() as test_client:
            response = test_client.get('/')
            assert response.status_code == 200
            assert b"" in response.data

    def test_hello(self):
        with self.app.test_client() as test_client:
            response = test_client.get('/status')
            data = json.loads(response.text)
            assert "Mscolab server" in data['message']
            assert True or False in data['use_saml2 ']

    def test_status_sends_attachment_settings(self):
        with mock.patch.dict(current_app.config, {'MSCOLAB_ATTACHMENT_EXTENSIONS': [".ZIP", "csv"]}):
            with self.app.test_client() as test_client:
                data = json.loads(test_client.get('/status').text)
        assert data["attachment_extensions"] == ["csv", "zip"]
        assert data["max_upload_size"] == current_app.config['MAX_UPLOAD_SIZE']

    def test_register_user(self):
        with self.app.test_client():
            result = register_user("newmail1@example.com", "password", "newuser1", "John Doe")
            assert result["success"] is True
            result = register_user("newmail1@example.com", "password", "newuser2", "John Doe")
            assert result["success"] is False
            assert result["message"] == "This email ID is already taken!"
            result = register_user("UV", "password", "newuser3", "John Doe")
            assert result["success"] is False
            assert result["message"] == "Your email ID is not valid!"
            result = register_user("newmail3@example.com", "password", "newuser@4", "John Doe")
            assert result["success"] is False
            assert result["message"] == "Your username cannot contain @ symbol!"
            result = register_user("newmail4@example.com", "password", "newuser5", "Jean-Luc Picard")
            assert result["success"] is True
            result = register_user("newemail5@example.com", "password", "newuser6", "John Doe")
            assert result["success"] is True
            result = register_user("newemail6@example.com", "password", "newuser7", "")
            assert result["success"] is True
            result = register_user("newemail7@example.com", "password", "newuser8", "John123")
            assert result["success"] is True

    def test_check_login(self):
        with self.app.test_client():
            result = register_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
            assert result["success"] is True
            result = check_login(self.userdata[0], self.userdata[1])
            user = User.query.filter_by(emailid=str(self.userdata[0])).first()
            assert user is not None
            assert result == user
            result = check_login('UV20@uv20.de', self.userdata[1])
            assert result is False

    def test_get_auth_token(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            token = self._get_token(test_client, self.userdata)
            assert User.verify_auth_token(token)
            response = test_client.post('/token', data={"email": self.userdata[0], "password": "fail"})
            assert response.status_code == 200
            assert response.data.decode('utf-8') == "False"

    def test_authorized(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            token = self._get_token(test_client, self.userdata)
            response = test_client.get('/test_authorized', data={"token": token})
            assert response.status_code == 200
            assert response.data.decode('utf-8') == "True"
            response = test_client.get('/test_authorized', data={"token": "effsdfs"})
            assert response.data.decode('utf-8') == "False"

    def test_user_register_handler(self):
        with self.app.test_client() as test_client:
            response = test_client.post('/register', data={"email": self.userdata[0],
                                                           "password": self.userdata[2],
                                                           "username": self.userdata[1],
                                                           "fullname": self.userdata[3]})
            assert response.status_code == 201
            response = test_client.post('/register', data={"email": self.userdata[0],
                                                           "pass": "dsss",
                                                           "username": self.userdata[1],
                                                           "fullname": self.userdata[3]})
            assert response.status_code == 400

    def test_get_user(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            token = self._get_token(test_client, self.userdata)
            response = test_client.get('/user', data={"token": token})
            data = json.loads(response.data.decode('utf-8'))
            assert data["user"]["username"] == self.userdata[1]

    def test_delete_user(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            # Case 1 : The user has no profile image set
            token = self._get_token(test_client, self.userdata)
            response = test_client.post('/delete_own_account', data={"token": token})
            assert response.status_code == 200
            assert response.get_json()["success"] is True

            # Case 2 : The user has a custom profile image set
            assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
            token = self._get_token(test_client, self.userdata)
            response = self._upload_profile_image(test_client, token, self.userdata[0])
            assert response.status_code == 200  # this will ensure image was uploaded

            user = get_user(self.userdata[0])
            relative_image_path = user.profile_image_path  # Capture the path before deletion
            full_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], relative_image_path)
            response = test_client.post('/delete_own_account', data={"token": token})
            assert response.status_code == 200
            assert response.get_json()["success"] is True
            assert not os.path.exists(full_image_path)

    def test_upload_endpoints_exist(self):
        # the upload limit applies to these endpoints by name, a renamed view would get the larger limit
        from mslib.mscolab.app import MSColabRequest
        assert set(MSColabRequest.UPLOAD_ENDPOINTS) <= set(self.app.view_functions)
        assert current_app.config['MAX_CONTENT_LENGTH'] > current_app.config['MAX_UPLOAD_SIZE']

    def test_operation_larger_than_upload_limit(self):
        # an operation created from a large flight track is limited by MAX_CONTENT_LENGTH, not MAX_UPLOAD_SIZE
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        padding = "x" * (current_app.config['MAX_UPLOAD_SIZE'] + 1)
        large = XML_CONTENT_INIT.replace("<ListOfWaypoints>", f"<!-- {padding} --><ListOfWaypoints>", 1)
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata, content=large)
            assert operation is not None
            too_large = "x" * (current_app.config['MAX_CONTENT_LENGTH'] + 1)
            response = test_client.post('/create_operation', data={"token": token, "path": "toolarge",
                                                                   "description": "d", "content": too_large})
            assert response.status_code == 413
            limit = current_app.config['MAX_CONTENT_LENGTH'] / 1024 / 1024
            assert response.get_json() == {"success": False,
                                           "message": f"Request too large. The limit is {limit:.1f} MiB."}

    def test_oversized_uploads_refused(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        oversized = b"x" * (current_app.config['MAX_UPLOAD_SIZE'] + 1)
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = test_client.post('/message_attachment', data={"token": token,
                                                                     "op_id": operation.id,
                                                                     "file": (io.BytesIO(oversized), 'big.txt'),
                                                                     "message_type": "3"})
            assert response.status_code == 413
            assert response.get_json() == {"success": False, "message": "Request too large. The limit is 2.0 MiB."}
            attachment_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(operation.id))
            assert not os.path.isdir(attachment_dir) or not os.listdir(attachment_dir)

            user = get_user(self.userdata[0])
            response = test_client.post('/upload_profile_image', data={
                "user_id": str(user.id), "token": token, "image": (io.BytesIO(oversized), 'big.jpeg', 'image/jpeg')})
            assert response.status_code == 413
            assert get_user(self.userdata[0]).profile_image_path is None

    def _attach(self, test_client, token, operation, filename, content, message_type="3"):
        return test_client.post('/message_attachment', data={"token": token,
                                                             "op_id": operation.id,
                                                             "file": (io.BytesIO(content), filename),
                                                             "message_type": message_type})

    @pytest.mark.parametrize("filename, content", [
        ("page.txt", b"<html><script>alert(document.domain)</script></html>"),
        ("track.ftml", b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>'),
    ])
    def test_uploads_served_as_download(self, filename, content):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = self._attach(test_client, token, operation, filename, content)
            assert response.status_code == 200
            pfn = response.get_json()["path"]
            response = test_client.get(pfn, data={"token": token})
            assert response.status_code == 200
            assert response.data == content
            assert response.headers["Content-Disposition"] == f'attachment; filename={os.path.basename(pfn)}'
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["Content-Security-Policy"] == "sandbox"

    def test_stored_html_attachment_served_as_download(self):
        # stored before the allow-list existed
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            attachment_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(operation.id))
            os.makedirs(attachment_dir, exist_ok=True)
            with open(os.path.join(attachment_dir, "page.html"), "wb") as f:
                f.write(b"<html><script>alert(document.domain)</script></html>")
            response = test_client.get(f'/{ATTACHMENTS_URL_PREFIX}/{operation.id}/page.html', data={"token": token})
            assert response.status_code == 200
            assert response.headers["Content-Disposition"] == "attachment; filename=page.html"
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["Content-Security-Policy"] == "sandbox"

    @pytest.mark.parametrize("filename", [
        "track.ftml", "track.CSV", "route.gpx", "route.kml", "data.nc", "data.nc4", "data.h5", "minutes.pdf",
        "plan.xlsx", "slides.pptx", "notes.md", "clip.mp4", "clip.mov",
    ])
    def test_attachment_extension_allowed(self, filename):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = self._attach(test_client, token, operation, filename, b"content")
            assert response.get_json()["success"] is True
            # stored with its own extension, also those mimetypes doesn't know, e.g. .ftml or .gpx
            assert response.get_json()["path"].endswith("." + filename.rsplit(".", 1)[1].lower())

    @pytest.mark.parametrize("filename, message", [
        ("page.html", "Files of type .html can not be sent."),
        ("image.svg", "Files of type .svg can not be sent."),
        ("setup.exe", "Files of type .exe can not be sent."),
        ("open.hta", "Files of type .hta can not be sent."),
        ("macro.docm", "Files of type .docm can not be sent."),
        ("archive.zip", "Files of type .zip can not be sent."),
        ("noextension", "Files without an extension can not be sent."),
    ])
    def test_attachment_extension_refused(self, filename, message):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = self._attach(test_client, token, operation, filename, b"<script>alert(1)</script>")
            assert response.get_json() == {"success": False, "message": message}
            attachment_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(operation.id))
            assert not os.path.isdir(attachment_dir) or not os.listdir(attachment_dir)

    def test_attachment_extensions_configurable(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with mock.patch.dict(current_app.config, {'MSCOLAB_ATTACHMENT_EXTENSIONS': [".ZIP", "csv"]}):
            with self.app.test_client() as test_client:
                operation, token = self._create_operation(test_client, self.userdata)
                response = self._attach(test_client, token, operation, "archive.zip", b"content")
                assert response.get_json()["success"] is True
                assert response.get_json()["path"].endswith(".zip")
                response = self._attach(test_client, token, operation, "minutes.pdf", b"content")
                assert response.get_json() == {"success": False, "message": "Files of type .pdf can not be sent."}

    def test_image_attachment_must_be_image(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        png = io.BytesIO()
        Image.new('RGB', (4, 4), color='yellow').save(png, format='PNG')
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = self._attach(test_client, token, operation, "image.png", png.getvalue(),
                                    message_type=str(int(MessageType.IMAGE)))
            assert response.get_json()["success"] is True
            response = self._attach(test_client, token, operation, "image.png", b"<html></html>",
                                    message_type=str(int(MessageType.IMAGE)))
            assert response.get_json() == {"success": False, "message": "The image is no valid image."}

    def test_uploads_non_latin1_path(self):
        # the download name is encoded by werkzeug, a path that is no latin-1 does not break the answer
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = test_client.get(f'/{ATTACHMENTS_URL_PREFIX}/{operation.id}/%E2%82%AC')
            assert response.status_code == 401
            response = test_client.get(f'/{ATTACHMENTS_URL_PREFIX}/{operation.id}/%E2%82%AC', data={"token": token})
            assert response.status_code == 404
            attachment_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(operation.id))
            os.makedirs(attachment_dir, exist_ok=True)
            with open(os.path.join(attachment_dir, "€.txt"), "wb") as f:
                f.write(b"euro")
            response = test_client.get(f'/{ATTACHMENTS_URL_PREFIX}/{operation.id}/%E2%82%AC.txt', data={"token": token})
            assert response.status_code == 200
            assert response.data == b"euro"
            assert "filename*=UTF-8''%E2%82%AC.txt" in response.headers["Content-Disposition"]
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["Content-Security-Policy"] == "sandbox"

    def test_profile_image_not_rendered_as_page(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            token = self._get_token(test_client, self.userdata)
            assert self._upload_profile_image(test_client, token, self.userdata[0]).status_code == 200
            user = get_user(self.userdata[0])
            response = test_client.get('/fetch_profile_image', data={"token": token, "user_id": str(user.id)})
            assert response.status_code == 200
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["Content-Security-Policy"] == "sandbox"

    def test_profile_image_stored_with_extension_of_its_content(self):
        # a valid image that is also valid HTML, uploaded as .html, must not be served as text/html
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        img_byte_arr = io.BytesIO()
        Image.new('RGB', (4, 4), color='yellow').save(img_byte_arr, format='PNG')
        content = img_byte_arr.getvalue() + b"<html><body>fake login</body></html>"
        with self.app.test_client() as test_client:
            token = self._get_token(test_client, self.userdata)
            user = get_user(self.userdata[0])
            response = test_client.post('/upload_profile_image', data={
                "user_id": str(user.id), "token": token, "image": (io.BytesIO(content), "x.html", "text/html")})
            assert response.status_code == 200
            assert get_user(self.userdata[0]).profile_image_path.endswith(".png")
            response = test_client.get('/fetch_profile_image', data={"token": token, "user_id": str(user.id)})
            assert response.status_code == 200
            assert response.mimetype == "image/png"
            assert response.headers["Content-Disposition"].startswith("inline;")
            assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_profile_image_with_other_format_refused(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        img_byte_arr = io.BytesIO()
        Image.new('RGB', (4, 4), color='yellow').save(img_byte_arr, format='TIFF')
        with self.app.test_client() as test_client:
            token = self._get_token(test_client, self.userdata)
            user = get_user(self.userdata[0])
            response = test_client.post('/upload_profile_image', data={
                "user_id": str(user.id), "token": token,
                "image": (io.BytesIO(img_byte_arr.getvalue()), "x.tiff", "image/tiff")})
            assert response.status_code == 400
            assert get_user(self.userdata[0]).profile_image_path is None

    def test_stored_profile_image_with_other_extension_served_as_download(self):
        # stored before the extension was taken from the content
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        profile_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], "profile")
        os.makedirs(profile_dir, exist_ok=True)
        with open(os.path.join(profile_dir, "legacy.html"), "wb") as f:
            f.write(b"<html><body>fake login</body></html>")
        user = get_user(self.userdata[0])
        user.profile_image_path = "profile/legacy.html"
        db.session.commit()
        with self.app.test_client() as test_client:
            token = self._get_token(test_client, self.userdata)
            response = test_client.get('/fetch_profile_image', data={"token": token, "user_id": str(user.id)})
            assert response.status_code == 200
            assert response.headers["Content-Disposition"] == "attachment; filename=legacy.html"
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["Content-Security-Policy"] == "sandbox"

    def test_unauthorized_profile_image_upload(self):
        other_user_data = 'other@ex.com', 'other', 'other', 'Other'
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        assert add_user(other_user_data[0], other_user_data[1], other_user_data[2], other_user_data[3])
        with self.app.test_client() as test_client:
            # Case 1: Unauthenticated upload attempt
            user = get_user(self.userdata[0])
            assert user.profile_image_path is None
            self._upload_profile_image(test_client, token="random-string", email=self.userdata[0])
            user = get_user(self.userdata[0])
            assert user.profile_image_path is None   # profile-image-path should remain None after failed upload

            # Case 2: Authenticated as another user trying to upload for main user
            token_of_other_user = self._get_token(test_client, other_user_data)
            self._upload_profile_image(test_client, token_of_other_user, self.userdata[0])
            user = get_user(self.userdata[0])
            assert user.profile_image_path is None  # User should not be able to upload an image for another user

    def test_messages(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = test_client.get('/messages', data={"token": token,
                                                          "op_id": operation.id})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["messages"] == []

    def test_message_attachment(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            attachment = io.BytesIO(b"this is a test")
            response = test_client.post('/message_attachment', data={"token": token,
                                                                     "op_id": operation.id,
                                                                     "file": (attachment, 'test.txt'),
                                                                     "message_type": "3"})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            pfn = data["path"]
            assert "txt" in pfn
            assert "uploads" in pfn

    def test_uploads(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            text = b"this is a test"
            attachment = io.BytesIO(text)
            response = test_client.post('/message_attachment', data={"token": token,
                                                                     "op_id": operation.id,
                                                                     "file": (attachment, 'test.txt'),
                                                                     "message_type": "3"})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            pfn = data["path"]
            response = test_client.get(f'/{pfn}', data={"token": token})
            assert response.status_code == 200
            assert response.data == text

    def test_uploads_require_membership(self):
        # attachments are served only to members of the operation they were sent to
        other_userdata = 'UV20@uv20.de', 'UV20', 'uv20.de', 'User UV20'
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        assert add_user(*other_userdata)
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = test_client.post('/message_attachment', data={"token": token,
                                                                     "op_id": operation.id,
                                                                     "file": (io.BytesIO(b"secret"), 'test.txt'),
                                                                     "message_type": "3"})
            pfn = json.loads(response.data.decode('utf-8'))["path"]
            other_token = get_user(other_userdata[0]).generate_auth_token()
            # without a token or with an invalid one
            assert test_client.get(f'/{pfn}').status_code == 401
            assert test_client.get(f'/{pfn}', data={"token": "invalid"}).status_code == 401
            # a registered user who is not a member of the operation
            response = test_client.get(f'/{pfn}', data={"token": other_token})
            assert response.status_code == 404
            # the folder has to be an operation id, e.g. not the profile images
            response = test_client.get(f'/{ATTACHMENTS_URL_PREFIX}/profile/x.png', data={"token": token})
            assert response.status_code == 404
            # digits int() refuses give 404 too, not a server error
            for name in ("²", "٣"):
                response = test_client.get(f'/{ATTACHMENTS_URL_PREFIX}/{name}/x.png', data={"token": token})
                assert response.status_code == 404
            # once a member, the attachment is served
            assert add_user_to_operation(path=operation.path, emailid=other_userdata[0])
            response = test_client.get(f'/{pfn}', data={"token": other_token})
            assert response.status_code == 200
            assert response.data == b"secret"

    @pytest.mark.parametrize("upload_folder_name", ["uploadshaha", r"C:\Temp", ], )
    def test_uploads_with_custom_upload_folder(self, tmp_path, upload_folder_name):
        # a UPLOAD_FOLDER not named "uploads" must not break serving the attachment
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        upload_folder = tmp_path / upload_folder_name
        with mock.patch.dict(current_app.config, {'UPLOAD_FOLDER': str(upload_folder)}):
            with self.app.test_client() as test_client:
                operation, token = self._create_operation(test_client, self.userdata)
                text = b"this is a test"
                attachment = io.BytesIO(text)
                response = test_client.post('/message_attachment', data={"token": token,
                                                                         "op_id": operation.id,
                                                                         "file": (attachment, 'test.txt'),
                                                                         "message_type": "3"})
                assert response.status_code == 200
                pfn = json.loads(response.data.decode('utf-8'))["path"]
                assert pfn.startswith(f"{ATTACHMENTS_URL_PREFIX}/{operation.id}/")
                # the file is stored in the configured UPLOAD_FOLDER
                assert (upload_folder / str(operation.id) / os.path.basename(pfn)).is_file()
                # and the client can fetch it by the path it got
                response = test_client.get(f'/{pfn}', data={"token": token})
                assert response.status_code == 200
                assert response.data == text

    def test_create_operation(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            assert operation is not None
            assert operation.active is True
            assert token is not None
            operation, token = self._create_operation(test_client,
                                                      self.userdata, path="archived_operation", active=False)
            assert operation is not None
            assert operation.active is False
            assert token is not None

    def test_dont_create_operation(self):
        content = """<?xml version="1.0" encoding="utf-8"?>
  <FlightTrack version="9.1.0">
    </ListOfWaypoints>
  </FlightTrack>
"""
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata, content=content)
            assert operation is None

    def test_get_operation_by_id(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = test_client.get('/get_operation_by_id', data={"token": token,
                                                                     "op_id": operation.id})
            assert response.status_code == 200
            assert "<ListOfWaypoints>" in response.data.decode('utf-8')

    def test_get_operations(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            self._create_operation(test_client, self.userdata, path="firstflightpath1")
            operation, token = self._create_operation(test_client, self.userdata, path="firstflightpath2")
            response = test_client.get('/operations', data={"token": token})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert len(data["operations"]) == 2
            assert data["operations"][0]["path"] == "firstflightpath1"
            assert data["operations"][1]["path"] == "firstflightpath2"

    def test_get_operations_skip_archived(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            self._create_operation(test_client, self.userdata, path="firstflightpath1")
            operation, token = self._create_operation(test_client, self.userdata, path="firstflightpath2", active=False)
            response = test_client.get('/operations', data={"token": token,
                                                            "skip_archived": "True"})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert len(data["operations"]) == 1
            assert data["operations"][0]["path"] == "firstflightpath1"
            assert "firstflightpath2" not in data["operations"]

    def test_get_all_changes(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            self._save_content(operation, self.userdata)
            sio = self.sockio.test_client(self.app)
            # ToDo implement storing comment
            sio.emit('file-save', {
                     "op_id": operation.id,
                     "token": token,
                     "content": XML_CONTENT2,
                     "comment": "XML_CONTENT2"})
            sio.emit('disconnect')

            # the newest change is on index 0, because it has a recent created_at time
            response = test_client.get('/get_all_changes', data={"token": token,
                                                                 "op_id": operation.id})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            all_changes = data["changes"]
            assert len(all_changes) == 2
            assert all_changes[0]["id"] == 2
            assert all_changes[0]["id"] > all_changes[1]["id"]
            assert all_changes[0]["created_at"] > all_changes[1]["created_at"]

    def test_get_change_content(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            user = self._save_content(operation, self.userdata)
            sio = self.sockio.test_client(self.app)
            # ToDo implement storing comment
            sio.emit('file-save', {
                     "op_id": operation.id,
                     "token": token,
                     "content": XML_CONTENT2,
                     "comment": "XML_CONTENT2"})
            sio.emit('disconnect')
            all_changes = self.fm.get_all_changes(operation.id, user)
            response = test_client.get('/get_change_content', data={"token": token,
                                                                    "ch_id": all_changes[1]["id"]})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data == {'content': XML_CONTENT1}

    def test_set_version_name(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            user = self._save_content(operation, self.userdata)
            sio = self.sockio.test_client(self.app)
            sio.emit('file-save', {
                     "op_id": operation.id,
                     "token": token,
                     "content": XML_CONTENT2,
                     "comment": "XML_CONTENT2"})
            sio.emit("disconnect")
            all_changes = self.fm.get_all_changes(operation.id, user)
            ch_id = all_changes[1]["id"]
            version_name = "THIS"
            response = test_client.post('/set_version_name', data={"token": token,
                                                                   "ch_id": ch_id,
                                                                   "op_id": operation.id,
                                                                   "version_name": version_name})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["success"] is True

    def test_authorized_users(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = test_client.get('/authorized_users', data={"token": token,
                                                                  "op_id": operation.id})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["users"] == [{'access_level': 'creator', 'username': self.userdata[1], 'id': 1}]

    def test_delete_operation(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = test_client.post('/delete_operation', data={"token": token,
                                                                   "op_id": operation.id})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["success"] is True

    def test_update_operation(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = test_client.post('/update_operation', data={"token": token,
                                                                   "op_id": operation.id,
                                                                   "attribute": "path",
                                                                   "value": "newflight"})
            assert response.status_code == 200
            data = response.data.decode('utf-8')
            assert data == "True"
            response = test_client.post('/update_operation', data={"token": token,
                                                                   "op_id": operation.id,
                                                                   "attribute": "description",
                                                                   "value": "sunday start"})
            assert response.status_code == 200
            data = response.data.decode('utf-8')
            assert data == "True"

    def test_get_operation_details(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            path = "flp1"
            operation, token = self._create_operation(test_client, self.userdata, path=path)
            response = test_client.get('/operation_details', data={"token": token,
                                                                   "op_id": operation.id})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["path"] == path

    def test_set_last_used(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            old = operation.last_used
            response = test_client.post('/set_last_used', data={"token": token,
                                                                "op_id": operation.id})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["success"] is True
            new = operation.last_used
            assert old != new
            response = test_client.post('/set_last_used', data={"token": token,
                                                                "op_id": operation.id,
                                                                "days": 10})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["success"] is True
            new = operation.last_used
            assert datetime.timedelta(days=11) > old - new > datetime.timedelta(days=9)

    def test_set_active(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            assert operation.active is True
            response = test_client.post('/update_operation', data={
                "token": token,
                "op_id": operation.id, "attribute": "active", "value": "False"})
            assert response.status_code == 200
            data = response.data.decode('utf-8')
            assert data == "True"
            assert operation.active is False

            response = test_client.post('/update_operation', data={
                "token": token,
                "op_id": operation.id, "attribute": "active", "value": "True"})
            assert response.status_code == 200
            data = response.data.decode('utf-8')
            assert data == "True"
            assert operation.active is True

            response = test_client.post('/update_operation', data={
                "token": token,
                "op_id": operation.id, "attribute": "active", "value": False})
            assert response.status_code == 200
            data = response.data.decode('utf-8')
            assert data == "True"
            assert operation.active is False

    def test_get_users_without_permission(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        unprevileged_user = 'UV20@uv20', 'UV20', 'uv20', 'User 20'
        assert add_user(unprevileged_user[0], unprevileged_user[1], unprevileged_user[2], unprevileged_user[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = test_client.get('/users_without_permission', data={"token": token,
                                                                          "op_id": operation.id})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            # ToDo after cleanup pf database use absolute values
            assert data["users"][-1][0] == unprevileged_user[1]

    def test_get_users_with_permission(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        another_user = 'UV20@uv20', 'UV20', 'uv20', 'User20'
        assert add_user(another_user[0], another_user[1], another_user[2], another_user[3])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = test_client.get('/users_with_permission', data={"token": token,
                                                                       "op_id": operation.id})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            # creator is not listed
            assert data["users"] == []

    def test_import_permissions(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        another_user = 'UV20@uv20', 'UV20', 'uv20', 'User20'
        assert add_user(another_user[0], another_user[1], another_user[2], another_user[3])
        with self.app.test_client() as test_client:
            import_operation, token = self._create_operation(test_client, self.userdata, path="import")
            user = get_user(self.userdata[0])
            another = get_user(another_user[0])
            fm = FileManager(self.app.config["OPERATIONS_DATA"])
            fm.add_bulk_permission(import_operation.id, user, [another.id], "viewer")
            current_operation, token = self._create_operation(test_client, self.userdata, path="current")
            response = test_client.post('/import_permissions', data={"token": token,
                                                                     "import_op_id": import_operation.id,
                                                                     "current_op_id": current_operation.id})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            # creator is not listed
            assert data["success"] is True

    def test_bulk_permissions_notify_group_member_operations(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
        another_user = 'UV20@uv20', 'UV20', 'uv20', 'User20'
        assert add_user(another_user[0], another_user[1], another_user[2], another_user[3])
        another = get_user(another_user[0])
        with self.app.test_client() as test_client:
            token = self._get_token(test_client)
            op_ids = []
            for path in ("flightno1", "bergenGroup"):
                response = test_client.post('/create_operation', data={
                    "token": token, "path": path, "description": path, "content": XML_CONTENT_INIT,
                    "category": "bergen"})
                assert response.status_code == 200
                op_ids.append(Operation.query.filter_by(path=path).first().id)
            op_id, group_op_id = op_ids
            sm = self.sockio.sm
            with mock.patch.object(sm, "emit_new_permission") as new_permission, \
                    mock.patch.object(sm, "emit_update_permission") as update_permission, \
                    mock.patch.object(sm, "emit_revoke_permission") as revoke_permission, \
                    mock.patch.object(sm, "emit_operation_permissions_updated") as permissions_updated:
                form = {"token": token, "op_id": group_op_id, "selected_userids": json.dumps([another.id])}
                for endpoint, access_level in (("add_bulk_permissions", "viewer"),
                                               ("modify_bulk_permissions", "collaborator"),
                                               ("delete_bulk_permissions", None)):
                    data = dict(form, selected_access_level=access_level) if access_level else form
                    response = test_client.post(f'/{endpoint}', data=data)
                    assert json.loads(response.data.decode('utf-8'))["success"] is True
            assert new_permission.call_args_list == [mock.call(another.id, group_op_id),
                                                     mock.call(another.id, op_id)]
            assert update_permission.call_args_list == [
                mock.call(another.id, group_op_id, access_level="collaborator"),
                mock.call(another.id, op_id, access_level="collaborator")]
            assert sorted(revoke_permission.call_args_list) == sorted([mock.call(another.id, group_op_id),
                                                                       mock.call(another.id, op_id)])
            assert permissions_updated.call_count == 6

    def _create_operation(self, test_client, userdata=None, path="firstflight", description="simple test",
                          content=XML_CONTENT_INIT, active=True):
        if userdata is None:
            userdata = self.userdata
        response = test_client.post('/token', data={"email": userdata[0], "password": userdata[2]})
        data = json.loads(response.data.decode('utf-8'))
        token = data["token"]
        response = test_client.post('/create_operation', data={"token": token,
                                                               "path": path,
                                                               "description": description,
                                                               "content": content,
                                                               "active": str(active)})
        assert response.status_code == 200
        operation = Operation.query.filter_by(path=path).first()
        return operation, token

    def _get_token(self, test_client, userdata=None):
        if userdata is None:
            userdata = self.userdata
        response = test_client.post('/token', data={"email": userdata[0], "password": userdata[2]})
        assert response.status_code == 200
        data = json.loads(response.data.decode('utf-8'))
        assert data["user"]["username"] == userdata[1]
        token = data["token"]
        return token

    def _save_content(self, operation, userdata=None):
        if userdata is None:
            userdata = self.userdata
        user = get_user(userdata[0])
        self.fm.save_file(operation.id, XML_CONTENT1, user)
        return user

    def _upload_profile_image(self, test_client, token, email):
        # Creating a dummy image
        img = Image.new('RGB', (64, 64), color='yellow')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        filename = "test.jpeg"

        # Post request for uploading the image
        user = get_user(email)
        data = {
            "user_id": str(user.id),
            "token": token,
            'image': (img_byte_arr, filename, 'image/jpeg')
        }
        response = test_client.post('/upload_profile_image', data=data)
        return response
