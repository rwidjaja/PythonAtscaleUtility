# tabs/catalog_tree_manager.py
import pandas as pd

def populate_catalog_treeviews(dimensions_tree, measures_tree, catalog_data, current_cube):
    """Populate the dimensions and measures treeviews with catalog structure"""
    # Clear existing trees
    dimensions_tree.delete(*dimensions_tree.get_children())
    measures_tree.delete(*dimensions_tree.get_children())
    
    # Populate dimensions tree
    dimensions_df = catalog_data.get('dimensions_detail_df')
    hierarchies_df = catalog_data.get('hierarchies_detail_df')
    levels_df = catalog_data.get('levels_detail_df')
    
    if dimensions_df is not None and not dimensions_df.empty:
        # Filter for current cube
        cube_dimensions = dimensions_df[dimensions_df['CUBE_NAME'] == current_cube]
        
        for _, dim_row in cube_dimensions.iterrows():
            dim_name = dim_row['DIMENSION_CAPTION']
            dim_unique_name = dim_row['DIMENSION_UNIQUE_NAME']
            
            dim_id = dimensions_tree.insert("", "end", text=dim_name, values=("dimension", dim_unique_name))
            
            # Add hierarchies for this dimension
            if hierarchies_df is not None and not hierarchies_df.empty:
                cube_hierarchies = hierarchies_df[
                    (hierarchies_df['CUBE_NAME'] == current_cube) & 
                    (hierarchies_df['DIMENSION_UNIQUE_NAME'] == dim_unique_name)
                ]
                
                for _, hier_row in cube_hierarchies.iterrows():
                    hier_name = hier_row['HIERARCHY_CAPTION']
                    hier_unique_name = hier_row['HIERARCHY_UNIQUE_NAME']
                    
                    hier_id = dimensions_tree.insert(dim_id, "end", text=hier_name, values=("hierarchy", hier_unique_name))
                    
                    # Add levels for this hierarchy
                    if levels_df is not None and not levels_df.empty:
                        hierarchy_levels = levels_df[
                            (levels_df['CUBE_NAME'] == current_cube) & 
                            (levels_df['HIERARCHY_UNIQUE_NAME'] == hier_unique_name)
                        ]
                        
                        for _, level_row in hierarchy_levels.iterrows():
                            level_name = level_row['LEVEL_CAPTION']
                            level_unique_name = level_row['LEVEL_UNIQUE_NAME']
                            
                            dimensions_tree.insert(hier_id, "end", text=level_name, values=("level", level_unique_name))
    
    # Populate measures tree
    measures_df = catalog_data.get('measures_detail_df')
    if measures_df is not None and not measures_df.empty:
        cube_measures = measures_df[measures_df['CUBE_NAME'] == current_cube]
        
        # Group by display folder
        if 'MEASURE_DISPLAY_FOLDER' in cube_measures.columns:
            grouped_measures = cube_measures.groupby('MEASURE_DISPLAY_FOLDER')
        else:
            grouped_measures = [('', cube_measures)]
        
        for folder_name, group in grouped_measures:
            if folder_name:
                folder_id = measures_tree.insert("", "end", text=folder_name, values=("folder", folder_name))
            else:
                folder_id = ""
            
            for _, measure_row in group.iterrows():
                measure_name = measure_row['MEASURE_CAPTION']
                measure_unique_name = measure_row['MEASURE_UNIQUE_NAME']
                
                if folder_name:
                    measures_tree.insert(folder_id, "end", text=measure_name, values=("measure", measure_unique_name))
                else:
                    measures_tree.insert("", "end", text=measure_name, values=("measure", measure_unique_name))

    return True

