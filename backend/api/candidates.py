from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import tuple_
from sqlmodel import select
from typing import List, Optional, Literal
import uuid
from datetime import datetime
import pdfplumber
import io

from db.database import get_session
from models.db import CandidateRecord
from models.domain import CandidateProfile, HiddenStrength, AuditLog
from services.llm import extract_resume_data, discover_hidden_talents, stream_chat_response, calculate_total_experience_months
from services.github import fetch_github_signals
from core.dependencies import get_current_org, get_current_job

router = APIRouter()

@router.get("", response_model=dict)
async def list_candidates(
    cursor: Optional[str] = Query(None, description="Cursor for pagination (created_at timestamp)"),
    limit: int = Query(100, le=500, description="Number of items to return"),
    session: AsyncSession = Depends(get_session),
    current_org: uuid.UUID = Depends(get_current_org)
):
    """Get paginated list of candidates using cursor-based pagination."""
    query = select(CandidateRecord).where(CandidateRecord.organization_id == current_org).order_by(
        CandidateRecord.created_at.desc(),
        CandidateRecord.id.desc()
    )
    if cursor:
        try:
            cursor_date_str, cursor_id_str = cursor.split('_')
            cursor_date = datetime.fromisoformat(cursor_date_str)
            cursor_id = uuid.UUID(cursor_id_str)
            query = query.where(tuple_(CandidateRecord.created_at, CandidateRecord.id) < (cursor_date, cursor_id))
        except ValueError:
            pass
    query = query.limit(limit)
    
    result = await session.execute(query)
    records = result.scalars().all()
    
    candidates = [CandidateProfile.model_validate(record) for record in records]
    
    next_cursor = None
    if len(records) == limit:
        next_cursor = f"{records[-1].created_at.isoformat()}_{records[-1].id}"
        
    return {
        "data": candidates,
        "next_cursor": next_cursor
    }

from pydantic import BaseModel
class SearchQuery(BaseModel):
    query: str
    job_id: Optional[uuid.UUID] = None

@router.post("/search")
async def semantic_search(
    search_req: SearchQuery,
    session: AsyncSession = Depends(get_session),
    current_org: uuid.UUID = Depends(get_current_org)
):
    """Semantic search over candidates."""
    from services.embedding import generate_embedding
    import numpy as np
    
    query_vector = generate_embedding(search_req.query)
    query_np = np.array(query_vector)
    
    stmt = select(CandidateRecord).where(
        CandidateRecord.organization_id == current_org,
        CandidateRecord.embedding.is_not(None)
    )
    if search_req.job_id:
        stmt = stmt.where(CandidateRecord.job_id == search_req.job_id)
        
    result = await session.execute(stmt)
    records = result.scalars().all()
    
    scored_records = []
    for r in records:
        if r.embedding is None:
            continue
        
        # pgvector returns a list or string depending on driver, handle both
        import json
        emb = r.embedding
        if isinstance(emb, str):
            try:
                emb = json.loads(emb)
            except:
                continue
                
        candidate_np = np.array(emb)
        # Cosine similarity for normalized vectors is just dot product
        sim = float(np.dot(query_np, candidate_np))
        scored_records.append((sim, r))
        
    scored_records.sort(key=lambda x: x[0], reverse=True)
    top_records = [r for sim, r in scored_records[:10] if sim >= 0.45]
    
    return {"data": [CandidateProfile.model_validate(r) for r in top_records]}


