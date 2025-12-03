# tabs/cube_data_preview_tab.py
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from common import append_log

# Import from our new modules
from .common_selector import CatalogCubeSelector  # NEW
from .cube_data_queries import run_xmla_query, build_xmla_request
from .cube_data_parsers import parse_xmla_result_to_dataframe
from .cube_data_metadata import load_cube_metadata, populate_listboxes
from .cube_data_drilldown import (
    get_hierarchy_levels, get_current_level_info, get_next_level_info,
    drill_down_selection, drill_up_selection
)

# Try different import approaches for the SQL module
try:
    from .cube_data_sql import execute_sql_query
except ImportError as e:
    print(f"Warning: Could not import execute_sql_query: {e}")
    # Define a fallback function
    def execute_sql_query(*args, **kwargs):
        print("SQL functionality not available")
        return pd.DataFrame()

def build_tab(content, log_ref_container):
    # Layout: selector row on top, then 2-left + 1-right frames
    content.rowconfigure(0, weight=0)  # Selector
    content.rowconfigure(1, weight=0)  # SQL Checkbox
    content.rowconfigure(2, weight=1)  # Content area
    content.rowconfigure(3, weight=0)  # Execute button
    content.columnconfigure(0, weight=1)
    content.columnconfigure(1, weight=3)
    
    # Data structures
    dimensions_df = None
    hierarchies_df = None  
    levels_df = None
    measures_df = None
    dimension_mapping = {}  # index -> (type, unique_name)
    measure_mapping = {}    # index -> unique_name
    query_history = []
    current_query_index = -1
    current_hierarchies = []
    current_measures = []
    current_catalog = ""
    current_cube = ""
    current_catalog_guid = ""  # ADD THIS
    current_cube_guid = ""     # ADD THIS
    current_drill_down_data = {}
    
    # SQL Dialect variable
    sql_dialect_var = tk.BooleanVar(value=False)

    # --- Core Functions (DEFINE THESE FIRST) ---
    
    def on_catalog_cube_selected(catalog, cube, catalog_guid=None, cube_guid=None):
        """Handle catalog-cube selection from common selector"""
        nonlocal dimensions_df, hierarchies_df, levels_df, measures_df, dimension_mapping, measure_mapping
        nonlocal current_catalog, current_cube, current_catalog_guid, current_cube_guid  # Now these exist
        
        current_catalog = catalog
        current_cube = cube
        current_catalog_guid = catalog_guid or ""
        current_cube_guid = cube_guid or ""
        
        append_log(log_ref_container[0], f"Loading metadata for: {catalog} -> {cube}")
        if catalog_guid or cube_guid:
            append_log(log_ref_container[0], f"GUIDs - Catalog: {catalog_guid}, Cube: {cube_guid}")
        
        # Load cube metadata using our imported function
        result = load_cube_metadata(catalog, cube, lambda msg: append_log(log_ref_container[0], msg))
        
        if result[0] is not None:
            dimensions_df, hierarchies_df, levels_df, measures_df, dimension_mapping, measure_mapping = result
            # Populate listboxes using our imported function
            populate_listboxes(dimensions_listbox, measures_listbox, dimensions_df, hierarchies_df, levels_df, measures_df, dimension_mapping, measure_mapping)
        
    # Common selector
    selector = CatalogCubeSelector(content, log_ref_container, on_catalog_cube_selected)
    selector.get_selector_widget().grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

    # SQL Dialect Checkbox
    sql_checkbox = ttk.Checkbutton(
        content, 
        text="SQL Dialect", 
        variable=sql_dialect_var,
        command=lambda: on_sql_dialect_change()
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

    # Measures listbox  
    ttk.Label(left_frame, text="Measures (Multiple Select):").grid(row=2, column=0, sticky="w", padx=5)
    measures_listbox = tk.Listbox(left_frame, selectmode="multiple", exportselection=False)
    measures_listbox.grid(row=3, column=0, sticky="nsew", padx=5, pady=(0,5))
    measure_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=measures_listbox.yview)
    measure_scrollbar.grid(row=3, column=1, sticky="ns")
    measures_listbox.configure(yscrollcommand=measure_scrollbar.set)
    
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

    result_tree = ttk.Treeview(tree_frame, yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set, show="tree headings")
    result_tree.grid(row=0, column=0, sticky="nsew")

    v_scrollbar.config(command=result_tree.yview)
    h_scrollbar.config(command=result_tree.xview)

    # --- Helper Functions ---
    def on_sql_dialect_change():
        """Handle SQL dialect checkbox change"""
        if sql_dialect_var.get():
            append_log(log_ref_container[0], "SQL Dialect enabled - drill-down disabled")
        else:
            append_log(log_ref_container[0], "MDX Dialect enabled - drill-down available")

    def show_selection_details():
        """Show details of the selected row"""
        selected_items = result_tree.selection()
        if not selected_items:
            append_log(log_ref_container[0], "Please select a row to show details")
            return
        
        item = selected_items[0]
        
        # Get row data from our storage dictionary
        if not hasattr(display_dataframe_in_treeview, "item_data") or item not in display_dataframe_in_treeview.item_data:
            append_log(log_ref_container[0], "No data available for selected row")
            return
        
        row_data = display_dataframe_in_treeview.item_data[item]
        
        if row_data:
            details = f"Selected Row Details:\n"
            details += f"Row Label: {row_data['display_text']}\n"
            details += f"Row Number: {row_data['row_number']}\n"
            details += "Values:\n"
            for key, value in row_data['values'].items():
                details += f"  {key}: {value}\n"
            
            append_log(log_ref_container[0], details)

    def drill_down_selection_wrapper():
        """Wrapper for drill-down that checks if SQL is enabled"""
        if sql_dialect_var.get():
            append_log(log_ref_container[0], "Drill-down not available in SQL dialect")
            return
            
        # Declare nonlocal variables FIRST
        nonlocal current_query_index, query_history, current_hierarchies, current_measures, current_catalog, current_cube
        # If needed for drill_down_selection function, add:
        # nonlocal current_catalog_guid, current_cube_guid
        
        # Wrapper to call the drill_down_selection from drilldown module
        result = drill_down_selection(
            result_tree, query_history, current_query_index, levels_df,
            current_hierarchies, current_measures, current_catalog, current_cube,
            lambda msg: append_log(log_ref_container[0], msg)
        )
        
        if result[0] is not None:
            df, current_hierarchies, current_measures, current_catalog, current_cube, query_history, current_query_index = result
            display_dataframe_in_treeview(df)

    def drill_up_selection_wrapper():
        """Wrapper for drill-up that checks if SQL is enabled"""
        if sql_dialect_var.get():
            append_log(log_ref_container[0], "Drill-up not available in SQL dialect")
            return
            
        # Declare nonlocal variables FIRST  
        nonlocal current_query_index, query_history, current_hierarchies, current_measures, current_catalog, current_cube
        # If needed for drill_up_selection function, add:
        # nonlocal current_catalog_guid, current_cube_guid
        
        # Wrapper to call the drill_up_selection from drilldown module
        result = drill_up_selection(
            query_history, current_query_index,
            current_hierarchies, current_measures, current_catalog, current_cube,
            lambda msg: append_log(log_ref_container[0], msg)
        )
        
        if result[0] is not None:
            df, current_hierarchies, current_measures, current_catalog, current_cube, query_history, current_query_index = result
            display_dataframe_in_treeview(df)

    # --- Context Menus ---
    result_context_menu = tk.Menu(result_tree, tearoff=0)
    result_context_menu.add_command(label="Drill Down", command=drill_down_selection_wrapper)
    result_context_menu.add_command(label="Drill Up", command=drill_up_selection_wrapper)
    result_context_menu.add_separator()
    result_context_menu.add_command(label="Show Details", command=show_selection_details)

    def show_result_context_menu(event):
        item = result_tree.identify_row(event.y)
        if item:
            result_tree.selection_set(item)
            try:
                result_context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                result_context_menu.grab_release()

    # --- Core Functions ---
    def on_listbox_click(event):
        widget = event.widget
        index = widget.nearest(event.y)

        if index < 0:
            return

        # Determine mapping based on listbox
        if widget == dimensions_listbox:
            mapping = dimension_mapping.get(index)
        else:
            mapping = measure_mapping.get(index)

        # If header → clear selection and stop selection only
        if mapping is None:
            widget.selection_clear(0, tk.END)
            return "break"   # prevent selecting headers, allow other events

        # If real item → do not return break so double/right click still fires
        return

    def display_dataframe_in_treeview(df, is_sql=False):
        """Display DataFrame in Treeview widget with Excel-like grid and proper data storage"""
        # Clear existing data
        result_tree.delete(*result_tree.get_children())
        
        # Remove duplicate rows based on index and all column values
        original_shape = df.shape
        df = df[~df.index.duplicated(keep='first')]
        
        # Also check for duplicate data in all columns
        df = df.drop_duplicates()
        
        if original_shape != df.shape:
            append_log(log_ref_container[0], f"Removed duplicates: {original_shape} -> {df.shape}")
        
        # Clear any previous item data
        if hasattr(display_dataframe_in_treeview, "item_data"):
            display_dataframe_in_treeview.item_data.clear()
        else:
            display_dataframe_in_treeview.item_data = {}
        
        # Configure columns differently for SQL vs MDX
        columns = list(df.columns)
        
        if is_sql:
            # For SQL: Use regular columns without the tree column
            result_tree["columns"] = columns
            result_tree["show"] = "headings"  # Hide the tree column completely
            
            # Configure headings for all columns
            for col in columns:
                result_tree.heading(col, text=col)
                result_tree.column(col, width=120, minwidth=80)
        else:
            # For MDX: Use tree column + regular columns
            result_tree["columns"] = columns
            result_tree["show"] = "tree headings"  # Show tree column
            
            # Configure tree column for row labels
            result_tree.heading("#0", text="Row Labels")
            result_tree.column("#0", width=120, minwidth=80)
            
            # Configure headings for data columns
            for col in columns:
                result_tree.heading(col, text=col)
                result_tree.column(col, width=120, minwidth=80)
            
        # Insert data
        for i, (index, row) in enumerate(df.iterrows()):
            values = [str(row[col]) if pd.notna(row[col]) else "" for col in columns]
            
            if is_sql:
                # For SQL: insert without tree column text
                item = result_tree.insert("", "end", text="", values=values)
            else:
                # For MDX: use index as tree column text
                item = result_tree.insert("", "end", text=str(index), values=values)
            
            # Store drill-down data
            row_data = {
                'index': index,
                'display_text': str(index),
                'values': dict(row),
                'row_number': i,
                'item_id': item,
                'member_caption': str(index)
            }
            
            display_dataframe_in_treeview.item_data[item] = row_data
            
            # Also store in our global drill-down data
            current_drill_down_data['rows'] = current_drill_down_data.get('rows', [])
            current_drill_down_data['rows'].append(row_data)

        # Update the global drill-down data with current context
        current_drill_down_data.update({
            'hierarchies': current_hierarchies,
            'measures': current_measures,
            'catalog': current_catalog,
            'cube': current_cube
        })

    def build_initial_mdx(dimension_items, measures_set, cube):
        """Build initial MDX query showing first level members"""
        if len(dimension_items) == 1:
            hierarchy_name = dimension_items[0].replace('.Members', '')
            # Get the first non-All level
            levels = get_hierarchy_levels(hierarchy_name, levels_df)
            if levels:
                first_level = levels[0]
                # Show members of the first level directly
                return f"""SELECT
        {{ {measures_set} }} ON COLUMNS,
        NON EMPTY {{ {first_level['LEVEL_UNIQUE_NAME']}.Members }} ON ROWS
        FROM [{cube}]"""
            else:
                return f"""SELECT
        {{ {measures_set} }} ON COLUMNS,
        NON EMPTY {{ {hierarchy_name}.Members }} ON ROWS
        FROM [{cube}]"""
        else:
            # For multiple hierarchies
            crossjoin_items = []
            for item in dimension_items:
                hierarchy_name = item.replace('.Members', '')
                levels = get_hierarchy_levels(hierarchy_name, levels_df)
                if levels:
                    first_level = levels[0]
                    crossjoin_items.append(f"{{ {first_level['LEVEL_UNIQUE_NAME']}.Members }}")
                else:
                    crossjoin_items.append(f"{{ {hierarchy_name}.Members }}")
            
            if len(crossjoin_items) == 2:
                crossjoin_result = f"CrossJoin({crossjoin_items[0]}, {crossjoin_items[1]})"
            else:
                crossjoin_result = f"CrossJoin({crossjoin_items[0]}, {crossjoin_items[1]})"
                for i in range(2, len(crossjoin_items)):
                    crossjoin_result = f"CrossJoin({crossjoin_result}, {crossjoin_items[i]})"
            
            return f"""SELECT
        {{ {measures_set} }} ON COLUMNS,
        NON EMPTY {crossjoin_result} ON ROWS
        FROM [{cube}]"""

    def execute_query():
        # Declare nonlocal variables FIRST
        nonlocal current_hierarchies, current_measures, current_catalog, current_cube, query_history, current_query_index
        nonlocal current_catalog_guid, current_cube_guid  # Add these
        
        # Get selected dimensions and measures
        selected_dim_indices = dimensions_listbox.curselection()
        selected_measure_indices = measures_listbox.curselection()
        
        if not selected_dim_indices or not selected_measure_indices:
            append_log(log_ref_container[0], "Please select at least one dimension and one measure")
            return
        
        try:
            # FIX: Unpack all 4 values correctly
            selection_result = selector.get_current_selection()
            
            # Handle unpacking - selector.get_current_selection() returns 4 values
            if len(selection_result) == 4:
                catalog, cube, catalog_guid, cube_guid = selection_result
            else:
                # Fallback for backward compatibility
                catalog, cube = selection_result[:2]
                catalog_guid, cube_guid = "", ""
            
            # UPDATE: Update all current variables
            current_catalog = catalog
            current_cube = cube
            current_catalog_guid = catalog_guid
            current_cube_guid = cube_guid
            
            if not catalog or not cube:
                append_log(log_ref_container[0], "Please select a catalog and cube first")
                return
            
            # Get the actual unique names from our mapping for ALL selected items
            dimension_items = []
            for idx in selected_dim_indices:
                mapping = dimension_mapping.get(idx)
                if mapping:
                    item_type, unique_name = mapping
                    # For SQL, we can use both hierarchies and levels directly
                    # For MDX, we need to handle them differently
                    dimension_items.append(unique_name)
            
            measure_unique_names = []
            for idx in selected_measure_indices:
                unique_name = measure_mapping.get(idx)
                if unique_name:
                    measure_unique_names.append(unique_name)
            
            if not dimension_items or not measure_unique_names:
                append_log(log_ref_container[0], "Error: Could not find unique names for selection")
                return
            
            # Store current context
            current_hierarchies = dimension_items
            current_measures = measure_unique_names
            current_catalog = catalog
            current_cube = cube
            
            if sql_dialect_var.get():
                # Execute SQL query
                append_log(log_ref_container[0], "Executing SQL query...")
                df = execute_sql_query(
                    dimension_items, 
                    measure_unique_names, 
                    catalog, 
                    cube,
                    lambda msg: append_log(log_ref_container[0], msg),
                    use_agg=True,  # Default value
                    use_cache=True  # Default value
                )           
                if not df.empty:
                    # Limit to first 1000 rows
                    if len(df) > 1000:
                        df = df.head(1000)
                        append_log(log_ref_container[0], f"Result truncated to first 1000 rows (original: {len(df)} rows)")
                    
                    # Display results in Treeview - pass is_sql=True
                    display_dataframe_in_treeview(df, is_sql=True)
                    
                    # Clear MDX history for SQL queries
                    query_history = []
                    current_query_index = -1
                    
            else:
                # Execute MDX query (existing logic)
                measures_set = ", ".join(measure_unique_names)
                MDX_QUERY = build_initial_mdx(dimension_items, measures_set, cube)

                # Store the hierarchies for drill-down context
                level_referenced_hierarchies = []
                for item in dimension_items:
                    hierarchy_name = item.replace('.Members', '')
                    # Get the first non-All level to track current level
                    levels = get_hierarchy_levels(hierarchy_name, levels_df)
                    if levels:
                        first_level = levels[0]
                        level_referenced_hierarchies.append(f"{first_level['LEVEL_UNIQUE_NAME']}.Members")
                    else:
                        level_referenced_hierarchies.append(item)

                current_mdx = MDX_QUERY
                # Clear history and add this as first query
                query_history = [{
                    'mdx': MDX_QUERY,
                    'hierarchies': level_referenced_hierarchies,
                    'measures': measure_unique_names.copy(),
                    'catalog': catalog,
                    'cube': cube,
                    'description': "Initial query"
                }]
                current_query_index = 0
                
                # Use the build_xmla_request function
                XMLA_REQUEST = build_xmla_request(MDX_QUERY, catalog, cube, use_agg=True, use_cache=True)
                
                # Log the MDX to bottom window
                append_log(log_ref_container[0], f"Generated MDX:\n{MDX_QUERY}")
                append_log(log_ref_container[0], "Executing MDX query...")
                
                # Execute query
                response = run_xmla_query(XMLA_REQUEST)
                
                # Parse the XMLA response into a DataFrame
                df = parse_xmla_result_to_dataframe(response)
                
                if not df.empty:
                    # Limit to first 1000 rows
                    if len(df) > 1000:
                        df = df.head(1000)
                        append_log(log_ref_container[0], f"Result truncated to first 1000 rows (original: {len(df)} rows)")
                    
                    # Display results in Treeview - pass is_sql=False (default)
                    display_dataframe_in_treeview(df, is_sql=False)
            
        except Exception as e:
            append_log(log_ref_container[0], f"Query execution error: {e}")

    def show_selected_message():
        value = get_selected_dimension()
        if value:
            messagebox.showinfo("Selected Dimension", value)

    def drill_down(value):
        if value is None:
            return

        item_type, unique_name = value
        append_log(log_ref_container[0], f"Drilling down on: {item_type}, {unique_name}")

        # TODO: Add your level expansion logic here
        
    def on_double_click(event):
        widget = event.widget
        index = widget.nearest(event.y)

        if index >= 0:
            mapping_value = dimension_mapping.get(index)
            if mapping_value is not None:  # skip headers
                drill_down(mapping_value)

    def on_right_click(event):
        widget = event.widget
        index = widget.nearest(event.y)

        if index < 0:
            return "break"

        if index not in widget.curselection():
            widget.selection_clear(0, tk.END)
            widget.selection_set(index)

        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

        return "break"

    def get_selected_dimension():
        selection = dimensions_listbox.curselection()
        if not selection:
            return None
        
        index = selection[0]
        mapping_value = dimension_mapping.get(index)

        # Skip non-selectable header rows
        if mapping_value is None:
            return None

        # Return (type, unique_name)
        return mapping_value

    def drill_down_listbox_item():
        """Drill down on a listbox item (different from result tree drill down)"""
        value = get_selected_dimension()
        if value is None:
            return

        item_type, unique_name = value
        append_log(log_ref_container[0], f"Listbox drill down on: {item_type}, {unique_name}")
        # TODO: Add your listbox level expansion logic here

    # Create context menu for listboxes (separate from result tree)
    listbox_context_menu = tk.Menu(content, tearoff=0)
    listbox_context_menu.add_command(label="Drill Down", command=drill_down_listbox_item)
    listbox_context_menu.add_command(label="Show Selected", command=lambda: print(get_selected_dimension()))

    # --- Event Bindings ---
    dimensions_listbox.bind("<Button-1>", on_listbox_click)
    measures_listbox.bind("<Button-1>", on_listbox_click)
    
    def on_listbox_select(event):
        # This prevents the default selection behavior from interfering
        pass

    dimensions_listbox.bind('<<ListboxSelect>>', on_listbox_select)
    measures_listbox.bind('<<ListboxSelect>>', on_listbox_select)
    
    dimensions_listbox.bind("<Double-Button-1>", on_double_click)
    dimensions_listbox.bind("<Button-3>", lambda e: on_right_click(e))

    measures_listbox.bind("<Double-Button-1>", on_double_click)
    measures_listbox.bind("<Button-3>", lambda e: on_right_click(e))

    result_tree.bind("<Button-3>", show_result_context_menu)

    execute_btn = ttk.Button(content, text="Execute Query", command=execute_query)
    execute_btn.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)