# overview_semantic_export.py
import os
import time
import re
import pandas as pd

def export_semantic_tables(cube_label, df_full_tables, export_dir, append_log, log_ref):
    """
    Writes df_full_tables (dict of DataFrame) to an Excel file inside export_dir.
    Returns the path to the created file.
    """
    safe = ''.join(ch if ch.isalnum() or ch in ('_', '-') else '_' for ch in cube_label)[:120]
    ts = int(time.time())

    os.makedirs(export_dir, exist_ok=True)
    out_file = os.path.join(export_dir, f"{safe}_cube_semantic_export_{ts}.xlsx")

    canonical_order = [
        "dimensions", "hierarchies", "levels", 
        "attributes", "attribute_keys",
        "datasets", "physical_tables", "physical_columns", 
        "logical_key_refs", "logical_attribute_refs",
        "cubes", "cube_dimensions", "measures", 
        "calc_members"
    ]

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

    append_log(log_ref, f"Exported {len(df_full_tables)} semantic tables to Excel: {out_file}")
    return out_file