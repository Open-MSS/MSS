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
    with db.engine.begin() as conn:
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
