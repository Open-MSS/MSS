# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_migrations
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for database migrations.

    This file is part of MSS.

    :copyright: Copyright 2024 Matthias Riße
    :copyright: Copyright 2024-2026 by the MSS team, see AUTHORS.
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
import copy
import mock
import pytest
import itertools
import flask_migrate
import sqlalchemy
import mslib.mscolab.migrations
import mslib.mscolab.models
import mslib.mscolab.mscolab
import mslib.mscolab.seed
from mslib.mscolab.app import create_app, db, initialise_db
from mslib.mscolab.conf import mscolab_settings


def test_migrations(mscolab_app):
    migrations_path = mslib.mscolab.migrations.__path__[0]
    with mscolab_app.app_context():
        # Seed the database and try to downgrade to each previous revision and then upgrade to the latest again
        mslib.mscolab.mscolab.handle_db_seed()
        # the migrations run on a connection of their own, on PostgreSQL the read locks of an open transaction
        # of the session would block their schema changes
        db.session.commit()
        backward_steps = 1
        all_revisions_tested = False
        while not all_revisions_tested:
            for _ in range(backward_steps):
                try:
                    flask_migrate.downgrade(directory=migrations_path)
                except SystemExit as e:
                    if e.code == 1:
                        all_revisions_tested = True
            flask_migrate.upgrade(directory=migrations_path)
            backward_steps += 1
        # Check that there are no differences between the now-current database schema and the defined model
        try:
            flask_migrate.check(directory=migrations_path)
        except SystemExit as e:
            assert (
                e.code == 0
            ), "The database models are inconsistent with the migration scripts. Did you forget to add a migration?"


_revision_to_name = {
    "92eaba86a92e": "v8",
    "c171019fe3ee": "v9",
}

_cases = list(
    pytest.param(revision, iterations, id=f"{_revision_to_name[revision]}-iterations={iterations}")
    for revision, iterations in itertools.product(["92eaba86a92e", "c171019fe3ee"], [1, 2, 100])
)


@pytest.mark.parametrize("revision,iterations", _cases)
def test_upgrade_from(revision, iterations, mscolab_app, tmp_path):
    """Test upgrading from a pre-v10 database that wasn't yet automatically managed with flask-migrate."""
    migrations_path = mslib.mscolab.migrations.__path__[0]
    # Construct a second app instance to create a separate database to migrate from
    # TODO: make this somehow configurable to use something other than sqlite as the source database
    source_settings = copy.copy(mscolab_settings)
    source_settings.SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(tmp_path.absolute() / "mscolab.db")
    app = create_app(source_settings)
    with app.app_context():
        # Seed the database and downgrade to the supplied revision
        mslib.mscolab.mscolab.handle_db_seed()
        flask_migrate.downgrade(directory=migrations_path, revision=revision)
        # Set the alembic_version to a non-existing revision to simulate a manual migration following the old migration
        # instructions.
        db.session.execute(sqlalchemy.text("UPDATE alembic_version SET version_num = 'e62d08ce88a4'"))
        # Collect all data for comparison with what's copied over
        metadata = sqlalchemy.MetaData()
        metadata.reflect(bind=db.engine)
        expected_data = {name: db.session.execute(table.select()).all() for name, table in metadata.tables.items()}
        del expected_data["alembic_version"]  # the alembic_version table will be different, but that is expected

    try:
        mscolab_app.config['SQLALCHEMY_DATABASE_URI_TO_MIGRATE_FROM'] = app.config["SQLALCHEMY_DATABASE_URI"]
        with mscolab_app.app_context():
            db.drop_all()
            db.session.execute(sqlalchemy.text("DROP TABLE alembic_version"))
            db.session.commit()
            inspector = sqlalchemy.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            assert existing_tables == []

            # Also try multiple applications of the db upgrade to ensure idempotence of the operation
            for _ in range(iterations):
                mslib.mscolab.app.initialise_db()

            # Check that no further migration is required
            flask_migrate.check(directory=migrations_path)
            actual_data = {name: db.session.execute(table.select()).all() for name, table in db.metadata.tables.items()}
            # Check that all tables have the right number of entries with matching ids copied over
            assert {k: [e[0] for e in v] for k, v in expected_data.items()} == {
                k: [e[0] for e in v] for k, v in actual_data.items()
            }
            # TODO: Maybe add more asserts? Basically anything could break with future migrations though, if the schema
            # is fundamentally changed. Having an id as the first column is already an assumption that might not always
            # hold (but should be reliable enough).
            db.session.commit()
            flask_migrate.downgrade(directory=migrations_path, revision=revision)
            metadata = sqlalchemy.MetaData()
            metadata.reflect(bind=db.engine)
            actual_data_after_downgrade = {
                name: db.session.execute(table.select()).all() for name, table in metadata.tables.items()
            }
            del actual_data_after_downgrade["alembic_version"]  # expected data doesn't have the revision table
            # Check that after a downgrade the data is definitely the same
            assert expected_data == actual_data_after_downgrade

            # Try to add a new user after the migration
            db.session.commit()
            flask_migrate.upgrade(directory=migrations_path)
            assert mslib.mscolab.seed.add_user('test123@test456', 'test123', 'test456', 'User test789')
    finally:
        mscolab_app.config['SQLALCHEMY_DATABASE_URI_TO_MIGRATE_FROM'] = None


