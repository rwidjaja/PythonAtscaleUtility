# [file name]: wizard_common_builder.py
import os
import re
import shutil
from tkinter import messagebox
from common import append_log

class WizardCommonBuilder:
    def __init__(self, migration_controller, log_ref_container):
        self.migration_controller = migration_controller
        self.log_ref_container = log_ref_container
        self.file_ops = None  # Will be set by WizardController
        self.git_ops = None   # Will be set by WizardController
    
    def build_common_dimensions_structure(self, common_name, selected_dimensions):
        """Build the complete common dimensions structure"""
        try:
            # Get workspace directory
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.migration_controller.config.get("workspace", "working_dir")
            
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
            
            # Create base directory in SML folder first (temporary)
            temp_common_dir = os.path.join(workspace, "sml", "common_dimensions", common_name)
            os.makedirs(temp_common_dir, exist_ok=True)
            
            append_log(self.log_ref_container[0], 
                      f"Creating common dimensions: {common_name} at {temp_common_dir}")
            
            # Create catalog.yml
            self.file_ops.create_catalog_file(temp_common_dir, common_name)
            
            # Create connections directory and file
            connection_id = self.file_ops.create_connection_file(temp_common_dir, common_name, selected_dimensions)
            
            # Create datasets directory and copy datasets
            self.file_ops.copy_datasets(temp_common_dir, selected_dimensions, connection_id)
            
            # Create dimensions directory and copy dimensions
            self.file_ops.copy_dimensions(temp_common_dir, selected_dimensions)
            
            # Create README or info file
            self.file_ops.create_info_file(temp_common_dir, common_name, selected_dimensions)
            
            append_log(self.log_ref_container[0], f"✓ Common dimensions structure created: {common_name}")
            
            # Move the structure to proper location for Git commit
            final_sml_dir = os.path.join(workspace, "sml", common_name)
            
            # If final directory exists, remove it
            if os.path.exists(final_sml_dir):
                shutil.rmtree(final_sml_dir)
            
            # Move the entire temp directory to final location
            shutil.move(temp_common_dir, final_sml_dir)
            
            # Commit to Git using migration_ops
            git_success = self.git_ops.commit_common_to_git(common_name, final_sml_dir)
            
            # Clean up temporary directory after Git commit
            try:
                if os.path.exists(final_sml_dir):
                    shutil.rmtree(final_sml_dir)
                    append_log(self.log_ref_container[0], f"Cleaned up directory: {final_sml_dir}")
            except Exception as e:
                append_log(self.log_ref_container[0], f"Note: Could not clean up directory: {e}")
            
            return git_success
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error building common dimensions: {e}")
            return False
    
    def sanitize_name(self, name):
        """Sanitize the name for folder and file naming"""
        sanitized = re.sub(r'[^\w\s-]', '', name)
        sanitized = re.sub(r'[-\s]+', '-', sanitized)
        return sanitized.strip('-')