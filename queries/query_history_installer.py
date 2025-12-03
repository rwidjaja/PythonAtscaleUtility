# tabs/query_history_installer.py
"""
Query history service for installer instances.
"""
import requests
from queries.query_history_base import QueryHistoryBase
from common import load_config, get_jwt, get_instance_type


class QueryHistoryInstaller(QueryHistoryBase):
    def __init__(self):
        super().__init__()
        self.config = load_config()
    
    # tabs/query_history_installer.py (updated sorting)
    def fetch_query_history(self, catalog_name=None, cube_name=None, catalog_id=None, cube_id=None):
        """
        Fetch query history from installer instance using project ID and cube ID.
        """
        jwt_token = get_jwt()
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
        
        host = self.config["host"]
        org = self.config["organization"]
        
        # Build URL with parameters
        url = f"https://{host}:10502/queries/orgId/{org}"
        params = {
            "limit": 100,
            "querySource": "user",
            "status": "success"
        }
        
        # Use catalog_id as projectId if provided
        if catalog_id and catalog_id.strip():
            params["projectId"] = catalog_id
            #print(f"[DEBUG] Using projectId: {catalog_id} for filtering")
        
        # Use cube_id if provided
        if cube_id and cube_id.strip():
            params["cubeId"] = cube_id
            #print(f"[DEBUG] Using cubeId: {cube_id} for filtering")
        
        queries = []
        
        try:
            response = requests.get(url, headers=headers, params=params, verify=False, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data and "response" in data and "data" in data["response"]:
                for query_data in data["response"]["data"]:
                    parsed = self._parse_query(query_data)
                    if parsed:
                        # Additional client-side filtering by cube name
                        if cube_name:
                            parsed_cube_name = parsed.get("cube_name", "")
                            if parsed_cube_name and cube_name.lower() not in parsed_cube_name.lower():
                                continue
                        queries.append(parsed)
            
            # Sort by start_time descending (most recent first)
            # Handle ISO datetime strings properly
            queries.sort(key=lambda x: self._parse_iso_datetime(x.get("start_time", "")), reverse=True)
            
            #print(f"[DEBUG] Loaded {len(queries)} queries, sorted by start_time")
            
            return queries
            
        except Exception as e:
            print(f"Error fetching installer query history: {e}")
            if 'response' in locals():
                print(f"Response status: {response.status_code}")
                print(f"Response text: {response.text[:500]}...")
            import traceback
            traceback.print_exc()
            return []
    

    # tabs/query_history_installer.py (updated _parse_query method)
    def _parse_query(self, query_data):
        """Parse installer API response into standardized format"""
        try:
            # Extract timeline event durations AND start time
            query_pre_planning = 0
            query_wall_time = 0
            subqueries_wall = 0
            subquery_count = 0
            use_aggregate = "N"
            start_time = ""  # Initialize start time
            
            timeline_events = query_data.get("timeline_events", [])
            for event in timeline_events:
                event_type = event.get("type", "")
                
                # Safely get duration
                duration = self._safe_get_duration(event)
                
                # Capture start time from QueryPrePlanning event
                if event_type == "QueryPrePlanning":
                    query_pre_planning = duration
                    # Get the started timestamp for sorting
                    started = event.get("started", "")
                    if started:
                        start_time = started
                elif event_type == "QueryWallTime":
                    query_wall_time = duration
                elif event_type == "SubqueriesWall":
                    subqueries_wall = duration
                    # Count subqueries in children
                    children = event.get("children", []) or []
                    subquery_count = len([c for c in children if isinstance(c, dict) and c.get("type") == "subquery_execution_info"])
                
                # Also check for SubqueryExec events directly
                elif event_type == "SubqueryExec":
                    subquery_count += 1
            
            # If no start_time found in QueryPrePlanning, try to get from first event
            if not start_time and timeline_events:
                first_event = timeline_events[0]
                started = first_event.get("started", "")
                if started:
                    start_time = started
            
            # Check if aggregates were used
            aggregates = query_data.get("aggregate_instance_table_names", []) or []
            if aggregates and len(aggregates) > 0:
                use_aggregate = "Y"
            
            # Determine query language - analysis -> MDX, else -> SQL
            query_language = query_data.get("query_language", "")
            query_language = self._determine_query_language(query_language)
            
            # Safely get cube name
            cube_name = query_data.get("cube_caption") or query_data.get("cube_name", "")
            if cube_name is None:
                cube_name = ""
            
            # Get query text - check multiple possible fields
            query_text = ""
            if "query_text" in query_data and query_data["query_text"]:
                query_text = query_data["query_text"]
            elif "query" in query_data and query_data["query"]:
                query_text = query_data["query"]
            elif "original_query" in query_data and query_data["original_query"]:
                query_text = query_data["original_query"]
            
            # Clean up query text if needed
            if query_text:
                query_text = query_text.strip()
            
            return {
                "cube_name": cube_name,
                "query_id": query_data.get("query_id", ""),
                "user_id": query_data.get("user_id", ""),
                "query_language": query_language,
                "query_pre_planning": round(query_pre_planning * 1000, 2) if query_pre_planning else 0,
                "query_wall_time": round(query_wall_time * 1000, 2) if query_wall_time else 0,
                "subquery_count": subquery_count,
                "subqueries_wall": round(subqueries_wall * 1000, 2) if subqueries_wall else 0,
                "use_aggregate": use_aggregate,
                "query_text": query_text,
                "start_time": start_time,  # Now properly extracted from timeline_events
                "original_data": query_data
            }
        except Exception as e:
            print(f"Error parsing installer query: {e}")
            import traceback
            traceback.print_exc()
            return None