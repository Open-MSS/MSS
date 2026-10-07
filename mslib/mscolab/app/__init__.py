# -*- coding: utf-8 -*-
"""

    mslib.mscolab.app
    ~~~~~~~~~~~~~~~~~

    app module of mscolab

    This file is part of MSS.

    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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
import os
import logging
import sys
from pathlib import Path

import flask_migrate
import sqlalchemy
from flask_mail import Mail

from flask_migrate import Migrate
from flask import Flask, Request, current_app, jsonify, request, url_for

import mslib

from flask_sqlalchemy import SQLAlchemy

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab import migrations
from mslib.utils import prefix_route, release_info
from mslib.utils.basic_auth import PasswordCheckBusy, check_basic_auth_setting
from mslib.utils.file_exists import file_exists
from xstatic.main import XStatic


DOCS_SERVER_PATH = os.path.dirname(os.path.abspath(mslib.__file__))
DOCS_BLUEPRINTS_DIR = os.path.join(DOCS_SERVER_PATH, 'blueprints')
DOCS_BLUEPRINTS_DOCS_DIR = os.path.join(DOCS_BLUEPRINTS_DIR, 'docs')
DOCS_TEMPLATES_DIR = os.path.join(DOCS_BLUEPRINTS_DOCS_DIR, 'templates')
DOCS_STATIC_DIR = os.path.join(DOCS_BLUEPRINTS_DOCS_DIR, 'static')
DOCS_IMG_DIR = os.path.join(DOCS_STATIC_DIR, 'img')
DOCS_DOCS_DIR = os.path.join(DOCS_STATIC_DIR, 'docs')
# This can be used to set a location by SCRIPT_NAME for testing. e.g. export SCRIPT_NAME=/demo/
SCRIPT_NAME = os.environ.get('SCRIPT_NAME', '/')

# SECRET_KEY values published in earlier versions of the sample mscolab_settings.py
PUBLISHED_SECRET_KEYS = ('MySecretKey',)
# RFC 7518 3.2: an HS256 key must be at least as long as the hash, 256 bits
MIN_SECRET_KEY_LENGTH = 32
# ADMIN_TOKEN is compared, not used as a key, its default secrets.token_urlsafe(16) has 22 characters
MIN_ADMIN_TOKEN_LENGTH = 16
# a secret needs at least this many different characters, e.g. 'a' * 32 has one, a random one of 32 about 25
MIN_SECRET_DISTINCT_CHARACTERS = 10
SECRET_HINT = f'Create one with: python -c "import secrets; print(secrets.token_urlsafe({MIN_SECRET_KEY_LENGTH}))"'


message, update = release_info.check_for_new_release()
if update:
    logging.warning(message)


db = SQLAlchemy(
    metadata=sqlalchemy.MetaData(
        naming_convention={
            # For reference: https://alembic.sqlalchemy.org/en/latest/naming.html#the-importance-of-naming-constraints
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    ),
)
mail = Mail()
migrate = Migrate(render_as_batch=True, user_module_prefix="cu.")


def _xstatic(name):
    mod_names = [
        'jquery', 'bootstrap',
    ]
    pkg = __import__('xstatic.pkg', fromlist=mod_names)
    serve_files = {}

    for mod_name in mod_names:
        mod = getattr(pkg, mod_name)
        # ToDo protocol should become configurable
        xs = XStatic(mod, root_url='/static', provider='local', protocol='http')
        serve_files[xs.name] = xs.base_dir
    try:
        return serve_files[name]
    except KeyError:
        return None


def create_files():
    Path(current_app.config['OPERATIONS_DATA']).mkdir(parents=True, exist_ok=True)
    Path(current_app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
    Path(current_app.config['SSO_DIR']).mkdir(parents=True, exist_ok=True)


def initialise_db():
    """Create the data directories and bring the database up to the latest revision.

    Must be called in an application context. This is not part of
    :func:`create_app`, so that creating an app has no side effects on the
    database (the CLI e.g. creates an app to then reset the database).
    """
    # imported here because mslib.mscolab.models imports db from this module; the
    # import also registers the models on the metadata, which the migrations need
    from mslib.mscolab.models import db

    # Remove any stale session state before inspecting the schema; a lingering
    # open transaction (e.g. from a previous iteration in test_upgrade_from)
    # can cause the inspector to see a stale/empty table list on Windows.
    db.session.remove()
    create_files()
    inspector = sqlalchemy.inspect(db.engine)
    existing_tables = inspector.get_table_names()
    if ("alembic_version" not in existing_tables and len(existing_tables) > 0) or (
        "alembic_version" in existing_tables
        and len(existing_tables) > 1
        and db.session.execute(sqlalchemy.text("SELECT * FROM alembic_version")).first() is None
    ):
        sys.exit(
            """Your database contains no alembic_version revision identifier, but it has a schema. This suggests \
