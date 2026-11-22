from datetime import datetime, timezone, timedelta
from typing import Optional, Any
import dateutil.parser
import re
from src.utils.logging import logger

class DateExtractor:
    @staticmethod
    def parse_datetime(raw_date: Any) -> Optional[datetime]:
        """
        Parses various date formats into a strict timezone-aware UTC datetime.
        Supports ISO 8601, RFC 2822, UNIX timestamps, and relative expressions.
        """
        if not raw_date:
            return None

        if isinstance(raw_date, datetime):
            if raw_date.tzinfo is None:
                return raw_date.replace(tzinfo=timezone.utc)
            return raw_date.astimezone(timezone.utc)

        if isinstance(raw_date, (int, float)):
            # Handle timestamps (seconds or milliseconds)
            ts = float(raw_date)
            if ts > 1e11:  # milliseconds
                ts /= 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc)

        date_str = str(raw_date).strip()

        # Handle relative dates like "2 hours ago", "30 minutes ago", "1 day ago"
        now = datetime.now(timezone.utc)
        rel_match = re.search(r"(\d+)\s+(minute|hour|day|week|month)s?\s+ago", date_str, re.IGNORECASE)
        if rel_match:
            val = int(rel_match.group(1))
            unit = rel_match.group(2).lower()
            if unit == "minute":
                return now - timedelta(minutes=val)
            elif unit == "hour":
                return now - timedelta(hours=val)
            elif unit == "day":
                return now - timedelta(days=val)
            elif unit == "week":
                return now - timedelta(weeks=val)
            elif unit == "month":
                return now - timedelta(days=val * 30)

        # Standard dateutil parser
        try:
            dt = dateutil.parser.parse(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except Exception as e:
            logger.debug(f"Could not parse date string '{date_str}': {e}")
            return None

    @staticmethod
    def is_within_rolling_window(dt: Optional[datetime], hours: int = 24) -> bool:
        """
        Verifies if datetime is within the specified rolling window up to current UTC time.
        Allows up to 15 minutes of future tolerance for minor clock skew.
        """
        if dt is None:
            return False

        now = datetime.now(timezone.utc)
        earliest_allowed = now - timedelta(hours=hours)
        latest_allowed = now + timedelta(minutes=15)

        return earliest_allowed <= dt <= latest_allowed

