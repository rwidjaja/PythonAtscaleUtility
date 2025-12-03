# tabs/cube_data_metadata.py
import pandas as pd
from cubes.cube_data_queries import run_xmla_query, DIMENSIONS_QUERY, HIERARCHIES_QUERY, LEVELS_QUERY, MEASURES_QUERY
from cubes.cube_data_parsers import parse_rows

def load_cube_metadata(catalog, cube, log_function):
    """Load all metadata for the selected cube"""
    dimensions_df = None
    hierarchies_df = None  
    levels_df = None
    measures_df = None
    dimension_mapping = {}
    measure_mapping = {}
    
    try:
        # Clear previous mappings
        dimension_mapping.clear()
        measure_mapping.clear()
        
        # Load dimensions
        log_function(f"Loading dimensions for {cube}...")
        dim_xml = run_xmla_query(DIMENSIONS_QUERY.format(catalog=catalog, cube_name=cube))
        dimensions_df = parse_rows(dim_xml, ["DIMENSION_UNIQUE_NAME", "DIMENSION_CAPTION", "DEFAULT_HIERARCHY"])
        log_function(f"Loaded {len(dimensions_df)} dimensions")
        
        # Load hierarchies - NOW INCLUDING HIERARCHY_CAPTION
        log_function(f"Loading hierarchies for {cube}...")
        hier_xml = run_xmla_query(HIERARCHIES_QUERY.format(catalog=catalog, cube_name=cube))
        hierarchies_df = parse_rows(hier_xml, ["DIMENSION_UNIQUE_NAME", "HIERARCHY_NAME", "HIERARCHY_UNIQUE_NAME", "HIERARCHY_CAPTION", "HIERARCHY_DISPLAY_FOLDER"])
        log_function(f"Loaded {len(hierarchies_df)} hierarchies")
        
        # Load levels
        log_function(f"Loading levels for {cube}...")
        levels_xml = run_xmla_query(LEVELS_QUERY.format(catalog=catalog, cube_name=cube))
        levels_df = parse_rows(levels_xml, ["DIMENSION_UNIQUE_NAME", "HIERARCHY_UNIQUE_NAME", "LEVEL_NAME", "LEVEL_UNIQUE_NAME", "LEVEL_CAPTION", "LEVEL_NUMBER"])
        log_function(f"Loaded {len(levels_df)} levels")
        
        # Load measures
        log_function(f"Loading measures for {cube}...")
        measures_xml = run_xmla_query(MEASURES_QUERY.format(catalog=catalog, cube_name=cube))
        measures_df = parse_rows(measures_xml, ["MEASURE_NAME", "MEASURE_UNIQUE_NAME", "MEASURE_CAPTION", "MEASURE_DISPLAY_FOLDER"])
        log_function(f"Loaded {len(measures_df)} measures")
        
        log_function(f"Successfully loaded metadata for {cube}")
        
        return dimensions_df, hierarchies_df, levels_df, measures_df, dimension_mapping, measure_mapping
        
    except Exception as e:
        log_function(f"Error loading cube metadata: {e}")
        return None, None, None, None, {}, {}

