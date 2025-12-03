# tabs/query_history_json_parser.py
"""
Helper to parse JSON files for testing query history display.
"""
import json
from queries.query_history_service import QueryHistoryService


class JsonQueryHistoryParser:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.history_service = QueryHistoryService()
    
    def parse_from_file(self, instance_type="installer"):
        """Parse queries from JSON file"""
        try:
            with open(self.json_file_path, 'r') as f:
                data = json.load(f)
            
            queries = []
            
            if instance_type == "installer":
                if "response" in data and "data" in data["response"]:
                    for query_data in data["response"]["data"]:
                        parsed = self.history_service._parse_installer_query(query_data)
                        if parsed:
                            queries.append(parsed)
            
            elif instance_type == "container":
                if "results" in data:
                    for query_data in data["results"]:
                        parsed = self.history_service._parse_container_query(query_data)
                        if parsed:
                            queries.append(parsed)
            
            return queries
            
        except Exception as e:
            print(f"Error parsing JSON file: {e}")
            return []