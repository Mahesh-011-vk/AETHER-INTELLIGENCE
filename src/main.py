import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import argparse
import asyncio
from typing import Optional, List
from pydantic import BaseModel
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from config.settings import settings
from src.pipeline import IntelligencePipeline, pipeline_progress
from src.database.repository import repo
from src.exporters.sheets_exporter import exporter
from src.utils.logging import logger

app = FastAPI(
    title="AI Intelligence Data Pipeline API",
    description="Automated intelligence collection, entity resolution, and structured extraction platform for AI Startups, Products, Papers, Jobs, and News.",
    version="1.0.0"
)

pipeline_status = {"last_run": None, "is_running": False}

STATIC_DIR = ROOT_DIR / "src" / "static"
STYLES_DIR = ROOT_DIR / "src" / "styles"

if STYLES_DIR.exists():
    app.mount("/styles", StaticFiles(directory=str(STYLES_DIR)), name="styles")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    if (STATIC_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def get_dashboard():
    template_path = ROOT_DIR / "src" / "templates" / "index.html"
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard template not found")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.api_route("/privacy", methods=["GET", "HEAD"], response_class=HTMLResponse)
def get_privacy():
    path = ROOT_DIR / "src" / "templates" / "privacy.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Privacy page not found")
    return path.read_text(encoding="utf-8")

@app.api_route("/terms", methods=["GET", "HEAD"], response_class=HTMLResponse)
def get_terms():
    path = ROOT_DIR / "src" / "templates" / "terms.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Terms page not found")
    return path.read_text(encoding="utf-8")

@app.api_route("/404", methods=["GET", "HEAD"], response_class=HTMLResponse)
def get_404():
    path = ROOT_DIR / "src" / "templates" / "404.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="404 page not found")
    return path.read_text(encoding="utf-8")

@app.api_route("/favicon.svg", methods=["GET", "HEAD"])
def get_favicon_svg():
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")

@app.api_route("/favicon.ico", methods=["GET", "HEAD"])
def get_favicon_ico():
    return FileResponse(STATIC_DIR / "favicon.ico", media_type="image/x-icon")

@app.api_route("/apple-touch-icon.png", methods=["GET", "HEAD"])
def get_apple_touch_icon():
    return FileResponse(STATIC_DIR / "apple-touch-icon.png", media_type="image/png")

@app.api_route("/site.webmanifest", methods=["GET", "HEAD"])
def get_manifest():
    return FileResponse(STATIC_DIR / "site.webmanifest", media_type="application/manifest+json")

@app.api_route("/robots.txt", methods=["GET", "HEAD"])
def get_robots():
    return FileResponse(STATIC_DIR / "robots.txt", media_type="text/plain")

@app.api_route("/sitemap.xml", methods=["GET", "HEAD"])
def get_sitemap():
    return FileResponse(STATIC_DIR / "sitemap.xml", media_type="application/xml")

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: Exception):
    if "text/html" in request.headers.get("accept", ""):
        path = ROOT_DIR / "src" / "templates" / "404.html"
        if path.exists():
            return HTMLResponse(content=path.read_text(encoding="utf-8"), status_code=404)
    return HTMLResponse(content='{"detail": "Not Found"}', status_code=404, media_type="application/json")

@app.api_route("/download/{filename}", methods=["GET", "HEAD"])
def download_export_file(filename: str):
    allowed_files = [
        "startups.csv", "products.csv", "research_papers.csv", "jobs.csv", "news.csv", "entity_mappings.csv",
        "startups.jsonl", "products.jsonl", "research_papers.jsonl", "jobs.jsonl", "news.jsonl", "entity_mappings.jsonl",
        "AETHER_AI_INTELLIGENCE_SUBMISSION.xlsx", "submission.xlsx"
    ]
    if filename not in allowed_files:
        raise HTTPException(status_code=404, detail="File not found or access denied")
    
    target_name = "AETHER_AI_INTELLIGENCE_SUBMISSION.xlsx" if filename == "submission.xlsx" else filename
    file_path = settings.DATA_PROCESSED_DIR / target_name
    if not file_path.exists():
        exporter.export_all()
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Export file has not been generated yet")
    
    if filename.endswith(".xlsx"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif filename.endswith(".csv"):
        media_type = "text/csv"
    else:
        media_type = "application/jsonl"
    return FileResponse(path=str(file_path), filename=filename, media_type=media_type)

@app.api_route("/export/submission.xlsx", methods=["GET", "HEAD"])
def download_submission_xlsx():
    return download_export_file("AETHER_AI_INTELLIGENCE_SUBMISSION.xlsx")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database_counts": repo.get_counts(),
        "is_pipeline_running": pipeline_status["is_running"]
    }

