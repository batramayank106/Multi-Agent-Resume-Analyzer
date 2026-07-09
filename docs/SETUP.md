# Setup & Configuration Guide

A walkthrough for getting CV Chacha running on your machine — no GPU, no expensive API keys, just a terminal and a little patience.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| **Python** | 3.14+ | 3.10+ may work but 3.14 is the target runtime |
| **pip** | Latest | Bundled with modern Python |
| **Tesseract OCR** | Optional | Needed only if you plan to upload image-based resumes (PNG, JPG) |

### Tesseract OCR (Optional)

CV Chacha can extract text from image-based resumes via OCR. If you want this feature:

**Windows:**
```bash
# Download from https://github.com/UB-Mannheim/tesseract/wiki
# Install to C:\Program Files\Tesseract-OCR\
# Add to PATH or set TESSERACT_CMD in .env
```

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt install tesseract-ocr
```

Without Tesseract, everything else works — you just won't be able to upload image-based resumes.

---

## Groq Cloud Setup (Primary Provider — Recommended)

**Groq** is the fastest free LLM provider — 30 RPM, ~14K requests/day, no credit card required. CV Chacha tries Groq first before any other provider.

### Getting a Groq API Key

1. Go to **https://console.groq.com/keys**
2. Sign up with Google/GitHub/email (no credit card)
3. Click **"Create API Key"** — copy the key (starts with `gsk_...`)

### Configure in .env

```env
GROQ_API_KEY=gsk_your_key_here
GROQ_DEFAULT_MODEL=llama-3.3-70b-versatile
```

That's it. No installation needed — Groq is cloud-based and works immediately.

### How It Fits

```
Your request → Groq Cloud (tried first)
             → Hugging Face API (fallback 1)
             → Ollama local (fallback 2)
             → Graceful degradation
```

---

## Local LLM Setup (Ollama with GPU Acceleration)

The Hugging Face Inference API free tier gives ~30K credits/month. Once depleted, you get a **402 Payment Required** error. CV Chacha also supports local inference via **Ollama** with optional GPU acceleration as a secondary fallback.

Currently (`PREFER_OLLAMA=false`), Ollama serves as a last resort fallback after Hugging Face API. Set `PREFER_OLLAMA=true` to promote Ollama to the first fallback.

### Installing Ollama

| Platform | Command |
|---|---|
| Windows | `winget install Ollama.Ollama` or download from [ollama.com](https://ollama.com) |
| macOS | `brew install ollama` |
| Linux | `curl -fsSL https://ollama.ai/install.sh \| sh` |

### Downloading Models

Pick models based on your hardware:

```bash
# Fastest, most CPU-friendly (~400MB) — good for 2GB RAM systems
ollama pull qwen2.5:0.5b

# Better quality, still lightweight (~900MB)
ollama pull qwen2.5:1.5b

# Best quality on GPU with 2GB+ VRAM (~1.9GB)
ollama pull qwen2.5:3b
```

We recommend `qwen2.5:3b` — good balance of quality, speed, and fits 2GB VRAM with partial GPU offloading.

### Starting Ollama with GPU Support

Ollama runs as a background service on port 11434. To enable GPU acceleration on NVIDIA GPUs (e.g., MX150, GTX, RTX series):

```bash
# Set these environment variables BEFORE starting Ollama
set CUDA_VISIBLE_DEVICES=0
set OLLAMA_LLM_LIBRARY=cuda_v12

# Start the Ollama service
ollama serve
```

On Windows, set these as **User environment variables** (Start Menu → "Edit environment variables") to make them permanent:
- `CUDA_VISIBLE_DEVICES` = `0`
- `OLLAMA_LLM_LIBRARY` = `cuda_v12`

**Note:** The CUDA v12 backend is required for older GPUs (compute cap 5.0–7.5). Newer GPUs (RTX 30/40 series) work with CUDA v13 (default).

### Configuring CV Chacha — by Mayank Batra to Use Ollama

Add these to your `.env` file:

```env
# Set to your Ollama server URL (default: http://localhost:11434)
OLLAMA_BASE_URL=http://localhost:11434

# The Ollama model to use
OLLAMA_MODEL=deepseek-r1:1.5b

# Still keep your HF key — system tries HF first, falls back to Ollama on 402
HF_API_KEY=hf_...
```

### How Failover Works

