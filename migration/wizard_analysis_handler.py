# [file name]: wizard_analysis_handler.py
import os
from tkinter import messagebox
from common import append_log

class WizardAnalysisHandler:
    def __init__(self, migration_controller, log_ref_container):
        self.migration_controller = migration_controller
        self.log_ref_container = log_ref_container
        self.wizard_ops = None  # Will be set by WizardController
        self.sml_analyzer = None  # Will be set by WizardController
        self.wizard_ui = None  # Will be set by WizardController
    
    def start_analysis_automatically(self, wizard_window):
        """Start the wizard analysis process automatically"""
        project_names = self._get_selected_projects()
        
        if self.migration_controller.migration_ops.is_running:
            messagebox.showwarning("Operation Running", 
                                 "A migration is already in progress. Please wait for it to complete.")
            return False
            
        # Find project IDs from installer data
        projects_to_analyze = []
        for project_name in project_names:
            project_id = self._find_project_id_by_name(project_name)
            if project_id:
                projects_to_analyze.append((project_id, project_name))
        
        if not projects_to_analyze:
            messagebox.showerror("Error", "Could not find project IDs for selected projects.")
            return False
            
        append_log(self.log_ref_container[0], f"Starting wizard analysis for {len(projects_to_analyze)} projects")
        
        # Disable UI controls during analysis
        self.wizard_ui.disable_controls()
        
        # Start the analysis with default options
        self._analyze_projects_sequence(projects_to_analyze, 0, True, 2, wizard_window)
        return True
    
    def _get_selected_projects(self):
        """Get list of selected project names"""
        selected_projects = self.migration_controller.installer_data_manager.get_selected_projects()
        return [project.get("project_name") for project in selected_projects]
    
    def _find_project_id_by_name(self, project_name):
        """Find project ID by project name in the installer data"""
        for item_data in self.migration_controller.installer_data_manager.flat_installer_list:
            if item_data.get("type") == "project":
                current_name = item_data.get("project_name")
                if current_name == project_name:
                    return item_data.get("project_data", {}).get("id")
        return None
    
    def _analyze_projects_sequence(self, projects, current_index, stop_on_error, delay_seconds, wizard_window):
        """Analyze projects in sequence - convert to SML and then analyze files"""
        if current_index >= len(projects):
            append_log(self.log_ref_container[0], "✓ All projects conversion completed")
            # Now analyze the SML files
            self._analyze_sml_files([p[1] for p in projects])
            return
            
        project_id, project_name = projects[current_index]
        
        append_log(self.log_ref_container[0], f"Analyzing project {current_index + 1}/{len(projects)}: {project_name}")
        self.wizard_ui.update_progress(f"Converting {project_name} to SML...")
        
        def conversion_callback(success, project_name):
            if success:
                append_log(self.log_ref_container[0], f"✓ Successfully converted '{project_name}' to SML")
            else:
                append_log(self.log_ref_container[0], f"✗ Failed to convert '{project_name}' to SML")
                if stop_on_error:
                    append_log(self.log_ref_container[0], "✗ Stopping due to failure (Stop on Error enabled)")
                    self.wizard_ui.enable_controls()
                    return
                    
            # Continue with next project after delay
            if delay_seconds > 0:
                wizard_window.after(delay_seconds * 1000, 
                                  lambda: self._analyze_projects_sequence(projects, current_index + 1, stop_on_error, delay_seconds, wizard_window))
            else:
                self._analyze_projects_sequence(projects, current_index + 1, stop_on_error, delay_seconds, wizard_window)
        
        # Convert project to SML (without Git commit)
        self.wizard_ops.convert_project_to_sml_only(
            self.migration_controller.migration_ops,
            project_id, 
            project_name, 
            conversion_callback
        )
    
    def _analyze_sml_files(self, project_names):
        """Analyze the converted SML files to find common dimensions"""
        self.wizard_ui.update_progress("Analyzing SML files...")
        append_log(self.log_ref_container[0], "Starting SML files analysis")
        
        try:
            # Get workspace directory
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.migration_controller.config.get("workspace", "working_dir")
            
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
                
            # Analyze SML files
            analysis_results = self.sml_analyzer.analyze_projects(project_names, workspace)
            
            # Display results
            self.wizard_ui.display_results(analysis_results)
            append_log(self.log_ref_container[0], f"✓ Analysis complete. Found {len(analysis_results.get('common_dimensions', []))} common dimension(s)")
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error analyzing SML files: {e}")
            self.wizard_ui.enable_controls()