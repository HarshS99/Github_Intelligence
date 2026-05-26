"""
github_client.py
Pure synchronous GitHub REST API client.
Called directly by app.py for all structured endpoints (fast, no LLM needed).
"""

import base64
import os
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://api.github.com"
SCRAPE_UA = {"User-Agent": "Mozilla/5.0 (compatible; GHIntelBot/1.0)"}


def _headers() -> dict:
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN")
    h = {"Accept": "application/vnd.github.v3+json"}
    if token:
        h["Authorization"] = f"token {token}"
    return h


def _get(path: str, params: dict = None):
    r = requests.get(f"{BASE_URL}{path}", headers=_headers(), params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def get_repo_info(repo: str) -> dict:
    d = _get(f"/repos/{repo}")
    return {
        "name": d.get("full_name"),
        "description": d.get("description"),
        "stars": d.get("stargazers_count", 0),
        "forks": d.get("forks_count", 0),
        "language": d.get("language"),
        "open_issues": d.get("open_issues_count", 0),
        "watchers": d.get("watchers_count", 0),
        "created_at": d.get("created_at"),
        "updated_at": d.get("updated_at"),
        "topics": d.get("topics", []),
        "license": d["license"]["name"] if d.get("license") else None,
        "url": d.get("html_url"),
        "default_branch": d.get("default_branch"),
        "homepage": d.get("homepage"),
    }


def get_readme(repo: str) -> str:
    try:
        d = _get(f"/repos/{repo}/readme")
        return base64.b64decode(d["content"]).decode("utf-8", errors="replace")[:4000]
    except requests.HTTPError:
        return "No README found."


def get_commits(repo: str, limit: int = 10) -> list:
    items = _get(f"/repos/{repo}/commits", {"per_page": min(limit, 30)})
    return [
        {
            "sha": c["sha"][:7],
            "message": c["commit"]["message"].split("\n")[0][:120],
            "author": c["commit"]["author"]["name"],
            "date": c["commit"]["author"]["date"],
        }
        for c in items
    ]


def search_repos(query: str, limit: int = 10) -> list:
    data = _get("/search/repositories", {"q": query, "sort": "stars", "per_page": min(limit, 30)})
    return [
        {
            "name": r["full_name"],
            "description": r.get("description") or "No description",
            "stars": r["stargazers_count"],
            "language": r.get("language"),
            "url": r["html_url"],
        }
        for r in data.get("items", [])
    ]


def get_languages(repo: str) -> dict:
    raw = _get(f"/repos/{repo}/languages")
    total = sum(raw.values()) or 1
    pct = {lang: round(b / total * 100, 2) for lang, b in raw.items()}
    return {
        "languages": pct,
        "primary": max(pct, key=pct.get) if pct else "Unknown",
        "count": len(pct),
    }


def get_contributors(repo: str, limit: int = 10) -> list:
    items = _get(f"/repos/{repo}/contributors", {"per_page": min(limit, 30)})
    return [
        {
            "username": c["login"],
            "contributions": c["contributions"],
            "profile": c["html_url"],
        }
        for c in items
    ]


def get_issues(repo: str, limit: int = 15) -> list:
    items = _get(f"/repos/{repo}/issues", {"state": "open", "per_page": min(limit, 30)})
    return [
        {
            "number": i["number"],
            "title": i["title"],
            "labels": [lb["name"] for lb in i.get("labels", [])],
            "created_at": i["created_at"],
            "url": i["html_url"],
        }
        for i in items
        if "pull_request" not in i
    ]


def get_pulls(repo: str, limit: int = 15) -> list:
    items = _get(f"/repos/{repo}/pulls", {"state": "open", "per_page": min(limit, 30)})
    return [
        {
            "number": p["number"],
            "title": p["title"],
            "author": p["user"]["login"],
            "created_at": p["created_at"],
            "url": p["html_url"],
        }
        for p in items
    ]


def get_user(username: str) -> dict:
    d = _get(f"/users/{username}")
    return {
        "username": d.get("login"),
        "name": d.get("name"),
        "bio": d.get("bio"),
        "company": d.get("company"),
        "location": d.get("location"),
        "public_repos": d.get("public_repos"),
        "followers": d.get("followers"),
        "following": d.get("following"),
        "created_at": d.get("created_at"),
        "url": d.get("html_url"),
        "avatar_url": d.get("avatar_url"),
    }


def get_user_repos(username: str, limit: int = 10) -> list:
    items = _get(f"/users/{username}/repos", {"per_page": min(limit, 30), "sort": "stars"})
    return [
        {
            "name": r["name"],
            "description": r.get("description") or "No description",
            "stars": r["stargazers_count"],
            "language": r.get("language"),
            "url": r["html_url"],
        }
        for r in items
    ]


def get_trending(language: str = "", since: str = "daily") -> list:
    lang_slug = language.lower().replace(" ", "-") if language else ""
    url = f"https://github.com/trending/{lang_slug}?since={since}"
    try:
        r = requests.get(url, headers=SCRAPE_UA, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        for article in soup.find_all("article", class_="Box-row")[:10]:
            try:
                h2 = article.find("h2")
                if not h2:
                    continue
                parts = [p.strip() for p in h2.get_text(separator="/").split("/") if p.strip()]
                name = "/".join(parts[:2]) if len(parts) >= 2 else h2.get_text(strip=True)
                desc_tag = article.find("p")
                desc = desc_tag.get_text(strip=True) if desc_tag else "No description"
                stars_tag = article.find("span", class_=lambda c: c and "float-sm-right" in c)
                stars = stars_tag.get_text(strip=True) if stars_tag else "N/A"
                results.append({"name": name, "description": desc, "stars_today": stars, "url": f"https://github.com/{name}"})
            except Exception:
                continue
        if results:
            return results
    except Exception:
        pass
    # Fallback to Search API
    q = "stars:>500" + (f" language:{language}" if language else "")
    try:
        return search_repos(q, limit=10)
    except Exception as e:
        return [{"error": f"Could not fetch trending: {e}"}]