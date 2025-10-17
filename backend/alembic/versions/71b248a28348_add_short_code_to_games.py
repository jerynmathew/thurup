"""add_short_code_to_games

Revision ID: 71b248a28348
Revises: 22dbfa4b623f
Create Date: 2025-10-14 17:50:58.104164

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71b248a28348'
down_revision: Union[str, Sequence[str], None] = '22dbfa4b623f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite doesn't support ALTER COLUMN, so we add the column as non-nullable with a default
    # Note: Since SQLite has limited ALTER TABLE support, we use a workaround
    # For new databases, this column will be non-nullable and indexed
    # For existing databases with data, they'll get temporary codes that should be updated

    # Add short_code column with default value for existing rows
    op.add_column('games', sa.Column('short_code', sa.String(length=50), nullable=False, server_default='temp'))

    # Update existing games with proper short codes
    op.execute("UPDATE games SET short_code = 'temp-' || SUBSTR(id, 1, 8)")

    # Create unique index on short_code
    op.create_index('ix_games_short_code', 'games', ['short_code'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_games_short_code', table_name='games')
    op.drop_column('games', 'short_code')
