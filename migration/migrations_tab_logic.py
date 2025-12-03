# tabs/migrations_tab_logic.py
import tkinter as tk
from tkinter import ttk, messagebox
from common import append_log, load_config
from migration.migration_controller import MigrationController
from migration.wizard_controller import WizardController
from migration.support_zip_processor import SupportZipProcessor
from migration.support_zip_ui import SupportZipUI
from migration.migration_operations import MigrationOperations


class MigrationsTabLogic:
    def __init__(self, ui, content, log_ref_container):
        """
        ui: MigrationsTabUI instance (built in migrations_tab_ui.py)
        content: parent container (frame)
        log_ref_container: shared log reference (list containing the log widget)
        """
        self.ui = ui
        self.content = content
        self.log_ref_container = log_ref_container

        # Controllers and ops
        self.config = load_config()
        self.migration_controller = MigrationController(
            config=self.config,
            log_ref_container=log_ref_container,
            left_listbox=self.ui.listbox_left,
            right_listbox=self.ui.listbox_right,
            mode_var=self.ui.mode_var
        )
        self.migration_wizard = WizardController(content, self.migration_controller, log_ref_container)

        migration_ops = MigrationOperations(self.config, log_ref_container)
        self.migration_controller.set_migration_ops(migration_ops)

        # Wire everything
        self._wire_mode_toggle()
        self._wire_sticky_selection()
        self._wire_buttons()
        self._wire_async_wrappers()

        # Initial load
        self._initial_load()

    # ----- Wiring helpers -----

    def _wire_mode_toggle(self):
        """Bind the mode toggle to set selection mode and log."""
        def toggle_mode():
            if self.ui.mode_var.get():
                append_log(self.log_ref_container[0], "Mode set: SML to Installer Project")
                self.migration_controller.set_selection_mode("container_to_installer")
            else:
                append_log(self.log_ref_container[0], "Mode set: Installer Project to SML")
                self.migration_controller.set_selection_mode("installer_to_container")
        self.ui.mode_check.configure(command=toggle_mode)

    def _wire_sticky_selection(self):
        """Sticky toggle selection for both listboxes (prevents drag-select overwriting)."""
        def toggle(lb, event):
            lb.focus_set()
            idx = lb.nearest(event.y)
            if idx is None or idx < 0 or idx >= lb.size():
                return "break"
            if lb.selection_includes(idx):
                lb.selection_clear(idx)
            else:
                lb.selection_set(idx)
            lb.activate(idx)
            lb.event_generate("<<ListboxSelect>>")
            return "break"

        def block_drag(event):
            return "break"

        self.ui.listbox_left.bind("<Button-1>", lambda e: toggle(self.ui.listbox_left, e), add=False)
        self.ui.listbox_left.bind("<B1-Motion>", block_drag, add=False)

        self.ui.listbox_right.bind("<Button-1>", lambda e: toggle(self.ui.listbox_right, e), add=False)
        self.ui.listbox_right.bind("<B1-Motion>", block_drag, add=False)

        # Update wizard button state on selection changes
        def update_wizard_button_state(*args):
            selected_count = self.migration_controller.get_selected_project_count()
            self.ui.wizard_btn.config(state="normal" if selected_count > 1 else "disabled")

        self.ui.listbox_left.bind("<<ListboxSelect>>", lambda e: update_wizard_button_state())
        self.ui.listbox_right.bind("<<ListboxSelect>>", lambda e: update_wizard_button_state())

    def _wire_buttons(self):
        """Bind button actions to controller and wizard."""
        def update_status():
            if self.migration_controller.migration_ops.is_running:
                current_project = self.migration_controller.migration_ops.current_project or "Processing..."
                self.ui.status_label.config(text=f"Migrating: {current_project}")
                self.content.after(1000, update_status)
            else:
                self.ui.status_label.config(text="Ready")

        def start_migration_with_status():
            self.migration_controller.start_migration()
            update_status()

        self.ui.migrate_btn.configure(command=start_migration_with_status)
        self.ui.refresh_btn.configure(command=lambda: self.migration_controller.refresh_all())
        self.ui.cleanup_btn.configure(command=lambda: self.migration_controller.cleanup_workspace())
        self.ui.delete_project_btn.configure(command=lambda: self.migration_controller.delete_selected_project())
        self.ui.delete_repo_btn.configure(command=lambda: self.migration_controller.delete_selected_git_repo())
        self.ui.wizard_btn.configure(command=lambda: self.migration_wizard.open_wizard())

        # Support.zip handling
        def load_support_zip():
            self.ui.load_support_zip_btn.config(state="disabled")
            self.content.update()
            try:
                support_processor = SupportZipProcessor(
                    self.config, self.log_ref_container, self.migration_controller.migration_ops
                )
                zip_path = support_processor.open_support_zip()
                if not zip_path:
                    self.ui.load_support_zip_btn.config(state="normal")
                    return

                processing_msg = tk.Toplevel(self.content)
                processing_msg.title("Processing")
                processing_msg.geometry("300x100")
                processing_msg.transient(self.content)
                processing_msg.grab_set()
                ttk.Label(processing_msg, text="Processing support zip file...\nPlease wait.").pack(pady=20)
                processing_msg.update()

                projects = support_processor.process_support_zip(zip_path)
                processing_msg.destroy()

                if not projects:
                    messagebox.showerror("Error", "No valid projects found in support zip")
                    self.ui.load_support_zip_btn.config(state="normal")
                    return

                support_ui = SupportZipUI(
                    support_processor,
                    self.migration_wizard,
                    self.migration_controller,
                    self.log_ref_container
                )
                selection_window = support_ui.create_selection_window(self.content, projects)

                def on_window_close():
                    self.ui.load_support_zip_btn.config(state="normal")
                    self.migration_controller.cleanup_workspace()
                    selection_window.destroy()

                selection_window.protocol("WM_DELETE_WINDOW", on_window_close)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to process support zip: {str(e)}")
                self.ui.load_support_zip_btn.config(state="normal")

        self.ui.load_support_zip_btn.configure(command=load_support_zip)

    def _wire_async_wrappers(self):
        """Wrap async ops to ensure status updates kick in."""
        mc = self.migration_controller
        def update_status():
            if mc.migration_ops.is_running:
                current_project = mc.migration_ops.current_project or "Processing..."
                self.ui.status_label.config(text=f"Migrating: {current_project}")
                self.content.after(1000, update_status)
            else:
                self.ui.status_label.config(text="Ready")

        original_to_git = mc.migration_ops.migrate_project_to_git_async
        def wrapped_to_git(project_id, project_name, callback=None):
            result = original_to_git(project_id, project_name, callback)
            if result:
                update_status()
            return result
        mc.migration_ops.migrate_project_to_git_async = wrapped_to_git

        original_git_to_installer = mc.migration_ops.migrate_git_to_installer_async
        def wrapped_git_to_installer(repo_name, project_name, callback=None):
            result = original_git_to_installer(repo_name, project_name, callback)
            if result:
                update_status()
            return result
        mc.migration_ops.migrate_git_to_installer_async = wrapped_git_to_installer

    def _initial_load(self):
        """Load initial data and set initial mode."""
        self.migration_controller.load_installer_data()
        self.migration_controller.load_git_repositories()
        # Default mode: Installer -> SML
        self.migration_controller.set_selection_mode("installer_to_container")
        self.ui.mode_var.set(False)
        self.ui.status_label.config(text="Ready")
