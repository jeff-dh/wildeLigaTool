"""empty message

Revision ID: 49dfe63e0b0d
Revises: 6618de7e1acd
Create Date: 2023-03-24 10:38:37.830740

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '49dfe63e0b0d'
down_revision = '6618de7e1acd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('games', schema=None) as batch_op:
        batch_op.alter_column('home_team_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('visiting_team_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('home_team_pts',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('visiting_team_pts',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('date',
               existing_type=sa.DATE(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('games', schema=None) as batch_op:
        batch_op.alter_column('date',
               existing_type=sa.DATE(),
               nullable=True)
        batch_op.alter_column('visiting_team_pts',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.alter_column('home_team_pts',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.alter_column('visiting_team_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.alter_column('home_team_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    # ### end Alembic commands ###
