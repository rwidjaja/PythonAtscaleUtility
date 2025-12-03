# [file name]: wizard_controller.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
from common import append_log
from migration.wizard_ui import WizardUI
from migration.wizard_operations import WizardOperations
from migration.sml_analyzer import SmlAnalyzer
from migration.wizard_common_builder import WizardCommonBuilder
from migration.wizard_git_operations import WizardGitOperations
from migration.wizard_file_operations import WizardFileOperations
from migration.wizard_analysis_handler import WizardAnalysisHandler

class WizardController:
    def __init__(self, parent, migration_controller, log_ref_container):
        self.parent = parent
        self.migration_controller = migration_controller
        self.log_ref_container = log_ref_container
        self.wizard_window = None
        
        # Initialize components
        self.wizard_ui = WizardUI(self, log_ref_container)
        self.wizard_ops = WizardOperations(migration_controller.config, log_ref_container)
        self.sml_analyzer = SmlAnalyzer(migration_controller.config, log_ref_container)
        
        # Initialize specialized handlers
        self.file_ops = WizardFileOperations(migration_controller, log_ref_container)
        self.git_ops = WizardGitOperations(migration_controller, log_ref_container)
        self.common_builder = WizardCommonBuilder(migration_controller, log_ref_container)
        self.analysis_handler = WizardAnalysisHandler(migration_controller, log_ref_container)
        
        # Connect handlers
        self.common_builder.file_ops = self.file_ops
        self.common_builder.git_ops = self.git_ops
        self.analysis_handler.wizard_ops = self.wizard_ops
        self.analysis_handler.sml_analyzer = self.sml_analyzer
        self.analysis_handler.wizard_ui = self.wizard_ui
    
    def open_wizard(self):
        """Open the migration wizard dialog and start analysis immediately"""
        if not self._has_multiple_selected_projects():
            messagebox.showinfo("Migration Wizard", "Please select multiple projects to use the Migration Wizard.")
            return
        
        # Get selected projects first
        project_names = self._get_selected_projects()
        
        # Clean up workspace before starting wizard
        append_log(self.log_ref_container[0], "Cleaning wizard workspace...")
        self.cleanup_wizard_workspace(project_names)
        
        self.wizard_window = self.wizard_ui.create_wizard_window(self.parent)
        self.wizard_ui.load_selected_projects(project_names)
        
        # Set cleanup on window close
        def cleanup_and_close():
            self.migration_controller.cleanup_workspace()
            self.wizard_window.destroy()
        
        self.wizard_window.protocol("WM_DELETE_WINDOW", cleanup_and_close)
        
        # Start analysis automatically
        self._start_analysis_automatically()
    
    def cleanup_wizard_workspace(self, project_names):
        """Clean up workspace specifically for wizard operations"""
        return self.file_ops.cleanup_wizard_workspace(project_names)
    
    def create_common_dimensions(self):
        """Create common dimensions from selected items"""
        try:
            # Get selected dimensions and name
            selected_dimensions = self.wizard_ui.get_selected_dimensions()
            common_name = self.wizard_ui.get_common_name()
            
            if not selected_dimensions:
                messagebox.showinfo("No Selection", "Please select at least one dimension to create common dimensions.")
                return
                
            if not common_name:
                messagebox.showinfo("No Name", "Please enter a name for the common dimensions.")
                return
            
            # Sanitize the name
            sanitized_name = self.common_builder.sanitize_name(common_name)
            
            # Disable create button during processing
            self.wizard_ui.set_create_button_state("disabled")
            self.wizard_ui.update_creation_info(f"Creating common dimensions: {sanitized_name}...")
            
            # Build the common dimensions structure
            success = self.common_builder.build_common_dimensions_structure(sanitized_name, selected_dimensions)
            
            if success:
                messagebox.showinfo("Success", 
                                  f"Common dimensions '{sanitized_name}' created and committed to Git successfully!")
                self.wizard_ui.update_creation_info(f"Successfully created and committed: {sanitized_name}")
            else:
                messagebox.showerror("Error", "Failed to create common dimensions")
                self.wizard_ui.update_creation_info("Creation failed", is_error=True)
                
            # Re-enable button
            self.wizard_ui.set_create_button_state("normal")
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error creating common dimensions: {e}")
            messagebox.showerror("Error", f"Failed to create common dimensions: {str(e)}")
            self.wizard_ui.update_creation_info(f"Error: {str(e)}", is_error=True)
            self.wizard_ui.set_create_button_state("normal")
    
    def _has_multiple_selected_projects(self):
        """Check if multiple projects are selected"""
        return self.migration_controller.get_selected_project_count() > 1
    
    def _get_selected_projects(self):
        """Get list of selected project names"""
        return self.analysis_handler._get_selected_projects()
    
    def _start_analysis_automatically(self):
        """Start the wizard analysis process automatically"""
        return self.analysis_handler.start_analysis_automatically(self.wizard_window)
    
    def close_wizard(self):
        """Close the wizard window"""
        if self.wizard_window:
            self.wizard_window.destroy()
            self.wizard_window = None
            
    def _analyze_sml_files(self, project_names):
        """Analyze SML files for projects (used by support zip wizard)"""
        self.analysis_handler._analyze_sml_files(project_names)