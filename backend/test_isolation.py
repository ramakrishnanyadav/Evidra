import asyncio
import uuid
import httpx
from db.database import get_session
from models.db import CandidateRecord, OrganizationRecord, JobRecord
from core.dependencies import DEFAULT_JOB_ID

async def test_isolation():
    other_org_id = uuid.UUID("99999999-9999-9999-9999-999999999999")
    
    # Direct DB insert bypassing API
    async for session in get_session():
        # Make sure org exists to satisfy FK
        org = await session.get(OrganizationRecord, other_org_id)
        if not org:
            session.add(OrganizationRecord(id=other_org_id, name="Other Org"))
            
        intruder = CandidateRecord(
            id=uuid.uuid4(),
            organization_id=other_org_id,
            job_id=DEFAULT_JOB_ID,
            name="Should Not Appear",
            resume_text="Some resume",
            recommendation="pass"
        )
        session.add(intruder)
        await session.commit()
        break # only one session needed
    
    # Now call the API and confirm this candidate is absent
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get("http://127.0.0.1:8000/api/v1/candidates")
        data = response.json()
        if "data" in data:
            candidates = data["data"]
        else:
            candidates = data.get("candidates", [])
            
        candidate_names = [c.get("name") for c in candidates]
        assert "Should Not Appear" not in candidate_names, "Isolation Failed! Intruder appeared in results."
        print("ISOLATION VERIFIED — cross-org candidate correctly filtered")

if __name__ == "__main__":
    asyncio.run(test_isolation())
