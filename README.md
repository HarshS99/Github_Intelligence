<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:161b22,100:21262d&height=200&section=header&text=GitHub%20Intelligence%20Platform&fontSize=40&fontColor=58a6ff&animation=fadeIn&fontAlignY=38&desc=AI-Powered%20GitHub%20Analysis%20%7C%20Repos%20%E2%80%A2%20Users%20%E2%80%A2%20PRs%20%E2%80%A2%20Issues%20%E2%80%A2%20Trending&descAlignY=58&descColor=8b949e" />

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Groq](https://img.shields.io/badge/Groq-LLaMA--3.3--70b-F55036?style=for-the-badge&logo=lightning&logoColor=white)](https://groq.com)
[![Docker](https://img.shields.io/badge/Docker-Required-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![GitHub MCP](https://img.shields.io/badge/GitHub%20MCP-Official-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

<br/>

```
 ██████╗ ██╗████████╗██╗  ██╗██╗   ██╗██████╗      █████╗ ██╗
██╔════╝ ██║╚══██╔══╝██║  ██║██║   ██║██╔══██╗    ██╔══██╗██║
██║  ███╗██║   ██║   ███████║██║   ██║██████╔╝    ███████║██║
██║   ██║██║   ██║   ██╔══██║██║   ██║██╔══██╗    ██╔══██║██║
╚██████╔╝██║   ██║   ██║  ██║╚██████╔╝██████╔╝    ██║  ██║██║
 ╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝     ╚═╝  ╚═╝╚═╝
```

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=58A6FF&center=true&vCenter=true&multiline=false&width=600&lines=AI-Powered+GitHub+Intelligence+%F0%9F%A4%96;Analyze+Any+Repo+in+Seconds+%E2%9A%A1;Powered+by+LLaMA+3.3+%2B+MCP+%F0%9F%A6%99;Ask+GitHub+Anything+%F0%9F%92%AC" alt="Typing SVG" />

</div>

---

## ✨ What is This?

> **GitHub Intelligence Platform** is a fully AI-powered analysis engine that connects to GitHub through the **official GitHub MCP Server**, powered by **Groq's LLaMA-3.3-70b** for blazing-fast inference. Ask anything about any repo, user, issue, or PR — in natural language.

<div align="center">

| 🤖 AI Chat | 📊 Repo Analysis | 👤 User Profiles | 🔥 Trending |
|:---:|:---:|:---:|:---:|
| Free-form GitHub Q&A | Deep repo insights | Stats + top repos | Live trending repos |

</div>

---

## 🚀 Features

<details open>
<summary><b>🧠 AI-Powered Free Chat</b></summary>
<br/>

Ask GitHub anything in plain English:
- *"What are the most active issues in torvalds/linux?"*
- *"Compare vercel/next.js vs remix-run/remix"*
- *"Who contributes most to microsoft/vscode?"*

</details>

<details open>
<summary><b>📦 Full Repository Analysis</b></summary>
<br/>

- Stars, forks, watchers, open issues
- Language breakdown
- README quality check
- Recent commit activity
- Top contributors

</details>

<details open>
<summary><b>👤 User Intelligence</b></summary>
<br/>

- Profile summary + bio
- All public repositories ranked by stars
- Contribution score
- Language diversity

</details>

<details open>
<summary><b>🔍 Smart Search & Trending</b></summary>
<br/>

- Search any repo by keyword or topic
- Trending repos by language (daily / weekly / monthly)
- Issues and PRs viewer per repo

</details>

---

## 📋 Requirements

<div align="center">

| Tool | Version | Status Check |
|:---|:---:|:---:|
| 🐍 Python | `3.11+` | `python --version` |
| 🐳 Docker Desktop | Running | `docker ps` |
| ⚡ Groq API Key | Free | [groq.com](https://console.groq.com) |
| 🔑 GitHub Token | Optional (recommended) | [github.com/settings/tokens](https://github.com/settings/tokens) |

</div>

---

## ⚡ Quick Start

### Step 1 — Clone the Project

```bash
git clone https://github.com/your-username/github-intelligence-platform.git
cd github-intelligence-platform
```

Make sure all these files are present:

```
📁 github-intelligence-platform/
├── 🐍 app.py              ← Flask API server
├── 💻 cli.py              ← Terminal interface
├── 🔗 github_client.py    ← GitHub REST client
├── ⚙️  config.json         ← MCP Docker config
├── 🌐 index.html          ← Web UI
├── 📦 requirements.txt    ← Python dependencies
├── 🔒 .env.example        ← Key template
└── 📖 README.md
```

---

### Step 2 — Set Up Environment

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```env
# Required — get free at https://console.groq.com
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx

# Recommended — without this, GitHub limits you to 60 req/hr
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxx
```

> 💡 **Tip:** Create a token with `repo` scope for full read/write and PR support. For public read-only operations, a token with no scopes is sufficient.

---

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

> ☕ First install downloads ~500 MB of ML libraries. Grab a coffee.

---

### Step 4 — Pull the GitHub MCP Docker Image

```bash
docker pull ghcr.io/github/github-mcp-server
```

> One-time download, ~100 MB.

---

### Step 5 — Run It!

This project supports both the original Flask API and a new Streamlit automation studio.

```bash
# Flask / web UI
python app.py

# Streamlit automation UI
streamlit run streamlit_app.py
```

The Streamlit studio includes built-in AI workflows for:
- repository structure analysis
- README improvement
- bug fix PR generation
- custom GitHub automation using MCP tools

Use `.env.example` as a template when creating your `.env` file.

You'll see:

```
═══════════════════════════════════════════════════════
  🐙 GitHub Intelligence API — http://localhost:8000
═══════════════════════════════════════════════════════
  GROQ_API_KEY   : ✅ set
  GITHUB_TOKEN   : ✅ set
  config.json    : ✅ loaded
═══════════════════════════════════════════════════════
```

Then open `index.html` in your browser — double-click or drag it into Chrome / Firefox.

---

## 🌐 API Reference

<div align="center">

| Method | Endpoint | Description |
|:---:|:---|:---|
| `GET` | `/status` | Health + config check |
| `POST` | `/chat` | Free-form AI chat `{"message": "..."}` |
| `POST` | `/analyze` | Full repo analysis `{"repository": "owner/repo"}` |
| `GET` | `/user/<username>` | User profile + top repos |
| `POST` | `/search` | Search repos `{"query": "..."}` |
| `GET` | `/issues/<owner>/<repo>` | Open issues |
| `GET` | `/pulls/<owner>/<repo>` | Open pull requests |
| `GET` | `/trending?language=python&since=daily` | Trending repos |
| `POST` | `/clear` | Clear session |

</div>

### Example Request

```bash
# Analyze a repository
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"repository": "microsoft/vscode"}'

# Free-form AI chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the trending Python repos this week?"}'
```

---

## 💻 CLI Mode (Optional)

Prefer the terminal? Run the interactive CLI:

```bash
python cli.py
```

Same features as the web UI — no browser needed.

---

## 🛠️ Troubleshooting

<details>
<summary><b>❌ GROQ_API_KEY not set</b></summary>

Your `.env` file is missing or in the wrong folder. It must be in the **same directory as `app.py`**.

</details>

<details>
<summary><b>❌ API shows "Offline" in the UI</b></summary>

The Flask server isn't running. Start it with:
```bash
python app.py
```

</details>

<details>
<summary><b>⏳ First request takes 30–60 seconds</b></summary>

Normal! Docker is starting the GitHub MCP container for the first time. Subsequent requests in the same session are much faster.

</details>

<details>
<summary><b>❌ ModuleNotFoundError: mcp_use</b></summary>

```bash
pip install mcp-use
```

</details>

<details>
<summary><b>❌ GitHub rate limit errors (403 / 429)</b></summary>

Add a GitHub Personal Access Token to your `.env`:
```env
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxxxxxxx
```

</details>

<details>
<summary><b>❌ Port 8000 already in use</b></summary>

Change the port at the bottom of `app.py`:
```python
app.run(host="0.0.0.0", port=8001, ...)
```
And update `index.html`:
```js
const API = 'http://localhost:8001'
```

</details>

<details>
<summary><b>❌ docker: command not found</b></summary>

Install Docker Desktop: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)

</details>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                     index.html                      │
│                   (Web Frontend)                    │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP
┌─────────────────────▼───────────────────────────────┐
│                     app.py                          │
│              (Flask API Server)                     │
│                                                     │
│  ┌──────────────┐    ┌────────────────────────────┐ │
│  │ github_      │    │     Groq LLaMA-3.3-70b     │ │
│  │ client.py    │    │    (AI Inference Engine)   │ │
│  │ (REST API)   │    └────────────────────────────┘ │
│  └──────────────┘              │                    │
└───────────────────────────┬────┼────────────────────┘
                            │    │ MCP Protocol
                ┌───────────▼────▼──────────────────┐
                │    GitHub MCP Server (Docker)      │
                │  ghcr.io/github/github-mcp-server  │
                └───────────────────────────────────┘
                                    │
                         ┌──────────▼──────────┐
                         │     GitHub API       │
                         │   api.github.com     │
                         └─────────────────────┘
```

---

## 📄 Project Structure

```
.
├── app.py            # Flask API server  ← start here
├── cli.py            # Terminal interface
├── github_client.py  # GitHub REST API client (used by app.py and streamlit_app.py)
├── config.json       # MCP Docker config
├── index.html        # Web UI
├── streamlit_app.py  # Streamlit automation studio
├── requirements.txt  # Python dependencies
├── .env.example      # Key template (copy to .env)
└── README.md
```

---

## 📊 Tech Stack

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-F55036?style=flat-square&logo=lightning&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub_MCP-181717?style=flat-square&logo=github&logoColor=white)
![LLaMA](https://img.shields.io/badge/LLaMA_3.3_70b-0467DF?style=flat-square&logo=meta&logoColor=white)

</div>

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:21262d,50:161b22,100:0d1117&height=120&section=footer&animation=fadeIn" />

**Made with ❤️ by [Harsh](https://github.com/your-username)**

⭐ **Star this repo if you found it useful!** ⭐

</div>
