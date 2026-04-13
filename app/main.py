"""Flux-Capacitor - FastAPI application."""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database.connection import init_db
from app.api.routes import health, presentations, slides, stats, prompts, uploads


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Flux-Capacitor · Gerador de apresentações friendly-first",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- API routes ----
API_PREFIX = "/api/v1"
app.include_router(health.router, prefix=API_PREFIX)
app.include_router(presentations.router, prefix=API_PREFIX)
app.include_router(slides.router, prefix=API_PREFIX)
app.include_router(slides.reorder_router, prefix=API_PREFIX)
app.include_router(stats.router, prefix=API_PREFIX)
app.include_router(prompts.router, prefix=API_PREFIX)
app.include_router(uploads.router, prefix=API_PREFIX)
# também exposto em /uploads/{id}/{filename} para permitir <img> em HTMLs exportados
app.include_router(uploads.router)


# ---- Frontend estático ----
FRONT_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONT_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONT_DIR / "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(str(FRONT_DIR / "index.html"))