@router.get("/{candidate_id}/explain")
async def explain_ranking(
    candidate_id: uuid.UUID,
    persona: Literal["startup_generalist", "enterprise_specialist", "research_engineer"] = Query("startup_generalist"),
    session: AsyncSession = Depends(get_session),
    current_org: uuid.UUID = Depends(get_current_org)
):
    """Provides a detailed score breakdown explaining why a candidate was ranked highly."""
    from services.ranking import PERSONA_WEIGHTS
    record = await session.get(CandidateRecord, candidate_id)
    if not record or record.organization_id != current_org:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    w = PERSONA_WEIGHTS.get(persona, PERSONA_WEIGHTS["startup_generalist"])
    
    verified_skills_count = len([s for s in record.extracted_skills if s.get("verified")]) if record.extracted_skills else 0
    verified_skills_score = min(verified_skills_count / 10.0, 1.0)
    has_hidden = 1.0 if record.hidden_strengths else 0.0
    readme_q = 0.0
    if record.github_signals and isinstance(record.github_signals, dict):
        q = record.github_signals.get("readme_depth")
        readme_q = 1.0 if q == "high" else 0.5 if q == "medium" else 0.0
    role_fit = 1.0 if record.recommendation == "shortlist" else 0.5 if record.recommendation == "review" else 0.0
    growth = 0.0
    if record.authenticity_index and isinstance(record.authenticity_index, dict):
        cs = record.authenticity_index.get("commit_consistency_score")
        growth = 1.0 if cs == "high" else 0.5 if cs == "medium" else 0.0
    experience_months = getattr(record, "total_experience_months", 0)
    if experience_months is None:
        experience_months = 0
    experience_depth_score = min(experience_months / 120.0, 1.0)

    factors = []
    total = 0
    
    def add_factor(name, value, weight):
        if weight > 0:
            impact = "high" if (value * weight) >= 0.15 else "medium" if (value * weight) >= 0.05 else "low"
            factors.append({
                "factor": name,
                "weight": weight,
                "score": round(value, 2),
                "weighted_score": round(value * weight, 2),
                "impact": impact
            })
            return value * weight
        return 0

    total += add_factor("verified_skills", verified_skills_score, w.get("verified_skills", 0))
    total += add_factor("growth_trajectory", growth, w.get("growth_trajectory", 0))
    total += add_factor("hidden_strengths_bonus", has_hidden, w.get("hidden_strengths_bonus", 0))
    total += add_factor("role_fit", role_fit, w.get("role_fit", 0))
    total += add_factor("readme_quality", readme_q, w.get("readme_quality", 0))
    total += add_factor("experience_depth", experience_depth_score, w.get("experience_depth", 0))
    
    factors.sort(key=lambda x: x["weighted_score"], reverse=True)
    
    return {
        "candidate_id": str(candidate_id),
        "overall_score": round(total, 3),
        "persona": persona,
        "factors": factors
    }

@router.get("/{candidate_id}/timeline")
async def get_candidate_timeline(
    candidate_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_org: uuid.UUID = Depends(get_current_org)
):
    """Retrieves the full audit trail and processing lifecycle of a candidate."""
    record = await session.get(CandidateRecord, candidate_id)
    if not record or record.organization_id != current_org:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return {
        "candidate_id": str(candidate_id),
        "timeline": record.audit_trail or []
    }

@router.get("/{candidate_id}", response_model=CandidateProfile)
async def get_candidate(
    candidate_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_org: uuid.UUID = Depends(get_current_org)
):
    """Retrieve a specific candidate profile. Returns partial data if enrichment is in progress."""
    record = await session.get(CandidateRecord, candidate_id)
    if not record or record.organization_id != current_org:
        raise HTTPException(status_code=404, detail={"status": "error", "message": "Candidate not found.", "code": "NOT_FOUND"})
    
    return CandidateProfile.model_validate(record)

