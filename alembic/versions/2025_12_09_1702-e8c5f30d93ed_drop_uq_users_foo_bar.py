"""drop uq_users_foo_bar

Revision ID: e8c5f30d93ed
Revises: e133393acc3f
Create Date: 2025-12-09 17:02:20.420091

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e8c5f30d93ed"
down_revision: Union[str, Sequence[str], None] = "e133393acc3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # снимаем уникальность с (foo, bar)
    op.drop_constraint("uq_users_foo_bar", "users", type_="unique")


def downgrade() -> None:
    # возвращаем (если вдруг понадобится откат)
    op.create_unique_constraint("uq_users_foo_bar", "users", ["foo", "bar"])
