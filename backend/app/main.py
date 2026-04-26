import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.database import init_db
from app.core.scheduler import start_scheduler
from app.scenarios.definitions import ScenarioRegistry
from app.api.v1.libraries import router as libraries_router
from app.api.v1.papers import router as papers_router
from app.api.v1.timeline import router as timeline_router
from app.api.v1.weekly_reports import router as weekly_router
from app.api.v1.ideas import router as ideas_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.evolution import router as evolution_router
from app.api.v1.operation_logs import router as op_logs_router
from app.api.v1.settings import router as settings_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.chat import router as chat_router
from app.api.v1.notes import router as notes_router
from app.gateway.llm_gateway import gateway
from app.core.database import async_session
from app.models.database import LLMUsage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("carvor.main")


async def _record_token_usage(scenario: str, model: str, input_tokens: int, output_tokens: int):
    async with async_session() as session:
        usage = LLMUsage(
            scenario=scenario,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        session.add(usage)
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized")
    gateway.set_token_callback(_record_token_usage)
    logger.info("Token usage callback registered")
    start_scheduler()
    logger.info("Scheduler started, Carvor is ready")
    yield


app = FastAPI(title="Carvor API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(libraries_router)
app.include_router(papers_router)
app.include_router(timeline_router)
app.include_router(weekly_router)
app.include_router(ideas_router)
app.include_router(tasks_router)
app.include_router(evolution_router)
app.include_router(op_logs_router)
app.include_router(settings_router)
app.include_router(conversations_router)
app.include_router(chat_router)
app.include_router(notes_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))
