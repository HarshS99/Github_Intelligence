"""
Flask API Server
Uses MCPAgent (mcp_use) as the AI backend — same agent as CLI
"""

import asyncio
import os
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_groq import ChatGroqa
from mcp_use import MCPAgent, MCPClient

load_dotenv()

app = Flask(__name__)
CORS(app)

# ── Shared async state ──────────────────────────────────────
loop = asyncio.new_event_loop()
agent: MCPAgent | None = None
client: MCPClient | None = None
agent_lock = threading.Lock()


def start_background_loop(lp):
    asyncio.set_event_loop(lp)
    lp.run_forever()


# Start the event loop in a background thread so Flask (sync) can call async code
bg_thread = threading.Thread(target=start_background_loop, args=(loop,), daemon=True)
bg_thread.start()


def run_async(coro):
    """Run an async coroutine from sync Flask context."""
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=60)


async def init_agent():
    global agent, client
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        raise RuntimeError("GROQ_API_KEY not set in .env")

    client = MCPClient.from_config_file("config.json")
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=2048,
        groq_api_key=groq_key,
    )
    agent = MCPAgent(
        llm=llm,
        client=client,
        max_steps=10,
        memory_enabled=True,
    )
    print("✅ MCPAgent initialized")


# Initialize agent at startup
try:
    run_async(init_agent())
    agent_ready = True
except Exception as e:
    print(f"⚠️  Agent init failed: {e}")
    agent_ready = False


# ── Routes ──────────────────────────────────────────────────

@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "status": "online",
        "agent": "ready" if agent_ready else "not available",
        "model": "groq/llama3-70b-8192",
        "mcp_client": "connected" if client else "not connected",
    })


@app.route("/chat", methods=["POST"])
def chat():
    """General chat endpoint — the agent decides which tools to use."""
    data = request.json or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "message is required"}), 400
    if not agent:
        return jsonify({"error": "Agent not initialized"}), 503

    try:
        with agent_lock:
            response = run_async(agent.run(message))
        return jsonify({"success": True, "response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/analyze", methods=["POST"])
def analyze():
    """Analyze a GitHub repository."""
    data = request.json or {}
    repo = data.get("repository", "").strip()

    if not repo:
        return jsonify({"error": "repository is required"}), 400

    prompt = (
        f"Analyze the GitHub repository '{repo}'. "
        "Use the available tools to get: repository info, language stats, "
        "recent commits, top contributors, and README. "
        "Then give a comprehensive analysis covering: project purpose, "
        "tech stack, activity level, community health, and recommendations."
    )

    try:
        with agent_lock:
            response = run_async(agent.run(prompt))
        return jsonify({"success": True, "repository": repo, "analysis": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/trending", methods=["GET"])
def trending():
    """Get trending repositories."""
    language = request.args.get("language", "")
    since = request.args.get("since", "daily")

    prompt = f"Get the trending GitHub repositories{' for ' + language if language else ''}. Since: {since}. List them with names, descriptions, and star counts."

    try:
        with agent_lock:
            response = run_async(agent.run(prompt))
        return jsonify({"success": True, "response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search", methods=["POST"])
def search():
    """Search GitHub repositories."""
    data = request.json or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "query is required"}), 400

    prompt = f"Search GitHub for repositories matching: '{query}'. Show the top results with name, description, stars, and language."

    try:
        with agent_lock:
            response = run_async(agent.run(prompt))
        return jsonify({"success": True, "response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/user/<username>", methods=["GET"])
def user_profile(username):
    """Get a GitHub user profile."""
    prompt = f"Get the GitHub profile and top repositories for user '{username}'. Summarize their activity and most popular projects."

    try:
        with agent_lock:
            response = run_async(agent.run(prompt))
        return jsonify({"success": True, "username": username, "response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/clear", methods=["POST"])
def clear_memory():
    """Clear agent conversation memory."""
    if agent:
        agent.clear_conversation_history()
    return jsonify({"success": True, "message": "Conversation memory cleared"})


if __name__ == "__main__":
    print("🚀 GitHub Intelligence API Server")
    print("📡 Running on http://localhost:8000")
    print("🤖 Model: Groq llama3-70b-8192")
    print("🔌 MCP: stdio (server.py)")
    app.run(host="0.0.0.0", port=8000, debug=False, threaded=True)