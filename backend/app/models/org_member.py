import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.organization import Organization


class OrgMember(Base):
    """Links a Supabase auth user to an organization.

    `user_id` has no foreign key — auth.users lives in Supabase's own schema,
    outside what FastAPI/SQLAlchemy manage (see spec.md section 5.1).
    """

    __tablename__ = "org_members"
    __table_args__ = (
        CheckConstraint("role in ('owner','admin','member','viewer')", name="ck_org_members_role"),
    )

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization"] = relationship(back_populates="members")
