import asyncio
import json
import time
import sys
import os

# Add the current directory to sys.path so we can import from core and services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import settings
from services.github import fetch_github_signals
from services.llm import extract_resume_data, discover_hidden_talents

async def main():
    print("=== API Key Check ===")
    print(f"Featherless API Key present: {bool(settings.FEATHERLESS_API_KEY)}")
    print(f"GitHub Token present: {bool(settings.GITHUB_TOKEN)}")
    
    if not settings.FEATHERLESS_API_KEY or settings.FEATHERLESS_API_KEY == "dummy_key":
        print("WARNING: Using dummy Featherless API key. LLM calls will fail.")
        
    if not settings.GITHUB_TOKEN or settings.GITHUB_TOKEN == "dummy_token":
        print("WARNING: Using dummy GitHub token. High rate limit not available.")

    print("\n=== Testing GitHub Enrichment ===")
    test_username = "tiangolo" # Known active GitHub user (FastAPI creator)
    print(f"Fetching GitHub data for '{test_username}'...")
    start = time.time()
    github_data = await fetch_github_signals(test_username)
    end = time.time()
    
    if github_data:
        print(f"Success! Fetched top repos for {test_username} in {end-start:.2f}s.")
        print(f"Original Repo Ratio: {github_data.original_repo_ratio}")
        print("Top 2 Repositories:")
        for repo in github_data.repos[:2]:
            print(f" - {repo.name} ({repo.language}): {repo.commits} commits")
    else:
        print(f"Failed to fetch GitHub data for {test_username}.")

    print("\n=== Testing Resume Extraction (Featherless LLM) ===")
    sample_resume = """
    Jane Smith
    Senior Backend Engineer
    
    Skills:
    - Python, FastAPI, Django
    - PostgreSQL, Redis
    - AWS, Docker, Kubernetes
    
    Experience:
    Tech Corp (2020 - Present)
    - Built microservices using FastAPI and Docker.
    - Reduced API latency by 40% through Redis caching.
    """
    print("Sending sample resume to LLM...")
    start = time.time()
    try:
        profile_data = await extract_resume_data(sample_resume)
        end = time.time()
        print(f"Success! Extraction took {end-start:.2f}s.")
        print("Extracted Candidate Name:", profile_data.get("name"))
        print("Skills Extracted:", len(profile_data.get("extracted_skills", [])))
        print("Recommendation:", profile_data.get("recommendation"))
        print("Narrative:", profile_data.get("reasoning", {}).get("narrative"))
        
        # Test hidden talent discovery
        print("\n=== Testing Hidden Talent Discovery (Featherless LLM) ===")
        print("Mocking GitHub repos showing 'Go' expertise (not in resume)...")
        mock_repos = [
            {"name": "go-microservice", "description": "A fast microservice", "language": "Go", "commits": 120},
            {"name": "go-cli-tool", "description": "CLI tool for deployment", "language": "Go", "commits": 85}
        ]
        start = time.time()
        hidden = await discover_hidden_talents(profile_data.get("extracted_skills", []), mock_repos)
        end = time.time()
        print(f"Success! Discovery took {end-start:.2f}s.")
        if hidden:
            print("Discovered Hidden Strengths:")
            for h in hidden:
                print(f" - Domain: {h.get('domain')}")
                print(f"   Confidence: {h.get('confidence')}")
                print(f"   Description: {h.get('description')}")
        else:
            print("No hidden strengths discovered.")
            
    except Exception as e:
        print(f"LLM Extraction failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
