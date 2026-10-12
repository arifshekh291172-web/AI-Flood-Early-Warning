import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.services.seed_data import seed_initial_data
from backend.app.services.scheduler import start_scheduler, shutdown_scheduler
from backend.app.ml.model_loader import model_registry
from backend.app.models.core import ApiLog
from backend.app.utils.logger import logger
from backend.app.routers import (
    auth_router, dashboard_router, health_router, weather_router,
    rainfall_router, warnings_router, risk_router, gis_router,
    reports_router, field_router, roads_router, model_router,
    data_sources_router, audit_router, websocket_router, satellite_router
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup: initialize database tables and seed verified initial data
    logger.info("Initializing NE-SHIELD Database and Schema...")
    Base.metadata.create_all(bind=engine)
    seed_initial_data()

    # 2. Initialize / load active ML model
    logger.info("Checking ML Model Engine...")
    model_registry.get_model()

    # 3. Start APScheduler for official data ingestion
    logger.info("Starting Background Data Ingestion Schedulers...")
    start_scheduler()

    yield

    # Shutdown
    logger.info("Shutting down NE-SHIELD background workers...")
    shutdown_scheduler()

app = FastAPI(
    title="NE-SHIELD: AI-Powered Landslide Early Warning & Real-Time Disaster Monitoring System",
    description="Operational disaster-intelligence platform for the North Eastern Region of India (Assam, Arunachal Pradesh, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, Tripura). Ingests official IMD weather/rainfall APIs, ISRO Bhuvan geospatial layers, NDMA/SACHET emergency alerts, and executes custom geotechnical ML risk models.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging & API latency middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    latency_ms = (time.time() - start_time) * 1000.0

    # Log API call to database
    path = request.url.path
    if not path.startswith("/static") and not path.startswith("/docs") and not path.startswith("/openapi.json"):
        try:
            db = SessionLocal()
            log = ApiLog(
                path=path,
                method=request.method,
                status_code=response.status_code,
                latency_ms=round(latency_ms, 2),
                ip_address=request.client.host if request.client else None
            )
            db.add(log)
            db.commit()
            db.close()
        except Exception:
            pass

    return response

# Mount Static Files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Register all Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(weather_router)
app.include_router(rainfall_router)
app.include_router(warnings_router)
app.include_router(risk_router)
app.include_router(gis_router)
app.include_router(reports_router)
app.include_router(field_router)
app.include_router(roads_router)
app.include_router(model_router)
app.include_router(data_sources_router)
app.include_router(audit_router)
app.include_router(websocket_router)
app.include_router(satellite_router)

@app.get("/")
def read_root():
    # If built frontend index.html exists in static, serve it; otherwise return operational API info
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "system": "NE-SHIELD",
        "description": "AI-Powered Landslide Early Warning & Real-Time Disaster Monitoring System",
        "region": "North Eastern Region of India (Assam, Arunachal Pradesh, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, Tripura)",
        "version": settings.APP_VERSION,
        "operational_mode": settings.OPERATIONAL_MODE,
        "documentation": "/docs",
        "health_check": "/api/health"
    }

# Fallback for frontend SPA client-side routes
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    if full_path.startswith("api/") or full_path.startswith("ws/") or full_path.startswith("static/") or full_path == "docs" or full_path == "openapi.json":
        return JSONResponse(status_code=404, content={"detail": "API endpoint not found"})
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "system": "NE-SHIELD",
        "path": full_path,
        "mode": settings.OPERATIONAL_MODE,
        "docs": "/docs"
    }
