"""clean up date indexes

Revision ID: 222cf71703d4
Revises: c54fc081afcc
Create Date: 2021-12-22 11:04:26.325158

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '222cf71703d4'
down_revision = 'c54fc081afcc'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('story_published_date_threshold', 'stories', [sa.text('(published_date::date)'), 'above_threshold'])
    op.create_index('story_processed_date_threshold', 'stories', [sa.text('(processed_date::date)'), 'above_threshold'])
    op.create_index('story_posted_date_threshold', 'stories', [sa.text('(posted_date::date)'), 'above_threshold'])


def downgrade():
    pass
