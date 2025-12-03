# [file name]: support_zip_processor.py
import os
from tkinter import filedialog, messagebox
from common import append_log
from migration.support_zip_file_ops import SupportZipFileOps
from migration.support_zip_git_ops import SupportZipGitOps

class SupportZipProcessor:
    def __init__(self, config, log_ref_container, migration_ops):
        self.config = config
        self.log_ref_container = log_ref_container
        self.migration_ops = migration_ops
        self.file_ops = SupportZipFileOps(config, log_ref_container, migration_ops)
        self.git_ops = SupportZipGitOps(config, log_ref_container, migration_ops)
        
    def open_support_zip(self):
        """Open file dialog to select support zip file"""
        zip_path = filedialog.askopenfilename(
            title="Select Support Zip File",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        
        if not zip_path:
            append_log(self.log_ref_container[0], "No support zip file selected")
            return None
            
        append_log(self.log_ref_container[0], f"Selected support zip: {zip_path}")
        return zip_path
        
    def cleanup_support_zip_folders(self):
        """Clean up previous support_zip_* folders"""
        return self.file_ops.cleanup_support_zip_folders()
    
    def process_support_zip(self, zip_path):
        """Process the support zip file by passing it directly to Java service"""
        return self.file_ops.process_support_zip(zip_path)
    
    def _find_projects_in_support_zip(self):
        """Find all projects in the latest support_zip_* folder"""
        return self.file_ops._find_projects_in_support_zip()
    
    def commit_project_to_git(self, project_info):
        """Commit a project from support zip to Git"""
        return self.git_ops.commit_project_to_git(project_info)
    
    def get_latest_support_zip_folder(self):
        """Get the latest support_zip_* folder"""
        return self.file_ops.get_latest_support_zip_folder()
    
    def _sanitize_name(self, name):
        """Sanitize the name for folder and file naming"""
        return self.file_ops.sanitize_name(name)