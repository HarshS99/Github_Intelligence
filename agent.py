"""
Agent — Autonomous GitHub Intelligence Agent.
Uses official GitHub MCP Server (v1.1.2) for actions + Groq LLaMA for reasoning.
Supports two modes:
  1. Action Mode — MCP tools (create repo, issues, PRs, branches, etc.)
  2. Analysis Mode — Deep repo/profile analysis via GitHub API + ScrapeGraphAI

Uses a manual tool-calling loop with llm.bind_tools() — no prebuilt agent needed.
"""

import os
import json
import asyncio
import threading
from pathlib import Path
from dotenv import load_dotenv

# ── Safely apply nest_asyncio (skip if uvloop is active) ────────────
try:
    import nest_asyncio
    loop = asyncio.get_event_loop()
    if isinstance(loop, asyncio.BaseEventLoop):
        nest_asyncio.apply(loop)
except Exception:
    pass  # uvloop or no running loop — skip patching

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import tool
from langchain.agents import create_agent

try:
    from scrapegraph_py import Client as ScrapeClient
    _SCRAPEGRAPH_AVAILABLE = True
except ImportError:
    _SCRAPEGRAPH_AVAILABLE = False

load_dotenv()

# ── Config ───────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")

# Load MCP configuration from mcp.json
MCP_COMMAND = None
MCP_ARGS = []
MCP_ENV = os.environ.copy()

config_path = Path(__file__).parent / "mcp.json"
if config_path.is_file():
    try:
        with open(config_path) as f:
            cfg = json.load(f)
        github_cfg = cfg.get("mcp", {}).get("servers", {}).get("github", {})
        MCP_COMMAND = github_cfg.get("command")
        MCP_ARGS = github_cfg.get("args", [])
        for k, v in github_cfg.get("env", {}).items():
            if v == "<YOUR_TOKEN>":
                v = GITHUB_TOKEN
            MCP_ENV[k] = v
    except Exception as e:
        print(f"[agent] Failed to load mcp.json: {e}")

# Inject multiple token formats as requested
if GITHUB_TOKEN:
    for key in [
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "GITHUB_LOGIN",
        "GITHUB_TOKEN",
        "GITHUB_AUTH",
        "GITHUB_ACCESS_TOKEN",
        "GITHUB_AUTH_TOKEN",
        "GITHUB_PAT"
    ]:
        MCP_ENV[key] = GITHUB_TOKEN

# Fallback to binary in project root
if not MCP_COMMAND:
    default_binary = Path(__file__).parent / "github-mcp-server"
    if default_binary.is_file():
        MCP_COMMAND = str(default_binary)
        MCP_ARGS = ["stdio", "--toolsets", "all"]
    else:
        MCP_COMMAND = None


# ── LLM ─────────────────────────────────────────────────────────────
def _get_llm():
    """Create LLM instance (reads env at call time so sidebar key updates work)."""
    key = os.environ.get("GROQ_API_KEY", GROQ_API_KEY)
    return ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=key,
        temperature=0,
    )


# ── Custom Tools ─────────────────────────────────────────────────────
@tool
async def scrape_website(url: str, prompt: str) -> str:
    """Scrape a website using ScrapeGraphAI and return extracted data based on the prompt."""
    if not _SCRAPEGRAPH_AVAILABLE:
        return "Error: scrapegraph_py package is not installed."
    api_key = os.environ.get("SCRAPEGRAPH_API_KEY", "")
    if not api_key:
        return "Error: SCRAPEGRAPH_API_KEY is not set."
    try:
        client = ScrapeClient.from_env()
        res = client.smartscraper(website_url=url, user_prompt=prompt)
        if getattr(res, "status", None) == "success":
            return json.dumps(res.data.json_data, indent=2)
        else:
            return f"Error: {getattr(res, 'error', 'unknown error')}"
    except Exception as e:
        return f"Error scraping website: {e}"


@tool
async def extract_documentation(url: str) -> str:
    """Extract full documentation (README, wiki, docs) from a GitHub repo or library URL."""
    prompt = (
        "Extract the complete documentation from the given URL, including README, "
        "any markdown files, and relevant docs. Return the result as formatted markdown."
    )
    return await scrape_website.ainvoke({"url": url, "prompt": prompt})

# ── MCP Tool Filter ──────────────────────────────────────────────────
ESSENTIAL_TOOL_NAMES = {
    "create_repository",
    "get_file_contents",
    "create_or_update_file",
    "push_files",
    "create_pull_request",
    "create_branch",
    "list_branches",
    "list_issues",
    "issue_write",
    "get_me",
    "create_issue",
    "get_repository",
    "search_repositories",
    "list_commits",
}


def _filter_tools(tools: list) -> list:
    """Keep only essential tools to stay within Groq's TPM limit."""
    filtered = [t for t in tools if t.name in ESSENTIAL_TOOL_NAMES]
    if not filtered:
        print("[agent] Warning: no essential tools matched — returning all MCP tools.")
        return tools
    return filtered


def _trim_tool_descriptions(tools: list, max_chars: int = 120) -> list:
    """Truncate tool descriptions to reduce token count for Groq's TPM limit."""
    for t in tools:
        if hasattr(t, 'description') and t.description and len(t.description) > max_chars:
            t.description = t.description[:max_chars].rstrip() + "…"
    return tools


# ── Action Mode (MCP Tools) ─────────────────────────────────────────
MAX_RETRIES = 3
RETRY_BASE_DELAY = 15  # seconds

