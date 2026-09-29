import httpx
from typing import List, Dict, Any

class GitHubApiClient:
    def __init__(self, username: str):
        self._username = username
        self._base_url = f"https://api.github.com/users/{username}/repos"
        # GitHub API требует User-Agent, иначе вернет 403 Forbidden
        self._client = httpx.Client(headers={"User-Agent": "PortfolioBot/1.0"}, timeout=10.0)

    def get_top_repos(self, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            params = {"sort": "updated", "per_page": limit, "type": "owner"}
            response = self._client.get(self._base_url, params=params)
            response.raise_for_status()
            
            repos = response.json()
            result = []
            for repo in repos:
                if repo.get("fork"):  # Пропускаем форки
                    continue
                result.append({
                    "name": repo.get("name"),
                    "description": repo.get("description") or "Описание отсутствует",
                    "url": repo.get("html_url"),
                    "language": repo.get("language") or "Python",
                    "stars": repo.get("stargazers_count", 0)
                })
            return result[:limit]
        except httpx.HTTPError:
            return []