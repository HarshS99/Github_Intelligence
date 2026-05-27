"""
github_client.py
Pure synchronous GitHub REST API client.
Called directly by app.py for all structured endpoints (fast, no LLM needed).
"""

import base64
import os
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from datetime import datetime

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


def _post(path: str, json_body: dict):
    r = requests.post(f"{BASE_URL}{path}", headers=_headers(), json=json_body, timeout=15)
    r.raise_for_status()
    return r.json()


def _put(path: str, json_body: dict):
    r = requests.put(f"{BASE_URL}{path}", headers=_headers(), json=json_body, timeout=15)
    r.raise_for_status()
    return r.json()


def _patch(path: str, json_body: dict):
    r = requests.patch(f"{BASE_URL}{path}", headers=_headers(), json=json_body, timeout=15)
    r.raise_for_status()
    return r.json()


def _delete(path: str):
    r = requests.delete(f"{BASE_URL}{path}", headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json() if r.text else {}


def get_authenticated_user() -> dict:
    return _get("/user")


def create_repo(name: str, description: str = "", private: bool = False, org: str = None) -> dict:
    payload = {
        "name": name,
        "description": description,
        "private": private,
        "auto_init": True,
    }
    if org:
        return _post(f"/orgs/{org}/repos", payload)
    return _post("/user/repos", payload)


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


def get_branches(repo: str, limit: int = 50) -> list:
    items = _get(f"/repos/{repo}/branches", {"per_page": min(limit, 100)})
    return [{
        "name": b["name"],
        "commit_sha": b["commit"]["sha"],
        "protected": b.get("protected", False),
    } for b in items]


def get_branch(repo: str, branch: str) -> dict:
    return _get(f"/repos/{repo}/branches/{branch}")


def create_branch(repo: str, new_branch: str, from_branch: str = None) -> dict:
    base_branch = from_branch or _get(f"/repos/{repo}")["default_branch"]
    commit_sha = _get(f"/repos/{repo}/git/ref/heads/{base_branch}")["object"]["sha"]
    return _post(f"/repos/{repo}/git/refs", {"ref": f"refs/heads/{new_branch}", "sha": commit_sha})


def get_file(repo: str, path: str, ref: str = None) -> dict:
    params = {"ref": ref} if ref else None
    d = _get(f"/repos/{repo}/contents/{path}", params=params)
    content = base64.b64decode(d["content"]).decode("utf-8", errors="replace") if d.get("content") else ""
    return {"path": d.get("path"), "sha": d.get("sha"), "content": content, "url": d.get("html_url"), "encoding": d.get("encoding")}


def create_or_update_file(repo: str, path: str, message: str, content: str, branch: str = None, sha: str = None) -> dict:
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
    }
    if branch:
        payload["branch"] = branch
    if sha:
        payload["sha"] = sha
    return _put(f"/repos/{repo}/contents/{path}", payload)


def create_pull_request(repo: str, title: str, body: str, head: str, base: str = "main") -> dict:
    payload = {"title": title, "body": body, "head": head, "base": base}
    return _post(f"/repos/{repo}/pulls", payload)


def create_issue(repo: str, title: str, body: str = "", labels: list[str] = None) -> dict:
    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    return _post(f"/repos/{repo}/issues", payload)


def close_issue(repo: str, issue_number: int) -> dict:
    return _patch(f"/repos/{repo}/issues/{issue_number}", {"state": "closed"})


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


def get_readme(repo: str) -> str:
    try:
        d = _get(f"/repos/{repo}/readme")
        return base64.b64decode(d["content"]).decode("utf-8", errors="replace")[:4000]
    except requests.HTTPError:
        return "No README found."


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