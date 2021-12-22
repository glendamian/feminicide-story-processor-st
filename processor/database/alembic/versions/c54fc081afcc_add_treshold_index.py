"""add treshold index

Revision ID: c54fc081afcc
Revises: d44d35264428
Create Date: 2021-12-22 10:31:32.925419

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c54fc081afcc'
down_revision = 'd44d35264428'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('story_above_threshold', 'stories', ['above_threshold'])


def downgrade():
    op.drop_index('story_above_threshold')
