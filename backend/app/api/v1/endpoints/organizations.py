from fastapi import APIRouter, Depends

from app.api.deps import get_current_org
from app.models.organization import Organization
from app.schemas.organization import OrganizationOut

router = APIRouter()


@router.get("/organizations/me", response_model=OrganizationOut)
async def get_my_organization(org: Organization = Depends(get_current_org)) -> Organization:
    """Exercises the full auth chain: JWT -> get_current_user -> get_current_org."""
    return org
