# aggregate/ui_components.py
import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any


class AggregatesTreeview:
    """Treeview widget for aggregates with multi-select support"""
    
    def __init__(self, parent, aggregate_tab):
        self.parent = parent
        self.aggregate_tab = aggregate_tab
        self.aggregates = []  # Store aggregate data
        
        # Frame for treeview and scrollbars
        self.tree_frame = ttk.Frame(parent)
        self.tree_frame.pack(fill="both", expand=True)
        
        # Treeview without checkboxes - use built-in multi-select
        columns = ("id", "name", "type", "status", "rows", "build_time")
        self.tree = ttk.Treeview(
            self.tree_frame, 
            columns=columns, 
            show="headings",
            selectmode="extended"
        )
        
        # Configure columns
        self.tree.column("id", width=120, stretch=False)
        self.tree.column("name", width=200)
        self.tree.column("type", width=100, stretch=False)
        self.tree.column("status", width=80, stretch=False)
        self.tree.column("rows", width=80, stretch=False)
        self.tree.column("build_time", width=100, stretch=False)
        
        # Configure headings
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("status", text="Status")
        self.tree.heading("rows", text="Rows")
        self.tree.heading("build_time", text="Build Time")
        
        # Scrollbars
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        self.tree_frame.columnconfigure(0, weight=1)
        self.tree_frame.rowconfigure(0, weight=1)
        
        # Bind events for selection count update
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_change)
        self.tree.bind("<Control-a>", self._select_all)
        
        # Store item ID to data mapping
        self.item_data_map = {}
    
    def _on_selection_change(self, event):
        """Handle selection changes in treeview"""
        selected_count = len(self.tree.selection())
        if hasattr(self.aggregate_tab, 'update_selection_count'):
            self.aggregate_tab.update_selection_count(selected_count)
    
    def _select_all(self, event):
        """Select all aggregates (Ctrl+A)"""
        items = self.tree.get_children()
        self.tree.selection_set(items)
        selected_count = len(items)
        if hasattr(self.aggregate_tab, 'update_selection_count'):
            self.aggregate_tab.update_selection_count(selected_count)
        return "break"
    
    def add_aggregate(self, agg_data: Dict[str, Any]) -> str:
        """Add an aggregate to the treeview"""
        item_id = self.tree.insert(
            "", "end",
            values=(
                agg_data["id"][:12] + "...",
                agg_data["name"][:30],
                agg_data["type"],
                agg_data["status"],
                agg_data["rows"],
                agg_data["build_time"]
            )
        )
        
        # Store mapping from tree item ID to aggregate data
        self.item_data_map[item_id] = agg_data
        return item_id
    
    def clear(self):
        """Clear all items from treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.item_data_map.clear()
        # Clear selection count
        if hasattr(self.aggregate_tab, 'update_selection_count'):
            self.aggregate_tab.update_selection_count(0)
    
    def get_selected_aggregates(self) -> List[Dict[str, Any]]:
        """Get list of selected aggregates"""
        selected = []
        for item_id in self.tree.selection():
            if item_id in self.item_data_map:
                selected.append(self.item_data_map[item_id])
        return selected
    
    def get_all_aggregates(self) -> List[Dict[str, Any]]:
        """Get list of all aggregates"""
        return list(self.item_data_map.values())
    
    def pack(self, **kwargs):
        """Pack the treeview frame"""
        return self.tree_frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the treeview frame"""
        return self.tree_frame.grid(**kwargs)