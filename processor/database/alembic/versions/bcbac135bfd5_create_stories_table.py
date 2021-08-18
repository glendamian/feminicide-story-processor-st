"""create stories table

Revision ID: bcbac135bfd5
Revises: 
Create Date: 2021-08-18 15:08:32.421387

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bcbac135bfd5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'stories',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('stories_id', sa.Integer),
        sa.Column('project_id', sa.Integer),
        sa.Column('model_id', sa.Integer),
        sa.Column('model_score', sa.Float),
        sa.Column('published_date', sa.DateTime(), nullable=False),
        sa.Column('queued_date', sa.DateTime()),
        sa.Column('processed_date', sa.DateTime()),
    )
    op.create_index('story_project', 'stories', ['stories_id', 'project_id'],)


def downgrade():
    op.drop_table('stories')
