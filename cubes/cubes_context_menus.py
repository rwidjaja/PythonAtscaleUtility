# cubes/tab_context_menus.py
import tkinter as tk
from cubes.cube_data_drilldown import drill_down_selection, drill_up_selection

def create_context_menus(parent, result_tree, log_function, 
                        drill_down_func, drill_up_func, show_details_func):
    """Create and return context menus"""
    
    # Result tree context menu
    result_context_menu = tk.Menu(result_tree, tearoff=0)
    result_context_menu.add_command(label="Drill Down", command=drill_down_func)
    result_context_menu.add_command(label="Drill Up", command=drill_up_func)
    result_context_menu.add_separator()
    result_context_menu.add_command(label="Show Details", command=show_details_func)
    
    # Listbox context menu
    listbox_context_menu = tk.Menu(parent, tearoff=0)
    listbox_context_menu.add_command(label="Drill Down", command=lambda: None)  # Will be set
    listbox_context_menu.add_command(label="Show Selected", 
                                    command=lambda: print("Selected"))  # Will be set
    
    return {
        'result_context_menu': result_context_menu,
        'listbox_context_menu': listbox_context_menu
    }

def show_result_context_menu(event, result_tree, result_context_menu):
    """Show context menu for result tree"""
    item = result_tree.identify_row(event.y)
    if item:
        result_tree.selection_set(item)
        try:
            result_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            result_context_menu.grab_release()

def create_drill_down_wrapper(state, result_tree):
    """Create drill-down wrapper that checks if SQL is enabled"""
    def wrapper():
        if state['components']['sql_dialect_var'].get():
            state['log_function']("Drill-down not available in SQL dialect")
            return
            
        # Call the drill_down_selection from drilldown module
        result = drill_down_selection(
            result_tree, state['query_history'], state['current_query_index'], 
            state['levels_df'], state['current_hierarchies'], state['current_measures'], 
            state['current_catalog'], state['current_cube'], state['log_function']
        )
        
        if result[0] is not None:
            df, state['current_hierarchies'], state['current_measures'], \
                state['current_catalog'], state['current_cube'], \
                state['query_history'], state['current_query_index'] = result
            state['display_function'](df)
    
    return wrapper

def create_drill_up_wrapper(state):
    """Create drill-up wrapper that checks if SQL is enabled"""
    def wrapper():
        if state['components']['sql_dialect_var'].get():
            state['log_function']("Drill-up not available in SQL dialect")
            return
            
        # Call the drill_up_selection from drilldown module
        result = drill_up_selection(
            state['query_history'], state['current_query_index'],
            state['current_hierarchies'], state['current_measures'], 
            state['current_catalog'], state['current_cube'], state['log_function']
        )
        
        if result[0] is not None:
            df, state['current_hierarchies'], state['current_measures'], \
                state['current_catalog'], state['current_cube'], \
                state['query_history'], state['current_query_index'] = result
            state['display_function'](df)
    
    return wrapper