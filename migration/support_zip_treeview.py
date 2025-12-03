# [file name]: support_zip_treeview.py
import tkinter as tk
from tkinter import ttk

class SupportZipTreeView:
    def __init__(self, parent_window, log_ref_container):
        self.parent_window = parent_window
        self.log_ref_container = log_ref_container
        self.projects_tree = None
        self.selection_callback = None
        self.project_data_map = {}  # Store project data separately
        
    def create_treeview_frame(self, parent_frame, projects):
        """Create the treeview frame with projects"""
        tree_frame = ttk.LabelFrame(parent_frame, text="Available Projects", padding="5")
        
        # Create treeview
        columns = ('selected', 'name', 'datasets', 'dimensions', 'metrics', 'connections')
        self.projects_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode='extended')
        
        # Configure columns
        self._configure_tree_columns()
        
        # Add scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.projects_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.projects_tree.xview)
        self.projects_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.projects_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind click on checkbox column to toggle selection
        self.projects_tree.bind('<Button-1>', self._on_tree_click)
        
        # Load projects into tree
        self._load_projects_into_tree(projects)
        
        return tree_frame
    
    def _configure_tree_columns(self):
        """Configure treeview columns"""
        # Define column headings
        self.projects_tree.heading('selected', text='Select')
        self.projects_tree.heading('name', text='Project Name')
        self.projects_tree.heading('datasets', text='Datasets')
        self.projects_tree.heading('dimensions', text='Dimensions')
        self.projects_tree.heading('metrics', text='Metrics')
        self.projects_tree.heading('connections', text='Connections')
        
        # Define column widths
        self.projects_tree.column('selected', width=60, anchor='center')
        self.projects_tree.column('name', width=250, anchor='w')
        self.projects_tree.column('datasets', width=80, anchor='center')
        self.projects_tree.column('dimensions', width=80, anchor='center')
        self.projects_tree.column('metrics', width=80, anchor='center')
        self.projects_tree.column('connections', width=80, anchor='center')
    
    def _load_projects_into_tree(self, projects):
        """Load projects into the treeview"""
        self.project_data_map.clear()  # Clear existing data
        
        for idx, project in enumerate(projects):
            structure = project['structure']
            
            # Count files
            dataset_count = len([f for f in structure['files'] if 'dataset' in f.lower()])
            dimension_count = len([f for f in structure['files'] if 'dimension' in f.lower()])
            metric_count = len([f for f in structure['files'] if 'metric' in f.lower()])
            connection_count = len([f for f in structure['files'] if 'connection' in f.lower()])
            
            # Insert with checkbox unchecked by default
            item_id = str(idx)
            self.projects_tree.insert('', 'end', iid=item_id,
                values=('☐', project['name'],
                       dataset_count, dimension_count, metric_count, connection_count))
            
            # Store project reference in dictionary, not in tree column
            self.project_data_map[item_id] = project
        
        # Update selection count
        self._update_selection_count()
    
    def _on_tree_click(self, event):
        """Handle click on treeview to toggle checkbox"""
        region = self.projects_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.projects_tree.identify_column(event.x)
            if column == "#1":  # Clicked on the checkbox column
                item = self.projects_tree.identify_row(event.y)
                if item:
                    current_value = self.projects_tree.set(item, 'selected')
                    new_value = "☐" if current_value == "☑" else "☑"
                    self.projects_tree.set(item, 'selected', new_value)
                    self._update_selection_count()
    
    def select_all_projects(self):
        """Select all projects in the tree"""
        for item in self.projects_tree.get_children():
            self.projects_tree.set(item, 'selected', '☑')
        self._update_selection_count()
    
    def deselect_all_projects(self):
        """Deselect all projects in the tree"""
        for item in self.projects_tree.get_children():
            self.projects_tree.set(item, 'selected', '☐')
        self._update_selection_count()
    
    def invert_selection(self):
        """Invert the current selection"""
        for item in self.projects_tree.get_children():
            current_value = self.projects_tree.set(item, 'selected')
            new_value = "☐" if current_value == "☑" else "☑"
            self.projects_tree.set(item, 'selected', new_value)
        self._update_selection_count()
    
    def _update_selection_count(self):
        """Update the selection count and call callback if set"""
        total = len(self.projects_tree.get_children())
        selected = 0
        for item in self.projects_tree.get_children():
            if self.projects_tree.set(item, 'selected') == '☑':
                selected += 1
        
        if self.selection_callback:
            self.selection_callback(selected, total)
    
    def get_selected_projects(self):
        """Get list of selected projects"""
        selected_projects = []
        for item in self.projects_tree.get_children():
            if self.projects_tree.set(item, 'selected') == '☑':
                # Get project data from our dictionary
                if item in self.project_data_map:
                    selected_projects.append(self.project_data_map[item])
        return selected_projects
    
    def set_selection_callback(self, callback):
        """Set a callback function for selection changes"""
        self.selection_callback = callback