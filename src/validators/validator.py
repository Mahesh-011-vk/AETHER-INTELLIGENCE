from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional, Set
from pydantic import ValidationError
from src.models.schemas import (
    StartupRecord,
    ProductRecord,
    ResearchPaperRecord,
    JobRecord,
    NewsRecord,
)
from src.extractors.date_extractor import DateExtractor
from src.utils.logging import logger
from config.settings import settings

class DataValidator:
    def __init__(self, rolling_window_hours: int = 24):
        self.rolling_window_hours = rolling_window_hours
        self.seen_startups: Set[str] = set()
        self.seen_products: Set[str] = set()
        self.seen_papers: Set[str] = set()
        self.seen_jobs: Set[str] = set()
        self.seen_news: Set[str] = set()

        self.stats: Dict[str, Any] = {
            "total_processed": 0,
            "total_valid": 0,
            "total_rejected": 0,
            "rejections_by_reason": {}
        }

    def _record_rejection(self, reason: str) -> None:
        self.stats["total_rejected"] += 1
        self.stats["rejections_by_reason"][reason] = (
            self.stats["rejections_by_reason"].get(reason, 0) + 1
        )

    def validate_startup(self, raw_data: Dict[str, Any]) -> Tuple[Optional[StartupRecord], Optional[str]]:
        self.stats["total_processed"] += 1
        name = str(raw_data.get("name", "")).strip()
        if not name or len(name) < 1:
            self._record_rejection("startup_missing_name")
            return None, "Startup name is required and cannot be empty"

        dedup_key = f"{name.lower()}::{str(raw_data.get('website', '')).lower()}"
        if dedup_key in self.seen_startups:
            self._record_rejection("duplicate_startup")
            return None, f"Duplicate startup detected: {name}"

        try:
            record = StartupRecord(**raw_data)
            self.seen_startups.add(dedup_key)
            self.stats["total_valid"] += 1
            return record, None
        except ValidationError as e:
            err_msg = f"Startup validation error: {e.errors()[0]['msg']}"
            self._record_rejection("startup_schema_violation")
            return None, err_msg

    def validate_product(self, raw_data: Dict[str, Any]) -> Tuple[Optional[ProductRecord], Optional[str]]:
        self.stats["total_processed"] += 1
        name = str(raw_data.get("name", "")).strip()
        if not name or len(name) < 1:
            self._record_rejection("product_missing_name")
            return None, "Product name is required and cannot be empty"

        dedup_key = f"{name.lower()}::{str(raw_data.get('product_url', '')).lower()}"
        if dedup_key in self.seen_products:
            self._record_rejection("duplicate_product")
            return None, f"Duplicate product detected: {name}"

        try:
            record = ProductRecord(**raw_data)
            self.seen_products.add(dedup_key)
            self.stats["total_valid"] += 1
            return record, None
        except ValidationError as e:
            err_msg = f"Product validation error: {e.errors()[0]['msg']}"
            self._record_rejection("product_schema_violation")
            return None, err_msg

    def validate_research_paper(self, raw_data: Dict[str, Any]) -> Tuple[Optional[ResearchPaperRecord], Optional[str]]:
        self.stats["total_processed"] += 1
        title = str(raw_data.get("title", "")).strip()
        if not title or len(title) < 2:
            self._record_rejection("paper_missing_title")
            return None, "Paper title is required and cannot be empty"

        arxiv_id = str(raw_data.get("arxiv_id", "")).strip().lower()
        dedup_key = f"{title.lower()}::{arxiv_id}"
        if dedup_key in self.seen_papers:
            self._record_rejection("duplicate_paper")
            return None, f"Duplicate research paper: {title}"

        try:
            record = ResearchPaperRecord(**raw_data)
            self.seen_papers.add(dedup_key)
            self.stats["total_valid"] += 1
            return record, None
        except ValidationError as e:
            err_msg = f"Paper validation error: {e.errors()[0]['msg']}"
            self._record_rejection("paper_schema_violation")
            return None, err_msg

    def validate_job(
        self,
        raw_data: Dict[str, Any],
        enforce_freshness: bool = True
    ) -> Tuple[Optional[JobRecord], Optional[str]]:
        self.stats["total_processed"] += 1
        job_title = str(raw_data.get("job_title", "")).strip()
        company = str(raw_data.get("company_name", "")).strip()

        if not job_title or not company:
            self._record_rejection("job_missing_required_fields")
            return None, "Job title and company name are required"

        # Check date existence and parse
        raw_published = raw_data.get("published_at")
        pub_dt = DateExtractor.parse_datetime(raw_published)
        if not pub_dt:
            self._record_rejection("job_invalid_or_missing_date")
            return None, f"Job publication date unverifiable: {raw_published}"

        raw_data["published_at"] = pub_dt

        # Strict 24-hour freshness check
        if enforce_freshness:
            if not DateExtractor.is_within_rolling_window(pub_dt, hours=self.rolling_window_hours):
                self._record_rejection("job_stale_exceeds_24h")
                return None, f"Job published at {pub_dt.isoformat()} exceeds {self.rolling_window_hours}h freshness window"

        dedup_key = f"{company.lower()}::{job_title.lower()}::{str(raw_data.get('job_url', '')).lower()}"
        if dedup_key in self.seen_jobs:
            self._record_rejection("duplicate_job")
            return None, f"Duplicate job: {job_title} at {company}"

        try:
            record = JobRecord(**raw_data)
            self.seen_jobs.add(dedup_key)
            self.stats["total_valid"] += 1
            return record, None
        except ValidationError as e:
            err_msg = f"Job validation error: {e.errors()[0]['msg']}"
            self._record_rejection("job_schema_violation")
            return None, err_msg

    def validate_news(
        self,
        raw_data: Dict[str, Any],
        enforce_freshness: bool = True
    ) -> Tuple[Optional[NewsRecord], Optional[str]]:
        self.stats["total_processed"] += 1
        title = str(raw_data.get("title", "")).strip()
        url = str(raw_data.get("article_url", "")).strip()

        if not title or len(title) < 3 or not url:
            self._record_rejection("news_missing_required_fields")
            return None, "Article title and URL are required"

        raw_published = raw_data.get("published_at")
        pub_dt = DateExtractor.parse_datetime(raw_published)
        if not pub_dt:
            self._record_rejection("news_invalid_or_missing_date")
            return None, f"News publication date unverifiable: {raw_published}"

        raw_data["published_at"] = pub_dt

        # Strict 24-hour freshness check
        if enforce_freshness:
            if not DateExtractor.is_within_rolling_window(pub_dt, hours=self.rolling_window_hours):
                self._record_rejection("news_stale_exceeds_24h")
                return None, f"News published at {pub_dt.isoformat()} exceeds {self.rolling_window_hours}h freshness window"

        dedup_key = f"{title.lower()}::{url.lower()}"
        if dedup_key in self.seen_news:
            self._record_rejection("duplicate_news")
            return None, f"Duplicate news article: {title}"

        try:
            record = NewsRecord(**raw_data)
            self.seen_news.add(dedup_key)
            self.stats["total_valid"] += 1
            return record, None
        except ValidationError as e:
            err_msg = f"News validation error: {e.errors()[0]['msg']}"
            self._record_rejection("news_schema_violation")
            return None, err_msg

validator = DataValidator(rolling_window_hours=settings.ROLLING_WINDOW_HOURS)

