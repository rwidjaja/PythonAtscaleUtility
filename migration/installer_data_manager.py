# [file name]: installer_data_manager.py
# [file content begin]
import tkinter as tk
import requests
from common import append_log, get_jwt
from api.folders import get_folders

class InstallerDataManager:
    def __init__(self, config, log_ref_container, left_listbox):
        self.config = config
        self.log_ref_container = log_ref_container
        self.left_listbox = left_listbox
        self.flat_installer_list = []  # Store the display structure
        self._selected_project_ids = set()  # Track selected projects by ID for sticky behavior

    def load_installer_data(self):
        """Load all projects from Installer and display as flat sorted list"""
        try:
            jwt = get_jwt()
            host = self.config["host"]
            org = self.config["organization"]
            
            folders_json = get_folders(host, org, jwt)
            append_log(self.log_ref_container[0], "Loaded installer folder structure")
            
            self._build_installer_listbox(folders_json)
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error loading installer data: {e}")

    def _build_installer_listbox(self, folders_json):
        """Build listbox from folders JSON - show only projects in flat sorted list"""
        # Save current selection before clearing (if we have existing data)
        if self.flat_installer_list:
            self.save_selection_state()
        
        self.left_listbox.delete(0, tk.END)
        self.flat_installer_list = []
        
        root_obj = folders_json.get("response", {})
        
        # Collect all projects
        all_projects = []
        
        def collect_projects_from_folder(folder_obj):
            """Collect all projects from a folder and its subfolders"""
            # Add projects from this folder
            for item in folder_obj.get("items", []) or []:
                if item.get("type") == "Project":
                    all_projects.append(item)
            
            # Process child folders recursively
            for cf in folder_obj.get("child_folders", []) or []:
                collect_projects_from_folder(cf)

        # Collect from top-level folders
        for folder in root_obj.get("child_folders", []) or []:
            collect_projects_from_folder(folder)
            
        # Collect root-level projects
        for item in root_obj.get("items", []) or []:
            if item.get("type") == "Project":
                all_projects.append(item)

        # Sort projects by name
        all_projects.sort(key=lambda x: (x.get("caption") or x.get("name") or "").lower())
        
        # Add projects to listbox
        for project_item in all_projects:
            self._add_project_to_list(project_item)

        # Restore selection after refresh
        self._restore_selection()

    def _add_project_to_list(self, project_item):
        """Add a project to the listbox"""
        project_name = project_item.get("caption") or project_item.get("name") or "Unnamed Project"
        project_id = project_item.get("id")
        
        index = self.left_listbox.size()
        self.left_listbox.insert(tk.END, project_name)
        
        # Store project data
        project_data = {
            "type": "project", 
            "data": project_item,
            "project_data": project_item,
            "project_name": project_name,
            "project_id": project_id
        }
        self.flat_installer_list.append(project_data)

    def get_item_data_by_index(self, index):
        """Get item data by listbox index"""
        if 0 <= index < len(self.flat_installer_list):
            return self.flat_installer_list[index]
        return None

    def refresh_installer_data(self):
        """Refresh installer data and update the listbox"""
        append_log(self.log_ref_container[0], "Refreshing installer source data...")
        self.load_installer_data()
        append_log(self.log_ref_container[0], "✓ Installer source refreshed")

    def save_selection_state(self):
        """Save current selection state by project IDs"""
        selected_indices = self.left_listbox.curselection()
        self._selected_project_ids.clear()
        
        for index in selected_indices:
            item_data = self.get_item_data_by_index(index)
            if item_data and item_data.get("type") == "project":
                project_id = item_data.get("project_id")
                if project_id:
                    self._selected_project_ids.add(project_id)

    def _restore_selection(self):
        """Restore selection after refresh using project IDs"""
        if not self._selected_project_ids:
            return
            
        # Clear any existing selection first
        self.left_listbox.selection_clear(0, tk.END)
        
        # Restore by project IDs
        for index, item_data in enumerate(self.flat_installer_list):
            if (item_data.get("type") == "project" and 
                item_data.get("project_id") in self._selected_project_ids):
                self.left_listbox.selection_set(index)

    def get_selected_projects(self):
        """Get list of selected project data"""
        selected_indices = self.left_listbox.curselection()
        selected_projects = []
        
        for index in selected_indices:
            item_data = self.get_item_data_by_index(index)
            if item_data and item_data.get("type") == "project":
                selected_projects.append(item_data)
                
        return selected_projects

    def get_selected_project_count(self):
        """Get count of selected projects"""
        return len([i for i in self.left_listbox.curselection() 
                   if self.get_item_data_by_index(i) and 
                   self.get_item_data_by_index(i).get("type") == "project"])

    def get_all_selected_indices(self):
        """Get all selected indices (for migration)"""
        return self.left_listbox.curselection()
# [file content end]