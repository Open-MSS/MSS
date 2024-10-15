# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_migrations
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for database migrations.

    This file is part of MSS.

    :copyright: Copyright 2024 Matthias Riße
    :copyright: Copyright 2024 by the MSS team, see AUTHORS.
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
import pytest
import itertools
import flask
import flask_migrate
import sqlalchemy
import mslib.mscolab.migrations
import mslib.index
from mslib.mscolab.app import db, migrate
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
    # Construct a dummy flask app to create a separate database to migrate from
    # TODO: this would be easier if it was possible to create multiple canonical MSColab Flask app instances,
    # i.e. if there was a factory function instead of one global instance. This test could then check the correct
    # functioning of the data migration while creating such an app instance, instead of having to call a private method.
    app = flask.Flask("whatever")
    # TODO: make this somehow configurable to use something other than sqlite as the source database
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(tmp_path.absolute() / "mscolab.db")
    db.init_app(app)
    migrate.init_app(app, db)
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
        mscolab_settings.SQLALCHEMY_DB_URI_TO_MIGRATE_FROM = app.config["SQLALCHEMY_DATABASE_URI"]
        with mscolab_app.app_context():
            db.drop_all()
            db.session.execute(sqlalchemy.text("DROP TABLE alembic_version"))
            db.session.commit()
            inspector = sqlalchemy.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            assert existing_tables == []

            # Also try multiple applications of the db upgrade to ensure idempotence of the operation
            for _ in range(iterations):
                mslib.mscolab.server._handle_db_upgrade()

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
            assert mslib.mscolab.seed.add_user('test123@test456', 'test123', 'test456')
    finally:
        mscolab_settings.SQLALCHEMY_DB_URI_TO_MIGRATE_FROM = None
