import asyncio
import uuid
from datetime import datetime
from db.database import get_session
from models.db import CandidateRecord
from models.domain import CandidateProfile

async def main():
    profile_data = {
        "name": "Test User",
        "resume_text": "This is a test resume that is long enough. " * 10,
        "github_username": "testuser",
        "processing_status": "completed",
        "recommendation": "shortlist",
        "extracted_skills": [],
        "reasoning": {
            "recommendation": "shortlist",
            "top_strengths": [],
            "concerns": [],
            "missing_information": [],
            "confidence_band": "high",
            "narrative": "test"
        },
        "authenticity_index": {
            "original_repo_ratio": 1.0,
            "commit_consistency_score": "high",
            "readme_quality_score": "high",
            "has_issue_participation": False,
            "signal_note": "test"
        }
    }
    
    try:
        profile = CandidateProfile(**profile_data)
        dump = profile.model_dump(mode='json')
        dump['id'] = profile.id
        dump['created_at'] = profile.created_at
        
        record = CandidateRecord(**dump)
        
        async for session in get_session():
            try:
                session.add(record)
                await session.commit()
                print("Success")
            except Exception as e:
                print(f"DB Error: {e}")
            finally:
                break
    except Exception as e:
        print(f"Pydantic Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
