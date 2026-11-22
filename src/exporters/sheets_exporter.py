import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from config.settings import settings
from src.database.repository import repo
from src.utils.logging import logger

TAB_HEADERS: Dict[str, List[str]] = {
    "Startups": [
        "name", "canonical_name", "description", "website", "founded_year",
        "headquarters", "funding_stage", "total_funding_usd", "focus_areas",
        "source_name", "source_url", "collected_at"
    ],
    "Products": [
        "name", "canonical_name", "company_name", "canonical_company_name",
        "description", "product_url", "category", "pricing_model",
        "github_repo_url", "github_stars", "github_forks",
        "source_name", "source_url", "collected_at"
    ],
    "Research Papers": [
        "title", "authors", "abstract", "arxiv_id", "paper_url",
        "published_date", "primary_category", "categories", "code_url",
        "citation_count", "source_name", "source_url", "collected_at"
    ],
    "Jobs": [
        "job_title", "company_name", "canonical_company_name", "location",
        "remote_eligibility", "job_url", "published_at", "salary_range",
        "description", "source_name", "source_url", "collected_at"
    ],
    "News": [
        "title", "article_url", "published_at", "summary", "key_entities",
        "sentiment_category", "source_name", "source_url", "collected_at"
    ],
    "Entity Mapping Log": [
        "raw_name", "canonical_name", "entity_type", "source",
        "confidence_score", "resolution_method", "timestamp"
    ]
}

TABLE_TO_TAB: Dict[str, str] = {
    "startups": "Startups",
    "products": "Products",
    "research_papers": "Research Papers",
    "jobs": "Jobs",
    "news": "News",
    "entity_mappings": "Entity Mapping Log"
}

class DataExporter:
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or settings.DATA_PROCESSED_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_csv_and_jsonl(self) -> Dict[str, Dict[str, str]]:
        """
        Exports all 6 database tables to CSV and JSONL files with exact schemas and headers.
        """
        exported_files: Dict[str, Dict[str, str]] = {}

        for table_name, tab_name in TABLE_TO_TAB.items():
            records = repo.fetch_all(table_name)
            headers = TAB_HEADERS[tab_name]

            # 1. Export CSV
            csv_path = self.output_dir / f"{table_name}.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for r in records:
                    row = []
                    for h in headers:
                        val = r.get(h)
                        if isinstance(val, (list, dict)):
                            val = json.dumps(val)
                        elif val is None:
                            val = ""
                        row.append(str(val))
                    writer.writerow(row)

            # 2. Export JSONL
            jsonl_path = self.output_dir / f"{table_name}.jsonl"
            with open(jsonl_path, "w", encoding="utf-8") as f:
                for r in records:
                    # Clean internal db id
                    clean_r = {k: v for k, v in r.items() if k != "id"}
                    f.write(json.dumps(clean_r, ensure_ascii=False, default=str) + "\n")

            exported_files[tab_name] = {
                "count": len(records),
                "csv": str(csv_path),
                "jsonl": str(jsonl_path)
            }
            logger.info(f"Exported {len(records)} records to {csv_path.name} and {jsonl_path.name}")

        return exported_files

    def export_google_sheets(self) -> Optional[str]:
        """
        Exports all 6 tabs to Google Sheets if service account credentials and spreadsheet ID are configured.
        """
        creds_path = settings.GOOGLE_APPLICATION_CREDENTIALS
        spreadsheet_id = settings.GOOGLE_SPREADSHEET_ID

        if not creds_path or not os.path.exists(creds_path):
            logger.info(
                "Google Application Credentials not found. Skipping Google Sheets API upload; CSV and JSONL files generated."
            )
            return None

        if not spreadsheet_id:
            logger.info("GOOGLE_SPREADSHEET_ID not configured. Skipping Google Sheets API upload.")
            return None

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            scopes = ["https://www.googleapis.com/auth/spreadsheets"]
            credentials = service_account.Credentials.from_service_account_file(
                creds_path, scopes=scopes
            )
            service = build("sheets", "v4", credentials=credentials)

            logger.info(f"Uploading 6 tabs to Google Spreadsheet: {spreadsheet_id}...")

            for table_name, tab_name in TABLE_TO_TAB.items():
                records = repo.fetch_all(table_name)
                headers = TAB_HEADERS[tab_name]

                values = [headers]
                for r in records:
                    row = []
                    for h in headers:
                        val = r.get(h)
                        if isinstance(val, (list, dict)):
                            val = json.dumps(val)
                        elif val is None:
                            val = ""
                        row.append(str(val))
                    values.append(row)

                # Ensure sheet tab exists
                try:
                    body = {
                        "requests": [{
                            "addSheet": {
                                "properties": {"title": tab_name}
                            }
                        }]
                    }
                    service.spreadsheets().batchUpdate(
                        spreadsheetId=spreadsheet_id, body=body
                    ).execute()
                except Exception:
                    # Sheet likely already exists
                    pass

                # Update data
                body = {"values": values}
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f"'{tab_name}'!A1",
                    valueInputOption="RAW",
                    body=body
                ).execute()

                logger.info(f"Uploaded {len(records)} rows to Google Sheets tab '{tab_name}'")

            return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        except Exception as e:
            logger.error(f"Failed to export to Google Sheets: {e}")
            return None

    def export_excel(self) -> str:
        """
        Exports all 6 tabs to a consolidated multi-tab Excel workbook formatted for direct Google Sheets import.
        """
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
            from openpyxl.utils import get_column_letter

            wb = openpyxl.Workbook()
            wb.remove(wb.active)  # Remove default empty sheet

            header_fill = PatternFill(start_color="1F1F1F", end_color="1F1F1F", fill_type="solid")
            header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")

            for table_name, tab_name in TABLE_TO_TAB.items():
                ws = wb.create_sheet(title=tab_name)
                headers = TAB_HEADERS[tab_name]
                records = repo.fetch_all(table_name)

                # Header
                ws.append(headers)
                for col_idx in range(1, len(headers) + 1):
                    cell = ws.cell(row=1, column=col_idx)
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="left", vertical="center")

                # Freeze header row
                ws.freeze_panes = "A2"

                # Rows
                for r in records:
                    row = []
                    for h in headers:
                        val = r.get(h)
                        if isinstance(val, (list, dict)):
                            val = json.dumps(val)
                        elif val is None:
                            val = ""
                        row.append(str(val))
                    ws.append(row)

                # Auto column width (sample first 100 rows)
                for col in ws.columns:
                    col_letter = get_column_letter(col[0].column)
                    max_len = max(len(str(cell.value or "")) for cell in col[:100])
                    ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 50)

            out_path = self.output_dir / "AETHER_AI_INTELLIGENCE_SUBMISSION.xlsx"
            wb.save(out_path)
            logger.info(f"Generated multi-tab Excel submission workbook: {out_path}")
            return str(out_path)
        except Exception as e:
            logger.error(f"Failed to generate Excel workbook: {e}")
            return ""

    def export_all(self) -> Dict[str, Any]:
        csv_jsonl_result = self.export_csv_and_jsonl()
        excel_path = self.export_excel()
        sheets_url = self.export_google_sheets()
        return {
            "files": csv_jsonl_result,
            "excel_path": excel_path,
            "google_sheets_url": sheets_url
        }

exporter = DataExporter()

if __name__ == "__main__":
    result = exporter.export_all()
    print("Export completed successfully:")
    print(f"  Excel: {result.get('excel_path')}")
    print(f"  Files: {len(result.get('files', {}))} datasets exported to CSV/JSONL")
    if result.get("google_sheets_url"):
        print(f"  Google Sheet: {result.get('google_sheets_url')}")