async def background_github_enrichment(candidate_id: uuid.UUID, github_username: str, extracted_skills: list):
    """Background task to fetch GitHub data, run hidden talent discovery, and update the DB."""
    # Get a fresh session for the background task
    from db.database import get_session
    async for session in get_session():
        try:
            audit_trail = []
            # 1. GitHub Enrichment
            try:
                github_signals = await fetch_github_signals(github_username)
                if github_signals:
                    audit_trail.append({"action": "GitHub Synced", "timestamp": datetime.utcnow().isoformat(), "details": f"Fetched {len(github_signals.repos)} repositories."})
            except Exception as e:
                print(f"GitHub Sync Failed: {e}")
                github_signals = None
                audit_trail.append({"action": "GitHub Sync Failed", "timestamp": datetime.utcnow().isoformat(), "details": str(e)})
            
            # 2. Hidden Talent Discovery
            hidden_strengths = []
            if github_signals and github_signals.repos:
                try:
                    repos_dict = [r.model_dump() for r in github_signals.repos]
                    hidden_strengths_data = await discover_hidden_talents(extracted_skills, repos_dict)
                    if hidden_strengths_data:
                        hidden_strengths = [HiddenStrength(**hs) for hs in hidden_strengths_data]
                        audit_trail.append({"action": "Hidden Strength Found", "timestamp": datetime.utcnow().isoformat(), "details": f"Discovered {len(hidden_strengths)} hidden capabilities."})
                except Exception as e:
                    print(f"Hidden Talent Discovery Failed: {e}")
                    audit_trail.append({"action": "Hidden Talent Discovery Failed", "timestamp": datetime.utcnow().isoformat(), "details": str(e)})

            # 3. Update DB Record
            record = await session.get(CandidateRecord, candidate_id)
            if record:
                if github_signals:
                    record.github_signals = github_signals.model_dump(mode='json')
                    
                    # Update authenticity_index to unlock the growth trajectory points!
                    auth_idx = record.authenticity_index or {}
                    
                    # Heuristic: if they have repos, give them 'high' or 'medium' consistency
                    if len(github_signals.repos) > 3:
                        auth_idx["commit_consistency_score"] = "high"
                    elif len(github_signals.repos) > 0:
                        auth_idx["commit_consistency_score"] = "medium"
                        
                    auth_idx["original_repo_ratio"] = github_signals.original_repo_ratio
                    auth_idx["signal_note"] = "GitHub data successfully analyzed."
                    record.authenticity_index = auth_idx
                    
                if hidden_strengths:
                    record.hidden_strengths = [hs.model_dump(mode='json') for hs in hidden_strengths]
                record.processing_status = "completed"
                
                if not github_signals:
                    auth_idx = record.authenticity_index or {}
                    auth_idx["signal_note"] = "GitHub data unavailable — ranking based on resume signals only."
                    record.authenticity_index = auth_idx

                from services.embedding import generate_embedding, build_candidate_embedding_text
                profile_dict = record.model_dump()
                embedding_text = build_candidate_embedding_text(profile_dict)
                record.embedding = generate_embedding(embedding_text)
                audit_trail.append({"action": "Embedding Updated", "timestamp": datetime.utcnow().isoformat(), "details": "Re-generated semantic embedding with GitHub enrichment data."})

                existing_audit = record.audit_trail or []
                record.audit_trail = list(existing_audit) + audit_trail

                session.add(record)
                await session.commit()
        except Exception as e:
            print(f"Background task failed: {e}")
            try:
                record = await session.get(CandidateRecord, candidate_id)
                if record:
                    record.processing_status = "failed"
                    session.add(record)
                    await session.commit()
            except Exception as inner_e:
                print(f"Failed to update status to failed: {inner_e}")
        break # Only use one session

