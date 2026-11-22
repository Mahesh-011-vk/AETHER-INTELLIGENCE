# AI Intelligence Data Pipeline

An enterprise-grade, source-verifiable intelligence collection and processing platform built with Python 3.11, asyncio, Pydantic v2, and SQLite.

The pipeline discovers, extracts, validates, normalizes, deduplicates, and stores intelligence across five critical AI domains, generating six structured export tabs (Google Sheets / CSV / JSONL):
1. **AI Startups** (1,000+ verifiable companies and venture-backed organizations)
2. **AI Products** (1,000+ AI models, applications, and frameworks)
3. **AI Research Papers** (1,000+ ArXiv preprints across machine learning disciplines)
4. **AI Jobs** (Active postings verified within a strict rolling 24-hour UTC window)
5. **AI News** (Articles and breaking discussions verified within a rolling 24-hour UTC window)
6. **Entity Mapping Log** (Full audit trail of canonical name resolution and fuzzy matching)

---

## 1. Quick Start

### 1.1. Prerequisites
- Python 3.11+
- Git
- Docker & Docker Compose (optional for containerized deployment)

### 1.2. Local Installation
```bash
# 1. Clone repository
git clone https://github.com/your-username/ai-intelligence-pipeline.git
cd ai-intelligence-pipeline

# 2. Create virtual environment using uv or python3.11 venv
uv venv --python 3.11 .venv
source .venv/bin/activate

# 3. Install dependencies
uv pip install -r requirements.txt
```

### 1.3. Environment Configuration
Copy the sample environment file:
```bash
cp .env.example .env
```
Configure your credentials in `.env` (all keys are optional; the pipeline features automatic fallbacks):
```ini
ENVIRONMENT=development
LOG_LEVEL=INFO

# LLM Providers (Priority: Gemini -> Groq -> DeepSeek)
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# GitHub Token (elevates search rate limits)
GITHUB_TOKEN=your_github_token

# Google Sheets Export (optional service account)
GOOGLE_APPLICATION_CREDENTIALS=
GOOGLE_SPREADSHEET_ID=
```

---

## 2. Running the Pipeline

### 2.1. Quick Test Run (Smoke Test)
Execute an accelerated run collecting ~15 records per category to verify connectivity, validation, database insertion, and file exports:
```bash
python src/main.py --quick-test
```

### 2.2. Full Production Run (1,000+ Targets)
Execute the complete data pipeline targeting 1,000+ startups, 1,000+ products, 1,000+ papers, and all qualifying 24h jobs and news:
```bash
python src/main.py --target-startups 1000 --target-products 1000 --target-papers 1000
```

### 2.3. Launch FastAPI Server & Web Terminal Interface
```bash
python src/main.py --api --port 8000
```
Open your browser to `http://localhost:8000` to access the full **Aether AI Intelligence Terminal**:
- **Bloomberg / Linear Dark UI**: High-density terminal aesthetics, 6 overview metric cards, responsive container tables.
- **Global Command Palette (`⌘K` / `Ctrl+K`)**: Universal search across all entities, papers, jobs, and tools.
- **AI Model Benchmark Comparison**: Multi-select up to 4 models from the Products table for a side-by-side architectural matrix.
- **Entity Resolution & Manual Override**: Audit fuzzy matching scores and execute manual canonical mapping corrections via `POST /api/mappings/correct`.
- **Slide-over Inspection Drawer**: Deep metadata inspection, permalink sharing (`#<tab>/<id>`), and raw JSON provenance viewer.
- **11-Stage Pipeline Ingestion Modal**: Real-time progress bar, animated step indicators, and live log terminal streaming.
- **Interactive Chart.js Analytics**: Multi-angle distribution charts for funding stages, model task pipelines, ArXiv sub-disciplines, remote workplace ratio, and entity confidence tiers.
- **System Diagnostics & Export Hub**: View database size, WAL mode, table row counts, masked provider credentials, and download or regenerate exports.

API documentation is also available:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health Check: `http://localhost:8000/health`
- Statistics: `http://localhost:8000/stats`

