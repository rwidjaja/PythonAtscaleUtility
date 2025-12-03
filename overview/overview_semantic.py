# overview_semantic.py
import json
import os
import time
import re
import traceback
import requests
import pandas as pd
from collections import defaultdict
from common import append_log

# Import helper modules (relative import so package layout remains)
from overview.overview_semantic_extract import extract_window_project, extract_basic_fields
from overview.overview_semantic_normalize import normalize_semantic
from overview.overview_semantic_export import export_semantic_tables
from overview.overview_semantic_ui import build_result_ui


class SemanticParser:
    def __init__(self, host, org, log_ref_container):
        self.host = host
        self.org = org
        self.log_ref_container = log_ref_container

    def process_cube_data(self, cube_label, cube_id, project_id, jwt, export_enabled, result_text):
        try:
            append_log(self.log_ref_container[0], f"Cube selected: {cube_label}")

            url = f"https://{self.host}:10500/org/{self.org}/project/{project_id}/cube/{cube_id}/"
            headers = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}
            resp = requests.get(url, headers=headers, verify=False, timeout=20)
            resp.raise_for_status()

            html_content = resp.text
            append_log(self.log_ref_container[0], f"Response received, length: {len(html_content)}")

            # Parse JSON or extract from HTML
            data = None
            txt = html_content.strip()
            if txt.startswith('{'):
                try:
                    data = resp.json()
                except Exception:
                    data = json.loads(html_content)
                append_log(self.log_ref_container[0], "Parsed JSON directly from response.")
            else:
                proj_json = extract_window_project(html_content)
                if not proj_json:
                    append_log(self.log_ref_container[0], "Could not locate window.project JSON in HTML.")
                    return
                cleaned = proj_json.replace(', }', ' }').replace(', ]', ' ]')
                data = json.loads(cleaned)
                append_log(self.log_ref_container[0], "Extracted and parsed window.project JSON.")

            # Normalize into semantic tables (uses helper normalize_semantic)
            semantic_tables = normalize_semantic(data)

            # Convert semantic tables to pandas DataFrames
            df_full_tables = {}
            df_ui_tables = {}

            # Define the order and which tables to include
            canonical_order = [
                "dimensions", "hierarchies", "levels", 
                "attributes", "attribute_keys",
                "datasets", "physical_tables", "physical_columns", 
                "logical_key_refs", "logical_attribute_refs",
                "cubes", "cube_dimensions", "measures", 
                "calc_members"
            ]

            for sem in list(semantic_tables.keys()):
                rows = semantic_tables[sem]
                if not rows:
                    continue

                # Clean the data
                for r in rows:
                    keys = list(r.keys())
                    for k in keys:
                        v = r[k]

                        # Clean null/empty values
                        if v is None or v == "" or v == {} or v == []:
                            r[k] = ""
                            continue

                        # Convert complex objects to JSON strings
                        if isinstance(v, (dict, list)):
                            try:
                                r[k] = json.dumps(v, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
                            except:
                                r[k] = str(v)

                        # Clean strings
                        if isinstance(v, str):
                            v = v.replace("\n", " ").replace("\r", " ").strip()
                            v = re.sub(r"\s{2,}", " ", v)
                            r[k] = v

                # Create DataFrame
                if rows:
                    cols = sorted({k for r in rows for k in r.keys()})
                    df_full = pd.DataFrame(rows, columns=cols)
                    df_full_tables[sem] = df_full

                    # Create UI-friendly version (hide internal fields)
                    ui_cols = [c for c in cols if not c.startswith('_')]
                    df_ui = df_full.reindex(columns=ui_cols).replace({None: '', pd.NA: '', 'null': ''}).fillna('')
                    df_ui_tables[sem] = df_ui

            # Check if we have any tables to export
            if not df_full_tables:
                append_log(self.log_ref_container[0], "No semantic tables found to export.")
                return

            if export_enabled:
                # Ensure export directory exists relative to this file (like previous behavior)
                export_dir = os.path.join(os.path.dirname(__file__), "../excel_export")
                os.makedirs(export_dir, exist_ok=True)

                try:
                    out_file = export_semantic_tables(
                        cube_label,
                        df_full_tables,
                        export_dir,
                        append_log,
                        self.log_ref_container[0]
                    )
                    append_log(self.log_ref_container[0], f"Exported {len(df_full_tables)} semantic tables to Excel: {out_file}")
                except Exception as e:
                    append_log(self.log_ref_container[0], f"Export failed: {e}")
                    append_log(self.log_ref_container[0], traceback.format_exc())
            else:
                append_log(self.log_ref_container[0], "Export to Excel not selected; skipping export.")

            # Build UI using helper
            try:
                build_result_ui(result_text, df_ui_tables, append_log, self.log_ref_container[0])
            except Exception as e:
                append_log(self.log_ref_container[0], f"UI build failed: {e}")
                append_log(self.log_ref_container[0], traceback.format_exc())

        except Exception as e:
            append_log(self.log_ref_container[0], f"Error in process_cube_data: {e}")
            append_log(self.log_ref_container[0], traceback.format_exc())