import time
import httpx
from typing import Optional, Dict, Any, Tuple
from backend.app.config import settings
from backend.app.utils.logger import logger
from backend.app.integrations.imd.cache import imd_cache

class IMDClient:
    """
    Official India Meteorological Department (IMD) API Client.
    Platform: https://api.imd.gov.in/public/
    """
    def __init__(self):
        self.base_url = settings.IMD_API_BASE_URL.rstrip("/")
        self.api_key = settings.IMD_API_KEY
        self.client_id = settings.IMD_CLIENT_ID
        self.timeout = settings.IMD_TIMEOUT_SECONDS

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "NE-SHIELD-Disaster-Monitoring/1.0 (Govt-Northeast-India)"
        }
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.client_id:
            headers["X-Client-Id"] = self.client_id
        return headers

    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[Any], float, Optional[str]]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        cache_key = f"imd:{endpoint}:{sorted(params.items()) if params else ''}"
        
        cached_data = imd_cache.get(cache_key)
        if cached_data is not None:
            return True, cached_data, 0.0, None

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=True) as client:
                response = await client.get(url, headers=self._get_headers(), params=params)
                latency_ms = (time.time() - start_time) * 1000.0

                if response.status_code == 200:
                    try:
                        data = response.json()
                        imd_cache.set(cache_key, data, ttl=settings.IMD_CACHE_TTL_SECONDS)
                        logger.info(f"IMD API query '{endpoint}' succeeded ({latency_ms:.1f}ms)")
                        return True, data, latency_ms, None
                    except Exception as json_err:
                        return False, None, latency_ms, f"Invalid JSON response: {str(json_err)}"
                elif response.status_code in [401, 403]:
                    logger.warning(f"IMD API auth failure on '{endpoint}': Status {response.status_code}")
                    return False, None, latency_ms, f"Authentication failure: status {response.status_code} - API key invalid or unapproved static IP"
                elif response.status_code == 429:
                    logger.warning(f"IMD API rate limit hit on '{endpoint}'")
                    return False, None, latency_ms, "Rate limit exceeded on IMD endpoint"
                else:
                    return False, None, latency_ms, f"IMD HTTP error status: {response.status_code}"

        except httpx.TimeoutException:
            latency_ms = (time.time() - start_time) * 1000.0
            logger.warning(f"IMD API request to '{endpoint}' timed out after {self.timeout}s")
            return False, None, latency_ms, f"Connection timed out after {self.timeout}s"
        except httpx.ConnectError:
            latency_ms = (time.time() - start_time) * 1000.0
            logger.warning(f"IMD API host unreachable at {self.base_url}")
            return False, None, latency_ms, "IMD host unreachable or network route down"
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000.0
            logger.error(f"Unexpected error querying IMD '{endpoint}': {str(e)}")
            return False, None, latency_ms, str(e)

    async def get_city_forecast(self, station_code: Optional[str] = None) -> Tuple[bool, Optional[Any], float, Optional[str]]:
        params = {"id": station_code} if station_code else None
        return await self._make_request("cityforecast", params=params)

    async def get_district_nowcast(self, state_code: Optional[str] = None) -> Tuple[bool, Optional[Any], float, Optional[str]]:
        params = {"state": state_code} if state_code else None
        return await self._make_request("district_nowcast", params=params)

    async def get_district_warnings(self, state_code: Optional[str] = None) -> Tuple[bool, Optional[Any], float, Optional[str]]:
        params = {"state": state_code} if state_code else None
        return await self._make_request("district_warnings", params=params)

    async def get_district_rainfall(self, state_code: Optional[str] = None) -> Tuple[bool, Optional[Any], float, Optional[str]]:
        params = {"state": state_code} if state_code else None
        return await self._make_request("district_rainfall", params=params)

    async def get_aws_arg_data(self, state_code: Optional[str] = None) -> Tuple[bool, Optional[Any], float, Optional[str]]:
        params = {"state": state_code} if state_code else None
        return await self._make_request("aws_arg_data", params=params)

imd_client = IMDClient()
