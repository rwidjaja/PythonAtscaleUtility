# aggregate/api_client.py
import requests
import json
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
    
    def unblock_aggregate(self, definition_id: str, instance_id: str) -> Dict:
        """Unblock an aggregate - TWO CALLS REQUIRED:
        1. Without instanceId (just definitionId)
        2. With instanceId
        """
        host = self.config["host"]
        org = self.config["organization"]
        
        results = {
            "first_call": None,
            "second_call": None,
            "overall_success": False
        }
        
        # FIRST CALL: Without instanceId
        url1 = f"https://{host}:10502/aggregates/orgId/{org}/definitionId/{definition_id}?unblock=true"
        
        try:
            response1 = requests.put(
                url1, 
                headers=self._get_headers(), 
                verify=False, 
                timeout=30
            )
            
            try:
                result1 = response1.json()
                results["first_call"] = {
                    "status_code": response1.status_code,
                    "result": result1,
                    "updated": result1.get("response", {}).get("updated", False)
                }
            except json.JSONDecodeError:
                results["first_call"] = {
                    "status_code": response1.status_code,
                    "result": {"text": response1.text[:200]}
                }
                
        except requests.exceptions.RequestException as e:
            results["first_call"] = {
                "error": str(e)
            }
        
        # SECOND CALL: With instanceId (even if first call failed)
        url2 = f"https://{host}:10502/aggregates/orgId/{org}/definitionId/{definition_id}/instanceId/{instance_id}?unblock=true"
        
        try:
            response2 = requests.put(
                url2, 
                headers=self._get_headers(), 
                verify=False, 
                timeout=30
            )
            
            try:
                result2 = response2.json()
                results["second_call"] = {
                    "status_code": response2.status_code,
                    "result": result2,
                    "updated": result2.get("response", {}).get("updated", False)
                }
            except json.JSONDecodeError:
                results["second_call"] = {
                    "status_code": response2.status_code,
                    "result": {"text": response2.text[:200]}
                }
                
        except requests.exceptions.RequestException as e:
            results["second_call"] = {
                "error": str(e)
            }
        
        # Determine overall success
        # Success if either call returned updated: true or if second call completed (even with updated: false)
        if results["first_call"] and results["first_call"].get("updated") is True:
            results["overall_success"] = True
        elif results["second_call"] and results["second_call"].get("status_code") in [200, 0]:
            results["overall_success"] = True
        elif results["second_call"] and results["second_call"].get("updated") is False:
            # Even if updated: false, the call succeeded
            results["overall_success"] = True
        
        return results
    
    def block_aggregate(self, definition_id: str, instance_id: str) -> Dict:
        """Block an aggregate (single call with instanceId)"""
        host = self.config["host"]
        org = self.config["organization"]
        
        # Build URL
        url = f"https://{host}:10502/aggregates/orgId/{org}/definitionId/{definition_id}/instanceId/{instance_id}?block=true"
        
        try:
            response = requests.delete(
                url, 
                headers=self._get_headers(), 
                verify=False, 
                timeout=30
            )
            
            try:
                result = response.json()
                return {
                    "status_code": response.status_code,
                    "result": result,
                    "deleted": result.get("response", {}).get("deleted", False)
                }
            except json.JSONDecodeError:
                return {
                    "status_code": response.status_code,
                    "result": {"text": response.text[:200]}
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e)
            }