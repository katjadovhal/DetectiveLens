# DetectiveLens

Gamified misinformation literacy web app for children — LMU PSIS SS2026 course project.

## Monorepo structure

| Package | Owner | Purpose |
|---------|-------|---------|
| `frontend/` | Person A | Static UI (HTML, CSS, JavaScript) |
| `backend/` | Person D | **Python FastAPI** API + JSON file storage |
| `challenge-data/` | Person B | JSON challenge content |

## Tech stack

- **Backend:** Python (FastAPI), JSON files for user progress and app state
- **Frontend:** HTML, CSS, JavaScript only — no React, Vite, or Tailwind
- **Challenge content:** JSON files in `challenge-data/`

## Prerequisites

- **Python 3.11+**

## Quick start

```bash
# 1. Python backend dependencies
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..

# 2. Configure backend env
cp .env.example backend/.env

# 3. Seed demo user data (JSON store)
npm run data:seed

# 4. Start app (serves frontend + API on :3001)
npm run dev
```

Open http://localhost:3001 — onboarding → home → Burger King fake-post challenge.

The Python backend serves the static frontend files and the API from the same port.

## Backend (Python)

Stack: **FastAPI + JSON file storage**

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 3001
```

| Command | Description |
|---------|-------------|
| `npm run dev` | Start FastAPI (frontend + API on port 3001) |
| `npm run data:seed` | Initialize JSON store with demo user |

User progress and sessions are stored in `backend/data/store.json`. Challenge content is loaded from `challenge-data/*.json`.

API docs (auto-generated): http://localhost:3001/docs

## Frontend structure

```
frontend/
  index.html       # App shell
  css/
    tokens.css     # Design tokens (colors, spacing)
    main.css       # All styles
  js/
    api.js         # API client + mock fallback
    router.js      # Client-side routing
    header.js      # Header component
    main.js        # Entry point
    pages/         # Page renderers
```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start app (frontend + backend on :3001) |
| `npm run data:seed` | Initialize JSON data store |

## API health check

```bash
curl http://localhost:3001/api/v1/health
```

## Team branches

```
main
├── feat/frontend-shell     # Person A
├── feat/challenge-engine   # Person B
├── feat/personalization    # Person C
└── feat/backend-api        # Person D (Python/FastAPI)
```

## Design reference

- [Figma prototype](https://www.figma.com/design/TdI5Wp1Nfgbj65XdwCgB6S/PSIS-Prototype)

## Course deliverables

| Date | Milestone |
|------|-----------|
| 15 Jun 2026 | Intermediate presentation + implementation plan |
| 29 Jul 2026 | Final demo |
| 14 Aug 2026 | Written report |
