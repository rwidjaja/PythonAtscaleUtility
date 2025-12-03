# queries/query_input_ui.py
import tkinter as tk
from tkinter import ttk, scrolledtext

class QueryInputUI:
    def __init__(self, parent, on_query_type_change=None, on_execute=None, on_show_history=None):
        self.parent = parent
        self.on_query_type_change = on_query_type_change
        self.on_execute = on_execute
        self.on_show_history = on_show_history

        self.query_type_var = tk.StringVar(value="MDX")
        self.use_agg_var = tk.BooleanVar(value=True)
        self.use_cache_var = tk.BooleanVar(value=True)

        self.query_text = None
        self.main_frame = None
        self.history_btn = None

        self.create_widgets()
        self.setup_bindings()

    def create_widgets(self):
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)

        # Options row
        options_frame = ttk.Frame(self.main_frame)
        options_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        ttk.Label(options_frame, text="Query Type:").grid(row=0, column=0, padx=(0, 5))
        self.mdx_radio = ttk.Radiobutton(options_frame, text="MDX", variable=self.query_type_var, value="MDX")
        self.sql_radio = ttk.Radiobutton(options_frame, text="SQL", variable=self.query_type_var, value="SQL")
        self.mdx_radio.grid(row=0, column=1, padx=(0, 10))
        self.sql_radio.grid(row=0, column=2, padx=(0, 20))

        ttk.Separator(options_frame, orient="vertical").grid(row=0, column=3, padx=10, sticky="ns")
        self.use_agg_checkbox = ttk.Checkbutton(options_frame, text="Use Agg", variable=self.use_agg_var)
        self.use_cache_checkbox = ttk.Checkbutton(options_frame, text="Use Cache", variable=self.use_cache_var)
        self.use_agg_checkbox.grid(row=0, column=4, padx=(0, 10))
        self.use_cache_checkbox.grid(row=0, column=5)

        # Query text area
        ttk.Label(self.main_frame, text="Query:").grid(row=1, column=0, sticky="w", pady=(0, 5))
        text_frame = ttk.Frame(self.main_frame)
        text_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 5))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self.query_text = tk.Text(text_frame, wrap=tk.WORD, height=15)
        self.query_text.grid(row=0, column=0, sticky="nsew")
        text_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.query_text.yview)
        text_scrollbar.grid(row=0, column=1, sticky="ns")
        self.query_text.configure(yscrollcommand=text_scrollbar.set)

        # Buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=3, column=0, pady=10)
        ttk.Button(button_frame, text="Execute Query", command=self.on_execute).pack(side="left", padx=(0, 10))

        self.history_btn = ttk.Button(button_frame, text="Query History", command=self.on_show_history)
        self.history_btn.pack(side="left")

    def setup_bindings(self):
        if self.on_query_type_change:
            self.mdx_radio.configure(command=self.on_query_type_change)
            self.sql_radio.configure(command=self.on_query_type_change)

    def set_on_show_history(self, callback):
        """Wire the history button to a callback"""
        self.on_show_history = callback
        if self.history_btn:
            self.history_btn.configure(command=callback)

    def get_widget(self):
        return self.main_frame
