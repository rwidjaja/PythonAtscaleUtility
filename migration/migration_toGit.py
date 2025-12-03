import os
import requests
import subprocess
from common import append_log
from api.git_operations import GitOperations as ApiGitOperations

class MigrationToGit:
    def __init__(self, config, log_ref_container):
        self.config = config
        self.log_ref_container = log_ref_container
        self.api_git_ops = ApiGitOperations(config)

    def commit_sml_to_git_new_repo(self, project_name, repo_name):
        """Commit SML files to a NEW Git repository using proper Git workflow"""
        try:
            # Use root directory as base for workspace
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.config.get("workspace", "working_dir")
            
            # If workspace is relative, make it relative to root directory
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
                
            sml_dir = os.path.join(workspace, "sml")
       
            # Try different possible directory names
            possible_dirs = [
                os.path.join(sml_dir, project_name),
                os.path.join(sml_dir, "common_dimensions", project_name)
            ]
            
            project_sml_dir = None
            for dir_path in possible_dirs:
                if os.path.exists(dir_path):
                    project_sml_dir = dir_path
                    break
            
            if not project_sml_dir:
                append_log(self.log_ref_container[0], f"No SML directory found for {project_name} in {possible_dirs}")
                return False
            
            # Sanitize the project name to match the directory naming convention
            # This should match the sanitization done in migration_operations.py
            import re
            sanitized_project_name = re.sub(r'[^\w\s-]', '', project_name)  # Remove special characters
            sanitized_project_name = re.sub(r'[-\s]+', '-', sanitized_project_name)  # Replace spaces with hyphens
            sanitized_project_name = sanitized_project_name.lower().strip('-')  # Convert to lowercase and trim hyphens
            
            project_sml_dir = os.path.join(sml_dir, sanitized_project_name)
            
            if not os.path.exists(project_sml_dir):
                append_log(self.log_ref_container[0], f"No SML directory found for {sanitized_project_name} at {project_sml_dir}")
                # Fallback: try the original project name
                project_sml_dir = os.path.join(sml_dir, project_name)
                if not os.path.exists(project_sml_dir):
                    append_log(self.log_ref_container[0], f"No SML directory found for {project_name} at {project_sml_dir}")
                    return False
                else:
                    append_log(self.log_ref_container[0], f"Using original project name directory: {project_sml_dir}")
            
            # Create the repository via GitHub API first
            append_log(self.log_ref_container[0], f"Creating new repository '{repo_name}' via GitHub API...")
            
            # Extract just the repository name (without username) for creation
            repo_name_only = repo_name.split("/")[-1] if "/" in repo_name else repo_name
            success, error = self.api_git_ops.create_repository(repo_name_only)
            if not success:
                append_log(self.log_ref_container[0], f"Failed to create repository {repo_name}: {error}")
                return False
            
            append_log(self.log_ref_container[0], f"✓ Repository '{repo_name}' created successfully")
            
            # Now use Git commands to initialize and push
            old_cwd = os.getcwd()
            try:
                os.chdir(project_sml_dir)
                
                # Initialize Git repository
                append_log(self.log_ref_container[0], "Initializing Git repository...")
                result = subprocess.run(['git', 'init'], capture_output=True, text=True, check=True)
                append_log(self.log_ref_container[0], f"✓ Git init: {result.stdout.strip()}")
                
                # Add all files
                append_log(self.log_ref_container[0], "Adding files to Git...")
                result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True, check=True)
                append_log(self.log_ref_container[0], "✓ Files added to Git")
                
                # Initial commit
                append_log(self.log_ref_container[0], "Creating initial commit...")
                result = subprocess.run(['git', 'commit', '-m', 'Initial commit with SML files'], 
                                    capture_output=True, text=True, check=True)
                append_log(self.log_ref_container[0], f"✓ Initial commit: {result.stdout.strip()}")
                
                # Rename branch to main
                append_log(self.log_ref_container[0], "Setting branch to main...")
                result = subprocess.run(['git', 'branch', '-M', 'main'], 
                                    capture_output=True, text=True, check=True)
                append_log(self.log_ref_container[0], "✓ Branch set to main")
                
                # Add remote origin
                git_id = self.config.get('git_id')
                remote_url = f"https://github.com/{repo_name}.git"
                append_log(self.log_ref_container[0], f"Adding remote origin: {remote_url}")
                result = subprocess.run(['git', 'remote', 'add', 'origin', remote_url], 
                                    capture_output=True, text=True, check=True)
                append_log(self.log_ref_container[0], "✓ Remote origin added")
                
                # Push to remote
                append_log(self.log_ref_container[0], "Pushing to remote repository...")
                result = subprocess.run(['git', 'push', '-u', 'origin', 'main'], 
                                    capture_output=True, text=True, check=True)
                append_log(self.log_ref_container[0], f"✓ Push successful: {result.stdout.strip()}")
                
                append_log(self.log_ref_container[0], f"✓ Successfully committed all files to new repository '{repo_name}'")
                return True
                
            except subprocess.CalledProcessError as e:
                append_log(self.log_ref_container[0], f"✗ Git command failed: {e}")
                append_log(self.log_ref_container[0], f"Error output: {e.stderr}")
                return False
            finally:
                os.chdir(old_cwd)
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"✗ Error committing files to Git: {e}")
            return False

    def commit_sml_to_git(self, project_name, repo_name):
        """Commit SML files to Git repository - recursively including all subdirectories and any file types"""
        try:
            # Use root directory as base for workspace
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.config.get("workspace", "working_dir")
            
            # If workspace is relative, make it relative to root directory
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
                
            sml_dir = os.path.join(workspace, "sml")
            project_sml_dir = os.path.join(sml_dir, project_name)
            
            if not os.path.exists(project_sml_dir):
                append_log(self.log_ref_container[0], f"No SML directory found for {project_name} at {project_sml_dir}")
                return False
            
            # Find ALL files recursively (not just .sml)
            all_files = {}
            file_count = 0
            for root, dirs, files in os.walk(project_sml_dir):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    # Calculate relative path from project_sml_dir
                    relative_path = os.path.relpath(file_path, project_sml_dir)
                    # Use forward slashes for Git paths
                    git_path = f"{project_name}/{relative_path}".replace('\\', '/')
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            all_files[git_path] = f.read()
                        file_count += 1
                    except Exception as e:
                        # If text reading fails, try binary for non-text files
                        try:
                            with open(file_path, 'rb') as f:
                                all_files[git_path] = f.read().decode('utf-8', errors='ignore')
                            file_count += 1
                        except Exception as e2:
                            append_log(self.log_ref_container[0], f"Error reading file {file_path}: {e2}")
            
            if not all_files:
                append_log(self.log_ref_container[0], f"No files found in {project_sml_dir}")
                return False
            
            # Count file types
            file_types = {}
            for git_path in all_files.keys():
                ext = os.path.splitext(git_path)[1].lower()
                file_types[ext] = file_types.get(ext, 0) + 1
            
            append_log(self.log_ref_container[0], f"Found {file_count} files to commit: {file_types}")
            
            # Check if repository exists, create if it doesn't
            repo_exists, error = self.api_git_ops.repository_exists(repo_name)
            if error:
                append_log(self.log_ref_container[0], f"Error checking repository {repo_name}: {error}")
                return False
                
            if not repo_exists:
                append_log(self.log_ref_container[0], f"Repository {repo_name} doesn't exist, creating it...")
                success, error = self.api_git_ops.create_repository(project_name)
                if not success:
                    append_log(self.log_ref_container[0], f"Failed to create repository {repo_name}: {error}")
                    return False
                append_log(self.log_ref_container[0], f"Created new repository: {repo_name}")
            
            # Commit all files to Git
            commit_message = f"Add SML files for project {project_name}"
            success_count = 0
            total_count = len(all_files)
            
            for git_path, content in all_files.items():
                success, error = self.api_git_ops.push_to_repository(
                    repo_name, content, git_path, commit_message
                )
                if success:
                    success_count += 1
                    append_log(self.log_ref_container[0], f"Committed {git_path} to {repo_name}")
                else:
                    append_log(self.log_ref_container[0], f"Failed to push {git_path}: {error}")
            
            append_log(self.log_ref_container[0], f"Successfully committed {success_count}/{total_count} files to {repo_name}")
            return success_count > 0
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error committing files to Git: {e}")
            return False