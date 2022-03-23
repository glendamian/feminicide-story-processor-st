"""add_history_last_url

Revision ID: d9ef1130744f
Revises: c10b2962dd30
Create Date: 2022-02-04 09:30:53.099941

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd9ef1130744f'
down_revision = 'c10b2962dd30'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('projects', sa.Column('last_url', sa.String))


def downgrade():
    op.drop_column('projects', 'last_url')
