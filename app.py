"""
app.py — GitHub Intelligence API Server
Run: python app.py
"""

import asyncio
import json
import os
import threading
from flask import Flask, request, jsonify
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
        max_tokens=1500,
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
        return None, str(e)


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
    resp, err = _call_agent(message)
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

    prompt = f"""You are a senior software engineer. Analyze this GitHub repository and write a clear, detailed report.

Repository: {info['name']}
Description: {info.get('description') or 'No description'}
Stars: {info['stars']:,}  |  Forks: {info['forks']:,}  |  Open issues: {info['open_issues']}
Primary language: {stats['primary']}
Languages: {', '.join(f"{k} {v}%" for k, v in list(stats['languages'].items())[:6])}
License: {info.get('license') or 'None'}
Last updated: {info['updated_at']}
Topics: {', '.join(info['topics']) or 'None'}
Top contributors: {', '.join(c['username'] + ' (' + str(c['contributions']) + ')' for c in contribs)}
Recent commits:
{chr(10).join('  - ' + c['date'][:10] + ': ' + c['message'] for c in commits)}
README preview:
{readme[:1500]}

Write a structured analysis:
1. Project overview and purpose
2. Tech stack and architecture
3. Community health (activity, contributors, issues)
4. Strengths and notable features
5. Recommendations for new contributors"""

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
    import github_client as gh
    try:
        return jsonify({"success": True, "repository": repo, "issues": gh.get_issues(repo)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/pulls/<path:repo>", methods=["GET"])
def get_pulls(repo):
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