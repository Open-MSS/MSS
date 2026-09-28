"""To version 12.0.0

Revision ID: 3a1c5e2b9d47
Revises: 922e4d9c94e2
Create Date: 2026-09-28 10:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '3a1c5e2b9d47'
down_revision = '922e4d9c94e2'
branch_labels = None
depends_on = None


def upgrade():
    # A user has at most one permission per operation. Older versions could create duplicates,
    # e.g. by adding members to a {category}Group operation. Keep the oldest one, which is the
    # creator permission for the creator of an operation.
    op.execute(
        "DELETE FROM permissions WHERE id NOT IN "
        "(SELECT min_id FROM (SELECT MIN(id) AS min_id FROM permissions GROUP BY u_id, op_id) AS keep)"
    )
    with op.batch_alter_table('permissions', schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f('uq_permissions_u_id'), ['u_id', 'op_id'])


def downgrade():
    with op.batch_alter_table('permissions', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_permissions_u_id'), type_='unique')
