"""add above_threshold

Revision ID: 7c5e6d44baca
Revises: d12c2987fc4d
Create Date: 2021-09-01 10:00:30.444304

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c5e6d44baca'
down_revision = 'd12c2987fc4d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('stories', sa.Column('above_threshold', sa.Boolean))


def downgrade():
    op.drop_column('stories', 'above_threshold')
