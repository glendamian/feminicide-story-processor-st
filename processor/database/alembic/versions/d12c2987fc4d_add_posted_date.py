"""add posted_date

Revision ID: d12c2987fc4d
Revises: bcbac135bfd5
Create Date: 2021-09-01 09:53:40.324450

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd12c2987fc4d'
down_revision = 'bcbac135bfd5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('stories', sa.Column('posted_date', sa.DateTime))


def downgrade():
    op.drop_column('stories', 'posted_date')
