from sentence_transformers import SentenceTransformer
from core.config import settings
import numpy as np

# Load model once at module level
# First load takes 5-10 seconds, subsequent calls are fast
_model: SentenceTransformer | None = None

def get_embedding_model():
    # Return None to signify local model is disabled to prevent OOM
    return None

def generate_embedding(text: str) -> list[float]:
    """
    Returns a dummy zero-vector to prevent PyTorch from loading and 
    crashing the free Render instance with an Out Of Memory (OOM) error.
    """
    return [0.0] * settings.EMBEDDING_DIMENSIONS

def build_candidate_embedding_text(candidate_profile: dict) -> str:
    parts = []
    
    # Narrative is the richest signal
    if candidate_profile.get("reasoning", {}).get("narrative"):
        parts.append(candidate_profile["reasoning"]["narrative"])
    
    # Skill names
    skills = candidate_profile.get("extracted_skills", [])
    skill_names = [s["skill_name"] for s in skills if s.get("skill_name")]
    if skill_names:
        parts.append("Skills: " + ", ".join(skill_names))
    
    # Work experience titles
    experience = candidate_profile.get("work_experience", [])
    titles = [e["title"] for e in experience if isinstance(e, dict) and e.get("title")]
    companies = [e["company"] for e in experience if isinstance(e, dict) and e.get("company")]
    if titles:
        parts.append("Experience: " + ", ".join(titles))
    if companies:
        parts.append("Companies: " + ", ".join(companies))
    
    # Education
    education = candidate_profile.get("education", [])
    degrees = [e.get("field_of_study", "") for e in education if isinstance(e, dict) and e.get("field_of_study")]
    if degrees:
        parts.append("Education: " + ", ".join(degrees))
    
    # Hidden strengths
    hidden = candidate_profile.get("hidden_strengths", [])
    if hidden:
        domains = [h["domain"] for h in hidden if isinstance(h, dict) and h.get("domain")]
        if domains:
            parts.append("Hidden capabilities: " + ", ".join(domains))
    
    return " | ".join(parts)
