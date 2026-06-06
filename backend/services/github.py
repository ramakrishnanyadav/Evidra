import httpx
import time
import logging
from typing import Optional
from core.config import settings
from models.domain import GitHubSignals, GitHubRepo

logger = logging.getLogger(__name__)

# Cache and Rate Limiting State
_cache = {}
_cache_ttl = 3600
_rate_limit_window = 60
_max_requests_per_window = 10
_request_timestamps = []

def _check_rate_limit() -> bool:
    """True if request is allowed, False if rate limited."""
    global _request_timestamps
    now = time.time()
    # Clean up old timestamps
    _request_timestamps = [t for t in _request_timestamps if now - t < _rate_limit_window]
    if len(_request_timestamps) >= _max_requests_per_window:
        return False
    _request_timestamps.append(now)
    return True

async def fetch_github_signals(username: str) -> Optional[GitHubSignals]:
    """Fetches GitHub profile data, applies rate limiting and caching."""
    if not username:
        return None

    now = time.time()
    if username in _cache:
        cached_data, timestamp = _cache[username]
        if now - timestamp < _cache_ttl:
            return cached_data

    if not _check_rate_limit():
        logger.warning(f"GitHub API rate limit reached. Skipping {username}.")
        return None

    headers = {"Accept": "application/vnd.github.v3+json"}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Fetch Repos
            repos_resp = await client.get(f"https://api.github.com/users/{username}/repos?per_page=100", headers=headers)
            if repos_resp.status_code != 200:
                logger.warning(f"Failed to fetch repos for {username}: {repos_resp.status_code}")
                return None
            
            repos_data = repos_resp.json()
            
            # Simple heuristic for original repos (not forks)
            original_repos = [r for r in repos_data if not r.get('fork', False)]
            original_repo_ratio = len(original_repos) / max(len(repos_data), 1)
            
            # Fetch events to get a sense of commit counts (heuristic for hackathon)
            events_resp = await client.get(f"https://api.github.com/users/{username}/events/public", headers=headers)
            commit_counts = {}
            if events_resp.status_code == 200:
                for event in events_resp.json():
                    if event.get("type") == "PushEvent":
                        repo_name = event["repo"]["name"].split("/")[-1]
                        commits = len(event["payload"].get("commits", []))
                        commit_counts[repo_name] = commit_counts.get(repo_name, 0) + commits

            # We will use the top original repos by stars or size
            top_repos = sorted(original_repos, key=lambda x: x.get('stargazers_count', 0), reverse=True)[:5]
            
            github_repos = []
            for r in top_repos:
                name = r['name']
                github_repos.append(GitHubRepo(
                    name=name,
                    language=r.get('language'),
                    commits=commit_counts.get(name, r.get('size', 10)), # Fallback to size if no recent commits
                    description=r.get('description')
                ))

            signals = GitHubSignals(
                repos=github_repos,
                original_repo_ratio=round(original_repo_ratio, 2),
                readme_depth="medium" # Mocked for speed, could fetch READMEs
            )

            _cache[username] = (signals, now)
            return signals

    except Exception as e:
        logger.error(f"GitHub API Error for {username}: {str(e)}")
        return None
