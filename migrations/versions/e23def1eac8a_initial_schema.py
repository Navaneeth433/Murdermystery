"""initial schema

Revision ID: e23def1eac8a
Revises: 
Create Date: 2026-02-25 13:37:21.012212

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e23def1eac8a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )

    # Create contents table
    op.create_table(
        'contents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('time_limit', sa.Integer(), nullable=False),
        sa.Column('is_unlocked', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('chapter_number', sa.Integer(), nullable=False),
        sa.Column('unlock_time', sa.DateTime(), nullable=True),
        sa.Column('requires_previous_completion', sa.Boolean(), nullable=False),
        sa.Column('panels_json', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create attempts table
    op.create_table(
        'attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('time_taken', sa.Integer(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'content_id', name='unique_user_content_attempt'),
    )


def downgrade():
    op.drop_table('attempts')
    op.drop_table('contents')
    op.drop_table('users')
