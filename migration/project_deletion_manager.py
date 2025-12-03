# [file name]: project_deletion_manager.py
# [file content begin]
import tkinter as tk
import requests
from common import append_log, get_jwt

class ProjectDeletionManager:
    def __init__(self, config, log_ref_container, installer_data_manager):
        self.config = config
        self.log_ref_container = log_ref_container
        self.installer_data_manager = installer_data_manager

    def delete_selected_project(self, selected_indices):
        """Delete the selected project from AtScale"""
        if not selected_indices:
            append_log(self.log_ref_container[0], "No item selected for deletion")
            return False
        
        # For now, we'll handle the first selected item
        index = selected_indices[0]
        item_data = self.installer_data_manager.get_item_data_by_index(index)
        
        if not item_data or item_data.get("type") != "project":
            append_log(self.log_ref_container[0], "Please select a project to delete")
            return False
        
        project_id = item_data.get("project_data", {}).get("id")
        project_name = item_data.get("project_name")
        
        if not project_id:
            append_log(self.log_ref_container[0], "Could not find project ID for selected project")
            return False
        
        # Confirm deletion - emphasize this deletes the ENTIRE project
        import tkinter.messagebox as messagebox
        result = messagebox.askyesno(
            "Confirm Delete Project", 
            f"WARNING: This will delete the ENTIRE PROJECT from AtScale!\n\n"
            f"Project: {project_name}\n\n"
            f"All cubes, models, and configurations in this project will be permanently deleted!\n\n"
            f"This action cannot be undone!\n\n"
            f"Are you sure you want to delete the entire project?"
        )
        
        if result:
            success = self._delete_project_from_atscale(project_id, project_name)
            if success:
                # Refresh installer data to reflect the deletion
                self.installer_data_manager.refresh_installer_data()
            return success
        return False

    def _delete_project_from_atscale(self, project_id, project_name):
        """Delete project from AtScale using API"""
        try:
            jwt = get_jwt()
            host = self.config["host"]
            org = self.config["organization"]
            
            url = f"https://{host}:10500/api/1.0/org/{org}/project/{project_id}"
            headers = {
                "Authorization": f"Bearer {jwt}",
                "Content-Type": "application/json"
            }
            
            append_log(self.log_ref_container[0], f"Deleting project '{project_name}' (ID: {project_id})...")
            
            response = requests.delete(url, headers=headers, verify=False, timeout=30)
            
            if response.status_code == 200:
                append_log(self.log_ref_container[0], f"✓ Successfully deleted project: {project_name}")
                return True
            else:
                error_msg = f"Failed to delete project: {response.status_code} - {response.text}"
                append_log(self.log_ref_container[0], f"✗ {error_msg}")
                return False
                
        except Exception as e:
            error_msg = f"Error deleting project: {e}"
            append_log(self.log_ref_container[0], f"✗ {error_msg}")
            return False
# [file content end]