"""create projects table

Revision ID: f71ecb3adf95
Revises: 7c5e6d44baca
Create Date: 2021-12-20 14:02:28.525226

"""
from alembic import op
import sqlalchemy as sa
import datetime as dt


# revision identifiers, used by Alembic.
revision = 'f71ecb3adf95'
down_revision = '7c5e6d44baca'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('last_processed_id', sa.BigInteger),
        sa.Column('created_at', sa.DateTime(), default=dt.datetime.now),
        sa.Column('updated_at', sa.DateTime(), default=dt.datetime.now, onupdate=dt.datetime.now)
    )


def downgrade():
    op.drop_table('projects')
