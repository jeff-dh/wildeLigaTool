"""added Game.date

Revision ID: 6618de7e1acd
Revises: 6d23817c897a
Create Date: 2023-03-22 15:44:20.421204

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6618de7e1acd'
down_revision = '6d23817c897a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('games', schema=None) as batch_op:
        batch_op.add_column(sa.Column('date', sa.Date(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('games', schema=None) as batch_op:
        batch_op.drop_column('date')

    # ### end Alembic commands ###
