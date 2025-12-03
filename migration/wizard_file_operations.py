# [file name]: wizard_file_operations.py
import os
import re
import shutil
import yaml
from datetime import datetime
from common import append_log

class WizardFileOperations:
    def __init__(self, migration_controller, log_ref_container):
        self.migration_controller = migration_controller
        self.log_ref_container = log_ref_container
        
    def sanitize_name(self, name):
        """Sanitize the name for folder and file naming"""
        sanitized = re.sub(r'[^\w\s-]', '', name)
        sanitized = re.sub(r'[-\s]+', '-', sanitized)
        sanitized = sanitized.lower().strip('-')
        return sanitized
    
    def cleanup_wizard_workspace(self, project_names):
        """Clean up workspace specifically for wizard operations"""
        try:
            # Get workspace directory
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.migration_controller.config.get("workspace", "working_dir")
            
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
            
            # Clean up SML directories for selected projects
            sml_dir = os.path.join(workspace, "sml")
            
            for project_name in project_names:
                # Try both original and sanitized names
                sanitized_name = re.sub(r'[^\w\s-]', '', project_name)
                sanitized_name = re.sub(r'[-\s]+', '-', sanitized_name)
                sanitized_name = sanitized_name.lower().strip('-')
                
                # Possible project directories to clean
                project_dirs = [
                    os.path.join(sml_dir, project_name),
                    os.path.join(sml_dir, sanitized_name)
                ]
                
                for project_dir in project_dirs:
                    if os.path.exists(project_dir):
                        shutil.rmtree(project_dir)
                        append_log(self.log_ref_container[0], f"Cleaned wizard workspace: {project_dir}")
            
            # Also clean common_dimensions directory
            common_dim_dir = os.path.join(sml_dir, "common_dimensions")
            if os.path.exists(common_dim_dir):
                shutil.rmtree(common_dim_dir)
                append_log(self.log_ref_container[0], f"Cleaned common dimensions directory: {common_dim_dir}")
                
            return True
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error cleaning wizard workspace: {e}")
            return False
    
    def create_catalog_file(self, common_dir, common_name):
        """Create catalog.yml file"""
        catalog_content = {
            "version": 1.3,
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
    
    def create_connection_file(self, common_dir, common_name, selected_dimensions):
        """Create connection file by finding the most common connection"""
        connections_dir = os.path.join(common_dir, "connections")
        os.makedirs(connections_dir, exist_ok=True)
        
        # Find the most common connection among selected dimensions
        connection_counter = {}
        for dim_data in selected_dimensions:
            connection = dim_data.get('connection_id', 'Unknown')
            if connection and connection != "Unknown":
                connection_counter[connection] = connection_counter.get(connection, 0) + 1
        
        if not connection_counter:
            append_log(self.log_ref_container[0], "No valid connections found among selected dimensions")
            # Use a default connection
            most_common_connection = "Postgres14"
        else:
            # Get the most common connection
            most_common_connection = max(connection_counter.items(), key=lambda x: x[1])[0]
        
        # Create connection file name
        connection_file_name = f"{common_name}_connection.yml"
        connection_path = os.path.join(connections_dir, connection_file_name)
        
        # Create connection file
        connection_content = {
            "unique_name": f"{common_name}_connection",
            "object_type": "connection",
            "label": f"{common_name}_connection",
            "as_connection": most_common_connection,
            "database": "atscale_data",
            "schema": "common_dimensions"
        }
        
        with open(connection_path, 'w', encoding='utf-8') as f:
            yaml.dump(connection_content, f, default_flow_style=False, sort_keys=False)
        
        append_log(self.log_ref_container[0], f"Created connection file: {connection_file_name}")
        return f"{common_name}_connection"
    
    def copy_datasets(self, common_dir, selected_dimensions, connection_id):
        """Copy dataset files and update connection_id"""
        datasets_dir = os.path.join(common_dir, "datasets")
        os.makedirs(datasets_dir, exist_ok=True)
        
        # Collect unique datasets from all selected dimensions
        all_datasets = set()
        dataset_files_map = {}
        
        for dim_data in selected_dimensions:
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
    
    def copy_dimensions(self, common_dir, selected_dimensions):
        """Copy dimension files"""
        dimensions_dir = os.path.join(common_dir, "dimensions")
        os.makedirs(dimensions_dir, exist_ok=True)
        
        for dim_data in selected_dimensions:
            source_path = dim_data.get('best_version', {}).get('file_path')
            
            if source_path and os.path.exists(source_path):
                try:
                    # Read the dimension file
                    with open(source_path, 'r', encoding='utf-8') as f:
                        dimension_content = yaml.safe_load(f) or {}
                    
                    # Write to destination
                    dimension_label = dim_data['dimension_label']
                    dest_filename = f"{dimension_label}.yml"
                    dest_filename = re.sub(r'[^\w\s.-]', '', dest_filename)  # Sanitize filename
                    dest_filename = re.sub(r'\s+', '_', dest_filename)
                    
                    dest_path = os.path.join(dimensions_dir, dest_filename)
                    
                    with open(dest_path, 'w', encoding='utf-8') as f:
                        yaml.dump(dimension_content, f, default_flow_style=False, sort_keys=False)
                    
                    append_log(self.log_ref_container[0], f"Copied dimension: {dimension_label}")
                    
                except Exception as e:
                    append_log(self.log_ref_container[0], f"Error copying dimension {dim_data['dimension_label']}: {e}")
            else:
                append_log(self.log_ref_container[0], f"Dimension file not found: {dim_data['dimension_label']}")
    
    def create_info_file(self, common_dir, common_name, selected_dimensions):
        """Create an info/README file about the common dimensions"""
        info_content = f"""# Common Dimensions: {common_name}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Total Dimensions: {len(selected_dimensions)}

## Included Dimensions:
"""
        
        for dim_data in selected_dimensions:
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