def test_upgrade_removes_duplicate_permissions(mscolab_app):
    """Duplicate permissions of older versions are reduced to the one with the highest access level."""
    migrations_path = mslib.mscolab.migrations.__path__[0]
    with mscolab_app.app_context():
        mslib.mscolab.mscolab.handle_db_seed()
        flask_migrate.downgrade(directory=migrations_path, revision="922e4d9c94e2")
        creator = db.session.execute(sqlalchemy.text(
            "SELECT u_id, op_id FROM permissions WHERE access_level = 'creator' ORDER BY id")).first()
        other_user = db.session.execute(sqlalchemy.text(
            "SELECT id FROM users WHERE id != :u_id ORDER BY id"), {"u_id": creator.u_id}).first()
        db.session.execute(sqlalchemy.text(
            "DELETE FROM permissions WHERE u_id = :u_id AND op_id = :op_id"),
            {"u_id": other_user.id, "op_id": creator.op_id})
        insert = sqlalchemy.text("INSERT INTO permissions (op_id, u_id, access_level) VALUES (:op_id, :u_id, :level)")
        # the older fan-out added the creator a second time, the newer duplicate must not win
        db.session.execute(insert, {"op_id": creator.op_id, "u_id": creator.u_id, "level": "viewer"})
        for level in ("viewer", "admin", "collaborator", "admin"):
            db.session.execute(insert, {"op_id": creator.op_id, "u_id": other_user.id, "level": level})
        db.session.commit()

        flask_migrate.upgrade(directory=migrations_path)
        levels = {row.u_id: row.access_level for row in db.session.execute(sqlalchemy.text(
            "SELECT id, u_id, access_level FROM permissions WHERE op_id = :op_id ORDER BY id"),
            {"op_id": creator.op_id})}
        assert levels[creator.u_id] == "creator"
        assert levels[other_user.id] == "admin"
        counts = db.session.execute(sqlalchemy.text(
            "SELECT COUNT(*) FROM permissions WHERE op_id = :op_id AND u_id IN (:creator, :other)"),
            {"op_id": creator.op_id, "creator": creator.u_id, "other": other_user.id}).scalar()
        assert counts == 2


def test_upgrade_gives_every_user_a_token_nonce(mscolab_app):
    """Users of a database before 12.0.0 get a random token nonce of their own."""
    migrations_path = mslib.mscolab.migrations.__path__[0]
    with mscolab_app.app_context():
        mslib.mscolab.mscolab.handle_db_seed()
        flask_migrate.downgrade(directory=migrations_path, revision="922e4d9c94e2")
        flask_migrate.upgrade(directory=migrations_path)
        nonces = [row.token_nonce for row in db.session.execute(sqlalchemy.text("SELECT token_nonce FROM users"))]
        assert len(nonces) > 1
        assert all(isinstance(nonce, str) and len(nonce) == 32 for nonce in nonces)
        assert len(set(nonces)) == len(nonces)


