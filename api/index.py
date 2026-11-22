import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.main import app

@app.api_route("/debug-info", methods=["GET", "HEAD"])
def debug_info():
    return {"status": "ok", "routes": [r.path for r in app.routes]}
