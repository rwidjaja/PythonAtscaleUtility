# [file name]: wizard_git_operations.py
import os
import shutil
import subprocess
from common import append_log

class WizardGitOperations:
    def __init__(self, migration_controller, log_ref_container):
        self.migration_controller = migration_controller
        self.log_ref_container = log_ref_container
    
    def commit_common_to_git(self, common_name, source_dir):
        """Commit common dimensions using migration_ops"""
        try:
            migration_ops = self.migration_controller.migration_ops
            
            # Create repository name
            repo_name = f"{self.migration_controller.config.get('git_id')}/{common_name}"
            
            append_log(self.log_ref_container[0], f"Committing common dimensions to Git: {repo_name}")
            
            # Use migration_to_git to commit the directory
            success = migration_ops.migration_to_git.commit_sml_to_git_new_repo(
                project_name=common_name,
                repo_name=repo_name
            )
            
            if success:
                append_log(self.log_ref_container[0], f"✓ Successfully committed common dimensions to Git: {repo_name}")
                return True
            else:
                append_log(self.log_ref_container[0], f"✗ Failed to commit common dimensions to Git")
                return False
                
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error in Git commit: {e}")
            return False
    
    def manual_git_commit(self, common_name, source_dir, repo_name):
        """Manual Git commit as fallback"""
        try:
            import subprocess
            import os
            
            # Get workspace directory
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.migration_controller.config.get("workspace", "working_dir")
            
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
            
            # Create Git repository directory
            git_dir = os.path.join(workspace, "git", repo_name)
            os.makedirs(git_dir, exist_ok=True)
            
            append_log(self.log_ref_container[0], f"Creating Git repository at: {git_dir}")
            
            # Initialize Git repository
            subprocess.run(['git', 'init'], cwd=git_dir, check=True)
            
            # Copy all files from source_dir to git_dir
            for item in os.listdir(source_dir):
                s = os.path.join(source_dir, item)
                d = os.path.join(git_dir, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
            
            # Add all files
            subprocess.run(['git', 'add', '.'], cwd=git_dir, check=True)
            
            # Commit
            commit_message = f"Add common dimensions: {common_name}"
            result = subprocess.run(['git', 'commit', '-m', commit_message], 
                                   cwd=git_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                append_log(self.log_ref_container[0], f"✓ Successfully committed common dimensions to Git: {repo_name}")
                append_log(self.log_ref_container[0], f"Git output: {result.stdout}")
                return True
            else:
                append_log(self.log_ref_container[0], f"✗ Git commit failed: {result.stderr}")
                return False
                
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error in manual Git commit: {e}")
            return False