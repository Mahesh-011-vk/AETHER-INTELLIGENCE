#!/usr/bin/env python3
"""
Build script for Aether AI Intelligence.
Packages frontend templates and static assets into dist/ for static verification and audit checks.
"""
import os
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
DIST_DIR = ROOT_DIR / "dist"

def build():
    print(f"Building distribution into {DIST_DIR}...")
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Main index.html
    shutil.copy(SRC_DIR / "templates" / "index.html", DIST_DIR / "index.html")

    # 2. /privacy page
    (DIST_DIR / "privacy").mkdir(parents=True, exist_ok=True)
    shutil.copy(SRC_DIR / "templates" / "privacy.html", DIST_DIR / "privacy" / "index.html")

    # 3. /terms page
    (DIST_DIR / "terms").mkdir(parents=True, exist_ok=True)
    shutil.copy(SRC_DIR / "templates" / "terms.html", DIST_DIR / "terms" / "index.html")

    # 4. /404 page
    shutil.copy(SRC_DIR / "templates" / "404.html", DIST_DIR / "404.html")

    # 5. Styles (tokens.css)
    styles_dir = SRC_DIR / "styles"
    if styles_dir.exists():
        shutil.copytree(styles_dir, DIST_DIR / "styles")

    # 6. Static assets
    static_dir = SRC_DIR / "static"
    if static_dir.exists():
        shutil.copytree(static_dir, DIST_DIR / "static")
        # Also copy assets directly to dist/assets for flat compatibility
        if (static_dir / "assets").exists():
            shutil.copytree(static_dir / "assets", DIST_DIR / "assets")

        # Copy root static files (favicons, manifests, robots, sitemap)
        for fname in ["favicon.svg", "favicon.ico", "apple-touch-icon.png", "site.webmanifest", "robots.txt", "sitemap.xml"]:
            src_f = static_dir / fname
            if src_f.exists():
                shutil.copy(src_f, DIST_DIR / fname)

    print("Build complete. Output files:")
    for root, _, files in os.walk(DIST_DIR):
        for f in sorted(files):
            rel = os.path.relpath(os.path.join(root, f), DIST_DIR)
            print(f" - {rel}")

if __name__ == "__main__":
    build()

