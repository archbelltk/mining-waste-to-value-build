"""Shared FastAPI dependencies.

This is the one place tenant-scoping is resolved (spec.md section 6): every
endpoint that touches a tenant-scoped table depends on `get_current_org` and
filters its query by `org.id` — never by an `org_id` taken from the request
body or query string. There is no database RLS backing this up, so this
dependency (and test_tenant_isolation.py, added once there's a tenant-scoped
table to test) is the whole safety net.

Like what you know: `Depends(...)` plays the role Express middleware plays,
except it's resolved per-parameter instead of mutating a shared `req` object.
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    AuthenticatedUser,
    InvalidTokenError,
    decode_access_token,
    unauthorized,
)
from app.models.org_member import OrgMember
from app.models.organization import Organization

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    if credentials is None:
        raise unauthorized()
    try:
        return decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise unauthorized(str(exc)) from exc


async def get_current_org(
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    """Resolves the caller's organization from their JWT `sub` claim via
    org_members, or raises 403. A user belonging to more than one org isn't
    supported yet — the first membership found wins (revisit in Phase 1)."""
    result = await db.execute(
        select(Organization)
        .join(OrgMember, OrgMember.org_id == Organization.id)
        .where(OrgMember.user_id == uuid.UUID(user.id))
    )
    org = result.scalars().first()
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of any organization",
        )
    return org


def require_org_type(*allowed: str):
    """Dependency factory: require_org_type('mine') blocks buyer/admin tokens
    from hitting mine-only endpoints."""

    async def _check(org: Organization = Depends(get_current_org)) -> Organization:
        if org.type not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires organization type in {allowed}",
            )
        return org

    return _check
