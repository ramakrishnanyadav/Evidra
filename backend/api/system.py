from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func
import json
import os
from uuid import UUID

from db.database import get_session
from models.db import CandidateRecord
from core.dependencies import get_current_org
from services.embedding import generate_embedding, build_candidate_embedding_text

router = APIRouter()

@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)):
    """Return system status, cached candidate count, and API availability."""
    try:
        result = await session.execute(select(func.count()).select_from(CandidateRecord))
        candidate_count = result.scalar()
        
        from core.config import settings
        featherless_available = bool(settings.FEATHERLESS_API_KEY)
        github_available = bool(settings.GITHUB_TOKEN)
        
        return {
            "status": "ok",
            "candidate_count": candidate_count,
            "api_availability": {
                "featherless": featherless_available,
                "github": github_available
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e), "code": "HEALTH_CHECK_FAILED"})

@router.post("/demo/seed")
async def seed_demo_data(
    org_id: UUID = Depends(get_current_org),
    session: AsyncSession = Depends(get_session)
):
    """Loads pre-built candidate profiles from a local JSON file into the database."""
    try:
        # Check if DB is already seeded for this org to prevent duplication
        result = await session.execute(select(func.count()).select_from(CandidateRecord).where(CandidateRecord.organization_id == org_id))
        count = result.scalar()
        if count > 0:
            return {"status": "ok", "message": "Database already seeded.", "code": "SEED_EXISTS"}

        seed_file_path = os.path.join(os.path.dirname(__file__), "..", "data", "seed.json")
        with open(seed_file_path, "r", encoding="utf-8") as f:
            seed_data = json.load(f)

        from models.domain import CandidateProfile
        from models.db import OrganizationRecord, JobRecord
        from core.dependencies import DEMO_JOB_ID
        
        # We don't need to create the org since the user already belongs to org_id
        
        # Job
        existing_job = await session.get(JobRecord, DEMO_JOB_ID)
        if not existing_job:
            session.add(JobRecord(
                id=DEMO_JOB_ID,
                organization_id=org_id,
                title="Senior Backend Engineer",
                description="Distributed systems, API architecture, Go or Node.js",
                persona_default="startup_generalist"
            ))

        await session.commit()

        for profile_data in seed_data:
            # Generate a new deterministic ID per org to allow multi-tenant testing
            import hashlib
            seed_id = hashlib.md5(f"{org_id}_{profile_data['id']}".encode()).hexdigest()
            new_id = UUID(seed_id)
            
            existing = await session.get(CandidateRecord, new_id)
            if not existing:
                profile_data["id"] = str(new_id)
                profile_data["organization_id"] = str(org_id)
                profile_data["job_id"] = str(DEMO_JOB_ID)
                
                # Parse through domain model to validate and cast types
                profile = CandidateProfile(**profile_data)
                dump = profile.model_dump(mode='json')
                
                # Manually set non-JSON columns to their proper Python types
                dump['id'] = profile.id
                if isinstance(dump['id'], str):
                    dump['id'] = UUID(dump['id'])
                dump['organization_id'] = org_id
                dump['job_id'] = DEMO_JOB_ID
                dump['created_at'] = profile.created_at
                
                record = CandidateRecord(**dump)
                
                profile_dict = record.model_dump()
                embedding_text = build_candidate_embedding_text(profile_dict)
                record.embedding = generate_embedding(embedding_text)
                
                session.add(record)
        
        await session.commit()
        return {"status": "ok", "message": f"Successfully seeded {len(seed_data)} candidates.", "code": "SEED_SUCCESS"}
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail={"status": "error", "message": "Seed file not found.", "code": "SEED_FILE_MISSING"})
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e), "code": "SEED_ERROR"})
