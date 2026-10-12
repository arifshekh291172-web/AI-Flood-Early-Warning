from datetime import datetime
from typing import Optional, Any, Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar("T")

class ProvenanceMetadata(BaseModel):
    source_name: str
    source_url: Optional[str] = None
    observed_at_ist: str
    retrieved_at_ist: str
    status: str # LIVE, RECENT, STALE, OFFLINE, NO_DATA
    raw_payload_hash: Optional[str] = None

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully"
    mode: str = "LIVE" # LIVE or DEMO
    timestamp: datetime = datetime.utcnow()
    data: Optional[T] = None

class DataSourceStatus(BaseModel):
    id: str
    name: str
    category: str
    endpoint_url: Optional[str] = None
    status: str
    last_successful_sync_ist: str
    latency_ms: float
    records_synced_today: int
    last_error_message: Optional[str] = None
