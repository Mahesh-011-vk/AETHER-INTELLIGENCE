import asyncio
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import aiohttp
from src.crawlers.base import BaseCrawler
from src.models.schemas import JobRecord
from src.extractors.date_extractor import DateExtractor
from src.entity_resolution.resolver import resolver
from src.utils.logging import logger

AI_JOB_KEYWORDS = [
    r"\bai\b",
    r"\bml\b",
    r"\bmachine learning\b",
    r"\bdeep learning\b",
    r"\bllm\b",
    r"\bdata scien",
    r"\bnlp\b",
    r"\bcomputer vision\b",
    r"\bartificial intelligence\b",
    r"\bprompt engineer",
    r"\bresearch scientist\b",
    r"\balgorithm\b",
    r"\bgenai\b",
    r"\bgenerative ai\b"
]

class JobCrawler(BaseCrawler):
    def __init__(self, rolling_window_hours: int = 24):
        super().__init__(source_name="Jobicy & Arbeitnow & Remotive", max_concurrency=3)
        self.rolling_window_hours = rolling_window_hours

    def _is_ai_relevant(self, title: str, description: str = "") -> bool:
        combined = f"{title} {description}".lower()
        return any(re.search(pat, combined) for pat in AI_JOB_KEYWORDS)

    async def crawl(self, session: aiohttp.ClientSession) -> List[JobRecord]:
        logger.info(f"Starting AI jobs crawl (strict {self.rolling_window_hours}h freshness window)...")
        records: List[JobRecord] = []
        raw_items: List[Dict[str, Any]] = []
        seen_keys = set()

        # 1. Jobicy Remote Jobs API
        for tag in ["ai", "machine-learning", "data-science", "dev"]:
            url = f"https://jobicy.com/api/v2/remote-jobs?count=50&tag={tag}"
            logger.info(f"Fetching Jobicy jobs for tag '{tag}'...")
            data = await self.fetch_json(url, session, timeout_seconds=20)
            if data and isinstance(data, dict) and "jobs" in data:
                for j in data["jobs"]:
                    title = j.get("jobTitle", "").strip()
                    desc = j.get("jobDescription", "")
                    if not self._is_ai_relevant(title, desc):
                        continue

                    pub_str = j.get("pubDate")
                    pub_dt = DateExtractor.parse_datetime(pub_str)
                    if not pub_dt or not DateExtractor.is_within_rolling_window(pub_dt, hours=self.rolling_window_hours):
                        continue

                    company = j.get("companyName", "Tech Company").strip()
                    job_url = j.get("url") or j.get("jobUrl", "")
                    if not job_url:
                        continue

                    dedup_key = f"{company.lower()}::{title.lower()}"
                    if dedup_key in seen_keys:
                        continue
                    seen_keys.add(dedup_key)

                    canonical_company, _ = resolver.resolve(company, "Company", "Jobicy")

                    record = JobRecord(
                        job_title=title,
                        company_name=company,
                        canonical_company_name=canonical_company,
                        location=j.get("jobGeo", "Remote"),
                        remote_eligibility="Remote",
                        job_url=job_url,
                        published_at=pub_dt,
                        salary_range=f"{j.get('annualSalaryMin', '')}-{j.get('annualSalaryMax', '')} {j.get('salaryCurrency', '')}".strip() or None,
                        description=f"AI/ML role at {company}. Industry: {j.get('jobIndustry', 'Technology')}.",
                        source_name="Jobicy API",
                        source_url=url,
                        collected_at=datetime.now(timezone.utc),
                        raw_evidence=j
                    )
                    records.append(record)
                    raw_items.append(j)

            await asyncio.sleep(0.5)

        # 2. Arbeitnow Free Job Board API
        arbeit_url = "https://www.arbeitnow.com/api/job-board-api"
        logger.info("Fetching Arbeitnow job board...")
        arb_data = await self.fetch_json(arbeit_url, session, timeout_seconds=20)
        if arb_data and isinstance(arb_data, dict) and "data" in arb_data:
            for j in arb_data["data"]:
                title = j.get("title", "").strip()
                desc = j.get("description", "")
                if not self._is_ai_relevant(title, desc):
                    continue

                created_at = j.get("created_at")
                pub_dt = DateExtractor.parse_datetime(created_at)
                if not pub_dt or not DateExtractor.is_within_rolling_window(pub_dt, hours=self.rolling_window_hours):
                    continue

                company = j.get("company_name", "Tech Company").strip()
                job_url = j.get("url", "")
                if not job_url:
                    continue

                dedup_key = f"{company.lower()}::{title.lower()}"
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)

                canonical_company, _ = resolver.resolve(company, "Company", "Arbeitnow")

                record = JobRecord(
                    job_title=title,
                    company_name=company,
                    canonical_company_name=canonical_company,
                    location=j.get("location", "Remote"),
                    remote_eligibility="Remote" if j.get("remote") else "Hybrid/On-site",
                    job_url=job_url,
                    published_at=pub_dt,
                    salary_range=None,
                    description=f"AI position at {company}. Location: {j.get('location')}.",
                    source_name="Arbeitnow API",
                    source_url=arbeit_url,
                    collected_at=datetime.now(timezone.utc),
                    raw_evidence=j
                )
                records.append(record)
                raw_items.append(j)

        # 3. Remotive API
        remotive_url = "https://remotive.com/api/remote-jobs?category=software-dev&search=AI"
        logger.info("Fetching Remotive AI jobs...")
        rem_data = await self.fetch_json(remotive_url, session, timeout_seconds=20)
        if rem_data and isinstance(rem_data, dict) and "jobs" in rem_data:
            for j in rem_data["jobs"]:
                title = j.get("title", "").strip()
                desc = j.get("description", "")
                if not self._is_ai_relevant(title, desc):
                    continue

                pub_str = j.get("publication_date")
                pub_dt = DateExtractor.parse_datetime(pub_str)
                if not pub_dt or not DateExtractor.is_within_rolling_window(pub_dt, hours=self.rolling_window_hours):
                    continue

                company = j.get("company_name", "Tech Company").strip()
                job_url = j.get("url", "")
                if not job_url:
                    continue

                dedup_key = f"{company.lower()}::{title.lower()}"
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)

                canonical_company, _ = resolver.resolve(company, "Company", "Remotive")

                record = JobRecord(
                    job_title=title,
                    company_name=company,
                    canonical_company_name=canonical_company,
                    location=j.get("candidate_required_location", "Remote"),
                    remote_eligibility="Remote",
                    job_url=job_url,
                    published_at=pub_dt,
                    salary_range=j.get("salary") or None,
                    description=f"AI/ML engineering role at {company}.",
                    source_name="Remotive API",
                    source_url=remotive_url,
                    collected_at=datetime.now(timezone.utc),
                    raw_evidence=j
                )
                records.append(record)
                raw_items.append(j)

        self.save_raw_evidence("ai_jobs_verified_24h", raw_items)
        logger.info(f"AI Jobs crawl completed. Collected {len(records)} verified jobs within 24h window.")
        return records

