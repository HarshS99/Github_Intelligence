"""
app.py — GitHub Intelligence API Server
Run: python app.py
"""

import asyncio
import json
import os
import threading
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# ── Background async event loop ──────────────────────────────
_loop = asyncio.new_event_loop()

def _start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=_start_loop, args=(_loop,), daemon=True).start()


def run_async(coro, timeout: int = 120):
    return asyncio.run_coroutine_threadsafe(coro, _loop).result(timeout=timeout)


# ── Startup checks ───────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN", "")

def _load_config() -> dict:
    path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(path) as f:
        cfg = json.load(f)
    cfg["mcpServers"]["github"]["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] = GITHUB_TOKEN
    return cfg

try:
    _CONFIG = _load_config()
    _CONFIG_OK = True
except FileNotFoundError:
    _CONFIG = {}
    _CONFIG_OK = False


# ── MCP agent runner ─────────────────────────────────────────
async def _run_prompt(prompt: str) -> str:
    from langchain_groq import ChatGroq
    from mcp_use import MCPAgent, MCPClient

    client = MCPClient(_CONFIG)
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=500,
        groq_api_key=GROQ_API_KEY,
    )
    agent = MCPAgent(llm=llm, client=client, max_steps=10, memory_enabled=False)
    try:
        return await agent.run(prompt)
    finally:
        try:
            if client.sessions:
                await client.close_all_sessions()
        except Exception:
            pass


def _agent_ok():
    return GROQ_API_KEY and _CONFIG_OK


def _call_agent(prompt: str):
    try:
        return run_async(_run_prompt(prompt)), None
    except TimeoutError:
        return None, "Request timed out (120s). Try a simpler query."
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "rate_limit_exceeded" in err_str:
            return None, "Rate limit exceeded on Groq. The GitHub MCP tools + your query exceed the free tier limits (or daily limit). Please try again later or upgrade your Groq tier."
        if "413" in err_str or "Request too large" in err_str:
            return None, "The GitHub MCP tool returned too much data, exceeding Groq's free tier token limit. Please try a more specific query."
        return None, err_str


# ── Screenshot helper (Playwright) ───────────────────────────
async def _take_screenshot(url: str, path: str, width: int = 1280, height: int = 900):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": width, "height": height})

        # Block unnecessary assets to load faster
        await page.route("**/*.{mp4,webm,ogg,mp3,wav,flac,aac,woff,woff2,ttf,otf}", 
                         lambda route: route.abort())

        await page.goto(url, wait_until="networkidle", timeout=30000)

        # Wait for GitHub's main content to appear
        try:
            await page.wait_for_selector("main", timeout=10000)
        except Exception:
            pass  # Proceed even if selector times out

        await page.screenshot(path=path, full_page=False)
        await browser.close()


# ── Routes ───────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "status": "online",
        "agent": "ready" if _agent_ok() else "not available",
        "model": "groq/llama-3.3-70b-versatile",
        "github_token": bool(GITHUB_TOKEN),
    })


@app.route("/chat", methods=["POST"])
def chat():
    if not _agent_ok():
        return jsonify({"error": "GROQ_API_KEY not set or config.json missing"}), 503
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400
    system_note = "\n\n(Note: When calling GitHub search tools, you MUST provide 'sort': 'stars', 'order': 'desc', 'page': 1, 'perPage': 10 as they are strictly required.)"
    resp, err = _call_agent(message + system_note)
    if err:
        return jsonify({"error": err}), 500
    return jsonify({"success": True, "response": resp})


