import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Dict

class SecretMaskingFilter(logging.Filter):
    def __init__(self, secrets_to_mask=None):
        super().__init__()
        self.secrets = [s for s in (secrets_to_mask or []) if s and len(s) > 4]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for secret in self.secrets:
                if secret in record.msg:
                    record.msg = record.msg.replace(secret, "[MASKED_SECRET]")
        return True

def setup_logger(name: str = "ai_pipeline", level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    from config.settings import settings
    secrets = [
        settings.GEMINI_API_KEY,
        settings.GROQ_API_KEY,
        settings.DEEPSEEK_API_KEY,
        settings.GITHUB_TOKEN
    ]
    handler.addFilter(SecretMaskingFilter(secrets))
    return logger

logger = setup_logger()