def _remove_token_nonce():
    # the state of a development database that ran the 12.0.0 migration before token_nonce was added to it
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from mslib.mscolab.migrations.schema_repair import sqlite_foreign_keys_off
    db.session.remove()
    # the batch mode recreates the table on SQLite, like a migration
    with db.engine.connect() as conn, sqlite_foreign_keys_off(conn), conn.begin():
        with Operations(MigrationContext.configure(conn)).batch_alter_table('users') as batch_op:
            batch_op.drop_column('token_nonce')
    db.session.remove()


def _columns_of_users():
    db.session.remove()
    return {column["name"] for column in sqlalchemy.inspect(db.engine).get_columns("users")}


def test_reset_of_database_without_token_nonce(mscolab_app):
    """mscolab db --reset downgrades through the 12.0.0 migration, also without the column"""
    with mscolab_app.app_context():
        mslib.mscolab.mscolab.handle_db_seed()
        _remove_token_nonce()
        assert "token_nonce" not in _columns_of_users()
        mslib.mscolab.mscolab.handle_db_reset(verbose=False)
        assert "token_nonce" in _columns_of_users()


def test_repair_of_database_without_token_nonce(mscolab_app):
    """The server start adds the column to such a database, every user gets a nonce and can log in again"""
    # the upgrade reconfigures logging (alembic's env.py), so caplog doesn't see the warning
    with mscolab_app.app_context():
        mslib.mscolab.mscolab.handle_db_seed()
        _remove_token_nonce()
        with mock.patch("mslib.mscolab.app.logging.warning") as warning:
            initialise_db()
        assert "earlier development state of the 12.0.0 migration" in warning.call_args.args[0]
        nonces = [row.token_nonce for row in db.session.execute(sqlalchemy.text("SELECT token_nonce FROM users"))]
        assert len(nonces) > 1 and len(set(nonces)) == len(nonces)
        user = mslib.mscolab.seed.get_user("a@notexisting.org")
        assert mslib.mscolab.models.User.verify_auth_token(user.generate_auth_token()).id == user.id
        # nothing to repair any more
        with mock.patch("mslib.mscolab.app.logging.warning") as warning:
            initialise_db()
        warning.assert_not_called()


_DELETED = 999999  # the id of a user and of an operation deleted by an older version


def _insert_dangling_rows():
    """
    Rows as older versions left them behind, referring to a deleted user or operation; returns their ids

    The foreign keys have to be bypassed for this: on SQLite they are switched off, on PostgreSQL its triggers.
    """
    db.session.remove()
    with db.engine.connect() as conn:
        sqlite = conn.dialect.name == "sqlite"
        conn.exec_driver_sql("PRAGMA foreign_keys=OFF" if sqlite else "SET session_replication_role = replica")
        conn.commit()
        op_id = conn.execute(sqlalchemy.text("SELECT id FROM operations ORDER BY id")).scalar()
        u_id = conn.execute(sqlalchemy.text("SELECT id FROM users ORDER BY id")).scalar()

        def insert(statement, **values):
            return conn.execute(sqlalchemy.text(statement + " RETURNING id"), values).scalar()

        message = "INSERT INTO messages (op_id, u_id, text, message_type, reply_id) " \
                  "VALUES (:op_id, :u_id, :text, 'TEXT', :reply_id)"
        change = "INSERT INTO changes (op_id, u_id, commit_hash) VALUES (:op_id, :u_id, 'abc')"
        permission = "INSERT INTO permissions (op_id, u_id, access_level) VALUES (:op_id, :u_id, 'collaborator')"
        ids = {
            "message_of_deleted_user": insert(message, op_id=op_id, u_id=_DELETED, text="kept", reply_id=None),
            "change_of_deleted_user": insert(change, op_id=op_id, u_id=_DELETED),
        }
        ids["message_of_deleted_operation"] = insert(message, op_id=_DELETED, u_id=u_id, text="gone", reply_id=None)
        ids["reply_to_removed_message"] = insert(message, op_id=op_id, u_id=u_id, text="reply",
                                                 reply_id=ids["message_of_deleted_operation"])
        ids["change_of_deleted_operation"] = insert(change, op_id=_DELETED, u_id=u_id)
        ids["reply_to_missing_message"] = insert(message, op_id=op_id, u_id=u_id, text="reply", reply_id=_DELETED)
        ids["permission_of_deleted_user"] = insert(permission, op_id=op_id, u_id=_DELETED)
        ids["permission_of_deleted_operation"] = insert(permission, op_id=_DELETED, u_id=u_id)
        conn.commit()
        conn.exec_driver_sql("PRAGMA foreign_keys=ON" if sqlite else "SET session_replication_role = origin")
        conn.commit()
    return ids


