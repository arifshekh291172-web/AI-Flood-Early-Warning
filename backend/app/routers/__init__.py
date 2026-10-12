from backend.app.routers.auth import router as auth_router
from backend.app.routers.dashboard import router as dashboard_router
from backend.app.routers.health import router as health_router
from backend.app.routers.weather import router as weather_router
from backend.app.routers.rainfall import router as rainfall_router
from backend.app.routers.warnings import router as warnings_router
from backend.app.routers.risk import router as risk_router
from backend.app.routers.gis import router as gis_router
from backend.app.routers.reports import router as reports_router
from backend.app.routers.field import router as field_router
from backend.app.routers.roads import router as roads_router
from backend.app.routers.model import router as model_router
from backend.app.routers.data_sources import router as data_sources_router
from backend.app.routers.audit import router as audit_router
from backend.app.routers.websocket import router as websocket_router
from backend.app.routers.satellite import router as satellite_router

__all__ = [
    "auth_router",
    "dashboard_router",
    "health_router",
    "weather_router",
    "rainfall_router",
    "warnings_router",
    "risk_router",
    "gis_router",
    "reports_router",
    "field_router",
    "roads_router",
    "model_router",
    "data_sources_router",
    "audit_router",
    "websocket_router",
    "satellite_router"
]
