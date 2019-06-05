from mslib.mscolab.server import db, check_login, register_user
from flask import Flask
from conf import SQLALCHEMY_DB_URI


class Test_UserMethods(object):

    def setup(self):
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DB_URI
        self.app.config['SECRET_KEY'] = 'secret!'
        db.init_app(self.app)

    def test_registration(self):
        with self.app.app_context():
            # db.create_all()
            # self.populate_db()
            x = register_user('sdf@s.com', 'sdf', 'sdf')
            assert x == 'True'
            x = register_user('sdf@s.com', 'sdf', 'sdf')
            assert x == 'False'

    def test_login(self):
        with self.app.app_context():
            # db.create_all()
            # self.populate_db()
            x = check_login('sdf@s.com', 'sdf')
            assert x is not None
            x = check_login('sdf@s.com', 'fd')
            assert x is not True

    def teardown(self):
        with self.app.app_context():
            user = check_login('sdf@s.com', 'sdf')
            if user:
                db.session.delete(user)
                db.session.commit()
