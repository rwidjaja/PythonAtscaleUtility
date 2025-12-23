# aggregate/common_selector.py
import tkinter as tk
from tkinter import ttk
import threading
from typing import List, Dict, Callable, Optional

from common import append_log
from .api_client import AtScaleAPIClient


class ProjectCubeSelector:
    """Selector for projects and cubes using REST API (like catalog_tab.py)"""
    
    def __init__(self, parent, log_ref_container, on_selection_change: Optional[Callable] = None):
        self.parent = parent
        self.log_widget = log_ref_container[0] if isinstance(log_ref_container, list) else log_ref_container
        self.on_selection_change = on_selection_change
        self.api_client = None
        self.available_combinations = []  # List of dicts with project/cube data
        self.current_project_id = ""
        self.current_cube_id = ""
        self.current_display = ""
        
        self.create_selector()
        self.load_initial_data()
    
    def create_selector(self):
        """Create the combobox selector"""
        self.selector_var = tk.StringVar()
        self.selector = ttk.Combobox(self.parent, textvariable=self.selector_var, 
                                     state="readonly", width=60)
        self.selector["values"] = ["Loading projects and cubes..."]
        self.selector.current(0)
        self.selector.bind("<<ComboboxSelected>>", self._on_select)
    
    def get_selector_widget(self):
        """Return the selector widget for placement in UI"""
        return self.selector
    
    def get_current_selection(self) -> Dict:
        """Return current selection as dict with all data"""
        for combo in self.available_combinations:
            if combo['display'] == self.current_display:
                return combo.copy()
        return {}
    
    def set_selection_change_callback(self, callback):
        """Set callback for when selection changes"""
        self.on_selection_change = callback
    
    def _on_select(self, event):
        """Handle selection changes"""
        choice = self.selector_var.get()
        if not choice or choice == "Loading projects and cubes..." or choice.startswith("Select"):
            return
        
        # Find the selected combination
        for combo in self.available_combinations:
            if combo['display'] == choice:
                self.current_display = choice
                self.current_project_id = combo['project_id']
                self.current_cube_id = combo['cube_id']
                
                self._safe_log(f"Selected: {combo['project_name']} -> {combo['cube_name']}")
                
                # Notify callback if provided
                if self.on_selection_change:
                    try:
                        self.on_selection_change(combo)
                    except Exception as e:
                        self._safe_log(f"Error in selection callback: {e}")
                return
    
    def load_initial_data(self):
        """Load initial project and cube data"""
        thread = threading.Thread(target=self._load_data_thread, daemon=True)
        thread.start()
    
    def _load_data_thread(self):
        """Thread function to load data"""
        try:
            self._safe_log("Loading published projects and cubes...")
            
            self.api_client = AtScaleAPIClient()
            projects = self.api_client.get_published_projects()
            
            if not projects:
                self._safe_update_selector(["No published projects found"])
                return
            
            results = []
            for project in projects:
                project_name = project.get("name", "Unknown Project")
                project_id = project.get("id", "")
                
                cubes_list = project.get("cubes", [])
                for cube in cubes_list:
                    cube_name = cube.get("name", "Unknown Cube")
                    cube_id = cube.get("id", "")
                    
                    display_text = f"{project_name} || {cube_name}"
                    results.append({
                        'display': display_text,
                        'project_name': project_name,
                        'project_id': project_id,
                        'cube_name': cube_name,
                        'cube_id': cube_id,
                        'full_data': {
                            'project': project,
                            'cube': cube
                        }
                    })
            
            self.available_combinations = results
            
            if results:
                display_values = ["Select Project || Cube"] + [r['display'] for r in results]
                self._safe_update_selector(display_values)
                self._safe_log(f"Loaded {len(results)} project-cube combinations")
            else:
                self._safe_update_selector(["No cubes found in published projects"])
                self._safe_log("No cubes found in published projects")
                
        except Exception as e:
            error_msg = f"Error loading projects/cubes: {e}"
            self._safe_log(error_msg)
            self._safe_update_selector([error_msg])
    
    def _safe_log(self, message):
        """Thread-safe logging"""
        try:
            if self.parent and self.parent.winfo_exists():
                self.parent.after(0, lambda: append_log(self.log_widget, message))
        except:
            pass
    
    def _safe_update_selector(self, values):
        """Thread-safe selector update"""
        try:
            if self.parent and self.parent.winfo_exists():
                self.parent.after(0, lambda: self._update_selector_values(values))
        except:
            pass
    
    def _update_selector_values(self, values):
        """Update selector values (called in main thread)"""
        self.selector["values"] = values
        if values and len(values) > 1:
            self.selector.current(0)
    
    def refresh_data(self):
        """Refresh the project-cube data"""
        self.selector["values"] = ["Refreshing..."]
        self.selector.current(0)
        self.load_initial_data()