def populate_listboxes(dimensions_listbox, measures_listbox, dimensions_df, hierarchies_df, levels_df, measures_df, dimension_mapping, measure_mapping):
    """Populate the dimensions and measures listboxes with hierarchies and levels"""
    dimensions_listbox.delete(0, 'end')
    measures_listbox.delete(0, 'end')
    
    # Clear mappings
    dimension_mapping.clear()
    measure_mapping.clear()
    
    # Build structure: Dimension -> Hierarchy -> Levels
    if (dimensions_df is not None and not dimensions_df.empty and 
        hierarchies_df is not None and not hierarchies_df.empty and
        levels_df is not None and not levels_df.empty):
        
        # Get dimension captions
        dim_captions = {}
        for _, dim_row in dimensions_df.iterrows():
            dim_captions[dim_row['DIMENSION_UNIQUE_NAME']] = dim_row['DIMENSION_CAPTION']
        
        # Group hierarchies by dimension
        dimension_hierarchies = {}
        for _, hierarchy_row in hierarchies_df.iterrows():
            dim_unique_name = hierarchy_row['DIMENSION_UNIQUE_NAME']
            if dim_unique_name not in dimension_hierarchies:
                dimension_hierarchies[dim_unique_name] = []
            dimension_hierarchies[dim_unique_name].append(hierarchy_row)
        
        # Group levels by hierarchy
        hierarchy_levels = {}
        for _, level_row in levels_df.iterrows():
            hierarchy_name = level_row['HIERARCHY_UNIQUE_NAME']
            if hierarchy_name not in hierarchy_levels:
                hierarchy_levels[hierarchy_name] = []
            hierarchy_levels[hierarchy_name].append(level_row)
        
        # Build the tree structure
        for dim_unique_name, hierarchies in dimension_hierarchies.items():
            dim_caption = dim_captions.get(dim_unique_name, dim_unique_name)
            
            # Add dimension as a header (non-selectable)
            dim_index = dimensions_listbox.size()
            dimensions_listbox.insert('end', f"=== {dim_caption} ===")
            # Remove font option, only use color
            dimensions_listbox.itemconfig(dim_index, {'fg': 'blue'})
            dimension_mapping[dim_index] = None  # Header, not selectable
            
            # Add hierarchies and their levels
            for hierarchy_row in hierarchies:
                hierarchy_caption = hierarchy_row.get('HIERARCHY_CAPTION', hierarchy_row['HIERARCHY_NAME'])
                hierarchy_unique_name = hierarchy_row['HIERARCHY_UNIQUE_NAME']
                
                # Add hierarchy (selectable)
                hierarchy_display = f"  [H] {hierarchy_caption}"
                hierarchy_index = dimensions_listbox.size()
                dimensions_listbox.insert('end', hierarchy_display)
                dimensions_listbox.itemconfig(hierarchy_index, {'fg': 'darkgreen'})
                dimension_mapping[hierarchy_index] = ("hierarchy", hierarchy_unique_name)
                
                # Add levels for this hierarchy
                if hierarchy_unique_name in hierarchy_levels:
                    for level_row in hierarchy_levels[hierarchy_unique_name]:
                        level_caption = level_row.get('LEVEL_CAPTION', level_row['LEVEL_NAME'])
                        level_unique_name = level_row['LEVEL_UNIQUE_NAME']
                        
                        level_display = f"    [L] {level_caption}"
                        level_index = dimensions_listbox.size()
                        dimensions_listbox.insert('end', level_display)
                        # Levels use default color (black)
                        dimension_mapping[level_index] = ("level", level_unique_name)
    
    if measures_df is not None and not measures_df.empty:
        # Group measures by display folder for better organization
        if 'MEASURE_DISPLAY_FOLDER' in measures_df.columns:
            grouped_measures = measures_df.groupby('MEASURE_DISPLAY_FOLDER')
        else:
            # If no display folder, just use the whole dataframe
            grouped_measures = [('', measures_df)]
        
        for folder_name, group in grouped_measures:
            if folder_name:
                # Add folder as a header (non-selectable)
                measure_index = measures_listbox.size()
                measures_listbox.insert('end', f"--- {folder_name} ---")
                measures_listbox.itemconfig(measure_index, {'fg': 'gray'})
                measure_mapping[measure_index] = None  # Header, not selectable
            
            for _, measure_row in group.iterrows():
                display_text = f"  {measure_row['MEASURE_CAPTION']}" if folder_name else measure_row['MEASURE_CAPTION']
                measure_index = measures_listbox.size()
                measures_listbox.insert('end', display_text)
                # Measures use default color (black)
                measure_mapping[measure_index] = measure_row['MEASURE_UNIQUE_NAME']