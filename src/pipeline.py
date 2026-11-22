import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import aiohttp

from config.settings import settings
from src.database.repository import repo
from src.crawlers.startup import StartupCrawler
from src.crawlers.product import ProductCrawler
from src.crawlers.research import ResearchCrawler
from src.crawlers.jobs import JobCrawler
from src.crawlers.news import NewsCrawler
from src.validators.validator import validator
from src.entity_resolution.resolver import resolver
from src.exporters.sheets_exporter import exporter
from src.llm.orchestrator import orchestrator
from src.utils.logging import logger

pipeline_progress: Dict[str, Any] = {
    "is_running": False,
    "run_id": None,
    "current_stage": "Idle",
    "stage_index": 0,
    "total_stages": 11,
    "progress_percent": 0,
    "records_fetched": 0,
    "records_processed": 0,
    "records_inserted": 0,
    "duplicate_records": 0,
    "failed_records": 0,
    "logs": [],
    "error": None
}

def set_stage(index: int, name: str, percent: int, log_msg: str, **kwargs):
    pipeline_progress["stage_index"] = index
    pipeline_progress["current_stage"] = name
    pipeline_progress["progress_percent"] = percent
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    pipeline_progress["logs"].append(f"[{ts}] {log_msg}")
    if len(pipeline_progress["logs"]) > 50:
        pipeline_progress["logs"] = pipeline_progress["logs"][-50:]
    for k, v in kwargs.items():
        if k in pipeline_progress:
            pipeline_progress[k] = v