def handle_tree_selection(event, tree_type, catalog_data, display_function, log_function):
    """Handle treeview item selection and display recursive information"""
    tree = event.widget
    selection = tree.selection()
    
    if not selection:
        return
    
    item = selection[0]
    item_values = tree.item(item, "values")
    
    if not item_values:
        return
    
    item_type, unique_name = item_values
    item_text = tree.item(item, "text")
    
    # Columns to remove from display
    columns_to_remove = ['CATALOG_NAME', 'SCHEMA_NAME', 'CUBE_NAME', 'CUBE_GUID']
    
    try:
        if tree_type == "dimensions":
            if item_type == "dimension":
                # Recursively get all hierarchies and levels for this dimension
                display_recursive_dimension(tree, item, catalog_data, display_function, columns_to_remove)
            
            elif item_type == "hierarchy":
                # Recursively get all levels for this hierarchy
                display_recursive_hierarchy(tree, item, catalog_data, display_function, columns_to_remove)
            
            elif item_type == "level":
                # Show detailed level information
                display_level_details(tree, item, catalog_data, display_function, columns_to_remove)
        
        elif tree_type == "measures":
            if item_type == "folder":
                # Show all measures in this folder recursively
                display_recursive_folder(tree, item, catalog_data, display_function, columns_to_remove)
            
            elif item_type == "measure":
                # Show detailed measure information
                display_measure_details(tree, item, catalog_data, display_function, columns_to_remove)
    
    except Exception as e:
        log_function(f"Error displaying catalog details: {e}")

def display_recursive_dimension(tree, item, catalog_data, display_function, columns_to_remove):
    """Display all hierarchies and levels for a dimension recursively"""
    item_values = tree.item(item, "values")
    dim_unique_name = item_values[1]
    dim_name = tree.item(item, "text")
    
    hierarchies_df = catalog_data.get('hierarchies_detail_df')
    levels_df = catalog_data.get('levels_detail_df')
    
    all_data = []
    
    if hierarchies_df is not None and not hierarchies_df.empty:
        # Get all hierarchies for this dimension
        dim_hierarchies = hierarchies_df[hierarchies_df['DIMENSION_UNIQUE_NAME'] == dim_unique_name]
        
        for _, hier_row in dim_hierarchies.iterrows():
            hier_name = hier_row['HIERARCHY_CAPTION']
            hier_unique_name = hier_row['HIERARCHY_UNIQUE_NAME']
            
            # Add hierarchy row
            all_data.append({
                'TYPE': 'Hierarchy',
                'NAME': hier_name,
                'DEFAULT_MEMBER': hier_row.get('DEFAULT_MEMBER', ''),
                'HIERARCHY_ORIGIN': hier_row.get('HIERARCHY_ORIGIN', ''),
                'HIERARCHY_DISPLAY_FOLDER': hier_row.get('HIERARCHY_DISPLAY_FOLDER', ''),
                'PARENT_DIMENSION': dim_name
            })
            
            # Get all levels for this hierarchy
            if levels_df is not None and not levels_df.empty:
                hierarchy_levels = levels_df[levels_df['HIERARCHY_UNIQUE_NAME'] == hier_unique_name]
                
                for _, level_row in hierarchy_levels.iterrows():
                    # Add level row
                    all_data.append({
                        'TYPE': 'Level',
                        'NAME': level_row['LEVEL_CAPTION'],
                        'LEVEL_NUMBER': level_row.get('LEVEL_NUMBER', ''),
                        'CARDINALITY': level_row.get('CARDINALITY', ''),
                        'LEVEL_TYPE': level_row.get('LEVEL_TYPE', ''),
                        'LEVEL_UNIQUE_SETTINGS': level_row.get('LEVEL_UNIQUE_SETTINGS', ''),
                        'LEVEL_IS_VISIBLE': level_row.get('LEVEL_IS_VISIBLE', ''),
                        'PARENT_HIERARCHY': hier_name,
                        'PARENT_DIMENSION': dim_name
                    })
    
    # Create combined dataframe
    if all_data:
        combined_df = pd.DataFrame(all_data)
        display_function(combined_df, f"Dimension (Recursive): {dim_name}")
    else:
        display_function(pd.DataFrame(), f"No data found for dimension: {dim_name}")

