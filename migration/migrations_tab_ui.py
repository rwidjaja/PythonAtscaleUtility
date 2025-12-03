import tkinter as tk
from tkinter import ttk

class MigrationsTabUI:
    def __init__(self, parent):
        self.parent = parent
        self._build_layout()

    def _build_layout(self):
        content = self.parent
        content.rowconfigure(0, weight=0)   # controls row
        content.rowconfigure(1, weight=1)   # trees row
        content.columnconfigure(0, weight=0)  # left column
        content.columnconfigure(1, weight=1)  # right column

        # -------------------------
        # Left control column
        # -------------------------
        self.left_controls = ttk.Frame(content)
        self.left_controls.grid(row=0, column=0, sticky="nw", padx=8, pady=8)
        self.left_controls.columnconfigure(0, weight=0)
        self.left_controls.columnconfigure(1, weight=0)

        self.mode_var = tk.BooleanVar(value=False)
        self.mode_check = ttk.Checkbutton(
            self.left_controls,
            text="Installer Project to SML",
            variable=self.mode_var
        )
        self.mode_check.grid(row=0, column=0, columnspan=2, sticky="w", padx=(0, 4))

        ttk.Separator(self.left_controls, orient="horizontal").grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(6, 6)
        )

        self.buttons_frame = ttk.Frame(self.left_controls)
        self.buttons_frame.grid(row=2, column=0, columnspan=2, sticky="w")

        # Buttons row 0
        self.migrate_btn = ttk.Button(self.buttons_frame, text="Migrate")
        self.refresh_btn = ttk.Button(self.buttons_frame, text="Refresh")
        self.load_support_zip_btn = ttk.Button(self.buttons_frame, text="Load Support.Zip", width=20)

        self.migrate_btn.grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        self.refresh_btn.grid(row=0, column=1, sticky="w", padx=(0, 6), pady=2)
        self.load_support_zip_btn.grid(row=0, column=2, sticky="w", padx=(0, 6), pady=2)

        # Buttons row 1
        self.cleanup_btn = ttk.Button(self.buttons_frame, text="Clean Workspace")
        self.delete_project_btn = ttk.Button(self.buttons_frame, text="Delete Project")
        self.wizard_btn = ttk.Button(self.buttons_frame, text="Migration Wizard", state="disabled")

        self.cleanup_btn.grid(row=1, column=0, sticky="w", padx=(0, 6), pady=2)
        self.delete_project_btn.grid(row=1, column=1, sticky="w", padx=(0, 6), pady=2)
        self.wizard_btn.grid(row=1, column=2, sticky="w", padx=(0, 6), pady=2)

        self.buttons_frame.columnconfigure(0, weight=0)
        self.buttons_frame.columnconfigure(1, weight=0)
        self.buttons_frame.columnconfigure(2, weight=0)

        self.status_label = ttk.Label(self.left_controls, text="Ready")
        self.status_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        # -------------------------
        # Left listbox
        # -------------------------
        self.left_frame = ttk.Frame(content)
        self.left_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.left_frame.columnconfigure(0, weight=1)
        self.left_frame.rowconfigure(1, weight=1)

        ttk.Label(self.left_frame, text="Installer Source").grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.listbox_left = tk.Listbox(self.left_frame, selectmode=tk.EXTENDED, exportselection=False)
        self.listbox_left.grid(row=1, column=0, sticky="nsew")

        self.left_scroll = ttk.Scrollbar(self.left_frame, orient="vertical", command=self.listbox_left.yview)
        self.left_scroll.grid(row=1, column=1, sticky="ns")
        self.listbox_left.configure(yscrollcommand=self.left_scroll.set)

        # -------------------------
        # Right frame
        # -------------------------
        self.right_frame = ttk.Frame(content)
        self.right_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=8, pady=8)
        self.right_frame.columnconfigure(0, weight=1)
        self.right_frame.rowconfigure(1, weight=1)

        self.header_frame = ttk.Frame(self.right_frame)
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.header_frame.columnconfigure(0, weight=1)
        self.header_frame.columnconfigure(1, weight=0)

        ttk.Label(self.header_frame, text="Git Repository").grid(row=0, column=0, sticky="w")
        self.delete_repo_btn = ttk.Button(self.header_frame, text="Delete Git Repo", width=12)
        self.delete_repo_btn.grid(row=0, column=1, sticky="e", padx=(8, 0))

        self.listbox_right = tk.Listbox(self.right_frame, selectmode=tk.EXTENDED, exportselection=False)
        self.listbox_right.grid(row=1, column=0, sticky="nsew")

        self.right_scroll = ttk.Scrollbar(self.right_frame, orient="vertical", command=self.listbox_right.yview)
        self.right_scroll.grid(row=1, column=1, sticky="ns")
        self.listbox_right.configure(yscrollcommand=self.right_scroll.set)

    def get_widgets(self):
        """Expose widgets for wiring logic"""
        return {
            "mode_var": self.mode_var,
            "mode_check": self.mode_check,
            "migrate_btn": self.migrate_btn,
            "refresh_btn": self.refresh_btn,
            "load_support_zip_btn": self.load_support_zip_btn,
            "cleanup_btn": self.cleanup_btn,
            "delete_project_btn": self.delete_project_btn,
            "wizard_btn": self.wizard_btn,
            "status_label": self.status_label,
            "listbox_left": self.listbox_left,
            "listbox_right": self.listbox_right,
            "delete_repo_btn": self.delete_repo_btn,
        }