that you have a pre-existing database but haven't followed the database migration instructions. To prevent damage to \
your database MSColab will abort. Please follow the documentation for a manual database migration from MSColab v8/v9."""
        )

    is_empty_database = len(existing_tables) == 0 or (
        len(existing_tables) == 1
        and "alembic_version" in existing_tables
        and db.session.execute(sqlalchemy.text("SELECT * FROM alembic_version")).first() is None
    )
    # If a database connection to migrate from is set and the target database is empty, then migrate the existing data
    if is_empty_database and current_app.config['SQLALCHEMY_DATABASE_URI_TO_MIGRATE_FROM'] is not None:
        logging.info("The target database is empty and a database to migrate from is set, starting the data migration")
        source_engine = sqlalchemy.create_engine(current_app.config['SQLALCHEMY_DATABASE_URI_TO_MIGRATE_FROM'])
        source_metadata = sqlalchemy.MetaData()
        source_metadata.reflect(bind=source_engine)
        # Determine the previous MSColab version based on the database content and upgrade to the corresponding revision
        if "authentication_backend" in source_metadata.tables["users"].columns:
            # It should be v9
            flask_migrate.upgrade(directory=migrations.__path__[0], revision="c171019fe3ee")
        else:
            # It's probably v8
            flask_migrate.upgrade(directory=migrations.__path__[0], revision="92eaba86a92e")
        # Copy over the existing data.
        # Use db.engine.url (the resolved absolute URL) rather than
        # current_app.config['SQLALCHEMY_DATABASE_URI'], which may be a relative SQLite
        # path that Flask-SQLAlchemy expands via instance_path — plain
        # sqlalchemy.create_engine would resolve it against CWD instead.
        target_engine = sqlalchemy.create_engine(str(db.engine.url))
        target_metadata = sqlalchemy.MetaData()
        target_metadata.reflect(bind=target_engine)
        with source_engine.connect() as src_connection, target_engine.connect() as target_connection:
            for table in source_metadata.sorted_tables:
                if table.name == "alembic_version":
                    # Do not migrate the alembic_version table!
                    continue
                logging.debug("Copying table %s", table.name)
                stmt = target_metadata.tables[table.name].insert()
                for row in src_connection.execute(table.select()):
                    logging.debug("Copying row %s", row)
                    row = tuple(
                        r.replace(tzinfo=datetime.timezone.utc) if isinstance(r, datetime.datetime) else r for r in row
                    )
                    target_connection.execute(stmt.values(row))
            target_connection.commit()
            if target_engine.name == "postgresql":
                # Fix the databases auto-increment sequences, if it is a PostgreSQL database
                # For reference, see: https://wiki.postgresql.org/wiki/Fixing_Sequences
                logging.info("Using a PostgreSQL database, will fix up sequences")
                cur = target_connection.execute(sqlalchemy.text(r"""
SELECT
    'SELECT SETVAL(' ||
    quote_literal(quote_ident(sequence_namespace.nspname) || '.' || quote_ident(class_sequence.relname)) ||
    ', COALESCE(MAX(' ||quote_ident(pg_attribute.attname)|| '), 1) ) FROM ' ||
    quote_ident(table_namespace.nspname)|| '.'||quote_ident(class_table.relname)|| ';'
FROM pg_depend
    INNER JOIN pg_class AS class_sequence
        ON class_sequence.oid = pg_depend.objid
            AND class_sequence.relkind = 'S'
    INNER JOIN pg_class AS class_table
        ON class_table.oid = pg_depend.refobjid
    INNER JOIN pg_attribute
        ON pg_attribute.attrelid = class_table.oid
            AND pg_depend.refobjsubid = pg_attribute.attnum
    INNER JOIN pg_namespace as table_namespace
        ON table_namespace.oid = class_table.relnamespace
    INNER JOIN pg_namespace AS sequence_namespace
        ON sequence_namespace.oid = class_sequence.relnamespace
ORDER BY sequence_namespace.nspname, class_sequence.relname;
"""))
                for stmt, in cur.all():
                    target_connection.execute(sqlalchemy.text(stmt))
                target_connection.commit()
        logging.info("Data migration finished")
        # Dispose the temporary copy engine so it doesn't hold SQLite
        # connections across subsequent initialise_db() iterations.
        target_engine.dispose()
        source_engine.dispose()

    # Upgrade to the latest database revision
    flask_migrate.upgrade(directory=migrations.__path__[0])

    logging.info("Database initialised successfully!")


class MSColabRequest(Request):
    """
    Limits the size of an upload to MAX_UPLOAD_SIZE and of any other request to MAX_CONTENT_LENGTH

    Flask refuses a larger request with 413 before reading it.
    """
    UPLOAD_ENDPOINTS = ("chat.message_attachment", "user.upload_profile_image")

    @property
    def max_content_length(self):
        if current_app and self.endpoint in self.UPLOAD_ENDPOINTS:
            return current_app.config["MAX_UPLOAD_SIZE"]
        return super().max_content_length


# 413: Payload Too Large
def error413(error):
    limit = request.max_content_length / 1024 / 1024
    return jsonify({"success": False, "message": f"Request too large. The limit is {limit:.1f} MiB."}), 413


class InsecureSecretError(RuntimeError):
    """A secret of the MSColab settings, SECRET_KEY or ADMIN_TOKEN, is missing or can be guessed"""


