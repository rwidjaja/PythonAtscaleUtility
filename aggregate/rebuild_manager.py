# aggregate/rebuild_manager.py
import requests
from typing import Dict
from common import get_jwt, load_config


class RebuildManager:
    def __init__(self):
        self.config = load_config()
    
    def execute_rebuild(self, project_id: str, cube_id: str) -> Dict:
        """Execute the rebuild API call"""
        host = self.config["host"]
        jwt = get_jwt()
        
        if self.config.get("instance_type") == "installer":
            org = self.config["organization"]
            url = f"https://{host}:10502/aggregate-batch/orgId/{org}/projectId/{project_id}?cubeId={cube_id}&isFullBuild=true"
        else:
            url = f"https://{host}/api/v1/projects/{project_id}/cubes/{cube_id}/rebuild?isFullBuild=true"
        
        headers = {
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, verify=False, timeout=60)
        response.raise_for_status()
        
        try:
            return response.json()
        except:
            return {"status": "success", "message": response.text[:200]}