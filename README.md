# 🤖 Coder Buddy — Autonomous AI Software Engineer

> **An autonomous coding agent that reads a Python repository, plans a fix, applies it, runs tests, and proposes a git commit — all powered by LangGraph + Groq.**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Coder Buddy Pipeline                            │
│                                                                     │
│  User Input                                                         │
│  (repo_path + instructions)                                         │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │ Planner │───▶│ File Reader │───▶│ Code Fixer  │                 │
│  │  (LLM)  │    │  (tools)    │    │   (LLM)     │                 │
│  └─────────┘    └─────────────┘    └──────┬──────┘                 │
│                                           │                         │
│                                           ▼                         │
│                                    ┌─────────────┐                 │
│                                    │ Test Runner │                 │
│                                    │  (pytest)   │                 │
│                                    └──────┬──────┘                 │
│                                           │                         │
│                            ┌──────────────┴──────────────┐         │
│                            ▼                             ▼          │
│                      Tests Pass?                  Retry < 3?        │
│                            │                             │          │
│                            ▼                             ▼          │
│                   ┌─────────────────┐          Back to Code Fixer   │
│                   │ Commit Proposer │                               │
│                   │     (LLM)       │                               │
│                   └────────┬────────┘                               │
│                            │                                         │
│                            ▼                                         │
│                    Structured Result                                 │
│              (plan + test output + commit msg)                       │
└─────────────────────────────────────────────────────────────────────┘

Tech Stack:
  LLM:          Groq API (llama-3.3-70b-versatile) — free tier
  Orchestration: LangGraph StateGraph
  Framework:    LangChain tools + prompts
  Backend:      FastAPI + Uvicorn
  Frontend:     Streamlit
  Testing:      pytest (subprocess)
  Git:          GitPython
```

---

## Features

- 🧠 **Intelligent Planning** — LLM generates a numbered action plan before touching any code
- 📖 **Full Repo Awareness** — reads all `.py` files automatically
- 🔧 **Autonomous Code Fixing** — applies LLM-generated fixes directly to disk
- 🔄 **Auto-Retry Loop** — retries up to 3× if tests still fail, learning from error output
- 📝 **Commit Proposal** — generates a Conventional Commit message + PR description + git diff
- 🔒 **Security Controls** — path whitelisting, rate limiting, test timeouts
- 🚀 **Production-Ready** — FastAPI backend, Streamlit UI, Dockerfile, Render deployment

---

## Prerequisites

- Python 3.11+
- Git installed
- A free [Groq API key](https://console.groq.com/keys)

---

## Quick Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd coder_buddy
```

### 2. Configure environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Groq API key
# GROQ_API_KEY=gsk_...
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the FastAPI backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start the Streamlit frontend (new terminal)

```bash
streamlit run frontend/streamlit_app.py
```

### 6. Open the UI

Navigate to **http://localhost:8501**

---

## First Test Run

Use the built-in broken calculator demo:

1. **Repository Path**: Enter the absolute path to `sample_repo/`  
   e.g. `C:/Users/acer/OneDrive/Desktop/AI-Assistant/coder_buddy/sample_repo`

2. **Instructions**: `Fix all bugs in the calculator module`

3. Click **🚀 Analyze & Fix**

Within ~30–60 seconds you'll see:
- ✅ A 3–5 step action plan
- ✅ pytest output showing all tests pass
- ✅ A ready-to-use git commit message
- ✅ The exact diff of what was changed

---

## API Usage

### Health check

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "ok",
  "model": "llama-3.3-70b-versatile",
  "max_retries": 3,
  "version": "1.0.0"
}
```

### Analyze a repository

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "C:/Users/acer/OneDrive/Desktop/AI-Assistant/coder_buddy/sample_repo",
    "instructions": "Fix all bugs in the calculator module"
  }'
```

```json
{
  "plan": ["Step 1: Read calculator.py ...", "Step 2: ..."],
  "test_result": {
    "passed": true,
    "output": "========= 12 passed in 0.5s ========="
  },
  "commit_proposal": {
    "message": "fix(calculator): resolve division, sqrt import, and factorial bugs",
    "diff": "--- a/calculator.py\n+++ b/calculator.py\n...",
    "pr_body": "## Summary\n\nFixed 3 bugs..."
  },
  "iterations_used": 1,
  "success": true,
  "error": null
}
```

---

## Getting a Free Groq API Key

1. Visit [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Go to **API Keys** → **Create API Key**
4. Copy the key and paste it into your `.env` file as `GROQ_API_KEY=gsk_...`

**Free tier limits**: ~14,400 tokens/minute on llama-3.3-70b-versatile (plenty for this agent)

---

## Deployment to Render (Free Tier)

### Step 1: Push to GitHub

```bash
git init && git add . && git commit -m "feat: initial Coder Buddy project"
git remote add origin https://github.com/<you>/coder-buddy.git
git push -u origin main
```

### Step 2: Create a new Render Web Service

1. Log in at [render.com](https://render.com)
2. Click **New** → **Web Service**
3. Connect your GitHub repository
4. Render will auto-detect `render.yaml`

### Step 3: Set the secret environment variable

In the Render dashboard → **Environment**:
- Key: `GROQ_API_KEY`
- Value: `gsk_...your key...`

### Step 4: Deploy

Click **Deploy**. Your API will be live at `https://coder-buddy-api.onrender.com`.

> **Note**: Free tier services spin down after 15 minutes of inactivity. The first request after sleep takes ~30s to wake up.

---

## Project Structure

```
coder_buddy/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI app entrypoint
│   ├── config.py             # Settings via pydantic-settings
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py          # LangGraph StateGraph
│   │   ├── nodes.py          # 5 async node functions
│   │   ├── state.py          # AgentState TypedDict
│   │   └── tools.py          # LangChain tools
│   └── schemas/
│       ├── __init__.py
│       └── models.py         # Pydantic models
├── frontend/
│   └── streamlit_app.py      # Streamlit UI
├── sample_repo/
│   ├── calculator.py         # Intentionally buggy demo
│   └── test_calculator.py    # pytest tests
├── .env.example
├── requirements.txt
├── Dockerfile
├── render.yaml
└── README.md
```

---

## Security Notes

- **Path validation**: `repo_path` must be an existing directory
- **Whitelist**: Set `ALLOWED_REPO_PATHS` to restrict which directories can be analysed
- **Rate limiting**: 10 requests/minute per IP (configurable via `RATE_LIMIT`)
- **Test timeout**: pytest is killed after `TEST_TIMEOUT` seconds (default 60)
- **No shell injection**: all subprocess calls use list arguments, never `shell=True`

---

## Screenshots

*[Add screenshots here after running the agent]*

---

## License

MIT — feel free to use, modify, and deploy.


cd C:\Users\acer\OneDrive\Desktop\AI-Assistant\coder_buddy
py -3.13 -m uvicorn app.main:app --reload --port 8000

cd C:\Users\acer\OneDrive\Desktop\AI-Assistant\coder_buddy
py -3.13 -m streamlit run frontend/streamlit_app.py