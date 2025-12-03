# tabs/id_converter.py
"""
Convert between XMLA GUIDs and API IDs for installer/container instances.
"""
import requests
from common import get_jwt, get_instance_type, load_config


class IdConverter:
    def __init__(self):
        self.config = load_config()
        self.instance_type = get_instance_type()
        self.jwt_token = get_jwt()
        self.headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
    
    def convert_catalog_guid_to_id(self, catalog_name, catalog_guid):
        """Convert XMLA catalog GUID to appropriate ID for instance type"""
        if self.instance_type == "installer":
            return self._get_installer_project_id(catalog_name, catalog_guid)
        elif self.instance_type == "container":
            return self._get_container_catalog_id(catalog_name, catalog_guid)
        return None
    
    def convert_cube_guid_to_id(self, catalog_name, cube_name, cube_guid):
        """Convert XMLA cube GUID to appropriate ID for instance type"""
        if self.instance_type == "installer":
            return self._get_installer_cube_id(cube_guid)
        elif self.instance_type == "container":
            return self._get_container_model_id(catalog_name, cube_name)
        return None
    
    def _get_installer_project_id(self, catalog_name, catalog_guid):
        """Get project ID for installer"""
        # For installer, try the catalog_guid first
        if catalog_guid:
            return catalog_guid
        
        # Fallback: try to get project by name
        host = self.config["host"]
        org = self.config["organization"]
        url = f"https://{host}:10502/projects/orgId/{org}"
        
        try:
            response = requests.get(url, headers=self.headers, verify=False, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "response" in data and "data" in data["response"]:
                for project in data["response"]["data"]:
                    if project.get("caption") == catalog_name:
                        return project.get("id")
        except Exception as e:
            print(f"Error getting installer project ID: {e}")
        
        return None
    
    def _get_installer_cube_id(self, cube_guid):
        """Get cube ID for installer - use GUID directly"""
        # For installer, cube_guid might be the cube ID
        return cube_guid
    
    def _get_container_catalog_id(self, catalog_name, catalog_guid):
        """Get catalog ID for container"""
        host = self.config["host"]
        url = f"https://{host}/wapi/p/catalogs"
        
        try:
            response = requests.get(url, headers=self.headers, verify=False, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            for catalog in data.get("catalogs", []):
                if catalog.get("name") == catalog_name:
                    return catalog.get("id")
        except Exception as e:
            print(f"Error getting container catalog ID: {e}")
        
        return None
    
    def _get_container_model_id(self, catalog_name, cube_name):
        """Get model ID for container"""
        # First get catalog ID
        catalog_id = self._get_container_catalog_id(catalog_name, None)
        if not catalog_id:
            return None
        
        host = self.config["host"]
        url = f"https://{host}/wapi/p/catalogs/{catalog_id}/models"
        
        try:
            response = requests.get(url, headers=self.headers, verify=False, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            for model in data.get("models", []):
                if model.get("name") == cube_name:
                    return model.get("id")
        except Exception as e:
            print(f"Error getting container model ID: {e}")
        
        return None