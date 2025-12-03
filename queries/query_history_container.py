# tabs/query_history_container.py
"""
Query history service for container instances.
"""
import requests
from queries.query_history_base import QueryHistoryBase
from queries.id_mapping_helper import IdMappingHelper


class QueryHistoryContainer(QueryHistoryBase):
    def __init__(self):
        super().__init__()
        self.mapping_helper = IdMappingHelper()
    
    def fetch_query_history(self, catalog_name=None, cube_name=None, catalog_id=None, model_id=None):
        """
        Fetch query history from container instance with proper filtering.
        """
        jwt_token = get_jwt()
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
        
        host = self.config["host"]
        
        # Build URL with parameters
        url = f"https://{host}/wapi/p/queries"
        params = {
            "page": 1,
            "showCanaries": "false",
            "status": "successful",
            "queryType": "User"
        }
        
        # Add catalog ID if provided
        if catalog_id:
            params["catalogId"] = catalog_id
        
        # Add model ID if provided
        if model_id:
            params["modelId"] = model_id
        
        queries = []
        
        try:
            response = requests.get(url, headers=headers, params=params, verify=False, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data and "results" in data:
                for query_data in data["results"]:
                    parsed = self._parse_query(query_data)
                    if parsed:
                        # Additional filtering by cube name if provided
                        if cube_name:
                            parsed_cube_name = parsed.get("cube_name", "")
                            if parsed_cube_name and cube_name.lower() not in self._safe_lower(parsed_cube_name):
                                continue
                        queries.append(parsed)
            
            # Sort by query wall time (most recent first)
            queries.sort(key=lambda x: x["query_wall_time"], reverse=True)
            
            return queries
            
        except Exception as e:
            print(f"Error fetching container query history: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_query(self, query_data):
        """Parse container API response into standardized format"""
        try:
            # Extract durations from events
            query_pre_planning = 0
            query_wall_time = 0
            subqueries_wall = 0
            subquery_count = 0
            use_aggregate = "N"
            
            events = query_data.get("events", []) or []
            for event in events:
                event_name = event.get("name", "")
                
                # Safely get duration
                duration = self._safe_get_duration(event)
                
                if event_name == "Planning":
                    query_pre_planning = duration
                elif event_name == "Inbound Query":
                    query_wall_time = duration
                elif event_name == "Outbound":
                    subqueries_wall = duration
                    # Count subqueries
                    subqueries = event.get("subqueries", []) or []
                    subquery_count = len(subqueries)
            
            # Check if aggregates were used
            aggregates = query_data.get("aggregatesTables", []) or []
            if aggregates and len(aggregates) > 0:
                use_aggregate = "Y"
            
            # Safely get cube name
            cube_name = query_data.get("modelName", "")
            if cube_name is None:
                cube_name = ""
            
            # Container query language mapping
            # Note: Container API doesn't provide query_language directly in the response
            # We need to check if there's a queryType or optimization field
            query_language = "SQL"  # Default to SQL for container
            
            # Check if we can determine from query type or optimization
            query_type = query_data.get("queryType", "")
            optimization = query_data.get("optimization", [])
            
            if "analysis" in str(query_type).lower() or "analysis" in str(optimization).lower():
                query_language = "MDX"
            
            return {
                "cube_name": cube_name,
                "query_id": query_data.get("queryId", ""),
                "user_id": query_data.get("userId", ""),
                "query_language": query_language,
                "query_pre_planning": round(query_pre_planning, 2) if query_pre_planning else 0,
                "query_wall_time": round(query_wall_time, 2) if query_wall_time else 0,
                "subquery_count": subquery_count,
                "subqueries_wall": round(subqueries_wall, 2) if subqueries_wall else 0,
                "use_aggregate": use_aggregate,
                "query_text": "",  # Container doesn't provide query text in this endpoint
                "catalog_id": query_data.get("catalogId", ""),
                "model_id": query_data.get("modelId", ""),
                "original_data": query_data
            }
        except Exception as e:
            print(f"Error parsing container query: {e}")
            import traceback
            traceback.print_exc()
            return None