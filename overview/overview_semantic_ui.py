# overview_semantic_ui.py
import tkinter as tk
from tkinter import ttk
import re

def build_result_ui(result_text, df_ui_tables, append_log, log_ref):
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
            try:
                max_len = df[c].astype(str).map(len).max()
            except Exception:
                max_len = 20
            col_width = max(120, (max_len or 0) * 8)  # allow full natural width, no cap
            tv.column(c, width=col_width, anchor='w', stretch=True)

        # insert rows (limit to 1000)
        limit = 1000
        for _, row in df.head(limit).iterrows():
            vals = [("" if (v is None or str(v).lower() == "nan" or str(v).lower() == "null") else str(v)) 
                    for v in row]
            tv.insert('', 'end', values=vals)

    lb.bind('<<ListboxSelect>>', on_table_select)

    append_log(log_ref, f"Loaded {len(df_ui_tables)} semantic tables into UI. Select a table on the left to preview.")