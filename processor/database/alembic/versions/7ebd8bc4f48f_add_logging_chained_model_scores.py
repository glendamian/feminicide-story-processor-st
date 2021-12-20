"""add logging chained model scores

Revision ID: 7ebd8bc4f48f
Revises: f71ecb3adf95
Create Date: 2021-12-20 15:33:52.135299

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7ebd8bc4f48f'
down_revision = 'f71ecb3adf95'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('stories', sa.Column('model_1_score', sa.Float))
    op.add_column('stories', sa.Column('model_2_score', sa.Float))


def downgrade():
    op.drop_column('stories', 'model_1_score')
    op.drop_column('stories', 'model_2_score')
