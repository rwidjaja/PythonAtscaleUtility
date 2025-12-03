import json
import os
import time
import re
import traceback
import tkinter as tk
from tkinter import ttk
import pandas as pd
import requests
from collections import defaultdict
from common import append_log

class SemanticParser:
    def __init__(self, host, org, log_ref_container):
        self.host = host
        self.org = org
        self.log_ref_container = log_ref_container

    def extract_window_project(self, html_text):
        marker = "window.project"
        idx = html_text.find(marker)
        if idx == -1:
            return None
        eq = html_text.find("=", idx)
        if eq == -1:
            return None
        brace = html_text.find("{", eq)
        if brace == -1:
            return None
        depth = 0
        i = brace
        while i < len(html_text):
            ch = html_text[i]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return html_text[brace:i+1]
            i += 1
        return None

    def extract_basic_fields(self, obj):
        basic = {}
        if isinstance(obj, dict):
            # Extract common fields
            for field in ['id', 'name', 'uiid']:
                if field in obj:
                    basic[field] = obj[field]
            
            # Extract from properties
            props = obj.get('properties', {})
            if isinstance(props, dict):
                if 'caption' in props:
                    basic['caption'] = props['caption']
                if 'visible' in props:
                    basic['visible'] = props['visible']
                # Extract other useful properties
                for prop_key in ['folder', 'dimension-type', 'level-type', 'default-aggregation']:
                    if prop_key in props:
                        basic[prop_key] = props[prop_key]
        
        return basic

    def normalize_semantic(self, payload):
        semantic_tables = defaultdict(list)
        
        # Process dimensions with hierarchies and levels
        if 'dimensions' in payload and 'dimension' in payload['dimensions']:
            for dimension in payload['dimensions']['dimension']:
                dim_data = self.extract_basic_fields(dimension)
                dim_data['type'] = 'dimension'
                
                # Process hierarchies within dimension
                if 'hierarchy' in dimension:
                    for hierarchy in dimension['hierarchy']:
                        hier_data = self.extract_basic_fields(hierarchy)
                        hier_data['type'] = 'hierarchy'
                        hier_data['dimension_id'] = dim_data.get('id')
                        hier_data['dimension_name'] = dim_data.get('name')
                        
                        # Process levels within hierarchy
                        if 'level' in hierarchy:
                            for level in hierarchy['level']:
                                level_data = self.extract_basic_fields(level)
                                level_data['type'] = 'level'
                                level_data['hierarchy_id'] = hier_data.get('id')
                                level_data['hierarchy_name'] = hier_data.get('name')
                                level_data['dimension_id'] = dim_data.get('id')
                                level_data['dimension_name'] = dim_data.get('name')
                                
                                # Extract primary attribute
                                if 'primary-attribute' in level:
                                    level_data['primary_attribute'] = level['primary-attribute']
                                
                                semantic_tables['levels'].append(level_data)
                        
                        semantic_tables['hierarchies'].append(hier_data)
                
                semantic_tables['dimensions'].append(dim_data)

        # Process attributes
        if 'attributes' in payload:
            # Process keyed attributes
            if 'keyed-attribute' in payload['attributes']:
                for attr in payload['attributes']['keyed-attribute']:
                    attr_data = self.extract_basic_fields(attr)
                    attr_data['type'] = 'keyed_attribute'
                    if 'key-ref' in attr:
                        attr_data['key_ref'] = attr['key-ref']
                    semantic_tables['attributes'].append(attr_data)
            
            # Process attribute keys
            if 'attribute-key' in payload['attributes']:
                for key in payload['attributes']['attribute-key']:
                    key_data = self.extract_basic_fields(key)
                    key_data['type'] = 'attribute_key'
                    semantic_tables['attribute_keys'].append(key_data)

        # Process datasets with their physical and logical components
        if 'datasets' in payload and 'data-set' in payload['datasets']:
            for dataset in payload['datasets']['data-set']:
                ds_data = self.extract_basic_fields(dataset)
                ds_data['type'] = 'dataset'
                
                # Process physical tables
                if 'physical' in dataset and 'tables' in dataset['physical']:
                    for table in dataset['physical']['tables']:
                        table_data = {
                            'dataset_id': ds_data.get('id'),
                            'dataset_name': ds_data.get('name'),
                            'schema': table.get('schema'),
                            'table_name': table.get('name')
                        }
                        semantic_tables['physical_tables'].append(table_data)
                
                # Process physical columns
                if 'physical' in dataset and 'columns' in dataset['physical']:
                    for column in dataset['physical']['columns']:
                        col_data = self.extract_basic_fields(column)
                        col_data['type'] = 'physical_column'
                        col_data['dataset_id'] = ds_data.get('id')
                        col_data['dataset_name'] = ds_data.get('name')
                        if 'type' in column and 'data-type' in column['type']:
                            col_data['data_type'] = column['type']['data-type']
                        semantic_tables['physical_columns'].append(col_data)
                
                # Process logical key references
                if 'logical' in dataset and 'key-ref' in dataset['logical']:
                    for key_ref in dataset['logical']['key-ref']:
                        key_ref_data = self.extract_basic_fields(key_ref)
                        key_ref_data['type'] = 'logical_key_ref'
                        key_ref_data['dataset_id'] = ds_data.get('id')
                        key_ref_data['dataset_name'] = ds_data.get('name')
                        if 'column' in key_ref:
                            key_ref_data['columns'] = ', '.join(key_ref['column'])
                        semantic_tables['logical_key_refs'].append(key_ref_data)
                
                # Process logical attribute references
                if 'logical' in dataset and 'attribute-ref' in dataset['logical']:
                    for attr_ref in dataset['logical']['attribute-ref']:
                        attr_ref_data = self.extract_basic_fields(attr_ref)
                        attr_ref_data['type'] = 'logical_attribute_ref'
                        attr_ref_data['dataset_id'] = ds_data.get('id')
                        attr_ref_data['dataset_name'] = ds_data.get('name')
                        if 'column' in attr_ref:
                            attr_ref_data['columns'] = ', '.join(attr_ref['column'])
                        semantic_tables['logical_attribute_refs'].append(attr_ref_data)
                
                semantic_tables['datasets'].append(ds_data)

        # Process cube measures and attributes
        if 'cubes' in payload and 'cube' in payload['cubes']:
            for cube in payload['cubes']['cube']:
                cube_data = self.extract_basic_fields(cube)
                cube_data['type'] = 'cube'
                
                # Process cube attributes (measures)
                if 'attributes' in cube and 'attribute' in cube['attributes']:
                    for attr in cube['attributes']['attribute']:
                        attr_data = self.extract_basic_fields(attr)
                        attr_data['type'] = 'cube_attribute'
                        attr_data['cube_id'] = cube_data.get('id')
                        attr_data['cube_name'] = cube_data.get('name')
                        
                        # Determine if it's a measure
                        if 'properties' in attr and 'type' in attr['properties']:
                            attr_type = attr['properties']['type']
                            if isinstance(attr_type, dict):
                                if 'measure' in attr_type:
                                    attr_data['attribute_type'] = 'measure'
                                    if 'default-aggregation' in attr_type['measure']:
                                        attr_data['aggregation'] = attr_type['measure']['default-aggregation']
                                elif 'count-distinct' in attr_type:
                                    attr_data['attribute_type'] = 'count_distinct_measure'
                                elif 'count-nonnull' in attr_type:
                                    attr_data['attribute_type'] = 'count_nonnull_measure'
                                elif 'sum-distinct' in attr_type:
                                    attr_data['attribute_type'] = 'sum_distinct_measure'
                        
                        semantic_tables['measures'].append(attr_data)
                
                # Process cube dimensions
                if 'dimensions' in cube and 'dimension' in cube['dimensions']:
                    for dim in cube['dimensions']['dimension']:
                        dim_data = self.extract_basic_fields(dim)
                        dim_data['type'] = 'cube_dimension'
                        dim_data['cube_id'] = cube_data.get('id')
                        dim_data['cube_name'] = cube_data.get('name')
                        semantic_tables['cube_dimensions'].append(dim_data)
                
                semantic_tables['cubes'].append(cube_data)

        # Process calculated members
        if 'calculated-members' in payload and 'calculated-member' in payload['calculated-members']:
            for calc_member in payload['calculated-members']['calculated-member']:
                calc_data = self.extract_basic_fields(calc_member)
                calc_data['type'] = 'calculated_member'
                if 'expression' in calc_member:
                    calc_data['expression'] = calc_member['expression']
                semantic_tables['calc_members'].append(calc_data)

        return semantic_tables

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
                proj_json = self.extract_window_project(html_content)
                if not proj_json:
                    append_log(self.log_ref_container[0], "Could not locate window.project JSON in HTML.")
                    return
                cleaned = proj_json.replace(', }', ' }').replace(', ]', ' ]')
                data = json.loads(cleaned)
                append_log(self.log_ref_container[0], "Extracted and parsed window.project JSON.")

            # Normalize into semantic tables
            semantic_tables = self.normalize_semantic(data)

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
                # Prepare Excel export path
                safe = ''.join(ch if ch.isalnum() or ch in ('_', '-') else '_' for ch in cube_label)[:120]
                ts = int(time.time())

                # Ensure excel_export folder exists next to this script
                export_dir = os.path.join(os.path.dirname(__file__), "../excel_export")
                os.makedirs(export_dir, exist_ok=True)

                # Build full output path
                out_file = os.path.join(export_dir, f"{safe}_cube_semantic_export_{ts}.xlsx")

                # Create Excel file only if we have tables
                with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
                    # Write tables in canonical order
                    for sem in canonical_order:
                        if sem in df_full_tables and not df_full_tables[sem].empty:
                            sheet_name = sem.capitalize()[:31]  # Excel sheet name limit
                            sheet_name = re.sub(r'[\\/*?\[\]:]', '_', sheet_name)  # Remove invalid chars
                            df_full_tables[sem].to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Write any remaining tables not in canonical order
                    for sem, df in df_full_tables.items():
                        if sem not in canonical_order and not df.empty:
                            sheet_name = sem.capitalize()[:31]
                            sheet_name = re.sub(r'[\\/*?\[\]:]', '_', sheet_name)
                            df.to_excel(writer, sheet_name=sheet_name, index=False)

                append_log(self.log_ref_container[0], f"Exported {len(df_full_tables)} semantic tables to Excel: {out_file}")
            else:
                append_log(self.log_ref_container[0], "Export to Excel not selected; skipping export.")
                
            # Build UI
            self.build_result_ui(result_text, df_ui_tables)

        except Exception as e:
            append_log(self.log_ref_container[0], f"Error in process_cube_data: {e}")
            append_log(self.log_ref_container[0], traceback.format_exc())

    def build_result_ui(self, result_text, df_ui_tables):
        # Clear existing content
        for child in result_text.winfo_children():
            child.destroy()

        left = tk.Frame(result_text, width=200)
        right = tk.Frame(result_text, width=600, height=400)

        # Prevent frames from resizing to fit children
        left.pack(side='left', fill='y', padx=6)
        left.pack_propagate(False)

        right.pack(side='right', fill='both', expand=True)
        right.pack_propagate(False)

        lb = tk.Listbox(left, width=28, height=30)
        lb.pack(fill='y', expand=False)

        # Define canonical order and display names
        canonical_order = [
            "dimensions", "hierarchies", "levels", 
            "attributes", "attribute_keys",
            "datasets", "physical_tables", "physical_columns", 
            "logical_key_refs", "logical_attribute_refs",
            "cubes", "cube_dimensions", "measures", 
            "calc_members"
        ]
        
        display_map = {
            "dimensions": "Dimensions", 
            "hierarchies": "Hierarchies", 
            "levels": "Levels",
            "attributes": "Attributes", 
            "attribute_keys": "Attribute Keys",
            "datasets": "Datasets", 
            "physical_tables": "Physical Tables",
            "physical_columns": "Physical Columns", 
            "logical_key_refs": "Logical Key Refs",
            "logical_attribute_refs": "Logical Attribute Refs",
            "cubes": "Cubes", 
            "cube_dimensions": "Cube Dimensions", 
            "measures": "Measures", 
            "calc_members": "Calc Members"
        }

        # populate left list with canonical (only those present)
        present = [s for s in canonical_order if s in df_ui_tables] + \
                [s for s in df_ui_tables.keys() if s not in canonical_order]
        
        for s in present:
            label = display_map.get(s, s)
            lb.insert('end', label)
        label_to_key = {display_map.get(k, k): k for k in df_ui_tables.keys()}

        # Right panel layout (Treeview + scrollbars, using grid only)
        tv = ttk.Treeview(right, columns=[], show='headings')

        # Scrollbars
        vsb = ttk.Scrollbar(right, orient='vertical', command=tv.yview)
        hsb = ttk.Scrollbar(right, orient='horizontal', command=tv.xview)

        tv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Layout with grid
        tv.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Configure grid weights so Treeview expands inside fixed frame
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        # Mousewheel bindings
        def _on_mousewheel_vertical(event):
            tv.yview_scroll(int(-1*(event.delta/120)), "units")

        def _on_mousewheel_horizontal(event):
            tv.xview_scroll(int(-1*(event.delta/120)), "units")

        tv.bind("<MouseWheel>", _on_mousewheel_vertical)
        tv.bind("<Shift-MouseWheel>", _on_mousewheel_horizontal)

        def on_table_select(evt):
            if not lb.curselection():
                return
            sel_label = lb.get(lb.curselection()[0])
            sem_key = label_to_key.get(sel_label)
            if not sem_key:
                return
            df = df_ui_tables[sem_key]

            # configure columns
            tv.delete(*tv.get_children())
            tv['columns'] = list(df.columns)
            for c in df.columns:
                tv.heading(c, text=c)
            
                # Auto widen based on max cell length (up to a limit)
                max_len = df[c].astype(str).map(len).max()
                col_width = max(120, max_len * 8)  # allow full natural width, no cap
                tv.column(c, width=col_width, anchor='w', stretch=True)

            # insert rows (limit to 1000)
            limit = 1000
            for _, row in df.head(limit).iterrows():
                vals = [("" if (v is None or str(v).lower() == "nan" or str(v).lower() == "null") else str(v)) 
                        for v in row]
                tv.insert('', 'end', values=vals)

        lb.bind('<<ListboxSelect>>', on_table_select)

        append_log(self.log_ref_container[0], f"Loaded {len(df_ui_tables)} semantic tables into UI. Select a table on the left to preview.")