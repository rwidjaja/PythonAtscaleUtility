import os
import requests
from common import append_log
from api.git_operations import GitOperations as ApiGitOperations

class MigrationFromGit:
    def __init__(self, config, log_ref_container):
        self.config = config
        self.log_ref_container = log_ref_container
        self.api_git_ops = ApiGitOperations(config)

    def clone_git_repository(self, repo_name, project_name):
        """Clone Git repository to workspace"""
        try:
            # Use root directory as base for workspace
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.config.get("workspace", "working_dir")
            
            # If workspace is relative, make it relative to root directory
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
                
            git_dir = os.path.join(workspace, "git_repos")
            repo_dir = os.path.join(git_dir, project_name)
            
            # Remove visibility tag for API call
            clean_repo_name = repo_name.split(" [")[0]
            
            # Check if repository already exists
            if os.path.exists(repo_dir):
                append_log(self.log_ref_container[0], f"Repository already exists at {repo_dir}, pulling latest...")
                # TODO: Implement git pull
                return True
            else:
                os.makedirs(repo_dir, exist_ok=True)
                
                # Clone using GitHub API to get archive
                headers = {
                    "Authorization": f"Bearer {self.config.get('git_token')}",
                    "Accept": "application/vnd.github.v3+json"
                }
                
                # Get repository contents recursively
                url = f"https://api.github.com/repos/{clean_repo_name}/contents/"
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code != 200:
                    append_log(self.log_ref_container[0], f"Failed to get repository contents: {response.status_code}")
                    return False
                
                contents = response.json()
                
                # Download all files recursively
                success = self._download_repository_contents(clean_repo_name, contents, repo_dir, "")
                if success:
                    append_log(self.log_ref_container[0], f"Cloned repository {clean_repo_name} to {repo_dir}")
                    return True
                else:
                    append_log(self.log_ref_container[0], f"Failed to clone repository {clean_repo_name}")
                    return False
                    
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error cloning Git repository: {e}")
            return False

    def _download_repository_contents(self, repo_name, contents, base_dir, path):
        """Download repository contents recursively"""
        try:
            headers = {
                "Authorization": f"Bearer {self.config.get('git_token')}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            for item in contents:
                item_path = os.path.join(path, item['name'])
                full_path = os.path.join(base_dir, item_path)
                
                if item['type'] == 'file':
                    # Download file content
                    if 'download_url' in item and item['download_url']:
                        response = requests.get(item['download_url'], timeout=30)
                        if response.status_code == 200:
                            os.makedirs(os.path.dirname(full_path), exist_ok=True)
                            with open(full_path, 'w', encoding='utf-8') as f:
                                f.write(response.text)
                        else:
                            append_log(self.log_ref_container[0], f"Failed to download {item_path}")
                            return False
                elif item['type'] == 'dir':
                    # Recursively download directory
                    dir_url = item['url']
                    dir_response = requests.get(dir_url, headers=headers, timeout=30)
                    if dir_response.status_code == 200:
                        dir_contents = dir_response.json()
                        if not self._download_repository_contents(repo_name, dir_contents, base_dir, item_path):
                            return False
                    else:
                        append_log(self.log_ref_container[0], f"Failed to get directory contents for {item_path}")
                        return False
            
            return True
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error downloading repository contents: {e}")
            return False