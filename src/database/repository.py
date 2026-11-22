import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.database.connection import get_db_connection
from src.models.schemas import (
    StartupRecord,
    ProductRecord,
    ResearchPaperRecord,
    JobRecord,
    NewsRecord,
    EntityMappingRecord,
)
from src.utils.logging import logger

class IRepository(ABC):
    @abstractmethod
    def init_db(self) -> None:
        pass

    @abstractmethod
    def save_startup(self, record: StartupRecord) -> bool:
        pass

    @abstractmethod
    def save_startups_bulk(self, records: List[StartupRecord]) -> int:
        pass

    @abstractmethod
    def save_product(self, record: ProductRecord) -> bool:
        pass

    @abstractmethod
    def save_products_bulk(self, records: List[ProductRecord]) -> int:
        pass

    @abstractmethod
    def save_research_paper(self, record: ResearchPaperRecord) -> bool:
        pass

    @abstractmethod
    def save_research_papers_bulk(self, records: List[ResearchPaperRecord]) -> int:
        pass

    @abstractmethod
    def save_job(self, record: JobRecord) -> bool:
        pass

    @abstractmethod
    def save_jobs_bulk(self, records: List[JobRecord]) -> int:
        pass

    @abstractmethod
    def save_news(self, record: NewsRecord) -> bool:
        pass

    @abstractmethod
    def save_news_bulk(self, records: List[NewsRecord]) -> int:
        pass

    @abstractmethod
    def save_entity_mapping(self, record: EntityMappingRecord) -> bool:
        pass

    @abstractmethod
    def save_entity_mappings_bulk(self, records: List[EntityMappingRecord]) -> int:
        pass

    @abstractmethod
    def get_counts(self) -> Dict[str, int]:
        pass

    @abstractmethod
    def fetch_all(self, table_name: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_item_by_id(self, table_name: str, item_id: int) -> Optional[Dict[str, Any]]:
        valid_tables = ["startups", "products", "research_papers", "jobs", "news", "entity_mappings"]
        if table_name not in valid_tables:
            return None
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def query_startups(
        self,
        search: Optional[str] = None,
        stage: Optional[str] = None,
        min_funding: Optional[float] = None,
        sort_by: str = "total_funding_usd",
        sort_dir: str = "DESC",
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            clauses = ["1=1"]
            params = []
            if search:
                clauses.append("(name LIKE ? OR focus_areas LIKE ? OR description LIKE ?)")
                q = f"%{search}%"
                params.extend([q, q, q])
            if stage and stage != "all":
                clauses.append("funding_stage = ?")
                params.append(stage)
            if min_funding:
                clauses.append("total_funding_usd >= ?")
                params.append(min_funding)

            where_sql = " AND ".join(clauses)
            cursor.execute(f"SELECT COUNT(*) FROM startups WHERE {where_sql}", params)
            total = cursor.fetchone()[0]

            valid_sort = {
                "total_funding_usd": "total_funding_usd",
                "name": "name",
                "funding_stage": "funding_stage",
                "id": "id"
            }
            order_col = valid_sort.get(sort_by, "total_funding_usd")
            direction = "ASC" if sort_dir.upper() == "ASC" else "DESC"
            offset = max(0, (page - 1) * page_size)

            cursor.execute(
                f"SELECT * FROM startups WHERE {where_sql} ORDER BY {order_col} {direction} NULLS LAST LIMIT ? OFFSET ?",
                params + [page_size, offset]
            )
            rows = [dict(r) for r in cursor.fetchall()]
            return {"items": rows, "total": total, "page": page, "page_size": page_size}

    def query_products(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        pricing: Optional[str] = None,
        sort_by: str = "github_stars",
        sort_dir: str = "DESC",
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            clauses = ["1=1"]
            params = []
            if search:
                clauses.append("(name LIKE ? OR company_name LIKE ? OR description LIKE ?)")
                q = f"%{search}%"
                params.extend([q, q, q])
            if category and category != "all":
                clauses.append("category LIKE ?")
                params.append(f"%{category}%")
            if pricing and pricing != "all":
                clauses.append("pricing_model = ?")
                params.append(pricing)

            where_sql = " AND ".join(clauses)
            cursor.execute(f"SELECT COUNT(*) FROM products WHERE {where_sql}", params)
            total = cursor.fetchone()[0]

            valid_sort = {
                "github_stars": "github_stars",
                "github_forks": "github_forks",
                "name": "name",
                "company_name": "company_name"
            }
            order_col = valid_sort.get(sort_by, "github_stars")
            direction = "ASC" if sort_dir.upper() == "ASC" else "DESC"
            offset = max(0, (page - 1) * page_size)

            cursor.execute(
                f"SELECT * FROM products WHERE {where_sql} ORDER BY {order_col} {direction} NULLS LAST LIMIT ? OFFSET ?",
                params + [page_size, offset]
            )
            rows = [dict(r) for r in cursor.fetchall()]
            return {"items": rows, "total": total, "page": page, "page_size": page_size}

    def query_papers(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        sort_by: str = "published_date",
        sort_dir: str = "DESC",
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            clauses = ["1=1"]
            params = []
            if search:
                clauses.append("(title LIKE ? OR abstract LIKE ? OR authors LIKE ?)")
                q = f"%{search}%"
                params.extend([q, q, q])
            if category and category != "all":
                clauses.append("primary_category = ?")
                params.append(category)

            where_sql = " AND ".join(clauses)
            cursor.execute(f"SELECT COUNT(*) FROM research_papers WHERE {where_sql}", params)
            total = cursor.fetchone()[0]

            direction = "ASC" if sort_dir.upper() == "ASC" else "DESC"
            offset = max(0, (page - 1) * page_size)

            cursor.execute(
                f"SELECT * FROM research_papers WHERE {where_sql} ORDER BY published_date {direction} LIMIT ? OFFSET ?",
                params + [page_size, offset]
            )
            rows = [dict(r) for r in cursor.fetchall()]
            return {"items": rows, "total": total, "page": page, "page_size": page_size}

    def query_jobs(
        self,
        search: Optional[str] = None,
        remote_only: bool = False,
        india_only: bool = False,
        sort_by: str = "published_at",
        sort_dir: str = "DESC",
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            clauses = ["1=1"]
            params = []
            if search:
                clauses.append("(job_title LIKE ? OR company_name LIKE ? OR description LIKE ?)")
                q = f"%{search}%"
                params.extend([q, q, q])
            if remote_only:
                clauses.append("remote_eligibility = 'Remote'")
            if india_only:
                clauses.append("(location LIKE '%India%' OR description LIKE '%India%' OR location = 'Remote')")

            where_sql = " AND ".join(clauses)
            cursor.execute(f"SELECT COUNT(*) FROM jobs WHERE {where_sql}", params)
            total = cursor.fetchone()[0]

            direction = "ASC" if sort_dir.upper() == "ASC" else "DESC"
            offset = max(0, (page - 1) * page_size)

            cursor.execute(
                f"SELECT * FROM jobs WHERE {where_sql} ORDER BY published_at {direction} LIMIT ? OFFSET ?",
                params + [page_size, offset]
            )
            rows = [dict(r) for r in cursor.fetchall()]
            return {"items": rows, "total": total, "page": page, "page_size": page_size}

    def query_news(
        self,
        search: Optional[str] = None,
        source: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            clauses = ["1=1"]
            params = []
            if search:
                clauses.append("(title LIKE ? OR summary LIKE ?)")
                q = f"%{search}%"
                params.extend([q, q])
            if source and source != "all":
                clauses.append("source_name = ?")
                params.append(source)

            where_sql = " AND ".join(clauses)
            cursor.execute(f"SELECT COUNT(*) FROM news WHERE {where_sql}", params)
            total = cursor.fetchone()[0]

            offset = max(0, (page - 1) * page_size)
            cursor.execute(
                f"SELECT * FROM news WHERE {where_sql} ORDER BY published_at DESC LIMIT ? OFFSET ?",
                params + [page_size, offset]
            )
            rows = [dict(r) for r in cursor.fetchall()]
            return {"items": rows, "total": total, "page": page, "page_size": page_size}

    def query_mappings(
        self,
        search: Optional[str] = None,
        min_confidence: Optional[float] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            clauses = ["1=1"]
            params = []
            if search:
                clauses.append("(raw_name LIKE ? OR canonical_name LIKE ?)")
                q = f"%{search}%"
                params.extend([q, q])
            if min_confidence:
                clauses.append("confidence_score >= ?")
                params.append(min_confidence)

            where_sql = " AND ".join(clauses)
            cursor.execute(f"SELECT COUNT(*) FROM entity_mappings WHERE {where_sql}", params)
            total = cursor.fetchone()[0]

            offset = max(0, (page - 1) * page_size)
            cursor.execute(
                f"SELECT * FROM entity_mappings WHERE {where_sql} ORDER BY id ASC LIMIT ? OFFSET ?",
                params + [page_size, offset]
            )
            rows = [dict(r) for r in cursor.fetchall()]
            return {"items": rows, "total": total, "page": page, "page_size": page_size}

    def get_analytics_summary(self) -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Startups by stage
            cursor.execute("""
                SELECT COALESCE(funding_stage, 'Unspecified') as stage, COUNT(*) as count, SUM(COALESCE(total_funding_usd, 0)) as total_funding
                FROM startups
                GROUP BY stage
                ORDER BY count DESC
                LIMIT 8
            """)
            startups_by_stage = [dict(r) for r in cursor.fetchall()]

            # Products by category
            cursor.execute("""
                SELECT COALESCE(category, 'General AI') as cat, COUNT(*) as count, SUM(COALESCE(github_stars, 0)) as total_likes
                FROM products
                GROUP BY cat
                ORDER BY count DESC
                LIMIT 8
            """)
            products_by_category = [dict(r) for r in cursor.fetchall()]

            # Research papers by primary category
            cursor.execute("""
                SELECT primary_category, COUNT(*) as count
                FROM research_papers
                GROUP BY primary_category
                ORDER BY count DESC
                LIMIT 6
            """)
            papers_by_category = [dict(r) for r in cursor.fetchall()]

            # Jobs by remote eligibility
            cursor.execute("""
                SELECT remote_eligibility, COUNT(*) as count
                FROM jobs
                GROUP BY remote_eligibility
            """)
            jobs_by_remote = [dict(r) for r in cursor.fetchall()]

            # News sources
            cursor.execute("""
                SELECT source_name, COUNT(*) as count
                FROM news
                GROUP BY source_name
                ORDER BY count DESC
                LIMIT 6
            """)
            news_by_source = [dict(r) for r in cursor.fetchall()]

            # Entity mappings confidence tiers
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN confidence_score >= 95 THEN 'High (95-100%)'
                        WHEN confidence_score >= 85 THEN 'Medium (85-94%)'
                        ELSE 'Review Needed (<85%)'
                    END as tier,
                    COUNT(*) as count
                FROM entity_mappings
                GROUP BY tier
            """)
            mappings_tiers = [dict(r) for r in cursor.fetchall()]

            return {
                "startups_by_stage": startups_by_stage,
                "products_by_category": products_by_category,
                "papers_by_category": papers_by_category,
                "jobs_by_remote": jobs_by_remote,
                "news_by_source": news_by_source,
                "mappings_tiers": mappings_tiers,
                "counts": self.get_counts()
            }

    def universal_search(self, q: str, limit_per_table: int = 5) -> Dict[str, Any]:
        if not q or len(q.strip()) < 2:
            return {"query": q, "results": {}}
        term = f"%{q.strip()}%"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            results = {}

            cursor.execute("SELECT id, name, funding_stage, headquarters, website FROM startups WHERE name LIKE ? OR description LIKE ? LIMIT ?", (term, term, limit_per_table))
            results["startups"] = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT id, name, company_name, category, product_url FROM products WHERE name LIKE ? OR company_name LIKE ? LIMIT ?", (term, term, limit_per_table))
            results["products"] = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT id, title, authors, primary_category, paper_url FROM research_papers WHERE title LIKE ? OR abstract LIKE ? LIMIT ?", (term, term, limit_per_table))
            results["papers"] = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT id, job_title, company_name, location, job_url FROM jobs WHERE job_title LIKE ? OR company_name LIKE ? LIMIT ?", (term, term, limit_per_table))
            results["jobs"] = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT id, title, source_name, article_url FROM news WHERE title LIKE ? OR summary LIKE ? LIMIT ?", (term, term, limit_per_table))
            results["news"] = [dict(r) for r in cursor.fetchall()]

            return {"query": q, "results": results}

    def log_error(self, component: str, error_message: str, details: Optional[Dict[str, Any]] = None) -> None:
        pass

class SQLiteRepository(IRepository):
    def init_db(self) -> None:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Startups Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS startups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                canonical_name TEXT,
                description TEXT,
                website TEXT,
                founded_year INTEGER,
                headquarters TEXT,
                funding_stage TEXT,
                total_funding_usd REAL,
                focus_areas TEXT,
                source_name TEXT NOT NULL,
                source_url TEXT NOT NULL,
                collected_at TEXT NOT NULL,
                raw_evidence TEXT,
                UNIQUE(name, website)
            );
            """)

            # Products Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                canonical_name TEXT,
                company_name TEXT,
                canonical_company_name TEXT,
                description TEXT,
                product_url TEXT,
                category TEXT,
                pricing_model TEXT,
                github_repo_url TEXT,
                github_stars INTEGER,
                github_forks INTEGER,
                source_name TEXT NOT NULL,
                source_url TEXT NOT NULL,
                collected_at TEXT NOT NULL,
                raw_evidence TEXT,
                UNIQUE(name, product_url)
            );
            """)

            # Research Papers Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT,
                abstract TEXT,
                arxiv_id TEXT,
                paper_url TEXT NOT NULL,
                published_date TEXT NOT NULL,
                primary_category TEXT NOT NULL,
                categories TEXT,
                code_url TEXT,
                citation_count INTEGER,
                source_name TEXT NOT NULL,
                source_url TEXT NOT NULL,
                collected_at TEXT NOT NULL,
                raw_evidence TEXT,
                UNIQUE(title, arxiv_id)
            );
            """)

            # Jobs Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT NOT NULL,
                company_name TEXT NOT NULL,
                canonical_company_name TEXT,
                location TEXT,
                remote_eligibility TEXT,
                job_url TEXT NOT NULL,
                published_at TEXT NOT NULL,
                salary_range TEXT,
                description TEXT,
                source_name TEXT NOT NULL,
                source_url TEXT NOT NULL,
                collected_at TEXT NOT NULL,
                raw_evidence TEXT,
                UNIQUE(company_name, job_title, job_url)
            );
            """)

            # News Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                article_url TEXT NOT NULL,
                published_at TEXT NOT NULL,
                summary TEXT,
                key_entities TEXT,
                sentiment_category TEXT,
                source_name TEXT NOT NULL,
                source_url TEXT NOT NULL,
                collected_at TEXT NOT NULL,
                raw_evidence TEXT,
                UNIQUE(title, article_url)
            );
            """)

            # Entity Mapping Log Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_name TEXT NOT NULL,
                canonical_name TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                source TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                resolution_method TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                UNIQUE(raw_name, entity_type)
            );
            """)

            # Ingestion Runs Log
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingestion_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                stats TEXT
            );
            """)

            # Error Logs
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component TEXT NOT NULL,
                error_message TEXT NOT NULL,
                details TEXT,
                timestamp TEXT NOT NULL
            );
            """)

            # Indexes for high performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_startups_name ON startups(name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_research_arxiv ON research_papers(arxiv_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_pub ON jobs(published_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_pub ON news(published_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mapping_raw ON entity_mappings(raw_name);")

            conn.commit()
            logger.info("Database schemas and indexes initialized successfully.")

    def save_startup(self, record: StartupRecord) -> bool:
        return self.save_startups_bulk([record]) > 0

    def save_startups_bulk(self, records: List[StartupRecord]) -> int:
        if not records:
            return 0
        inserted = 0
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for r in records:
                try:
                    cursor.execute("""
                    INSERT INTO startups (
                        name, canonical_name, description, website, founded_year,
                        headquarters, funding_stage, total_funding_usd, focus_areas,
                        source_name, source_url, collected_at, raw_evidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(name, website) DO UPDATE SET
                        canonical_name=COALESCE(excluded.canonical_name, startups.canonical_name),
                        description=COALESCE(excluded.description, startups.description),
                        total_funding_usd=COALESCE(excluded.total_funding_usd, startups.total_funding_usd),
                        funding_stage=COALESCE(excluded.funding_stage, startups.funding_stage);
                    """, (
                        r.name,
                        r.canonical_name,
                        r.description,
                        r.website,
                        r.founded_year,
                        r.headquarters,
                        r.funding_stage,
                        r.total_funding_usd,
                        json.dumps(r.focus_areas),
                        r.source_name,
                        r.source_url,
                        r.collected_at.isoformat(),
                        json.dumps(r.raw_evidence) if r.raw_evidence else None
                    ))
                    inserted += 1
                except sqlite3.Error as e:
                    logger.debug(f"Error inserting startup '{r.name}': {e}")
            conn.commit()
        return inserted

    def save_product(self, record: ProductRecord) -> bool:
        return self.save_products_bulk([record]) > 0

    def save_products_bulk(self, records: List[ProductRecord]) -> int:
        if not records:
            return 0
        inserted = 0
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for r in records:
                try:
                    cursor.execute("""
                    INSERT INTO products (
                        name, canonical_name, company_name, canonical_company_name,
                        description, product_url, category, pricing_model,
                        github_repo_url, github_stars, github_forks,
                        source_name, source_url, collected_at, raw_evidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(name, product_url) DO UPDATE SET
                        canonical_name=COALESCE(excluded.canonical_name, products.canonical_name),
                        company_name=COALESCE(excluded.company_name, products.company_name),
                        canonical_company_name=COALESCE(excluded.canonical_company_name, products.canonical_company_name),
                        github_stars=COALESCE(excluded.github_stars, products.github_stars),
                        github_forks=COALESCE(excluded.github_forks, products.github_forks);
                    """, (
                        r.name,
                        r.canonical_name,
                        r.company_name,
                        r.canonical_company_name,
                        r.description,
                        r.product_url,
                        r.category,
                        r.pricing_model,
                        r.github_repo_url,
                        r.github_stars,
                        r.github_forks,
                        r.source_name,
                        r.source_url,
                        r.collected_at.isoformat(),
                        json.dumps(r.raw_evidence) if r.raw_evidence else None
                    ))
                    inserted += 1
                except sqlite3.Error as e:
                    logger.debug(f"Error inserting product '{r.name}': {e}")
            conn.commit()
        return inserted

    def save_research_paper(self, record: ResearchPaperRecord) -> bool:
        return self.save_research_papers_bulk([record]) > 0

    def save_research_papers_bulk(self, records: List[ResearchPaperRecord]) -> int:
        if not records:
            return 0
        inserted = 0
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for r in records:
                try:
                    cursor.execute("""
                    INSERT INTO research_papers (
                        title, authors, abstract, arxiv_id, paper_url,
                        published_date, primary_category, categories, code_url,
                        citation_count, source_name, source_url, collected_at, raw_evidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(title, arxiv_id) DO UPDATE SET
                        code_url=COALESCE(excluded.code_url, research_papers.code_url),
                        citation_count=COALESCE(excluded.citation_count, research_papers.citation_count);
                    """, (
                        r.title,
                        json.dumps(r.authors),
                        r.abstract,
                        r.arxiv_id,
                        r.paper_url,
                        r.published_date.isoformat(),
                        r.primary_category,
                        json.dumps(r.categories),
                        r.code_url,
                        r.citation_count,
                        r.source_name,
                        r.source_url,
                        r.collected_at.isoformat(),
                        json.dumps(r.raw_evidence) if r.raw_evidence else None
                    ))
                    inserted += 1
                except sqlite3.Error as e:
                    logger.debug(f"Error inserting research paper '{r.title}': {e}")
            conn.commit()
        return inserted

    def save_job(self, record: JobRecord) -> bool:
        return self.save_jobs_bulk([record]) > 0

    def save_jobs_bulk(self, records: List[JobRecord]) -> int:
        if not records:
            return 0
        inserted = 0
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for r in records:
                try:
                    cursor.execute("""
                    INSERT INTO jobs (
                        job_title, company_name, canonical_company_name, location,
                        remote_eligibility, job_url, published_at, salary_range,
                        description, source_name, source_url, collected_at, raw_evidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(company_name, job_title, job_url) DO UPDATE SET
                        canonical_company_name=COALESCE(excluded.canonical_company_name, jobs.canonical_company_name);
                    """, (
                        r.job_title,
                        r.company_name,
                        r.canonical_company_name,
                        r.location,
                        r.remote_eligibility,
                        r.job_url,
                        r.published_at.isoformat(),
                        r.salary_range,
                        r.description,
                        r.source_name,
                        r.source_url,
                        r.collected_at.isoformat(),
                        json.dumps(r.raw_evidence) if r.raw_evidence else None
                    ))
                    inserted += 1
                except sqlite3.Error as e:
                    logger.debug(f"Error inserting job '{r.job_title}': {e}")
            conn.commit()
        return inserted

    def save_news(self, record: NewsRecord) -> bool:
        return self.save_news_bulk([record]) > 0

    def save_news_bulk(self, records: List[NewsRecord]) -> int:
        if not records:
            return 0
        inserted = 0
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for r in records:
                try:
                    cursor.execute("""
                    INSERT INTO news (
                        title, article_url, published_at, summary,
                        key_entities, sentiment_category, source_name, source_url,
                        collected_at, raw_evidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(title, article_url) DO UPDATE SET
                        summary=COALESCE(excluded.summary, news.summary);
                    """, (
                        r.title,
                        r.article_url,
                        r.published_at.isoformat(),
                        r.summary,
                        json.dumps(r.key_entities),
                        r.sentiment_category,
                        r.source_name,
                        r.source_url,
                        r.collected_at.isoformat(),
                        json.dumps(r.raw_evidence) if r.raw_evidence else None
                    ))
                    inserted += 1
                except sqlite3.Error as e:
                    logger.debug(f"Error inserting news '{r.title}': {e}")
            conn.commit()
        return inserted

    def save_entity_mapping(self, record: EntityMappingRecord) -> bool:
        return self.save_entity_mappings_bulk([record]) > 0

    def save_entity_mappings_bulk(self, records: List[EntityMappingRecord]) -> int:
        if not records:
            return 0
        inserted = 0
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for r in records:
                try:
                    cursor.execute("""
                    INSERT INTO entity_mappings (
                        raw_name, canonical_name, entity_type, source,
                        confidence_score, resolution_method, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(raw_name, entity_type) DO UPDATE SET
                        canonical_name=excluded.canonical_name,
                        confidence_score=excluded.confidence_score,
                        resolution_method=excluded.resolution_method,
                        timestamp=excluded.timestamp;
                    """, (
                        r.raw_name,
                        r.canonical_name,
                        r.entity_type,
                        r.source,
                        r.confidence_score,
                        r.resolution_method,
                        r.timestamp.isoformat()
                    ))
                    inserted += 1
                except sqlite3.Error as e:
                    logger.debug(f"Error inserting entity mapping '{r.raw_name}': {e}")
            conn.commit()
        return inserted

    def get_counts(self) -> Dict[str, int]:
        counts = {}
        tables = ["startups", "products", "research_papers", "jobs", "news", "entity_mappings"]
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for t in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {t}")
                counts[t] = cursor.fetchone()[0]
        return counts

    def fetch_all(self, table_name: str) -> List[Dict[str, Any]]:
        valid_tables = ["startups", "products", "research_papers", "jobs", "news", "entity_mappings"]
        if table_name not in valid_tables:
            raise ValueError(f"Invalid table name: {table_name}")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY id ASC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_item_by_id(self, table_name: str, item_id: int) -> Optional[Dict[str, Any]]:
        valid_tables = ["startups", "products", "research_papers", "jobs", "news", "entity_mappings"]
        if table_name not in valid_tables:
            return None
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def query_startups(
        self,
        search: Optional[str] = None,
        stage: Optional[str] = None,
        min_funding: Optional[float] = None,
        sort_by: str = "total_funding_usd",
        sort_dir: str = "DESC",
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            clauses = ["1=1"]
            params = []
            if search:
                clauses.append("(name LIKE ? OR focus_areas LIKE ? OR description LIKE ?)")
                q = f"%{search}%"
                params.extend([q, q, q])
            if stage and stage != "all":
                clauses.append("funding_stage = ?")
                params.append(stage)
            if min_funding:
                clauses.append("total_funding_usd >= ?")
                params.append(min_funding)

            where_sql = " AND ".join(clauses)
            cursor.execute(f"SELECT COUNT(*) FROM startups WHERE {where_sql}", params)
            total = cursor.fetchone()[0]

            valid_sort = {
                "total_funding_usd": "total_funding_usd",
                "name": "name",
                "funding_stage": "funding_stage",
                "id": "id"
            }
            order_col = valid_sort.get(sort_by, "total_funding_usd")
            direction = "ASC" if sort_dir.upper() == "ASC" else "DESC"
            offset = max(0, (page - 1) * page_size)

            cursor.execute(
                f"SELECT * FROM startups WHERE {where_sql} ORDER BY {order_col} {direction} NULLS LAST LIMIT ? OFFSET ?",
                params + [page_size, offset]
            )
            rows = [dict(r) for r in cursor.fetchall()]
            return {"items": rows, "total": total, "page": page, "page_size": page_size}

    def query_products(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        pricing: Optional[str] = None,
        sort_by: str = "github_stars",
        sort_dir: str = "DESC",
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            clauses = ["1=1"]
            params = []
            if search:
                clauses.append("(name LIKE ? OR company_name LIKE ? OR description LIKE ?)")
                q = f"%{search}%"
                params.extend([q, q, q])
            if category and category != "all":
                clauses.append("category LIKE ?")
                params.append(f"%{category}%")
            if pricing and pricing != "all":
                clauses.append("pricing_model = ?")
                params.append(pricing)

            where_sql = " AND ".join(clauses)
            cursor.execute(f"SELECT COUNT(*) FROM products WHERE {where_sql}", params)
            total = cursor.fetchone()[0]

            valid_sort = {
                "github_stars": "github_stars",
                "github_forks": "github_forks",
                "name": "name",
                "company_name": "company_name"
            }
            order_col = valid_sort.get(sort_by, "github_stars")
            direction = "ASC" if sort_dir.upper() == "ASC" else "DESC"
            offset = max(0, (page - 1) * page_size)

            cursor.execute(
                f"SELECT * FROM products WHERE {where_sql} ORDER BY {order_col} {direction} NULLS LAST LIMIT ? OFFSET ?",
                params + [page_size, offset]
            )
            rows = [dict(r) for r in cursor.fetchall()]
            return {"items": rows, "total": total, "page": page, "page_size": page_size}

    def query_papers(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        sort_by: str = "published_date",
        sort_dir: str = "DESC",
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            clauses = ["1=1"]
            params = []
            if search:
                clauses.append("(title LIKE ? OR abstract LIKE ? OR authors LIKE ?)")
                q = f"%{search}%"
                params.extend([q, q, q])
            if category and category != "all":
                clauses.append("primary_category = ?")
                params.append(category)

            where_sql = " AND ".join(clauses)
            cursor.execute(f"SELECT COUNT(*) FROM research_papers WHERE {where_sql}", params)
            total = cursor.fetchone()[0]

            direction = "ASC" if sort_dir.upper() == "ASC" else "DESC"
            offset = max(0, (page - 1) * page_size)

            cursor.execute(
                f"SELECT * FROM research_papers WHERE {where_sql} ORDER BY published_date {direction} LIMIT ? OFFSET ?",
                params + [page_size, offset]
            )
            rows = [dict(r) for r in cursor.fetchall()]
            return {"items": rows, "total": total, "page": page, "page_size": page_size}

    def query_jobs(
        self,
        search: Optional[str] = None,
        remote_only: bool = False,
        india_only: bool = False,
        sort_by: str = "published_at",
        sort_dir: str = "DESC",
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            clauses = ["1=1"]
            params = []
            if search:
                clauses.append("(job_title LIKE ? OR company_name LIKE ? OR description LIKE ?)")
                q = f"%{search}%"
                params.extend([q, q, q])
            if remote_only:
                clauses.append("remote_eligibility = 'Remote'")
            if india_only:
                clauses.append("(location LIKE '%India%' OR description LIKE '%India%' OR location = 'Remote')")

            where_sql = " AND ".join(clauses)
            cursor.execute(f"SELECT COUNT(*) FROM jobs WHERE {where_sql}", params)
            total = cursor.fetchone()[0]

            direction = "ASC" if sort_dir.upper() == "ASC" else "DESC"
            offset = max(0, (page - 1) * page_size)

            cursor.execute(
                f"SELECT * FROM jobs WHERE {where_sql} ORDER BY published_at {direction} LIMIT ? OFFSET ?",
                params + [page_size, offset]
            )
            rows = [dict(r) for r in cursor.fetchall()]
            return {"items": rows, "total": total, "page": page, "page_size": page_size}

    def query_news(
        self,
        search: Optional[str] = None,
        source: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            clauses = ["1=1"]
            params = []
            if search:
                clauses.append("(title LIKE ? OR summary LIKE ?)")
                q = f"%{search}%"
                params.extend([q, q])
            if source and source != "all":
                clauses.append("source_name = ?")
                params.append(source)

            where_sql = " AND ".join(clauses)
            cursor.execute(f"SELECT COUNT(*) FROM news WHERE {where_sql}", params)
            total = cursor.fetchone()[0]

            offset = max(0, (page - 1) * page_size)
            cursor.execute(
                f"SELECT * FROM news WHERE {where_sql} ORDER BY published_at DESC LIMIT ? OFFSET ?",
                params + [page_size, offset]
            )
            rows = [dict(r) for r in cursor.fetchall()]
            return {"items": rows, "total": total, "page": page, "page_size": page_size}

    def query_mappings(
        self,
        search: Optional[str] = None,
        min_confidence: Optional[float] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            clauses = ["1=1"]
            params = []
            if search:
                clauses.append("(raw_name LIKE ? OR canonical_name LIKE ?)")
                q = f"%{search}%"
                params.extend([q, q])
            if min_confidence:
                clauses.append("confidence_score >= ?")
                params.append(min_confidence)

            where_sql = " AND ".join(clauses)
            cursor.execute(f"SELECT COUNT(*) FROM entity_mappings WHERE {where_sql}", params)
            total = cursor.fetchone()[0]

            offset = max(0, (page - 1) * page_size)
            cursor.execute(
                f"SELECT * FROM entity_mappings WHERE {where_sql} ORDER BY id ASC LIMIT ? OFFSET ?",
                params + [page_size, offset]
            )
            rows = [dict(r) for r in cursor.fetchall()]
            return {"items": rows, "total": total, "page": page, "page_size": page_size}

    def get_analytics_summary(self) -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Startups by stage
            cursor.execute("""
                SELECT COALESCE(funding_stage, 'Unspecified') as stage, COUNT(*) as count, SUM(COALESCE(total_funding_usd, 0)) as total_funding
                FROM startups
                GROUP BY stage
                ORDER BY count DESC
                LIMIT 8
            """)
            startups_by_stage = [dict(r) for r in cursor.fetchall()]

            # Products by category
            cursor.execute("""
                SELECT COALESCE(category, 'General AI') as cat, COUNT(*) as count, SUM(COALESCE(github_stars, 0)) as total_likes
                FROM products
                GROUP BY cat
                ORDER BY count DESC
                LIMIT 8
            """)
            products_by_category = [dict(r) for r in cursor.fetchall()]

            # Research papers by primary category
            cursor.execute("""
                SELECT primary_category, COUNT(*) as count
                FROM research_papers
                GROUP BY primary_category
                ORDER BY count DESC
                LIMIT 6
            """)
            papers_by_category = [dict(r) for r in cursor.fetchall()]

            # Jobs by remote eligibility
            cursor.execute("""
                SELECT remote_eligibility, COUNT(*) as count
                FROM jobs
                GROUP BY remote_eligibility
            """)
            jobs_by_remote = [dict(r) for r in cursor.fetchall()]

            # News sources
            cursor.execute("""
                SELECT source_name, COUNT(*) as count
                FROM news
                GROUP BY source_name
                ORDER BY count DESC
                LIMIT 6
            """)
            news_by_source = [dict(r) for r in cursor.fetchall()]

            # Entity mappings confidence tiers
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN confidence_score >= 95 THEN 'High (95-100%)'
                        WHEN confidence_score >= 85 THEN 'Medium (85-94%)'
                        ELSE 'Review Needed (<85%)'
                    END as tier,
                    COUNT(*) as count
                FROM entity_mappings
                GROUP BY tier
            """)
            mappings_tiers = [dict(r) for r in cursor.fetchall()]

            return {
                "startups_by_stage": startups_by_stage,
                "products_by_category": products_by_category,
                "papers_by_category": papers_by_category,
                "jobs_by_remote": jobs_by_remote,
                "news_by_source": news_by_source,
                "mappings_tiers": mappings_tiers,
                "counts": self.get_counts()
            }

    def universal_search(self, q: str, limit_per_table: int = 5) -> Dict[str, Any]:
        if not q or len(q.strip()) < 2:
            return {"query": q, "results": {}}
        term = f"%{q.strip()}%"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            results = {}

            cursor.execute("SELECT id, name, funding_stage, headquarters, website FROM startups WHERE name LIKE ? OR description LIKE ? LIMIT ?", (term, term, limit_per_table))
            results["startups"] = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT id, name, company_name, category, product_url FROM products WHERE name LIKE ? OR company_name LIKE ? LIMIT ?", (term, term, limit_per_table))
            results["products"] = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT id, title, authors, primary_category, paper_url FROM research_papers WHERE title LIKE ? OR abstract LIKE ? LIMIT ?", (term, term, limit_per_table))
            results["papers"] = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT id, job_title, company_name, location, job_url FROM jobs WHERE job_title LIKE ? OR company_name LIKE ? LIMIT ?", (term, term, limit_per_table))
            results["jobs"] = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT id, title, source_name, article_url FROM news WHERE title LIKE ? OR summary LIKE ? LIMIT ?", (term, term, limit_per_table))
            results["news"] = [dict(r) for r in cursor.fetchall()]

            return {"query": q, "results": results}

    def log_error(self, component: str, error_message: str, details: Optional[Dict[str, Any]] = None) -> None:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO error_logs (component, error_message, details, timestamp)
            VALUES (?, ?, ?, ?)
            """, (
                component,
                error_message,
                json.dumps(details) if details else None,
                datetime.now(timezone.utc).isoformat()
            ))
            conn.commit()

    def correct_entity_mapping(self, raw_name: str, canonical_name: str, entity_type: str = "Company") -> bool:
        record = EntityMappingRecord(
            raw_name=raw_name.strip(),
            canonical_name=canonical_name.strip(),
            entity_type=entity_type.strip(),
            source="manual_override",
            confidence_score=100.0,
            resolution_method="ManualReviewOverride",
            timestamp=datetime.now(timezone.utc)
        )
        return self.save_entity_mapping(record)

    def get_products_by_ids(self, ids: List[int]) -> List[Dict[str, Any]]:
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM products WHERE id IN ({placeholders})", ids)
            return [dict(r) for r in cursor.fetchall()]

    def get_system_info(self) -> Dict[str, Any]:
        from config.settings import settings, BASE_DIR
        import os

        db_file = BASE_DIR / "data" / "ai_pipeline.db"
        db_size_mb = round(db_file.stat().st_size / (1024 * 1024), 2) if db_file.exists() else 0.0

        journal_mode = "unknown"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode;")
            row = cursor.fetchone()
            if row:
                journal_mode = row[0]

        counts = self.get_counts()
        total_records = sum(counts.values())

        # Inspect exported files
        exports = []
        if settings.DATA_PROCESSED_DIR.exists():
            for f in sorted(settings.DATA_PROCESSED_DIR.glob("*.*")):
                if f.is_file() and not f.name.startswith("."):
                    stat = f.stat()
                    exports.append({
                        "name": f.name,
                        "size_kb": round(stat.st_size / 1024, 2),
                        "last_modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                        "download_url": f"/download/{f.name}"
                    })

        return {
            "status": "online",
            "environment": settings.ENVIRONMENT,
            "database": {
                "engine": "SQLite 3 (PostgreSQL Schema Compatible)",
                "path": str(db_file),
                "size_mb": db_size_mb,
                "journal_mode": journal_mode.upper(),
                "total_records": total_records,
                "table_counts": counts
            },
            "configuration": {
                "gemini_api": "Configured (" + settings.mask_secret(settings.GEMINI_API_KEY) + ")" if settings.GEMINI_API_KEY else "Not Configured (Fallback enabled)",
                "groq_api": "Configured (" + settings.mask_secret(settings.GROQ_API_KEY) + ")" if settings.GROQ_API_KEY else "Not Configured",
                "deepseek_api": "Configured (" + settings.mask_secret(settings.DEEPSEEK_API_KEY) + ")" if settings.DEEPSEEK_API_KEY else "Not Configured",
                "github_token": "Configured (" + settings.mask_secret(settings.GITHUB_TOKEN) + ")" if settings.GITHUB_TOKEN else "Unauthenticated Rate Limit",
                "google_sheets": "Configured" if settings.GOOGLE_SPREADSHEET_ID and settings.GOOGLE_APPLICATION_CREDENTIALS else "Local CSV / JSONL Fallback",
                "rolling_window_hours": settings.ROLLING_WINDOW_HOURS,
                "rapidfuzz_threshold": f"{settings.RAPIDFUZZ_SIMILARITY_THRESHOLD}%"
            },
            "exports": exports
        }

repo = SQLiteRepository()

