import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Tuple

IST = timezone(timedelta(hours=5, minutes=30))

def compute_payload_hash(data: Any) -> str:
    """Computes SHA-256 hash of raw data/dict for tamper-proof provenance."""
    if isinstance(data, dict) or isinstance(data, list):
        serialized = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    elif isinstance(data, str):
        serialized = data.encode("utf-8")
    elif isinstance(data, bytes):
        serialized = data
    else:
        serialized = str(data).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()

def to_ist_string(dt: datetime | None) -> str:
    """Formats UTC datetime to IST formatted string e.g. '23 Sep 2026, 14:15 IST'."""
    if not dt:
        return "N/A"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    ist_dt = dt.astimezone(IST)
    return ist_dt.strftime("%d %b %Y, %H:%M:%S IST")

def evaluate_provenance_status(last_updated: datetime | None, stale_minutes: int = 60) -> Tuple[str, str]:
    """
    Returns (STATUS, DISPLAY_TEXT)
    STATUS is one of: 'LIVE', 'RECENT', 'STALE', 'OFFLINE', 'NO_DATA'
    """
    if not last_updated:
        return ("NO_DATA", "No current observation available")
    
    now_utc = datetime.utcnow()
    diff_minutes = (now_utc - last_updated).total_seconds() / 60.0
    
    if diff_minutes <= 20:
        return ("LIVE", f"Live (Synced {int(diff_minutes)}m ago)")
    elif diff_minutes <= stale_minutes:
        return ("RECENT", f"Recent ({int(diff_minutes)}m ago)")
    elif diff_minutes <= stale_minutes * 6:
        return ("STALE", f"Stale ({int(diff_minutes // 60)}h ago)")
    else:
        return ("OFFLINE", f"Offline (Last sync: {to_ist_string(last_updated)})")
