# [file name]: support_zip_actions.py
import os
import shutil
from common import append_log

class SupportZipActions:
    def __init__(self, processor, wizard_controller, migration_controller, log_ref_container):
        self.processor = processor
        self.wizard_controller = wizard_controller
        self.migration_controller = migration_controller
        self.log_ref_container = log_ref_container
    
    def open_migration_wizard(self, selected_projects):
        """Open migration wizard for selected projects"""
        try:
            # Get the support_zip_* folder path
            support_zip_folder = selected_projects[0]['support_zip_folder']
            
            # Get project names
            project_names = [project['name'] for project in selected_projects]
            
            # Create a modified wizard that works with support zip projects
            self._open_wizard_for_support_zip(project_names, support_zip_folder, selected_projects)
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error opening wizard for support zip: {e}")
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", f"Failed to open wizard: {str(e)}")
    
    def _open_wizard_for_support_zip(self, project_names, support_zip_folder, projects_data):
        """Open a modified wizard for support zip projects"""
        # Get the wizard controller
        wizard_controller = self.wizard_controller
        
        # Clean up wizard workspace first
        wizard_controller.cleanup_wizard_workspace(project_names)
        
        # Copy projects from support_zip folder to workspace/sml for wizard analysis
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        workspace = self.processor.config.get("workspace", "working_dir")
        
        if not os.path.isabs(workspace):
            workspace = os.path.join(root_dir, workspace)
        
        sml_dir = os.path.join(workspace, "sml")
        
        for project_data in projects_data:
            project_name = project_data['name']
            source_dir = project_data['directory']
            
            # Use file_ops.sanitize_name instead of processor._sanitize_name
            sanitized_name = self.processor.file_ops.sanitize_name(project_name)
            target_dir = os.path.join(sml_dir, sanitized_name)
            
            # Remove existing directory if it exists
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            
            # Copy project to workspace for wizard
            shutil.copytree(source_dir, target_dir)
            
            append_log(self.log_ref_container[0], f"Copied project {project_name} to {target_dir} for wizard")
        
        # Now open the wizard with the project names
        wizard_controller.wizard_window = wizard_controller.wizard_ui.create_wizard_window(
            wizard_controller.parent
        )
        wizard_controller.wizard_ui.load_selected_projects(project_names)
        
        # Start analysis automatically (projects are already in SML format in workspace/sml)
        wizard_controller._analyze_sml_files(project_names)
    
    def migrate_to_git(self, selected_projects):
        """Migrate selected projects to Git"""
        success_count = 0
        for project in selected_projects:
            if self.processor.commit_project_to_git(project):
                success_count += 1
        
        return success_count