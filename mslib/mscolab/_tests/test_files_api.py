# # -*- coding: utf-8 -*-
# """

#     mslib.mscolab._tests.test_files_api
#     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#     api integration tests for file based handlers

#     This file is part of mss.

#     :copyright: Copyright 2019 Shivashis Padhi
#     :license: APACHE-2.0, see LICENSE for details.

#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at

#        http://www.apache.org/licenses/LICENSE-2.0

#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
# """
# import requests
# import multiprocessing
# import json
# import time

# from mslib.mscolab.models import User, Change
# from mslib.mscolab.sockets_manager import fm
# from mslib._tests.constants import MSCOLAB_URL_TEST
# from mslib.mscolab.server import db, sockio, app


# class Test_Files(object):
#     def setup(self):
#         self.sockets = []
#         self.file_message_counter = [0] * 2
#         self.thread = multiprocessing.Process(
#             target=sockio.run,
#             args=(app,),
#             kwargs={'port': 8083})
#         self.thread.start()
#         self.app = app
#         db.init_app(self.app)
#         time.sleep(1)
#         data = {
#             'email': 'a',
#             'password': 'a'
#         }
#         r = requests.post(MSCOLAB_URL_TEST + '/token', data=data)
#         self.token = json.loads(r.text)['token']
#         with self.app.app_context():
#             self.user = User.query.filter_by(id=8).first()

#     def test_create_project(self):
#         data = {
#             "token": self.token,
#             "path": "dummy",
#             "description": "test description"
#         }
#         r = requests.post(MSCOLAB_URL_TEST + '/create_project', data=data)
#         assert r.text == "True"
#         r = requests.post(MSCOLAB_URL_TEST + '/create_project', data=data)
#         assert r.text == "False"

#     def test_projects(self):
#         data = {
#             "token": self.token
#         }
#         r = requests.get(MSCOLAB_URL_TEST + '/projects', data=data)
#         json_res = json.loads(r.text)
#         assert len(json_res["projects"]) == 3
#         data["token"] = "garbage text"
#         r = requests.get(MSCOLAB_URL_TEST + '/projects', data=data)
#         assert r.text == "False"

#     def test_get_project(self):
#         with self.app.app_context():
#             projects = fm.list_projects(self.user)
#             p_id = projects[-1]["p_id"]
#             data = {
#                 "token": self.token,
#                 "p_id": p_id
#             }
#             r = requests.get(MSCOLAB_URL_TEST + '/get_project', data=data)
#             assert json.loads(r.text)["content"] == fm.get_file(int(p_id), self.user)

#     def test_delete_project(self):
#         with self.app.app_context():
#             projects = fm.list_projects(self.user)
#             p_id = projects[-1]["p_id"]
#         data = {
#             "token": self.token,
#             "p_id": p_id
#         }
#         r = requests.post(MSCOLAB_URL_TEST + '/delete_project', data=data)
#         assert r.text == "True"
#         r = requests.post(MSCOLAB_URL_TEST + '/delete_project', data=data)
#         assert r.text == "False"

#     def test_change_api(self):
#         with self.app.app_context():
#             projects = fm.list_projects(self.user)
#             p_id = projects[-1]["p_id"]
#             ch = Change(int(p_id), 8, 'some content', 'some comment')
#             db.session.add(ch)
#             db.session.commit()
#         data = {
#             "token": self.token,
#             "p_id": p_id
#         }
#         r = requests.get(MSCOLAB_URL_TEST + '/get_changes', data=data)
#         changes = json.loads(r.text)["changes"]
#         assert len(changes) == 1
#         assert changes[0]["comment"] == "some comment"

#         data = {
#             "token": self.token,
#             "ch_id": changes[0]["id"]
#         }
#         r = requests.get(MSCOLAB_URL_TEST + '/get_change_id', data=data)
#         change = json.loads(r.text)["change"]
#         assert change["content"] == "some content"

#         data["p_id"] = 123
#         data["ch_id"] = 123
#         r = requests.get(MSCOLAB_URL_TEST + '/get_changes', data=data)
#         assert r.text == "False"
#         r = requests.get(MSCOLAB_URL_TEST + '/get_change_id', data=data)
#         assert r.text == "False"
#         with self.app.app_context():
#             Change.query.filter_by(content="some content").delete()
#             db.session.commit()

#     """
#     todo tests:
#     - authorized users
#     - add permission
#     - remove permissin
#     - modify permission
#     - update project
#     """
#     def teardown(self):
#         for socket in self.sockets:
#             socket.disconnect()
#         self.thread.terminate()
