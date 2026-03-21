"""merge heads after user notes

Revision ID: c3e8d6ab4a11
Revises: b7c09ca0d8a9, 9a7c1f0d2e11
Create Date: 2026-02-22 09:46:00.000000

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "c3e8d6ab4a11"
down_revision: Union[str, Sequence[str], None] = ("b7c09ca0d8a9", "9a7c1f0d2e11")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge migration; schema changes are in parent revisions."""
    pass


def downgrade() -> None:
    """No-op downgrade for merge migration."""
    pass
