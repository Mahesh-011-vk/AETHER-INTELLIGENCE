import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import aiohttp
from src.crawlers.base import BaseCrawler
from src.models.schemas import ProductRecord
from src.entity_resolution.resolver import resolver
from src.utils.logging import logger

PIPELINES = [
    "text-generation",
    "text-to-image",
    "feature-extraction",
    "conversational",
    "translation",
    "automatic-speech-recognition",
    "image-to-text",
    "text-classification",
    "object-detection",
    "robotics"
]

class ProductCrawler(BaseCrawler):
    def __init__(self, target_records: int = 1000):
        super().__init__(source_name="Hugging Face Models API", max_concurrency=4)
        self.target_records = target_records
        self.endpoint = "https://huggingface.co/api/models"

    async def crawl(self, session: aiohttp.ClientSession) -> List[ProductRecord]:
        logger.info(f"Starting AI product crawl (target: {self.target_records}+)...")
        records: List[ProductRecord] = []
        raw_items: List[Dict[str, Any]] = []
        seen_ids = set()

        for pipeline in PIPELINES:
            if len(records) >= self.target_records:
                break

            limit = 100
            for sort_field in ["likes", "downloads"]:
                if len(records) >= self.target_records:
                    break

                url = f"{self.endpoint}?pipeline_tag={pipeline}&sort={sort_field}&direction=-1&limit={limit}&full=false"
                logger.info(f"Fetching HF products for pipeline '{pipeline}' sorted by {sort_field}...")

                data = await self.fetch_json(url, session, timeout_seconds=25)
                if not data or not isinstance(data, list):
                    continue

                for item in data:
                    model_id = item.get("id")
                    if not model_id or model_id in seen_ids:
                        continue
                    seen_ids.add(model_id)

                    author = item.get("author")
                    if not author and "/" in model_id:
                        author = model_id.split("/")[0]
                    author = author or "Independent AI Creator"

                    model_name = model_id.split("/")[-1] if "/" in model_id else model_id

                    canonical_prod, _ = resolver.resolve(model_name, "Product", self.source_name)
                    canonical_comp, _ = resolver.resolve(author, "Company", self.source_name)

                    likes = item.get("likes", 0)
                    downloads = item.get("downloads", 0)
                    pipeline_tag = item.get("pipeline_tag", pipeline)
                    product_url = f"https://huggingface.co/{model_id}"

                    record = ProductRecord(
                        name=model_id,
                        canonical_name=canonical_prod,
                        company_name=author,
                        canonical_company_name=canonical_comp,
                        description=f"AI model and product specialized in {pipeline_tag}. Created by {author}.",
                        product_url=product_url,
                        category=pipeline_tag.replace("-", " ").title(),
                        pricing_model="Open Source",
                        github_repo_url=None,
                        github_stars=likes,
                        github_forks=downloads,
                        source_name=self.source_name,
                        source_url=url,
                        collected_at=datetime.now(timezone.utc),
                        raw_evidence={"likes": likes, "downloads": downloads, "pipeline_tag": pipeline_tag}
                    )
                    records.append(record)
                    raw_items.append(item)

                    if len(records) >= self.target_records:
                        break

                await asyncio.sleep(0.5)

        self.save_raw_evidence("huggingface_products", raw_items)
        logger.info(f"AI Product crawl completed. Collected {len(records)} products.")
        return records

