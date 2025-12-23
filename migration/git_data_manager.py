# [file name]: git_data_manager.py

import threading
import queue
import tkinter as tk
from common import append_log


class GitDataManager:
    def __init__(self, config, log_ref_container, right_listbox, migration_ops):
        self.config = config
        self.log_ref_container = log_ref_container
        self.right_listbox = right_listbox
        self.migration_ops = migration_ops

        self._selected_repo_names = set()   # Track selected repos by name
        self._ui_queue = queue.Queue()      # Thread-safe UI communication queue
        self._polling_started = False

    def load_git_repositories(self):
        """Load only repositories that contain catalog.yml (non-blocking)."""

        # --- UI updates MUST happen on main thread ---
        self.right_listbox.delete(0, tk.END)
        append_log(
            self.log_ref_container[0],
            "Filtering repositories for catalog.yml..."
        )

        # Start UI queue polling once
        if not self._polling_started:
            self._polling_started = True
            self.right_listbox.after(100, self._process_ui_queue)

        def worker():
            """Background thread: NO Tkinter calls allowed here"""
            try:
                git_ops = getattr(self.migration_ops, "git_ops", None)

                if git_ops is None:
                    try:
                        from api.git_operations import GitOperations
                    except Exception:
                        from api.git import GitOperations

                    cfg = getattr(
                        self.migration_ops,
                        "config",
                        getattr(self, "config", {})
                    )
                    git_ops = GitOperations(cfg)

                matched = git_ops.get_repos_with_catalog(
                    use_threads=True,
                    max_workers=8
                )

                # Send success result to main thread
                self._ui_queue.put(("success", matched))

            except Exception as e:
                # Send error to main thread
                self._ui_queue.put(("error", str(e)))

        # Start background worker
        threading.Thread(target=worker, daemon=True).start()

    def _process_ui_queue(self):
        """Process queued UI updates on the main Tk thread"""
        try:
            while True:
                msg_type, payload = self._ui_queue.get_nowait()

                if msg_type == "success":
                    self.right_listbox.delete(0, tk.END)

                    for repo in payload:
                        self.right_listbox.insert(tk.END, repo)

                    append_log(
                        self.log_ref_container[0],
                        f"Loaded {len(payload)} Git repositories containing catalog.yml"
                    )

                    self._restore_selection()

                elif msg_type == "error":
                    append_log(
                        self.log_ref_container[0],
                        f"Error filtering repositories: {payload}"
                    )

        except queue.Empty:
            pass

        # Continue polling
        self.right_listbox.after(100, self._process_ui_queue)

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