"""
GitHub Intelligence Platform — Streamlit UI
Premium dark-themed interface with MCP + ScrapeGraphAI + Groq integration.
"""

import streamlit as st
import time
import json
import os
import base64
from agent import run_action, list_mcp_tools

# ── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="GitHub Intelligence Platform",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    st.logo("logo.png")
except AttributeError:
    pass

# ── Load Logo ────────────────────────────────────────────────────────
try:
    with open("logo.png", "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    logo_src = f"data:image/png;base64,{logo_b64}"
except Exception:
    logo_src = ""

# ── Custom CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ── Global ── */
    .stApp {
        background: #07080d;
        font-family: 'Inter', sans-serif;
    }

    /* Animated grain overlay for texture */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(ellipse at 20% 50%, rgba(88,166,255,0.03) 0%, transparent 50%),
                    radial-gradient(ellipse at 80% 20%, rgba(139,92,246,0.03) 0%, transparent 50%),
                    radial-gradient(ellipse at 50% 80%, rgba(236,72,153,0.02) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c0d14 0%, #080a10 100%) !important;
        border-right: 1px solid rgba(88,166,255,0.08) !important;
    }
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #58a6ff !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(13,17,23,0.6);
        border: 1px solid rgba(48,54,61,0.4);
        border-radius: 12px;
        padding: 4px;
        backdrop-filter: blur(12px);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        color: #6e7681;
        font-weight: 600;
        font-size: 0.88rem;
        padding: 10px 20px;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #c9d1d9;
        background: rgba(88,166,255,0.05);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(88,166,255,0.12), rgba(139,92,246,0.08)) !important;
        color: #58a6ff !important;
        box-shadow: 0 0 20px rgba(88,166,255,0.06);
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #1a7f37 0%, #238636 50%, #2ea043 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 10px 28px !important;
        letter-spacing: 0.3px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 2px 8px rgba(35,134,54,0.2) !important;
    }
    .stButton > button:hover {
        box-shadow: 0 6px 24px rgba(46, 160, 67, 0.35) !important;
        transform: translateY(-2px) !important;
    }
    .stButton > button:active {
        transform: translateY(0px) !important;
    }

    /* ── Text Inputs ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(10,12,18,0.9) !important;
        border: 1px solid rgba(48,54,61,0.5) !important;
        color: #e6edf3 !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.2s ease !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #58a6ff !important;
        box-shadow: 0 0 0 3px rgba(88,166,255,0.12), 0 0 20px rgba(88,166,255,0.05) !important;
    }

    /* ── Chat Messages ── */
    [data-testid="stChatMessage"] {
        background: rgba(13,17,23,0.5) !important;
        border: 1px solid rgba(48,54,61,0.3) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(8px) !important;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        background: rgba(13,17,23,0.6) !important;
        border-radius: 10px !important;
        color: #c9d1d9 !important;
        font-weight: 500 !important;
        border: 1px solid rgba(48,54,61,0.3) !important;
    }

    /* ── Spinner ── */
    .stSpinner > div {
        border-top-color: #58a6ff !important;
    }

    /* ── Hide default elements ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ── Custom Components ── */
    .hero-container {
        position: relative;
        background: linear-gradient(135deg, rgba(88,166,255,0.04) 0%, rgba(139,92,246,0.04) 50%, rgba(236,72,153,0.03) 100%);
        border: 1px solid rgba(88,166,255,0.1);
        border-radius: 20px;
        padding: 32px 36px;
        margin-bottom: 28px;
        backdrop-filter: blur(20px);
        overflow: hidden;
    }
    .hero-container::before {
        content: '';
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: radial-gradient(circle at 30% 40%, rgba(88,166,255,0.06) 0%, transparent 40%),
                    radial-gradient(circle at 70% 60%, rgba(139,92,246,0.04) 0%, transparent 40%);
        animation: heroGlow 8s ease-in-out infinite alternate;
        pointer-events: none;
    }
    @keyframes heroGlow {
        0% { transform: translate(0, 0) rotate(0deg); }
        100% { transform: translate(2%, -2%) rotate(3deg); }
    }
    .hero-title-row {
        display: flex;
        align-items: center;
        gap: 16px;
        flex-wrap: wrap;
        position: relative;
        z-index: 1;
    }
    .hero-logo {
        height: 52px;
        filter: drop-shadow(0 0 12px rgba(88,166,255,0.2));
        transition: transform 0.3s ease;
    }
    .hero-logo:hover {
        transform: scale(1.08) rotate(-3deg);
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 900;
        background: linear-gradient(135deg, #e6edf3 0%, #58a6ff 40%, #8b5cf6 70%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-size: 200% 200%;
        animation: gradientShift 4s ease-in-out infinite alternate;
        letter-spacing: -0.8px;
        line-height: 1.2;
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        100% { background-position: 100% 50%; }
    }
    .hero-subtitle {
        color: #6e7681;
        font-size: 0.92rem;
        font-weight: 400;
        margin-top: 8px;
        position: relative;
        z-index: 1;
    }
    .hero-badges {
        display: flex;
        gap: 10px;
        margin-top: 16px;
        flex-wrap: wrap;
        position: relative;
        z-index: 1;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.78rem;
        color: #8b949e;
        font-weight: 500;
        transition: all 0.25s ease;
    }
    .hero-badge:hover {
        background: rgba(88,166,255,0.06);
        border-color: rgba(88,166,255,0.15);
        color: #c9d1d9;
    }
    .hero-badge img {
        height: 16px;
        width: 16px;
        filter: brightness(0.9);
    }

    /* ── Glass Card ── */
    .glass-card {
        background: rgba(13, 17, 23, 0.5);
        border: 1px solid rgba(48, 54, 61, 0.4);
        border-radius: 14px;
        padding: 18px 22px;
        margin-bottom: 10px;
        backdrop-filter: blur(12px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .glass-card:hover {
        border-color: rgba(88, 166, 255, 0.2);
        box-shadow: 0 4px 20px rgba(88, 166, 255, 0.04);
        transform: translateY(-1px);
    }

    /* ── Quick Action Cards ── */
    .action-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
        margin-bottom: 24px;
    }

    /* ── Command Box ── */
    .command-box {
        background: linear-gradient(135deg, rgba(13,17,23,0.8), rgba(10,15,26,0.9));
        border: 1px solid rgba(0,212,177,0.15);
        border-left: 3px solid #00D4B1;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 20px;
    }
    .command-label {
        color: #6e7681;
        font-weight: 700;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 6px;
    }
    .command-text {
        color: #e6edf3;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
    }

    /* ── Status pill ── */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .status-connected {
        background: rgba(63, 185, 80, 0.1);
        color: #3fb950;
        border: 1px solid rgba(63, 185, 80, 0.2);
    }
    .status-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: #3fb950;
        box-shadow: 0 0 6px rgba(63,185,80,0.5);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; box-shadow: 0 0 6px rgba(63,185,80,0.5); }
        50% { opacity: 0.4; box-shadow: 0 0 2px rgba(63,185,80,0.2); }
    }

    /* ── Section headers ── */
    .section-header {
        font-size: 1.05rem;
        font-weight: 700;
        color: #e6edf3;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .section-header .accent {
        width: 3px;
        height: 18px;
        background: linear-gradient(180deg, #58a6ff, #8b5cf6);
        border-radius: 2px;
    }

    /* ── Toolset cards in explorer ── */
    .toolset-card {
        background: rgba(13, 17, 23, 0.4);
        border: 1px solid rgba(48, 54, 61, 0.3);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 12px;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .toolset-card:hover {
        border-color: rgba(88, 166, 255, 0.15);
        background: rgba(88, 166, 255, 0.03);
        transform: translateX(4px);
    }
    .toolset-icon {
        font-size: 1.3rem;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(88,166,255,0.06);
        border-radius: 8px;
        flex-shrink: 0;
    }
    .toolset-info {
        flex: 1;
    }
    .toolset-name {
        font-weight: 600;
        color: #e6edf3;
        font-size: 0.9rem;
    }
    .toolset-desc {
        color: #6e7681;
        font-size: 0.8rem;
        margin-top: 2px;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(88,166,255,0.15); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(88,166,255,0.3); }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 Credentials")

    groq_key = st.text_input(
        "Groq API Key",
        value=os.getenv("GROQ_API_KEY", ""),
        type="password",
    )
    github_token = st.text_input(
        "GitHub Token",
        value=os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", ""),
        type="password"
    )
    scrapegraph_key = st.text_input(
        "ScrapeGraph API Key",
        value=os.getenv("SCRAPEGRAPH_API_KEY", ""),
        type="password"
    )

    if st.button("💾 Save Keys", use_container_width=True):
        st.session_state["GROQ_API_KEY"] = groq_key
        st.session_state["GITHUB_PERSONAL_ACCESS_TOKEN"] = github_token
        st.session_state["SCRAPEGRAPH_API_KEY"] = scrapegraph_key

        os.environ["GROQ_API_KEY"] = groq_key
        os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"] = github_token
        os.environ["SCRAPEGRAPH_API_KEY"] = scrapegraph_key

        st.success("Credentials updated!")
        time.sleep(1)
        st.rerun()

    if groq_key or github_token or scrapegraph_key:
        st.markdown("""
        <div class="status-pill status-connected" style="margin-top: 8px;">
            <div class="status-dot"></div>
            Credentials active
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Sidebar footer
    st.markdown("""
    <div style="color: #3d4450; font-size: 0.72rem; text-align: center; padding-top: 12px;">
        Powered by GitHub MCP · Groq · ScrapeGraphAI
    </div>
    """, unsafe_allow_html=True)


# ── Hero Header ──────────────────────────────────────────────────────
logo_img = f'<img src="{logo_src}" alt="Logo" class="hero-logo"/>' if logo_src else ''

st.markdown(
    f"""
    <div class="hero-container">
        <div class="hero-title-row">
            {logo_img}
            <div>
                <div class="hero-title">GitHub Intelligence</div>
            </div>
        </div>
        <div class="hero-subtitle">
            Autonomous AI-powered GitHub management — create repos, branches, issues & PRs with natural language.
        </div>
        <div class="hero-badges">
            <div class="hero-badge">
                <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" style="filter: invert(1);"/>
                GitHub MCP
            </div>
            <div class="hero-badge">⚡ Groq LLM</div>
            <div class="hero-badge">🌐 ScrapeGraphAI</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Tabs ─────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🤖 AI Agent",
    "GitHub Automation",
    "MCP Tools Explorer",
])


# ══════════════════════════════════════════════════════════════════════
# TAB 1 — AI Agent (Chat)
# ══════════════════════════════════════════════════════════════════════
with tab1:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

    # Input
    user_input = st.chat_input("Ask the agent anything... (e.g., 'analyze HarshS99/Github_Intelligence')")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # Command executed indicator
        st.markdown(
            f"""
            <div class="command-box">
                <div class="command-label">Command Executed</div>
                <div class="command-text">{user_input}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🧠 Agent is thinking..."):
                try:
                    response = run_action(user_input)
                except Exception as e:
                    response = f"❌ Error: {str(e)}"

            st.markdown(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})


# ══════════════════════════════════════════════════════════════════════
# TAB 2 — GitHub Automation Studio
# ══════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("""
    <div class="section-header">
        <div class="accent"></div>
        Quick Actions
    </div>
    """, unsafe_allow_html=True)

    qcols = st.columns(4)
    quick_actions = [
        ("📦 Create Repo", "Create a new public repository called 'my-new-project' with a README"),
        ("🌿 Create Branch", "Create a branch called 'feature/new-feature' in HarshS99/Github_Intelligence"),
        ("🐛 Create Issue", "Create an issue titled 'Bug: Fix login flow' in HarshS99/Github_Intelligence"),
        ("🔀 List PRs", "List all open pull requests in HarshS99/Github_Intelligence"),
    ]

    if "selected_action" not in st.session_state:
        st.session_state.selected_action = ""
    for col, (label, cmd) in zip(qcols, quick_actions):
        with col:
            if st.button(label, use_container_width=True):
                st.session_state.selected_action = cmd

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Custom command
    action_input = st.text_area(
        "Command",
        value=st.session_state.selected_action,
        placeholder="Type any GitHub command in natural language...\ne.g., 'Create a repo called ai-platform with description AI tools'",
        height=100,
        label_visibility="collapsed",
    )

    if st.button("Execute via MCP", use_container_width=True, key="exec_mcp"):
        if action_input:
            with st.spinner("⚡ Executing via GitHub MCP Server..."):
                try:
                    result = run_action(action_input)
                    st.success("✅ Action executed!")
                    st.markdown(result)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        else:
            st.warning("Enter a command first.")


# ══════════════════════════════════════════════════════════════════════
# TAB 3 — MCP Tools Explorer
# ══════════════════════════════════════════════════════════════════════
with tab3:
    if st.button("🔄 Discover MCP Tools", use_container_width=True, key="load_tools"):
        with st.spinner("Connecting to GitHub MCP Server..."):
            try:
                tools = list_mcp_tools()
                if tools and tools[0].get("name") != "error":
                    st.success(f"✅ Loaded **{len(tools)}** tools from GitHub MCP Server!")
                    for tool in tools:
                        with st.expander(f"🔹 `{tool['name']}`"):
                            st.markdown(f"_{tool['description']}_")
                else:
                    err_msg = tools[0].get('description', 'Unknown error') if tools else 'No tools returned by MCP server'
                    st.error(f"Failed to load tools: {err_msg}")
            except Exception as e:
                st.error(f"❌ Error: {e}")

    st.markdown("""
    <div class="section-header" style="margin-top: 20px;">
        <div class="accent"></div>
        Available Toolsets
    </div>
    """, unsafe_allow_html=True)

    toolset_data = [
        ("🗂️", "Repos", "Create, delete, list, search, fork repositories. Read files, manage settings."),
        ("🐛", "Issues", "Create, update, close, assign, label issues. Read comments, sub-issues."),
        ("🔀", "Pull Requests", "Open, review, merge, comment on PRs. Get diffs, reviews, files changed."),
        ("⚡", "Actions", "Monitor workflows, check runs, view logs, manage CI/CD pipelines."),
        ("🔒", "Code Security", "Code scanning alerts, Dependabot alerts, secret scanning."),
        ("🌿", "Git", "Create branches, tags, refs. Low-level Git operations."),
        ("👤", "Users", "Get user profiles, search users, check permissions."),
        ("💬", "Discussions", "Read and manage GitHub Discussions."),
        ("📝", "Gists", "Create, read, update gists."),
        ("🔔", "Notifications", "Read and manage GitHub notifications."),
        ("📊", "Projects", "Manage GitHub Projects (v2)."),
        ("🏷️", "Labels", "Create and manage labels."),
        ("⭐", "Stargazers", "List stargazers, check if starred."),
    ]
    for icon, name, desc in toolset_data:
        st.markdown(f"""
        <div class="toolset-card">
            <div class="toolset-icon">{icon}</div>
            <div class="toolset-info">
                <div class="toolset-name">{name}</div>
                <div class="toolset-desc">{desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
