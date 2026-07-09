import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database.connection import init_db
from api.routes.llm import router as llm_router
from api.routes.analysis import router as analysis_router
from api.routes.auth import router as auth_router
from api.routes.vault import router as vault_router
from api.routes.comparison import router as comparison_router
from api.routes.resume_library import router as library_router
from services.auth_service import create_super_admin
from middleware.security import SecurityMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting CV Chacha 😎 Backend...")
    logger.info(f"App: {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    hf_key = settings.hf_api_key
    if hf_key:
        logger.info(f"HF_API_KEY loaded: {hf_key[:8]}...{hf_key[-4:]} (length={len(hf_key)})")
    else:
        logger.warning("HF_API_KEY is NOT configured. LLM features will use fallback behavior.")
    init_db()
    create_super_admin()
    yield
    logger.info("Shutting down CV Chacha 😎 Backend...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityMiddleware)

app.include_router(llm_router)
app.include_router(analysis_router)
app.include_router(auth_router)
app.include_router(vault_router)
app.include_router(comparison_router)
app.include_router(library_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
