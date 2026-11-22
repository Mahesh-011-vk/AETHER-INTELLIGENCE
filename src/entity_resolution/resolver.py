import re
from typing import Dict, Tuple, List, Optional
from datetime import datetime, timezone
from rapidfuzz import fuzz, process
from config.settings import settings
from src.models.schemas import EntityMappingRecord
from src.utils.logging import logger

LEGAL_SUFFIXES = [
    r"\binc(?:\.|\b)",
    r"\bincorporated\b",
    r"\bllc\b",
    r"\bltd(?:\.|\b)",
    r"\blimited\b",
    r"\bcorp(?:\.|\b)",
    r"\bcorporation\b",
    r"\bco(?:\.|\b)",
    r"\bcompany\b",
    r"\btechnologies\b",
    r"\btech\b",
    r"\bgmbh\b",
    r"\bs\.?a\.?\b",
    r"\bpvt(?:\.|\b)",
    r"\bplc\b",
    r"\bpbc\b",
]

PREDEFINED_CANONICALS: Dict[str, str] = {
    "google": "Google",
    "google llc": "Google",
    "alphabet": "Google",
    "alphabet inc": "Google",
    "deepmind": "Google DeepMind",
    "google deepmind": "Google DeepMind",
    "openai": "OpenAI",
    "openai inc": "OpenAI",
    "openai llc": "OpenAI",
    "anthropic": "Anthropic",
    "anthropic pbc": "Anthropic",
    "microsoft": "Microsoft",
    "microsoft corp": "Microsoft",
    "microsoft corporation": "Microsoft",
    "meta": "Meta",
    "meta platforms": "Meta",
    "meta platforms inc": "Meta",
    "facebook": "Meta",
    "mistral": "Mistral AI",
    "mistral ai": "Mistral AI",
    "cohere": "Cohere",
    "cohere inc": "Cohere",
    "huggingface": "Hugging Face",
    "hugging face": "Hugging Face",
    "hugging face inc": "Hugging Face",
    "perplexity": "Perplexity AI",
    "perplexity ai": "Perplexity AI",
    "stability": "Stability AI",
    "stability ai": "Stability AI",
    "scale ai": "Scale AI",
    "scale computing": "Scale AI",
    "xai": "xAI",
    "x ai": "xAI",
    "nvidia": "NVIDIA",
    "nvidia corporation": "NVIDIA",
    "apple": "Apple",
    "apple inc": "Apple",
    "amazon": "Amazon",
    "amazon web services": "Amazon Web Services",
    "aws": "Amazon Web Services",
}

class EntityResolver:
    def __init__(self, threshold: float = 85.0):
        self.threshold = threshold
        # Maps normalized key -> canonical display name
        self._registry: Dict[str, str] = {}
        # Prepopulate with standard canonical entities
        for k, v in PREDEFINED_CANONICALS.items():
            self._registry[self.normalize(k)] = v

    @staticmethod
    def normalize(name: str) -> str:
        """
        Deterministic normalization: lowercase, strip punctuation, remove legal suffixes, collapse whitespace.
        """
        if not name:
            return ""

        text = name.strip().lower()

        # Remove legal suffixes
        for suffix_pat in LEGAL_SUFFIXES:
            text = re.sub(suffix_pat, "", text, flags=re.IGNORECASE)

        # Remove special characters / punctuation
        text = re.sub(r"[^\w\s-]", "", text)

        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def resolve(self, raw_name: str, entity_type: str, source: str) -> Tuple[str, EntityMappingRecord]:
        """
        Resolves a raw name into a canonical name. Returns canonical name and audit record.
        """
        if not raw_name or not raw_name.strip():
            raw_name = "Unknown"

        raw_trimmed = raw_name.strip()
        norm = self.normalize(raw_trimmed)

        # 1. Exact match in registry
        if norm in self._registry:
            canonical = self._registry[norm]
            record = EntityMappingRecord(
                raw_name=raw_trimmed,
                canonical_name=canonical,
                entity_type=entity_type,
                source=source,
                confidence_score=100.0 if raw_trimmed == canonical else 95.0,
                resolution_method="ExactRegistry" if raw_trimmed == canonical else "RuleNormalized",
                timestamp=datetime.now(timezone.utc)
            )
            return canonical, record

        # 2. Fuzzy match against existing normalized candidates
        candidates = list(self._registry.keys())
        if candidates and len(norm) > 3:
            best_match = process.extractOne(
                norm,
                candidates,
                scorer=fuzz.token_sort_ratio
            )
            if best_match:
                matched_key, score, _ = best_match
                if score >= self.threshold:
                    # Prevent false positive merges for short or disparate names
                    len_ratio = len(norm) / max(len(matched_key), 1)
                    if 0.6 <= len_ratio <= 1.6:
                        canonical = self._registry[matched_key]
                        record = EntityMappingRecord(
                            raw_name=raw_trimmed,
                            canonical_name=canonical,
                            entity_type=entity_type,
                            source=source,
                            confidence_score=round(float(score), 2),
                            resolution_method="RapidFuzzMatch",
                            timestamp=datetime.now(timezone.utc)
                        )
                        # Cache raw norm to speed up future lookups
                        self._registry[norm] = canonical
                        return canonical, record

        # 3. New Canonical Entity
        # Capitalize nicely if not capitalized
        canonical = raw_trimmed
        self._registry[norm] = canonical
        record = EntityMappingRecord(
            raw_name=raw_trimmed,
            canonical_name=canonical,
            entity_type=entity_type,
            source=source,
            confidence_score=100.0,
            resolution_method="NewCanonical",
            timestamp=datetime.now(timezone.utc)
        )
        return canonical, record

resolver = EntityResolver(threshold=settings.RAPIDFUZZ_SIMILARITY_THRESHOLD)

