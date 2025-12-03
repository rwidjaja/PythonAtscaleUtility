# [file name]: support_zip_git_ops.py
import os
import re
import shutil
import subprocess
from tkinter import messagebox
from common import append_log

class SupportZipGitOps:
    def __init__(self, config, log_ref_container, migration_ops):
        self.config = config
        self.log_ref_container = log_ref_container
        self.migration_ops = migration_ops
        
    def sanitize_name(self, name):
        """Sanitize the name for folder and file naming"""
        sanitized = re.sub(r'[^\w\s-]', '', name)
        sanitized = re.sub(r'[-\s]+', '-', sanitized)
        sanitized = sanitized.lower().strip('-')
        return sanitized
        
    def commit_project_to_git(self, project_info):
        """Commit a project from support zip to Git - simplified for existing SML"""
        try:
            project_name = project_info['name']
            project_dir = project_info['directory']
            
            # Sanitize repository name
            sanitized_name = self._sanitize_name(project_name)
            repo_name = f"{self.config.get('git_id')}/{sanitized_name}"
            
            append_log(self.log_ref_container[0], 
                      f"Committing project {project_name} to Git repository {repo_name}")
            
            # Check if repository already exists
            repo_exists, error = self.migration_ops.api_git_ops.repository_exists(repo_name)
            if error:
                append_log(self.log_ref_container[0], f"Error checking repository {repo_name}: {error}")
                return False
                
            if repo_exists:
                append_log(self.log_ref_container[0], f"Repository {repo_name} already exists")
                
                # Ask if we should overwrite or create new
                overwrite = messagebox.askyesno(
                    "Repository Exists",
                    f"Repository '{repo_name}' already exists.\n\n"
                    f"Do you want to:\n"
                    f"1. Overwrite existing repository? (will delete and recreate)\n"
                    f"2. Cancel?"
                )
                
                if overwrite:
                    # Delete existing repository
                    success, error = self.migration_ops.api_git_ops.delete_repository(repo_name)
                    if not success:
                        append_log(self.log_ref_container[0], f"Failed to delete repository: {error}")
                        return False
                else:
                    return False
            
            # Create repository
            success, error = self.migration_ops.api_git_ops.create_repository(sanitized_name)
            if not success:
                append_log(self.log_ref_container[0], f"Failed to create repository: {error}")
                return False
            
            append_log(self.log_ref_container[0], f"Created repository: {repo_name}")
            
            # Create a temporary workspace directory for Git operations
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.config.get("workspace", "working_dir")
            
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
            
            # Create temp directory for Git operations
            temp_dir = os.path.join(workspace, "temp_git", sanitized_name)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            # Copy project to temp directory
            shutil.copytree(project_dir, temp_dir)
            
            # Initialize Git repository and push
            success = self._init_and_push_git(temp_dir, sanitized_name, repo_name)
            
            # Clean up temp directory
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except:
                pass
            
            if success:
                append_log(self.log_ref_container[0], f"✓ Successfully committed {project_name} to Git")
            else:
                append_log(self.log_ref_container[0], f"✗ Failed to commit {project_name} to Git")
            
            return success
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error committing project to Git: {e}")
            return False
    
    def _init_and_push_git(self, project_dir, project_name, repo_name):
        """Initialize Git repository and push using standard Git commands"""
        try:
            old_cwd = os.getcwd()
            os.chdir(project_dir)
            
            append_log(self.log_ref_container[0], "Initializing Git repository...")
            
            # Step 1: git init
            result = subprocess.run(['git', 'init'], capture_output=True, text=True)
            if result.returncode != 0:
                append_log(self.log_ref_container[0], f"Git init failed: {result.stderr}")
                return False
            append_log(self.log_ref_container[0], "✓ git init completed")
            
            # Step 2: git add README.md (if exists) or all files
            if os.path.exists("README.md"):
                result = subprocess.run(['git', 'add', 'README.md'], capture_output=True, text=True)
                append_log(self.log_ref_container[0], "✓ git add README.md")
            else:
                # Create a README.md file
                with open("README.md", "w") as f:
                    f.write(f"# {project_name}\n\nProject migrated from support zip.")
                result = subprocess.run(['git', 'add', 'README.md'], capture_output=True, text=True)
                append_log(self.log_ref_container[0], "✓ Created and added README.md")
            
            # Add all other files
            result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
            if result.returncode != 0:
                append_log(self.log_ref_container[0], f"Git add failed: {result.stderr}")
                return False
            append_log(self.log_ref_container[0], "✓ git add . completed")
            
            # Step 3: git commit -m "first commit"
            result = subprocess.run(['git', 'commit', '-m', 'first commit'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                append_log(self.log_ref_container[0], f"Git commit failed: {result.stderr}")
                return False
            append_log(self.log_ref_container[0], "✓ git commit completed")
            
            # Step 4: git branch -M main
            result = subprocess.run(['git', 'branch', '-M', 'main'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                append_log(self.log_ref_container[0], f"Git branch rename failed: {result.stderr}")
                return False
            append_log(self.log_ref_container[0], "✓ git branch -M main completed")
            
            # Step 5: git remote add origin
            git_id = self.config.get('git_id')
            remote_url = f"https://github.com/{repo_name}.git"
            result = subprocess.run(['git', 'remote', 'add', 'origin', remote_url], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                append_log(self.log_ref_container[0], f"Git remote add failed: {result.stderr}")
                return False
            append_log(self.log_ref_container[0], f"✓ git remote add origin {remote_url}")
            
            # Step 6: git push -u origin main
            append_log(self.log_ref_container[0], "Pushing to remote repository...")
            result = subprocess.run(['git', 'push', '-u', 'origin', 'main'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                append_log(self.log_ref_container[0], f"Git push failed: {result.stderr}")
                return False
            
            append_log(self.log_ref_container[0], "✓ git push -u origin main completed")
            
            return True
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error in Git operations: {e}")
            return False
        finally:
            os.chdir(old_cwd)
    