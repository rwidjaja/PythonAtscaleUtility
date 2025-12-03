# tabs/query_history_service.py (refactored)
"""
Main query history service that delegates to installer or container specific services.
"""
from queries.query_history_installer import QueryHistoryInstaller
from queries.query_history_container import QueryHistoryContainer
from common import get_jwt, get_instance_type, load_config
import requests


class QueryHistoryService:
    def __init__(self):
        self.config = load_config()
        self.instance_type = get_instance_type()
        self.history_service = None
        
        # Initialize the appropriate service based on instance type
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize the appropriate history service"""
        if self.instance_type == "installer":
            from .query_history_installer import QueryHistoryInstaller
            self.history_service = QueryHistoryInstaller()
        elif self.instance_type == "container":
            from .query_history_container import QueryHistoryContainer
            self.history_service = QueryHistoryContainer()
        else:
            print(f"Warning: Unknown instance type: {self.instance_type}")
    
    def fetch_query_history(self, catalog_name=None, cube_name=None, catalog_id=None, cube_id=None):
        """
        Fetch query history with proper ID filtering.
        """
        if not self.history_service:
            print("Error: No history service available for instance type:", self.instance_type)
            return []
        
        try:
            # Get queries from the appropriate service
            queries = self.history_service.fetch_query_history(
                catalog_name=catalog_name,
                cube_name=cube_name,
                catalog_id=catalog_id,
                cube_id=cube_id
            )
            
            # The service already sorts by start_time, but we'll do it here too for safety
            # Use datetime parsing for consistent sorting
            queries.sort(key=lambda x: self.history_service._parse_iso_datetime(x.get("start_time", "")), reverse=True)
            
            return queries
        except Exception as e:
            print(f"Error fetching query history: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_query_history_service(self):
        """Get the underlying service (for direct access if needed)"""
        return self.history_service
    
    def get_query_history_service(self):
        """Get the underlying service (for direct access if needed)"""
        return self.history_service
    
    def _parse_installer_query(self, query_data):
        """Parse installer API response"""
        try:
            # Extract timeline event durations
            query_pre_planning = 0
            query_wall_time = 0
            subqueries_wall = 0
            subquery_count = 0
            use_aggregate = "N"
            
            timeline_events = query_data.get("timeline_events", [])
            for event in timeline_events:
                event_type = event.get("type", "")
                duration = event.get("duration", 0) or 0
                
                if event_type == "QueryPrePlanning":
                    query_pre_planning = duration
                elif event_type == "QueryWallTime":
                    query_wall_time = duration
                elif event_type == "SubqueriesWall":
                    subqueries_wall = duration
                    # Count subqueries in children
                    children = event.get("children", []) or []
                    subquery_count = len([c for c in children if isinstance(c, dict) and c.get("type") == "subquery_execution_info"])
            
            # Check if aggregates were used
            aggregates = query_data.get("aggregate_instance_table_names", []) or []
            if aggregates and len(aggregates) > 0:
                use_aggregate = "Y"
            
            # Determine query language
            query_language = query_data.get("query_language", "")
            if query_language == "analysis":
                query_language = "MDX"
            else:
                query_language = "SQL"
            
            # Get cube name
            cube_name = query_data.get("cube_caption") or query_data.get("cube_name", "") or ""
            
            return {
                "cube_name": cube_name,
                "query_id": query_data.get("query_id", ""),
                "user_id": query_data.get("user_id", ""),
                "query_language": query_language,
                "query_pre_planning": round(query_pre_planning * 1000, 2),
                "query_wall_time": round(query_wall_time * 1000, 2),
                "subquery_count": subquery_count,
                "subqueries_wall": round(subqueries_wall * 1000, 2),
                "use_aggregate": use_aggregate,
                "query_text": query_data.get("query_text", "")
            }
        except Exception as e:
            print(f"Error parsing query: {e}")
            return None