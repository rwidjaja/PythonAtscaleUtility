# [file name]: common_dimensions_builder.py
# [file content begin]
import os
import shutil
import re
import yaml
from tkinter import ttk, messagebox, simpledialog
from common import append_log

class CommonDimensionsBuilder:
    def __init__(self, config, log_ref_container, migration_ops):
        self.config = config
        self.log_ref_container = log_ref_container
        self.migration_ops = migration_ops
        
    def create_common_dimensions_dialog(self, parent, common_dimensions_data):
        """Create a dialog for selecting dimensions to include in common dimensions"""
        dialog = ttk.Toplevel(parent)
        dialog.title("Create Common Dimensions")
        dialog.geometry("800x600")
        dialog.transient(parent)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        ttk.Label(main_frame, text="Create Common Dimensions", 
                 font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Name entry
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(name_frame, text="Common Dimensions Name:").pack(side="left", padx=(0, 10))
        name_var = ttk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=name_var, width=30)
        name_entry.pack(side="left")
        
        # Dimensions selection tree
        tree_frame = ttk.LabelFrame(main_frame, text="Select Dimensions to Include", padding="5")
        tree_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Create tree with checkboxes
        tree = ttk.Treeview(tree_frame, columns=("dataset", "hierarchies", "levels", "attributes", "connection"), 
                           show="tree headings", selectmode="extended")
        
        # Define columns
        tree.heading("#0", text="Dimension")
        tree.column("#0", width=200)
        
        tree.heading("dataset", text="Dataset")
        tree.column("dataset", width=150)
        
        tree.heading("hierarchies", text="Hierarchies")
        tree.column("hierarchies", width=80)
        
        tree.heading("levels", text="Levels")
        tree.column("levels", width=80)
        
        tree.heading("attributes", text="Attributes")
        tree.column("attributes", width=80)
        
        tree.heading("connection", text="Connection")
        tree.column("connection", width=150)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Load dimensions data
        self.dimensions_data = {}
        self.selected_dimensions = {}
        
        for dim_data in common_dimensions_data:
            dim_id = f"{dim_data['dimension_label']}|{dim_data['dataset_name']}"
            self.dimensions_data[dim_id] = dim_data
            
            # Count hierarchies, levels, and attributes from the best version
            hierarchies_count = dim_data.get('hierarchies_count', 0)
            levels_count = dim_data.get('levels_count', 0)
            attributes_count = dim_data.get('attributes_count', 0)
            
            tree.insert("", "end", iid=dim_id, 
                       values=(dim_data['dataset_name'], 
                              hierarchies_count, 
                              levels_count, 
                              attributes_count,
                              dim_data['connection_id']),
                       text=dim_data['dimension_label'])
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(10, 0))
        
        # Select all button
        ttk.Button(buttons_frame, text="Select All", 
                  command=lambda: self.select_all_items(tree)).pack(side="left", padx=(0, 10))
        
        # Deselect all button
        ttk.Button(buttons_frame, text="Deselect All", 
                  command=lambda: self.deselect_all_items(tree)).pack(side="left", padx=(0, 10))
        
        # Create button
        create_btn = ttk.Button(buttons_frame, text="Create Common Dimensions", 
                               command=lambda: self.create_common_dimensions(
                                   name_var.get(), tree, dialog))
        create_btn.pack(side="right")
        
        # Set default name
        name_var.set("CommonDimensions")
        
        return dialog
    
    def select_all_items(self, tree):
        """Select all items in the tree"""
        for item in tree.get_children():
            tree.selection_add(item)
    
    def deselect_all_items(self, tree):
        """Deselect all items in the tree"""
        tree.selection_clear()
    
    def create_common_dimensions(self, common_name, tree, dialog):
        """Create the common dimensions project"""
        if not common_name.strip():
            messagebox.showerror("Error", "Please enter a name for the common dimensions")
            return
        
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select at least one dimension")
            return
        
        # Get workspace path
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        workspace = self.config.get("workspace", "working_dir")
        
        if not os.path.isabs(workspace):
            workspace = os.path.join(root_dir, workspace)
        
        # Sanitize the name
        sanitized_name = self.sanitize_name(common_name)
        
        # Create the common dimensions structure
        success = self.build_common_dimensions_structure(
            workspace, sanitized_name, selected_items, self.dimensions_data)
        
        if success:
            messagebox.showinfo("Success", 
                              f"Common dimensions '{sanitized_name}' created successfully!")
            dialog.destroy()
        else:
            messagebox.showerror("Error", "Failed to create common dimensions")
    
    def sanitize_name(self, name):
        """Sanitize the name for folder and file naming"""
        sanitized = re.sub(r'[^\w\s-]', '', name)
        sanitized = re.sub(r'[-\s]+', '-', sanitized)
        return sanitized.strip('-')
    
    def build_common_dimensions_structure(self, workspace, common_name, selected_dimensions, dimensions_data):
        """Build the complete common dimensions structure"""
        try:
            # Create base directory
            common_dir = os.path.join(workspace, "sml", "common_dimensions", common_name)
            os.makedirs(common_dir, exist_ok=True)
            
            append_log(self.log_ref_container[0], 
                      f"Creating common dimensions: {common_name} at {common_dir}")
            
            # Create catalog.yml
            self.create_catalog_file(common_dir, common_name)
            
            # Create connections directory and file
            connection_id = self.create_connection_file(common_dir, common_name, selected_dimensions, dimensions_data)
            
            if not connection_id:
                append_log(self.log_ref_container[0], "Warning: No connection found, using default")
                connection_id = f"{common_name}_connection"
            
            # Create datasets directory and copy datasets
            self.copy_datasets(common_dir, selected_dimensions, dimensions_data, connection_id)
            
            # Create dimensions directory and copy dimensions
            self.copy_dimensions(common_dir, selected_dimensions, dimensions_data)
            
            # Create README or info file
            self.create_info_file(common_dir, common_name, selected_dimensions, dimensions_data)
            
            append_log(self.log_ref_container[0], f"✓ Common dimensions structure created: {common_name}")
            
            # Commit to Git
            self.commit_to_git(common_name, common_dir)
            
            return True
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error building common dimensions: {e}")
            return False
    
    def create_catalog_file(self, common_dir, common_name):
        """Create catalog.yml file"""
        catalog_content = {
            "version": "1.3",
            "unique_name": common_name,
            "object_type": "catalog",
            "label": common_name,
            "aggressive_agg_promotion": False,
            "build_speculative_aggs": True
        }
        
        catalog_path = os.path.join(common_dir, "catalog.yml")
        with open(catalog_path, 'w', encoding='utf-8') as f:
            yaml.dump(catalog_content, f, default_flow_style=False, sort_keys=False)
        
        append_log(self.log_ref_container[0], f"Created catalog.yml at {catalog_path}")
    
    def create_connection_file(self, common_dir, common_name, selected_dimensions, dimensions_data):
        """Create connection file by finding the most common connection"""
        connections_dir = os.path.join(common_dir, "connections")
        os.makedirs(connections_dir, exist_ok=True)
        
        # Find the most common connection among selected dimensions
        connection_counter = {}
        for dim_id in selected_dimensions:
            dim_data = dimensions_data[dim_id]
            connection = dim_data.get('connection_id', 'Unknown')
            if connection and connection != "Unknown":
                connection_counter[connection] = connection_counter.get(connection, 0) + 1
        
        if not connection_counter:
            append_log(self.log_ref_container[0], "No valid connections found among selected dimensions")
            return None
        
        # Get the most common connection
        most_common_connection = max(connection_counter.items(), key=lambda x: x[1])[0]
        
        # Create connection file name
        connection_file_name = f"{common_name}_connection.yml"
        connection_path = os.path.join(connections_dir, connection_file_name)
        
        # For now, create a simple connection file
        # In a real implementation, you would fetch the actual connection details from AtScale
        connection_content = {
            "unique_name": f"{common_name}_connection",
            "object_type": "connection",
            "label": f"{common_name}_connection",
            "as_connection": most_common_connection,
            "database": "atscale_data",  # Default values
            "schema": "common_dimensions"
        }
        
        with open(connection_path, 'w', encoding='utf-8') as f:
            yaml.dump(connection_content, f, default_flow_style=False, sort_keys=False)
        
        append_log(self.log_ref_container[0], f"Created connection file: {connection_file_name}")
        return f"{common_name}_connection"
    
    def copy_datasets(self, common_dir, selected_dimensions, dimensions_data, connection_id):
        """Copy dataset files and update connection_id"""
        datasets_dir = os.path.join(common_dir, "datasets")
        os.makedirs(datasets_dir, exist_ok=True)
        
        # Collect unique datasets from all selected dimensions
        all_datasets = set()
        dataset_files_map = {}
        
        for dim_id in selected_dimensions:
            dim_data = dimensions_data[dim_id]
            if 'datasets' in dim_data:
                for dataset_info in dim_data['datasets']:
                    if dataset_info.get('file_path'):
                        dataset_name = dataset_info.get('dataset_name', '')
                        if dataset_name and dataset_info['file_path']:
                            all_datasets.add(dataset_name)
                            dataset_files_map[dataset_name] = dataset_info['file_path']
        
        # Copy and update each dataset file
        for dataset_name in all_datasets:
            source_path = dataset_files_map.get(dataset_name)
            if source_path and os.path.exists(source_path):
                try:
                    # Read the dataset file
                    with open(source_path, 'r', encoding='utf-8') as f:
                        dataset_content = yaml.safe_load(f) or {}
                    
                    # Update connection_id
                    if 'connection_id' in dataset_content:
                        dataset_content['connection_id'] = f"{connection_id}.connection"
                    
                    # Write to destination
                    dest_filename = f"{dataset_name}.dataset.yml"
                    dest_path = os.path.join(datasets_dir, dest_filename)
                    
                    with open(dest_path, 'w', encoding='utf-8') as f:
                        yaml.dump(dataset_content, f, default_flow_style=False, sort_keys=False)
                    
                    append_log(self.log_ref_container[0], f"Copied dataset: {dataset_name}")
                    
                except Exception as e:
                    append_log(self.log_ref_container[0], f"Error copying dataset {dataset_name}: {e}")
            else:
                append_log(self.log_ref_container[0], f"Dataset file not found: {dataset_name}")
    
    def copy_dimensions(self, common_dir, selected_dimensions, dimensions_data):
        """Copy dimension files"""
        dimensions_dir = os.path.join(common_dir, "dimensions")
        os.makedirs(dimensions_dir, exist_ok=True)
        
        for dim_id in selected_dimensions:
            dim_data = dimensions_data[dim_id]
            source_path = dim_data.get('best_version', {}).get('file_path')
            
            if source_path and os.path.exists(source_path):
                try:
                    # Read the dimension file
                    with open(source_path, 'r', encoding='utf-8') as f:
                        dimension_content = yaml.safe_load(f) or {}
                    
                    # Write to destination
                    dest_filename = f"{dim_data['dimension_label']}.yml"
                    dest_filename = re.sub(r'[^\w\s.-]', '', dest_filename)  # Sanitize filename
                    dest_filename = re.sub(r'\s+', '_', dest_filename)
                    
                    dest_path = os.path.join(dimensions_dir, dest_filename)
                    
                    with open(dest_path, 'w', encoding='utf-8') as f:
                        yaml.dump(dimension_content, f, default_flow_style=False, sort_keys=False)
                    
                    append_log(self.log_ref_container[0], f"Copied dimension: {dim_data['dimension_label']}")
                    
                except Exception as e:
                    append_log(self.log_ref_container[0], f"Error copying dimension {dim_data['dimension_label']}: {e}")
            else:
                append_log(self.log_ref_container[0], f"Dimension file not found: {dim_data['dimension_label']}")
    
    def create_info_file(self, common_dir, common_name, selected_dimensions, dimensions_data):
        """Create an info/README file about the common dimensions"""
        info_content = f"""# Common Dimensions: {common_name}
Generated: {self.get_current_timestamp()}
Total Dimensions: {len(selected_dimensions)}

## Included Dimensions:
"""
        
        for dim_id in selected_dimensions:
            dim_data = dimensions_data[dim_id]
            info_content += f"""
- {dim_data['dimension_label']}
  Dataset: {dim_data['dataset_name']}
  Connection: {dim_data['connection_id']}
  Hierarchies: {dim_data.get('hierarchies_count', 0)}
  Levels: {dim_data.get('levels_count', 0)}
  Attributes: {dim_data.get('attributes_count', 0)}
"""
        
        info_path = os.path.join(common_dir, "README.md")
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(info_content)
    
    def get_current_timestamp(self):
        """Get current timestamp for info file"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def commit_to_git(self, common_name, common_dir):
        """Commit the common dimensions to Git repository"""
        try:
            # Get the relative path from workspace
            workspace = self.config.get("workspace", "working_dir")
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
            
            # Create Git repository name
            repo_name = f"common-dimensions-{common_name}"
            
            # Use migration_ops to create Git repository
            if hasattr(self.migration_ops, 'create_git_repository'):
                success = self.migration_ops.create_git_repository(
                    repo_name, 
                    f"Common Dimensions: {common_name}",
                    common_dir
                )
                
                if success:
                    append_log(self.log_ref_container[0], 
                             f"✓ Committed common dimensions '{common_name}' to Git repository: {repo_name}")
                else:
                    append_log(self.log_ref_container[0], 
                             f"✗ Failed to commit common dimensions to Git")
            else:
                append_log(self.log_ref_container[0], 
                         "Git commit functionality not available in migration_ops")
                
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error committing to Git: {e}")
# [file content end]