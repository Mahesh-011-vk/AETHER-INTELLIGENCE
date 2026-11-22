import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
import aiohttp
from config.settings import settings
from src.utils.logging import logger
from src.utils.retry import async_retry

class BaseCrawler:
    def __init__(self, source_name: str, max_concurrency: int = 5):
        self.source_name = source_name
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.headers = {
            "User-Agent": "AI-Intelligence-Pipeline/1.0 (+https://github.com/assessment/ai-pipeline)",
            "Accept": "application/json, application/xml, text/html, */*"
        }

    @async_retry(max_retries=3, base_delay=1.0, backoff_factor=1.5)
    async def fetch_text(
        self,
        url: str,
        session: aiohttp.ClientSession,
        headers: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 20
    ) -> Optional[str]:
        req_headers = {**self.headers, **(headers or {})}
        async with self.semaphore:
            try:
                async with session.get(url, headers=req_headers, timeout=aiohttp.ClientTimeout(total=timeout_seconds)) as resp:
                    if resp.status == 429:
                        logger.warning(f"Rate limited (429) fetching {url}")
                        await asyncio.sleep(3.0)
                        raise aiohttp.ClientResponseError(resp.request_info, resp.history, status=429, message="Rate limited")
                    if resp.status != 200:
                        logger.warning(f"HTTP {resp.status} while fetching {url}")
                        return None
                    return await resp.text()
            except Exception as e:
                logger.debug(f"Error fetching {url}: {e}")
                return None

    @async_retry(max_retries=3, base_delay=1.0, backoff_factor=1.5)
    async def fetch_json(
        self,
        url: str,
        session: aiohttp.ClientSession,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 20
    ) -> Optional[Any]:
        req_headers = {**self.headers, **(headers or {})}
        async with self.semaphore:
            try:
                async with session.get(
                    url,
                    headers=req_headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=timeout_seconds)
                ) as resp:
                    if resp.status == 429:
                        logger.warning(f"Rate limited (429) fetching JSON from {url}")
                        await asyncio.sleep(3.0)
                        raise aiohttp.ClientResponseError(resp.request_info, resp.history, status=429, message="Rate limited")
                    if resp.status != 200:
                        logger.warning(f"HTTP {resp.status} while fetching JSON from {url}")
                        return None
                    return await resp.json(content_type=None)
            except Exception as e:
                logger.debug(f"Error fetching JSON from {url}: {e}")
                return None

    def save_raw_evidence(self, domain_label: str, data: Any) -> Path:
        """
        Saves raw crawler payload to data/raw/ directory with timestamp.
        """
        raw_dir = settings.DATA_RAW_DIR
        raw_dir.mkdir(parents=True, exist_ok=True)
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{domain_label}_{timestamp_str}.json"
        target_path = raw_dir / filename
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return target_path

