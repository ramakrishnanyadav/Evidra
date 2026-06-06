from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional, Literal
from datetime import datetime, date
import uuid

class AuditLog(BaseModel):
    """Log of events occurring during candidate processing."""
    action: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: str


class EvidenceSource(BaseModel):
    """Source of evidence for a skill or strength."""
    type: str
    label: str
    url: Optional[str] = None
    commit_count: Optional[int] = None
    last_active: Optional[date] = None

class SkillEvidence(BaseModel):
    """Evidence backing a specific skill."""
    skill_name: str
    confidence: str
    sources: List[EvidenceSource] = Field(default_factory=list)
    verified: bool

class HiddenStrength(BaseModel):
    """A strength discovered via GitHub data but not mentioned in resume."""
    domain: str
    description: str
    evidence_repos: List[str] = Field(default_factory=list)
    commit_count: int
    confidence: str

class ReasoningPoint(BaseModel):
    """A specific point of reasoning with evidence."""
    point: str = Field(max_length=100) # Increased max_length
    evidence: str

class ReasoningPanel(BaseModel):
    """Panel detailing the reasoning behind a recommendation."""
    recommendation: str
    top_strengths: List[ReasoningPoint] = Field(default_factory=list)
    concerns: List[ReasoningPoint] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    confidence_band: str
    narrative: str = Field(default="", max_length=400) # Assuming ~60 words max

class AuthenticityIndex(BaseModel):
    """Metrics regarding the authenticity of the candidate's signals."""
    original_repo_ratio: float
    commit_consistency_score: str
    readme_quality_score: str
    has_issue_participation: bool
    signal_note: str

class GitHubRepo(BaseModel):
    name: str
    language: Optional[str] = None
    commits: int
    description: Optional[str] = None

class GitHubSignals(BaseModel):
    repos: List[GitHubRepo] = Field(default_factory=list)
    original_repo_ratio: Optional[float] = None
    readme_depth: Optional[Literal["high", "medium", "low"]] = None

class Education(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[int] = None
    verified: bool = False

class WorkExperience(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    duration_months: Optional[int] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    description: Optional[str] = None
    is_current: bool = False

class CandidateProfile(BaseModel):
    """Complete profile of a candidate."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    organization_id: uuid.UUID = Field(
        default=uuid.UUID("00000000-0000-0000-0000-000000000001")
    )
    job_id: uuid.UUID = Field(
        default=uuid.UUID("00000000-0000-0000-0000-000000000001")
    )
    
    @field_validator('organization_id', mode='before')
    @classmethod
    def organization_id_not_from_user(cls, v):
        return v

    name: Optional[str] = None
    resume_text: str
    github_username: Optional[str] = None
    
    education: List[Education] = Field(default_factory=list)
    work_experience: List[WorkExperience] = Field(default_factory=list)
    total_experience_months: int = 0
    processing_status: Literal["pending", "processing", "completed", "failed"] = "pending"
    github_signals: Optional[GitHubSignals] = None
    extracted_skills: List[SkillEvidence] = Field(default_factory=list)
    hidden_strengths: Optional[List[HiddenStrength]] = None
    recommendation: Literal["shortlist", "review", "pass"]
    reasoning: ReasoningPanel = Field(
        default_factory=lambda: ReasoningPanel(
            recommendation="review",
            top_strengths=[],
            concerns=[],
            missing_information=["Extraction incomplete"],
            confidence_band="low",
            narrative="Insufficient data for complete analysis."
        )
    )
    authenticity_index: AuthenticityIndex = Field(
        default_factory=lambda: AuthenticityIndex(
            original_repo_ratio=0.0,
            commit_consistency_score="insufficient_data",
            readme_quality_score="low",
            has_issue_participation=False,
            signal_note="GitHub analysis pending or unavailable."
        )
    )
    audit_trail: List[AuditLog] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    blind_mode_active: bool = False
