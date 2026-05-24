# 🐙 GitHub Intelligence Platform

AI-powered GitHub analyzer using **MCP** (Model Context Protocol) + **mcp_use** + **Groq llama-3.3-70b**.

## 🎯 Features

- 🔍 **User Profile Analysis** - Get detailed GitHub user information
- 📊 **Repository Analytics** - Analyze repos with language stats, commits, contributors
- 🔥 **Trending Repos** - Scrape GitHub trending page (no API needed)
- 🤖 **AI-Powered Insights** - Natural language queries powered by Groq LLM
- 💬 **Conversational Memory** - Agent remembers context across queries
- 🌐 **Web UI + CLI** - Use via browser or terminal

## 🏗️ Architecture

```
index.html  →  api_server.py (Flask :8000)
                    ↓
              MCPAgent (mcp_use)  ← conversation memory
                    ↓
            MCP Client (stdio)
                    ↓
              server.py  ← 9 GitHub tools
                    ↓
            GitHub API + Web Scraping
```

**MCP server runs as a subprocess** — no separate terminal needed. `mcp_use` manages launching via `config.json`.

## 📋 Prerequisites

- **Python 3.11+** (required for `mcp-use`)
- **Groq API Key** (free at [console.groq.com](https://console.groq.com))
- **GitHub Token** (optional but recommended for higher rate limits)

## 🚀 Setup

### 1. Install Python 3.11+

```bash
# macOS
brew install python@3.11

# Linux
sudo apt update && sudo apt install python3.11
```

### 2. Clone & Install

```bash
git clone https://github.com/HarshS99/GitHub-Profile-Analyzer.git
cd GitHub-Profile-Analyzer

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file:

```bash
cat > .env << 'EOF'
GROQ_API_KEY=your-groq-api-key-here
GITHUB_TOKEN=your-github-token-here
EOF
```

**Get API Keys:**
- Groq: https://console.groq.com/keys
- GitHub: https://github.com/settings/tokens (need `public_repo` scope)

### 4. Run

**Option A — Web UI:**
```bash
python3.11 api_server.py
# Open index.html in browser
```

**Option B — CLI:**
```bash
python3.11 cli.py
```

## 🛠️ Available MCP Tools

| Tool | Description |
|------|-------------|
| `get_repository_info` | Stars, forks, issues, language, topics |
| `get_repository_readme` | README content |
| `get_repository_commits` | Recent commit history |
| `search_repositories` | Search by keyword |
| `get_trending_repos` | Scrape GitHub trending (web scraping) |
| `analyze_code_stats` | Language breakdown percentages |
| `get_contributors` | Top contributors |
| `get_user_profile` | GitHub user profile |
| `get_user_repos` | User's public repos |

## 💬 Example Queries

**Web UI or CLI:**
```
Analyze facebook/react
Get the GitHub profile for user torvalds
What are the trending Python repos today?
Search for machine learning frameworks
Show me the latest commits in vercel/next.js
Who are the top contributors of django/django?
```

## 📁 Project Structure

```
├── server.py          # MCP server (stdio) with 9 GitHub tools
├── api_server.py      # Flask API wrapping MCPAgent
├── cli.py             # Terminal chat interface
├── config.json        # MCP client configuration
├── index.html         # Web UI
├── requirements.txt   # Python dependencies
├── .env              # API keys (create this)
└── README.md         # This file
```

## 🔧 Configuration

**config.json** - MCP server configuration:
```json
{
    "mcpServers": {
        "github-intelligence": {
            "command": "python3.11",
            "args": ["/absolute/path/to/server.py"]
        }
    }
}
```

Update the path to your actual `server.py` location.

## 🐛 Troubleshooting

**401 Unauthorized errors:**
- Check `.env` has valid `GITHUB_TOKEN`
- Verify `config.json` has absolute path to `server.py`
- Regenerate GitHub token at github.com/settings/tokens

**ModuleNotFoundError:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Groq rate limit (413 error):**
- Free tier: 12,000 tokens/minute
- Solution: Reduce `max_tokens` in `api_server.py` or upgrade to Pro

**Python version issues:**
```bash
python3.11 --version  # Must be 3.11 or higher
```

## 🎨 Web UI Features

- **User Profile Lookup** - Enter GitHub username
- **Repository Analysis** - Deep dive into any repo
- **Search Repos** - Find repos by keyword
- **Quick Tools** - One-click trending, ML repos, etc.
- **Clear Memory** - Reset conversation context

## 📝 Notes

- MCP server launches automatically via `mcp_use`
- Conversation memory persists within a session
- GitHub token is optional but recommended for higher rate limits (5,000/hour vs 60/hour)
- Web scraping used for trending repos (no API available)

## 🤝 Contributing

Pull requests welcome! For major changes, open an issue first.

## 📄 License

MIT

## 🙏 Acknowledgments

- [MCP](https://modelcontextprotocol.io) - Model Context Protocol
- [mcp-use](https://github.com/wong2/mcp-use) - Python MCP client
- [Groq](https://groq.com) - Fast LLM inference
- [LangChain](https://langchain.com) - AI framework

---

Built with ❤️ using MCP + Groq