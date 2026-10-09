from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.modules.ads.routes import router as ads_router
from app.modules.crm.routes import router as crm_router
from app.modules.marketing.routes import router as marketing_router
from app.modules.operations.routes import router as operations_router
from app.modules.tracking.routes import router as tracking_router
from app.modules.vsl.routes import pages_router as vsl_pages_router
from app.modules.vsl.routes import router as vsl_router
from app.utils.auth import require_admin
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME}...")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Sistema de Automação de Marketing e Vendas com IA",
    version="1.0.0",
    lifespan=lifespan,
)

# The VSL page is served by this API (same origin), so browsers only need CORS for extra origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip().rstrip("/") for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

admin_only = [Depends(require_admin)]

# Register routers
# Internal: CRM, sales operations and agents (dashboard only)
app.include_router(ads_router, prefix="/api/v1", dependencies=admin_only)
app.include_router(crm_router, prefix="/api/v1", dependencies=admin_only)
app.include_router(marketing_router, prefix="/api/v1", dependencies=admin_only)
app.include_router(operations_router, prefix="/api/v1", dependencies=admin_only)
# Mixed: public endpoints plus admin-only ones protected route by route
app.include_router(tracking_router, prefix="/api/v1")
app.include_router(vsl_router, prefix="/api/v1")
app.include_router(vsl_pages_router)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
