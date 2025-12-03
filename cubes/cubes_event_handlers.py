# cubes/tab_event_handlers.py
import tkinter as tk
from tkinter import messagebox
from cubes.cube_data_queries import run_xmla_query, build_xmla_request
from cubes.cube_data_parsers import parse_xmla_result_to_dataframe
from cubes.cube_data_drilldown import get_hierarchy_levels

def on_listbox_click(event, dimension_mapping, measure_mapping):
    """Handle listbox click events"""
    widget = event.widget
    index = widget.nearest(event.y)
    
    if index < 0:
        return
    
    # Determine mapping based on listbox
    if widget == widget.master.winfo_children()[1]:  # Dimensions listbox
        mapping = dimension_mapping.get(index)
    else:  # Measures listbox
        mapping = measure_mapping.get(index)
    
    # If header → clear selection and stop selection only
    if mapping is None:
        widget.selection_clear(0, tk.END)
        return "break"   # prevent selecting headers, allow other events
    
    # If real item → do not return break so double/right click still fires
    return

def get_selected_dimension(dimensions_listbox, dimension_mapping):
    """Get selected dimension from listbox"""
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

def drill_down_listbox_item(log_function, get_selected_dimension_func):
    """Drill down on a listbox item"""
    value = get_selected_dimension_func()
    if value is None:
        return
    
    item_type, unique_name = value
    log_function(f"Listbox drill down on: {item_type}, {unique_name}")
    # TODO: Add your listbox level expansion logic here

def execute_query(state):
    """Execute the query based on current selections"""
    # Get selected dimensions and measures
    dim_listbox = state['components']['dimensions_listbox']
    measure_listbox = state['components']['measures_listbox']
    
    selected_dim_indices = dim_listbox.curselection()
    selected_measure_indices = measure_listbox.curselection()
    
    if not selected_dim_indices or not selected_measure_indices:
        state['log_function']("Please select at least one dimension and one measure")
        return
    
    try:
        # Get current selection from selector
        selection_result = state['components']['selector'].get_current_selection()
        
        # Handle unpacking
        if len(selection_result) == 4:
            catalog, cube, catalog_guid, cube_guid = selection_result
        else:
            # Fallback for backward compatibility
            catalog, cube = selection_result[:2]
            catalog_guid, cube_guid = "", ""
        
        # Update state
        state.update({
            'current_catalog': catalog,
            'current_cube': cube,
            'current_catalog_guid': catalog_guid,
            'current_cube_guid': cube_guid
        })
        
        if not catalog or not cube:
            state['log_function']("Please select a catalog and cube first")
            return
        
        # Get the actual unique names from our mapping for ALL selected items
        dimension_items = []
        for idx in selected_dim_indices:
            mapping = state['dimension_mapping'].get(idx)
            if mapping:
                item_type, unique_name = mapping
                dimension_items.append(unique_name)
        
        measure_unique_names = []
        for idx in selected_measure_indices:
            unique_name = state['measure_mapping'].get(idx)
            if unique_name:
                measure_unique_names.append(unique_name)
        
        if not dimension_items or not measure_unique_names:
            state['log_function']("Error: Could not find unique names for selection")
            return
        
        # Store current context
        state['current_hierarchies'] = dimension_items
        state['current_measures'] = measure_unique_names
        
        if state['components']['sql_dialect_var'].get():
            # Execute SQL query
            state['log_function']("Executing SQL query...")
            from cubes.cubes_core_functions import execute_sql_query  # Import here to avoid circular import
            df = execute_sql_query(
                dimension_items, 
                measure_unique_names, 
                catalog, 
                cube,
                state['log_function'],
                use_agg=True,
                use_cache=True
            )           
            if not df.empty:
                # Limit to first 1000 rows
                if len(df) > 1000:
                    df = df.head(1000)
                    state['log_function'](f"Result truncated to first 1000 rows (original: {len(df)} rows)")
                
                # Display results in Treeview - pass is_sql=True
                state['display_function'](df, is_sql=True)
                
                # Clear MDX history for SQL queries
                state['query_history'] = []
                state['current_query_index'] = -1
                
        else:
            # Execute MDX query
            from cubes.cubes_core_functions import build_initial_mdx  # Import here
            measures_set = ", ".join(measure_unique_names)
            MDX_QUERY = build_initial_mdx(dimension_items, measures_set, cube, state['levels_df'])
            
            # Store the hierarchies for drill-down context
            level_referenced_hierarchies = []
            for item in dimension_items:
                hierarchy_name = item.replace('.Members', '')
                # Get the first non-All level to track current level
                levels = get_hierarchy_levels(hierarchy_name, state['levels_df'])
                if levels:
                    first_level = levels[0]
                    level_referenced_hierarchies.append(f"{first_level['LEVEL_UNIQUE_NAME']}.Members")
                else:
                    level_referenced_hierarchies.append(item)
            
            # Clear history and add this as first query
            state['query_history'] = [{
                'mdx': MDX_QUERY,
                'hierarchies': level_referenced_hierarchies,
                'measures': measure_unique_names.copy(),
                'catalog': catalog,
                'cube': cube,
                'description': "Initial query"
            }]
            state['current_query_index'] = 0
            
            # Build and execute XMLA request
            XMLA_REQUEST = build_xmla_request(MDX_QUERY, catalog, cube, use_agg=True, use_cache=True)
            
            state['log_function'](f"Generated MDX:\n{MDX_QUERY}")
            state['log_function']("Executing MDX query...")
            
            # Execute query
            response = run_xmla_query(XMLA_REQUEST)
            df = parse_xmla_result_to_dataframe(response)
            
            if not df.empty:
                # Limit to first 1000 rows
                if len(df) > 1000:
                    df = df.head(1000)
                    state['log_function'](f"Result truncated to first 1000 rows (original: {len(df)} rows)")
                
                # Display results
                state['display_function'](df, is_sql=False)
    
    except Exception as e:
        state['log_function'](f"Query execution error: {e}")