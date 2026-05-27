import asyncio
import json
import os
import time
import base64
from typing import Optional

import streamlit as st
from dotenv import load_dotenv

import github_client as gh

load_dotenv()

APP_TITLE = "GitHub Intelligence Studio"
DESCRIPTION = "AI-powered GitHub automation with MCP tool access, repository management, branch control, file editing, PRs, and issues."

APP_CSS = """
<style>
:root {
  --bg: #020617;
  --panel: rgba(15, 23, 42, 0.96);
  --border: rgba(148, 163, 184, 0.18);
  --text: #e2e8f0;
  --muted: #94a3b8;
  --accent: #38bdf8;
  --accent-strong: #22d3ee;
  --success: #4ade80;
}
body, .block-container { background: linear-gradient(180deg, #050816 0%, #020617 100%); color: var(--text); }
.stApp { background: none; }
.stButton>button {
  border-radius: 14px;
  border: none;
  background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
  color: #fff;
  font-weight: 700;
  box-shadow: 0 16px 40px rgba(14, 165, 233, 0.18);
}
.stButton>button:hover { opacity: 0.95; }
.stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div>div>div {
  border-radius: 16px !important;
  border: 1px solid rgba(148, 163, 184, 0.3) !important;
  background: rgba(15, 23, 42, 0.95) !important;
  color: #e2e8f0 !important;
}
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus { border-color: rgba(56, 189, 248, 0.75) !important; }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown p, .stMarkdown span { color: #e2e8f0; }
.header-panel { padding: 1.8rem 1.75rem; border-radius: 24px; background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(148, 163, 184, 0.18); margin-bottom: 1.8rem; }
.header-panel .title { font-size: 2.5rem; font-weight: 800; margin-bottom: 0.65rem; letter-spacing: -0.04em; }
.header-panel .subtitle { color: #cbd5e1; font-size: 1rem; line-height: 1.75; max-width: 860px; margin-bottom: 1.5rem; }
.header-panel .brand-row { display: flex; flex-wrap: wrap; align-items: center; gap: 0.95rem; margin-bottom: 1.6rem; }
.brand-item { display: inline-flex; align-items: center; gap: 0.75rem; background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 999px; padding: 0.75rem 1rem; color: #e2e8f0; font-size: 0.95rem; }
.brand-item img { width: 24px; height: 24px; border-radius: 8px; object-fit: contain; }
.brand-item span { display: inline-block; vertical-align: middle; }
.top-summary { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; }
.summary-card { background: rgba(15, 23, 42, 0.88); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 20px; padding: 1.15rem 1.25rem; min-height: 120px; }
.summary-card h4 { margin: 0 0 0.55rem; color: #38bdf8; font-size: 0.95rem; letter-spacing: 0.04em; text-transform: uppercase; }
.summary-card p { margin: 0; color: #cbd5e1; font-size: 0.94rem; line-height: 1.7; }
.section-box { background: rgba(15, 23, 42, 0.92); border: 1px solid rgba(148, 163, 184, 0.16); border-radius: 22px; padding: 1.4rem; margin-bottom: 1.5rem; }
.section-label { font-size: 0.85rem; letter-spacing: 0.2em; text-transform: uppercase; color: #38bdf8; margin-bottom: 0.8rem; display: block; }
.custom-divider { border: none; height: 1px; background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.35), transparent); margin: 2rem 0; }
.sidebar .stButton>button { border-radius: 14px; margin-top: 0.6rem; }
.sidebar .stTextInput>div>div>input, .sidebar .stTextArea>div>div>textarea { background: rgba(15, 23, 42, 0.95) !important; }
</style>
"""


