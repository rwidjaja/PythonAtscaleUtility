# tabs/query_history_base.py
"""
Base class for query history services.
"""
from common import get_jwt, get_instance_type, load_config
import datetime


class QueryHistoryBase:
    def __init__(self):
        self.config = load_config()
        self.instance_type = get_instance_type()
    
    def _safe_get_duration(self, event, key="duration", default=0):
        """Safely get duration value, handling None and converting to float"""
        try:
            value = event.get(key, default)
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default
    
    def _safe_lower(self, text):
        """Safely convert text to lowercase, handling None"""
        if text is None:
            return ""
        return str(text).lower()
    
    def _determine_query_language(self, query_language):
        """Determine query language: analysis -> MDX, else -> SQL"""
        if query_language == "analysis":
            return "MDX"
        else:
            return "SQL"
    
    def _parse_iso_datetime(self, datetime_str):
        """Parse ISO datetime string to datetime object"""
        try:
            if not datetime_str:
                return datetime.datetime.min
            # Remove microseconds if present
            if '.' in datetime_str:
                datetime_str = datetime_str.split('.')[0] + 'Z'
            # Parse ISO format
            return datetime.datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except Exception:
            return datetime.datetime.min