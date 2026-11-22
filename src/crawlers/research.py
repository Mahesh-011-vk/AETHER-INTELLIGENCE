import asyncio
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import aiohttp
from src.crawlers.base import BaseCrawler
from src.models.schemas import ResearchPaperRecord
from src.extractors.date_extractor import DateExtractor
from src.utils.logging import logger
from config.settings import settings

ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"

class ResearchCrawler(BaseCrawler):
    def __init__(self, target_records: int = 1000):
        super().__init__(source_name="ArXiv API", max_concurrency=2)
        self.target_records = target_records
        self.endpoint = "http://export.arxiv.org/api/query"

    async def crawl(self, session: aiohttp.ClientSession) -> List[ResearchPaperRecord]:
        logger.info(f"Starting ArXiv research paper crawl (target: {self.target_records}+)...")
        records: List[ResearchPaperRecord] = []
        raw_items: List[Dict[str, Any]] = []

        batch_size = 100
        start = 0
        categories = ["cs.AI", "cs.LG", "cs.CL", "cs.CV"]
        cat_query = "+OR+".join([f"cat:{c}" for c in categories])

        while len(records) < self.target_records:
            url = f"{self.endpoint}?search_query={cat_query}&start={start}&max_results={batch_size}&sortBy=submittedDate&sortOrder=descending"
            logger.info(f"Fetching ArXiv papers {start} to {start + batch_size}...")

            xml_text = await self.fetch_text(url, session, timeout_seconds=30)
            if not xml_text:
                logger.warning(f"Failed to fetch ArXiv page at start={start}. Retrying next offset...")
                start += batch_size
                await asyncio.sleep(3.0)
                if start > self.target_records * 2:
                    break
                continue

            try:
                root = ET.fromstring(xml_text)
                entries = root.findall(f"{ATOM_NS}entry")
                if not entries:
                    logger.info("No more ArXiv entries found.")
                    break

                for entry in entries:
                    id_elem = entry.find(f"{ATOM_NS}id")
                    title_elem = entry.find(f"{ATOM_NS}title")
                    summary_elem = entry.find(f"{ATOM_NS}summary")
                    published_elem = entry.find(f"{ATOM_NS}published")

                    if title_elem is None or not title_elem.text:
                        continue

                    raw_id = id_elem.text.strip() if id_elem is not None else ""
                    arxiv_id = raw_id.split("/abs/")[-1] if "/abs/" in raw_id else raw_id
                    arxiv_id = re.sub(r"v\d+$", "", arxiv_id)  # Remove version suffix like v1, v2

                    clean_title = re.sub(r"\s+", " ", title_elem.text).strip()
                    clean_abstract = re.sub(r"\s+", " ", summary_elem.text).strip() if summary_elem is not None else ""

                    # Authors
                    author_elems = entry.findall(f"{ATOM_NS}author")
                    authors = []
                    for a in author_elems:
                        name_elem = a.find(f"{ATOM_NS}name")
                        if name_elem is not None and name_elem.text:
                            authors.append(name_elem.text.strip())

                    # Categories
                    category_elems = entry.findall(f"{ATOM_NS}category")
                    all_categories = [c.get("term") for c in category_elems if c.get("term")]
                    primary_category = all_categories[0] if all_categories else "cs.AI"

                    # Publication date
                    pub_str = published_elem.text.strip() if published_elem is not None else None
                    pub_dt = DateExtractor.parse_datetime(pub_str) or datetime.now(timezone.utc)

                    # Scan for code repository URL in abstract
                    code_url = None
                    code_match = re.search(r"https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", clean_abstract)
                    if code_match:
                        code_url = code_match.group(0).rstrip(".,;)")

                    paper_url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else raw_id

                    paper_record = ResearchPaperRecord(
                        title=clean_title,
                        authors=authors,
                        abstract=clean_abstract,
                        arxiv_id=arxiv_id,
                        paper_url=paper_url,
                        published_date=pub_dt,
                        primary_category=primary_category,
                        categories=all_categories,
                        code_url=code_url,
                        citation_count=None,
                        source_name=self.source_name,
                        source_url=url,
                        collected_at=datetime.now(timezone.utc),
                        raw_evidence={"arxiv_raw_id": raw_id, "primary_category": primary_category}
                    )
                    records.append(paper_record)
                    raw_items.append({
                        "title": clean_title,
                        "arxiv_id": arxiv_id,
                        "authors": authors,
                        "url": paper_url,
                        "published": pub_str
                    })

                    if len(records) >= self.target_records:
                        break

                start += len(entries)
                # Polite ArXiv spacing
                await asyncio.sleep(2.0)

            except Exception as e:
                logger.warning(f"Error parsing ArXiv XML: {e}")
                start += batch_size
                await asyncio.sleep(2.0)

        self.save_raw_evidence("arxiv_research_papers", raw_items)
        logger.info(f"ArXiv crawl completed. Collected {len(records)} research papers.")
        return records

