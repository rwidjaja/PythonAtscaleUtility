import json
import pandas as pd
import tkinter as tk
from tkinter import ttk

with open("nested.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

# --- Recursive array finder ---
def find_arrays(obj, path=None, results=None):
    if results is None:
        results = {}
    if path is None:
        path = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            find_arrays(v, path + [k], results)
    elif isinstance(obj, list):
        label = " → ".join(path)
        try:
            df = pd.json_normalize(
                raw,
                record_path=path,
                meta=["id","name","version"],
                meta_prefix="cube_",
                errors="ignore"
            )
            results[label] = df
        except Exception:
            pass
        for item in obj:
            find_arrays(item, path, results)
    return results

# Collect all entity sets
options = {"Metadata": pd.json_normalize(raw)}
options.update(find_arrays(raw))

# --- Build relationships ---
def build_relationships(options):
    # Keyed attributes → attribute keys
    if "attributes → keyed-attribute" in options and "attributes → attribute-key" in options:
        df_keyed = options["attributes → keyed-attribute"]
        df_keys = options["attributes → attribute-key"]
        df_rel = df_keyed.merge(df_keys, left_on="key-ref", right_on="id", how="left",
                                suffixes=("_keyed","_base"))
        options["Relationships → keyed-attribute ↔ attribute-key"] = df_rel

    # Dimensions → hierarchy → level (primary-attribute links to attribute-key)
    if "dimensions → dimension → hierarchy → level" in options and "attributes → attribute-key" in options:
        df_levels = options["dimensions → dimension → hierarchy → level"]
        df_keys = options["attributes → attribute-key"]
        df_rel = df_levels.merge(df_keys, left_on="primary-attribute", right_on="id", how="left",
                                 suffixes=("_level","_attribute"))
        options["Relationships → level ↔ attribute-key"] = df_rel

build_relationships(options)

# --- Tkinter GUI ---
root = tk.Tk()
root.title("Cube JSON Explorer")

frame = ttk.Frame(root, padding=10)
frame.pack(fill="both", expand=True)

selected = tk.StringVar(value=list(options.keys())[0])
dropdown = ttk.OptionMenu(frame, selected, list(options.keys())[0], *options.keys())
dropdown.pack(pady=5)

grid_frame = ttk.Frame(frame)
grid_frame.pack(fill="both", expand=True)

def show_dataframe(df):
    for widget in grid_frame.winfo_children():
        widget.destroy()
    tree = ttk.Treeview(grid_frame, columns=list(df.columns), show="headings")
    for col in df.columns:
        tree.heading(col, text=col)
        tree.column(col, width=200, anchor="w")
    for _, row in df.iterrows():
        tree.insert("", "end", values=list(row))
    scrollbar = ttk.Scrollbar(grid_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

def refresh():
    df = options[selected.get()]
    show_dataframe(df)

btn = ttk.Button(frame, text="Load Data", command=refresh)
btn.pack(pady=5)

root.mainloop()