def _load_config() -> dict:
    path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(path) as f:
        cfg = json.load(f)
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN", "")
    cfg["mcpServers"]["github"]["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] = token
    return cfg


async def _run_agent_async(query: str) -> str:
    from langchain_groq import ChatGroq
    from mcp_use import MCPAgent, MCPClient

    client = MCPClient(_load_config())
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.25,
        max_tokens=600,
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
    )
    agent = MCPAgent(llm=llm, client=client, max_steps=12, memory_enabled=False)
    try:
        return await agent.run(query)
    finally:
        try:
            if client.sessions:
                await client.close_all_sessions()
        except Exception:
            pass


def run_agent(query: str) -> str:
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run_agent_async(query))
    finally:
        loop.close()


def show_status() -> dict:
    gh_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN", "")
    groq_key = os.getenv("GROQ_API_KEY", "")
    token_valid = False
    auth_user = None

    st.sidebar.header("Connection status")
    if gh_token:
        try:
            user = gh.get_authenticated_user()
            token_valid = True
            auth_user = user.get("login")
            st.sidebar.markdown(
                """
                - **GitHub:** Connected
                - **GROQ:** %s
                - **MCP config:** %s
                """
                % (
                    "Configured" if groq_key else "Missing",
                    "Loaded" if os.path.exists("config.json") else "Missing",
                )
            )
            st.sidebar.markdown(f"**Authenticated:** {auth_user}")
        except Exception:
            st.sidebar.markdown(
                """
                - **GitHub:** Invalid token
                - **GROQ:** %s
                - **MCP config:** %s
                """
                % (
                    "Configured" if groq_key else "Missing",
                    "Loaded" if os.path.exists("config.json") else "Missing",
                )
            )
            st.sidebar.markdown("**Authenticated:** Invalid token")
    else:
        st.sidebar.markdown(
            """
            - **GitHub:** Missing
            - **GROQ:** %s
            - **MCP config:** %s
            """
            % (
                "Configured" if groq_key else "Missing",
                "Loaded" if os.path.exists("config.json") else "Missing",
            )
        )

    return {
        "token_present": bool(gh_token),
        "token_valid": token_valid,
        "auth_user": auth_user,
        "groq_configured": bool(groq_key),
        "config_loaded": os.path.exists("config.json"),
    }


def format_repo_info(repo: str):
    try:
        info = gh.get_repo_info(repo)
        st.subheader("Repository Info")
        st.json(info)

        st.markdown("**README preview:**")
        st.code(gh.get_readme(repo)[:2000], language="markdown")

        commits = gh.get_commits(repo, limit=5)
        st.markdown("**Recent commits**")
        for c in commits:
            st.write(f"- `{c['sha']}` {c['message']} — {c['author']} ({c['date'][:10]})")

        lang = gh.get_languages(repo)
        st.markdown("**Languages**")
        st.json(lang)
    except Exception as e:
        st.error(f"Could not load repo: {e}")


def normalize_repo_name(repo: str) -> str:
    if not repo:
        return ""
    repo = repo.strip()
    if repo.endswith(".git"):
        repo = repo[:-4]
    if repo.startswith("git@github.com:"):
        repo = repo[len("git@github.com:") :]
    if repo.startswith("https://github.com/") or repo.startswith("http://github.com/"):
        parts = repo.rstrip("/").split("/")
        if len(parts) >= 5:
            return f"{parts[3]}/{parts[4]}"
        return ""
    if repo.startswith("github.com/"):
        parts = repo.rstrip("/").split("/")
        if len(parts) >= 3:
            return f"{parts[1]}/{parts[2]}"
        return ""
    return repo


def load_file(repo: str, path: str, branch: str):
    try:
        file_data = gh.get_file(repo, path, ref=branch if branch else None)
        st.code(file_data["content"], language="text")
        return file_data
    except Exception as e:
        st.error(f"Could not load file: {e}")
        return None


def get_default_branch(repo: str) -> str:
    try:
        return gh.get_repo_info(repo).get("default_branch") or "main"
    except Exception:
        return "main"