@app.get("/stats")
def get_stats():
    return {
        "database_counts": repo.get_counts(),
        "last_run": pipeline_status["last_run"]
    }

@app.get("/startups")
def get_startups(limit: int = 50):
    return repo.fetch_all("startups")[:limit]

@app.get("/products")
def get_products(limit: int = 50):
    return repo.fetch_all("products")[:limit]

@app.get("/papers")
def get_papers(limit: int = 50):
    return repo.fetch_all("research_papers")[:limit]

@app.get("/jobs")
def get_jobs(limit: int = 50):
    return repo.fetch_all("jobs")[:limit]

@app.get("/news")
def get_news(limit: int = 50):
    return repo.fetch_all("news")[:limit]

@app.get("/mappings")
def get_mappings(limit: int = 50):
    return repo.fetch_all("entity_mappings")[:limit]

@app.get("/api/pipeline/progress")
def get_pipeline_progress():
    return pipeline_progress

@app.get("/api/analytics")
def get_analytics():
    return repo.get_analytics_summary()

@app.get("/api/search")
def universal_search(q: str = ""):
    return repo.universal_search(q)

@app.get("/api/startups")
def query_startups(
    search: Optional[str] = None,
    stage: Optional[str] = None,
    min_funding: Optional[float] = None,
    sort_by: str = "total_funding_usd",
    sort_dir: str = "DESC",
    page: int = 1,
    page_size: int = 50
):
    return repo.query_startups(search, stage, min_funding, sort_by, sort_dir, page, page_size)

@app.get("/api/products")
def query_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    pricing: Optional[str] = None,
    sort_by: str = "github_stars",
    sort_dir: str = "DESC",
    page: int = 1,
    page_size: int = 50
):
    return repo.query_products(search, category, pricing, sort_by, sort_dir, page, page_size)

@app.get("/api/papers")
def query_papers(
    search: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: str = "published_date",
    sort_dir: str = "DESC",
    page: int = 1,
    page_size: int = 50
):
    return repo.query_papers(search, category, sort_by, sort_dir, page, page_size)

@app.get("/api/jobs")
def query_jobs(
    search: Optional[str] = None,
    remote_only: bool = False,
    india_only: bool = False,
    sort_by: str = "published_at",
    sort_dir: str = "DESC",
    page: int = 1,
    page_size: int = 50
):
    return repo.query_jobs(search, remote_only, india_only, sort_by, sort_dir, page, page_size)

@app.get("/api/news")
def query_news(
    search: Optional[str] = None,
    source: Optional[str] = None,
    page: int = 1,
    page_size: int = 50
):
    return repo.query_news(search, source, page, page_size)

@app.get("/api/mappings")
def query_mappings(
    search: Optional[str] = None,
    min_confidence: Optional[float] = None,
    page: int = 1,
    page_size: int = 50
):
    return repo.query_mappings(search, min_confidence, page, page_size)

class MappingCorrectionRequest(BaseModel):
    raw_name: str
    canonical_name: str
    entity_type: str = "Company"