@router.post("/upload", response_model=CandidateProfile)
async def upload_candidate(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    github_username: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_session),
    current_org: uuid.UUID = Depends(get_current_org),
    current_job: uuid.UUID = Depends(get_current_job)
):
    """Stage 1 & 2 of the resume pipeline."""
    content = await file.read()
    filename = file.filename.lower() if file.filename else ""
    
    async def extract_pdf_text(content: bytes) -> str:
        def _extract():
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                return ''.join(page.extract_text() or '' for page in pdf.pages)
        return await run_in_threadpool(_extract)

    async def extract_docx_text(content: bytes) -> str:
        def _extract():
            import docx2txt
            return docx2txt.process(io.BytesIO(content))
        return await run_in_threadpool(_extract)

    try:
        if filename.endswith(".docx") or file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            extracted_text = await extract_docx_text(content)
        elif filename.endswith(".pdf") or file.content_type == "application/pdf":
            extracted_text = await extract_pdf_text(content)
        else:
            raise HTTPException(
                status_code=422,
                detail={"status": "error", "message": "Unsupported file format. Please upload a PDF or DOCX file.", "code": "UNSUPPORTED_FORMAT"}
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=422, 
            detail={"status": "error", "message": f"Failed to read file. ({str(e)})", "code": "FILE_READ_ERROR"}
        )

    if len(extracted_text.strip()) < 100:
        raise HTTPException(
            status_code=422, 
            detail={"status": "error", "message": "Resume format not supported — please upload a text-based PDF.", "code": "INVALID_RESUME_FORMAT"}
        )

    audit_trail = [
        {"action": "Resume Uploaded", "timestamp": datetime.utcnow().isoformat(), "details": f"File {filename} parsed successfully."}
    ]
    
    try:
        profile_data = await extract_resume_data(extracted_text)
        profile_data["resume_text"] = extracted_text
        
        # Merge Form data and LLM extraction (form overrides LLM if present)
        # Note: If form data was sent as empty string or "null", ignore it.
        if github_username in ["", "null", "undefined", None]:
            github_username = None
            
        final_github_username = github_username or profile_data.get("github_username")
        
        # Sanitize: If user or LLM provided a full URL, extract just the username
        if final_github_username:
            final_github_username = final_github_username.strip().rstrip('/')
            if "github.com/" in final_github_username:
                final_github_username = final_github_username.split("github.com/")[-1].split('/')[0]
                
        profile_data["github_username"] = final_github_username
        profile_data["processing_status"] = "processing" if final_github_username else "completed"
        
        audit_trail.append({"action": "Data Extracted", "timestamp": datetime.utcnow().isoformat(), "details": "LLM successfully extracted profile data."})
    except Exception as e:
        # Failure Recovery for Claude API issues
        print(f"Extraction failed: {e}")
        final_github_username = github_username
        profile_data = {
            "name": "Unknown Candidate",
            "resume_text": extracted_text,
            "github_username": final_github_username,
            "processing_status": "failed",
            "recommendation": "review",
            "reasoning": {"confidence_band": "low", "narrative": f"Extraction failed: {str(e)}"},
            "authenticity_index": {"signal_note": "Extraction failed, candidate needs manual review."}
        }
        audit_trail.append({"action": "Extraction Failed", "timestamp": datetime.utcnow().isoformat(), "details": str(e)})
    
    # Calculate experience
    from models.domain import WorkExperience
    work_exp_dicts = profile_data.get("work_experience", [])
    work_exps = [WorkExperience(**w) for w in work_exp_dicts]
    profile_data["total_experience_months"] = calculate_total_experience_months(work_exps)
    
    try:
        # Normalize LLM outputs to prevent Pydantic Literal validation crashes
        if isinstance(profile_data.get("recommendation"), str):
            rec = profile_data["recommendation"].lower()
            profile_data["recommendation"] = rec if rec in ["shortlist", "review", "pass"] else "review"
        else:
            profile_data["recommendation"] = "review"

        reasoning = profile_data.get("reasoning", {})
        if isinstance(reasoning.get("confidence_band"), str):
            cb = reasoning["confidence_band"].lower()
            reasoning["confidence_band"] = cb if cb in ["high", "medium", "low"] else "medium"
        else:
            reasoning["confidence_band"] = "medium"
            
        profile_data["reasoning"] = reasoning

        profile = CandidateProfile(**profile_data)
        dump = profile.model_dump(mode='json')
        dump['id'] = profile.id
        dump['organization_id'] = current_org
        dump['job_id'] = current_job
        dump['created_at'] = profile.created_at
        
        # Generate embedding for the new candidate
        try:
            from services.embedding import generate_embedding, build_candidate_embedding_text
            embedding_text = build_candidate_embedding_text(dump)
            dump['embedding'] = generate_embedding(embedding_text)
            audit_trail.append({"action": "Embedding Generated", "timestamp": datetime.utcnow().isoformat(), "details": "Generated semantic embedding for search."})
        except Exception as e:
            dump['embedding'] = None
            audit_trail.append({"action": "Embedding Failed", "timestamp": datetime.utcnow().isoformat(), "details": str(e)})
            
        dump['audit_trail'] = audit_trail
        
        record = CandidateRecord(**dump)
        session.add(record)
        await session.commit()
        await session.refresh(record)
    except Exception as e:
        await session.rollback()
        import traceback
        err_str = f"{str(e)} | Trace: {traceback.format_exc()}"
        raise HTTPException(status_code=500, detail={"status": "error", "message": f"Failed to save profile to DB. Exception: {err_str}", "code": "DB_ERROR"})

    if final_github_username:
        background_tasks.add_task(background_github_enrichment, record.id, final_github_username, profile_data.get("extracted_skills", []))

    return CandidateProfile.model_validate(record)


