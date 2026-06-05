"""
Coder Buddy v2 — Streamlit Frontend
Full-featured UI with GitHub PR, Slack/Discord, and multi-repo batch support.
"""
import streamlit as st
import httpx
import json

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Coder Buddy — AI Software Engineer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = "http://localhost:8000"
TIMEOUT  = 300

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg0: #0d1117; --bg1: #161b22; --bg2: #1c2128; --bg3: #21262d;
    --blue: #58a6ff; --green: #3fb950; --red: #f85149;
    --purple: #d2a8ff; --yellow: #e3b341; --orange: #f78166;
    --text: #e6edf3; --muted: #7d8590; --border: #30363d;
}
html, body, [class*="css"] { font-family:'Inter',sans-serif!important; background:var(--bg0)!important; color:var(--text)!important; }
.main .block-container { padding:1.5rem 2.5rem; max-width:1400px; }

/* Hero */
.hero { background:linear-gradient(135deg,#1c2541,#0d1117 50%,#1a1f35);
  border:1px solid var(--border); border-radius:16px; padding:2rem 2.5rem; margin-bottom:1.5rem; position:relative; overflow:hidden; }
.hero::before { content:''; position:absolute; inset:0;
  background:radial-gradient(ellipse at 20% 50%,rgba(88,166,255,.07),transparent 60%); pointer-events:none; }
.hero-title { font-size:2.2rem; font-weight:700;
  background:linear-gradient(90deg,#58a6ff,#d2a8ff); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0 0 .3rem 0; }
.hero-sub { color:var(--muted); font-size:1rem; margin:0 0 .8rem 0; }
.badge { display:inline-flex; align-items:center; gap:5px;
  border-radius:20px; font-size:.72rem; font-weight:600; padding:3px 10px; margin-right:6px; }
.badge-blue  { background:rgba(88,166,255,.12); border:1px solid rgba(88,166,255,.3); color:var(--blue); }
.badge-green { background:rgba(63,185,80,.12);  border:1px solid rgba(63,185,80,.3);  color:var(--green); }
.badge-purple{ background:rgba(210,168,255,.12);border:1px solid rgba(210,168,255,.3);color:var(--purple);}

/* Cards */
.card { background:var(--bg2); border:1px solid var(--border); border-radius:10px; padding:1.2rem; margin-bottom:1rem; transition:border-color .2s; }
.card:hover { border-color:#58a6ff44; }
.section-label { font-size:.75rem; font-weight:600; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); margin-bottom:.6rem; }

/* Inputs */
.stTextInput>div>div>input,
.stTextArea>div>div>textarea {
  background:var(--bg1)!important; border:1px solid var(--border)!important;
  border-radius:8px!important; color:var(--text)!important; font-size:.88rem!important; }
.stTextInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus { border-color:var(--blue)!important; box-shadow:0 0 18px rgba(88,166,255,.12)!important; }

/* Toggle / Checkbox */
.stCheckbox > label { color:var(--text)!important; font-size:.88rem!important; }

/* Buttons */
.stButton>button {
  background:linear-gradient(135deg,#1f6feb,#388bfd)!important; color:#fff!important;
  border:none!important; border-radius:8px!important; font-weight:600!important;
  padding:.6rem 1.6rem!important; width:100%!important;
  box-shadow:0 4px 14px rgba(31,111,235,.35)!important; transition:all .2s!important; }
.stButton>button:hover { transform:translateY(-1px)!important; box-shadow:0 6px 20px rgba(31,111,235,.5)!important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background:var(--bg1)!important; border-radius:10px!important;
  padding:4px!important; gap:2px!important; border:1px solid var(--border)!important; }
.stTabs [data-baseweb="tab"] {
  background:transparent!important; color:var(--muted)!important;
  border-radius:7px!important; font-weight:500!important; padding:8px 18px!important; border:none!important; }
.stTabs [aria-selected="true"] {
  background:var(--bg2)!important; color:var(--text)!important; border:1px solid var(--border)!important; }
.stTabs [data-baseweb="tab-panel"] { padding:1.2rem 0!important; }

/* Status badges */
.pass { display:inline-flex;align-items:center;gap:6px;background:rgba(63,185,80,.12);
  border:1px solid rgba(63,185,80,.3);color:var(--green);padding:6px 14px;border-radius:20px;font-weight:600;font-size:.83rem; }
.fail { display:inline-flex;align-items:center;gap:6px;background:rgba(248,81,73,.12);
  border:1px solid rgba(248,81,73,.3);color:var(--red);padding:6px 14px;border-radius:20px;font-weight:600;font-size:.83rem; }

/* Plan steps */
.step { display:flex;align-items:flex-start;gap:10px;padding:10px 14px;
  background:var(--bg1);border:1px solid var(--border);border-radius:8px;margin-bottom:6px; }
.step-n { background:linear-gradient(135deg,#1f6feb,#388bfd);color:#fff;border-radius:50%;
  width:24px;height:24px;display:flex;align-items:center;justify-content:center;font-size:.7rem;font-weight:700;flex-shrink:0; }
.step-t { color:var(--text);font-size:.88rem;line-height:1.5;padding-top:2px; }

/* Commit msg */
.commit-box { font-family:'JetBrains Mono',monospace;background:var(--bg1);
  border:1px solid var(--blue);border-radius:8px;padding:12px 16px;
  color:var(--blue);font-size:.85rem;font-weight:500;margin-bottom:1rem; }

/* PR link */
.pr-link { display:inline-flex;align-items:center;gap:8px;
  background:rgba(63,185,80,.1);border:1px solid rgba(63,185,80,.3);
  color:var(--green);padding:8px 16px;border-radius:8px;text-decoration:none;font-weight:600; }

/* Sidebar */
section[data-testid="stSidebar"] { background:var(--bg1)!important; border-right:1px solid var(--border)!important; }

/* Metrics */
[data-testid="metric-container"] { background:var(--bg2)!important; border:1px solid var(--border)!important; border-radius:10px!important; }

/* Code */
.stCode,pre { background:var(--bg1)!important; border:1px solid var(--border)!important;
  border-radius:8px!important; font-family:'JetBrains Mono',monospace!important; font-size:.78rem!important; }

hr { border-color:var(--border)!important; margin:1.2rem 0!important; }

/* Batch table */
.batch-row { display:flex;align-items:center;gap:12px;padding:10px 14px;
  background:var(--bg2);border:1px solid var(--border);border-radius:8px;margin-bottom:6px; }
.batch-row:hover { border-color:#58a6ff44; }

/* Notification indicator */
.notif-ok  { color:var(--green);font-size:.8rem;font-weight:600; }
.notif-err { color:var(--red);  font-size:.8rem;font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "result"       not in st.session_state: st.session_state.result       = None
if "batch_result" not in st.session_state: st.session_state.batch_result = None

# ── Health check ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def get_health():
    try:
        r = httpx.get(f"{API_BASE}/health", timeout=5)
        return (r.json(), None) if r.status_code == 200 else (None, f"HTTP {r.status_code}")
    except httpx.ConnectError:
        return None, "Cannot connect to API server"
    except Exception as e:
        return None, str(e)

health, health_err = get_health()

# ── Hero ──────────────────────────────────────────────────────────────────────
gh_badge    = '<span class="badge badge-green">🐙 GitHub PR</span>'   if (health and health.get("github_enabled"))  else '<span class="badge badge-blue">🐙 GitHub</span>'
slack_badge = '<span class="badge badge-purple">💬 Slack</span>'       if (health and health.get("slack_enabled"))   else ''
disc_badge  = '<span class="badge badge-purple">🎮 Discord</span>'     if (health and health.get("discord_enabled")) else ''

st.markdown(f"""
<div class="hero">
  <p class="hero-title">🤖 Coder Buddy</p>
  <p class="hero-sub">Autonomous AI Software Engineer · LangGraph × Groq × LLaMA 3.3 70B</p>
  <span class="badge badge-blue">⚡ Groq Free</span>
  <span class="badge badge-green">🔁 Auto-Retry</span>
  {gh_badge}{slack_badge}{disc_badge}
</div>
""", unsafe_allow_html=True)

if health_err:
    st.error(f"⚠️ **API offline** — {health_err}  \nStart with: `py -3.13 -m uvicorn app.main:app --reload`")
else:
    integrations = []
    if health.get("github_enabled"):  integrations.append("GitHub PR ✅")
    if health.get("slack_enabled"):   integrations.append("Slack ✅")
    if health.get("discord_enabled"): integrations.append("Discord ✅")
    st.success(f"✅ API online · `{health.get('model')}` · Integrations: {', '.join(integrations) or 'none configured'}")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Options")

    mode = st.radio("Mode", ["Single Repo", "Batch (Multi-Repo)"], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("### 🔌 Integrations")

    create_pr     = st.toggle("🐙 Create GitHub PR",    value=False, help="Requires GITHUB_TOKEN + GITHUB_REPO in .env")
    notify_slack  = st.toggle("💬 Notify Slack",         value=False, help="Requires SLACK_WEBHOOK_URL in .env")
    notify_discord= st.toggle("🎮 Notify Discord",       value=False, help="Requires DISCORD_WEBHOOK_URL in .env")

    if create_pr and health and not health.get("github_enabled"):
        st.warning("⚠️ GITHUB_TOKEN / GITHUB_REPO not set in .env")
    if notify_slack and health and not health.get("slack_enabled"):
        st.warning("⚠️ SLACK_WEBHOOK_URL not set in .env")
    if notify_discord and health and not health.get("discord_enabled"):
        st.warning("⚠️ DISCORD_WEBHOOK_URL not set in .env")

    st.markdown("---")
    st.markdown("### 💡 Quick Demo")
    st.markdown("""
<div class="card" style="font-size:.8rem">
Paste this as repo path:<br/>
<code style="color:#58a6ff">…/coder_buddy/sample_repo</code><br/><br/>
Instructions:<br/>
<em>"Fix all bugs in the calculator module"</em>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔄 Pipeline")
    for icon, name in [("🧠","Planner"),("📖","File Reader"),("🔧","Code Fixer"),("🧪","Test Runner"),("📝","Commit Proposer")]:
        st.markdown(f"**{icon} {name}**", help=f"{name} node in the LangGraph pipeline")


# ─────────────────────────────────────────────────────────────────────────────
# SINGLE REPO MODE
# ─────────────────────────────────────────────────────────────────────────────
if mode == "Single Repo":
    col_l, col_r = st.columns([3, 2], gap="large")

    with col_l:
        st.markdown('<div class="section-label">📁 Repository</div>', unsafe_allow_html=True)
        repo_path    = st.text_input("Repo Path", placeholder="C:/Users/.../my_project", label_visibility="collapsed")
        instructions = st.text_area("Instructions", placeholder="Describe what needs fixing…", height=120, label_visibility="collapsed")
        clicked = st.button("🚀 Analyze & Fix")

    with col_r:
        st.markdown('<div class="section-label">🔌 Active Integrations</div>', unsafe_allow_html=True)
        flags = []
        if create_pr:      flags.append("🐙 GitHub PR will be created")
        if notify_slack:   flags.append("💬 Slack notification enabled")
        if notify_discord: flags.append("🎮 Discord notification enabled")
        if flags:
            for f in flags:
                st.markdown(f"- {f}")
        else:
            st.markdown("*No integrations active — toggle in sidebar*")

    if clicked:
        if not repo_path.strip() or not instructions.strip():
            st.error("❌ Please fill in both fields.")
        else:
            with st.spinner("🤖 Agent working… (30–90 sec)"):
                try:
                    resp = httpx.post(
                        f"{API_BASE}/analyze",
                        json={
                            "repo_path": repo_path.strip(),
                            "instructions": instructions.strip(),
                            "create_github_pr": create_pr,
                            "notify_slack": notify_slack,
                            "notify_discord": notify_discord,
                        },
                        timeout=TIMEOUT,
                    )
                    if resp.status_code == 200:
                        st.session_state.result = resp.json()
                    else:
                        st.error(f"❌ API error {resp.status_code}: {resp.json().get('detail', resp.text)[:300]}")
                        st.session_state.result = None
                except httpx.TimeoutException:
                    st.error("⏱️ Timed out — the agent is still running.")
                except httpx.ConnectError:
                    st.error("🔌 Cannot connect to API.")
                except Exception as e:
                    st.error(f"❌ {e}")

    result = st.session_state.result
    if result:
        st.markdown("<hr/>", unsafe_allow_html=True)

        # Metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Status",     "✅ Passed" if result.get("success") else "❌ Failed")
        m2.metric("Iterations", result.get("iterations_used", 0))
        m3.metric("Plan Steps", len(result.get("plan", [])))
        m4.metric("GitHub PR",  "✅ Created" if result.get("github_pr", {}).get("created") else "—")
        m5.metric("Notified",   "✅ Sent" if (result.get("notifications",{}).get("slack_sent") or result.get("notifications",{}).get("discord_sent")) else "—")

        st.markdown("<hr/>", unsafe_allow_html=True)

        tab_plan, tab_tests, tab_commit, tab_pr, tab_notif = st.tabs(
            ["📋 Plan", "🧪 Tests", "📝 Commit", "🐙 GitHub PR", "🔔 Notifications"]
        )

        with tab_plan:
            st.markdown("#### Agent's Action Plan")
            for i, step in enumerate(result.get("plan", []), 1):
                st.markdown(f'<div class="step"><div class="step-n">{i}</div><div class="step-t">{step}</div></div>', unsafe_allow_html=True)

        with tab_tests:
            tr = result.get("test_result", {})
            badge = '<div class="pass">✅ &nbsp;All Tests Passed</div>' if tr.get("passed") else '<div class="fail">❌ &nbsp;Tests Failed</div>'
            st.markdown(badge, unsafe_allow_html=True)
            st.code(tr.get("output", "No output"), language="text")

        with tab_commit:
            cp = result.get("commit_proposal", {})
            if cp.get("message"):
                st.markdown("#### Commit Message")
                st.markdown(f'<div class="commit-box">$ git commit -m "{cp["message"]}"</div>', unsafe_allow_html=True)
                if cp.get("pr_body"):
                    st.markdown("#### PR Description")
                    st.markdown(cp["pr_body"])
                if cp.get("diff"):
                    st.markdown("#### Git Diff")
                    st.code(cp["diff"], language="diff")
            else:
                st.info("No commit proposal generated (tests may not have passed).")

        with tab_pr:
            gh = result.get("github_pr", {})
            if gh.get("created"):
                st.markdown("#### ✅ Pull Request Created!")
                st.markdown(f'<a class="pr-link" href="{gh["pr_url"]}" target="_blank">🔗 View PR #{gh["pr_number"]} on GitHub</a>', unsafe_allow_html=True)
                st.markdown(f"\n\n**Branch:** `{gh['branch_name']}`")
            elif gh.get("error"):
                st.error(f"❌ PR creation failed: {gh['error']}")
            else:
                if create_pr:
                    st.warning("⚠️ PR was requested but not created — check the error tab or .env config.")
                else:
                    st.info("GitHub PR not requested. Toggle **Create GitHub PR** in the sidebar.")

        with tab_notif:
            notif = result.get("notifications", {})
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**💬 Slack**")
                if notif.get("slack_sent"):
                    st.markdown('<span class="notif-ok">✅ Sent successfully</span>', unsafe_allow_html=True)
                elif notif.get("slack_error"):
                    st.markdown(f'<span class="notif-err">❌ {notif["slack_error"]}</span>', unsafe_allow_html=True)
                else:
                    st.markdown("*Not requested*")
            with c2:
                st.markdown("**🎮 Discord**")
                if notif.get("discord_sent"):
                    st.markdown('<span class="notif-ok">✅ Sent successfully</span>', unsafe_allow_html=True)
                elif notif.get("discord_error"):
                    st.markdown(f'<span class="notif-err">❌ {notif["discord_error"]}</span>', unsafe_allow_html=True)
                else:
                    st.markdown("*Not requested*")

        if result.get("error"):
            with st.expander("⚠️ Partial Error"):
                st.warning(result["error"])


# ─────────────────────────────────────────────────────────────────────────────
# BATCH MODE
# ─────────────────────────────────────────────────────────────────────────────
else:
    st.markdown('<div class="section-label">📦 Batch Analysis — up to 5 Repositories</div>', unsafe_allow_html=True)

    num_repos = st.slider("Number of repositories", min_value=2, max_value=5, value=2)

    repos = []
    for i in range(num_repos):
        with st.expander(f"Repository {i+1}", expanded=(i == 0)):
            rp = st.text_input(f"Path {i+1}", key=f"rp_{i}", placeholder="C:/absolute/path/to/repo")
            ri = st.text_area(f"Instructions {i+1}", key=f"ri_{i}", placeholder="What to fix…", height=80)
            repos.append({"repo_path": rp, "instructions": ri})

    if st.button("🚀 Analyze All Repos", use_container_width=True):
        filled = [r for r in repos if r["repo_path"].strip() and r["instructions"].strip()]
        if not filled:
            st.error("❌ Fill in at least one repo + instructions pair.")
        else:
            with st.spinner(f"🤖 Running agent on {len(filled)} repos concurrently…"):
                try:
                    resp = httpx.post(
                        f"{API_BASE}/analyze/batch",
                        json={
                            "repos": filled,
                            "create_github_pr": create_pr,
                            "notify_slack": notify_slack,
                            "notify_discord": notify_discord,
                        },
                        timeout=TIMEOUT,
                    )
                    if resp.status_code == 200:
                        st.session_state.batch_result = resp.json()
                    else:
                        st.error(f"❌ API error {resp.status_code}: {resp.json().get('detail', resp.text)[:300]}")
                except httpx.TimeoutException:
                    st.error("⏱️ Timed out.")
                except httpx.ConnectError:
                    st.error("🔌 Cannot connect to API.")
                except Exception as e:
                    st.error(f"❌ {e}")

    br = st.session_state.batch_result
    if br:
        st.markdown("<hr/>", unsafe_allow_html=True)
        bm1, bm2, bm3 = st.columns(3)
        bm1.metric("Total Repos", br.get("total", 0))
        bm2.metric("✅ Passed",   br.get("passed", 0))
        bm3.metric("❌ Failed",   br.get("failed", 0))

        st.markdown("<hr/>", unsafe_allow_html=True)
        st.markdown("#### Results per Repository")
        for item in br.get("results", []):
            success = item.get("success", False)
            icon = "✅" if success else "❌"
            with st.expander(f"{icon}  {item.get('repo_path', 'Unknown')}"):
                if item.get("error"):
                    st.error(item["error"])
                else:
                    cols = st.columns([2,1,1])
                    cols[0].markdown(f"**Commit:** `{item.get('commit_message','—')[:60]}`")
                    cols[1].markdown(f"**Iterations:** {item.get('iterations_used',0)}")
                    cols[2].markdown(f"**PR:** {'✅ ' + item['github_pr']['pr_url'] if item.get('github_pr',{}).get('created') else '—'}")
                    if item.get("plan"):
                        st.markdown("**Plan:**")
                        for j, s in enumerate(item["plan"], 1):
                            st.markdown(f"&nbsp;&nbsp;{j}. {s}")
                    st.markdown("**Test Output:**")
                    st.code(item.get("test_output","")[-1000:], language="text")
