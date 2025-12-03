# tabs/common_selector.py
import tkinter as tk
from tkinter import ttk
from common import append_log
from .cube_data_queries import run_xmla_query, CATALOG_QUERY, CUBE_QUERY_TEMPLATE
from .cube_data_parsers import parse_catalogs, parse_cubes

class CatalogCubeSelector:
    def __init__(self, parent, log_ref_container, on_selection_change=None):
        self.parent = parent
        self.log_ref_container = log_ref_container
        self.on_selection_change = on_selection_change
        self.current_catalog = ""
        self.current_cube = ""
        self.current_catalog_guid = ""
        self.current_cube_guid = ""
        self.available_combinations = []  # List of dicts
        
        self.create_selector()
        self.load_initial_data()
    
    def create_selector(self):
        """Create the combobox selector"""
        self.selector_var = tk.StringVar()
        self.selector = ttk.Combobox(self.parent, textvariable=self.selector_var, state="readonly")
        self.selector["values"] = ["Select Catalog || Cube"]
        self.selector.current(0)
        self.selector.bind("<<ComboboxSelected>>", self._on_select)
    
    def get_selector_widget(self):
        """Return the selector widget for placement in UI"""
        return self.selector
    
    def get_current_selection(self):
        """Return current catalog and cube with GUIDs"""
        return self.current_catalog, self.current_cube, self.current_catalog_guid, self.current_cube_guid
    
    def set_selection_change_callback(self, callback):
        """Set callback for when selection changes"""
        self.on_selection_change = callback
    
    def _on_select(self, event):
        """Handle selection changes"""
        choice = self.selector_var.get()
        if choice == "Select Catalog || Cube":
            self.current_catalog = ""
            self.current_cube = ""
            self.current_catalog_guid = ""
            self.current_cube_guid = ""
            return
        
        # Find the selected combination
        for combo in self.available_combinations:
            if combo['display'] == choice:
                self.current_catalog = combo['catalog_name']
                self.current_cube = combo['cube_name']
                self.current_catalog_guid = combo.get('catalog_guid', '')
                self.current_cube_guid = combo.get('cube_guid', '')
                
                append_log(self.log_ref_container[0], 
                          f"Selected: {self.current_catalog} (GUID: {self.current_catalog_guid}) -> {self.current_cube} (GUID: {self.current_cube_guid})")
                
                # Notify callback if provided
                if self.on_selection_change:
                    self.on_selection_change(
                        self.current_catalog, 
                        self.current_cube,
                        self.current_catalog_guid,
                        self.current_cube_guid
                    )
                return

        
        append_log(self.log_ref_container[0], f"Selected: {catalog} -> {cube}")
        
        # Notify callback if provided
        if self.on_selection_change:
            self.on_selection_change(catalog, cube)
    
    def load_initial_data(self):
        """Load initial catalog and cube data with GUIDs"""
        try:
            append_log(self.log_ref_container[0], "Loading catalogs...")
            cat_xml = run_xmla_query(CATALOG_QUERY)
            catalog_dicts = parse_catalogs(cat_xml)
            append_log(self.log_ref_container[0], f"Catalogs retrieved: {len(catalog_dicts)}")
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error fetching catalogs: {e}")
            return

        results = []
        for cat_dict in catalog_dicts:
            cat_name = cat_dict['name']
            cat_guid = cat_dict['guid']
            
            try:
                append_log(self.log_ref_container[0], f"Loading cubes for catalog: {cat_name}")
                cube_xml = run_xmla_query(CUBE_QUERY_TEMPLATE.format(catalog=cat_name))
                cube_dicts = parse_cubes(cube_xml)
                
                for cube_dict in cube_dicts:
                    cube_name = cube_dict['name']
                    cube_guid = cube_dict['guid']
                    
                    display_text = f"{cat_name} || {cube_name}"
                    results.append({
                        'display': display_text,
                        'catalog_name': cat_name,
                        'cube_name': cube_name,
                        'catalog_guid': cat_guid,
                        'cube_guid': cube_guid
                    })
                
                append_log(self.log_ref_container[0], f"Found {len(cube_dicts)} cubes in {cat_name}")
            except Exception as e:
                append_log(self.log_ref_container[0], f"Error fetching cubes for {cat_name}: {e}")

        if not results:
            append_log(self.log_ref_container[0], "No cubes found.")
            return

        self.available_combinations = results
        display_values = ["Select Catalog || Cube"] + [r['display'] for r in results]
        self.selector["values"] = display_values
        self.selector.current(0)
        append_log(self.log_ref_container[0], f"Loaded {len(results)} catalog-cube combinations with GUIDs")
        
        
    def refresh_data(self):
        """Refresh the catalog-cube data"""
        self.load_initial_data()