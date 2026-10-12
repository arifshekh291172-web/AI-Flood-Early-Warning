import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "NE-SHIELD"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    OPERATIONAL_MODE: str = os.getenv("OPERATIONAL_MODE", "LIVE")  # "LIVE" or "DEMO"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./ne_shield.db"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "ne_shield_super_secure_jwt_secret_key_change_in_production_987654321")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    
    # Official IMD API Platform
    IMD_API_BASE_URL: str = os.getenv("IMD_API_BASE_URL", "https://api.imd.gov.in/api/v1")
    IMD_API_KEY: str = os.getenv("IMD_API_KEY", "")
    IMD_CLIENT_ID: str = os.getenv("IMD_CLIENT_ID", "")
    IMD_TIMEOUT_SECONDS: int = int(os.getenv("IMD_TIMEOUT_SECONDS", "10"))
    IMD_CACHE_TTL_SECONDS: int = int(os.getenv("IMD_CACHE_TTL_SECONDS", "900"))
    
    # ISRO / NRSC Bhuvan
    BHUVAN_WMS_URL: str = os.getenv("BHUVAN_WMS_URL", "https://bhuvan-vec1.nrsc.gov.in/bhuvan/wms")
    BHUVAN_API_KEY: str = os.getenv("BHUVAN_API_KEY", "")
    
    # NDMA / SACHET
    NDMA_CAP_FEED_URL: str = os.getenv("NDMA_CAP_FEED_URL", "https://sachet.ndma.gov.in/cap_feed/rss")
    NDMA_API_KEY: str = os.getenv("NDMA_API_KEY", "")
    
    # Scheduling Intervals (minutes)
    IMD_WEATHER_INTERVAL: int = int(os.getenv("IMD_WEATHER_INTERVAL", "15"))
    RAINFALL_INTERVAL: int = int(os.getenv("RAINFALL_INTERVAL", "15"))
    WARNING_INTERVAL: int = int(os.getenv("WARNING_INTERVAL", "30"))
    SENSOR_INTERVAL: int = int(os.getenv("SENSOR_INTERVAL", "5"))
    GOV_ALERT_INTERVAL: int = int(os.getenv("GOV_ALERT_INTERVAL", "15"))
    RISK_PREDICTION_INTERVAL: int = int(os.getenv("RISK_PREDICTION_INTERVAL", "10"))
    DATA_SOURCE_HEALTH_INTERVAL: int = int(os.getenv("DATA_SOURCE_HEALTH_INTERVAL", "2"))
    
    # ML Model
    MODEL_PATH: str = os.getenv("MODEL_PATH", "backend/app/ml/models/active_model.json")
    MIN_CONFIDENCE_THRESHOLD: float = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", "0.65"))
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000"
    ]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
