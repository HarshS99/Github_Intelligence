# 🐙 GitHub Intelligence Platform

> AI-powered GitHub analysis — repos, users, issues, PRs, trending, and free-form chat.
> Built with Groq llama-3.3-70b, official GitHub MCP Server, and Flask.

---

## Requirements

| Tool | Version | Check with |
|---|---|---|
| Python | 3.11 or newer | `python --version` |
| Docker Desktop | Running | `docker ps` |
| Groq API key | Free at groq.com | — |
| GitHub token | Optional (recommended) | — |

---

## Quick start (4 steps)

### 1 — Clone / copy project files

Make sure these files are all in the same folder:

```
app.py
cli.py
github_client.py
config.json
index.html
requirements.txt
.env.example
```

### 2 — Create your `.env` file

```bash
cp .env.example .env
```

Then open `.env` and fill in your keys:

```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxx
```

- **GROQ_API_KEY** (required) — get it free at https://console.groq.com
- **GITHUB_PERSONAL_ACCESS_TOKEN** (recommended) — without it GitHub limits
  you to 60 API calls/hour. Create a token at https://github.com/settings/tokens
  (no scopes needed for public repos).

### 3 — Install Python packages

```bash
pip install -r requirements.txt
```

On first install this downloads ~500 MB of ML libraries. Grab a coffee. ☕

### 4 — Pull the GitHub MCP Docker image (one-time, ~100 MB)

```bash
docker pull ghcr.io/github/github-mcp-server
```

---

## Run

```bash
python app.py
```

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

Then open `index.html` in your browser (just double-click it or drag it into Chrome/Firefox).

---

## Using the CLI (optional)

```bash
python cli.py
```

Interactive terminal — same features as the web UI.

---

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/status` | Health + config check |
| POST | `/chat` | Free-form AI chat `{"message": "..."}` |
| POST | `/analyze` | Full repo analysis `{"repository": "owner/repo"}` |
| GET | `/user/<username>` | User profile + top repos |
| POST | `/search` | Search repos `{"query": "..."}` |
| GET | `/issues/<owner>/<repo>` | Open issues |
| GET | `/pulls/<owner>/<repo>` | Open pull requests |
| GET | `/trending?language=python&since=daily` | Trending repos |
| POST | `/clear` | Clear session |

---

## Troubleshooting

### `GROQ_API_KEY not set`
Your `.env` file is missing or in the wrong folder.
The `.env` must be in the same directory as `app.py`.

### API shows "Offline" in the UI
The Flask server isn't running. Run `python app.py` first.

### First request takes 30–60 seconds
Normal — Docker is starting the GitHub MCP container for the first time.
Subsequent requests within the session are faster.

### `ModuleNotFoundError: mcp_use`
```bash
pip install mcp-use
```

### GitHub rate limit errors (`403` or `429`)
Add a `GITHUB_PERSONAL_ACCESS_TOKEN` to your `.env`.

### Port 8000 already in use
Change the port at the bottom of `app.py`:
```python
app.run(host="0.0.0.0", port=8001, ...)
```
And update the `const API = 'http://localhost:8001'` line in `index.html`.

### `docker: command not found`
Install Docker Desktop: https://docs.docker.com/get-docker/

---

## Project structure

```
.
├── app.py            # Flask API server  ← start here
├── cli.py            # Terminal interface
├── github_client.py  # GitHub REST API client (used by app.py)
├── config.json       # MCP Docker config
├── index.html        # Web UI
├── requirements.txt  # Python dependencies
├── .env.example      # Key template (copy to .env)
└── README.md
```