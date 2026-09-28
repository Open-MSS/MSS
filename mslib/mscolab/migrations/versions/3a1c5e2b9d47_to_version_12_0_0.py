"""To version 12.0.0

Revision ID: 3a1c5e2b9d47
Revises: 922e4d9c94e2
Create Date: 2026-09-28 10:00:00.000000

"""
import logging

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '3a1c5e2b9d47'
down_revision = '922e4d9c94e2'
branch_labels = None
depends_on = None


# the highest access level wins when a user has more than one permission on an operation
_ACCESS_LEVEL_RANK = {"creator": 3, "admin": 2, "collaborator": 1, "viewer": 0}


def upgrade():
    # A user has at most one permission per operation. Older versions could create duplicates,
    # e.g. by adding members to a {category}Group operation. Keep the one with the highest
    # access level, and of those the oldest.
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, u_id, op_id, access_level FROM permissions ORDER BY id")).fetchall()
    keep = {}
    duplicate_ids = []
    for row in rows:
        key = (row.u_id, row.op_id)
        kept = keep.get(key)
        if kept is None:
            keep[key] = row
        elif _ACCESS_LEVEL_RANK.get(row.access_level, -1) > _ACCESS_LEVEL_RANK.get(kept.access_level, -1):
            duplicate_ids.append(kept.id)
            keep[key] = row
        else:
            duplicate_ids.append(row.id)
    if duplicate_ids:
        conn.execute(sa.text("DELETE FROM permissions WHERE id IN :ids")
                     .bindparams(sa.bindparam("ids", expanding=True)), {"ids": duplicate_ids})

    # Older versions could also downgrade or remove the creator through a {category}Group operation.
    # Who created such an operation is not recorded elsewhere, so this can't be repaired automatically.
    creator_op_ids = {row.op_id for row in keep.values() if row.access_level == "creator"}
    for (op_id,) in conn.execute(sa.text("SELECT id FROM operations ORDER BY id")).fetchall():
        if op_id not in creator_op_ids:
            logging.warning("operation %s has no creator, only a creator can delete it", op_id)

    with op.batch_alter_table('permissions', schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f('uq_permissions_u_id'), ['u_id', 'op_id'])


def downgrade():
    with op.batch_alter_table('permissions', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_permissions_u_id'), type_='unique')
