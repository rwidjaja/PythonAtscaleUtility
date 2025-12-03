# tabs/catalog_display.py
import pandas as pd

def display_catalog_details(details_tree, df, title=""):
    """Display catalog DataFrame in the details treeview with proper column handling"""
    # Clear existing data
    details_tree.delete(*details_tree.get_children())
    
    if df is None or df.empty:
        # Show empty message
        details_tree["columns"] = ["Message"]
        details_tree.heading("Message", text="Message")
        details_tree.column("Message", width=200)
        details_tree.insert("", "end", values=("No data available"))
        return
    
    # Configure columns - ensure TYPE column is first if it exists
    columns = list(df.columns)
    if 'TYPE' in columns:
        # Move TYPE to the front for better visibility
        columns.remove('TYPE')
        columns.insert(0, 'TYPE')
    
    details_tree["columns"] = columns
    
    # Configure headings with better sizing
    for col in columns:
        details_tree.heading(col, text=col)
        # Set reasonable column widths
        if col == 'TYPE':
            details_tree.column(col, width=100, minwidth=80, stretch=False)
        else:
            details_tree.column(col, width=120, minwidth=80, stretch=False)
    
    # Insert data
    for _, row in df.iterrows():
        values = [str(row[col]) if pd.notna(row[col]) else "" for col in columns]
        details_tree.insert("", "end", values=values)
    
    return True