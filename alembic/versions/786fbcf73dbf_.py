"""empty message

Revision ID: 786fbcf73dbf
Revises: 1d62efd58836
Create Date: 2023-06-19 23:24:01.637400

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '786fbcf73dbf'
down_revision = '1d62efd58836'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('jwt_tokens_blacklist',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('token', sa.String(length=32), nullable=False),
    sa.Column('email', sa.String(length=150), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('jwt_tokens_blacklist')
    # ### end Alembic commands ###
