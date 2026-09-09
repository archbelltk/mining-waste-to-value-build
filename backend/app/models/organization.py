from datetime import datetime
from typing import TYPE_CHECKING

from geoalchemy2 import Geography
from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.org_member import OrgMember


class Organization(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "organizations"
    __table_args__ = (
        CheckConstraint("type in ('mine','buyer','admin')", name="ck_organizations_type"),
        CheckConstraint(
            "verification_status in ('pending','verified','rejected','suspended')",
            name="ck_organizations_verification_status",
        ),
    )

    type: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    registration_number: Mapped[str | None] = mapped_column(String)
    country: Mapped[str | None] = mapped_column(String)
    location: Mapped[str | None] = mapped_column(Geography(geometry_type="POINT", srid=4326))
    verification_status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    members: Mapped[list["OrgMember"]] = relationship(back_populates="organization")
