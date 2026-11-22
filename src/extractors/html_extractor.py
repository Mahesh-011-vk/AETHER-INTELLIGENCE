import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from src.utils.logging import logger

class HTMLExtractor:
    @staticmethod
    def extract_clean_text(html_content: str, max_chars: int = 8000) -> str:
        """
        Strips scripts, styling, navigation, and noise. Returns concise readable text.
        """
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, "html.parser")

        # Remove irrelevant noise elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg", "form"]):
            tag.decompose()

        # Get text
        text = soup.get_text(separator="\n")

        # Clean multiple spaces and blank lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars] + "\n...[truncated]"

        return clean_text

    @staticmethod
    def extract_metadata(html_content: str) -> Dict[str, Optional[str]]:
        """
        Extracts title, meta description, and open graph / twitter metadata.
        """
        if not html_content:
            return {}

        soup = BeautifulSoup(html_content, "html.parser")
        metadata: Dict[str, Optional[str]] = {
            "title": None,
            "description": None,
            "canonical_url": None,
            "og_title": None,
            "og_description": None,
            "og_image": None,
            "published_time": None
        }

        if soup.title and soup.title.string:
            metadata["title"] = soup.title.string.strip()

        desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        if desc_tag and desc_tag.get("content"):
            metadata["description"] = desc_tag["content"].strip()

        canonical_tag = soup.find("link", rel="canonical")
        if canonical_tag and canonical_tag.get("href"):
            metadata["canonical_url"] = canonical_tag["href"].strip()

        for prop, key in [
            ("og:title", "og_title"),
            ("og:description", "og_description"),
            ("og:image", "og_image"),
            ("article:published_time", "published_time")
        ]:
            meta = soup.find("meta", property=prop)
            if meta and meta.get("content"):
                metadata[key] = meta["content"].strip()

        return metadata

