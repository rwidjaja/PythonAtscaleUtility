# tabs/id_mapping_helper.py
"""
Helper to map between catalog/cube names and IDs for API calls.
"""
import requests
from common import get_jwt, get_instance_type, load_config


class IdMappingHelper:
    def __init__(self):
        self.config = load_config()
        self.instance_type = get_instance_type()
        self.jwt_token = get_jwt()
        self.headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        
        # Cache for mappings
        self.catalog_name_to_id = {}
        self.cube_name_to_id = {}
        
    def get_catalog_id(self, catalog_name):
        """Get catalog ID from catalog name"""
        if catalog_name in self.catalog_name_to_id:
            return self.catalog_name_to_id[catalog_name]
        
        if self.instance_type == "installer":
            # For installer, catalog maps to organization/project
            # We'll use project caption as catalog name
            project_id = self.get_project_id(catalog_name)
            if project_id:
                self.catalog_name_to_id[catalog_name] = project_id
                return project_id
        elif self.instance_type == "container":
            # Fetch catalog list
            host = self.config["host"]
            url = f"https://{host}/wapi/p/catalogs"
            
            try:
                response = requests.get(url, headers=self.headers, verify=False, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                for catalog in data.get("catalogs", []):
                    if catalog.get("name") == catalog_name:
                        catalog_id = catalog.get("id")
                        self.catalog_name_to_id[catalog_name] = catalog_id
                        return catalog_id
            except Exception as e:
                print(f"Error fetching catalogs: {e}")
        
        return None
    
    def get_project_id(self, project_name):
        """Get project ID from project name (installer only)"""
        if self.instance_type != "installer":
            return None
        
        host = self.config["host"]
        org = self.config["organization"]
        url = f"https://{host}:10502/projects/orgId/{org}"
        
        try:
            response = requests.get(url, headers=self.headers, verify=False, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "response" in data and "data" in data["response"]:
                for project in data["response"]["data"]:
                    if project.get("caption") == project_name:
                        return project.get("id")
        except Exception as e:
            print(f"Error fetching projects: {e}")
        
        return None
    
    def get_cube_id(self, catalog_name, cube_name):
        """Get cube/model ID from cube name"""
        cache_key = f"{catalog_name}:{cube_name}"
        if cache_key in self.cube_name_to_id:
            return self.cube_name_to_id[cache_key]
        
        if self.instance_type == "installer":
            # For installer, we need to use XMLA discovery or other methods
            # This is complex - return None for now
            return None
            
        elif self.instance_type == "container":
            # Get catalog ID first
            catalog_id = self.get_catalog_id(catalog_name)
            if not catalog_id:
                return None
            
            # Get models in catalog
            host = self.config["host"]
            url = f"https://{host}/wapi/p/catalogs/{catalog_id}/models"
            
            try:
                response = requests.get(url, headers=self.headers, verify=False, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                for model in data.get("models", []):
                    if model.get("name") == cube_name:
                        model_id = model.get("id")
                        self.cube_name_to_id[cache_key] = model_id
                        return model_id
            except Exception as e:
                print(f"Error fetching models: {e}")
        
        return None