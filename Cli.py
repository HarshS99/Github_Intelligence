"""
cli.py — GitHub Intelligence CLI
Run: python cli.py
"""

import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

BANNER = """
╔══════════════════════════════════════════════════════╗
║   🐙  GitHub Intelligence CLI                       ║
║   Groq llama-3.3-70b  ·  Official GitHub MCP        ║
╠══════════════════════════════════════════════════════╣
║  exit / quit  →  end session                        ║
║  clear        →  wipe conversation memory           ║
║  help         →  example prompts                    ║
╚══════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
Example prompts:
  • Analyze the repository microsoft/vscode
  • Get the profile of user torvalds
  • List open issues in facebook/react
  • Show open PRs in vercel/next.js
  • Search for Rust web frameworks
  • Latest commits in nodejs/node
  • Find AI agent repos created in 2025
  • Get README of django/django
"""


def _load_config() -> dict:
    path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(path) as f:
        cfg = json.load(f)
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN", "")
    cfg["mcpServers"]["github"]["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] = token
    return cfg


async def main():
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("❌  GROQ_API_KEY not found in .env")
        return

    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        print("⚠️  No GitHub token — rate limits apply (60 req/hr)")

    print(BANNER)
    print("⏳ Starting MCP server (first Docker pull may take ~30s)…\n")

    from langchain_groq import ChatGroq
    from mcp_use import MCPAgent, MCPClient

    client = MCPClient(_load_config())
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=1500,
        groq_api_key=groq_key,
    )
    agent = MCPAgent(llm=llm, client=client, max_steps=10, memory_enabled=True)
    print("✅ Ready. Type 'help' for examples.\n")

    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye! 👋")
                break

            if not user_input:
                continue
            cmd = user_input.lower()
            if cmd in ("exit", "quit"):
                print("Goodbye! 👋")
                break
            if cmd == "clear":
                agent.clear_conversation_history()
                print("🧹 Memory cleared.\n")
                continue
            if cmd == "help":
                print(HELP_TEXT)
                continue

            print("\n🤖 ", end="", flush=True)
            try:
                print(await agent.run(user_input))
            except Exception as e:
                print(f"❌ {e}")
            print()
    finally:
        print("Closing sessions…")
        try:
            if client.sessions:
                await client.close_all_sessions()
        except Exception:
            pass
        print("Bye!")


if __name__ == "__main__":
    asyncio.run(main())