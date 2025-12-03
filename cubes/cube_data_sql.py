# tabs/cube_data_sql.py
import json
import requests
import urllib3
import xml.etree.ElementTree as ET
import pandas as pd
from common import load_config, get_jwt, get_instance_type, append_log

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def submit_sql_query(sql_query, catalog, cube, use_agg=True, use_cache=True):
    """Submit SQL query to AtScale with flags"""
    # Use the common get_jwt function instead of duplicating the logic
    jwt = get_jwt()
    config = load_config()
    organization = config.get("organization", "default")
    instance_type = get_instance_type()
    host = config["host"]
    
    payload = {
        "language": "SQL",
        "query": sql_query,
        "context": {
            "organization": {"id": organization},
            "environment": {"id": "default"},
            "project": {"name": catalog}
        },
        "useAggs": use_agg,
        "genAggs": use_agg,
        "fakeResults": False,
        "dryRun": False,
        "useLocalCache": use_cache,
        "useAggregateCache": use_cache,
        "timeout": "2.minutes"
    }
    
    if instance_type == "installer":
        url = f"https://{host}:10502/query/orgId/{organization}/submit"
    else:
        url = f"https://{host}/engine/query/submit"
        
    headers = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}
    resp = requests.post(url, json=payload, headers=headers, verify=False)
    resp.raise_for_status()
    return resp.text

def parse_sql_results(xml_text):
    """Parse SQL query results from XML response - FIXED to match MDX format"""
    try:
        root = ET.fromstring(xml_text)
        columns = [col.find("name").text for col in root.findall(".//columns/column")]
        rows = []
        for row in root.findall(".//data/row"):
            values = []
            for col in row.findall("column"):
                if "null" in col.attrib:
                    values.append(None)
                else:
                    values.append(col.text)
            rows.append(values)
        
        df = pd.DataFrame(rows, columns=columns)
        
        # Convert numeric columns (skip the first column which is usually dimension)
        for col in df.columns:
            # Use the new approach without errors parameter
            try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                # If conversion fails, leave as string
                pass
            
        return df
    except Exception as e:
        print(f"Error parsing SQL results: {e}")
        return pd.DataFrame()

def extract_sql_column_name(unique_name):
    """Extract SQL column name from MDX unique name"""
    # MDX format: [Dimension].[Hierarchy].[Level] or [Measures].[MeasureName]
    # SQL format: column_name (no brackets, no hierarchy/level structure)
    
    # Remove brackets if present
    if unique_name.startswith('[') and unique_name.endswith(']'):
        # Remove outer brackets
        name = unique_name[1:-1]
        
        # Split by dots and brackets to get the last part
        parts = name.replace('].[', '.').split('.')
        
        # The last part is usually the column name
        if len(parts) > 0:
            column_name = parts[-1]
            # Remove any remaining brackets
            column_name = column_name.replace('[', '').replace(']', '')
            return column_name
    
    # If no brackets, return as is
    return unique_name

def build_sql_query(dimensions, measures, cube_name):
    """Build SQL query from selected dimensions and measures using SQL column names"""
    # Format dimensions - extract SQL column names from MDX unique names
    dim_clauses = []
    for dim in dimensions:
        sql_column = extract_sql_column_name(dim)
        dim_clauses.append(f"`{cube_name}`.`{sql_column}` AS `{sql_column}`")
    
    # Format measures - extract SQL column names from MDX unique names
    measure_clauses = []
    for measure in measures:
        sql_column = extract_sql_column_name(measure)
        # For measures in SQL, we don't need aggregation functions - AtScale handles it
        measure_clauses.append(f"`{sql_column}`")
    
    # Build SELECT clause
    select_parts = dim_clauses + measure_clauses
    select_clause = ", ".join(select_parts)
    
    # Build GROUP BY clause using position numbers
    group_by_clause = ", ".join([str(i+1) for i in range(len(dim_clauses))])
    
    sql_query = f"""SELECT {select_clause}
FROM `{cube_name}` `{cube_name}`
GROUP BY {group_by_clause}"""
    
    return sql_query

def execute_sql_query(dimensions, measures, catalog, cube, log_function, use_agg=True, use_cache=True):
    """Execute SQL query with the given dimensions and measures with flags"""
    try:
        log_function("Building SQL query...")
        sql_query = build_sql_query(dimensions, measures, cube)
        
        log_function(f"Generated SQL:\n{sql_query}")
        log_function(f"Flags - Use Agg: {use_agg}, Use Cache: {use_cache}")
        log_function("Executing SQL query...")
        
        # Submit query with flags
        xml_response = submit_sql_query(sql_query, catalog, cube, use_agg, use_cache)
        
        # Parse results
        df = parse_sql_results(xml_response)
        
        if not df.empty:
            log_function(f"SQL query executed successfully! ({len(df)} rows)")
            return df
        else:
            log_function("No data returned from SQL query")
            return pd.DataFrame()
            
    except Exception as e:
        log_function(f"SQL query execution error: {e}")
        import traceback
        log_function(f"Traceback: {traceback.format_exc()}")
        return pd.DataFrame()

def execute_raw_sql_query(sql_query, catalog, cube, log_function, use_agg=True, use_cache=True):
    """Execute raw SQL query using AtScale's SQL endpoint with flags"""
    try:
        log_function("Executing raw SQL query...")
        
        # Clean the query by removing comments and extra whitespace
        lines = sql_query.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped_line = line.strip()
            # Remove lines that are only SQL comments
            if not stripped_line.startswith('--') and stripped_line != '':
                cleaned_lines.append(line)
        cleaned_query = '\n'.join(cleaned_lines).strip()
        
        log_function(f"Cleaned SQL query:\n{cleaned_query}")
        log_function(f"Flags - Use Agg: {use_agg}, Use Cache: {use_cache}")
        log_function("Submitting SQL query to AtScale...")
        
        # Submit the raw SQL query directly with flags
        xml_response = submit_sql_query(cleaned_query, catalog, cube, use_agg, use_cache)
        
        log_function("Parsing SQL results...")
        # Parse the results using your existing function
        df = parse_sql_results(xml_response)
        
        if not df.empty:
            log_function(f"Raw SQL query executed successfully! ({len(df)} rows returned)")
            return df
        else:
            log_function("No data returned from raw SQL query")
            return pd.DataFrame()
            
    except Exception as e:
        log_function(f"Raw SQL query execution error: {e}")
        import traceback
        log_function(f"Traceback: {traceback.format_exc()}")
        return pd.DataFrame()