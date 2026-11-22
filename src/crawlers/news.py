import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import aiohttp
import feedparser
from src.crawlers.base import BaseCrawler
from src.models.schemas import NewsRecord
from src.extractors.date_extractor import DateExtractor
from src.llm.orchestrator import orchestrator
from src.utils.logging import logger

NEWS_RSS_FEEDS = [
    {"name": "Google News AI", "url": "https://news.google.com/rss/search?q=Artificial+Intelligence+when:1d&hl=en-US&gl=US&ceid=US:en"},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "OpenAI News", "url": "https://openai.com/news/rss.xml"},
    {"name": "MIT Tech Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"}
]

class NewsCrawler(BaseCrawler):
    def __init__(self, rolling_window_hours: int = 24):
        super().__init__(source_name="AI Multi-Source News Aggregator", max_concurrency=4)
        self.rolling_window_hours = rolling_window_hours

    async def crawl(self, session: aiohttp.ClientSession) -> List[NewsRecord]:
        logger.info(f"Starting AI news crawl (strict {self.rolling_window_hours}h freshness window)...")
        records: List[NewsRecord] = []
        raw_items: List[Dict[str, Any]] = []
        seen_urls = set()

        now = datetime.now(timezone.utc)
        since_ts = int((now - timedelta(hours=self.rolling_window_hours)).timestamp())

        # 1. Hacker News Algolia Realtime AI Stories
        hn_url = f"https://hn.algolia.com/api/v1/search_by_date?tags=story&query=AI&numericFilters=created_at_i>{since_ts}&hitsPerPage=100"
        logger.info("Fetching Hacker News AI stories from past 24 hours...")
        hn_data = await self.fetch_json(hn_url, session, timeout_seconds=20)
        if hn_data and isinstance(hn_data, dict) and "hits" in hn_data:
            for hit in hn_data["hits"]:
                title = hit.get("title", "").strip()
                article_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                created_at_str = hit.get("created_at")

                if not title or not article_url or article_url in seen_urls:
                    continue

                pub_dt = DateExtractor.parse_datetime(created_at_str)
                if not pub_dt or not DateExtractor.is_within_rolling_window(pub_dt, hours=self.rolling_window_hours):
                    continue

                seen_urls.add(article_url)
                record = NewsRecord(
                    title=title,
                    source_name="Hacker News AI Community",
                    source_url=hn_url,
                    article_url=article_url,
                    published_at=pub_dt,
                    summary=f"Community reported discussion on '{title}'. Points: {hit.get('points', 0)}, Comments: {hit.get('num_comments', 0)}.",
                    key_entities=["AI", "Hacker News"],
                    sentiment_category="Discussion / Technical",
                    collected_at=datetime.now(timezone.utc),
                    raw_evidence=hit
                )
                records.append(record)
                raw_items.append(hit)

        # 2. RSS Feeds with strict 24-hour verification
        for feed_info in NEWS_RSS_FEEDS:
            name = feed_info["name"]
            url = feed_info["url"]
            logger.info(f"Fetching RSS feed '{name}'...")

            xml_content = await self.fetch_text(url, session, timeout_seconds=20)
            if not xml_content:
                continue

            try:
                feed = feedparser.parse(xml_content)
                for entry in feed.entries:
                    title = getattr(entry, "title", "").strip()
                    link = getattr(entry, "link", "").strip()
                    if not title or not link or link in seen_urls:
                        continue

                    # Try published, updated, or created date
                    pub_str = (
                        getattr(entry, "published", None) or
                        getattr(entry, "updated", None) or
                        getattr(entry, "created", None)
                    )
                    pub_dt = DateExtractor.parse_datetime(pub_str)
                    if not pub_dt or not DateExtractor.is_within_rolling_window(pub_dt, hours=self.rolling_window_hours):
                        continue

                    seen_urls.add(link)
                    summary = getattr(entry, "summary", "") or f"AI industry development: {title}"
                    # Clean html tags from summary
                    clean_summary = summary.replace("<p>", "").replace("</p>", "").replace("<b>", "").replace("</b>", "").strip()
                    if len(clean_summary) > 400:
                        clean_summary = clean_summary[:397] + "..."

                    record = NewsRecord(
                        title=title,
                        source_name=name,
                        source_url=url,
                        article_url=link,
                        published_at=pub_dt,
                        summary=clean_summary,
                        key_entities=["Artificial Intelligence"],
                        sentiment_category="Industry News",
                        collected_at=datetime.now(timezone.utc),
                        raw_evidence={"feed_name": name, "raw_published": pub_str}
                    )
                    records.append(record)
                    raw_items.append({"title": title, "link": link, "published": pub_str, "feed": name})

            except Exception as e:
                logger.warning(f"Error parsing feed '{name}': {e}")

            await asyncio.sleep(0.5)

        self.save_raw_evidence("ai_news_verified_24h", raw_items)
        logger.info(f"AI News crawl completed. Collected {len(records)} verified news articles within 24h window.")
        return records
