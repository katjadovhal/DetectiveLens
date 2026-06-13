# DetectiveLens

Gamified misinformation literacy web app for children — LMU PSIS SS2026 course project.

## Monorepo structure

| Package | Owner | Purpose |
|---------|-------|---------|
| `frontend/` | Person A | React UI (JavaScript + HTML), routing, components |
| `backend/` | Person D | **Python FastAPI** API + JSON file storage |
| `challenge-data/` | Person B | JSON challenge content |

## Tech stack

- **Backend:** Python (FastAPI), JSON files for user progress and app state
- **Frontend:** JavaScript, HTML, React, Vite, Tailwind CSS — no TypeScript
- **Challenge content:** JSON files in `challenge-data/`

## Prerequisites

- **Node.js 20+** (includes npm)
- **Python 3.11+** (backend only)

## Quick start

```bash
# 1. Install frontend dependencies
npm install

# 2. Python backend dependencies
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..

# 3. Configure backend env
cp .env.example backend/.env

# 4. Seed demo user data (JSON store)
npm run data:seed

# 5. Start dev servers (frontend :5173, backend :3001)
npm run dev
```

Open http://localhost:5173 — onboarding → home → Burger King fake-post challenge.

**Frontend-only mode** (no Python backend): run `npm run dev:frontend` — mock data is used automatically when the API is unavailable.

## Backend (Python)

Stack: **FastAPI + JSON file storage**

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 3001
```

| Command | Description |
|---------|-------------|
| `npm run dev:backend` | Start FastAPI with hot reload |
| `npm run data:seed` | Initialize JSON store with demo user |

User progress and sessions are stored in `backend/data/store.json`. Challenge content is loaded from `challenge-data/*.json`.

API docs (auto-generated): http://localhost:3001/docs

## Scripts

| Command | Description |
|---------|-------------|
| `npm install` | Install frontend workspace packages |
| `npm run dev` | Run frontend + Python backend |
| `npm run build` | Build frontend for production |
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
