"""
GitHub Intelligence CLI
Interactive chat using MCPAgent + mcp_use + ChatGroq (llama3-70b)
"""

import asyncio
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from mcp_use import MCPAgent, MCPClient

load_dotenv()


BANNER = """
╔══════════════════════════════════════════════════════╗
║       🤖  GitHub Intelligence CLI  🐙               ║
║   Powered by MCP + mcp_use + Groq llama3-70b        ║
╠══════════════════════════════════════════════════════╣
║  Commands:                                           ║
║    exit / quit  → end the session                   ║
║    clear        → clear conversation memory         ║
║    help         → show example prompts              ║
╚══════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
Example prompts you can try:
  • Analyze the repository facebook/react
  • What are the trending Python repos today?
  • Search for repositories about machine learning
  • Get the profile of user torvalds
  • What language does microsoft/vscode use?
  • Show me the latest commits in vercel/next.js
  • Who are the top contributors of django/django?
"""


async def run_cli():
    load_dotenv()

    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("❌ GROQ_API_KEY not found in .env file")
        return

    print(BANNER)
    print("Initializing MCP client and agent...")

    # MCP Client from config
    client = MCPClient.from_config_file("config.json")

    # Groq LLM
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=2048,
        groq_api_key=groq_key,
    )

    # MCPAgent with memory
    agent = MCPAgent(
        llm=llm,
        client=client,
        max_steps=10,
        memory_enabled=True,
    )

    print("✅ Agent ready! Type 'help' for example prompts.\n")

    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye! 👋")
                break

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit"):
                print("Ending session. Goodbye! 👋")
                break

            if user_input.lower() == "clear":
                agent.clear_conversation_history()
                print("🧹 Conversation memory cleared.\n")
                continue

            if user_input.lower() == "help":
                print(HELP_TEXT)
                continue

            print("\n🤖 Assistant: ", end="", flush=True)
            try:
                response = await agent.run(user_input)
                print(response)
            except Exception as e:
                print(f"\n❌ Error: {e}")
            print()

    finally:
        print("\nClosing MCP sessions...")
        if client and client.sessions:
            await client.close_all_sessions()
        print("Done. Bye!")


if __name__ == "__main__":
    asyncio.run(run_cli())