def check_secret(name, secret, min_length, where):
    """
    Raises InsecureSecretError if secret can't keep its tokens from being forged

    SECRET_KEY signs the login tokens, the email confirmation and password reset tokens and the Flask
    sessions, anyone who knows it can log in as any user. ADMIN_TOKEN lets local processes trigger
    socket.io events. where says where the secret is set, for the message.
    """
    if secret is None or secret == "" or secret == b"":
        raise InsecureSecretError(f"{name} is not set. Set it in {where}. {SECRET_HINT}")
    if not isinstance(secret, (str, bytes)):
        raise InsecureSecretError(f"{name} must be a string. Set it in {where}. {SECRET_HINT}")
    if secret in PUBLISHED_SECRET_KEYS:
        raise InsecureSecretError(
            f"{name} is the published sample value {secret!r}, with it anyone can log in as any user. "
            f"Set a secret of your own in {where}. {SECRET_HINT}")
    if len(secret) < min_length:
        raise InsecureSecretError(
            f"{name} must have at least {min_length} characters. Set it in {where}. {SECRET_HINT}")
    if secret != secret.strip():
        raise InsecureSecretError(f"{name} must not start or end with whitespace. Set it in {where}.")
    if len(set(secret)) < MIN_SECRET_DISTINCT_CHARACTERS:
        raise InsecureSecretError(
            f"{name} must have at least {MIN_SECRET_DISTINCT_CHARACTERS} different characters, it can be "
            f"guessed. Set it in {where}. {SECRET_HINT}")


def check_secrets(app):
    """
    Takes SECRET_KEY from the environment variable MSCOLAB_SECRET_KEY if it is set and checks the secrets

    The environment variable wins over mscolab_settings, e.g. over an old settings file with the published
    sample key. There is no random default: every process of the server has to sign tokens with the same key,
    a random key per process would log users out at random with several workers and on every restart.
    """
    secret_key = os.environ.get("MSCOLAB_SECRET_KEY", "").strip()
    if secret_key:
        app.config["SECRET_KEY"] = secret_key
    check_secret("SECRET_KEY", app.config.get("SECRET_KEY"), MIN_SECRET_KEY_LENGTH,
                 "the environment variable MSCOLAB_SECRET_KEY or in your mscolab_settings")
    check_secret("ADMIN_TOKEN", app.config.get("ADMIN_TOKEN"), MIN_ADMIN_TOKEN_LENGTH, "your mscolab_settings")


def create_app(config_object=mscolab_settings):
    """Create and configure an MSColab Flask application.

    :param config_object: the object the configuration is read from, by default the
        :class:`mslib.mscolab.conf.DefaultSettings` instance updated with the
        settings of the users ``mscolab_settings`` module.

    The returned app is not connected to a database schema yet, call
    :func:`initialise_db` within an application context of it to do so.

    :raises InsecureSecretError: if SECRET_KEY or ADMIN_TOKEN is missing or can be guessed,
        see :func:`check_secrets`.
    """
    app = Flask(__name__, template_folder=DOCS_TEMPLATES_DIR)
    app.config.from_object(config_object)
    check_secrets(app)
    check_basic_auth_setting(config_object, "mscolab_settings")
    app.register_error_handler(PasswordCheckBusy, lambda error: (str(error), 503, {"Retry-After": "10"}))
    # uploads are limited to MAX_UPLOAD_SIZE, other requests to MAX_CONTENT_LENGTH
    app.request_class = MSColabRequest
    app.register_error_handler(413, error413)
    # Expose docs path for callers/tests and make it part of Flask config for consistency.
    app.config['DOCS_SERVER_PATH'] = DOCS_SERVER_PATH
    app.route = prefix_route(app.route, SCRIPT_NAME)
    # Keep backward compatibility with callers/tests expecting an app attribute.
    app.xstatic = _xstatic

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    # mslib.utils.auth.send_email sends its messages via current_app.mail
    app.mail = mail

    app.jinja_env.globals.update(file_exists=file_exists)
    app.jinja_env.globals["imprint"] = app.config['IMPRINT'] or ""
    app.jinja_env.globals["gdpr"] = app.config['GDPR'] or ""
    app.jinja_env.globals.update(get_topmenu=get_topmenu)

    from mslib.mscolab.blueprints.admin import ADMIN_BP
    from mslib.mscolab.blueprints.auth import AUTH_BP
    from mslib.mscolab.blueprints.chat import CHAT_BP
    from mslib.mscolab.blueprints.operation import OPERATION_BP
    from mslib.mscolab.blueprints.user import USER_BP
    from mslib.mscolab.blueprints.docs import DOCS_BP

    for bp in (ADMIN_BP, AUTH_BP, CHAT_BP, OPERATION_BP, USER_BP, DOCS_BP):
        app.register_blueprint(bp)

    return app


def get_topmenu():
    menu = [
        (url_for('docs.index'), 'Mission Support System',
         ((url_for('docs.about'), 'About'),
          (url_for('docs.install'), 'Install'),
          (url_for('docs.help'), 'Help'),
          )),
    ]
    return menu
