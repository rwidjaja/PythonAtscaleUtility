# tabs/queries_tab.py
import tkinter as tk
from tkinter import ttk
from common import append_log

# Import our new modular components
from cubes.common_selector import CatalogCubeSelector
from queries.query_input_ui import QueryInputUI
from queries.query_input_logic import QueryInputLogic
from queries.queries_results import QueryResults
from queries.queries_executor import QueryExecutor
from queries.id_converter import IdConverter


def build_tab(content, log_ref_container):
    # Layout configuration
    content.rowconfigure(0, weight=0)  # Selector
    content.rowconfigure(1, weight=0)  # Options row
    content.rowconfigure(2, weight=1)  # Content area
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

    # --- Core Functions ---
    def on_catalog_cube_selected(catalog, cube, catalog_id=None, cube_id=None):
        nonlocal current_catalog, current_cube, current_catalog_id, current_cube_id
        current_catalog = catalog
        current_cube = cube
        current_catalog_id = catalog_id or ""
        current_cube_id = cube_id or ""

        append_log(log_ref_container[0], f"Selected: {catalog} -> {cube}")
        query_results.set_status(f"Selected: {catalog} -> {cube}")

        # Update sample queries with actual cube name and IDs
        query_logic.update_sample_for_cube(catalog, cube, catalog_id, cube_id)

    def on_query_type_change():
        query_type = query_ui.query_type_var.get()
        if current_cube:
            query_logic.update_sample_for_cube(current_catalog, current_cube,
                                               current_catalog_id, current_cube_id)
        else:
            query_logic.update_sample_for_cube("", "YourCubeName", "", "")

    def execute_query():
        if not current_catalog or not current_cube:
            append_log(log_ref_container[0], "Please select a catalog and cube first")
            return

        query = query_ui.query_text.get("1.0", "end-1c").strip()
        query_type = query_ui.query_type_var.get()

        use_agg = query_ui.use_agg_var.get()
        use_cache = query_ui.use_cache_var.get()
        append_log(log_ref_container[0], f"Use Agg: {use_agg}, Use Cache: {use_cache}")

        cleaned_query = clean_query(query)
        append_log(log_ref_container[0], f"Executing {query_type} query...")

        df = executor.execute_query(cleaned_query, query_type, current_catalog, current_cube,
                                    use_agg=use_agg, use_cache=use_cache)

        if df is not None:
            if not df.empty:
                was_truncated = query_results.display_results(df)
                if was_truncated:
                    append_log(log_ref_container[0], "Results were truncated to first 1000 rows")
                append_log(log_ref_container[0], f"Query executed successfully: {len(df)} rows returned")
            else:
                query_results.clear_results()
                append_log(log_ref_container[0], "Query executed but returned no data")
        else:
            query_results.set_status("Query execution failed")
            append_log(log_ref_container[0], "Query execution failed - no results")

    def clean_query(query):
        lines = query.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line.startswith('--') and stripped_line != '':
                cleaned_lines.append(line)
        return '\n'.join(cleaned_lines).strip()

    # --- UI Components ---
    selector = CatalogCubeSelector(content, log_ref_container, on_catalog_cube_selected)
    selector.get_selector_widget().grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

    # Query input UI + Logic
    query_ui = QueryInputUI(content,
                            on_query_type_change=on_query_type_change,
                            on_execute=execute_query,
                            on_show_history=None)
    query_ui.get_widget().grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    query_logic = QueryInputLogic(query_ui)
    query_ui.set_on_show_history(query_logic.show_query_history)

    # Query results component
    query_results = QueryResults(content)
    query_results.get_widget().grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

    # Set sample queries
    query_logic.set_sample_queries(mdx_sample, sql_sample)
