# [file name]: migration_runner.py
# [file content begin]
import time
from common import append_log

class MigrationRunner:
    def __init__(self, migration_ops, installer_data_manager, git_data_manager, log_ref_container):
        self.migration_ops = migration_ops
        self.installer_data_manager = installer_data_manager
        self.git_data_manager = git_data_manager
        self.log_ref_container = log_ref_container

    def migrate_installer_to_container(self, selected_indices):
        """Migrate from Installer to Container/Git - automatically use project name as repo"""
        if not selected_indices:
            append_log(self.log_ref_container[0], "No projects selected for migration")
            return
        
        append_log(self.log_ref_container[0], f"Starting migration for {len(selected_indices)} selected items: Installer -> Container")
        
        # Collect projects to migrate
        projects_to_migrate = {}
        
        for index in selected_indices:
            item_data = self.installer_data_manager.get_item_data_by_index(index)
            if item_data and item_data.get("type") == "project":
                project_name = item_data.get("project_name")
                project_data = item_data.get("project_data", {})
                project_id = project_data.get("id")
                
                if project_name and project_id:
                    projects_to_migrate[project_name] = {
                        "project_id": project_id,
                        "project_data": project_data
                    }
        
        if not projects_to_migrate:
            append_log(self.log_ref_container[0], "No valid projects found for migration")
            return
        
        append_log(self.log_ref_container[0], f"Found {len(projects_to_migrate)} projects to migrate: {list(projects_to_migrate.keys())}")
        
        # Start migration for all projects
        project_names = list(projects_to_migrate.keys())
        self._migrate_projects_sequentially(project_names, projects_to_migrate, 0)

    def _migrate_projects_sequentially(self, project_names, projects_to_migrate, current_index):
        """Migrate projects one after another"""
        if current_index >= len(project_names):
            append_log(self.log_ref_container[0], "✓ All projects migration completed")
            # Refresh Git repositories list after successful migration
            append_log(self.log_ref_container[0], "Refreshing Git repositories list...")
            self.git_data_manager.refresh_git_repositories()
            return
        
        project_name = project_names[current_index]
        project_info = projects_to_migrate[project_name]
        
        append_log(self.log_ref_container[0], f"Starting migration {current_index + 1}/{len(project_names)} for project '{project_name}'")
        
        def migration_callback(success, project_name):
            if success:
                append_log(self.log_ref_container[0], f"✓ Migration completed successfully for '{project_name}'")
            else:
                append_log(self.log_ref_container[0], f"✗ Migration failed for '{project_name}'")
            
            # Reset the running flag before starting the next migration
            self.migration_ops.is_running = False
            
            # Add a small delay before starting the next migration
            time.sleep(1)
            
            # Continue with next project
            self._migrate_projects_sequentially(project_names, projects_to_migrate, current_index + 1)
        
        # Reset running flag before starting the next migration
        self.migration_ops.is_running = False
        success = self.migration_ops.migrate_project_to_git_async(
            project_info["project_id"], 
            project_name, 
            migration_callback
        )
        
        if not success:
            append_log(self.log_ref_container[0], f"Failed to start migration for '{project_name}', continuing with next project")
            # Continue with next project even if this one failed to start
            self._migrate_projects_sequentially(project_names, projects_to_migrate, current_index + 1)

    def migrate_container_to_installer(self, selected_repos):
        """Migrate from Container/Git to Installer"""
        if not selected_repos:
            append_log(self.log_ref_container[0], "No Git repositories selected for migration")
            return
            
        append_log(self.log_ref_container[0], f"Starting migration for {len(selected_repos)} selected repositories: Container -> Installer")
        
        # Get all selected repository names
        repo_names = selected_repos
        
        append_log(self.log_ref_container[0], f"Selected repositories: {repo_names}")
        
        # Start migration for all repositories
        self._migrate_repos_sequentially(repo_names, 0)

    def _migrate_repos_sequentially(self, repo_names, current_index):
        """Migrate repositories one after another"""
        if current_index >= len(repo_names):
            append_log(self.log_ref_container[0], "✓ All repositories migration completed")
            
            # Refresh installer data to show newly imported projects
            append_log(self.log_ref_container[0], "Refreshing installer source data...")
            self.installer_data_manager.refresh_installer_data()
            append_log(self.log_ref_container[0], "✓ Installer source refreshed")
            
            return
        
        repo_name = repo_names[current_index]
        
        # Extract project name from repo name (remove visibility tag)
        clean_repo_name = repo_name.split(" [")[0]
        project_name = clean_repo_name.split("/")[-1] if "/" in clean_repo_name else clean_repo_name
        
        append_log(self.log_ref_container[0], f"Starting migration {current_index + 1}/{len(repo_names)} for repository '{repo_name}' to project '{project_name}'")
        
        def migration_callback(success, project_name):
            if success:
                append_log(self.log_ref_container[0], f"✓ Reverse migration completed successfully for '{project_name}'")
            else:
                append_log(self.log_ref_container[0], f"✗ Reverse migration failed for '{project_name}'")
            
            # Reset the running flag before starting the next migration
            self.migration_ops.is_running = False
            
            # Add a small delay before starting the next migration
            time.sleep(1)
            
            # Continue with next repository
            self._migrate_repos_sequentially(repo_names, current_index + 1)
        
        # Reset running flag before starting the next migration
        self.migration_ops.is_running = False
        success = self.migration_ops.migrate_git_to_installer_async(
            repo_name, 
            project_name, 
            migration_callback
        )
        
        if not success:
            append_log(self.log_ref_container[0], f"Failed to start migration for '{repo_name}', continuing with next repository")
            # Continue with next repository even if this one failed to start
            self._migrate_repos_sequentially(repo_names, current_index + 1)
# [file content end]