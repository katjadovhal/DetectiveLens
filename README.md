# DetectiveLens

Gamified misinformation literacy web app for children — LMU PSIS SS2026 course project.

## Monorepo structure

| Package | Owner | Purpose |
|---------|-------|---------|
| `frontend/` | Person A | React UI, routing, components |
| `backend/` | Person D | **Python FastAPI** API + PostgreSQL |
| `packages/shared/` | All | Shared TypeScript types & validators |
| `personalization-engine/` | Person C | TS reference lib; Python logic lives in `backend/app/services/` |
| `challenge-data/` | Person B | JSON challenge content |

## Prerequisites

- **Node.js 20+** (includes npm — no extra package manager needed)
- **Python 3.11+** (backend)
- Docker (for PostgreSQL)

## Quick start

```bash
# 1. Install frontend dependencies (npm workspaces)
npm install

# 2. Python backend dependencies
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..

# 3. Start PostgreSQL
docker compose up -d

# 4. Configure backend env
cp .env.example backend/.env

# 5. Build shared TS package (required before frontend dev)
npm run build:shared

# 6. Create tables & seed data
npm run db:seed

# 7. Start dev servers (frontend :5173, backend :3001)
npm run dev
```

Open http://localhost:5173 — onboarding → home → Burger King fake-post challenge.

**Frontend-only mode** (no Python/DB): run `npm run dev:frontend` — mock data is used automatically when the API is unavailable.

## Backend (Python)

Stack: **FastAPI + SQLAlchemy + PostgreSQL**

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 3001
```

| Command | Description |
|---------|-------------|
| `npm run dev:backend` | Start FastAPI with hot reload |
| `npm run db:seed` | Create tables + seed demo user & challenges |
| `python -m app.seed` | Same as above (from `backend/`) |

API docs (auto-generated): http://localhost:3001/docs

## Scripts

| Command | Description |
|---------|-------------|
| `npm install` | Install all JS/TS workspace packages |
| `npm run dev` | Run frontend + Python backend |
| `npm run build` | Build all workspace packages |
| `npm run build:shared` | Build shared types only |
| `npm run db:seed` | Initialize DB schema and seed data |

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
