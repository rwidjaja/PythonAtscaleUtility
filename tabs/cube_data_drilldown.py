# tabs/cube_data_drilldown.py
import pandas as pd
import tkinter as tk
from tkinter import ttk
from .cube_data_queries import run_xmla_query, build_xmla_request
from .cube_data_parsers import parse_xmla_result_to_dataframe

def get_hierarchy_levels_fallback(hierarchy_unique_name, levels_df):
    """Fallback method to get levels if LEVEL_NUMBER is not available"""
    if levels_df is not None and not levels_df.empty:
        hierarchy_levels = levels_df[
            (levels_df['HIERARCHY_UNIQUE_NAME'] == hierarchy_unique_name)
        ]
        
        # If LEVEL_NUMBER is not available, try to infer order from LEVEL_UNIQUE_NAME
        if 'LEVEL_NUMBER' not in hierarchy_levels.columns or hierarchy_levels['LEVEL_NUMBER'].isna().all():
            # Create a temporary ordering based on row order or level name pattern
            hierarchy_levels = hierarchy_levels.reset_index(drop=True)
            hierarchy_levels['_inferred_order'] = hierarchy_levels.index
            
            # Try to detect natural hierarchy order
            all_levels = hierarchy_levels.to_dict('records')
            return sorted(all_levels, key=lambda x: x.get('_inferred_order', 0))
        
        return hierarchy_levels.to_dict('records')
    return []

def get_hierarchy_levels(hierarchy_unique_name, levels_df):
    """Get all levels for a hierarchy, sorted by level number with fallback"""
    if levels_df is not None and not levels_df.empty:
        hierarchy_levels = levels_df[
            (levels_df['HIERARCHY_UNIQUE_NAME'] == hierarchy_unique_name)
        ]
        
        # Check if LEVEL_NUMBER exists and has valid data
        if 'LEVEL_NUMBER' in hierarchy_levels.columns and not hierarchy_levels['LEVEL_NUMBER'].isna().all():
            try:
                # Convert to integer and sort
                hierarchy_levels = hierarchy_levels.copy()
                hierarchy_levels['LEVEL_NUMBER'] = hierarchy_levels['LEVEL_NUMBER'].astype(int)
                hierarchy_levels = hierarchy_levels.sort_values('LEVEL_NUMBER')
                return hierarchy_levels.to_dict('records')
            except (ValueError, TypeError):
                # If conversion fails, use fallback
                pass
        
        # Use fallback ordering
        return get_hierarchy_levels_fallback(hierarchy_unique_name, levels_df)
    return []

def get_current_level_info(current_hierarchy, levels_df):
    """Get information about the current level being displayed"""
    if not current_hierarchy:
        return None
        
    # Extract level unique name from current hierarchy reference
    # Format: [Dimension].[Hierarchy].[Level].Members
    level_unique_name = current_hierarchy.replace('.Members', '')
    
    # Find this level in our levels_df
    if levels_df is not None and not levels_df.empty:
        matching_levels = levels_df[levels_df['LEVEL_UNIQUE_NAME'] == level_unique_name]
        if not matching_levels.empty:
            return matching_levels.iloc[0].to_dict()
    
    return None

def get_next_level_info(current_level_info, levels_df):
    """Get the next level in the hierarchy"""
    if not current_level_info:
        return None
        
    hierarchy_unique_name = current_level_info['HIERARCHY_UNIQUE_NAME']
    all_levels = get_hierarchy_levels(hierarchy_unique_name, levels_df)
    
    if not all_levels:
        return None
        
    # Find current level and get next one
    for i, level in enumerate(all_levels):
        if level['LEVEL_UNIQUE_NAME'] == current_level_info['LEVEL_UNIQUE_NAME']:
            if i + 1 < len(all_levels):
                return all_levels[i + 1]
            break
            
    return None

def build_drilldown_mdx(current_hierarchies, current_measures, 
                    selected_member_caption, current_level_info, next_level_info, cube):
    """Build MDX for drill-down operation starting from current level's [All] member"""
    if not current_hierarchies or not current_level_info or not next_level_info:
        return None
        
    # For now, focus on the first hierarchy for drill-down
    hierarchy_info = current_level_info
    current_level_unique_name = current_level_info['LEVEL_UNIQUE_NAME']
    
    # Build the member reference for drill-down
    # Format: [Dimension].[Hierarchy].[Level].&[MemberKey]
    cleaned_caption = selected_member_caption.replace("'", "''")
    member_reference = f"{current_level_unique_name}.&[{cleaned_caption}]"
    
    # Build the drill-down MDX using DrilldownMember starting from current level's [All]
    measures_set = ", ".join(current_measures)
    
    # Use the current level's [All] member, not the hierarchy's [All]
    current_level_all = f"{current_level_unique_name}.[All]"
    
    MDX_QUERY = f"""SELECT
    {{ {measures_set} }} ON COLUMNS,
    NON EMPTY Hierarchize(
        DrilldownMember(
            {{ {{ {current_level_all} }} }},
            {{ {member_reference} }},,,
            INCLUDE_CALC_MEMBERS
        )
    ) DIMENSION PROPERTIES PARENT_UNIQUE_NAME, HIERARCHY_UNIQUE_NAME ON ROWS
    FROM [{cube}]"""
    
    return MDX_QUERY