def display_recursive_hierarchy(tree, item, catalog_data, display_function, columns_to_remove):
    """Display all levels for a hierarchy recursively"""
    item_values = tree.item(item, "values")
    hier_unique_name = item_values[1]
    hier_name = tree.item(item, "text")
    
    hierarchies_df = catalog_data.get('hierarchies_detail_df')
    levels_df = catalog_data.get('levels_detail_df')
    
    all_data = []
    
    # Get hierarchy details
    if hierarchies_df is not None and not hierarchies_df.empty:
        hierarchy_details = hierarchies_df[hierarchies_df['HIERARCHY_UNIQUE_NAME'] == hier_unique_name]
        if not hierarchy_details.empty:
            hier_row = hierarchy_details.iloc[0]
            # Add hierarchy row
            all_data.append({
                'TYPE': 'Hierarchy',
                'NAME': hier_row['HIERARCHY_CAPTION'],
                'DEFAULT_MEMBER': hier_row.get('DEFAULT_MEMBER', ''),
                'HIERARCHY_ORIGIN': hier_row.get('HIERARCHY_ORIGIN', ''),
                'HIERARCHY_DISPLAY_FOLDER': hier_row.get('HIERARCHY_DISPLAY_FOLDER', '')
            })
    
    # Get all levels for this hierarchy
    if levels_df is not None and not levels_df.empty:
        hierarchy_levels = levels_df[levels_df['HIERARCHY_UNIQUE_NAME'] == hier_unique_name]
        
        for _, level_row in hierarchy_levels.iterrows():
            # Add level row
            all_data.append({
                'TYPE': 'Level',
                'NAME': level_row['LEVEL_CAPTION'],
                'LEVEL_NUMBER': level_row.get('LEVEL_NUMBER', ''),
                'CARDINALITY': level_row.get('CARDINALITY', ''),
                'LEVEL_TYPE': level_row.get('LEVEL_TYPE', ''),
                'LEVEL_UNIQUE_SETTINGS': level_row.get('LEVEL_UNIQUE_SETTINGS', ''),
                'LEVEL_IS_VISIBLE': level_row.get('LEVEL_IS_VISIBLE', ''),
                'PARENT_HIERARCHY': hier_name
            })
    
    # Create combined dataframe
    if all_data:
        combined_df = pd.DataFrame(all_data)
        display_function(combined_df, f"Hierarchy (Recursive): {hier_name}")
    else:
        display_function(pd.DataFrame(), f"No data found for hierarchy: {hier_name}")

def display_recursive_folder(tree, item, catalog_data, display_function, columns_to_remove):
    """Display all measures in a folder recursively"""
    item_values = tree.item(item, "values")
    folder_name = item_values[1]
    
    measures_df = catalog_data.get('measures_detail_df')
    
    if measures_df is not None and not measures_df.empty:
        folder_measures = measures_df[measures_df['MEASURE_DISPLAY_FOLDER'] == folder_name].copy()
        
        # Remove unwanted columns
        for col in columns_to_remove:
            if col in folder_measures.columns:
                folder_measures = folder_measures.drop(columns=[col])
        
        if not folder_measures.empty:
            # Add a TYPE column to distinguish in display
            folder_measures['TYPE'] = 'Measure'
            display_function(folder_measures, f"Folder (All Measures): {folder_name}")
        else:
            display_function(pd.DataFrame(), f"No measures found in folder: {folder_name}")

def display_level_details(tree, item, catalog_data, display_function, columns_to_remove):
    """Display detailed level information"""
    item_values = tree.item(item, "values")
    level_unique_name = item_values[1]
    
    levels_df = catalog_data.get('levels_detail_df')
    if levels_df is not None and not levels_df.empty:
        detail_df = levels_df[levels_df['LEVEL_UNIQUE_NAME'] == level_unique_name].copy()
        # Remove unwanted columns
        for col in columns_to_remove:
            if col in detail_df.columns:
                detail_df = detail_df.drop(columns=[col])
        # Add TYPE column
        detail_df['TYPE'] = 'Level Detail'
        display_function(detail_df, f"Level Detail: {tree.item(item, 'text')}")

def display_measure_details(tree, item, catalog_data, display_function, columns_to_remove):
    """Display detailed measure information"""
    item_values = tree.item(item, "values")
    measure_unique_name = item_values[1]
    
    measures_df = catalog_data.get('measures_detail_df')
    if measures_df is not None and not measures_df.empty:
        detail_df = measures_df[measures_df['MEASURE_UNIQUE_NAME'] == measure_unique_name].copy()
        # Remove unwanted columns
        for col in columns_to_remove:
            if col in detail_df.columns:
                detail_df = detail_df.drop(columns=[col])
        # Add TYPE column
        detail_df['TYPE'] = 'Measure Detail'
        display_function(detail_df, f"Measure Detail: {tree.item(item, 'text')}")