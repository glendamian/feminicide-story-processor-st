"""add_google_alerts

Revision ID: bc600b8d18eb
Revises: 222cf71703d4
Create Date: 2022-02-03 14:30:00.433249

"""
from alembic import op
import sqlalchemy as sa
import datetime as dt


# revision identifiers, used by Alembic.
revision = 'bc600b8d18eb'
down_revision = '222cf71703d4'
branch_labels = None
depends_on = None


def upgrade():
    # use the date Media Cloud went down
    op.add_column('projects', sa.Column('last_publish_date', sa.DateTime, default=dt.datetime(2021, 12, 25)))
    op.add_column('stories', sa.Column('source', sa.String, default="media-cloud"))


def downgrade():
    op.drop_column('projects', 'last_publish_date')
    op.drop_column('stories', 'source')
