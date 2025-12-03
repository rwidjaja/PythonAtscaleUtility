import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from common import append_log

class GitOperations:
    def __init__(self, config):
        self.config = config
        self.git_token = config.get("git_token")
        self.git_id = config.get("git_id")
        self.base_url = "https://api.github.com"
        # Simple in-memory cache to avoid repeated checks during a session
        self._catalog_check_cache = {}

    def _headers(self):
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if self.git_token:
            headers["Authorization"] = f"Bearer {self.git_token}"
        return headers

    def get_personal_repositories(self):
        """Get personal Git repositories (both public and private)"""
        try:
            headers = self._headers()
            url = f"{self.base_url}/user/repos"
            params = {
                "visibility": "all",
                "affiliation": "owner",
                "sort": "full_name",
                "per_page": 100
            }

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code != 200:
                error_msg = f"GitHub API returned {response.status_code}: {response.text}"
                return [], error_msg

            repositories = response.json()

            if not isinstance(repositories, list):
                error_msg = f"Unexpected response format: {repositories}"
                return [], error_msg

            repo_list = []
            for repo in repositories:
                repo_name = repo.get("full_name", "")
                private = repo.get("private", False)
                visibility = "private" if private else "public"
                display_name = f"{repo_name} [{visibility}]"
                repo_list.append(display_name)

            return repo_list, None

        except requests.exceptions.RequestException as e:
            error_msg = f"GitHub API request failed: {e}"
            return [], error_msg
        except Exception as e:
            error_msg = f"Unexpected error fetching repositories: {e}"
            return [], error_msg

    def repository_exists(self, repo_name):
        """Check if a repository exists"""
        try:
            headers = self._headers()
            url = f"{self.base_url}/repos/{repo_name}"
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                return True, None
            elif response.status_code == 404:
                return False, None
            else:
                error_msg = f"GitHub API returned {response.status_code}: {response.text}"
                return False, error_msg

        except Exception as e:
            return False, f"Error checking repository existence: {e}"

    def create_repository(self, repo_name):
        """Create a new repository"""
        try:
            headers = self._headers()
            url = f"{self.base_url}/user/repos"
            payload = {
                "name": repo_name,
                "private": True,
                "auto_init": False
            }

            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 201:
                return True, None
            else:
                error_msg = f"GitHub API returned {response.status_code}: {response.text}"
                return False, error_msg

        except Exception as e:
            return False, f"Error creating repository: {e}"

    def delete_repository(self, repo_name):
        """Delete a repository"""
        try:
            headers = self._headers()
            url = f"{self.base_url}/repos/{repo_name}"
            response = requests.delete(url, headers=headers, timeout=30)

            if response.status_code == 204:
                return True, None
            else:
                error_msg = f"GitHub API returned {response.status_code}: {response.text}"
                return False, error_msg

        except Exception as e:
            return False, f"Error deleting repository: {e}"

    def _get_fallback_repositories(self):
        """Fallback repositories in case GitHub API fails"""
        git_id = self.git_id or "your-username"
        return [
            f"{git_id}/atscale-models [private]",
            f"{git_id}/business-analytics [public]",
            f"{git_id}/data-warehouse [private]",
            f"{git_id}/sales-dashboard [public]",
            f"{git_id}/marketing-reports [private]",
            f"{git_id}/personal-projects [public]",
            f"{git_id}/experimental-models [private]"
        ]

    def get_repository_contents(self, repo_name):
        """Get contents of a specific repository (root contents)"""
        try:
            clean_repo_name = repo_name.split(" [")[0]
            headers = self._headers()
            url = f"{self.base_url}/repos/{clean_repo_name}/contents"
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                return [], f"GitHub API returned {response.status_code} for {clean_repo_name}"

            return response.json(), None

        except Exception as e:
            return [], f"Error getting repository contents for {repo_name}: {e}"

    def push_to_repository(self, repo_name, data, file_path, commit_message):
        """Push data to Git repository"""
        try:
            clean_repo_name = repo_name.split(" [")[0]
            headers = self._headers()
            url = f"{self.base_url}/repos/{clean_repo_name}/contents/{file_path}"

            import base64
            content_b64 = base64.b64encode(data.encode('utf-8')).decode('utf-8')

            payload = {
                "message": commit_message,
                "content": content_b64,
                "branch": "main"
            }

            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                existing_file = response.json()
                payload["sha"] = existing_file.get("sha")

            response = requests.put(url, headers=headers, json=payload, timeout=30)

            if response.status_code in [200, 201]:
                return True, None
            else:
                error_msg = f"GitHub API returned {response.status_code}: {response.text}"
                return False, error_msg

        except Exception as e:
            return False, f"Error pushing to repository {repo_name}: {e}"

    def pull_from_repository(self, repo_name, file_path):
        """Pull data from Git repository"""
        try:
            clean_repo_name = repo_name.split(" [")[0]
            headers = self._headers()
            url = f"{self.base_url}/repos/{clean_repo_name}/contents/{file_path}"
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                return None, f"GitHub API returned {response.status_code} for {file_path}"

            file_data = response.json()
            import base64
            content = base64.b64decode(file_data["content"]).decode('utf-8')
            return content, None

        except Exception as e:
            return None, f"Error pulling from repository {repo_name}: {e}"

    # -------------------------
    # New helper: check for catalog.yml
    # -------------------------
    def _repo_has_catalog(self, display_repo_name):
        """
        Check whether the repository contains 'catalog.yml' at the repository root.
        display_repo_name is expected in the format 'owner/repo [visibility]'.
        Uses cache to avoid repeated network calls.
        """
        try:
            clean_name = display_repo_name.split(" [")[0]
            if clean_name in self._catalog_check_cache:
                return self._catalog_check_cache[clean_name]

            headers = self._headers()
            url = f"{self.base_url}/repos/{clean_name}/contents/catalog.yml"
            resp = requests.get(url, headers=headers, timeout=12)

            # 200 -> exists, 404 -> not found, other -> treat as not found but log
            if resp.status_code == 200:
                has_catalog = True
            elif resp.status_code == 404:
                has_catalog = False
            else:
                append_log(f"Warning: checking {clean_name} returned {resp.status_code}")
                has_catalog = False

            # Cache the result (True/False)
            self._catalog_check_cache[clean_name] = has_catalog
            return has_catalog

        except requests.RequestException as e:
            append_log(f"Network error checking {display_repo_name}: {e}")
            self._catalog_check_cache[clean_name] = False
            return False
        except Exception as e:
            append_log(f"Error checking {display_repo_name} for catalog.yml: {e}")
            self._catalog_check_cache[clean_name] = False
            return False

    def get_repos_with_catalog(self, use_threads=True, max_workers=8):
        """
        Return a list of repositories (display names) that contain 'catalog.yml' at the repo root.
        - use_threads: run checks concurrently to speed up many-repo scenarios.
        - max_workers: number of threads to use when use_threads is True.
        """
        repos, err = self.get_personal_repositories()
        if err:
            append_log(f"Error loading repositories: {err}")
            # Do not return the unfiltered list; return empty so UI shows only matching repos
            return []

        if not repos:
            return []

        matched = []

        if use_threads:
            with ThreadPoolExecutor(max_workers=min(max_workers, len(repos))) as ex:
                future_to_repo = {ex.submit(self._repo_has_catalog, r): r for r in repos}
                for fut in as_completed(future_to_repo):
                    repo = future_to_repo[fut]
                    try:
                        if fut.result():
                            matched.append(repo)
                    except Exception as e:
                        append_log(f"Error checking repo {repo}: {e}")
        else:
            for r in repos:
                try:
                    if self._repo_has_catalog(r):
                        matched.append(r)
                except Exception as e:
                    append_log(f"Error checking repo {r}: {e}")

        return matched
