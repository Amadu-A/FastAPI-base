"""expand activation_key to 255

Revision ID: e133393acc3f
Revises: 655d3e998655
Create Date: 2025-12-09 16:32:43.704552

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e133393acc3f"
down_revision: Union[str, Sequence[str], None] = "655d3e998655"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Было VARCHAR(64), делаем VARCHAR(255)
    op.alter_column(
        "users",
        "activation_key",
        existing_type=sa.String(length=64),
        type_=sa.String(length=255),
        existing_nullable=True,
    )


def downgrade() -> None:
    # ОСТОРОЖНО: при откате обрежем значения до 64 символов
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE users
        SET activation_key = LEFT(activation_key, 64)
        WHERE activation_key IS NOT NULL;
    """))
    op.alter_column(
        "users",
        "activation_key",
        existing_type=sa.String(length=255),
        type_=sa.String(length=64),
        existing_nullable=True,
    )