# tabs/queries_executor.py
import pandas as pd
from cubes.cube_data_queries import run_xmla_query, build_xmla_request
from cubes.mdx_parser import parse_mdx_result, debug_xmla_response
from cubes.cube_data_sql import execute_raw_sql_query


class QueryExecutor:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        
    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
    
    def execute_query(self, query, query_type, catalog, cube, use_agg=True, use_cache=True):
        """Execute query and return results as DataFrame"""
        try:
            self.log(f"Using flags - Use Agg: {use_agg}, Use Cache: {use_cache}")
            
            if query_type == "MDX":
                return self.execute_mdx(query, catalog, cube, use_agg, use_cache)
            elif query_type == "SQL":
                return self.execute_sql(query, catalog, cube, use_agg, use_cache)
            else:
                self.log(f"Unknown query type: {query_type}")
                return None
        except Exception as e:
            self.log(f"Query execution error: {e}")
            return None
    
    def execute_mdx(self, query, catalog, cube, use_agg=True, use_cache=True):
        """Execute MDX query using XMLA with flags"""
        try:
            self.log(f"Executing MDX query against {catalog}.{cube}")
            
            # Build and execute XMLA request with flags
            xmla_request = build_xmla_request(query, catalog, cube, use_agg, use_cache)
            response = run_xmla_query(xmla_request)
            
            if not response:
                self.log("Empty response from XMLA query")
                return pd.DataFrame()
            
            # Only show minimal debug info, not the full XMLA response
            debug_info = debug_xmla_response(response)
            self.log(f"MDX response: {debug_info['tuple_count']} tuples, {debug_info['cell_count']} cells")
            
            # Parse the response using our XMLA-specific parser
            df = parse_mdx_result(response)
            
            if df is None or df.empty:
                self.log("Failed to parse MDX response - no data extracted")
                # Only show error details if parsing fails
                if 'error' in response.lower() or 'fault' in response.lower():
                    self.log("XMLA response contains error indicators")
                    # Extract error message if possible
                    if '<faultstring>' in response:
                        start = response.find('<faultstring>') + 13
                        end = response.find('</faultstring>')
                        error_msg = response[start:end]
                        self.log(f"XMLA Error: {error_msg}")
                return pd.DataFrame()
                
            self.log(f"Successfully parsed MDX result: {len(df)} rows, {len(df.columns)} columns")
            
            # Log column names for debugging
            self.log(f"Columns: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            self.log(f"MDX execution error: {e}")
            return pd.DataFrame()
    
    def execute_sql(self, query, catalog, cube, use_agg=True, use_cache=True):
        """Execute SQL query with flags"""
        try:
            self.log(f"Executing SQL query against {catalog}.{cube}")
            
            # Import and use the raw SQL execution function with flags

            return execute_raw_sql_query(query, catalog, cube, self.log, use_agg, use_cache)
            
        except ImportError as e:
            self.log(f"Error importing SQL module: {e}")
            return pd.DataFrame({
                'Error': ['SQL execution module not available'],
                'Message': ['Please ensure cube_data_sql.py has execute_raw_sql_query function'],
                'Query': [query[:100] + '...' if len(query) > 100 else query]
            })
        except Exception as e:
            self.log(f"SQL execution error: {e}")
            return pd.DataFrame({
                'Error': [f'SQL execution error: {str(e)}'],
                'Query': [query[:100] + '...' if len(query) > 100 else query]
            })