def _assert_repaired(ids):
    def row(statement, row_id):
        return db.session.execute(sqlalchemy.text(statement), {"id": row_id}).first()

    message = "SELECT u_id, reply_id FROM messages WHERE id = :id"
    # the messages and changes of a deleted user stay, without the user
    assert row(message, ids["message_of_deleted_user"]) == (None, None)
    assert row("SELECT u_id FROM changes WHERE id = :id", ids["change_of_deleted_user"]) == (None,)
    # the rows of a deleted operation and the permissions of a deleted user go
    assert row(message, ids["message_of_deleted_operation"]) is None
    assert row("SELECT id FROM changes WHERE id = :id", ids["change_of_deleted_operation"]) is None
    for permission in ("permission_of_deleted_user", "permission_of_deleted_operation"):
        assert row("SELECT id FROM permissions WHERE id = :id", ids[permission]) is None
    # a reply to a removed or missing message stays, as a message of its own
    assert row(message, ids["reply_to_removed_message"])[1] is None
    assert row(message, ids["reply_to_missing_message"])[1] is None


def test_upgrade_repairs_rows_of_deleted_users_and_operations(mscolab_app):
    migrations_path = mslib.mscolab.migrations.__path__[0]
    with mscolab_app.app_context():
        mslib.mscolab.mscolab.handle_db_seed()
        db.session.commit()
        flask_migrate.downgrade(directory=migrations_path, revision="922e4d9c94e2")
        ids = _insert_dangling_rows()
        flask_migrate.upgrade(directory=migrations_path)
        _assert_repaired(ids)


def test_server_start_repairs_rows_of_deleted_users_and_operations(mscolab_app):
    """a development database that ran the 12.0.0 migration before the repair was added to it"""
    with mscolab_app.app_context():
        mslib.mscolab.mscolab.handle_db_seed()
        ids = _insert_dangling_rows()
        with mock.patch("mslib.mscolab.app.logging.warning") as warning:
            initialise_db()
        assert "referred to a deleted user or operation" in warning.call_args.args[0]
        _assert_repaired(ids)


def test_ids_of_deleted_users_are_not_reused(mscolab_app):
    # SQLite gave a new user the id of the deleted user with the highest id, a socket or token of that one could
    # then belong to the new one
    with mscolab_app.app_context():
        assert mslib.mscolab.seed.add_user("first@example.org", "first", "first-password", "First")
        assert mslib.mscolab.seed.add_user("last@example.org", "last", "last-password", "Last")
        deleted_id = mslib.mscolab.seed.get_user("last@example.org").id
        assert mslib.mscolab.seed.delete_user("last@example.org")
        assert mslib.mscolab.seed.add_user("new@example.org", "new", "new-password", "New")
        assert mslib.mscolab.seed.get_user("new@example.org").id > deleted_id


def test_migrate_from_repairs_rows_of_deleted_users_and_operations(mscolab_app, tmp_path):
    """The copy of an old database with SQLALCHEMY_DATABASE_URI_TO_MIGRATE_FROM, the target enforces foreign keys"""
    migrations_path = mslib.mscolab.migrations.__path__[0]
    source_settings = copy.copy(mscolab_settings)
    source_settings.SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(tmp_path.absolute() / "mscolab.db")
    app = create_app(source_settings)
    with app.app_context():
        mslib.mscolab.mscolab.handle_db_seed()
        db.session.commit()
        flask_migrate.downgrade(directory=migrations_path, revision="c171019fe3ee")
        ids = _insert_dangling_rows()
        db.session.execute(sqlalchemy.text("UPDATE alembic_version SET version_num = 'e62d08ce88a4'"))
        db.session.commit()
        db.session.remove()
        db.engine.dispose()
    try:
        mscolab_app.config['SQLALCHEMY_DATABASE_URI_TO_MIGRATE_FROM'] = source_settings.SQLALCHEMY_DATABASE_URI
        with mscolab_app.app_context():
            db.drop_all()
            db.session.execute(sqlalchemy.text("DROP TABLE alembic_version"))
            db.session.commit()
            with mock.patch("mslib.mscolab.app.logging.warning") as warning:
                initialise_db()
            assert any("referred to a deleted user or operation" in call.args[0] for call in warning.call_args_list)
            _assert_repaired(ids)
    finally:
        mscolab_app.config['SQLALCHEMY_DATABASE_URI_TO_MIGRATE_FROM'] = None