1. Pipeline tries **Groq** first (if `GROQ_API_KEY` is set)
2. If Groq fails → tries **Hugging Face Inference API**
3. If HF fails → tries **Ollama** (if `PREFER_OLLAMA=false`, only as last resort)
4. If all LLMs fail → agent uses graceful fallback (shows "LLM unavailable" note)

> **Note:** With `PREFER_OLLAMA=false`, Ollama is the last resort after HF. Set `PREFER_OLLAMA=true` to make Ollama the first fallback instead.
5. Remove `GROQ_API_KEY` from `.env` for pure offline Ollama-only mode

### GPU Performance

Partial GPU offloading provides significant speedup on low-VRAM GPUs:

| Metric | CPU Only | GPU (20 of 36 layers) | Improvement |
|--------|----------|----------------------|-------------|
| Prompt evaluation | 17.75 t/s | **58.8 t/s** | **3.3x** |
| Text generation | 2.91 t/s | **6.5 t/s** | **2.2x** |
| Cached response (2nd call) | ~9.5s | **~2.3s** | **4x faster** |

### GPU Configuration for 2GB VRAM (MX150, GTX 1050, etc.)

These GPUs have limited VRAM — the full model (36 layers) won't fit. Use partial offloading:

1. Set `OLLAMA_GPU_LAYERS=20` in `.env` (not 999 — that causes OOM)
2. Use the CUDA v12 backend: set `OLLAMA_LLM_LIBRARY=cuda_v12`
3. Kill orphaned `llama-server.exe` processes if VRAM gets stuck:
   ```bash
   taskkill /F /IM llama-server.exe
   ```

For GPUs with 4GB+ VRAM (RTX 3050+), you can use `OLLAMA_GPU_LAYERS=999` to offload all layers.

### Performance Notes

- First inference is slow (~10-30s) as the model loads from disk to GPU memory
- Subsequent calls are faster (~2-5s) due to caching
- After restarting Ollama, the first call reloads the model

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/batramayank106/Multi-Agent-Resume-Analyzer.git
cd Multi-Agent-Resume-Analyzer
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

