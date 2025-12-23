# aggregate/build_history.py
from datetime import datetime
from typing import Dict, List
from .api_client import AtScaleAPIClient


class BuildHistory:
    def __init__(self):
        self.api_client = AtScaleAPIClient()
    
    def get_build_history(self, cube_data: Dict, limit: int = 20) -> List[Dict]:
        """Get build history for a cube"""
        response = self.api_client.get_aggregate_build_history(
            cube_data["project_id"],
            cube_data["cube_id"],
            limit
        )
        
        return response.get("response", {}).get("data", [])