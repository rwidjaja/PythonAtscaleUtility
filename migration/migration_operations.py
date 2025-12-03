import os
import json
import requests
import threading
import time
import re
from common import append_log, get_jwt
from migration.java_service import JavaServiceManager
from migration.xml_to_sml import XmlToSmlConverter
from migration.sml_to_xml import SmlToXmlConverter
from migration.migration_toGit import MigrationToGit
from migration.migration_fromGit import MigrationFromGit
from api.git_operations import GitOperations as ApiGitOperations

class MigrationOperations:
    def __init__(self, config, log_ref_container):
        self.config = config
        self.log_ref_container = log_ref_container
        self.java_service = JavaServiceManager(config, log_ref_container)
        self.xml_to_sml = XmlToSmlConverter(config, log_ref_container)
        self.sml_to_xml = SmlToXmlConverter(config, log_ref_container)
        self.migration_to_git = MigrationToGit(config, log_ref_container)
        self.migration_from_git = MigrationFromGit(config, log_ref_container)
        self.api_git_ops = ApiGitOperations(config)
        self.current_project = None
        self.is_running = False

    def sanitize_repo_name(self, project_name):
        """Sanitize project name for use in Git repository names"""
        # Replace spaces and special characters with hyphens
        sanitized = re.sub(r'[^\w\s-]', '', project_name)  # Remove special characters
        sanitized = re.sub(r'[-\s]+', '-', sanitized)      # Replace spaces and multiple hyphens with single hyphen
        sanitized = sanitized.lower().strip('-')           # Convert to lowercase and trim hyphens
        return sanitized

    def ensure_java_service_running(self):
        """Ensure the Java ML service is running"""
        return self.java_service.ensure_java_service_running()

    def load_git_repositories(self):
        """Load Git repositories for reference only"""
        repositories, error = self.api_git_ops.get_repos_with_catalog()
        if error:
            append_log(self.log_ref_container[0], f"Git API error: {error}")
            return self.api_git_ops._get_fallback_repositories()
        return repositories

    def cleanup_workspace(self):
        """Clean up the entire workspace directory"""
        try:
            # Use root directory as base for workspace
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.config.get("workspace", "working_dir")
            
            # If workspace is relative, make it relative to root directory
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
            
            if os.path.exists(workspace):
                import shutil
                shutil.rmtree(workspace)
                append_log(self.log_ref_container[0], f"Cleaned up workspace: {workspace}")
            
            # Recreate the directory structure
            os.makedirs(os.path.join(workspace, "xml"), exist_ok=True)
            os.makedirs(os.path.join(workspace, "sml"), exist_ok=True)
            os.makedirs(os.path.join(workspace, "git_repos"), exist_ok=True)
            append_log(self.log_ref_container[0], "Recreated clean workspace directory structure")
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error cleaning workspace: {e}")

    def cleanup_project_artifacts(self, project_name):
        """Clean up artifacts for a specific project"""
        try:
            # Use root directory as base for workspace
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.config.get("workspace", "working_dir")
            
            # If workspace is relative, make it relative to root directory
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
            
            # Create sanitized version of project name
            sanitized_project_name = self.sanitize_repo_name(project_name)
            
            # Clean up project-specific directories (both original and sanitized names)
            project_paths = [
                os.path.join(workspace, "sml", project_name),
                os.path.join(workspace, "sml", sanitized_project_name),
                os.path.join(workspace, "git_repos", project_name),
                os.path.join(workspace, "git_repos", sanitized_project_name),
            ]
            
            # Clean up project-specific XML files
            import glob
            xml_files = glob.glob(os.path.join(workspace, "xml", f"*{project_name}*"))
            project_paths.extend(xml_files)
            
            # Also clean up files with sanitized name
            xml_files_sanitized = glob.glob(os.path.join(workspace, "xml", f"*{sanitized_project_name}*"))
            project_paths.extend(xml_files_sanitized)
            
            cleaned_count = 0
            for path in project_paths:
                if os.path.exists(path):
                    import shutil
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    cleaned_count += 1
            
            if cleaned_count > 0:
                append_log(self.log_ref_container[0], f"Cleaned up {cleaned_count} artifacts for project '{project_name}'")
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error cleaning project artifacts for {project_name}: {e}")
            
    def migrate_multiple_projects_to_git_async(self, project_ids, project_names, callback=None):
        """Start migration for multiple projects in sequence"""
        if self.is_running:
            append_log(self.log_ref_container[0], "Migration already in progress")
            return False
        
        self.is_running = True
        
        def run_sequential_migrations(index=0):
            if index >= len(project_names):
                self.is_running = False
                if callback:
                    callback(True, "All projects completed")
                return
            
            project_id = project_ids[index]
            project_name = project_names[index]
            self.current_project = project_name
            
            def single_project_callback(success, project_name):
                if not success:
                    append_log(self.log_ref_container[0], f"Failed to migrate project: {project_name}")
                # Continue with next project
                run_sequential_migrations(index + 1)
            
            self.migrate_project_to_git_async(project_id, project_name, single_project_callback)
        
        thread = threading.Thread(target=run_sequential_migrations)
        thread.daemon = True
        thread.start()
        return True

    def migrate_multiple_repos_to_installer_async(self, repo_names, project_names, callback=None):
        """Start reverse migration for multiple repositories in sequence"""
        if self.is_running:
            append_log(self.log_ref_container[0], "Migration already in progress")
            return False
        
        self.is_running = True
        
        def run_sequential_migrations(index=0):
            if index >= len(repo_names):
                self.is_running = False
                if callback:
                    callback(True, "All repositories completed")
                return
            
            repo_name = repo_names[index]
            project_name = project_names[index]
            self.current_project = project_name
            
            def single_repo_callback(success, project_name):
                if not success:
                    append_log(self.log_ref_container[0], f"Failed to migrate repository: {repo_name}")
                # Continue with next repository
                run_sequential_migrations(index + 1)
            
            self.migrate_git_to_installer_async(repo_name, project_name, single_repo_callback)
        
        thread = threading.Thread(target=run_sequential_migrations)
        thread.daemon = True
        thread.start()
        return True

    def migrate_project_to_git_async(self, project_id, project_name, callback=None):
        """Start migration in a separate thread"""
        if self.is_running:
            append_log(self.log_ref_container[0], f"Migration already in progress for '{self.current_project}', skipping '{project_name}'")
            return False
        
        self.is_running = True
        self.current_project = project_name
        
        def run_migration():
            try:
                success = self._migrate_project_to_git(project_id, project_name)
                if callback:
                    callback(success, project_name)
            except Exception as e:
                append_log(self.log_ref_container[0], f"Migration thread error for '{project_name}': {e}")
                if callback:
                    callback(False, project_name)
            finally:
                # Don't reset is_running here - let the controller handle it for sequential migrations
                self.current_project = None
                # Note: is_running is reset by the controller after callback
        
        thread = threading.Thread(target=run_migration)
        thread.daemon = True
        thread.start()
        return True


    def _migrate_project_to_git(self, project_id, project_name):
        """Migrate a project to Git repository using project name as repo name"""
        try:
            # Clean up any existing artifacts for this project first
            self.cleanup_project_artifacts(project_name)
            
            # Ensure Java service is running
            append_log(self.log_ref_container[0], f"Starting migration for project '{project_name}'")
            append_log(self.log_ref_container[0], "Ensuring Java service is running...")
            
            if not self.ensure_java_service_running():
                append_log(self.log_ref_container[0], "Cannot proceed without Java ML service")
                return False

            append_log(self.log_ref_container[0], f"✓ Java service ready")
            append_log(self.log_ref_container[0], f"Processing project '{project_name}' to Git repo")
            
            # Step 1: Export XML from AtScale
            append_log(self.log_ref_container[0], f"Exporting XML for project '{project_name}'...")
            xml_content = self._export_xml(project_id)
            if not xml_content:
                append_log(self.log_ref_container[0], f"✗ Failed to export XML for project {project_name}")
                return False
            append_log(self.log_ref_container[0], f"✓ Project export '{project_name}' successful")
            
            # Step 2: Save XML to workspace
            xml_filename = f"{project_id}.xml"
            formatted_xml_filename = f"{project_id}_formatted.xml"
            xml_path = self.xml_to_sml.save_xml(xml_content, xml_filename)
            
            # Step 3: Convert XML to SML using Java service
            append_log(self.log_ref_container[0], f"Converting project '{project_name}' from XML to SML...")
            sml_success = self.xml_to_sml.convert_xml_to_sml(xml_filename, formatted_xml_filename, project_name)
            if not sml_success:
                append_log(self.log_ref_container[0], f"✗ Failed to convert XML to SML for {project_name}")
                return False
            append_log(self.log_ref_container[0], f"✓ XML to SML conversion successful for '{project_name}'")
            
            # Step 4: Sanitize repository name and check if it exists
            sanitized_repo_name = self.sanitize_repo_name(project_name)
            repo_name = f"{self.config.get('git_id')}/{sanitized_repo_name}"
            
            append_log(self.log_ref_container[0], f"Original project name: '{project_name}'")
            append_log(self.log_ref_container[0], f"Sanitized repository name: '{sanitized_repo_name}'")
            append_log(self.log_ref_container[0], f"Checking if Git repository '{repo_name}' exists...")
            
            repo_exists, error = self.api_git_ops.repository_exists(repo_name)
            if error:
                append_log(self.log_ref_container[0], f"✗ Error checking repository {repo_name}: {error}")
                return False
                
            if repo_exists:
                append_log(self.log_ref_container[0], f"✗ Repository '{repo_name}' already exists!")
                append_log(self.log_ref_container[0], "Please either:")
                append_log(self.log_ref_container[0], "  - Rename the existing repository")
                append_log(self.log_ref_container[0], "  - Delete the existing repository using the 'Delete Git Repo' button")
                append_log(self.log_ref_container[0], "  - Choose a different project name")
                return False
            
            append_log(self.log_ref_container[0], f"✓ Repository name '{repo_name}' is available")
            
            # Step 5: Use sanitized repository name and commit SML using proper Git workflow
            append_log(self.log_ref_container[0], f"Creating and pushing to new repository '{repo_name}'...")
            git_success = self.migration_to_git.commit_sml_to_git_new_repo(project_name, repo_name)
            if git_success:
                append_log(self.log_ref_container[0], f"✓ Successfully migrated '{project_name}' to Git repo '{repo_name}'")
                return True
            else:
                append_log(self.log_ref_container[0], f"✗ Failed to commit SML to Git for {project_name}")
                return False
                
        except Exception as e:
            append_log(self.log_ref_container[0], f"✗ Error migrating project to Git: {e}")
            return False

    def migrate_git_to_installer_async(self, repo_name, project_name, callback=None):
        """Start reverse migration in a separate thread"""
        if self.is_running:
            append_log(self.log_ref_container[0], f"Migration already in progress for '{self.current_project}', skipping '{project_name}'")
            return False
        
        self.is_running = True
        self.current_project = project_name
        
        def run_migration():
            try:
                success = self._migrate_git_to_installer(repo_name, project_name)
                if callback:
                    callback(success, project_name)
            except Exception as e:
                append_log(self.log_ref_container[0], f"Migration thread error for '{project_name}': {e}")
                # Don't call callback with error here - let the controller handle it
                # The controller will continue with next item even if this fails
            finally:
                # Don't reset is_running here - let the controller handle it for sequential migrations
                self.current_project = None
        
        thread = threading.Thread(target=run_migration)
        thread.daemon = True
        thread.start()
        return True

    def _migrate_git_to_installer(self, repo_name, project_name):
        """Migrate from Git repository to Installer"""
        try:
            # Clean up any existing artifacts for this project first
            self.cleanup_project_artifacts(project_name)
            
            # Ensure Java service is running
            if not self.ensure_java_service_running():
                append_log(self.log_ref_container[0], "Cannot proceed without Java ML service")
                return False

            append_log(self.log_ref_container[0], f"Processing Git repo '{repo_name}' to project '{project_name}'")
            
            # Step 1: Clone/pull Git repository
            repo_success = self.migration_from_git.clone_git_repository(repo_name, project_name)
            if not repo_success:
                append_log(self.log_ref_container[0], f"Failed to clone Git repository {repo_name}")
                return False
            
            # Step 2: Convert SML to XML using Java service (reverse conversion)
            xml_success = self.sml_to_xml.convert_sml_to_xml(project_name, f"{project_name}.xml")
            if not xml_success:
                append_log(self.log_ref_container[0], f"Failed to convert SML to XML for {project_name}")
                return False
            
            # Step 3: Import XML to AtScale
            import_success = self.sml_to_xml.import_xml_to_atscale(project_name)
            if import_success:
                append_log(self.log_ref_container[0], f"Successfully migrated '{repo_name}' to AtScale project '{project_name}'")
                return True
            else:
                append_log(self.log_ref_container[0], f"Failed to import XML to AtScale for {project_name}")
                return False
                
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error migrating Git to Installer: {e}")
            return False

    def delete_git_repository(self, repo_name):
        """Delete a Git repository"""
        try:
            append_log(self.log_ref_container[0], f"Attempting to delete repository: {repo_name}")
            
            # Remove visibility tag for API call
            clean_repo_name = repo_name.split(" [")[0]
            
            success, error = self.api_git_ops.delete_repository(clean_repo_name)
            if success:
                append_log(self.log_ref_container[0], f"✓ Successfully deleted repository: {repo_name}")
                return True
            else:
                append_log(self.log_ref_container[0], f"✗ Failed to delete repository {repo_name}: {error}")
                return False
                
        except Exception as e:
            append_log(self.log_ref_container[0], f"✗ Error deleting repository: {e}")
            return False

    def _export_xml(self, project_id):
        """Export project XML from AtScale"""
        try:
            jwt = get_jwt()
            host = self.config["host"]
            org = self.config["organization"]
            
            url = f"https://{host}:10500/org/{org}/project/{project_id}/xml/download"
            headers = {
                "Authorization": f"Bearer {jwt}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, verify=False, timeout=30)
            response.raise_for_status()
            
            return response.text
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error exporting XML for project {project_id}: {e}")
            return None