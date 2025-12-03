# [file name]: support_zip_ui.py
import tkinter as tk
from tkinter import ttk
from common import append_log
from migration.support_zip_treeview import SupportZipTreeView
from migration.support_zip_actions import SupportZipActions

class SupportZipUI:
    def __init__(self, processor, wizard_controller, migration_controller, log_ref_container):
        self.processor = processor
        self.wizard_controller = wizard_controller
        self.migration_controller = migration_controller
        self.log_ref_container = log_ref_container
        self.selection_window = None
        self.tree_view = None
        self.actions = None
        self.selection_count_var = tk.StringVar()
        
    def create_selection_window(self, parent, projects):
        """Create window for selecting projects from support zip"""
        self.selection_window = tk.Toplevel(parent)
        self.selection_window.title("Support Zip Projects")
        self.selection_window.geometry("900x600")
        self.selection_window.resizable(True, True)
        
        # Make it modal
        self.selection_window.transient(parent)
        self.selection_window.grab_set()
        
        # Initialize components
        self.tree_view = SupportZipTreeView(self.selection_window, self.log_ref_container)
        self.actions = SupportZipActions(
            self.processor, 
            self.wizard_controller, 
            self.migration_controller,
            self.log_ref_container
        )
        
        self._build_ui(projects)
        return self.selection_window
    
    def _build_ui(self, projects):
        """Build the project selection UI"""
        main_frame = ttk.Frame(self.selection_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and info
        self._build_header(main_frame)
        
        # Treeview section
        tree_frame = self.tree_view.create_treeview_frame(main_frame, projects)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Selection control buttons
        self._build_selection_controls(main_frame)
        
        # Action buttons
        self._build_action_buttons(main_frame)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Select projects and choose an action")
        self.status_label.pack(pady=(10, 0))
    
    def _build_header(self, parent):
        """Build the header section with title and info"""
        title_label = ttk.Label(parent, text="Projects from Support Zip", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))
        
        info_label = ttk.Label(parent, 
                              text="Select projects from the list below and choose an action.",
                              wraplength=800)
        info_label.pack(pady=(0, 15))
    
    def _build_selection_controls(self, parent):
        """Build selection control buttons"""
        button_frame1 = ttk.Frame(parent)
        button_frame1.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame1, text="Select All", 
                  command=self.tree_view.select_all_projects).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame1, text="Deselect All", 
                  command=self.tree_view.deselect_all_projects).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame1, text="Invert Selection", 
                  command=self.tree_view.invert_selection).pack(side=tk.LEFT)
        
        # Selection count label
        self.selection_count_var = tk.StringVar(value="Selected: 0 / 0")
        ttk.Label(button_frame1, textvariable=self.selection_count_var).pack(side=tk.RIGHT)
        
        # Update selection count when tree changes
        self.tree_view.set_selection_callback(self._update_selection_count)
    
    def _build_action_buttons(self, parent):
        """Build action buttons"""
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Migration Wizard button
        wizard_btn = ttk.Button(action_frame, text="Migration Wizard", 
                               command=self._open_migration_wizard,
                               width=15)
        wizard_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Migrate button
        migrate_btn = ttk.Button(action_frame, text="Migrate", 
                                command=self._migrate_selected_to_git,
                                width=15)
        migrate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Close button
        ttk.Button(action_frame, text="Close", 
                  command=self.selection_window.destroy,
                  width=15).pack(side=tk.RIGHT)
    
    def _update_selection_count(self, selected, total):
        """Update the selection count label"""
        self.selection_count_var.set(f"Selected: {selected} / {total}")
    
    def _open_migration_wizard(self):
        """Open migration wizard for selected projects"""
        selected_projects = self.tree_view.get_selected_projects()
        
        if not selected_projects:
            self.status_label.config(text="Please select at least one project", foreground="red")
            return
        
        if len(selected_projects) < 2:
            self.status_label.config(text="Wizard requires at least 2 projects for analysis", foreground="red")
            return
        
        # Close selection window
        self.selection_window.destroy()
        
        # Open wizard
        self.actions.open_migration_wizard(selected_projects)
    
    def _migrate_selected_to_git(self):
        """Migrate selected projects to Git"""
        selected_projects = self.tree_view.get_selected_projects()
        
        if not selected_projects:
            self.status_label.config(text="Please select at least one project", foreground="red")
            return
        
        self.status_label.config(text="Migrating selected projects to Git...", foreground="black")
        self.selection_window.update()
        
        success_count = self.actions.migrate_to_git(selected_projects)
        
        self.status_label.config(
            text=f"Migrated {success_count}/{len(selected_projects)} project(s) to Git", 
            foreground="green" if success_count > 0 else "red"
        )
        
        # Refresh Git repositories list in main UI
        if success_count > 0:
            self.migration_controller.refresh_git_repositories()