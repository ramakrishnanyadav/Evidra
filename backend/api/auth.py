from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from pydantic import BaseModel, EmailStr
from db.database import get_session
from models.db import OrganizationRecord, RecruiterRecord
from core.security import (
    verify_password,
    get_password_hash,
    create_access_token
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    organization_name: str
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    organization_id: str
    recruiter_id: str
    email: str

@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_session)
):
    # Check email not already registered
    existing = await session.execute(
        select(RecruiterRecord).where(
            RecruiterRecord.email == request.email
        )
    )
    if existing.first():
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Create organization
    org = OrganizationRecord(
        id=uuid4(),
        name=request.organization_name
    )
    session.add(org)

    # Create recruiter
    recruiter = RecruiterRecord(
        id=uuid4(),
        organization_id=org.id,
        email=request.email,
        hashed_password=get_password_hash(request.password)
    )
    session.add(recruiter)
    await session.commit()

    token = create_access_token(
        organization_id=org.id,
        recruiter_id=recruiter.id,
        recruiter_email=recruiter.email
    )

    return TokenResponse(
        access_token=token,
        organization_id=str(org.id),
        recruiter_id=str(recruiter.id),
        email=recruiter.email
    )

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session)
):
    # Find recruiter by email
    result = await session.execute(
        select(RecruiterRecord).where(
            RecruiterRecord.email == form_data.username
        )
    )
    recruiter = result.scalar_one_or_none()

    if not recruiter or not verify_password(
        form_data.password,
        recruiter.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = create_access_token(
        organization_id=recruiter.organization_id,
        recruiter_id=recruiter.id,
        recruiter_email=recruiter.email
    )

    return TokenResponse(
        access_token=token,
        organization_id=str(recruiter.organization_id),
        recruiter_id=str(recruiter.id),
        email=recruiter.email
    )
