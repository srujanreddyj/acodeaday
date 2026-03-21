"""add_user_problem_notes_and_telegram_logs

Revision ID: 9a7c1f0d2e11
Revises: f9b5f87f0cb2
Create Date: 2026-02-20 09:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9a7c1f0d2e11'
down_revision: Union[str, Sequence[str], None] = 'f9b5f87f0cb2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE notificationtype AS ENUM (
                'morning_due',
                'day_solved',
                'evening_pending',
                'morning_flashcards'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
    )

    op.create_table(
        'user_problem_notes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('problem_id', sa.UUID(), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('personal_solution', sa.Text(), nullable=True),
        sa.Column('revision_notes', sa.Text(), nullable=True),
        sa.Column('is_reference_only', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('send_flashcard_to_telegram', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('flashcard_front', sa.Text(), nullable=True),
        sa.Column('flashcard_back', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_problem_notes_user_id', 'user_problem_notes', ['user_id'], unique=False)
    op.create_index('ix_user_problem_notes_problem_id', 'user_problem_notes', ['problem_id'], unique=False)
    op.create_index('ix_user_problem_notes_unique', 'user_problem_notes', ['user_id', 'problem_id'], unique=True)

    op.create_table(
        'telegram_notification_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('notification_date', sa.Date(), nullable=False),
        sa.Column(
            'notification_type',
            postgresql.ENUM(
                'morning_due',
                'day_solved',
                'evening_pending',
                'morning_flashcards',
                name='notificationtype',
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_telegram_logs_user_id', 'telegram_notification_logs', ['user_id'], unique=False)
    op.create_index(
        'ix_telegram_logs_unique',
        'telegram_notification_logs',
        ['user_id', 'notification_date', 'notification_type'],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_telegram_logs_unique', table_name='telegram_notification_logs')
    op.drop_index('ix_telegram_logs_user_id', table_name='telegram_notification_logs')
    op.drop_table('telegram_notification_logs')

    op.drop_index('ix_user_problem_notes_unique', table_name='user_problem_notes')
    op.drop_index('ix_user_problem_notes_problem_id', table_name='user_problem_notes')
    op.drop_index('ix_user_problem_notes_user_id', table_name='user_problem_notes')
    op.drop_table('user_problem_notes')

    op.execute('DROP TYPE IF EXISTS notificationtype')
