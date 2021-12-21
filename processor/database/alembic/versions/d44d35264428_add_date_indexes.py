"""add date indexes

Revision ID: d44d35264428
Revises: 7ebd8bc4f48f
Create Date: 2021-12-21 12:44:08.745568

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd44d35264428'
down_revision = '7ebd8bc4f48f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('story_project_id', 'stories', ['project_id'])
    op.create_index('story_published_date', 'stories', [sa.text('(published_date::date)')])
    op.create_index('story_processed_date', 'stories', [sa.text('(processed_date::date)')])
    op.create_index('story_posted_date', 'stories', [sa.text('(posted_date::date)')])


def downgrade():
    op.drop_index('story_project_id')
    op.drop_index('story_published_date')
    op.drop_index('story_processed_date')
    op.drop_index('story_posted_date')
