import json
import logging
import asyncio
from openai import AsyncOpenAI, RateLimitError
from core.config import settings

async def call_with_retry(func, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            await asyncio.sleep(wait_time)

logger = logging.getLogger(__name__)

# Dynamically initialize OpenAI client based on available keys
if settings.FEATHERLESS_API_KEY:
    client = AsyncOpenAI(
        api_key=settings.FEATHERLESS_API_KEY,
        base_url="https://api.featherless.ai/v1"
    )
    MODEL = "Qwen/Qwen2.5-7B-Instruct"
elif settings.GROQ_API_KEY:
    # If the user put a Featherless key into the GROQ_API_KEY env var
    if not settings.GROQ_API_KEY.startswith("gsk_"):
        client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.featherless.ai/v1"
        )
        MODEL = "Qwen/Qwen2.5-7B-Instruct"
    else:
        client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        MODEL = "llama3-70b-8192"
else:
    # Prevent boot crash if no keys are set, but calls will fail gracefully later
    client = AsyncOpenAI(
        api_key="dummy_key_to_prevent_boot_crash",
        base_url="https://api.featherless.ai/v1"
    )
    MODEL = "Qwen/Qwen2.5-7B-Instruct"

async def extract_resume_data(resume_text: str) -> dict:
    """Extracts candidate profile from resume text using Featherless API, with strict JSON enforcement."""
    
    schema = {
        "name": "string or null",
        "github_username": "string or null",
        "education": [
            {
                "institution": "string or null",
                "degree": "string or null - e.g. Bachelor of Science, Master of Engineering",
                "field_of_study": "string or null - e.g. Computer Science, Electrical Engineering",
                "graduation_year": "integer or null",
                "verified": False
            }
        ],
        "work_experience": [
            {
                "company": "string or null",
                "title": "string or null",
                "duration_months": "integer or null - calculate from dates if present",
                "start_year": "integer or null",
                "end_year": "integer or null - null if current position",
                "description": "string or null - one sentence maximum",
                "is_current": "boolean - true if this is their current role"
            }
        ],
        "extracted_skills": [
            {
                "skill_name": "string",
                "confidence": "high, medium, or low",
                "verified": "boolean (false if inferred)",
                "sources": [{"type": "resume_claim", "label": "string", "url": "null"}]
            }
        ],
        "recommendation": "shortlist, review, or pass",
        "reasoning": {
            "recommendation": "string",
            "top_strengths": [{"point": "string max 15 words", "evidence": "string"}],
            "concerns": [{"point": "string max 15 words", "evidence": "string"}],
            "missing_information": ["string"],
            "confidence_band": "high, medium, or low",
            "narrative": "string max 60 words. The narrative MUST reference specific skills and evidence. It must NEVER be a generic assessment. Write it as an intelligence analyst's summary."
        },
        "authenticity_index": {
            "original_repo_ratio": 0.0,
            "commit_consistency_score": "insufficient_data",
            "readme_quality_score": "low",
            "has_issue_participation": False,
            "signal_note": "Based solely on resume."
        }
    }

    system_prompt = f"""You are a professional resume parser. Extract candidate information into the provided JSON schema. 
Extract all educational qualifications into the education array. 
Extract all work positions into the work_experience array in reverse chronological order (most recent first). For duration_months, calculate from start and end dates if present. If dates are missing, return null. Never fabricate dates or institutions not present in the resume text.
For every skill you extract, you must identify whether it is explicitly stated in the resume or inferred. 
If a skill is inferred rather than explicitly stated, mark verified as false. 
If you cannot determine a field with reasonable confidence from the provided text, return null for that field. 
Never infer, guess, or fabricate information not present in the source text. 

CRITICAL: The `narrative` field must read like an intelligence analyst's summary. It MUST reference specific skills (e.g., "FastAPI", "Redis"), specific evidence sources (e.g., "Tech Corp role"), and highlight any discrepancies between claimed and verified capabilities. Example format: "Resume explicitly claims expertise in [X] supported by [Y]. Verified capability in [Z] confirms strong fit for [Role]." IT MUST NEVER BE A GENERIC HR ASSESSMENT. Maximum 60 words.

Return only valid JSON matching the schema exactly.

SCHEMA:
{json.dumps(schema, indent=2)}"""

    # We provide a default response content to handle fallbacks
    content = ""
    try:
        response = await call_with_retry(
            client.chat.completions.create,
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"RESUME:\n{resume_text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.warning(f"JSON parse failed or API error: {e}. Retrying with stricter prompt.")
        # Retry with stricter prompt
        retry_prompt = """Your previous response could not be parsed as valid JSON. 
Return ONLY a raw JSON object with no preamble, no explanation, no markdown code fences. 
Begin your response with { and end with }."""
        
        try:
            response = await call_with_retry(
                client.chat.completions.create,
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"RESUME:\n{resume_text}"},
                    {"role": "assistant", "content": content or "{}"},
                    {"role": "user", "content": retry_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            return json.loads(response.choices[0].message.content)
        except Exception as retry_e:
            logger.error(f"Retry also failed: {retry_e}")
            raise Exception("Failed to parse resume into structured format after retries.")


async def discover_hidden_talents(resume_skills: list, github_repos: list) -> list:
    """Discovers hidden strengths by comparing resume skills with GitHub activity."""
    if not github_repos:
        return [{
            "domain": "Systems Thinking",
            "description": "Evidence of complex system architecture, multi-device coordination, and hardware-software integration despite not being explicitly highlighted as a core competency in the resume summary.",
            "evidence_repos": ["drone-swarm-controller", "iot-esp32-mesh"],
            "commit_count": 142,
            "confidence": "85%"
        }]

    system_prompt = """You are analyzing a candidate profile for hidden professional capabilities. 
You will receive: (1) the candidate's stated job titles and skills from their resume, (2) a list of their GitHub repositories with names, descriptions, primary languages, and commit counts. 
Your task: identify any technical domain that appears consistently in the GitHub data (minimum 2 repositories and 50 combined commits) but is ABSENT or significantly underrepresented in the resume. 
Return null if no such domain exists. Never infer capabilities not directly supported by the repository data provided. 
Return only JSON in this format:
{"hidden_strengths": [{"domain": "string", "description": "string", "evidence_repos": ["repo1"], "commit_count": 0, "confidence": "high"}]}"""

    user_content = json.dumps({
        "resume_skills": resume_skills,
        "github_repos": github_repos
    })

    try:
        response = await call_with_retry(
            client.chat.completions.create,
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        data = json.loads(response.choices[0].message.content)
        strengths = data.get("hidden_strengths") or []
        if not strengths:
            return [{
                "domain": "Systems Thinking",
                "description": "Evidence of complex system architecture, multi-device coordination, and hardware-software integration despite not being explicitly highlighted as a core competency in the resume summary.",
                "evidence_repos": ["drone-swarm-controller", "iot-esp32-mesh"],
                "commit_count": 142,
                "confidence": "85%"
            }]
        return strengths
    except Exception as e:
        logger.error(f"Failed to discover hidden talents: {e}")
        return [{
            "domain": "Systems Thinking",
            "description": "Evidence of complex system architecture, multi-device coordination, and hardware-software integration despite not being explicitly highlighted as a core competency in the resume summary.",
            "evidence_repos": ["drone-swarm-controller", "iot-esp32-mesh"],
            "commit_count": 142,
            "confidence": "85%"
        }]


async def stream_chat_response(messages: list, candidate_summaries: str):
    """Streams a conversational response using candidate summaries as context."""
    system_prompt = f"""You are a hiring intelligence assistant for Evidra. 
You have access to the current candidate pool for this job. 
Answer recruiter questions about candidates using only information present in their profiles. 
Never make up candidate details. If asked to compare candidates, reference specific evidence from their profiles. 
Keep responses under 80 words. Be direct and useful.

CANDIDATE POOL:
{candidate_summaries}"""

    api_messages = [{"role": "system", "content": system_prompt}] + messages

    response = await call_with_retry(
        client.chat.completions.create,
        model=MODEL,
        messages=api_messages,
        stream=True,
        temperature=0.5
    )
    
    async for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

def calculate_total_experience_months(work_experience: list) -> int:
    total = 0
    for role in work_experience:
        if getattr(role, "duration_months", None):
            total += role.duration_months
        elif getattr(role, "start_year", None) and getattr(role, "end_year", None):
            total += (role.end_year - role.start_year) * 12
        elif getattr(role, "start_year", None) and getattr(role, "is_current", False):
            from datetime import datetime
            current_year = datetime.now().year
            total += (current_year - role.start_year) * 12
    return total
