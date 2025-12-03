# tabs/catalog_data_loader.py
import pandas as pd
from .cube_data_queries import run_xmla_query
from .cube_data_parsers import parse_rows
from .catalog_queries import CATALOG_QUERIES
from .common_xmla import build_xmla_query

def load_catalog_data(catalog: str, cube: str, log_function):
    """Load all catalog metadata for the selected catalog and cube."""
    catalog_data = {name: None for name in CATALOG_QUERIES.keys()}

    try:
        log_function(f"Loading catalog metadata for {catalog} -> {cube}...")

        for df_name, meta in CATALOG_QUERIES.items():
            try:
                log_function(f"Loading {df_name}...")
                query_xml = query_xml = build_xmla_query(meta["sql"], catalog, cube)
                xml_response = run_xmla_query(query_xml)
                catalog_data[df_name] = parse_rows(xml_response, meta["columns"])
                log_function(f"Loaded {len(catalog_data[df_name])} rows for {df_name}")
            except Exception as e:
                log_function(f"Error loading {df_name}: {e}")
                catalog_data[df_name] = pd.DataFrame()

        log_function(f"Successfully loaded catalog metadata for {catalog}")
        return catalog_data

    except Exception as e:
        log_function(f"Error loading catalog metadata: {e}")
        return catalog_data
