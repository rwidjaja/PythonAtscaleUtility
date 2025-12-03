# tabs/cube_data_preview_tab.py
import tkinter as tk
import pandas as pd
from common import append_log

# Import from our new modules
from cubes.cubes_ui_components import create_ui_components
from cubes.cubes_core_functions import on_catalog_cube_selected_wrapper, on_sql_dialect_change
from cubes.cubes_event_handlers import (
    on_listbox_click, get_selected_dimension, 
    drill_down_listbox_item, execute_query
)
from cubes.cubes_context_menus import (
    create_context_menus, show_result_context_menu,
    create_drill_down_wrapper, create_drill_up_wrapper
)

def build_tab(content, log_ref_container):
    """Build the cube data preview tab - MAIN DRIVER FUNCTION"""
    
    # Initialize state
    state = {
        # Data structures
        'dimensions_df': None,
        'hierarchies_df': None,  
        'levels_df': None,
        'measures_df': None,
        'dimension_mapping': {},
        'measure_mapping': {},
        'query_history': [],
        'current_query_index': -1,
        'current_hierarchies': [],
        'current_measures': [],
        'current_catalog': "",
        'current_cube': "",
        'current_catalog_guid': "",
        'current_cube_guid': "",
        'current_drill_down_data': {},
        
        # Functions
        'log_function': lambda msg: append_log(log_ref_container[0], msg),
        'display_function': None  # Will be set later
    }
    
    # Create UI components with callback for SQL checkbox
    def on_catalog_selected(catalog, cube, catalog_guid=None, cube_guid=None):
        on_catalog_cube_selected_wrapper(state, catalog, cube, catalog_guid, cube_guid)
    
    def on_sql_checkbox_change():
        on_sql_dialect_change(state)
    
    components = create_ui_components(
        content, log_ref_container, on_catalog_selected, on_sql_checkbox_change
    )
    state['components'] = components
    
    # Create display function
    def display_dataframe_in_treeview(df, is_sql=False):
        """Display DataFrame in Treeview widget"""
        # Clear existing data
        components['result_tree'].delete(*components['result_tree'].get_children())
        
        # Remove duplicate rows
        original_shape = df.shape
        df = df[~df.index.duplicated(keep='first')]
        df = df.drop_duplicates()
        
        if original_shape != df.shape:
            state['log_function'](f"Removed duplicates: {original_shape} -> {df.shape}")
        
        # Clear any previous item data
        if hasattr(display_dataframe_in_treeview, "item_data"):
            display_dataframe_in_treeview.item_data.clear()
        else:
            display_dataframe_in_treeview.item_data = {}
        
        # Configure columns
        columns = list(df.columns)
        
        if is_sql:
            # For SQL: Use regular columns without the tree column
            components['result_tree']["columns"] = columns
            components['result_tree']["show"] = "headings"
            
            for col in columns:
                components['result_tree'].heading(col, text=col)
                components['result_tree'].column(col, width=120, minwidth=80)
        else:
            # For MDX: Use tree column + regular columns
            components['result_tree']["columns"] = columns
            components['result_tree']["show"] = "tree headings"
            
            components['result_tree'].heading("#0", text="Row Labels")
            components['result_tree'].column("#0", width=120, minwidth=80)
            
            for col in columns:
                components['result_tree'].heading(col, text=col)
                components['result_tree'].column(col, width=120, minwidth=80)
        
        # Insert data
        for i, (index, row) in enumerate(df.iterrows()):
            values = [str(row[col]) if pd.notna(row[col]) else "" for col in columns]
            
            if is_sql:
                item = components['result_tree'].insert("", "end", text="", values=values)
            else:
                item = components['result_tree'].insert("", "end", text=str(index), values=values)
            
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
            state['current_drill_down_data']['rows'] = state['current_drill_down_data'].get('rows', [])
            state['current_drill_down_data']['rows'].append(row_data)
        
        # Update global drill-down data
        state['current_drill_down_data'].update({
            'hierarchies': state['current_hierarchies'],
            'measures': state['current_measures'],
            'catalog': state['current_catalog'],
            'cube': state['current_cube']
        })
    
    state['display_function'] = display_dataframe_in_treeview
    
    # Create show details function
    def show_selection_details():
        selected_items = components['result_tree'].selection()
        if not selected_items:
            state['log_function']("Please select a row to show details")
            return
        
        item = selected_items[0]
        if not hasattr(display_dataframe_in_treeview, "item_data") or item not in display_dataframe_in_treeview.item_data:
            state['log_function']("No data available for selected row")
            return
        
        row_data = display_dataframe_in_treeview.item_data[item]
        if row_data:
            details = f"Selected Row Details:\n"
            details += f"Row Label: {row_data['display_text']}\n"
            details += f"Row Number: {row_data['row_number']}\n"
            details += "Values:\n"
            for key, value in row_data['values'].items():
                details += f"  {key}: {value}\n"
            
            state['log_function'](details)
    
    # Create context menus
    drill_down_wrapper = create_drill_down_wrapper(state, components['result_tree'])
    drill_up_wrapper = create_drill_up_wrapper(state)
    
    context_menus = create_context_menus(
        content, components['result_tree'], state['log_function'],
        drill_down_wrapper, drill_up_wrapper, show_selection_details
    )
    
    # Set up listbox menu commands
    def get_dim_selection():
        return get_selected_dimension(components['dimensions_listbox'], state['dimension_mapping'])
    
    context_menus['listbox_context_menu'].entryconfig(0, 
        command=lambda: drill_down_listbox_item(state['log_function'], get_dim_selection))
    context_menus['listbox_context_menu'].entryconfig(1,
        command=lambda: print(get_dim_selection()))
    
    # Set up event bindings
    def bind_listbox_click(event):
        return on_listbox_click(event, state['dimension_mapping'], state['measure_mapping'])
    
    components['dimensions_listbox'].bind("<Button-1>", bind_listbox_click)
    components['measures_listbox'].bind("<Button-1>", bind_listbox_click)
    
    def on_listbox_select(event):
        pass  # Prevent default selection behavior
    
    components['dimensions_listbox'].bind('<<ListboxSelect>>', on_listbox_select)
    components['measures_listbox'].bind('<<ListboxSelect>>', on_listbox_select)
    
    # Bind context menus
    components['result_tree'].bind("<Button-3>", 
        lambda e: show_result_context_menu(e, components['result_tree'], context_menus['result_context_menu']))
    
    # Set execute button command
    components['execute_btn'].config(command=lambda: execute_query(state))
    
    return content