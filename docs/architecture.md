# AI Intelligence Pipeline — Architecture & Scalability Guide

## 1. System Overview

The AI Intelligence Data Pipeline is an automated, production-grade intelligence harvesting and normalization platform designed to discover, validate, deduplicate, resolve, and export structured datasets across five core AI domains:
1. **AI Startups** (Unicorns, stealth startups, and venture ecosystems)
2. **AI Products** (Commercial SaaS, foundation models, agents, open-source repositories)
3. **AI Research Papers** (ArXiv preprints across computer science AI sub-disciplines)
4. **AI Jobs** (Active hiring roles published within a strict rolling 24-hour UTC window)
5. **AI News** (Real-time announcements and technical discussions within a rolling 24-hour UTC window)

In addition, the pipeline produces a sixth consolidated stream:
6. **Entity Mapping Log** (Auditable fuzzy matching, normalization, and canonical name resolution logs)

---

## 2. Component Architecture

```
                       +-----------------------------+
                       |   External Data Sources     |
                       | ArXiv | HF | GitHub | RSS   |
                       +--------------+--------------+
                                      |
                                      v
                      +---------------+---------------+
                      |      BaseCrawler (Async)      |
                      |  Bounded Concurrency (Sem)   |
                      |  Exponential Retry & Jitter  |
                      +---------------+---------------+
                                      |
                                      v
                      +---------------+---------------+
                      |        Data Extraction        |
                      |  HTML Cleaner | DateExtractor |
                      |    (UTC Normalization)        |
                      +---------------+---------------+
                                      |
                                      v
                      +---------------+---------------+
                      |       LLM Orchestrator        |
                      | Gemini -> Groq -> DeepSeek    |
                      |   Structured JSON Output      |
                      |   Deterministic Fallback      |
                      +---------------+---------------+
                                      |
                                      v
                      +---------------+---------------+
                      |   Entity Resolution Engine    |
                      |  Legal Suffix Stripping       |
                      |  RapidFuzz Candidate Matching |
                      +---------------+---------------+
                                      |
                                      v
                      +---------------+---------------+
                      |        Data Validator         |
                      |   Pydantic V2 Schemas         |
                      |   24h Rolling Window Check    |
                      |   In-Flight Deduplication     |
                      +---------------+---------------+
                                      |
                                      v
                      +---------------+---------------+
                      |       Persistence Layer       |
                      |    SQLite (WAL Mode) /        |
                      | PostgreSQL-Ready Repository   |
                      +---------------+---------------+
                                      |
                                      v
                      +---------------+---------------+
                      |        Exporters Layer        |
                      |  CSV | JSONL | Google Sheets  |
                      +-------------------------------+
```

---

## 3. Core Architectural Principles

### 3.1. Repository Pattern & Storage Decoupling
The database operations implement the `IRepository` interface. While the initial working implementation uses SQLite configured with Write-Ahead Logging (`WAL`), the data access layer contains no SQLite-specific syntax that precludes substituting PostgreSQL. All schema operations rely on standard SQL types, unique constraints, and upsert clauses (`ON CONFLICT`).

### 3.2. Resilient Multi-Provider LLM Orchestration
The extraction engine decouples prompts from specific LLM vendors using a priority-driven orchestrator:
1. **Primary**: Google Gemini API (`gemini-1.5-flash` / `gemini-2.0-flash`) with structured JSON mode.
2. **Secondary Fallback**: Groq Cloud API (`llama-3.1-8b-instant`) with JSON schema enforcement.
3. **Tertiary Fallback**: DeepSeek API (`deepseek-chat`).
4. **Deterministic Fallback**: Comprehensive regex, HTML metadata, and rule-based extraction when no API keys are provided.

### 3.3. Deterministic Normalization & Fuzzy Entity Resolution
Entity resolution combines:
- Pre-cleaning of legal suffixes (`Inc`, `LLC`, `Corp`, `Ltd`, `GmbH`, `PBC`, `Technologies`).
- Punctuation stripping and case normalization.
- RapidFuzz `token_sort_ratio` candidate matching with configurable similarity thresholds (default: 85.0%).
- Length ratio verification to prevent catastrophic short-token false positives.
- Comprehensive audit trail preserving raw input, canonical entity, confidence score, resolution method, and timestamp.

### 3.4. Strict 24-Hour UTC Freshness Verification
For high-velocity categories (News and Jobs), the platform enforces strict publication date validation:
- The system parses RFC 2822, ISO 8601, and UNIX timestamps into timezone-aware UTC `datetime` objects.
- Verification calculates: `(now_utc - 24h) <= published_at <= (now_utc + 15m)`.
- Records with unparseable or outdated publication timestamps are rejected with explicit audit reasons. The collection timestamp is never substituted for publication date.

---

## 4. Scaling Architecture (Transitioning to 500,000+ Records)

To scale this pipeline to handle 500,000+ records continuously across enterprise data volumes, the following modular enhancements are designed into the codebase:

### 4.1. Storage: Transition to PostgreSQL & Partitioning
- **Database Engine**: Replace SQLite with PostgreSQL 16+ hosted on AWS RDS or Cloud SQL with connection pooling (e.g., PgBouncer).
- **Table Partitioning**: Implement range partitioning by `published_at` (monthly partitions) for high-volume tables (`jobs`, `news`, `research_papers`).
- **Full-Text & Vector Search**: Add `pgvector` extensions to store 1536-dimensional embeddings of abstracts and descriptions for semantic search.

### 4.2. Distributed Ingestion: Redis & Celery / Temporal
- **Task Queue**: Introduce Redis as a distributed message broker and Celery / Celery Beat or Temporal.io for workflow orchestration.
- **Worker Fan-Out**: Run specialized worker pools:
  - `crawler-workers`: Asynchronously scrape web pages, XML feeds, and APIs.
  - `llm-workers`: Dedicated rate-limited workers communicating with LLM endpoints with backpressure management.
  - `indexing-workers`: Bulk insert validated records into PostgreSQL.

### 4.3. Raw Evidence: Object Storage
- Store raw HTML payloads, XML documents, and JSON evidence in AWS S3 or Google Cloud Storage partitioned by `s3://ai-intelligence-lake/{domain}/{YYYY}/{MM}/{DD}/{record_id}.json.gz`.
- SQLite/PostgreSQL stores only the S3 URI pointer in `raw_evidence`, keeping database index footprint minimal.

### 4.4. Deduplication & Caching: Redis Bloom Filters
- In-memory sets are replaced by scalable Redis Bloom Filters (`BF.ADD`, `BF.EXISTS`) allowing constant-time ($O(1)$) duplicate detection across tens of millions of records with near-zero memory footprint.

### 4.5. High-Throughput Entity Resolution: Embedding + Vector Search
- For millions of entities, pairwise RapidFuzz comparison is optimized using Hierarchical Navigable Small World (HNSW) indexing on text embeddings (e.g., Qdrant or Milvus) to query nearest neighbors in $O(\log N)$ time, applying RapidFuzz only to the top-5 vector candidates.

