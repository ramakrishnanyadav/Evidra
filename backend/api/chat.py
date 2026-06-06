from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, text
from pydantic import BaseModel
from typing import List
from uuid import UUID

from db.database import get_session
from models.db import CandidateRecord
from services.llm import stream_chat_response
from services.embedding import generate_embedding
from core.dependencies import get_current_org

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    job_id: str
    messages: List[ChatMessage]

def build_context_from_rows(rows) -> str:
    parts = []
    for row in rows:
        name = row.name or "Unknown"
        recommendation = row.recommendation or "review"
        similarity = round(row.similarity * 100, 1)
        
        skills = []
        if row.extracted_skills:
            import json
            skill_data = json.loads(row.extracted_skills) if isinstance(row.extracted_skills, str) else row.extracted_skills
            skills = [s.get("skill_name", "") for s in skill_data[:3]]
        
        hidden = ""
        if row.hidden_strengths:
            import json
            hs_data = json.loads(row.hidden_strengths) if isinstance(row.hidden_strengths, str) else row.hidden_strengths
            if hs_data:
                hidden = f" | Hidden: {hs_data[0].get('domain', '')}"
        
        parts.append(
            f"{name} [{recommendation.upper()}] "
            f"Skills: {', '.join(skills)}{hidden} "
            f"(relevance: {similarity}%)"
        )
    
    return "\n".join(parts)

def build_context_from_records(records) -> str:
    parts = []
    for row in records:
        name = row.name or "Unknown"
        recommendation = row.recommendation or "review"
        
        skills = []
        if row.extracted_skills:
            import json
            skill_data = json.loads(row.extracted_skills) if isinstance(row.extracted_skills, str) else row.extracted_skills
            skills = [s.get("skill_name", "") for s in skill_data[:3]]
        
        hidden = ""
        if row.hidden_strengths:
            import json
            hs_data = json.loads(row.hidden_strengths) if isinstance(row.hidden_strengths, str) else row.hidden_strengths
            if hs_data:
                hidden = f" | Hidden: {hs_data[0].get('domain', '')}"
        
        parts.append(
            f"{name} [{recommendation.upper()}] "
            f"Skills: {', '.join(skills)}{hidden} "
            f"(relevance: fallback)"
        )
    
    return "\n".join(parts)

@router.post("")
async def chat_with_recruiter(
    request: ChatRequest,
    org_id: UUID = Depends(get_current_org),
    session: AsyncSession = Depends(get_session)
):
    # Generate embedding for the recruiter's query
    query_embedding = generate_embedding(request.messages[-1].content)
    
    # Vector similarity search with organization isolation
    # Using cosine distance operator <=> for normalized embeddings
    similarity_query = text("""
        SELECT id, name, reasoning, extracted_skills, 
               hidden_strengths, recommendation,
               1 - (embedding <=> CAST(:query_vector AS vector)) as similarity
        FROM candidates
        WHERE organization_id = :org_id
          AND embedding IS NOT NULL
        ORDER BY embedding <=> CAST(:query_vector AS vector)
        LIMIT 5
    """)
    
    result = await session.execute(
        similarity_query,
        {
            "query_vector": str(query_embedding),
            "org_id": str(org_id)
        }
    )
    
    relevant_candidates = result.fetchall()
    
    if not relevant_candidates:
        # Fallback to recency-based if no embeddings exist yet
        fallback_query = select(CandidateRecord).where(
            CandidateRecord.organization_id == org_id
        ).order_by(CandidateRecord.created_at.desc()).limit(5)
        
        fallback_result = await session.execute(fallback_query)
        relevant_candidates_records = fallback_result.scalars().all()
        context = build_context_from_records(relevant_candidates_records)
    else:
        context = build_context_from_rows(relevant_candidates)
    
    api_messages = [{"role": m.role, "content": m.content} for m in request.messages]
    system_prompt = f"""You are a hiring intelligence assistant for Evidra.
You have access to the following candidate profiles most relevant to the recruiter's question.
Answer using only information present in these profiles.
Never fabricate candidate details.
Keep responses under 80 words. Be direct and useful.

RELEVANT CANDIDATE CONTEXT:
{context}"""

    # Inject system prompt at start
    if api_messages and api_messages[0]["role"] == "system":
        api_messages[0]["content"] = system_prompt
    else:
        api_messages.insert(0, {"role": "system", "content": system_prompt})
    
    return StreamingResponse(
        stream_chat_response(api_messages, ""),
        media_type="text/event-stream"
    )
