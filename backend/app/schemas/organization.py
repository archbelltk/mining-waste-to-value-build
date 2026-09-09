"""Pydantic response schema for Organization.

Like what you know: this is the Zod schema you'd derive an API response type
from — `model_config = {"from_attributes": True}` lets it read straight off
the SQLAlchemy model instance instead of requiring a manual dict conversion.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    name: str
    registration_number: str | None
    country: str | None
    verification_status: str
    created_at: datetime
