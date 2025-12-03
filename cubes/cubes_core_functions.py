# cubes/tab_core_functions.py
import pandas as pd
from cubes.cube_data_metadata import load_cube_metadata, populate_listboxes
from cubes.cube_data_drilldown import get_hierarchy_levels

# Try different import approaches for the SQL module
try:
    from cubes.cube_data_sql import execute_sql_query
except ImportError as e:
    print(f"Warning: Could not import execute_sql_query: {e}")
    # Define a fallback function
    def execute_sql_query(*args, **kwargs):
        print("SQL functionality not available")
        return pd.DataFrame()

def on_catalog_cube_selected_wrapper(state, catalog, cube, catalog_guid=None, cube_guid=None):
    """Handle catalog-cube selection from common selector"""
    state.update({
        'current_catalog': catalog,
        'current_cube': cube,
        'current_catalog_guid': catalog_guid or "",
        'current_cube_guid': cube_guid or ""
    })
    
    state['log_function'](f"Loading metadata for: {catalog} -> {cube}")
    
    # Load cube metadata
    result = load_cube_metadata(catalog, cube, state['log_function'])
    
    if result[0] is not None:
        (state['dimensions_df'], state['hierarchies_df'], state['levels_df'], 
         state['measures_df'], state['dimension_mapping'], state['measure_mapping']) = result
        # Populate listboxes
        populate_listboxes(
            state['components']['dimensions_listbox'],
            state['components']['measures_listbox'],
            state['dimensions_df'], state['hierarchies_df'], state['levels_df'], 
            state['measures_df'], state['dimension_mapping'], state['measure_mapping']
        )

def on_sql_dialect_change(state):
    """Handle SQL dialect checkbox change"""
    if state['components']['sql_dialect_var'].get():
        state['log_function']("SQL Dialect enabled - drill-down disabled")
    else:
        state['log_function']("MDX Dialect enabled - drill-down available")

def build_initial_mdx(dimension_items, measures_set, cube, levels_df):
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