@router.post("/jobs/{job_id}/rerank")
async def rerank_candidates(
    job_id: uuid.UUID,
    persona: Literal["startup_generalist", "enterprise_specialist", "research_engineer"],
    session: AsyncSession = Depends(get_session),
    current_org: uuid.UUID = Depends(get_current_org)
):
    """Pure computation reranking based on persona weights."""
    from services.ranking import PERSONA_WEIGHTS
    w = PERSONA_WEIGHTS.get(persona, PERSONA_WEIGHTS["startup_generalist"])
    
    # Enforce isolation: only fetch candidates for this org AND this job
    query = select(CandidateRecord).where(
        CandidateRecord.organization_id == current_org,
        CandidateRecord.job_id == job_id
    )
    result = await session.execute(query)
    records = result.scalars().all()
    
    scored_candidates = []
    for r in records:
        verified_skills_count = len([s for s in r.extracted_skills if s.get("verified")]) if r.extracted_skills else 0
        verified_skills_score = min(verified_skills_count / 10.0, 1.0)
        
        has_hidden = 1.0 if r.hidden_strengths else 0.0
        
        readme_q = 0.0
        if r.github_signals and isinstance(r.github_signals, dict):
            q = r.github_signals.get("readme_depth")
            readme_q = 1.0 if q == "high" else 0.5 if q == "medium" else 0.0
            
        role_fit = 1.0 if r.recommendation == "shortlist" else 0.5 if r.recommendation == "review" else 0.0
        
        growth = 0.0
        if r.authenticity_index and isinstance(r.authenticity_index, dict):
            cs = r.authenticity_index.get("commit_consistency_score")
            growth = 1.0 if cs == "high" else 0.5 if cs == "medium" else 0.0

        experience_months = getattr(r, "total_experience_months", 0)
        if experience_months is None:
            experience_months = 0
        experience_depth_score = min(experience_months / 120.0, 1.0)

        score = (
            verified_skills_score * w.get("verified_skills", 0) +
            growth * w.get("growth_trajectory", 0) +
            has_hidden * w.get("hidden_strengths_bonus", 0) +
            role_fit * w.get("role_fit", 0) +
            readme_q * w.get("readme_quality", 0) +
            experience_depth_score * w.get("experience_depth", 0)
        )
        
        scored_candidates.append({"candidate_id": str(r.id), "score": round(score, 3), "profile": CandidateProfile.model_validate(r)})
        
    scored_candidates.sort(key=lambda x: x["score"], reverse=True)
    return {"data": scored_candidates}




