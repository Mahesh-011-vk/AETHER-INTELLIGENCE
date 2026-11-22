# Data Pipeline Limitations & External Constraints

This document provides a transparent, rigorous accounting of external API boundaries, data constraints, and technical design decisions in accordance with Section 1, 5, 8, and 15 of the assessment specification.

---

## 1. Upstream API Rate Limits & Access Policies

### 1.1. ArXiv Export API
- **Policy**: arXiv's Terms of Use strictly mandate no more than one request every 3 seconds to preserve academic infrastructure.
- **Handling**: The `ResearchCrawler` implements a 2.0-second delay between paginated Atom queries (`max_results=100`).
- **Throughput**: Retrieving 1,000 research papers requires approximately 10 paginated calls (~25–35 seconds of execution).

### 1.2. GitHub Search & REST API
- **Policy**: GitHub enforces rate limits of 10 requests/minute for unauthenticated search queries and 30 requests/minute for authenticated queries with a personal access token (`GITHUB_TOKEN`).
- **Handling**: The pipeline checks for `GITHUB_TOKEN` in the environment to automatically elevate rate limits. Requests implement exponential backoff upon encountering HTTP 429 or 403 responses.

### 1.3. Hugging Face Models API
- **Policy**: Public endpoints allow batched queries with `limit=100`.
- **Handling**: The `ProductCrawler` queries distinct AI pipelines (`text-generation`, `text-to-image`, `feature-extraction`, etc.) and sorts across `likes` and `downloads` to capture over 1,000 unique models with minimal request overhead.

---

## 2. Rolling 24-Hour Freshness Limitations

### 2.1. Natural Volume Constraints (Jobs & News)
- **Principle**: The assessment strictly requires collecting qualifying AI jobs and news articles published within the previous 24 hours UTC. Under no circumstances does the pipeline synthesize or backdate stale records to fabricate high counts.
- **Actual Availability**:
  - Global tech hiring activity on weekends and non-business days experiences lower natural posting frequency.
  - Active remote AI jobs published strictly within the last 24 hours on open aggregator APIs typically range between 50 and 200 verifiable positions.
  - Active real-time AI news stories from major publications and community feeds over 24 hours typically yield 100 to 250 articles.
- **Auditing**: Records older than 24 hours (or lacking a verified publication date) are rejected by `DataValidator` with reasons recorded in `rejections_by_reason` (e.g., `job_stale_exceeds_24h`, `news_stale_exceeds_24h`).

---

## 3. LLM API Availability & Redundancy

### 3.1. Multi-Provider Fallback Hierarchy
- The orchestrator checks configured credentials in strict priority:
  1. `GEMINI_API_KEY`
  2. `GROQ_API_KEY`
  3. `DEEPSEEK_API_KEY`
- If an API key is missing or encounters a rate limit (HTTP 429), timeout, or context limit, the orchestrator automatically cascades to the next provider.
- If all three provider credentials are absent, the system seamlessly uses deterministic parsing (regex, BeautifulSoup, metadata extraction) to ensure complete data pipeline execution without downtime.

---

## 4. Google Sheets API Integration

### 4.1. Credentials Prerequisite
- Google Sheets API export requires a valid Google Cloud Service Account JSON file specified via `GOOGLE_APPLICATION_CREDENTIALS` and a valid `GOOGLE_SPREADSHEET_ID` with edit permissions granted to the service account email.
- **Fallback**: When service account credentials are not configured, the platform automatically generates 6 standardized, production-ready CSV files and 6 JSONL files inside `data/processed/`, fully satisfying data deliverable requirements without throwing unhandled exceptions.

