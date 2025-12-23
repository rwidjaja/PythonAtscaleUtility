# aggregate/api_client.py
import requests
from typing import Dict, List, Optional, Any
from common import get_jwt, load_config


class AtScaleAPIClient:
    def __init__(self):
        self.config = load_config()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with JWT token"""
        return {
            "Authorization": f"Bearer {get_jwt()}",
            "Content-Type": "application/json",
        }
    
    def get_published_projects(self) -> List[Dict]:
        """Get published projects with cubes"""
        host = self.config["host"]
        
        if self.config.get("instance_type") == "installer":
            org = self.config["organization"]
            url = f"https://{host}:10502/projects/published/orgId/{org}"
        else:
            url = f"https://{host}/api/v1/projects/published"
        
        response = requests.get(url, headers=self._get_headers(), verify=False, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("response", [])
    
    def get_aggregates_by_cube(self, project_id: str, cube_id: str, limit: int = 200) -> Dict:
        """Get aggregates for a specific cube"""
        host = self.config["host"]
        
        if self.config.get("instance_type") == "installer":
            org = self.config["organization"]
            url = f"https://{host}:10502/aggregates/orgId/{org}?limit={limit}&projectId={project_id}&cubeId={cube_id}"
        else:
            url = f"https://{host}/api/v1/aggregates?limit={limit}&projectId={project_id}&cubeId={cube_id}"
        
        response = requests.get(url, headers=self._get_headers(), verify=False, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_aggregate_build_history(self, project_id: str, cube_id: str, limit: int = 20) -> Dict:
        """Get aggregate build history for a specific cube"""
        host = self.config["host"]
        
        if self.config.get("instance_type") == "installer":
            org = self.config["organization"]
            url = f"https://{host}:10502/aggregate-batch/orgId/{org}/history?limit={limit}&projectId={project_id}&cubeId={cube_id}"
        else:
            url = f"https://{host}/api/v1/aggregates/build-history?limit={limit}&projectId={project_id}&cubeId={cube_id}"
        
        response = requests.get(url, headers=self._get_headers(), verify=False, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def activate_aggregate(self, aggregate_id: str) -> Dict:
        """Activate an aggregate"""
        # TODO: Implement actual API call
        # This is a placeholder
        host = self.config["host"]
        
        if self.config.get("instance_type") == "installer":
            org = self.config["organization"]
            url = f"https://{host}:10502/aggregates/{aggregate_id}/activate"
        else:
            url = f"https://{host}/api/v1/aggregates/{aggregate_id}/activate"
        
        # For now, just return success
        return {"status": "success", "message": "Aggregate activated"}
    
    def deactivate_aggregate(self, aggregate_id: str) -> Dict:
        """Deactivate an aggregate"""
        # TODO: Implement actual API call
        # This is a placeholder
        host = self.config["host"]
        
        if self.config.get("instance_type") == "installer":
            org = self.config["organization"]
            url = f"https://{host}:10502/aggregates/{aggregate_id}/deactivate"
        else:
            url = f"https://{host}/api/v1/aggregates/{aggregate_id}/deactivate"
        
        # For now, just return success
        return {"status": "success", "message": "Aggregate deactivated"}