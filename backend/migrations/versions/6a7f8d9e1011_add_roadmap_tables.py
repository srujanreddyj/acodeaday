"""add roadmap tables

Revision ID: 6a7f8d9e1011
Revises: e1f4a9b72c10
Create Date: 2026-03-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '6a7f8d9e1011'
down_revision: Union[str, Sequence[str], None] = 'e1f4a9b72c10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


roadmap_node_difficulty = postgresql.ENUM('easy', 'med', 'hard', name='roadmapnodedifficulty', create_type=False)
roadmap_item_type = postgresql.ENUM('tutorial', 'template', name='roadmapitemtype', create_type=False)


def upgrade() -> None:
    roadmap_node_difficulty.create(op.get_bind(), checkfirst=True)
    roadmap_item_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'roadmaps',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('total_problem_goal', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )

    op.create_table(
        'roadmap_nodes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('roadmap_id', sa.UUID(), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('difficulty', roadmap_node_difficulty, nullable=False),
        sa.Column('x', sa.Integer(), nullable=False),
        sa.Column('y', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), server_default='220', nullable=False),
        sa.Column('height', sa.Integer(), server_default='96', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['roadmap_id'], ['roadmaps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'roadmap_edges',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('roadmap_id', sa.UUID(), nullable=False),
        sa.Column('source_node_id', sa.UUID(), nullable=False),
        sa.Column('target_node_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['roadmap_id'], ['roadmaps.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_node_id'], ['roadmap_nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_node_id'], ['roadmap_nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'roadmap_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('roadmap_node_id', sa.UUID(), nullable=False),
        sa.Column('item_type', roadmap_item_type, nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('resource_url', sa.Text(), nullable=True),
        sa.Column('code_language', sa.String(length=64), nullable=True),
        sa.Column('group_key', sa.String(length=255), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['roadmap_node_id'], ['roadmap_nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'user_roadmap_item_progress',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('roadmap_item_id', sa.UUID(), nullable=False),
        sa.Column('completed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['roadmap_item_id'], ['roadmap_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'roadmap_node_problems',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('roadmap_node_id', sa.UUID(), nullable=False),
        sa.Column('problem_id', sa.UUID(), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['roadmap_node_id'], ['roadmap_nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'roadmap_node_flashcards',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('roadmap_node_id', sa.UUID(), nullable=False),
        sa.Column('flashcard_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['roadmap_node_id'], ['roadmap_nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['flashcard_id'], ['user_flashcards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('ix_roadmap_nodes_roadmap_id', 'roadmap_nodes', ['roadmap_id'], unique=False)
    op.create_index('ix_roadmap_nodes_slug', 'roadmap_nodes', ['slug'], unique=False)
    op.create_index('ix_roadmap_nodes_roadmap_slug', 'roadmap_nodes', ['roadmap_id', 'slug'], unique=True)
    op.create_index('ix_roadmap_edges_roadmap_id', 'roadmap_edges', ['roadmap_id'], unique=False)
    op.create_index('ix_roadmap_edges_source_node_id', 'roadmap_edges', ['source_node_id'], unique=False)
    op.create_index('ix_roadmap_edges_target_node_id', 'roadmap_edges', ['target_node_id'], unique=False)
    op.create_index('ix_roadmap_items_node_id', 'roadmap_items', ['roadmap_node_id'], unique=False)
    op.create_index('ix_roadmap_items_type', 'roadmap_items', ['item_type'], unique=False)
    op.create_index('ix_user_roadmap_item_progress_user_id', 'user_roadmap_item_progress', ['user_id'], unique=False)
    op.create_index('ix_user_roadmap_item_progress_item_id', 'user_roadmap_item_progress', ['roadmap_item_id'], unique=False)
    op.create_index('ix_user_roadmap_item_progress_unique', 'user_roadmap_item_progress', ['user_id', 'roadmap_item_id'], unique=True)
    op.create_index('ix_roadmap_node_problems_node_id', 'roadmap_node_problems', ['roadmap_node_id'], unique=False)
    op.create_index('ix_roadmap_node_problems_problem_id', 'roadmap_node_problems', ['problem_id'], unique=False)
    op.create_index('ix_roadmap_node_problems_unique', 'roadmap_node_problems', ['roadmap_node_id', 'problem_id'], unique=True)
    op.create_index('ix_roadmap_node_flashcards_node_id', 'roadmap_node_flashcards', ['roadmap_node_id'], unique=False)
    op.create_index('ix_roadmap_node_flashcards_flashcard_id', 'roadmap_node_flashcards', ['flashcard_id'], unique=False)
    op.create_index('ix_roadmap_node_flashcards_unique', 'roadmap_node_flashcards', ['roadmap_node_id', 'flashcard_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_roadmap_node_flashcards_unique', table_name='roadmap_node_flashcards')
    op.drop_index('ix_roadmap_node_flashcards_flashcard_id', table_name='roadmap_node_flashcards')
    op.drop_index('ix_roadmap_node_flashcards_node_id', table_name='roadmap_node_flashcards')
    op.drop_index('ix_roadmap_node_problems_unique', table_name='roadmap_node_problems')
    op.drop_index('ix_roadmap_node_problems_problem_id', table_name='roadmap_node_problems')
    op.drop_index('ix_roadmap_node_problems_node_id', table_name='roadmap_node_problems')
    op.drop_index('ix_user_roadmap_item_progress_unique', table_name='user_roadmap_item_progress')
    op.drop_index('ix_user_roadmap_item_progress_item_id', table_name='user_roadmap_item_progress')
    op.drop_index('ix_user_roadmap_item_progress_user_id', table_name='user_roadmap_item_progress')
    op.drop_index('ix_roadmap_items_type', table_name='roadmap_items')
    op.drop_index('ix_roadmap_items_node_id', table_name='roadmap_items')
    op.drop_index('ix_roadmap_edges_target_node_id', table_name='roadmap_edges')
    op.drop_index('ix_roadmap_edges_source_node_id', table_name='roadmap_edges')
    op.drop_index('ix_roadmap_edges_roadmap_id', table_name='roadmap_edges')
    op.drop_index('ix_roadmap_nodes_roadmap_slug', table_name='roadmap_nodes')
    op.drop_index('ix_roadmap_nodes_slug', table_name='roadmap_nodes')
    op.drop_index('ix_roadmap_nodes_roadmap_id', table_name='roadmap_nodes')

    op.drop_table('roadmap_node_flashcards')
    op.drop_table('roadmap_node_problems')
    op.drop_table('user_roadmap_item_progress')
    op.drop_table('roadmap_items')
    op.drop_table('roadmap_edges')
    op.drop_table('roadmap_nodes')
    op.drop_table('roadmaps')

    roadmap_item_type.drop(op.get_bind(), checkfirst=True)
    roadmap_node_difficulty.drop(op.get_bind(), checkfirst=True)
