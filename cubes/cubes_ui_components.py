# cubes/tab_ui_components.py
import tkinter as tk
from tkinter import ttk
from cubes.common_selector import CatalogCubeSelector

def create_ui_components(content, log_ref_container, on_catalog_cube_selected, on_sql_change_callback=None):
    """Create and return all UI widgets"""
    
    # Data structures - will be populated by caller
    components = {
        'dimensions_listbox': None,
        'measures_listbox': None,
        'result_tree': None,
        'sql_dialect_var': tk.BooleanVar(value=False),
        'selector': None,
        'execute_btn': None
    }
    
    # Layout: selector row on top, then 2-left + 1-right frames
    content.rowconfigure(0, weight=0)  # Selector
    content.rowconfigure(1, weight=0)  # SQL Checkbox
    content.rowconfigure(2, weight=1)  # Content area
    content.rowconfigure(3, weight=0)  # Execute button
    content.columnconfigure(0, weight=1)
    content.columnconfigure(1, weight=3)
    
    # Common selector
    selector = CatalogCubeSelector(content, log_ref_container, on_catalog_cube_selected)
    selector.get_selector_widget().grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
    components['selector'] = selector
    
    # SQL Dialect Checkbox
    sql_checkbox = ttk.Checkbutton(
        content, 
        text="SQL Dialect", 
        variable=components['sql_dialect_var'],
        command=on_sql_change_callback  # Set the callback
    )
    sql_checkbox.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=2)
    
    # Left frame
    left_frame = ttk.Frame(content)
    left_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
    left_frame.rowconfigure(0, weight=0)
    left_frame.rowconfigure(1, weight=1)
    left_frame.rowconfigure(2, weight=0)
    left_frame.rowconfigure(3, weight=1)
    left_frame.columnconfigure(0, weight=1)
    
    # Dimensions listbox
    ttk.Label(left_frame, text="Dimensions & Hierarchies (Multiple Select):").grid(row=0, column=0, sticky="w", padx=5)
    dimensions_listbox = tk.Listbox(left_frame, selectmode="multiple", exportselection=False)
    dimensions_listbox.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0,10))
    dim_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=dimensions_listbox.yview)
    dim_scrollbar.grid(row=1, column=1, sticky="ns")
    dimensions_listbox.configure(yscrollcommand=dim_scrollbar.set)
    components['dimensions_listbox'] = dimensions_listbox
    
    # Measures listbox  
    ttk.Label(left_frame, text="Measures (Multiple Select):").grid(row=2, column=0, sticky="w", padx=5)
    measures_listbox = tk.Listbox(left_frame, selectmode="multiple", exportselection=False)
    measures_listbox.grid(row=3, column=0, sticky="nsew", padx=5, pady=(0,5))
    measure_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=measures_listbox.yview)
    measure_scrollbar.grid(row=3, column=1, sticky="ns")
    measures_listbox.configure(yscrollcommand=measure_scrollbar.set)
    components['measures_listbox'] = measures_listbox
    
    # Right frame with Treeview
    right_frame = ttk.Frame(content)
    right_frame.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)
    right_frame.rowconfigure(0, weight=1)
    right_frame.columnconfigure(0, weight=1)
    
    tree_frame = ttk.Frame(right_frame)
    tree_frame.grid(row=0, column=0, sticky="nsew")
    tree_frame.rowconfigure(0, weight=1)
    tree_frame.columnconfigure(0, weight=1)
    
    v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")
    h_scrollbar.grid(row=1, column=0, sticky="ew")
    
    result_tree = ttk.Treeview(tree_frame, yscrollcommand=v_scrollbar.set, 
                              xscrollcommand=h_scrollbar.set, show="tree headings")
    result_tree.grid(row=0, column=0, sticky="nsew")
    
    v_scrollbar.config(command=result_tree.yview)
    h_scrollbar.config(command=result_tree.xview)
    components['result_tree'] = result_tree
    
    # Execute button
    execute_btn = ttk.Button(content, text="Execute Query", command=None)  # Will be set by caller
    execute_btn.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
    components['execute_btn'] = execute_btn
    
    return components