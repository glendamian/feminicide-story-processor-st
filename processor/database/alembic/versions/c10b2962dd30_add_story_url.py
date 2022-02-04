"""add story url

Revision ID: c10b2962dd30
Revises: bc600b8d18eb
Create Date: 2022-02-03 20:39:20.544104

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c10b2962dd30'
down_revision = 'bc600b8d18eb'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('stories', sa.Column('url', sa.String))


def downgrade():
    op.drop_column('stories', 'url')