@app.route("/analyze", methods=["POST"])
def analyze():
    if not _agent_ok():
        return jsonify({"error": "GROQ_API_KEY not set or config.json missing"}), 503
    import github_client as gh
    data = request.get_json(silent=True) or {}
    repo = (data.get("repository") or "").strip()
    if not repo:
        return jsonify({"error": "repository is required"}), 400
    if "/" not in repo:
        return jsonify({"error": "Use owner/repo format, e.g. facebook/react"}), 400
    try:
        info    = gh.get_repo_info(repo)
        readme  = gh.get_readme(repo)
        stats   = gh.get_languages(repo)
        commits = gh.get_commits(repo, limit=5)
        contribs= gh.get_contributors(repo, limit=5)
    except Exception as e:
        return jsonify({"error": f"GitHub API error: {e}"}), 502
    
    prompt = f"""
You are a senior software engineer performing a deep technical review of a GitHub repository.

Your goal is to analyze the repository like a code reviewer + system designer.

-------------------------
REPOSITORY METADATA
-------------------------
Name: {info['name']}
Description: {info.get('description') or 'No description'}
Stars: {info['stars']:,}
Forks: {info['forks']:,}
Open Issues: {info['open_issues']}
Primary Language: {stats['primary']}
Languages: {', '.join(f"{k} {v}%" for k, v in list(stats['languages'].items())[:6])}
License: {info.get('license') or 'None'}
Last Updated: {info['updated_at']}
Topics: {', '.join(info['topics']) or 'None'}

Top Contributors:
{', '.join(c['username'] + ' (' + str(c['contributions']) + ')' for c in contribs)}

Recent Commits:
{chr(10).join('  - ' + c['date'][:10] + ': ' + c['message'] for c in commits)}

README Preview:
{readme[:1500]}

-------------------------
INSTRUCTIONS
-------------------------

Write a structured report with the following sections:

1. Overview
   - What problem does this repository solve?
   - Who is it for?

2. Architecture & Design
   - High-level system design
   - Key components and how they interact
   - Any design patterns used

3. Code Quality
   - Readability, modularity, maintainability
   - Testing presence
   - Documentation quality

4. Strengths
   - What is done particularly well?

5. Weaknesses / Risks
   - Bugs, anti-patterns, scalability concerns, missing features

6. Activity & Maturity
   - Based on commits, contributors, and updates
   - Is the project actively maintained?

7. Use Cases
   - Real-world applications of this repo

8. Improvements (Actionable)
   - Specific suggestions to improve the project

9. Resume Value
   - Would this project be strong for a software engineer’s resume?
   - Why or why not?

-------------------------
OUTPUT FORMAT
-------------------------
- Use clear headings
- Be concise but insightful
- Avoid generic statements
- Think like a senior engineer reviewing production code
"""

    resp, err = _call_agent(prompt)
    if err:
        return jsonify({"error": err}), 500
    return jsonify({"success": True, "repository": repo, "info": info, "analysis": resp})


@app.route("/user/<username>", methods=["GET"])
def user_profile(username):
    import github_client as gh
    try:
        profile = gh.get_user(username)
        repos   = gh.get_user_repos(username, limit=6)
        return jsonify({"success": True, "profile": profile, "top_repos": repos})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search", methods=["POST"])
