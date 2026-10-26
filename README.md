# DetectiveLens

Gamified misinformation-literacy web app for children (LMU PSIS project).  
The FastAPI backend serves both the API and the frontend on the same port.

## Prerequisites

- **Python 3.11+**
- **pip** (Python package installer)
- **Node.js 20+** and **npm** (needed for repo scripts in `package.json`)

## Quick Start

1. Prepare Python environment for backend dependencies.

**Option A — IDE already has an active project virtual environment**

**Windows / macOS / Linux:**
```bash
cd backend
pip install -r requirements.txt
cd ..
```

**Option B — no virtual environment yet (create one in `backend`)**

**Windows (PowerShell):**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
```

**macOS / Linux:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
```

2. Create backend env file:

   - If `backend/.env` already exists and is correctly configured, you can skip this step.

**Windows (PowerShell):**
```powershell
Copy-Item .env.example backend\.env
```

**macOS / Linux:**
```bash
cp .env.example backend/.env
```

3. Seed demo data:

```bash
cd backend
python -m app.seed
cd ..
```

4. Start the app:

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 3001
```

Then open:
- App: http://localhost:3001
- API docs: http://localhost:3001/docs
- Health check: http://localhost:3001/api/v1/health

## Backend structure (short overview)

```
backend/
  app/
    main.py              # FastAPI app, API router wiring, static frontend serving
    config.py            # Environment settings (.env)
    routers/             # API endpoints (health, users, challenges, onboarding, etc.)
    services/            # Domain logic (challenge flows, personalization, hint engine)
    badges/              # Badge catalog + award engine
    storage.py           # JSON store read/write helpers
    repositories.py      # Data access helpers for app features
    seed.py              # Demo data seeding entrypoint
  data/                  # Runtime JSON storage (e.g. store.json)
  tests/                 # Pytest test suite
```

## Frontend structure (short overview)

```
frontend/
  index.html             # SPA shell
  css/
    tokens.css           # Design tokens
    main.css             # Global styles
  js/
    main.js              # Frontend entrypoint
    router.js            # Client-side routing
    api.js               # API client
    pages/               # Route/page renderers
    *.js                 # UI modules (header, badges, animations, HQ/shop, etc.)
  public/assets/         # Challenge and avatar images
  assets/                # Additional worldbuilding graphics
```