def safe_create_branch(repo: str, branch_name: str, base_branch: str):
    try:
        return gh.create_branch(repo, branch_name, from_branch=base_branch)
    except Exception as e:
        msg = str(e)
        if "Reference already exists" in msg or "already exists" in msg:
            return {"ref": f"refs/heads/{branch_name}"}
        raise


def ai_improve_readme(repo: str, base_branch: str) -> str:
    readme = gh.get_readme(repo)
    prompt = (
        f"You are a GitHub AI assistant. Improve the README for the repository {repo}. "
        f"Return only the updated Markdown content, with better structure, examples, and clarity. "
        f"Do not include any commentary.\n\nCurrent README:\n{readme}"
    )
    return run_agent(prompt)


def ai_fix_file(repo: str, path: str, issue_description: str, base_branch: str) -> str:
    original = gh.get_file(repo, path, ref=base_branch)
    prompt = (
        f"You are a GitHub AI assistant. Fix the bug described below in the file {path} for repository {repo}. "
        f"The bug description is: {issue_description}.\n\n"
        f"Current file content:\n{original['content']}\n\n"
        f"Return the complete updated file content only, with no code fences or extra explanation."
    )
    return run_agent(prompt)


def ai_create_pr(repo: str, branch_name: str, base_branch: str, title: str, body: str) -> dict:
    return gh.create_pull_request(repo, title=title, body=body, head=branch_name, base=base_branch)