### 2.4. Docker Deployment
```bash
docker-compose up --build -d
```

---

## 3. Test Suite

Run the complete test suite covering schema compliance, entity resolution, fuzzy matching, date extraction, and 24-hour freshness rules:
```bash
pytest -v tests/
```

---

## 4. Architecture & Key Features

```
ai-intelligence-pipeline/
├── config/
│   └── settings.py              # Pydantic BaseSettings & secret masking
├── src/
│   ├── crawlers/                # Async crawlers for ArXiv, HF, GitHub, Jobs, RSS
│   ├── extractors/              # HTML boiler-plate stripping & UTC date parser
│   ├── llm/                     # Gemini/Groq/DeepSeek provider fallback & chunker
│   ├── models/                  # Pydantic v2 data models with validators
│   ├── entity_resolution/       # RapidFuzz canonical matcher & legal suffix stripper
│   ├── validators/              # Freshness window, deduplication & schema validation
│   ├── database/                # WAL SQLite repository & PostgreSQL-ready interface
│   ├── exporters/               # 6-Tab CSV, JSONL & Google Sheets API exporters
│   ├── pipeline.py              # End-to-end asynchronous pipeline orchestrator
│   └── main.py                  # CLI and FastAPI endpoints
├── tests/                       # 20+ unit and integration tests
├── data/
│   ├── raw/                     # Preserved raw crawler evidence payloads
│   └── processed/               # 6 standardized CSV and JSONL files
└── docs/
    ├── architecture.md          # System design & 500k+ scalability transition
    └── limitations.md           # Transparent API limits & freshness constraints
```

### 4.1. Entity Resolution
- Strips legal noise suffixes (`Inc`, `LLC`, `Corp`, `Ltd`, `GmbH`, `PBC`, `Technologies`).
- Leverages RapidFuzz token sorting with configurable similarity thresholds ($\ge 85\%$).
- Generates a persistent, auditable mapping log tracking `raw_name`, `canonical_name`, `entity_type`, `source`, `confidence_score`, and `resolution_method`.

### 4.2. Strict 24-Hour Freshness Window
- News and job records must have confirmed publication timestamps strictly within the preceding 24 hours UTC.
- Records with unverified or stale dates are rejected with explicit reasons recorded in the audit log. The system never substitutes collection timestamps for publication dates.

### 4.3. Multi-Provider LLM Fallback
- Strict priority hierarchy: **1. Gemini** $\rightarrow$ **2. Groq** $\rightarrow$ **3. DeepSeek**.
- Automatic fallback on timeouts, HTTP 429 rate limits, and JSON errors.
- Robust deterministic fallback when API keys are absent, ensuring guaranteed pipeline execution.

### 4.4. Six Output Tabs / Files
The pipeline exports 6 structured tabs matching the exact schema requirements:
1. `data/processed/startups.csv` / `.jsonl`
2. `data/processed/products.csv` / `.jsonl`
3. `data/processed/research_papers.csv` / `.jsonl`
4. `data/processed/jobs.csv` / `.jsonl`
5. `data/processed/news.csv` / `.jsonl`
6. `data/processed/entity_mapping_log.csv` / `.jsonl`

When `GOOGLE_APPLICATION_CREDENTIALS` and `GOOGLE_SPREADSHEET_ID` are provided, all 6 tabs are automatically updated via the Google Sheets API.

---

## 5. Scaling to 500,000+ Records

For enterprise-scale workloads:
- **Database**: Swap SQLite for PostgreSQL 16 with range partitioning on `published_at`.
- **Queuing & Workers**: Introduce Redis and Celery to distribute crawler and extraction workloads across worker nodes.
- **Storage**: Store raw evidence in object storage (AWS S3 / GCS) referenced by URI.
- **Deduplication**: Employ Redis Bloom Filters for $O(1)$ duplicate checking across millions of records.
- **Vector Search**: Use pgvector / Qdrant for semantic nearest-neighbor candidate retrieval prior to fuzzy matching.

Detailed design diagrams are available in [`docs/architecture.md`](docs/architecture.md).

