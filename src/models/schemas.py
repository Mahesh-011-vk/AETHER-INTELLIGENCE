from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re

def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def validate_url_string(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return None
    return url

class BaseRecord(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    source_name: str = Field(..., description="Name of the legitimate data source")
    source_url: str = Field(..., description="URL of the original source")
    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when record was gathered in UTC"
    )
    raw_evidence: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Preserved raw evidence or payload from crawler"
    )

    @field_validator("collected_at", mode="after")
    @classmethod
    def check_utc(cls, v: datetime) -> datetime:
        return ensure_utc(v)

class StartupRecord(BaseRecord):
    name: str = Field(..., min_length=1, description="Company or startup name")
    canonical_name: Optional[str] = Field(default=None, description="Resolved canonical name")
    description: Optional[str] = Field(default=None, description="Brief startup description")
    website: Optional[str] = Field(default=None, description="Official website URL")
    founded_year: Optional[int] = Field(default=None, ge=1900, le=2100, description="Year founded")
    headquarters: Optional[str] = Field(default=None, description="Headquarters location (City, Country)")
    funding_stage: Optional[str] = Field(default=None, description="Funding stage, e.g. Seed, Series A")
    total_funding_usd: Optional[float] = Field(default=None, ge=0.0, description="Total funding in USD")
    focus_areas: List[str] = Field(default_factory=list, description="Core AI focus areas/tags")

    @field_validator("website", mode="before")
    @classmethod
    def clean_website(cls, v: Any) -> Optional[str]:
        return validate_url_string(str(v) if v else None)

class ProductRecord(BaseRecord):
    name: str = Field(..., min_length=1, description="Product or model name")
    canonical_name: Optional[str] = Field(default=None, description="Resolved canonical name")
    company_name: Optional[str] = Field(default=None, description="Vendor or parent company name")
    canonical_company_name: Optional[str] = Field(default=None, description="Resolved canonical vendor name")
    description: Optional[str] = Field(default=None, description="Product overview and capabilities")
    product_url: Optional[str] = Field(default=None, description="Official product URL")
    category: Optional[str] = Field(default=None, description="Product category (e.g. LLM, Agent, Vision)")
    pricing_model: Optional[str] = Field(
        default="Unknown",
        description="Pricing model (Free, Freemium, Paid, Open Source, Enterprise, Contact Sales, Unknown)"
    )
    github_repo_url: Optional[str] = Field(default=None, description="Repository URL if open-source")
    github_stars: Optional[int] = Field(default=None, ge=0, description="GitHub star count")
    github_forks: Optional[int] = Field(default=None, ge=0, description="GitHub fork count")

    @field_validator("product_url", "github_repo_url", mode="before")
    @classmethod
    def clean_urls(cls, v: Any) -> Optional[str]:
        return validate_url_string(str(v) if v else None)

class ResearchPaperRecord(BaseRecord):
    title: str = Field(..., min_length=2, description="Paper title")
    authors: List[str] = Field(default_factory=list, description="List of paper authors")
    abstract: Optional[str] = Field(default=None, description="Full or executive abstract")
    arxiv_id: Optional[str] = Field(default=None, description="ArXiv ID (e.g., 2401.12345)")
    paper_url: str = Field(..., description="Link to paper landing page or PDF")
    published_date: datetime = Field(..., description="Original publication date in UTC")
    primary_category: str = Field(..., description="Primary classification, e.g. cs.AI, cs.LG, cs.CL")
    categories: List[str] = Field(default_factory=list, description="All associated categories")
    code_url: Optional[str] = Field(default=None, description="Official code repository if linked")
    citation_count: Optional[int] = Field(default=None, ge=0, description="Citation count if available")

    @field_validator("published_date", mode="after")
    @classmethod
    def check_pub_utc(cls, v: datetime) -> datetime:
        return ensure_utc(v)

    @field_validator("paper_url", "code_url", mode="before")
    @classmethod
    def clean_paper_urls(cls, v: Any) -> Optional[str]:
        return validate_url_string(str(v) if v else None)

class JobRecord(BaseRecord):
    job_title: str = Field(..., min_length=2, description="Job title")
    company_name: str = Field(..., min_length=1, description="Hiring organization")
    canonical_company_name: Optional[str] = Field(default=None, description="Resolved canonical company name")
    location: Optional[str] = Field(default="Remote", description="Job location")
    remote_eligibility: str = Field(default="Remote", description="Remote, Hybrid, On-site, or Unknown")
    job_url: str = Field(..., description="Direct link to job posting")
    published_at: datetime = Field(..., description="Confirmed posting timestamp in UTC")
    salary_range: Optional[str] = Field(default=None, description="Compensation range if listed")
    description: Optional[str] = Field(default=None, description="Job description or requirements summary")

    @field_validator("published_at", mode="after")
    @classmethod
    def check_job_utc(cls, v: datetime) -> datetime:
        return ensure_utc(v)

    @field_validator("job_url", mode="before")
    @classmethod
    def clean_job_url(cls, v: Any) -> str:
        clean = validate_url_string(str(v) if v else None)
        if not clean:
            raise ValueError(f"Invalid job URL: {v}")
        return clean

class NewsRecord(BaseRecord):
    title: str = Field(..., min_length=3, description="Article title")
    article_url: str = Field(..., description="Direct URL to news article")
    published_at: datetime = Field(..., description="Publication timestamp in UTC")
    summary: Optional[str] = Field(default=None, description="Structured summary of the story")
    key_entities: List[str] = Field(default_factory=list, description="Mentioned companies, products, people")
    sentiment_category: Optional[str] = Field(default=None, description="Category or sentiment tag")

    @field_validator("published_at", mode="after")
    @classmethod
    def check_news_utc(cls, v: datetime) -> datetime:
        return ensure_utc(v)

    @field_validator("article_url", mode="before")
    @classmethod
    def clean_news_url(cls, v: Any) -> str:
        clean = validate_url_string(str(v) if v else None)
        if not clean:
            raise ValueError(f"Invalid article URL: {v}")
        return clean

class EntityMappingRecord(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    raw_name: str = Field(..., min_length=1, description="Raw entity name from source")
    canonical_name: str = Field(..., min_length=1, description="Resolved canonical entity name")
    entity_type: str = Field(..., description="Entity category: Startup, Company, Product")
    source: str = Field(..., description="Source dataset or crawler name")
    confidence_score: float = Field(..., ge=0.0, le=100.0, description="Resolution confidence percentage (0-100)")
    resolution_method: str = Field(..., description="Method used: Exact, RuleNormalized, RapidFuzz, LLM")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("timestamp", mode="after")
    @classmethod
    def check_map_utc(cls, v: datetime) -> datetime:
        return ensure_utc(v)

