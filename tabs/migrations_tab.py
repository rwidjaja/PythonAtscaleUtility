# [file name]: migrations_tab.py
# [file content begin]
import tkinter as tk
from tkinter import ttk, messagebox
from common import append_log, load_config
from migration.migration_controller import MigrationController
from migration.wizard_controller import WizardController  # Use WizardController directly
from migration.support_zip_processor import SupportZipProcessor
from migration.support_zip_ui import SupportZipUI

def build_tab(content, log_ref_container):
    # Top-level grid: controls on left column, trees on both columns below
    content.rowconfigure(0, weight=0)   # controls row
    content.rowconfigure(1, weight=1)   # trees row
    content.columnconfigure(0, weight=0)  # left column (controls + left tree)
    content.columnconfigure(1, weight=1)  # right column (right tree)

    # Keep a placeholder for migration_controller so callbacks can reference it safely
    migration_controller = None
    migration_wizard = None  # Add wizard reference

    # -------------------------
    # Left control column (stacked vertically)
    # -------------------------
    left_controls = ttk.Frame(content)
    left_controls.grid(row=0, column=0, sticky="nw", padx=8, pady=8)
    # Use grid inside left_controls for precise alignment
    # ensure the control row doesn't expand and push widgets to the right
    left_controls.columnconfigure(0, weight=0)
    left_controls.columnconfigure(1, weight=0)

    # Mode selector as a single Checkbutton (text sits next to the box)
    mode_var = tk.BooleanVar(value=False)

    def toggle_mode():
        # Update label text and log immediately
        if mode_var.get():
            append_log(log_ref_container[0], "Mode set: SML to Installer Project")
            if migration_controller:
                migration_controller.set_selection_mode("container_to_installer")
        else:
            append_log(log_ref_container[0], "Mode set: Installer Project to SML")
            if migration_controller:
                migration_controller.set_selection_mode("installer_to_container")

    mode_check = ttk.Checkbutton(
        left_controls,
        text="Installer Project to SML",
        variable=mode_var,
        command=toggle_mode
    )
    mode_check.grid(row=0, column=0, columnspan=2, sticky="w", padx=(0, 4))

    # Small spacer
    ttk.Separator(left_controls, orient="horizontal").grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 6))

    # Buttons area: stacked vertically, aligned under the checkbox
    buttons_frame = ttk.Frame(left_controls)
    buttons_frame.grid(row=2, column=0, columnspan=2, sticky="w")

    # Use grid for consistent alignment of buttons in three rows
    # Row 0 of buttons
    migrate_btn = ttk.Button(buttons_frame, text="Migrate")
    migrate_btn.grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)

    refresh_btn = ttk.Button(buttons_frame, text="Refresh")
    refresh_btn.grid(row=0, column=1, sticky="w", padx=(0, 6), pady=2)

    # NEW: Add Load Support.Zip button at the top
    load_support_zip_btn = ttk.Button(buttons_frame, text="Load Support.Zip", width=20)
    load_support_zip_btn.grid(row=0, column=2, sticky="w", padx=(0, 6), pady=2)

    # Row 1 of buttons - Add Migration Wizard button here
    cleanup_btn = ttk.Button(buttons_frame, text="Clean Workspace")
    cleanup_btn.grid(row=1, column=0, sticky="w", padx=(0, 6), pady=2)

    delete_project_btn = ttk.Button(buttons_frame, text="Delete Project")
    delete_project_btn.grid(row=1, column=1, sticky="w", padx=(0, 6), pady=2)

    wizard_btn = ttk.Button(buttons_frame, text="Migration Wizard", state="disabled")
    wizard_btn.grid(row=1, column=2, sticky="w", padx=(0, 6), pady=2)

    # Make sure columns in buttons_frame don't expand unexpectedly
    buttons_frame.columnconfigure(0, weight=0)
    buttons_frame.columnconfigure(1, weight=0)
    buttons_frame.columnconfigure(2, weight=0)

    # Status label directly under the buttons, aligned with the checkbox and buttons
    status_label = ttk.Label(left_controls, text="Ready")
    status_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

    # -------------------------
    # Left listbox (Installer Source)
    # -------------------------
    left_frame = ttk.Frame(content)
    left_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
    left_frame.columnconfigure(0, weight=1)
    left_frame.rowconfigure(1, weight=1)

    ttk.Label(left_frame, text="Installer Source").grid(row=0, column=0, sticky="w", pady=(0, 6))

    # Use exportselection=False so selection persists when focus changes
    listbox_left = tk.Listbox(left_frame, selectmode=tk.EXTENDED, exportselection=False)
    listbox_left.grid(row=1, column=0, sticky="nsew")

    left_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=listbox_left.yview)
    left_scroll.grid(row=1, column=1, sticky="ns")
    listbox_left.configure(yscrollcommand=left_scroll.set)

    # --- Sticky toggle selection for left listbox (Installer Source) ---
    def _left_listbox_toggle_selection(event):
        lb = event.widget
        lb.focus_set()

        idx = lb.nearest(event.y)
        if idx is None or idx < 0 or idx >= lb.size():
            return "break"

        # Toggle selection manually
        if lb.selection_includes(idx):
            lb.selection_clear(idx)
        else:
            lb.selection_set(idx)

        lb.activate(idx)
        lb.event_generate("<<ListboxSelect>>")
        return "break"

    # Prevent drag selection from overriding toggle behavior
    def _block_drag(event):
        return "break"

    listbox_left.bind("<Button-1>", _left_listbox_toggle_selection, add=False)
    listbox_left.bind("<B1-Motion>", _block_drag, add=False)

    # -------------------------
    # Right pane: header (label + delete) and Git repository listbox
    # -------------------------
    right_frame = ttk.Frame(content)
    right_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=8, pady=8)
    right_frame.columnconfigure(0, weight=1)
    right_frame.rowconfigure(1, weight=1)

    # Header row: label on the left, compact delete button on the right
    header_frame = ttk.Frame(right_frame)
    header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))
    header_frame.columnconfigure(0, weight=1)
    header_frame.columnconfigure(1, weight=0)

    ttk.Label(header_frame, text="Git Repository").grid(row=0, column=0, sticky="w")

    # compact delete button placed next to the label (above the list)
    delete_repo_btn = ttk.Button(header_frame, text="Delete Git Repo", width=12)
    delete_repo_btn.grid(row=0, column=1, sticky="e", padx=(8, 0))

    # The listbox itself
    listbox_right = tk.Listbox(right_frame, selectmode=tk.EXTENDED, exportselection=False)
    listbox_right.grid(row=1, column=0, sticky="nsew")

    right_scroll = ttk.Scrollbar(right_frame, orient="vertical", command=listbox_right.yview)
    right_scroll.grid(row=1, column=1, sticky="ns")
    listbox_right.configure(yscrollcommand=right_scroll.set)

    # Sticky toggle for right listbox
    def _right_listbox_toggle_selection(event):
        lb = event.widget
        lb.focus_set()
        idx = lb.nearest(event.y)
        if idx is None or idx < 0 or idx >= lb.size():
            return "break"
        if lb.selection_includes(idx):
            lb.selection_clear(idx)
        else:
            lb.selection_set(idx)
        lb.event_generate('<<ListboxSelect>>')
        return "break"

    listbox_right.bind("<Button-1>", _right_listbox_toggle_selection, add=False)
    listbox_right.bind("<B1-Motion>", _block_drag, add=False)

    # -------------------------
    # Initialize migration controller (after widgets exist)
    # -------------------------
    config = load_config()
    migration_controller = MigrationController(
        config=config,
        log_ref_container=log_ref_container,
        left_listbox=listbox_left,
        right_listbox=listbox_right,
        mode_var=mode_var
    )

    # Initialize migration wizard with the new modular structure
    migration_wizard = WizardController(content, migration_controller, log_ref_container)
    

    # Set migration operations after controller is created
    from migration.migration_operations import MigrationOperations
    migration_ops = MigrationOperations(config, log_ref_container)
    migration_controller.set_migration_ops(migration_ops)

    # Wire up button commands now that migration_controller exists
    def update_status():
        if migration_controller.migration_ops.is_running:
            current_project = migration_controller.migration_ops.current_project or 'Processing...'
            status_text = f"Migrating: {current_project}"
            status_label.config(text=status_text)
            content.after(1000, update_status)
        else:
            status_label.config(text="Ready")

    def start_migration_with_status():
        migration_controller.start_migration()
        update_status()

    def update_wizard_button_state(*args):
        """Update wizard button state based on selection - called on selection changes"""
        selected_count = migration_controller.get_selected_project_count()
        if selected_count > 1:
            wizard_btn.config(state="normal")
        else:
            wizard_btn.config(state="disabled")

    migrate_btn.configure(command=start_migration_with_status)
    # wire delete button in right header to controller
    delete_repo_btn.configure(command=lambda: migration_controller.delete_selected_git_repo())
    refresh_btn.configure(command=lambda: migration_controller.refresh_all())
    cleanup_btn.configure(command=lambda: migration_controller.cleanup_workspace())
    delete_project_btn.configure(command=lambda: migration_controller.delete_selected_project())
    wizard_btn.configure(command=lambda: migration_wizard.open_wizard())  # Updated to use new wizard

    # Define the load_support_zip function
    def load_support_zip():
        """Handle Load Support.Zip button click"""
        # Disable button while processing
        load_support_zip_btn.config(state="disabled")
        content.update()
        
        try:
            # Initialize support zip processor
            support_processor = SupportZipProcessor(
                config, 
                log_ref_container, 
                migration_controller.migration_ops
            )
            
            # Open file dialog
            zip_path = support_processor.open_support_zip()
            if not zip_path:
                load_support_zip_btn.config(state="normal")
                return
            
            # Show processing message
            processing_msg = tk.Toplevel(content)
            processing_msg.title("Processing")
            processing_msg.geometry("300x100")
            processing_msg.transient(content)
            processing_msg.grab_set()
            
            ttk.Label(processing_msg, text="Processing support zip file...\nPlease wait.").pack(pady=20)
            processing_msg.update()
            
            # Process the zip file directly through Java service
            projects = support_processor.process_support_zip(zip_path)
            
            # Close processing message
            processing_msg.destroy()
            
            if not projects:
                messagebox.showerror("Error", "No valid projects found in support zip")
                load_support_zip_btn.config(state="normal")
                return
            
            # Create and show project selection UI
            support_ui = SupportZipUI(
                support_processor,
                migration_wizard,
                migration_controller,
                log_ref_container
            )
            
            selection_window = support_ui.create_selection_window(content, projects)
            
            # Re-enable button when window closes
            def on_window_close():
                load_support_zip_btn.config(state="normal")
                # Clean up workspace after support zip operations
                migration_controller.cleanup_workspace()
                selection_window.destroy()
            
            selection_window.protocol("WM_DELETE_WINDOW", on_window_close)
            
            # Also re-enable button when window is destroyed
            def on_window_destroy(event):
                if event.widget == selection_window:
                    load_support_zip_btn.config(state="normal")
            
            selection_window.bind("<Destroy>", on_window_destroy)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process support zip: {str(e)}")
            load_support_zip_btn.config(state="normal")

    # Connect the button to the function
    load_support_zip_btn.configure(command=load_support_zip)

    # Hook selection events to update wizard button state
    def on_listbox_selection(event):
        update_wizard_button_state()

    listbox_left.bind('<<ListboxSelect>>', on_listbox_selection)
    listbox_right.bind('<<ListboxSelect>>', on_listbox_selection)

    # Hook async wrappers to trigger status updates when operations start
    original_migrate_async = migration_controller.migration_ops.migrate_project_to_git_async
    def wrapped_migrate_async(project_id, project_name, callback=None):
        result = original_migrate_async(project_id, project_name, callback)
        if result:
            update_status()
        return result
    migration_controller.migration_ops.migrate_project_to_git_async = wrapped_migrate_async

    original_migrate_git_async = migration_controller.migration_ops.migrate_git_to_installer_async
    def wrapped_migrate_git_async(repo_name, project_name, callback=None):
        result = original_migrate_git_async(repo_name, project_name, callback)
        if result:
            update_status()
        return result
    migration_controller.migration_ops.migrate_git_to_installer_async = wrapped_migrate_git_async

    # Load initial data and set initial mode
    migration_controller.load_installer_data()
    migration_controller.load_git_repositories()
    migration_controller.set_selection_mode("installer_to_container")
# [file content end]