@app.post("/api/mappings/correct")
def correct_mapping(payload: MappingCorrectionRequest):
    if not payload.raw_name or not payload.canonical_name:
        raise HTTPException(status_code=400, detail="raw_name and canonical_name are required")
    success = repo.correct_entity_mapping(
        raw_name=payload.raw_name,
        canonical_name=payload.canonical_name,
        entity_type=payload.entity_type
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save mapping correction")
    return {
        "status": "success",
        "message": f"Mapping updated: '{payload.raw_name}' -> '{payload.canonical_name}'",
        "raw_name": payload.raw_name,
        "canonical_name": payload.canonical_name
    }

@app.get("/api/products/compare")
def compare_products(ids: str):
    try:
        id_list = [int(i.strip()) for i in ids.split(",") if i.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID list. Provide comma-separated integers.")
    if len(id_list) < 2 or len(id_list) > 4:
        raise HTTPException(status_code=400, detail="Comparison requires between 2 and 4 product IDs.")
    items = repo.get_products_by_ids(id_list)
    return {"products": items, "count": len(items)}

@app.get("/api/system/settings")
def get_system_settings():
    return repo.get_system_info()

@app.post("/api/export/regenerate")
def regenerate_exports():
    res = exporter.export_all()
    return {"status": "success", "exports": res, "system_info": repo.get_system_info()}

@app.get("/api/{table}/{item_id}")
def get_item_detail(table: str, item_id: int):
    item = repo.get_item_by_id(table, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Record not found")
    return item

async def run_pipeline_task(target_startups: int, target_products: int, target_papers: int):
    pipeline_status["is_running"] = True
    try:
        pipeline = IntelligencePipeline(
            target_startups=target_startups,
            target_products=target_products,
            target_papers=target_papers
        )
        summary = await pipeline.execute()
        pipeline_status["last_run"] = summary
    except Exception as e:
        logger.error(f"Pipeline background run failed: {e}")
        pipeline_status["last_run"] = {"status": "FAILED", "error": str(e)}
    finally:
        pipeline_status["is_running"] = False

@app.post("/pipeline/run")
def trigger_pipeline(
    background_tasks: BackgroundTasks,
    target_startups: int = 100,
    target_products: int = 100,
    target_papers: int = 100
):
    if pipeline_status["is_running"]:
        return {"status": "error", "message": "Pipeline already executing"}
    background_tasks.add_task(run_pipeline_task, target_startups, target_products, target_papers)
    return {"status": "accepted", "message": "Pipeline execution started in background"}

def main():
    parser = argparse.ArgumentParser(description="AI Intelligence Data Pipeline")
    parser.add_argument("--api", action="store_true", help="Launch FastAPI web service")
    parser.add_argument("--host", default="0.0.0.0", help="API bind host")
    parser.add_argument("--port", type=int, default=8000, help="API bind port")
    parser.add_argument("--quick-test", action="store_true", help="Run quick test with 10 records per category")
    parser.add_argument("--target-startups", type=int, default=1000, help="Target count for AI startups")
    parser.add_argument("--target-products", type=int, default=1000, help="Target count for AI products")
    parser.add_argument("--target-papers", type=int, default=1000, help="Target count for research papers")
    parser.add_argument("--export-only", action="store_true", help="Export existing DB to CSV/JSONL/Sheets")

    args = parser.parse_args()

    if args.export_only:
        logger.info("Executing export on existing database records...")
        repo.init_db()
        res = exporter.export_all()
        print("Export completed:", res)
        return

    if args.api:
        logger.info(f"Starting API server on {args.host}:{args.port}...")
        uvicorn.run("src.main:app", host=args.host, port=args.port, reload=False)
        return

    target_startups = 15 if args.quick_test else args.target_startups
    target_products = 15 if args.quick_test else args.target_products
    target_papers = 15 if args.quick_test else args.target_papers

    pipeline = IntelligencePipeline(
        target_startups=target_startups,
        target_products=target_products,
        target_papers=target_papers
    )

    summary = asyncio.run(pipeline.execute())
    print("\n================== PIPELINE EXECUTION SUMMARY ==================")
    print(f"Run ID: {summary['run_id']}")
    print(f"Duration: {summary['duration_seconds']}s")
    print(f"Database Counts: {summary['saved_in_db']}")
    print(f"Validated Counts: {summary['validated_records']}")
    print(f"Validation Rejections: {summary['validation_stats']['rejections_by_reason']}")
    print(f"Exports: {list(summary['exports']['files'].keys())}")
    print("===============================================================\n")

if __name__ == "__main__":
    main()
