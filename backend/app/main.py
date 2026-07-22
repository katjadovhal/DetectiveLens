from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.routers import challenges, health, home, onboarding, personalization, profiles, users

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

app = FastAPI(title="DetectiveLens API", version="0.1.0")


class NoCacheStaticMiddleware(BaseHTTPMiddleware):
    """Avoid stale ES-module caches during local development."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.startswith("/js/") or path.startswith("/css/") or path == "/" or path.endswith(".html"):
            response.headers["Cache-Control"] = "no-store, max-age=0"
        return response


app.add_middleware(NoCacheStaticMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

app.include_router(health.router, prefix=API_PREFIX)
app.include_router(home.router, prefix=API_PREFIX)
app.include_router(onboarding.router, prefix=API_PREFIX)
app.include_router(profiles.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(challenges.router, prefix=API_PREFIX)
app.include_router(personalization.router, prefix=API_PREFIX)

# Mount static files BEFORE catch-all routes
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
# Mount assets directory first
try:
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
except Exception:
    pass  # Directory might not exist
# Mount public directory for images and other assets
app.mount("/public", StaticFiles(directory=FRONTEND_DIR / "public"), name="public")


@app.get("/")
async def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404)

    static_file = FRONTEND_DIR / full_path
    if static_file.is_file():
        return FileResponse(static_file)

    return FileResponse(FRONTEND_DIR / "index.html")
