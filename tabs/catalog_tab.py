# tabs/catalog_tab.py
import tkinter as tk
from tkinter import ttk
import pandas as pd
from common import append_log

# Import from our existing modules
from cubes.common_selector import CatalogCubeSelector
from catalog.catalog_data_loader import load_catalog_data
from catalog.catalog_tree_manager import populate_catalog_treeviews, handle_tree_selection
from catalog.catalog_display import display_catalog_details

def build_tab(content, log_ref_container):
    # FIXED LAYOUT - Prevent takeover
    content.rowconfigure(0, weight=0)  # Selector - fixed height
    content.rowconfigure(1, weight=1)  # Content area - expands
    content.columnconfigure(0, weight=1, minsize=400)  # Left panel - minimum width
    content.columnconfigure(1, weight=2, minsize=600)  # Right panel - more weight but minimum width
    
    # Data structures
    catalog_data = {}
    current_catalog = ""
    current_cube = ""
    current_catalog_guid = ""  # ADD THIS
    current_cube_guid = ""     # ADD THIS
    # REMOVE: dimensions_df, hierarchies_df, levels_df, measures_df, dimension_mapping, measure_mapping
    # These belong to cube_data_preview_tab.py, not catalog_tab.py

    # Track last selection to prevent multiple triggers
    last_dimensions_selection = None
    last_measures_selection = None

    # --- Core Functions (DEFINE THESE FIRST) ---
    
    def on_catalog_cube_selected(catalog, cube, catalog_guid=None, cube_guid=None):
        """Handle catalog-cube selection from common selector"""
        # FIXED: Only declare variables that exist in outer scope
        nonlocal catalog_data, current_catalog, current_cube, current_catalog_guid, current_cube_guid
        
        current_catalog = catalog
        current_cube = cube
        current_catalog_guid = catalog_guid or ""
        current_cube_guid = cube_guid or ""
        
        append_log(log_ref_container[0], f"Loading catalog data for: {catalog} -> {cube}")
        if catalog_guid or cube_guid:
            append_log(log_ref_container[0], f"GUIDs - Catalog: {catalog_guid}, Cube: {cube_guid}")
        
        # REMOVE: The cube metadata loading part - that belongs to cube_data_preview_tab.py
        # FIXED: Just load catalog data for treeviews
        catalog_data = load_catalog_data(catalog, cube, lambda msg: append_log(log_ref_container[0], msg))
        
        # Populate treeviews
        if catalog_data:
            populate_catalog_treeviews(dimensions_tree, measures_tree, catalog_data, current_cube)
            append_log(log_ref_container[0], "Catalog treeviews populated")
        else:
            append_log(log_ref_container[0], "Failed to load catalog data")

    def on_dimensions_tree_select(event):
        """Handle dimension tree selection - allow parent node selection"""
        nonlocal last_dimensions_selection
        
        # Get current selection
        current_selection = dimensions_tree.selection()
        if not current_selection:
            return
            
        # Check if this is the same selection (to prevent double-trigger)
        if current_selection == last_dimensions_selection:
            return
            
        last_dimensions_selection = current_selection
        
        # Allow ALL node types to trigger display (dimensions, hierarchies, levels)
        # The catalog_tree_manager will handle the appropriate aggregation
        handle_tree_selection(
            event, "dimensions", catalog_data,
            lambda df, title: display_catalog_details(details_tree, df, title),
            lambda msg: append_log(log_ref_container[0], msg)
        )

    def on_measures_tree_select(event):
        """Handle measures tree selection - allow parent node selection"""
        nonlocal last_measures_selection
        
        # Get current selection
        current_selection = measures_tree.selection()
        if not current_selection:
            return
            
        # Check if this is the same selection (to prevent double-trigger)
        if current_selection == last_measures_selection:
            return
            
        last_measures_selection = current_selection
        
        # Allow ALL node types to trigger display (folders, measures)
        # The catalog_tree_manager will handle the appropriate aggregation
        handle_tree_selection(
            event, "measures", catalog_data,
            lambda df, title: display_catalog_details(details_tree, df, title),
            lambda msg: append_log(log_ref_container[0], msg)
        )

    # --- UI Components (CREATE THESE AFTER FUNCTION DEFINITIONS) ---
    
    # Common selector
    selector = CatalogCubeSelector(content, log_ref_container, on_catalog_cube_selected)
    selector.get_selector_widget().grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

    # Left panel with two treeviews - FIXED PROPORTIONS
    left_panel = ttk.Frame(content)
    left_panel.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
    left_panel.columnconfigure(0, weight=1)
    left_panel.rowconfigure(0, weight=0)  # Dimensions label
    left_panel.rowconfigure(1, weight=1)  # Dimensions tree
    left_panel.rowconfigure(2, weight=0)  # Measures label  
    left_panel.rowconfigure(3, weight=1)  # Measures tree

    # Dimensions treeview
    ttk.Label(left_panel, text="Dimensions").grid(row=0, column=0, sticky="w", pady=(0, 5))
    dimensions_tree_frame = ttk.Frame(left_panel)
    dimensions_tree_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
    dimensions_tree_frame.rowconfigure(0, weight=1)
    dimensions_tree_frame.columnconfigure(0, weight=1)

    dimensions_tree = ttk.Treeview(dimensions_tree_frame, show="tree", height=12)
    dimensions_tree_scrollbar = ttk.Scrollbar(dimensions_tree_frame, orient="vertical", command=dimensions_tree.yview)
    dimensions_tree.configure(yscrollcommand=dimensions_tree_scrollbar.set)
    dimensions_tree.grid(row=0, column=0, sticky="nsew")
    dimensions_tree_scrollbar.grid(row=0, column=1, sticky="ns")

    # Measures treeview
    ttk.Label(left_panel, text="Measures").grid(row=2, column=0, sticky="w", pady=(0, 5))
    measures_tree_frame = ttk.Frame(left_panel)
    measures_tree_frame.grid(row=3, column=0, sticky="nsew")
    measures_tree_frame.rowconfigure(0, weight=1)
    measures_tree_frame.columnconfigure(0, weight=1)

    measures_tree = ttk.Treeview(measures_tree_frame, show="tree", height=12)
    measures_tree_scrollbar = ttk.Scrollbar(measures_tree_frame, orient="vertical", command=measures_tree.yview)
    measures_tree.configure(yscrollcommand=measures_tree_scrollbar.set)
    measures_tree.grid(row=0, column=0, sticky="nsew")
    measures_tree_scrollbar.grid(row=0, column=1, sticky="ns")

    # Right panel with details - STRICTLY CONTAINED
    right_panel = ttk.Frame(content)
    right_panel.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
    right_panel.columnconfigure(0, weight=1)
    right_panel.rowconfigure(0, weight=0)  # Label
    right_panel.rowconfigure(1, weight=1)  # Details frame

    # Details label
    details_label = ttk.Label(right_panel, text="Details: Select a dimension or measure")
    details_label.grid(row=0, column=0, sticky="ew", pady=(0, 5))

    # Details frame with FIXED height container
    details_frame = ttk.Frame(right_panel)
    details_frame.grid(row=1, column=0, sticky="nsew")
    details_frame.columnconfigure(0, weight=1)
    details_frame.rowconfigure(0, weight=1)

    # Tree container with scrollbars
    tree_container = ttk.Frame(details_frame)
    tree_container.grid(row=0, column=0, sticky="nsew")
    tree_container.columnconfigure(0, weight=1)
    tree_container.rowconfigure(0, weight=1)

    # Scrollbars
    v_scrollbar = ttk.Scrollbar(tree_container, orient="vertical")
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    h_scrollbar = ttk.Scrollbar(tree_container, orient="horizontal")
    h_scrollbar.grid(row=1, column=0, sticky="ew")

    # Details treeview with STRICT height control
    details_tree = ttk.Treeview(
        tree_container,
        height=18,  # Fixed visible rows
        yscrollcommand=v_scrollbar.set,
        xscrollcommand=h_scrollbar.set,
        show="headings"
    )
    details_tree.grid(row=0, column=0, sticky="nsew")

    v_scrollbar.config(command=details_tree.yview)
    h_scrollbar.config(command=details_tree.xview)

    # --- Event Bindings ---
    dimensions_tree.bind("<<TreeviewSelect>>", on_dimensions_tree_select)
    measures_tree.bind("<<TreeviewSelect>>", on_measures_tree_select)