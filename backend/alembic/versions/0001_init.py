"""init: extensions, organizations, org_members

Revision ID: 0001
Revises:
Create Date: 2026-09-09
"""

from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("registration_number", sa.String(), nullable=True),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column(
            "location",
            geoalchemy2.Geography(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
        sa.Column(
            "verification_status", sa.String(), nullable=False, server_default="pending"
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("type in ('mine','buyer','admin')", name="ck_organizations_type"),
        sa.CheckConstraint(
            "verification_status in ('pending','verified','rejected','suspended')",
            name="ck_organizations_verification_status",
        ),
    )

    op.create_table(
        "org_members",
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "role in ('owner','admin','member','viewer')", name="ck_org_members_role"
        ),
    )


def downgrade() -> None:
    op.drop_table("org_members")
    op.drop_table("organizations")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP EXTENSION IF EXISTS postgis")