def _drop_users_column(column):
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from mslib.mscolab.migrations.schema_repair import sqlite_foreign_keys_off
    db.session.remove()
    with db.engine.connect() as conn, sqlite_foreign_keys_off(conn), conn.begin():
        with Operations(MigrationContext.configure(conn)).batch_alter_table('users') as batch_op:
            batch_op.drop_column(column)
    db.session.remove()


def test_upgrade_of_a_database_of_10_x_without_fullname(mscolab_app):
    """the migration of 10.0.0 as 10.x released it had no users.fullname, 11.0.0 added it there later"""
    migrations_path = mslib.mscolab.migrations.__path__[0]
    with mscolab_app.app_context():
        mslib.mscolab.mscolab.handle_db_seed()
        db.session.commit()
        flask_migrate.downgrade(directory=migrations_path, revision="922e4d9c94e2")
        _drop_users_column("fullname")
        assert "fullname" not in _columns_of_users()
        flask_migrate.upgrade(directory=migrations_path)
        assert "fullname" in _columns_of_users()
        # the users can be read and log in
        user = mslib.mscolab.seed.get_user("a@notexisting.org")
        assert mslib.mscolab.models.User.verify_auth_token(user.generate_auth_token()).id == user.id


def test_repair_of_a_database_upgraded_from_10_x_without_fullname(mscolab_app):
    """e.g. a server of 10.x upgraded to 11.0.0 and then to a development state of 12.0.0"""
    with mscolab_app.app_context():
        mslib.mscolab.mscolab.handle_db_seed()
        _drop_users_column("fullname")
        with mock.patch("mslib.mscolab.app.logging.warning") as warning:
            initialise_db()
        assert any("users.fullname" in call.args[0] for call in warning.call_args_list)
        assert "fullname" in _columns_of_users()


def test_new_rows_after_the_seed(mscolab_app, mscolab_managers):
    # the seed sets the ids of its users and operations; on PostgreSQL the next new row got one of them
    _, _, fm = mscolab_managers
    with mscolab_app.app_context():
        mslib.mscolab.mscolab.handle_db_seed()
        assert fm.create_operation("after_seed", "description", mslib.mscolab.seed.get_user("a@notexisting.org"),
                                   content=mslib.mscolab.seed.XML_CONTENT_INIT)
        assert mslib.mscolab.seed.add_user("after_seed@example.org", "after_seed", "a-password", "After Seed")


def test_server_start_moves_lagging_sequences_forward_only(mscolab_app, mscolab_managers):
    _, _, fm = mscolab_managers
    with mscolab_app.app_context():
        mslib.mscolab.mscolab.handle_db_seed()
        if db.engine.dialect.name == "postgresql":
            # a database seeded by an earlier state of the seed
            for table in ("users", "operations"):
                db.session.execute(sqlalchemy.text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), 1)"))
            db.session.commit()
        initialise_db()
        assert fm.create_operation("after_repair", "description", mslib.mscolab.seed.get_user("a@notexisting.org"),
                                   content=mslib.mscolab.seed.XML_CONTENT_INIT)
        # the user with the highest id is deleted, the next start must not hand its id out again
        assert mslib.mscolab.seed.add_user("highest@example.org", "highest", "a-password", "Highest")
        deleted_id = mslib.mscolab.seed.get_user("highest@example.org").id
        assert deleted_id == db.session.execute(sqlalchemy.text("SELECT MAX(id) FROM users")).scalar()
        assert mslib.mscolab.seed.delete_user("highest@example.org")
        initialise_db()
        assert mslib.mscolab.seed.add_user("new@example.org", "new", "a-password", "New")
        assert mslib.mscolab.seed.get_user("new@example.org").id > deleted_id
