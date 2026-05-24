"""
GitHub Intelligence MCP Server
Uses stdio transport (standard MCP pattern)
"""

import asyncio
import json
import base64
import os
import requests
from bs4 import BeautifulSoup
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from dotenv import load_dotenv

# Use absolute path so .env is found even when launched as a subprocess
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=_env_path)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
BASE_URL = "https://api.github.com"

app = Server("github-intelligence")


# ─────────────────────────────────────────────
# Tool definitions
# ─────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_repository_info",
            description="Get detailed info about a GitHub repository (stars, forks, issues, language, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "Repository in format 'owner/repo', e.g. 'facebook/react'"
                    }
                },
                "required": ["repo"]
            }
        ),
        types.Tool(
            name="get_repository_readme",
            description="Fetch the README content of a GitHub repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "owner/repo format"}
                },
                "required": ["repo"]
            }
        ),
        types.Tool(
            name="get_repository_commits",
            description="Get recent commits from a GitHub repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "owner/repo format"},
                    "limit": {"type": "integer", "description": "Number of commits (default 10)", "default": 10}
                },
                "required": ["repo"]
            }
        ),
        types.Tool(
            name="search_repositories",
            description="Search GitHub repositories by keyword or topic",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Max results (default 10)", "default": 10}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_trending_repos",
            description="Scrape trending repositories from GitHub Trending page",
            inputSchema={
                "type": "object",
                "properties": {
                    "language": {"type": "string", "description": "Filter by language (optional)", "default": ""},
                    "since": {"type": "string", "description": "'daily', 'weekly', or 'monthly'", "default": "daily"}
                }
            }
        ),
        types.Tool(
            name="analyze_code_stats",
            description="Get language breakdown and code statistics for a repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "owner/repo format"}
                },
                "required": ["repo"]
            }
        ),
        types.Tool(
            name="get_contributors",
            description="Get top contributors of a GitHub repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "owner/repo format"},
                    "limit": {"type": "integer", "description": "Number of contributors", "default": 10}
                },
                "required": ["repo"]
            }
        ),
        types.Tool(
            name="get_user_profile",
            description="Get a GitHub user's public profile information",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "GitHub username"}
                },
                "required": ["username"]
            }
        ),
        types.Tool(
            name="get_user_repos",
            description="Get public repositories of a GitHub user",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "GitHub username"},
                    "limit": {"type": "integer", "description": "Number of repos", "default": 10}
                },
                "required": ["username"]
            }
        ),
    ]


# ─────────────────────────────────────────────
# Tool implementations
# ─────────────────────────────────────────────

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "get_repository_info":
            result = get_repository_info(arguments["repo"])

        elif name == "get_repository_readme":
            result = get_repository_readme(arguments["repo"])

        elif name == "get_repository_commits":
            result = get_repository_commits(arguments["repo"], arguments.get("limit", 10))

        elif name == "search_repositories":
            result = search_repositories(arguments["query"], arguments.get("limit", 10))

        elif name == "get_trending_repos":
            result = get_trending_repos(arguments.get("language", ""), arguments.get("since", "daily"))

        elif name == "analyze_code_stats":
            result = analyze_code_stats(arguments["repo"])

        elif name == "get_contributors":
            result = get_contributors(arguments["repo"], arguments.get("limit", 10))

        elif name == "get_user_profile":
            result = get_user_profile(arguments["username"])

        elif name == "get_user_repos":
            result = get_user_repos(arguments["username"], arguments.get("limit", 10))

        else:
            result = {"error": f"Unknown tool: {name}"}

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]


# ─────────────────────────────────────────────
# GitHub helper functions
# ─────────────────────────────────────────────