class IntelligencePipeline:
    def __init__(
        self,
        target_startups: int = 1000,
        target_products: int = 1000,
        target_papers: int = 1000,
        rolling_window_hours: int = 24
    ):
        self.target_startups = target_startups
        self.target_products = target_products
        self.target_papers = target_papers
        self.rolling_window_hours = rolling_window_hours
        self.run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    async def execute(self) -> Dict[str, Any]:
        start_time = datetime.now(timezone.utc)
        pipeline_progress["is_running"] = True
        pipeline_progress["run_id"] = self.run_id
        pipeline_progress["logs"] = []
        pipeline_progress["error"] = None

        logger.info(f"=== Starting AI Intelligence Pipeline [{self.run_id}] ===")
        set_stage(1, "Initializing Pipeline", 5, "Initializing SQLite WAL database and schema verification...")

        # 1. Initialize DB
        repo.init_db()

        collected_counts = {}
        validated_counts = {}
        saved_counts = {}
        total_fetched = 0
        total_saved = 0

        try:
            async with aiohttp.ClientSession() as session:
                # Stage 2: Startups
                set_stage(2, "Fetching AI Startups", 18, f"Harvesting startups from GitHub AI Orgs & Curated directory (target: {self.target_startups})...")
                startup_crawler = StartupCrawler(target_records=self.target_startups)
                raw_startups = await startup_crawler.crawl(session)
                collected_counts["startups"] = len(raw_startups)
                total_fetched += len(raw_startups)

                # Stage 3: Products
                set_stage(3, "Fetching AI Products & Models", 32, f"Harvesting open-source models & products from Hugging Face Hub (target: {self.target_products})...")
                product_crawler = ProductCrawler(target_records=self.target_products)
                raw_products = await product_crawler.crawl(session)
                collected_counts["products"] = len(raw_products)
                total_fetched += len(raw_products)

                # Stage 4: Research Papers
                set_stage(4, "Collecting Research Publications", 46, f"Querying ArXiv API for cs.AI, cs.LG, cs.CL, cs.CV preprints (target: {self.target_papers})...")
                research_crawler = ResearchCrawler(target_records=self.target_papers)
                raw_papers = await research_crawler.crawl(session)
                collected_counts["research_papers"] = len(raw_papers)
                total_fetched += len(raw_papers)

                # Stage 5: Jobs
                set_stage(5, "Fetching AI Job Postings", 58, "Querying Jobicy, Arbeitnow, and Remotive APIs for AI/ML positions (strict 24h filter)...")
                job_crawler = JobCrawler(rolling_window_hours=self.rolling_window_hours)
                raw_jobs = await job_crawler.crawl(session)
                collected_counts["jobs"] = len(raw_jobs)
                total_fetched += len(raw_jobs)

                # Stage 6: News
                set_stage(6, "Collecting AI Industry News", 68, "Gathering verified 24h news from Hacker News Algolia, Google News RSS, and TechCrunch...")
                news_crawler = NewsCrawler(rolling_window_hours=self.rolling_window_hours)
                raw_news = await news_crawler.crawl(session)
                collected_counts["news"] = len(raw_news)
                total_fetched += len(raw_news)

            # Stage 7: Entity Resolution
            set_stage(7, "Normalizing Canonical Entities", 78, "Normalizing company, startup, and model entities using RapidFuzz & suffix stripping...")
            mapping_records = []
            for norm_key, canonical in resolver._registry.items():
                _, rec = resolver.resolve(canonical, "Entity", "PipelineRegistry")
                mapping_records.append(rec)
            saved_counts["entity_mappings"] = repo.save_entity_mappings_bulk(mapping_records)

            # Stage 8 & 9: Validation & Duplicate Detection
            set_stage(8, "Validating & Deduplicating Records", 86, "Executing Pydantic schema validation, URL verification, and duplicate screening...")
            
            valid_startups = [s for s in raw_startups if validator.validate_startup(s.model_dump())[0]]
            valid_products = [p for p in raw_products if validator.validate_product(p.model_dump())[0]]
            valid_papers = [p for p in raw_papers if validator.validate_research_paper(p.model_dump())[0]]
            valid_jobs = [j for j in raw_jobs if validator.validate_job(j.model_dump(), enforce_freshness=True)[0]]
            valid_news = [n for n in raw_news if validator.validate_news(n.model_dump(), enforce_freshness=True)[0]]

            # Stage 10: Store in Database
            set_stage(10, "Storing Data in Database", 92, "Persisting atomic batch inserts to SQLite WAL database...")
            saved_counts["startups"] = repo.save_startups_bulk(valid_startups)
            saved_counts["products"] = repo.save_products_bulk(valid_products)
            saved_counts["research_papers"] = repo.save_research_papers_bulk(valid_papers)
            saved_counts["jobs"] = repo.save_jobs_bulk(valid_jobs)
            saved_counts["news"] = repo.save_news_bulk(valid_news)

            total_saved = sum(saved_counts.values())

            # Stage 11: Generate Execution Report & Exports
            set_stage(11, "Generating Execution Report & Exports", 98, "Exporting 6 standardized CSV and JSONL tabs to data/processed/...")
            export_summary = exporter.export_all()

            end_time = datetime.now(timezone.utc)
            duration_seconds = (end_time - start_time).total_seconds()
            db_counts = repo.get_counts()

            summary = {
                "run_id": self.run_id,
                "started_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "duration_seconds": round(duration_seconds, 2),
                "status": "COMPLETED",
                "active_llm_providers": orchestrator.get_available_providers(),
                "collected_records": collected_counts,
                "validated_records": {
                    "startups": len(valid_startups),
                    "products": len(valid_products),
                    "research_papers": len(valid_papers),
                    "jobs": len(valid_jobs),
                    "news": len(valid_news)
                },
                "saved_in_db": db_counts,
                "validation_stats": validator.stats,
                "exports": export_summary
            }

            set_stage(11, "Pipeline Completed", 100, f"Pipeline finished successfully in {duration_seconds:.2f}s. All 6 datasets updated.", records_fetched=total_fetched, records_inserted=total_saved)
            logger.info(f"=== Pipeline [{self.run_id}] Finished in {duration_seconds:.2f}s ===")
            return summary

        except Exception as e:
            logger.error(f"Pipeline execution encountered error: {e}")
            pipeline_progress["error"] = str(e)
            set_stage(pipeline_progress["stage_index"], "Failed", pipeline_progress["progress_percent"], f"ERROR: {str(e)}")
            raise
        finally:
            pipeline_progress["is_running"] = False
