"""NEI FastAPI application."""
from contextlib import asynccontextmanager
from uuid import uuid4
import secrets

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse, FileResponse
import logging

from nei.api import routes, sse
from nei.connectors import api as connectors_api
from nei.core.config import settings
from nei.core.database import init_db, get_db
from nei.engineering.seed import ensure_built_in_formulas

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory session token (regenerated on every backend start per SECURITY.md)
_session_token: str = ""

# Paths that never require auth (first-visit flow + health)
_PUBLIC_PATHS = {
    "/api/v1/health",
    "/api/v1/auth/session",
}


def _generate_session_token() -> str:
    global _session_token
    _session_token = uuid4().hex  # 128-bit random, 64 hex chars
    return _session_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting NEI...")
    if settings.session_secret == "insecure-change-me" and settings.environment != "dev":
        raise RuntimeError(
            "Session secret is still the default 'insecure-change-me'. "
            "Set NEI_SESSION_SECRET in .env before starting in non-dev mode."
        )
    await init_db()
    await ensure_built_in_formulas()
    _generate_session_token()
    # Persist token to app_state so restarts can be audited
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO app_state (key, value) VALUES ('session_token', ?)",
            (_session_token,),
        )
        await db.commit()
    yield
    logger.info("Shutting down NEI...")


app = FastAPI(
    title="NEI",
    description="Nautical Engineering Intelligence - local-first AI engineering assistant",
    version="0.1.0-alpha",
    lifespan=lifespan,
)


# ── Security middleware ────────────────────────────────────────────────────────

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    path = request.url.path

    # Public paths bypass auth
    if path in _PUBLIC_PATHS:
        return await call_next(request)

    # API paths: DNS rebinding check + auth
    if path.startswith("/api/"):
        host = request.headers.get("host", "").split(":")[0].lower()
        # "testserver" is Starlette TestClient's default host header
        if host not in ("localhost", "127.0.0.1", "testserver"):
            return JSONResponse(
                status_code=403,
                content={"detail": "FORBIDDEN_HOST"},
            )

        # Require session cookie on all non-public API endpoints,
        # unless running in dev mode (local single-user workflow)
        if settings.environment != "dev":
            cookie = request.cookies.get("nei_session")
            if not cookie or not secrets.compare_digest(cookie, _session_token):
                if path != "/api/v1/auth/session":
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "UNAUTHENTICATED"},
                    )

    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Auth endpoints ─────────────────────────────────────────────────────────────

@app.post("/api/v1/auth/session")
async def auth_session(request: Request):
    """Mint a fresh session token cookie (single-user, no password)."""
    token = _generate_session_token()
    # Persist new token
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO app_state (key, value) VALUES ('session_token', ?)",
            (token,),
        )
        await db.commit()
    response = JSONResponse(content={"session": "active"})
    response.set_cookie(
        key="nei_session",
        value=token,
        httponly=True,
        samesite="strict",
        secure=False,  # localhost only per SECURITY.md §2
        path="/",
        max_age=settings.session_timeout_minutes * 60,
    )
    return response


# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(routes.router, prefix="/api/v1")
app.include_router(sse.router, prefix="/api/v1")
app.include_router(connectors_api.router, prefix="/api/v1")
from nei.api import evidence_routes
app.include_router(evidence_routes.router, prefix="/api/v1")
from nei.api import engineering_routes
app.include_router(engineering_routes.router, prefix="/api/v1")

if settings.static_build_path.exists():
    app.mount("/", StaticFiles(html=True, directory=str(settings.static_build_path)), name="static")


@app.middleware("http")
async def spa_fallback(request: Request, call_next):
    """Serve `index.html` for unknown frontend routes (deep links, refresh)."""
    response = await call_next(request)
    if (
        response.status_code == 404
        and not request.url.path.startswith("/api/")
        and request.url.path not in ("/openapi.json", "/docs", "/redoc", "/favicon.ico")
    ):
        return FileResponse(str(settings.static_build_path / "index.html"), status_code=200)
    return response