def build_nested_drilldown_mdx(base_mdx, current_hierarchies, current_measures, 
                            selected_member_caption, current_level_info, next_level_info, cube):
    """Build MDX for nested drill-down operations"""
    if not current_hierarchies or not current_level_info or not next_level_info:
        return None
        
    hierarchy_info = current_level_info
    current_level_unique_name = current_level_info['LEVEL_UNIQUE_NAME']
    
    # Build the member reference for drill-down
    cleaned_caption = selected_member_caption.replace("'", "''")
    member_reference = f"{current_level_unique_name}.&[{cleaned_caption}]"
    
    measures_set = ", ".join(current_measures)
    
    import re
    
    # For nested drill-downs, we need to find the appropriate level to start from
    # Look for patterns like [Dimension].[Hierarchy].[Level].[All]
    all_pattern = r'(\[.*?\]\.\[.*?\]\.\[.*?\])\.[All]'
    all_match = re.search(all_pattern, base_mdx)
    
    if all_match:
        # Found an existing [All] reference, use it as the base
        base_all = all_match.group(1) + ".[All]"
        
        # Extract the current drill-down structure
        pattern = r'DrilldownMember\s*\(\s*\{([^}]+)\}\s*,\s*\{([^}]+)\}'
        drilldown_match = re.search(pattern, base_mdx)
        
        if drilldown_match:
            inner_set = drilldown_match.group(1).strip()
            previous_member = drilldown_match.group(2).strip()
            
            # Nest the new drill-down inside the existing one
            MDX_QUERY = f"""SELECT
    {{ {measures_set} }} ON COLUMNS,
    NON EMPTY Hierarchize(
        DrilldownMember(
            {{ {{ DrilldownMember(
                {{ {inner_set} }},
                {{ {previous_member} }},,,
                INCLUDE_CALC_MEMBERS
            ) }} }},
            {{ {member_reference} }},,,
            INCLUDE_CALC_MEMBERS
        )
    ) DIMENSION PROPERTIES PARENT_UNIQUE_NAME, HIERARCHY_UNIQUE_NAME ON ROWS
    FROM [{cube}]"""
        else:
            # Fallback to simple drill-down from the base [All]
            MDX_QUERY = f"""SELECT
    {{ {measures_set} }} ON COLUMNS,
    NON EMPTY Hierarchize(
        DrilldownMember(
            {{ {{ {base_all} }} }},
            {{ {member_reference} }},,,
            INCLUDE_CALC_MEMBERS
        )
    ) DIMENSION PROPERTIES PARENT_UNIQUE_NAME, HIERARCHY_UNIQUE_NAME ON ROWS
    FROM [{cube}]"""
    else:
        # Fallback to simple drill-down from current level's [All]
        current_level_all = f"{current_level_unique_name}.[All]"
        MDX_QUERY = f"""SELECT
    {{ {measures_set} }} ON COLUMNS,
    NON EMPTY Hierarchize(
        DrilldownMember(
            {{ {{ {current_level_all} }} }},
            {{ {member_reference} }},,,
            INCLUDE_CALC_MEMBERS
        )
    ) DIMENSION PROPERTIES PARENT_UNIQUE_NAME, HIERARCHY_UNIQUE_NAME ON ROWS
    FROM [{cube}]"""
    
    return MDX_QUERY

