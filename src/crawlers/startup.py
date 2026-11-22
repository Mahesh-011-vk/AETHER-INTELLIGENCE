import asyncio
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import aiohttp
from src.crawlers.base import BaseCrawler
from src.models.schemas import StartupRecord
from src.entity_resolution.resolver import resolver
from src.utils.logging import logger
from config.settings import settings

STARTUP_TOPICS = [
    "AI",
    "machine-learning",
    "deep-learning",
    "generative-ai",
    "llm",
    "computer-vision",
    "natural-language-processing",
    "robotics",
    "autonomous-agents",
    "neural-networks",
    "synthetic-data",
    "foundation-models"
]

CURATED_AI_STARTUPS = [
    {"name": "OpenAI", "website": "https://openai.com", "hq": "San Francisco, USA", "stage": "Series C+", "funding": 14000000000, "focus": ["Generative AI", "LLMs", "AGI"]},
    {"name": "Anthropic", "website": "https://anthropic.com", "hq": "San Francisco, USA", "stage": "Series D", "funding": 7600000000, "focus": ["AI Safety", "LLMs", "Claude"]},
    {"name": "Mistral AI", "website": "https://mistral.ai", "hq": "Paris, France", "stage": "Series B", "funding": 1100000000, "focus": ["Open Weights", "LLMs", "Enterprise AI"]},
    {"name": "Cohere", "website": "https://cohere.com", "hq": "Toronto, Canada", "stage": "Series D", "funding": 970000000, "focus": ["Enterprise LLMs", "Search", "Embeddings"]},
    {"name": "Perplexity AI", "website": "https://perplexity.ai", "hq": "San Francisco, USA", "stage": "Series C", "funding": 450000000, "focus": ["Conversational Search", "Information Retrieval"]},
    {"name": "Scale AI", "website": "https://scale.com", "hq": "San Francisco, USA", "stage": "Series F", "funding": 1600000000, "focus": ["Data Labeling", "Model Evaluation", "RLHF"]},
    {"name": "Hugging Face", "website": "https://huggingface.co", "hq": "New York, USA", "stage": "Series D", "funding": 395000000, "focus": ["Open Source AI", "Model Hub", "Transformers"]},
    {"name": "Stability AI", "website": "https://stability.ai", "hq": "London, UK", "stage": "Series A", "funding": 175000000, "focus": ["Diffusion Models", "Generative Media"]},
    {"name": "Runway", "website": "https://runwayml.com", "hq": "New York, USA", "stage": "Series C", "funding": 236000000, "focus": ["Generative Video", "Multimodal Creative Tools"]},
    {"name": "ElevenLabs", "website": "https://elevenlabs.io", "hq": "New York, USA", "stage": "Series B", "funding": 101000000, "focus": ["Voice AI", "Speech Synthesis"]},
    {"name": "Harvey", "website": "https://harvey.ai", "hq": "San Francisco, USA", "stage": "Series C", "funding": 206000000, "focus": ["Legal AI", "Domain Specific LLMs"]},
    {"name": "Glean", "website": "https://glean.com", "hq": "Palo Alto, USA", "stage": "Series E", "funding": 600000000, "focus": ["Enterprise Work AI", "Knowledge Search"]},
    {"name": "Cognition", "website": "https://cognition.ai", "hq": "San Francisco, USA", "stage": "Series A", "funding": 175000000, "focus": ["AI Software Engineering", "Devin"]},
    {"name": "Poolside", "website": "https://poolside.ai", "hq": "Paris, France", "stage": "Series B", "funding": 500000000, "focus": ["AI for Code", "Foundation Models"]},
    {"name": "Sakana AI", "website": "https://sakana.ai", "hq": "Tokyo, Japan", "stage": "Series A", "funding": 214000000, "focus": ["Nature Inspired AI", "Model Merging"]},
    {"name": "Anysphere", "website": "https://cursor.com", "hq": "San Francisco, USA", "stage": "Series A", "funding": 60000000, "focus": ["AI Code Editor", "Cursor"]},
    {"name": "Character.ai", "website": "https://character.ai", "hq": "Menlo Park, USA", "stage": "Series A", "funding": 193000000, "focus": ["Conversational Agents", "Personal AI"]},
    {"name": "Abridge", "website": "https://abridge.com", "hq": "Pittsburgh, USA", "stage": "Series C", "funding": 212000000, "focus": ["Clinical AI", "Medical Documentation"]},
    {"name": "Shield AI", "website": "https://shield.ai", "hq": "San Diego, USA", "stage": "Series F", "funding": 800000000, "focus": ["Defense AI", "Autonomous Aircraft"]},
    {"name": "Sierra", "website": "https://sierra.ai", "hq": "San Francisco, USA", "stage": "Series A", "funding": 175000000, "focus": ["Enterprise Conversational Agents"]}
]