| Platform | Command |
|---|---|
| Windows (PowerShell) | `venv\Scripts\Activate.ps1` |
| Windows (CMD) | `venv\Scripts\activate.bat` |
| macOS / Linux | `source venv/bin/activate` |

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs ~30 packages including FastAPI, Streamlit, LangGraph, ChromaDB, sentence-transformers, Plotly, and more. Expect 2-5 minutes depending on your internet speed — the `sentence-transformers` and `cross-encoder` packages pull in PyTorch (CPU) which is the heaviest dependency.

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` in your editor. Here is what each variable does:

| Variable | Required | Default | Purpose |
|---|---|---|---|---|---|
| `GROQ_API_KEY` | Yes | — | Primary LLM provider (fast, free, no CC). Get one at [console.groq.com/keys](https://console.groq.com/keys) |
| `GROQ_DEFAULT_MODEL` | No | `llama-3.3-70b-versatile` | Model to use via Groq |
| `HF_API_KEY` | No | — | Hugging Face Inference API token (fallback). Get at [hf.co/settings/tokens](https://huggingface.co/settings/tokens) |
| `HF_DEFAULT_MODEL` | No | `Qwen/Qwen2.5-7B-Instruct` | Default model for HF fallback |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama server URL for local inference |
| `OLLAMA_MODEL` | No | `qwen2.5:3b` | Local model name when using Ollama fallback |
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./cv_chacha.db` | SQLite database path |
| `CHROMA_PERSIST_DIR` | No | `./chroma_db` | ChromaDB vector store directory |
| `EMBEDDING_MODEL` | No | `BAAI/bge-small-en-v1.5` | 384-dim CPU-friendly embedding model |
| `EMBEDDING_FALLBACK_MODEL` | No | `all-MiniLM-L6-v2` | Fallback if primary model fails to load |
| `TESSERACT_CMD` | No | — | Path to Tesseract executable (only needed for image OCR) |
| `JWT_SECRET` | Yes | — | Secret key for JWT token signing (generate with `openssl rand -hex 32`) |
| `SUPER_ADMIN_EMAIL` | Yes | — | Email for the auto-created super admin account |
| `SUPER_ADMIN_PASSWORD` | Yes | — | Password for the super admin account (must meet password policy) |
| `ENCRYPTION_KEY` | Yes | — | Fernet encryption key for Resume Library (generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`) |
| `DEBUG` | No | `true` | Enable debug logging |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |

**Important:** The ATS Scoring agent is fully rule-based and works without any API key. All other agents use **Groq** first, then fall back to Ollama → HF API. They degrade gracefully if all providers are unavailable.

---

## Running the Application

Start the **backend** and **frontend** in two separate terminals.

### Terminal 1 — Backend

```bash
python run.py --backend
```

This starts FastAPI with Uvicorn on `http://localhost:8000`. The `--reload` flag is active in debug mode, so code changes trigger automatic restarts.

To start manually:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify the backend is running:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status": "ok", "app": "CV Chacha", "version": "1.0.0"}
```

### Terminal 2 — Frontend

```bash
python run.py --frontend
```

This starts Streamlit on `http://localhost:8501`. Open this URL in your browser.

To start manually:

```bash
streamlit run frontend/app.py --server.port 8501
```

### Run Both Together (Single Terminal)

```bash
python run.py --all
```

This spawns both services using a `ThreadPoolExecutor`. Output will interleave in the same terminal — useful for quick demos.

---

## Verifying the Installation

1. Open `http://localhost:8501` in your browser
2. You should see the **Login / Sign Up** page — register a new account or use super admin credentials to sign in
3. After login, the sidebar shows your email and role badge
4. Navigate to **Upload Resume** and upload a PDF or paste resume text
5. Navigate to **Upload JD** and paste a job description
6. Analysis starts automatically once both resume text and a JD are present — results appear incrementally as each agent completes. You can also click **Run Analysis** on the ATS page.
7. After analysis, check **Vault** to see your saved session with all scores
8. Navigate to **Resume Library** to upload and manage encrypted resume files
9. If logged in as super admin, the **Admin** page shows audit logs and user management

If everything works, the 12-agent pipeline will execute and you will see results across the full platform.

---

## Troubleshooting

### "GROQ_API_KEY not configured" errors

The `.env` file is missing or the Groq key is not set. Copy `.env.example` to `.env` and add your Groq API key. Get one free at [console.groq.com/keys](https://console.groq.com/keys) — no credit card needed.

### Login fails with "Account locked"

After 5 failed login attempts, the account is locked for 15 minutes. Wait for the lock to expire or contact a super admin to unlock the account via the Admin dashboard.

### JWT token errors

If you see 401 errors, clear your browser session (close tab) and log in again. The tokens are stored in `st.session_state` and are invalidated on logout.

### "No models available" on LLM routes

The Groq API key is missing or all providers failed. Ensure `GROQ_API_KEY` is set in `.env`. The system will also try Ollama and HF as fallbacks. The ATS agent is rule-based and works without any API key.

### Resume Library returns 500 on upload

The `ENCRYPTION_KEY` in `.env` must be a valid Fernet key. Generate one with:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
This key must remain consistent across restarts — changing it will make previously encrypted files unreadable.

### Backend won't start — port 8000 in use

```bash
# Find the process using port 8000
netstat -ano | findstr :8000
# Kill it (replace PID with the actual process ID)
taskkill /PID <PID> /F
```

### "ModuleNotFoundError" for sentence-transformers or cross-encoder

Some sub-dependencies may not install cleanly on Windows. Try:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### TesseractNotFoundError

You uploaded an image resume but Tesseract is not installed. Either:
- Install Tesseract and set `TESSERACT_CMD` in `.env`
- Use a PDF or plain-text resume instead

### ChromaDB persistence errors

Delete the `chroma_db/` directory and restart:

```bash
rm -rf chroma_db/
# Then restart the backend
```

The seed data will be recreated on startup.

### Analysis runs but all LLM results show errors

Your Groq API key may be invalid or rate-limited. The system automatically falls back to Ollama → Hugging Face API. Check the backend logs for specific error details. Verify `GROQ_API_KEY` is correct in `.env`.

### Streamlit shows blank page or CSS issues

Clear the browser cache and hard-reload (Ctrl+Shift+R on Windows/Linux, Cmd+Shift+R on macOS). Some older browsers may not support CSS custom properties used in the theme.

---

## What's Next?

- Read [API.md](API.md) for endpoint documentation (auth, vault, comparison, library, admin)
- Read [AGENTS.md](AGENTS.md) to understand the 12-agent pipeline
- Read [INTERVIEW.md](INTERVIEW.md) for the Interview Prep module
- Explore the **Vault**, **Comparison**, and **Resume Library** pages in the frontend
- If you're a super admin, check the **Admin** page for audit logs and user management
