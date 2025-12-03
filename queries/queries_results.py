# tabs/queries_results.py
import tkinter as tk
from tkinter import ttk
import pandas as pd

class QueryResults:
    def __init__(self, parent):
        self.parent = parent
        self.create_widgets()
    
    def create_widgets(self):
        """Create results display widgets using grid geometry manager"""
        # Main frame
        self.main_frame = ttk.Frame(self.parent)
        
        # Configure grid weights for main frame
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)  # Tree container row
        
        # Results label
        ttk.Label(self.main_frame, text="Results:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # Treeview with scrollbars
        tree_container = ttk.Frame(self.main_frame)
        tree_container.grid(row=1, column=0, sticky="nsew", pady=(0, 5))
        
        # Configure tree container grid
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)
        
        # Scrollbars
        self.v_scrollbar = ttk.Scrollbar(tree_container, orient="vertical")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.h_scrollbar = ttk.Scrollbar(tree_container, orient="horizontal")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Results treeview
        self.results_tree = ttk.Treeview(
            tree_container,
            height=20,
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set,
            show="headings"
        )
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        
        # Configure scrollbars
        self.v_scrollbar.config(command=self.results_tree.yview)
        self.h_scrollbar.config(command=self.results_tree.xview)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.main_frame, textvariable=self.status_var)
        self.status_label.grid(row=2, column=0, sticky="w", pady=(5, 0))
    
    def display_results(self, df):
        """Display DataFrame in the results treeview"""
        # Clear existing data
        self.results_tree.delete(*self.results_tree.get_children())
        
        if df is None or df.empty:
            self.status_var.set("No results to display")
            return False
        
        # Configure columns
        columns = list(df.columns)
        self.results_tree["columns"] = columns
        
        # Configure headings
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=120, minwidth=80, stretch=False)
        
        # Insert data (limit to reasonable number)
        max_display_rows = 1000
        display_df = df.head(max_display_rows) if len(df) > max_display_rows else df
        
        for _, row in display_df.iterrows():
            values = [str(row[col]) if pd.notna(row[col]) else "" for col in columns]
            self.results_tree.insert("", "end", values=values)
        
        # Update status
        if len(df) > max_display_rows:
            self.status_var.set(f"Showing first {max_display_rows} of {len(df)} rows")
        else:
            self.status_var.set(f"Displaying {len(df)} rows")
        
        return len(df) > max_display_rows  # Return whether results were truncated
    
    def clear_results(self):
        """Clear the results treeview"""
        self.results_tree.delete(*self.results_tree.get_children())
        self.status_var.set("Results cleared")
    
    def set_status(self, message):
        """Set status message"""
        self.status_var.set(message)
    
    def get_widget(self):
        """Get the main widget"""
        return self.main_frame