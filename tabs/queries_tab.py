# tabs/queries_tab.py
import tkinter as tk
from tkinter import ttk
from common import append_log

# Import our new modular components
from .common_selector import CatalogCubeSelector
from queries.queries_input import QueryInput
from queries.queries_results import QueryResults
from queries.queries_executor import QueryExecutor
from queries.id_converter import IdConverter



def build_tab(content, log_ref_container):
    # Layout configuration
    content.rowconfigure(0, weight=0)  # Selector
    content.rowconfigure(1, weight=0)  # Options row
    content.rowconfigure(2, weight=1)  # Content area
    content.columnconfigure(0, weight=1)
    content.columnconfigure(1, weight=1)
    
    # Use the same uniform name for both columns so they split 50/50
    content.columnconfigure(0, weight=1, uniform="cols")
    content.columnconfigure(1, weight=1, uniform="cols")
    
    # Data structures
    current_catalog = ""
    current_cube = ""
    current_catalog_id = ""
    current_cube_id = ""
    
    # Initialize components
    executor = QueryExecutor(lambda msg: append_log(log_ref_container[0], msg))
    
    # Define sample queries
    mdx_sample = """-- Sample MDX Query
SELECT 
    { [Measures].[Sales Amount] } ON COLUMNS,
    { [Date].[Calendar Year].[Calendar Year].Members } ON ROWS
FROM [YourCubeName]"""
    
    sql_sample = """-- Sample SQL Query
SELECT 
    `Calendar Year`,
    SUM(`Sales Amount`) as TotalSales
FROM `YourCubeName`
GROUP BY `Calendar Year`
ORDER BY `Calendar Year`"""
    
    # --- Core Functions (DEFINE THESE FIRST) ---
    
    def on_catalog_cube_selected(catalog, cube, catalog_id=None, cube_id=None):
        """Handle catalog-cube selection with IDs"""
        nonlocal current_catalog, current_cube, current_catalog_id, current_cube_id
        current_catalog = catalog
        current_cube = cube
        current_catalog_id = catalog_id or ""
        current_cube_id = cube_id or ""
        
        append_log(log_ref_container[0], f"Selected: {catalog} -> {cube}")
        if 'query_results' in locals():
            query_results.set_status(f"Selected: {catalog} -> {cube}")
        
        # Update sample queries with actual cube name and IDs
        if 'query_input' in locals():
            query_input.update_sample_for_cube(catalog, cube, catalog_id, cube_id)
    
    def on_query_type_change():
        """Handle query type changes"""
        if 'query_input' in locals():
            query_type = query_input.get_query_type()
            # Pass catalog and cube to update_sample_for_cube
            if current_cube:
                query_input.update_sample_for_cube(current_catalog, current_cube, 
                                                 current_catalog_id, current_cube_id)
            else:
                query_input.update_sample_for_cube("", "YourCubeName", "", "")
    
    def execute_query():
        """Execute the current query with Use Agg and Use Cache options"""
        if not current_catalog or not current_cube:
            append_log(log_ref_container[0], "Please select a catalog and cube first")
            return
            
        if 'query_input' not in locals():
            append_log(log_ref_container[0], "Query input not available")
            return
            
        query = query_input.get_query()
        query_type = query_input.get_query_type()
        
        # Get Use Agg and Use Cache values
        use_agg = query_input.get_use_agg()
        use_cache = query_input.get_use_cache()
        
        append_log(log_ref_container[0], f"Use Agg: {use_agg}, Use Cache: {use_cache}")
        
        # Remove comment lines and clean the query
        cleaned_query = clean_query(query)
        
        append_log(log_ref_container[0], f"Executing {query_type} query...")
        
        # Execute query using the improved executor with flags
        df = executor.execute_query(cleaned_query, query_type, current_catalog, current_cube, 
                                   use_agg=use_agg, use_cache=use_cache)
        
        # Display results
        if df is not None and 'query_results' in locals():
            if not df.empty:
                was_truncated = query_results.display_results(df)
                if was_truncated:
                    append_log(log_ref_container[0], "Results were truncated to first 1000 rows")
                append_log(log_ref_container[0], f"Query executed successfully: {len(df)} rows returned")
            else:
                query_results.clear_results()
                append_log(log_ref_container[0], "Query executed but returned no data")
        else:
            if 'query_results' in locals():
                query_results.set_status("Query execution failed")
            append_log(log_ref_container[0], "Query execution failed - no results")
    
    def clean_query(query):
        """Clean the query by removing comment lines and extra whitespace"""
        lines = query.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove lines that are only comments
            stripped_line = line.strip()
            if not stripped_line.startswith('--') and stripped_line != '':
                cleaned_lines.append(line)
        return '\n'.join(cleaned_lines).strip()
    
    # --- UI Components (CREATE THESE AFTER FUNCTION DEFINITIONS) ---
    
    # Common selector
    selector = CatalogCubeSelector(content, log_ref_container, on_catalog_cube_selected)
    selector.get_selector_widget().grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
    
    # Query input component
    query_input = QueryInput(
        content, 
        on_query_type_change=on_query_type_change,
        on_execute=execute_query
    )
    query_input.get_widget().grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
    
    # Query results component
    query_results = QueryResults(content)
    query_results.get_widget().grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
    
    # Set sample queries
    query_input.set_sample_queries(mdx_sample, sql_sample)