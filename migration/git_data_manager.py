# [file name]: git_data_manager.py
# [file content begin]
import threading
import tkinter as tk
from common import append_log

class GitDataManager:
    def __init__(self, config, log_ref_container, right_listbox, migration_ops):
        self.config = config
        self.log_ref_container = log_ref_container
        self.right_listbox = right_listbox
        self.migration_ops = migration_ops
        self._selected_repo_names = set()  # Track selected repos by name

    def load_git_repositories(self):
        """Load only repositories that contain catalog.yml (non-blocking)."""
        try:
            # Clear UI and show temporary status
            self.right_listbox.delete(0, tk.END)
            append_log(self.log_ref_container[0], "Filtering repositories for catalog.yml...")

            def worker():
                try:
                    # Prefer an existing GitOperations instance on migration_ops if present
                    git_ops = getattr(self.migration_ops, "git_ops", None)

                    # Fallback: import and create GitOperations if migration_ops doesn't expose one
                    if git_ops is None:
                        try:
                            from api.git_operations import GitOperations
                        except Exception:
                            # try alternate module path if needed
                            from api.git import GitOperations
                        cfg = getattr(self.migration_ops, "config", getattr(self, "config", {}))
                        git_ops = GitOperations(cfg)

                    # This performs the catalog.yml checks (concurrent by default)
                    matched = git_ops.get_repos_with_catalog(use_threads=True, max_workers=8)

                    # Update UI on main thread
                    def on_main_thread():
                        self.right_listbox.delete(0, tk.END)
                        for repo in matched:
                            self.right_listbox.insert(tk.END, repo)
                        append_log(self.log_ref_container[0], f"Loaded {len(matched)} Git repositories containing catalog.yml")
                        self._restore_selection()

                    # schedule UI update
                    self.right_listbox.after(0, on_main_thread)

                except Exception as e:
                    # Ensure any errors are reported on the main thread
                    self.right_listbox.after(0, lambda: append_log(self.log_ref_container[0], f"Error filtering repositories: {e}"))

            # Start background worker
            t = threading.Thread(target=worker, daemon=True)
            t.start()

        except Exception as e:
            append_log(self.log_ref_container[0], f"Error starting repository load: {e}")

    def refresh_git_repositories(self):
        """Refresh the Git repositories list"""
        self.save_selection_state()
        self.load_git_repositories()

    def save_selection_state(self):
        """Save current selection state"""
        selected_indices = self.right_listbox.curselection()
        self._selected_repo_names.clear()
        
        for index in selected_indices:
            repo_name = self.right_listbox.get(index)
            self._selected_repo_names.add(repo_name)

    def _restore_selection(self):
        """Restore selection after refresh"""
        if not self._selected_repo_names:
            return
            
        for index in range(self.right_listbox.size()):
            repo_name = self.right_listbox.get(index)
            if repo_name in self._selected_repo_names:
                self.right_listbox.selection_set(index)

    def get_selected_repositories(self):
        """Get list of selected repository names"""
        selected_indices = self.right_listbox.curselection()
        return [self.right_listbox.get(i) for i in selected_indices]
# [file content end]