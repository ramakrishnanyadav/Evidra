from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from core.security import decode_access_token
from models.db import RecruiterRecord
from db.database import get_session

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False
)

# Keep demo fallback for seed endpoint only
DEMO_ORG_ID = UUID("00000000-0000-0000-0000-000000000001")
DEMO_JOB_ID = UUID("00000000-0000-0000-0000-000000000001")

async def get_token_data(
    token: str = Depends(oauth2_scheme)
) -> dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return payload

async def get_current_org(
    token_data: dict = Depends(get_token_data)
) -> UUID:
    return UUID(token_data["organization_id"])

async def get_current_recruiter_id(
    token_data: dict = Depends(get_token_data)
) -> UUID:
    return UUID(token_data["sub"])

async def get_current_job() -> UUID:
    # Job selection will be dynamic in Phase 3
    # For now returns demo job ID within the authenticated org
    return DEMO_JOB_ID

# Special dependency for demo seed endpoint
# Bypasses auth to allow initial data population
async def get_demo_org() -> UUID:
    return DEMO_ORG_ID