def search():
    import github_client as gh
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "query is required"}), 400
    try:
        return jsonify({"success": True, "results": gh.search_repos(query, limit=10)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/issues/<path:repo>", methods=["GET"])
def get_issues(repo):
    if "/" not in repo:
        return jsonify({"error": "Invalid repository format. Please use 'owner/repo' (e.g. facebook/react)"}), 400
    import github_client as gh
    try:
        return jsonify({"success": True, "repository": repo, "issues": gh.get_issues(repo)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/pulls/<path:repo>", methods=["GET"])
def get_pulls(repo):
    if "/" not in repo:
        return jsonify({"error": "Invalid repository format. Please use 'owner/repo' (e.g. facebook/react)"}), 400
    import github_client as gh
    try:
        return jsonify({"success": True, "repository": repo, "pulls": gh.get_pulls(repo)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/trending", methods=["GET"])
def trending():
    import github_client as gh
    language = request.args.get("language", "")
    since    = request.args.get("since", "daily")
    if since not in ("daily", "weekly", "monthly"):
        since = "daily"
    try:
        return jsonify({"success": True, "results": gh.get_trending(language, since)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/clear", methods=["POST"])
def clear():
    return jsonify({"success": True, "message": "Session cleared."})


# ── Screenshot route ─────────────────────────────────────────
@app.route("/screenshot", methods=["POST"])
def screenshot():
    """
    POST /screenshot
    Body (JSON):
      - target  : "repo" | "user"          (required)
      - name    : "owner/repo" or "username" (required)
      - width   : viewport width in px      (optional, default 1280)
      - height  : viewport height in px     (optional, default 900)

    Returns: PNG image file
    """
    data   = request.get_json(silent=True) or {}
    target = (data.get("target") or "").strip().lower()   # "repo" or "user"
    name   = (data.get("name")   or "").strip()
    width  = int(data.get("width",  1280))
    height = int(data.get("height", 900))

    # ── Validate inputs ──────────────────────────────────────
    if target not in ("repo", "user"):
        return jsonify({"error": "'target' must be 'repo' or 'user'"}), 400
    if not name:
        return jsonify({"error": "'name' is required (e.g. 'torvalds/linux' or 'torvalds')"}), 400
    if target == "repo" and "/" not in name:
        return jsonify({"error": "For target='repo' use owner/repo format"}), 400

    # ── Build GitHub URL ─────────────────────────────────────
    url = f"https://github.com/{name}"

    # ── Temp file for screenshot ─────────────────────────────
    import tempfile
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()

    try:
        run_async(_take_screenshot(url, tmp.name, width=width, height=height), timeout=45)
    except TimeoutError:
        os.unlink(tmp.name)
        return jsonify({"error": "Screenshot timed out (45s)"}), 504
    except Exception as e:
        os.unlink(tmp.name)
        return jsonify({"error": f"Screenshot failed: {e}"}), 500

    # ── Stream PNG back to caller ────────────────────────────
    slug = name.replace("/", "_")
    return send_file(
        tmp.name,
        mimetype="image/png",
        as_attachment=True,
        download_name=f"github_{slug}.png",
    )


# ── User profile formatter ───────────────────────────────────
def format_user_profile(user: dict, repos: list) -> str:
    lines = []

    # Header
    lines.append(f"👤 {user.get('name') or user['username']}")
    
    if user.get("bio"):
        lines.append(f"📝 {user['bio']}")

    if user.get("location"):
        lines.append(f"📍 {user['location']}")

    lines.append("")

    # Stats
    lines.append(
        f"⭐ Followers: {user['followers']}  "
        f"·  Following: {user['following']}  "
        f"·  Repos: {user['public_repos']}"
    )

    lines.append(f"🔗 {user['url']}")
    lines.append("")

    # Top repos
    lines.append("🚀 Top Repositories:\n")

    if not repos:
        lines.append("No repositories found.")
        return "\n".join(lines)

    for repo in repos[:6]:
        stars = repo.get("stars", 0)
        lang = repo.get("language") or "Unknown"
        desc = repo.get("description") or "No description"

        lines.append(
            f"⭐ {stars:<3}  {repo['name']}  [{lang}]"
        )
        lines.append(f"   {desc}")
        lines.append("")

    return "\n".join(lines)


# ── Entry point ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 52)
    print("  🐙 GitHub Intelligence — http://localhost:8000")
    print("=" * 52)
    print(f"  GROQ_API_KEY  : {'✅ set' if GROQ_API_KEY else '❌ MISSING — add to .env'}")
    print(f"  GITHUB_TOKEN  : {'✅ set' if GITHUB_TOKEN else '⚠️  not set (60 req/hr)'}")
    print(f"  config.json   : {'✅ loaded' if _CONFIG_OK else '❌ MISSING'}")
    print("=" * 52)
    app.run(host="0.0.0.0", port=8000, debug=False, threaded=True)