def get_repository_info(repo: str) -> dict:
    r = requests.get(f"{BASE_URL}/repos/{repo}", headers=HEADERS)
    r.raise_for_status()
    d = r.json()
    return {
        "name": d.get("full_name"),
        "description": d.get("description"),
        "stars": d.get("stargazers_count"),
        "forks": d.get("forks_count"),
        "language": d.get("language"),
        "open_issues": d.get("open_issues_count"),
        "watchers": d.get("watchers_count"),
        "created_at": d.get("created_at"),
        "updated_at": d.get("updated_at"),
        "topics": d.get("topics", []),
        "license": d.get("license", {}).get("name") if d.get("license") else None,
        "url": d.get("html_url"),
        "default_branch": d.get("default_branch"),
    }


def get_repository_readme(repo: str) -> dict:
    r = requests.get(f"{BASE_URL}/repos/{repo}/readme", headers=HEADERS)
    r.raise_for_status()
    content = base64.b64decode(r.json()["content"]).decode("utf-8")
    return {"readme": content[:3000]}


def get_repository_commits(repo: str, limit: int = 10) -> list:
    r = requests.get(f"{BASE_URL}/repos/{repo}/commits", headers=HEADERS, params={"per_page": limit})
    r.raise_for_status()
    return [
        {
            "sha": c["sha"][:7],
            "message": c["commit"]["message"].split("\n")[0],
            "author": c["commit"]["author"]["name"],
            "date": c["commit"]["author"]["date"],
        }
        for c in r.json()
    ]


def search_repositories(query: str, limit: int = 10) -> list:
    r = requests.get(
        f"{BASE_URL}/search/repositories",
        headers=HEADERS,
        params={"q": query, "sort": "stars", "per_page": limit}
    )
    r.raise_for_status()
    return [
        {
            "name": repo["full_name"],
            "description": repo["description"],
            "stars": repo["stargazers_count"],
            "language": repo["language"],
            "url": repo["html_url"],
        }
        for repo in r.json()["items"]
    ]


def get_trending_repos(language: str = "", since: str = "daily") -> list:
    url = f"https://github.com/trending/{language}?since={since}"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    repos = []
    for article in soup.find_all("article", class_="Box-row")[:10]:
        try:
            name = article.find("h2").get_text(strip=True).replace(" ", "").replace("\n", "")
            desc_elem = article.find("p", class_="col-9")
            desc = desc_elem.get_text(strip=True) if desc_elem else "No description"
            stars_elem = article.find("span", class_="d-inline-block float-sm-right")
            stars = stars_elem.get_text(strip=True) if stars_elem else "0"
            repos.append({"name": name, "description": desc, "stars_today": stars, "url": f"https://github.com/{name}"})
        except Exception:
            continue
    return repos


def analyze_code_stats(repo: str) -> dict:
    r = requests.get(f"{BASE_URL}/repos/{repo}/languages", headers=HEADERS)
    r.raise_for_status()
    languages = r.json()
    total = sum(languages.values()) or 1
    percentages = {lang: round((b / total) * 100, 2) for lang, b in languages.items()}
    return {
        "languages": percentages,
        "primary_language": max(percentages, key=percentages.get) if percentages else "Unknown",
        "language_count": len(languages),
    }


def get_contributors(repo: str, limit: int = 10) -> list:
    r = requests.get(f"{BASE_URL}/repos/{repo}/contributors", headers=HEADERS, params={"per_page": limit})
    r.raise_for_status()
    return [
        {
            "username": c["login"],
            "contributions": c["contributions"],
            "profile": c["html_url"],
        }
        for c in r.json()
    ]


def get_user_profile(username: str) -> dict:
    r = requests.get(f"{BASE_URL}/users/{username}", headers=HEADERS)
    r.raise_for_status()
    d = r.json()
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
    }


def get_user_repos(username: str, limit: int = 10) -> list:
    r = requests.get(
        f"{BASE_URL}/users/{username}/repos",
        headers=HEADERS,
        params={"per_page": limit, "sort": "stars"}
    )
    r.raise_for_status()
    return [
        {
            "name": repo["name"],
            "description": repo["description"],
            "stars": repo["stargazers_count"],
            "language": repo["language"],
            "url": repo["html_url"],
        }
        for repo in r.json()
    ]


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())