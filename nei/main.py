"""NEI FastAPI application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging

from nei.api import routes, sse
from nei.connectors import api as connectors_api
from nei.core.config import settings
from nei.core.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting NEI...")
    await init_db()
    yield
    logger.info("Shutting down NEI...")


app = FastAPI(
    title="NEI",
    description="Nautical Engineering Intelligence - local-first AI engineering assistant",
    version="0.1.0-alpha",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api/v1")
app.include_router(sse.router, prefix="/api/v1")
app.include_router(connectors_api.router, prefix="/api/v1")
from nei.api import evidence_routes
app.include_router(evidence_routes.router, prefix="/api/v1")
from nei.api import engineering_routes
app.include_router(engineering_routes.router, prefix="/api/v1")

if settings.static_build_path.exists():
    app.mount("/", StaticFiles(html=True, directory=str(settings.static_build_path)), name="static")