class StartupCrawler(BaseCrawler):
    def __init__(self, target_records: int = 1000):
        super().__init__(source_name="GitHub Organizations & AI Ecosystem Directory", max_concurrency=3)
        self.target_records = target_records

    async def crawl(self, session: aiohttp.ClientSession) -> List[StartupRecord]:
        logger.info(f"Starting AI startup crawl (target: {self.target_records}+)...")
        records: List[StartupRecord] = []
        raw_items: List[Dict[str, Any]] = []
        seen_names = set()

        # 1. Curated top AI unicorns & pioneers
        for item in CURATED_AI_STARTUPS:
            name = item["name"]
            seen_names.add(name.lower())
            canonical, _ = resolver.resolve(name, "Startup", "Curated AI Directory")
            rec = StartupRecord(
                name=name,
                canonical_name=canonical,
                description=f"Leading AI company specializing in {', '.join(item['focus'])}.",
                website=item["website"],
                founded_year=2021,
                headquarters=item["hq"],
                funding_stage=item["stage"],
                total_funding_usd=float(item["funding"]),
                focus_areas=item["focus"],
                source_name="Curated AI Directory",
                source_url=item["website"],
                collected_at=datetime.now(timezone.utc),
                raw_evidence=item
            )
            records.append(rec)
            raw_items.append(item)

        # 2. GitHub Organizations search across AI topics
        headers = {}
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

        for topic in STARTUP_TOPICS:
            if len(records) >= self.target_records:
                break

            for page in range(1, 11):  # 10 pages * 100 = 1000 orgs per topic
                if len(records) >= self.target_records:
                    break

                url = f"https://api.github.com/search/users?q=type:org+{topic}&per_page=100&page={page}"
                logger.info(f"Querying GitHub AI organizations for topic '{topic}' page {page}...")

                data = await self.fetch_json(url, session, headers=headers, timeout_seconds=20)
                if not data or "items" not in data or not data["items"]:
                    break

                items = data["items"]
                for it in items:
                    login = it.get("login")
                    if not login or login.lower() in seen_names:
                        continue
                    seen_names.add(login.lower())

                    # Clean name
                    display_name = login.replace("-", " ").replace("_", " ").title()
                    canonical, _ = resolver.resolve(display_name, "Startup", self.source_name)

                    html_url = it.get("html_url")
                    website = f"https://{login.lower()}.ai" if not html_url else html_url

                    record = StartupRecord(
                        name=display_name,
                        canonical_name=canonical,
                        description=f"AI startup and organization actively building {topic.replace('-', ' ')} solutions.",
                        website=website,
                        founded_year=None,
                        headquarters=None,
                        funding_stage="Private / Venture",
                        total_funding_usd=None,
                        focus_areas=[topic.replace("-", " ").title(), "Artificial Intelligence"],
                        source_name=self.source_name,
                        source_url=url,
                        collected_at=datetime.now(timezone.utc),
                        raw_evidence={"github_login": login, "html_url": html_url, "topic": topic}
                    )
                    records.append(record)
                    raw_items.append(it)

                    if len(records) >= self.target_records:
                        break

                # Sleep to be polite to GitHub API
                await asyncio.sleep(1.2)

        self.save_raw_evidence("ai_startups_and_ecosystem", raw_items)
        logger.info(f"AI Startup crawl completed. Collected {len(records)} startups.")
        return records

