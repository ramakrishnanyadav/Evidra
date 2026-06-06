import json
import uuid
import os
from datetime import datetime

ARJUN_PROFILE = {
  "id": "11111111-1111-1111-1111-111111111111",
  "name": "Arjun Sharma",
  "github_username": "arjun-oss",
  "recommendation": "shortlist",
  "resume_text": "Junior Frontend Developer. Skilled in React, CSS, HTML.",
  "extracted_skills": [
    {"skill_name": "React", "confidence": "high", "verified": True,
     "sources": [{"type": "resume_claim", "label": "Resume", "url": None}]},
    {"skill_name": "CSS", "confidence": "high", "verified": True,
     "sources": [{"type": "resume_claim", "label": "Resume", "url": None}]},
    {"skill_name": "HTML", "confidence": "medium", "verified": True,
     "sources": [{"type": "resume_claim", "label": "Resume", "url": None}]}
  ],
  "hidden_strengths": [{
    "domain": "Backend Systems",
    "description": "Consistent backend engineering activity across multiple repositories not represented in resume title or skills",
    "evidence_repos": ["api-gateway", "microservice-template"],
    "commit_count": 145,
    "confidence": "high"
  }],
  "github_signals": {
    "repos": [
      {"name": "api-gateway", "language": "Node.js",
       "commits": 84, "description": "REST API with rate limiting and auth middleware"},
      {"name": "microservice-template", "language": "Go",
       "commits": 61, "description": "Production microservice boilerplate with service mesh"}
    ],
    "original_repo_ratio": 0.8,
    "readme_depth": "high"
  },
  "reasoning": {
    "recommendation": "shortlist",
    "top_strengths": [
      {"point": "Backend capability significantly exceeds resume representation",
       "evidence": "145 commits across 2 backend repositories"},
      {"point": "Consistent contribution patterns over 14 months",
       "evidence": "github.com/arjun-oss"}
    ],
    "concerns": [
      {"point": "Resume does not reflect actual technical depth",
       "evidence": "Resume lists only frontend skills"}
    ],
    "missing_information": ["No system design samples available", "No code review history"],
    "confidence_band": "high",
    "narrative": "Resume describes a frontend developer. GitHub reveals a backend engineer. Hidden capability in distributed systems and API architecture confirmed across multiple production-grade repositories."
  },
  "authenticity_index": {
    "original_repo_ratio": 0.8,
    "commit_consistency_score": "high",
    "readme_quality_score": "high",
    "has_issue_participation": True,
    "signal_note": "Consistent contribution patterns across 14 months with high original repository ratio."
  },
  "created_at": datetime.utcnow().isoformat(),
  "processing_status": "completed"
}

NO_GITHUB_PROFILE = {
  "id": str(uuid.uuid4()),
  "name": "Sarah Connor",
  "github_username": None,
  "recommendation": "review",
  "resume_text": "Experienced Project Manager and Scrum Master.",
  "extracted_skills": [
    {"skill_name": "Agile", "confidence": "high", "verified": False,
     "sources": [{"type": "resume_claim", "label": "Resume", "url": None}]}
  ],
  "hidden_strengths": None,
  "github_signals": None,
  "reasoning": {
    "recommendation": "review",
    "top_strengths": [{"point": "Strong management skills", "evidence": "Resume"}],
    "concerns": [],
    "missing_information": ["No technical evidence"],
    "confidence_band": "medium",
    "narrative": "Strong resume profile but lacks verifiable technical signals."
  },
  "authenticity_index": {
    "original_repo_ratio": 0.0,
    "commit_consistency_score": "insufficient_data",
    "readme_quality_score": "low",
    "has_issue_participation": False,
    "signal_note": "GitHub data unavailable — ranking based on resume signals only."
  },
  "created_at": datetime.utcnow().isoformat(),
  "processing_status": "completed"
}

def generate():
    profiles = [ARJUN_PROFILE, NO_GITHUB_PROFILE]
    
    for i in range(8):
        profiles.append({
            "id": str(uuid.uuid4()),
            "name": f"Candidate {i+3}",
            "github_username": f"user{i+3}",
            "recommendation": "pass",
            "resume_text": "Standard resume text.",
            "extracted_skills": [],
            "hidden_strengths": None,
            "github_signals": {
                "repos": [],
                "original_repo_ratio": 0.5,
                "readme_depth": "medium"
            },
            "reasoning": {
                "recommendation": "pass",
                "top_strengths": [],
                "concerns": [],
                "missing_information": [],
                "confidence_band": "low",
                "narrative": "Average profile."
            },
            "authenticity_index": {
                "original_repo_ratio": 0.5,
                "commit_consistency_score": "low",
                "readme_quality_score": "low",
                "has_issue_participation": False,
                "signal_note": "Average data."
            },
            "created_at": datetime.utcnow().isoformat(),
            "processing_status": "completed"
        })

    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)
    out_path = os.path.join(data_dir, "seed.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2)

if __name__ == "__main__":
    generate()
    print("Seed data generated.")
