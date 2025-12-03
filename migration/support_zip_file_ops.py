# [file name]: support_zip_file_ops.py
import os
import glob
import yaml
import re  # ADD THIS IMPORT
import shutil
import time
import requests
from common import append_log

class SupportZipFileOps:
    def __init__(self, config, log_ref_container, migration_ops):
        self.config = config
        self.log_ref_container = log_ref_container
        self.migration_ops = migration_ops
        
    def cleanup_support_zip_folders(self):
        """Clean up previous support_zip_* folders"""
        try:
            # Get workspace directory
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.config.get("workspace", "working_dir")
            
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
            
            sml_dir = os.path.join(workspace, "sml")
            
            # Find all support_zip_* folders
            support_zip_folders = glob.glob(os.path.join(sml_dir, "support_zip_*"))
            
            for folder in support_zip_folders:
                if os.path.isdir(folder):
                    shutil.rmtree(folder)
                    append_log(self.log_ref_container[0], f"Cleaned up previous support zip folder: {folder}")
                    
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error cleaning up support zip folders: {e}")
    
    def process_support_zip(self, zip_path):
        """Process the support zip file by passing it directly to Java service"""
        try:
            # First, ensure Java service is running
            if not self.migration_ops.ensure_java_service_running():
                append_log(self.log_ref_container[0], "Cannot proceed without Java ML service")
                return None
            
            # Clean up previous support zip folders
            self.cleanup_support_zip_folders()
            
            # Get workspace directory
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.config.get("workspace", "working_dir")
            
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
            
            # Create output directory with timestamp
            timestamp = int(time.time())
            output_dir = os.path.join(workspace, "sml", f"support_zip_{timestamp}")
            
            append_log(self.log_ref_container[0], f"Processing support zip, output to: {output_dir}")
            
            # Pass the zip file directly to the Java service
            payload = {
                "atscale-server": {
                    "apihost": self.config["host"],
                    "dchost": self.config["host"],
                    "authhost": self.config["host"],
                    "authport": 10500,
                    "dcport": 10500,
                    "apiport": 10502,
                    "username": self.config["username"],
                    "password": self.config["password"],
                    "disablessl": True,
                    "organizationfilterguid": self.config["organization"],
                    "organizationfiltername": self.config["organization"]
                },
                "inbound-resource": {
                    "location_type": "file",
                    "location": zip_path,
                    "source_type": "atscale"
                },
                "outbound-resource": {
                    "location_type": "directory",
                    "location": output_dir,
                    "source_type": "sml"
                }
            }
            
            append_log(self.log_ref_container[0], "Sending zip file to Java service for processing...")
            
            response = requests.post(
                "http://localhost:8000/atscale-sml-service/convert",
                json=payload,
                auth=('admin', '@scale800'),
                timeout=300
            )
            
            if response.status_code == 200:
                # Wait a moment for files to be written
                time.sleep(2)
                
                # Find the latest support_zip_* folder (should be our output_dir)
                projects = self._find_projects_in_support_zip()
                
                if not projects:
                    append_log(self.log_ref_container[0], "No projects found in support zip output")
                    return None
                
                append_log(self.log_ref_container[0], f"Found {len(projects)} project(s) in support zip")
                return projects
            else:
                append_log(self.log_ref_container[0], f"Java service failed to process zip: {response.status_code} - {response.text}")
                return None
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error processing support zip: {e}")
            return None
    
    def _find_projects_in_support_zip(self):
        """Find all projects in the latest support_zip_* folder"""
        projects = []
        
        try:
            # Get workspace directory
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.config.get("workspace", "working_dir")
            
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
            
            sml_dir = os.path.join(workspace, "sml")
            
            # Find all support_zip_* folders
            support_zip_folders = glob.glob(os.path.join(sml_dir, "support_zip_*"))
            
            if not support_zip_folders:
                append_log(self.log_ref_container[0], "No support_zip_* folders found")
                return []
            
            # Get the latest folder (by creation time)
            latest_folder = max(support_zip_folders, key=os.path.getctime)
            append_log(self.log_ref_container[0], f"Scanning projects in: {latest_folder}")
            
            # Look for project directories inside the support_zip folder
            for item in os.listdir(latest_folder):
                project_path = os.path.join(latest_folder, item)
                
                if os.path.isdir(project_path):
                    # Check if this directory has catalog.yml
                    catalog_path = os.path.join(project_path, 'catalog.yml')
                    
                    if os.path.exists(catalog_path):
                        try:
                            # Read catalog.yml to get project name
                            with open(catalog_path, 'r', encoding='utf-8') as f:
                                catalog_data = yaml.safe_load(f) or {}
                            
                            project_name = catalog_data.get('label', item)
                            
                            # Get project structure
                            project_structure = self._get_project_structure(project_path)
                            
                            projects.append({
                                'name': project_name,
                                'directory': project_path,
                                'catalog_path': catalog_path,
                                'structure': project_structure,
                                'catalog_data': catalog_data,
                                'support_zip_folder': latest_folder
                            })
                            
                            append_log(self.log_ref_container[0], f"Found project: {project_name}")
                            
                        except Exception as e:
                            append_log(self.log_ref_container[0], f"Error reading catalog.yml at {catalog_path}: {e}")
        
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error finding projects in support zip: {e}")
        
        return projects
    
    def _get_project_structure(self, project_dir):
        """Get the structure of a project directory"""
        structure = {
            'datasets': False,
            'dimensions': False,
            'metrics': False,
            'connections': False,
            'files': []
        }
        
        # Check for common directories
        for subdir in ['datasets', 'dimensions', 'metrics', 'connections']:
            subdir_path = os.path.join(project_dir, subdir)
            if os.path.exists(subdir_path) and os.listdir(subdir_path):
                structure[subdir] = True
        
        # Count files in each directory
        for root, dirs, files in os.walk(project_dir):
            relative_path = os.path.relpath(root, project_dir)
            if relative_path == '.':
                relative_path = ''
            
            for file in files:
                if file.endswith('.yml'):
                    structure['files'].append(os.path.join(relative_path, file))
        
        return structure
    
    def get_latest_support_zip_folder(self):
        """Get the latest support_zip_* folder"""
        try:
            # Get workspace directory
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.config.get("workspace", "working_dir")
            
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
            
            sml_dir = os.path.join(workspace, "sml")
            
            # Find all support_zip_* folders
            support_zip_folders = glob.glob(os.path.join(sml_dir, "support_zip_*"))
            
            if not support_zip_folders:
                return None
            
            # Get the latest folder
            latest_folder = max(support_zip_folders, key=os.path.getctime)
            return latest_folder
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error getting latest support zip folder: {e}")
            return None
    
    def sanitize_name(self, name):
        """Sanitize the name for folder and file naming"""
        sanitized = re.sub(r'[^\w\s-]', '', name)
        sanitized = re.sub(r'[-\s]+', '-', sanitized)
        sanitized = sanitized.lower().strip('-')
        return sanitized