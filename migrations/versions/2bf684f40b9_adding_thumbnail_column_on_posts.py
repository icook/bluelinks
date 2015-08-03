"""Adding thumbnail column on posts

Revision ID: 2bf684f40b9
Revises: 380b0627149
Create Date: 2015-07-30 15:53:43.355410

"""

# revision identifiers, used by Alembic.
revision = '2bf684f40b9'
down_revision = '380b0627149'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('post', sa.Column('thumbnail_path', sa.String(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('post', 'thumbnail_path')
    ### end Alembic commands ###