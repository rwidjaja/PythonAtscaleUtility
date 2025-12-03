# [file name]: migration_controller.py
# [file content begin]
import tkinter as tk
from common import append_log
from migration.installer_data_manager import InstallerDataManager
from migration.git_data_manager import GitDataManager
from migration.migration_runner import MigrationRunner
from migration.project_deletion_manager import ProjectDeletionManager

class MigrationController:
    def __init__(self, config, log_ref_container, left_listbox, right_listbox, mode_var):
        self.config = config
        self.log_ref_container = log_ref_container
        self.left_listbox = left_listbox
        self.right_listbox = right_listbox
        self.mode_var = mode_var
        
        # Initialize managers
        self.installer_data_manager = InstallerDataManager(config, log_ref_container, left_listbox)
        self.git_data_manager = None  # Will be set after migration_ops is available
        self.migration_runner = None  # Will be set after migration_ops is available
        self.project_deletion_manager = ProjectDeletionManager(config, log_ref_container, self.installer_data_manager)
        
        self.migration_ops = None

    def set_migration_ops(self, migration_ops):
        """Set the migration operations instance and initialize dependent managers"""
        self.migration_ops = migration_ops
        self.git_data_manager = GitDataManager(self.config, self.log_ref_container, self.right_listbox, self.migration_ops)
        self.migration_runner = MigrationRunner(self.migration_ops, self.installer_data_manager, self.git_data_manager, self.log_ref_container)

    def refresh_all(self):
        """Refresh both installer data and Git repositories"""
        append_log(self.log_ref_container[0], "Refreshing both installer and Git data...")
        
        # Save selection states before refresh
        self.installer_data_manager.save_selection_state()
        if self.git_data_manager:
            self.git_data_manager.save_selection_state()
        
        self.load_installer_data()
        self.refresh_git_repositories()
        append_log(self.log_ref_container[0], "✓ Both installer and Git data refreshed")

    def delete_selected_project(self):
        """Delete the selected project from AtScale"""
        # Save selection state before deletion
        self.installer_data_manager.save_selection_state()
        
        selected_indices = self.left_listbox.curselection()
        return self.project_deletion_manager.delete_selected_project(selected_indices)

    def set_selection_mode(self, mode):
        """Enable/disable selection based on migration direction"""
        if mode == "installer_to_container":
            self.left_listbox.configure(selectmode=tk.EXTENDED)
            self.right_listbox.configure(selectmode=tk.MULTIPLE)
            self.right_listbox.configure(state='normal')
            append_log(self.log_ref_container[0], "Mode: Installer to Container - Select projects on left")
        else:
            self.left_listbox.configure(selectmode=tk.MULTIPLE)
            self.right_listbox.configure(selectmode=tk.MULTIPLE)
            self.right_listbox.configure(state='normal')
            append_log(self.log_ref_container[0], "Mode: Container to Installer - Select repos on right")

    def load_installer_data(self):
        """Load installer data using InstallerDataManager"""
        self.installer_data_manager.load_installer_data()

    def load_git_repositories(self):
        """Load Git repositories using GitDataManager"""
        if self.git_data_manager:
            self.git_data_manager.load_git_repositories()

    def cleanup_workspace(self):
        """Clean up the entire workspace"""
        if self.migration_ops:
            self.migration_ops.cleanup_workspace()

    def delete_selected_git_repo(self):
        """Delete the selected Git repository"""
        # Save selection state before deletion
        if self.git_data_manager:
            self.git_data_manager.save_selection_state()
            
        selected_repos = self.right_listbox.curselection()
        if not selected_repos:
            append_log(self.log_ref_container[0], "No Git repository selected for deletion")
            return False
            
        repo_name = self.right_listbox.get(selected_repos[0])
        
        # Confirm deletion
        import tkinter.messagebox as messagebox
        result = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete repository:\n{repo_name}?\n\nThis action cannot be undone!"
        )
        
        if result:
            success = self.migration_ops.delete_git_repository(repo_name)
            if success:
                # Reload repositories list
                self.load_git_repositories()
            return success
        return False

    def refresh_git_repositories(self):
        """Refresh the Git repositories list"""
        if self.git_data_manager:
            self.git_data_manager.refresh_git_repositories()

    def start_migration(self):
        """Start the migration process based on selected mode and items"""
        if not self.migration_runner:
            append_log(self.log_ref_container[0], "Migration runner not initialized")
            return
            
        try:
            if self.migration_ops.is_running:
                append_log(self.log_ref_container[0], "Migration already in progress. Please wait...")
                return

            if self.mode_var.get():  # Container to Installer
                selected_repos = self.git_data_manager.get_selected_repositories()
                self.migration_runner.migrate_container_to_installer(selected_repos)
            else:  # Installer to Container
                selected_indices = self.installer_data_manager.get_all_selected_indices()
                self.migration_runner.migrate_installer_to_container(selected_indices)
                
        except Exception as e:
            append_log(self.log_ref_container[0], f"Migration error: {e}")

    def refresh_installer_data(self):
        """Refresh installer data and update the listbox"""
        self.installer_data_manager.refresh_installer_data()

    def get_selected_project_count(self):
        """Get count of selected projects for wizard button"""
        return self.installer_data_manager.get_selected_project_count()
# [file content end]