"""add standalone flashcards and tags

Revision ID: e1f4a9b72c10
Revises: c3e8d6ab4a11
Create Date: 2026-02-22 10:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e1f4a9b72c10'
down_revision: Union[str, Sequence[str], None] = 'c3e8d6ab4a11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'user_problem_notes',
        sa.Column('tags', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=False),
    )

    op.create_table(
        'user_flashcards',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('problem_id', sa.UUID(), nullable=True),
        sa.Column('front', sa.Text(), nullable=False),
        sa.Column('back', sa.Text(), nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('next_review_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('ix_user_flashcards_user_id', 'user_flashcards', ['user_id'], unique=False)
    op.create_index('ix_user_flashcards_problem_id', 'user_flashcards', ['problem_id'], unique=False)
    op.create_index('ix_user_flashcards_next_review_date', 'user_flashcards', ['next_review_date'], unique=False)
    op.create_index('ix_user_flashcards_user_active', 'user_flashcards', ['user_id', 'is_active'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_user_flashcards_user_active', table_name='user_flashcards')
    op.drop_index('ix_user_flashcards_next_review_date', table_name='user_flashcards')
    op.drop_index('ix_user_flashcards_problem_id', table_name='user_flashcards')
    op.drop_index('ix_user_flashcards_user_id', table_name='user_flashcards')
    op.drop_table('user_flashcards')

    op.drop_column('user_problem_notes', 'tags')
