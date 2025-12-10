"""cascade deletes + trigger profile->user

Revision ID: 87f35af16311
Revises: e8c5f30d93ed
Create Date: 2025-12-10 14:36:51.024796

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "87f35af16311"
down_revision: Union[str, Sequence[str], None] = "e8c5f30d93ed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) Пересоздаем FK с ON DELETE CASCADE
    op.drop_constraint(op.f("fk_profiles_user_id_users"), "profiles", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_profiles_user_id_users"),
        "profiles",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(op.f("fk_permissions_profile_id_profiles"), "permissions", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_permissions_profile_id_profiles"),
        "permissions",
        "profiles",
        ["profile_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 2) Функция триггера (одна команда — можно в одном op.execute)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION delete_user_on_profile_delete()
        RETURNS trigger AS $$
        BEGIN
            DELETE FROM users WHERE id = OLD.user_id;
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # 3) Триггер — РАЗДЕЛЬНО (каждая команда в своем op.execute)
    op.execute("DROP TRIGGER IF EXISTS trg_delete_user_on_profile_delete ON profiles;")
    op.execute(
        """
        CREATE TRIGGER trg_delete_user_on_profile_delete
        AFTER DELETE ON profiles
        FOR EACH ROW
        EXECUTE FUNCTION delete_user_on_profile_delete();
        """
    )


def downgrade():
    # Удаляем триггер и функцию
    op.execute("DROP TRIGGER IF EXISTS trg_delete_user_on_profile_delete ON profiles;")
    op.execute("DROP FUNCTION IF EXISTS delete_user_on_profile_delete();")

    # Возвращаем FK без каскада
    op.drop_constraint(op.f("fk_permissions_profile_id_profiles"), "permissions", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_permissions_profile_id_profiles"),
        "permissions",
        "profiles",
        ["profile_id"],
        ["id"],
        ondelete=None,
    )

    op.drop_constraint(op.f("fk_profiles_user_id_users"), "profiles", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_profiles_user_id_users"),
        "profiles",
        "users",
        ["user_id"],
        ["id"],
        ondelete=None,
    )