async def run_action_async(query: str) -> str:
    """Execute GitHub actions via official MCP Server tools with auto-retry on rate limits."""
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if not MCP_COMMAND:
                return (
                    "❌ MCP configuration not found or binary missing.\n"
                    "Please provide a valid `mcp.json` or place the `github-mcp-server` binary "
                    "in the project root directory."
                )

            llm = _get_llm()

            server_params = StdioServerParameters(
                command=MCP_COMMAND,
                args=MCP_ARGS,
                env={"GITHUB_PERSONAL_ACCESS_TOKEN":GITHUB_TOKEN}
            )

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the connection
                    await session.initialize()

                    # Get tools
                    tools = await load_mcp_tools(session)

                    if not tools:
                        return "❌ No MCP tools loaded. Check the github-mcp-server binary."

                    filtered = _filter_tools(tools)
                    filtered = filtered + [scrape_website, extract_documentation]

                    # Trim descriptions to save tokens
                    _trim_tool_descriptions(filtered)

                    # Enable graceful error handling for all tools so agent can recover from ToolExceptions
                    for t in filtered:
                        t.handle_tool_error = True

                    system_prompt = (
                        "You are an autonomous GitHub assistant focused on repository automation.\n"
                        "Use the provided MCP tools to create repositories, manage branches, open issues, "
                        "submit pull requests, and edit files.\n"
                        "When invoking tools, respect the exact argument names and types. "
                        "CRITICAL: NEVER include extra arguments not defined in the tool's schema (e.g. NEVER add a 'method' parameter). "
                        "CRITICAL: Do NOT pass 'null' or 'None' for optional parameters. If you don't have a value for an optional parameter, OMIT it completely from the tool call.\n"
                        "Provide concise, actionable responses."
                    )

                    agent = create_agent(
                        model=llm,
                        tools=filtered,
                        system_prompt=system_prompt,
                        
                    )

                    response = await agent.ainvoke({"messages": [HumanMessage(content=query)]})
                    
                    # Get the last message content
                    if "messages" in response and len(response["messages"]) > 0:
                        content = response["messages"][-1].content
                        if isinstance(content, list):
                            # Extract all text blocks if it's a list
                            text_blocks = [block["text"] for block in content if isinstance(block, dict) and "text" in block]
                            if text_blocks:
                                return "\n".join(text_blocks)
                            return str(content)
                        return str(content)
                    return "✅ Done (no further output)."

        except FileNotFoundError:
            return (
                "❌ `github-mcp-server` binary not found.\n"
                "Download it from: https://github.com/github/github-mcp-server/releases\n"
                "Place it in the project root directory."
            )
        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()

            # Check if it's a rate-limit error
            is_rate_limit = (
                "RateLimitError" in tb_str
                or "429" in tb_str
                or "rate_limit" in tb_str.lower()
            )

            if is_rate_limit and attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * attempt
                print(f"[agent] Rate limited (attempt {attempt}/{MAX_RETRIES}). Retrying in {delay}s...")
                await asyncio.sleep(delay)
                last_error = tb_str
                continue

            if is_rate_limit:
                return (
                    f"⏳ **Rate Limited** — Groq's free tier limits requests. "
                    f"Retried {MAX_RETRIES} times but still rate-limited. "
                    f"Please wait ~60 seconds and try again."
                )

            if "tool_use_failed" in tb_str or "BadRequestError" in tb_str:
                import re
                m = re.search(r"'failed_generation':\s*'(.*?)'", tb_str, re.DOTALL)
                if m:
                    failed = m.group(1)
                    return (
                        f"⚠️ **Groq Tool Validation Error**\n\n"
                        f"The Groq API rejected the tool call because of strict schema validation (e.g., passing `null` for omitted arguments).\n\n"
                        f"AI Attempt:\n```\n{failed}\n```\n\n"
                        f"Please try again or refine your prompt."
                    )
            return f"❌ **Agent Error**\n```\n{tb_str}```"

    # Should not reach here, but just in case
    return f"❌ **Agent Error** — All {MAX_RETRIES} retry attempts failed.\n```\n{last_error}\n```"


def _run_in_new_loop(coro):
    """Run an async coroutine in a fresh event loop on a new thread.
    This avoids conflicts with Streamlit's uvloop."""
    result = [None]
    exc = [None]

    def _target():
        try:
            result[0] = asyncio.run(coro)
        except Exception as e:
            exc[0] = e

    t = threading.Thread(target=_target)
    t.start()
    t.join()

    if exc[0] is not None:
        raise exc[0]
    return result[0]


def run_action(query: str) -> str:
    """Sync wrapper for action mode. Works inside Streamlit (uvloop)."""
    return _run_in_new_loop(run_action_async(query))


# ── List Available MCP Tools ─────────────────────────────────────────
async def list_mcp_tools_async() -> list:
    """List all tools from the official GitHub MCP Server."""
    if not MCP_COMMAND:
        return [{"name": "error", "description": "MCP configuration not found or binary missing."}]
    server_params = StdioServerParameters(
        command=MCP_COMMAND,
        args=MCP_ARGS,
        env=MCP_ENV,
    )
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                filtered = _filter_tools(tools)
                return [{"name": t.name, "description": t.description[:120]} for t in filtered]
    except Exception as e:
        return [{"name": "error", "description": str(e)}]


def list_mcp_tools() -> list:
    """Sync wrapper. Works inside Streamlit (uvloop)."""
    return _run_in_new_loop(list_mcp_tools_async())
