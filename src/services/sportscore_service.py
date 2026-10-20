import os
import time
import requests
from typing import Dict, Any, Optional
from src.config.settings import settings
from src.utils.logger import logger

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

class SportScoreException(Exception):
    """Custom exception for SportScore API failures."""
    pass

class SportScoreClient:
    def __init__(self, base_url: str = None, app_name: str = None):
        self.base_url = base_url or settings.sportscore_api_url
        self.app_name = app_name or settings.sportscore_app_name
        self.ssl_verify = os.getenv("SSL_VERIFY", "true").strip().lower() != "false"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        })

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 3, timeout: int = 12) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        query_params = dict(params or {})
        if "src" not in query_params:
            query_params["src"] = self.app_name

        attempt = 0
        last_exception = None

        while attempt < max_retries:
            attempt += 1
            try:
                response = self.session.get(url, params=query_params, timeout=timeout, verify=self.ssl_verify)
                
                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "5"))
                    logger.warning(f"SportScore API rate limit reached (429). Retrying after {retry_after}s (Attempt {attempt}/{max_retries})...")
                    time.sleep(retry_after)
                    continue

                # Server error or gateway timeout retry
                if response.status_code in (500, 502, 503, 504):
                    logger.warning(f"SportScore API server error ({response.status_code}). Retrying in {attempt * 2}s (Attempt {attempt}/{max_retries})...")
                    time.sleep(attempt * 2)
                    continue

                response.raise_for_status()

                try:
                    return response.json()
                except ValueError as e:
                    logger.error(f"SportScore API returned invalid JSON: {response.text[:200]}")
                    raise SportScoreException("SportScore API returned invalid JSON response") from e

            except requests.exceptions.Timeout as e:
                logger.error(f"SportScore API timeout on {url} (Attempt {attempt}/{max_retries})")
                last_exception = e
                if attempt < max_retries:
                    time.sleep(attempt * 2)
            except requests.exceptions.RequestException as e:
                logger.error(f"SportScore API network error: {e} (Attempt {attempt}/{max_retries})")
                last_exception = e
                if attempt < max_retries:
                    time.sleep(attempt * 2)

        # All retries failed
        raise SportScoreException(f"SportScore API request failed after {max_retries} attempts: {last_exception}")

sportscore_client = SportScoreClient()
