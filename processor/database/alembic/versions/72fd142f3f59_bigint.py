"""bigint

Revision ID: 72fd142f3f59
Revises: d9ef1130744f
Create Date: 2022-03-25 08:30:13.115592

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '72fd142f3f59'
down_revision = 'd9ef1130744f'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('stories', 'stories_id', type_=sa.BIGINT, postgresql_using='id::BIGINT')


def downgrade():
    op.alter_column('stories', 'stories_id', type_=sa.INT, postgresql_using='id::INT')
