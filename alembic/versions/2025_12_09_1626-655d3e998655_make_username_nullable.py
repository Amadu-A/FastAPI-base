"""make username nullable

Revision ID: 655d3e998655
Revises: 33aa3a368fa8
Create Date: 2025-12-09 16:26:43.983839

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "655d3e998655"
down_revision: Union[str, Sequence[str], None] = "33aa3a368fa8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Делаем username nullable=True
    op.alter_column("users", "username", existing_type=sa.String(length=64), nullable=True)


def downgrade() -> None:
    # Откат осторожный: перед запретом NULL нужно заполнить пустые username
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE users
        SET username = 'user_' || id::text
        WHERE username IS NULL
    """))
    op.alter_column("users", "username", existing_type=sa.String(length=64), nullable=False)
