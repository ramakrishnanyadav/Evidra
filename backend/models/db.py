from sqlmodel import SQLModel, Field
from typing import Optional, Any
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid

class OrganizationRecord(SQLModel, table=True):
    __tablename__ = "organizations"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class JobRecord(SQLModel, table=True):
    __tablename__ = "jobs"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    organization_id: uuid.UUID = Field(
        sa_column=Column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    )
    title: str
    description: Optional[str] = None
    persona_default: str = "review"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RecruiterRecord(SQLModel, table=True):
    __tablename__ = "recruiters"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    organization_id: uuid.UUID = Field(
        sa_column=Column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    )
    email: str = Field(unique=True, index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CandidateRecord(SQLModel, table=True):
    """Database model for storing candidate profiles."""
    __tablename__ = "candidates"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    organization_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False
        )
    )
    job_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("jobs.id", ondelete="SET NULL"),
            nullable=True
        )
    )

    name: Optional[str] = None
    resume_text: str
    github_username: Optional[str] = None
    processing_status: str = Field(default="pending")
    
    # Store nested models as JSONB
    education: Any = Field(default=[], sa_column=Column(JSONB))
    work_experience: Any = Field(default=[], sa_column=Column(JSONB))
    github_signals: Optional[Any] = Field(default=None, sa_column=Column(JSONB))
    extracted_skills: Any = Field(default=[], sa_column=Column(JSONB))
    hidden_strengths: Optional[Any] = Field(default=None, sa_column=Column(JSONB))
    recommendation: str = Field(default="review")
    reasoning: Any = Field(default={}, sa_column=Column(JSONB))
    authenticity_index: Any = Field(default={}, sa_column=Column(JSONB))
    audit_trail: Any = Field(default=[], sa_column=Column(JSONB))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    blind_mode_active: bool = Field(default=False)
    embedding: Optional[list] = Field(default=None, sa_column=Column(Vector(384), nullable=True))