def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="🚀", layout="wide", initial_sidebar_state="expanded")
    st.markdown(APP_CSS, unsafe_allow_html=True)

    status = show_status()
    auth_label = (
        "Connected" if status["token_valid"] else "Invalid token" if status["token_present"] else "Missing"
    )

    st.markdown(
        f"""
        <div class='header-panel'>
            <div class='title'>{APP_TITLE}</div>
            <div class='subtitle'>{DESCRIPTION}</div>
            <div class='brand-row'>
                <div class='brand-item'>
                    <img src='https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png' alt='GitHub' />
                    <span>GitHub automation</span>
                </div>
                <div class='brand-item'>
                    <img src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PGNpcmNsZSBjeD0iMTAiIGN5PSIxMCIgcj0iNyIgZmlsbD0iIzM4YmRmOCIvPjxwYXRoIGQ9Ik0xNC41IDE0LjVsNSA1IiBzdHJva2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+PC9zdmc+' alt='Scraping' />
                    <span>Scraping intelligence</span>
                </div>
                <div class='brand-item'>
                    <img src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHJlY3QgeD0iNSIgeT0iNSIgd2lkdGg9IjE0IiBoZWlnaHQ9IjE0IiByeD0iNCIgZmlsbD0iIzM4YmRmOCIvPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjMuNSIgZmlsbD0iI2ZmZmZmZiIvPjwvc3ZnPg==' alt='AI' />
                    <span>AI workflow</span>
                </div>
            </div>
            <div class='top-summary'>
                <div class='summary-card'>
                    <h4>Repository target</h4>
                    <p>{normalize_repo_name(st.session_state.get('repo_input', '')) or 'Not set'}</p>
                </div>
                <div class='summary-card'>
                    <h4>GitHub auth</h4>
                    <p>{auth_label}</p>
                </div>
                <div class='summary-card'>
                    <h4>AI access</h4>
                    <p>{'Ready' if status['groq_configured'] else 'Missing'}</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if status["token_present"] and not status["token_valid"]:
        st.error("GitHub token is invalid. Please update your PAT with the correct scope and restart the app.")

    repo_input = st.text_input("Repository (owner/repo or URL)", value=st.session_state.get("repo_input", ""))
    st.session_state["repo_input"] = repo_input
    repo_id = normalize_repo_name(repo_input)
    if repo_input and repo_id and repo_input != repo_id:
        st.success(f"Detected repository: {repo_id}")

    tabs = st.tabs(["Repo", "Branches", "Files", "Pull Requests", "Issues", "AI Assistant"])

    with tabs[0]:
        st.header("Repository Operations")
        left, right = st.columns([2, 1])

        with left:
            st.subheader("Repository overview")
            if st.button("Load repository details"):
                if repo_id:
                    format_repo_info(repo_id)
                else:
                    st.warning("Enter a repository name in owner/repo format or a GitHub repo URL.")

        with right:
            st.subheader("Quick ops")
            st.write("Use this panel to inspect the repository or create a new GitHub repo from your token.")
            st.write("**Note:** GitHub repo creation requires `repo` or `public_repo` scope.")

        st.markdown("---")
        st.subheader("Create a new repository")
        create_name = st.text_input("New repository name", key="new_repo_name")
        create_desc = st.text_area("Description", key="new_repo_desc", height=120)
        create_private = st.checkbox("Private repository", key="new_repo_private")
        org_name = st.text_input("Organization (optional)", key="new_repo_org")
        st.caption("Leave Organization blank to create the repo in your GitHub account. Use this only for organizations you belong to.")
        if st.button("Create repository"):
            if not create_name:
                st.warning("Enter a repository name.")
            else:
                try:
                    new_repo = gh.create_repo(create_name, description=create_desc, private=create_private, org=org_name or None)
                    st.success("Repository created successfully.")
                    st.write(f"[{new_repo.get('full_name')}]({new_repo.get('html_url')})")
                except Exception as e:
                    error_msg = str(e)
                    if "403" in error_msg or "Forbidden" in error_msg:
                        st.error("Failed to create repository: GitHub token does not have repository creation permission. Please grant `repo` or `public_repo` scope and try again.")
                    else:
                        st.error(f"Failed to create repository: {e}")

    with tabs[1]:
        st.header("Branch Management")
        branch_base = st.text_input("Base branch", value="main", key="branch_base")
        new_branch_name = st.text_input("New branch name", key="branch_new")

        if st.button("List branches"):
            if repo_id:
                try:
                    branches = gh.get_branches(repo_id)
                    st.table(branches)
                except Exception as e:
                    st.error(f"Could not list branches: {e}")
            else:
                st.warning("Enter a repository name first.")

        if st.button("Create branch"):
            if not repo_id or not new_branch_name:
                st.warning("Enter repo and new branch name.")
            else:
                try:
                    branch = gh.create_branch(repo_id, new_branch_name, from_branch=branch_base)
                    st.success(f"Branch created: {branch['ref']}")
                except Exception as e:
                    st.error(f"Failed to create branch: {e}")

    with tabs[2]:
        st.header("File Management")
        file_path = st.text_input("File path", value="README.md", key="file_path")
        file_branch = st.text_input("Branch", value="main", key="file_branch")

        if st.button("Load file content"):
            if repo_id and file_path:
                file_data = load_file(repo_id, file_path, file_branch)
                if file_data:
                    st.session_state["loaded_file_sha"] = file_data.get("sha")
                    st.session_state["file_edit_content"] = file_data.get("content", "")
            else:
                st.warning("Enter repo and file path.")

        st.markdown("**Edit file content**")
        content = st.text_area("File text", height=320, key="file_edit_content")
        commit_message = st.text_input("Commit message", value="Update file via GitHub Intelligence Studio", key="file_commit_message")
        if st.button("Save file"):
            if not repo_id or not file_path or not content:
                st.warning("Provide repo, file path, and file content.")
            else:
                sha = st.session_state.get("loaded_file_sha")
                try:
                    result = gh.create_or_update_file(repo_id, file_path, commit_message, content, branch=file_branch or None, sha=sha)
                    st.success("File saved successfully.")
                    st.write(result.get("content", {}).get("html_url") or result.get("commit", {}).get("html_url"))
                except Exception as e:
                    st.error(f"Could not save file: {e}")

    with tabs[3]:
        st.header("Pull Request Creator")
        pr_head = st.text_input("Head branch", key="pr_head")
        pr_base = st.text_input("Base branch", value="main", key="pr_base")
        pr_title = st.text_input("PR title", key="pr_title")
        pr_body = st.text_area("PR description", key="pr_body")
        if st.button("Create pull request"):
            if not repo_id or not pr_head or not pr_title:
                st.warning("Enter repo, head branch, and PR title.")
            else:
                try:
                    pr = gh.create_pull_request(repo_id, pr_title, pr_body, pr_head, base=pr_base)
                    st.success("Pull request created successfully.")
                    st.write(pr.get("html_url"))
                except Exception as e:
                    st.error(f"Failed to create PR: {e}")

    with tabs[4]:
        st.header("Issue Manager")
        if st.button("List open issues"):
            if repo_id:
                try:
                    issues = gh.get_issues(repo_id, limit=30)
                    if issues:
                        st.table(issues)
                    else:
                        st.info("No open issues found.")
                except Exception as e:
                    st.error(f"Could not fetch issues: {e}")
            else:
                st.warning("Enter a repository name first.")

        st.markdown("---")
        issue_title = st.text_input("New issue title", key="issue_title")
        issue_body = st.text_area("New issue body", key="issue_body")
        issue_labels = st.text_input("Labels (comma separated)", key="issue_labels")
        if st.button("Create issue"):
            if not repo_id or not issue_title:
                st.warning("Enter repo and issue title.")
            else:
                try:
                    labels = [label.strip() for label in issue_labels.split(",") if label.strip()]
                    issue = gh.create_issue(repo_id, issue_title, body=issue_body, labels=labels or None)
                    st.success("Issue created successfully.")
                    st.write(issue.get("html_url"))
                except Exception as e:
                    st.error(f"Failed to create issue: {e}")

        close_number = st.number_input("Close issue number", min_value=1, step=1, key="close_issue_number")
        if st.button("Close issue"):
            if not repo_id:
                st.warning("Enter repo first.")
            else:
                try:
                    issue = gh.close_issue(repo_id, int(close_number))
                    st.write(issue.get("html_url"))
                except Exception as e:
                    st.error(f"Could not close issue: {e}")

    with tabs[5]:
        st.header("AI Assistant")
        st.write("Use AI to improve README, create a bug-fix PR, analyze repository structure, or run custom GitHub automation workflows.")

        ai_task = st.selectbox(
            "AI task",
            [
                "Analyze repository structure",
                "Improve README",
                "Create bug-fix PR",
                "Custom GitHub assistant"
            ],
            key="ai_task",
        )

        if ai_task == "Analyze repository structure":
            prompt = st.text_area("Analysis prompt", value="Review the repository and summarize its architecture, strengths, risks, and recommended improvements.", height=180, key="ai_analysis_prompt")
            if st.button("Run analysis"):
                if not repo_input:
                    st.warning("Enter a repository name first.")
                else:
                    try:
                        final_prompt = (
                            f"You are a GitHub AI assistant. Analyze the repository {repo_input} and produce a clear report. "
                            f"Include architecture, component relationships, code quality, and concrete suggestions.\n\n"
                            f"Current repo: {repo_input}."
                        )
                        with st.spinner("Running analysis..."):
                            response = run_agent(final_prompt)
                        st.text_area("Analysis result", value=response, height=380)
                    except Exception as e:
                        st.error(f"AI assistant failed: {e}")

        elif ai_task == "Improve README":
            branch_name = st.text_input("New branch name", value=f"ai-readme-improvement-{int(time.time())}", key="ai_readme_branch")
            base_branch = st.text_input("Base branch", value=get_default_branch(repo_input), key="ai_readme_base")
            if st.button("Generate improved README"):
                if not repo_id:
                    st.warning("Enter a repository name first.")
                else:
                    try:
                        with st.spinner("Generating improved README..."):
                            improved = ai_improve_readme(repo_id, base_branch)
                        st.session_state["ai_readme_content"] = improved
                        st.success("Improved README generated.")
                        st.code(improved, language="markdown")
                    except Exception as e:
                        st.error(f"Could not generate improved README: {e}")

            if st.button("Create README PR"):
                if not repo_id or not st.session_state.get("ai_readme_content"):
                    st.warning("Generate the improved README first.")
                else:
                    try:
                        branch = safe_create_branch(repo_id, branch_name, base_branch)
                        current_file = gh.get_file(repo_id, "README.md", ref=base_branch)
                        gh.create_or_update_file(
                            repo_id,
                            "README.md",
                            "Improve README with AI",
                            st.session_state["ai_readme_content"],
                            branch=branch_name,
                            sha=current_file["sha"],
                        )
                        pr = ai_create_pr(
                            repo_id,
                            branch_name,
                            base_branch,
                            "Improve README with AI",
                            "This PR improves the README content using automated GitHub MCP assistant guidance.",
                        )
                        st.success("README improvement PR created.")
                        st.write(pr.get("html_url"))
                    except Exception as e:
                        st.error(f"Failed to create README PR: {e}")

        elif ai_task == "Create bug-fix PR":
            file_path = st.text_input("Target file path", value="README.md", key="ai_bugfix_file")
            issue_desc = st.text_area("Bug or improvement description", key="ai_bugfix_desc", height=140)
            branch_name = st.text_input("New branch name", value=f"ai-bugfix-{int(time.time())}", key="ai_bugfix_branch")
            base_branch = st.text_input("Base branch", value=get_default_branch(repo_input), key="ai_bugfix_base")

            if st.button("Generate fix content"):
                if not repo_id or not issue_desc or not file_path:
                    st.warning("Enter repo, file path, and bug description.")
                else:
                    try:
                        with st.spinner("Generating fix content..."):
                            improved = ai_fix_file(repo_id, file_path, issue_desc, base_branch)
                        st.session_state["ai_bugfix_content"] = improved
                        st.success("Bug fix content generated.")
                        st.code(improved, language="text")
                    except Exception as e:
                        st.error(f"Could not generate fix content: {e}")

            if st.button("Create bug-fix PR"):
                if not repo_id or not file_path or not issue_desc or not st.session_state.get("ai_bugfix_content"):
                    st.warning("Generate the fix content before creating the PR.")
                else:
                    try:
                        branch = safe_create_branch(repo_id, branch_name, base_branch)
                        current_file = gh.get_file(repo_id, file_path, ref=base_branch)
                        gh.create_or_update_file(
                            repo_id,
                            file_path,
                            f"Apply bug fix to {file_path} with AI",
                            st.session_state["ai_bugfix_content"],
                            branch=branch_name,
                            sha=current_file["sha"],
                        )
                        pr = ai_create_pr(
                            repo_id,
                            branch_name,
                            base_branch,
                            f"AI bug fix for {file_path}",
                            f"Automated bug fix PR generated by AI for {file_path}.\n\nIssue summary: {issue_desc}",
                        )
                        st.success("Bug-fix PR created.")
                        st.write(pr.get("html_url"))
                    except Exception as e:
                        st.error(f"Failed to create bug-fix PR: {e}")

        else:
            user_prompt = st.text_area("Your custom GitHub prompt", key="ai_prompt", height=180)
            if st.button("Run custom AI assistant"):
                if not user_prompt:
                    st.warning("Enter a prompt describing what you want the AI to do.")
                else:
                    try:
                        prompt = (
                            f"You are a GitHub automation assistant with access to GitHub MCP tools. "
                            f"The user asked: {user_prompt}\n\n"
                            f"Use repo {repo_id or repo_input} if applicable. "
                            f"If you need to inspect repo metadata or create branches, files, PRs or issues, do so via GitHub MCP tool capabilities."
                        )
                        with st.spinner("Running AI agent..."):
                            response = run_agent(prompt)
                        st.text_area("Assistant response", value=response, height=380)
                    except Exception as e:
                        st.error(f"AI agent failed: {e}")


if __name__ == "__main__":
    main()
