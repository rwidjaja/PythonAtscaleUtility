# tabs/query_history_mapping.py
"""
Helper module to map catalog/cube names to IDs for API calls.
"""
import requests
from common import get_jwt, get_instance_type, load_config


class QueryHistoryMapping:
    def __init__(self):
        self.config = load_config()
        self.instance_type = get_instance_type()
        self.jwt_token = get_jwt()
        self.headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
    
    def get_catalog_id_by_name(self, catalog_name):
        """Get catalog ID by name"""
        try:
            if self.instance_type == "installer":
                # Installer uses organization as catalog
                return self.config["organization"]
            elif self.instance_type == "container":
                # Need to call catalog API
                host = self.config["host"]
                url = f"https://{host}/wapi/p/catalogs"
                response = requests.get(url, headers=self.headers, verify=False, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                for catalog in data.get("catalogs", []):
                    if catalog.get("name") == catalog_name:
                        return catalog.get("id")
        except Exception as e:
            print(f"Error getting catalog ID: {e}")
        return None
    
    def get_cube_id_by_name(self, catalog_id, cube_name):
        """Get cube/model ID by name"""
        try:
            if self.instance_type == "installer":
                # For installer, we need to use XMLA discovery
                # This is complex, so we'll rely on name filtering for now
                return None
            elif self.instance_type == "container":
                # Get models in catalog
                host = self.config["host"]
                url = f"https://{host}/wapi/p/catalogs/{catalog_id}/models"
                response = requests.get(url, headers=self.headers, verify=False, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                for model in data.get("models", []):
                    if model.get("name") == cube_name:
                        return model.get("id")
        except Exception as e:
            print(f"Error getting cube ID: {e}")
        return None
    
    def get_project_id_by_catalog_name(self, catalog_name):
        """Get project ID from catalog name (installer only)"""
        if self.instance_type != "installer":
            return None
        
        try:
            # Try to get projects list
            host = self.config["host"]
            org = self.config["organization"]
            url = f"https://{host}:10502/projects/orgId/{org}"
            response = requests.get(url, headers=self.headers, verify=False, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if "response" in data and "data" in data["response"]:
                for project in data["response"]["data"]:
                    if project.get("caption") == catalog_name:
                        return project.get("id")
        except Exception as e:
            print(f"Error getting project ID: {e}")
        return None