def drill_down_selection(result_tree, query_history, current_query_index, levels_df, 
                        current_hierarchies, current_measures, current_catalog, current_cube,
                        log_function):
    """Drill down into the selected hierarchy member"""
    selected_items = result_tree.selection()
    if not selected_items:
        log_function("Please select a row to drill down")
        return None, current_hierarchies, current_measures, current_catalog, current_cube, query_history, current_query_index
    
    item = selected_items[0]
    row_text = result_tree.item(item, "text")
    
    try:
        # Get current query context from history
        if current_query_index < 0 or current_query_index >= len(query_history):
            log_function("No current query available for drill-down")
            return None, current_hierarchies, current_measures, current_catalog, current_cube, query_history, current_query_index
        
        current_query = query_history[current_query_index]
        
        log_function(f"Current query MDX: {current_query['mdx']}")
        log_function(f"Current hierarchies: {current_query['hierarchies']}")
        
        # For now, drill down on the first hierarchy
        if current_query['hierarchies'] and levels_df is not None:
            current_hierarchy = current_query['hierarchies'][0]
            
            # Get current level information
            current_level_info = get_current_level_info(current_hierarchy, levels_df)
            next_level_info = get_next_level_info(current_level_info, levels_df)
            
            if current_level_info and next_level_info:
                log_function(f"Drilling down from level: {current_level_info['LEVEL_CAPTION']}")
                log_function(f"Drilling down to level: {next_level_info['LEVEL_CAPTION']}")
                log_function(f"Selected member: {row_text}")
                log_function(f"Current level unique name: {current_level_info['LEVEL_UNIQUE_NAME']}")
                
                # Choose the appropriate MDX builder based on whether this is the first drill-down or nested
                if current_query_index == 0:
                    # First drill-down - use current level's [All] as starting point
                    new_mdx = build_drilldown_mdx(
                        current_query['hierarchies'],
                        current_query['measures'],
                        row_text,
                        current_level_info,
                        next_level_info,
                        current_query['cube']
                    )
                else:
                    # Nested drill-down - build on previous drill-down structure
                    new_mdx = build_nested_drilldown_mdx(
                        current_query['mdx'],
                        current_query['hierarchies'],
                        current_query['measures'],
                        row_text,
                        current_level_info,
                        next_level_info,
                        current_query['cube']
                    )
                
                if not new_mdx:
                    log_function("Failed to build drill-down MDX")
                    return None, current_hierarchies, current_measures, current_catalog, current_cube, query_history, current_query_index
                
                # Update hierarchies to use the next level
                new_hierarchies = current_query['hierarchies'].copy()
                new_hierarchies[0] = f"{next_level_info['LEVEL_UNIQUE_NAME']}.Members"
                
                # Create new query entry
                new_query = {
                    'mdx': new_mdx,
                    'hierarchies': new_hierarchies,
                    'measures': current_query['measures'].copy(),
                    'catalog': current_query['catalog'],
                    'cube': current_query['cube'],
                    'description': f"Drill down from '{row_text}' to {next_level_info['LEVEL_CAPTION']}"
                }
                
                # Add to history and update index
                # Remove any future history if we're drilling from middle
                if current_query_index < len(query_history) - 1:
                    query_history = query_history[:current_query_index + 1]
                
                query_history.append(new_query)
                current_query_index = len(query_history) - 1
                
                # Build XMLA request and execute
                XMLA_REQUEST = build_xmla_request(new_mdx, current_query['catalog'], current_query['cube'])
                
                log_function(f"Drill-down MDX:\n{new_mdx}")
                log_function("Executing drill-down query...")
                
                # Execute drill-down query
                response = run_xmla_query(XMLA_REQUEST)
                df = parse_xmla_result_to_dataframe(response)
                
                if not df.empty:
                    # Limit to first 1000 rows
                    if len(df) > 1000:
                        df = df.head(1000)
                    
                    # Update current context
                    current_hierarchies = new_hierarchies
                    current_measures = new_query['measures']
                    current_catalog = new_query['catalog']
                    current_cube = new_query['cube']
                    
                    return df, current_hierarchies, current_measures, current_catalog, current_cube, query_history, current_query_index
                else:
                    log_function("No data returned from drill-down query")
                    # Remove the failed query from history
                    query_history.pop()
                    current_query_index = len(query_history) - 1
            else:
                log_function("No next level available for drill-down")
                if not current_level_info:
                    log_function("Could not determine current level")
                if not next_level_info:
                    log_function("Could not determine next level")
        else:
            log_function("No hierarchy levels available for drill-down")
            
    except Exception as e:
        log_function(f"Drill-down error: {e}")
        import traceback
        log_function(f"Traceback: {traceback.format_exc()}")
    
    return None, current_hierarchies, current_measures, current_catalog, current_cube, query_history, current_query_index

def drill_up_selection(query_history, current_query_index, 
                      current_hierarchies, current_measures, current_catalog, current_cube,
                      log_function):
    """Drill up to previous query state"""
    if current_query_index <= 0:
        log_function("Already at the top level - cannot drill up")
        return None, current_hierarchies, current_measures, current_catalog, current_cube, query_history, current_query_index
    
    # Move to previous query in history
    current_query_index -= 1
    previous_query = query_history[current_query_index]
    
    log_function(f"Drilling up to: {previous_query['description']}")
    
    try:
        # Build XMLA request and execute
        XMLA_REQUEST = build_xmla_request(previous_query['mdx'], previous_query['catalog'], previous_query['cube'])
        
        log_function(f"Executing previous query...")
        
        # Execute query
        response = run_xmla_query(XMLA_REQUEST)
        df = parse_xmla_result_to_dataframe(response)
        
        if not df.empty:
            # Limit to first 1000 rows
            if len(df) > 1000:
                df = df.head(1000)
            
            # Update current context
            current_hierarchies = previous_query['hierarchies']
            current_measures = previous_query['measures']
            current_catalog = previous_query['catalog']
            current_cube = previous_query['cube']
            
            return df, current_hierarchies, current_measures, current_catalog, current_cube, query_history, current_query_index
        else:
            log_function("No data returned from drill-up query")
            
    except Exception as e:
        log_function(f"Drill-up error: {e}")
    
    return None, current_hierarchies, current_measures, current_catalog, current_cube, query_history, current_query_index