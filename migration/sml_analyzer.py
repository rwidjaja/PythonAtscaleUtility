# [file name]: sml_analyzer.py
# [file content begin]
import os
import glob
import yaml
import re
from common import append_log

class SmlAnalyzer:
    def __init__(self, config, log_ref_container):
        self.config = config
        self.log_ref_container = log_ref_container
        
    def sanitize_project_name(self, project_name):
        """Sanitize project name to match directory naming convention"""
        sanitized = re.sub(r'[^\w\s-]', '', project_name)
        sanitized = re.sub(r'[-\s]+', '-', sanitized)
        sanitized = sanitized.lower().strip('-')
        return sanitized
        
    def analyze_projects(self, project_names, workspace):
        """Analyze the converted SML files to create comprehensive Excel-like report"""
        append_log(self.log_ref_container[0], "Starting comprehensive SML analysis")
        
        sml_dir = os.path.join(workspace, "sml")
        
        # Collect all data for analysis
        all_projects_data = {}
        
        # First pass: collect all datasets, dimensions, and metrics
        for project_name in project_names:
            sanitized_name = self.sanitize_project_name(project_name)
            project_sml_dir = os.path.join(sml_dir, sanitized_name)
            
            if not os.path.exists(project_sml_dir):
                project_sml_dir = os.path.join(sml_dir, project_name)
            
            if os.path.exists(project_sml_dir):
                project_data = self._analyze_project_sml(project_name, project_sml_dir)
                all_projects_data[project_name] = project_data
                append_log(self.log_ref_container[0], f"✓ Analyzed SML files for {project_name}")
            else:
                append_log(self.log_ref_container[0], f"Warning: SML directory not found for {project_name}")
        
        # Build comprehensive report with enhanced dimension analysis
        report_data = self._build_comprehensive_report(all_projects_data)
        return report_data
        
    def _analyze_project_sml(self, project_name, project_sml_dir):
        """Analyze SML files for a single project and return structured data"""
        project_data = {
            'datasets': {},      # {dataset_unique_name: dataset_info}
            'dimensions': {},    # {dimension_filename: dimension_info}
            'metrics': {},       # {metric_filename: metric_info}
            'fact_datasets': set(),  # dataset names used in metrics
            'all_dimension_datasets': set()  # ALL dataset names used in dimensions
        }
        
        # Analyze datasets
        datasets_dir = os.path.join(project_sml_dir, 'datasets')
        if os.path.exists(datasets_dir):
            for yaml_file in glob.glob(os.path.join(datasets_dir, "*.yml")):
                dataset_info = self._read_yaml_file(yaml_file)
                if dataset_info and 'unique_name' in dataset_info:
                    unique_name = dataset_info['unique_name']
                    project_data['datasets'][unique_name] = {
                        'unique_name': unique_name,
                        'object_type': dataset_info.get('object_type', ''),
                        'label': dataset_info.get('label', ''),
                        'connection_id': dataset_info.get('connection_id', ''),
                        'table': dataset_info.get('table', ''),
                        'filename': os.path.basename(yaml_file),
                        'file_path': yaml_file
                    }
        
        # Analyze metrics to identify fact datasets FIRST
        metrics_dir = os.path.join(project_sml_dir, 'metrics')
        if os.path.exists(metrics_dir):
            for yaml_file in glob.glob(os.path.join(metrics_dir, "*.yml")):
                metric_info = self._read_yaml_file(yaml_file)
                if metric_info and 'unique_name' in metric_info:
                    filename = os.path.basename(yaml_file)
                    dataset_ref = metric_info.get('dataset', '')
                    
                    project_data['metrics'][filename] = {
                        'unique_name': metric_info.get('unique_name', ''),
                        'object_type': metric_info.get('object_type', ''),
                        'label': metric_info.get('label', ''),
                        'dataset': dataset_ref,
                        'filename': filename
                    }
                    
                    # Track fact datasets
                    if dataset_ref:
                        project_data['fact_datasets'].add(dataset_ref)
        
        # Analyze dimensions AFTER we know fact datasets
        dimensions_dir = os.path.join(project_sml_dir, 'dimensions')
        if os.path.exists(dimensions_dir):
            for yaml_file in glob.glob(os.path.join(dimensions_dir, "*.yml")):
                dimension_info = self._read_yaml_file(yaml_file)
                if dimension_info and 'unique_name' in dimension_info:
                    filename = os.path.basename(yaml_file)
                    
                    # Extract ALL dataset references from dimension
                    dataset_refs = self._extract_all_datasets_from_dimension(dimension_info)
                    
                    # Check if this dimension uses ANY fact datasets
                    uses_fact_table = any(ds_ref in project_data['fact_datasets'] for ds_ref in dataset_refs)
                    
                    # Count hierarchies, levels, and attributes
                    hierarchies_count, levels_count, attributes_count = self._count_dimension_elements(dimension_info)
                    
                    project_data['dimensions'][filename] = {
                        'unique_name': dimension_info.get('unique_name', ''),
                        'object_type': dimension_info.get('object_type', ''),
                        'label': dimension_info.get('label', ''),
                        'description': dimension_info.get('description', ''),
                        'type': dimension_info.get('type', ''),
                        'dataset_refs': dataset_refs,  # Store ALL dataset references
                        'primary_dataset': self._get_primary_dataset(dataset_refs),  # Determine primary dataset
                        'uses_fact_table': uses_fact_table,  # Flag if uses any fact table
                        'hierarchies_count': hierarchies_count,
                        'levels_count': levels_count,
                        'attributes_count': attributes_count,
                        'filename': filename,
                        'file_path': yaml_file,
                        'project_name': project_name
                    }
                    
                    # Track all datasets used in dimensions
                    if not uses_fact_table:  # Only track datasets from pure dimension tables
                        project_data['all_dimension_datasets'].update(dataset_refs)
        
        return project_data
    
    def _count_dimension_elements(self, dimension_info):
        """Count hierarchies, levels, and secondary attributes in a dimension"""
        hierarchies = dimension_info.get('hierarchies', [])
        hierarchies_count = len(hierarchies)
        
        levels_count = 0
        attributes_count = 0
        
        for hierarchy in hierarchies:
            levels = hierarchy.get('levels', [])
            levels_count += len(levels)
            
            for level in levels:
                # Count secondary attributes
                secondary_attrs = level.get('secondary_attributes', [])
                attributes_count += len(secondary_attrs)
                
                # Count level attributes
                level_attrs = level.get('level_attributes', [])
                attributes_count += len(level_attrs)
        
        # Count root level attributes
        root_attrs = dimension_info.get('level_attributes', [])
        attributes_count += len(root_attrs)
        
        return hierarchies_count, levels_count, attributes_count
    
    def _extract_all_datasets_from_dimension(self, dimension_info):
        """Extract ALL dataset references from dimension structure"""
        datasets = set()
        
        # Check top-level dataset
        if 'dataset' in dimension_info and dimension_info['dataset']:
            datasets.add(dimension_info['dataset'])
        
        # Check hierarchies and levels
        if 'hierarchies' in dimension_info:
            for hierarchy in dimension_info['hierarchies']:
                # Check hierarchy level dataset
                if 'dataset' in hierarchy and hierarchy['dataset']:
                    datasets.add(hierarchy['dataset'])
                
                # Check levels in hierarchy
                if 'levels' in hierarchy:
                    for level in hierarchy['levels']:
                        if 'dataset' in level and level['dataset']:
                            datasets.add(level['dataset'])
                        
                        # Check secondary attributes
                        if 'secondary_attributes' in level:
                            for attr in level['secondary_attributes']:
                                if 'dataset' in attr and attr['dataset']:
                                    datasets.add(attr['dataset'])
                        
                        # Check level attributes  
                        if 'level_attributes' in level:
                            for attr in level['level_attributes']:
                                if 'dataset' in attr and attr['dataset']:
                                    datasets.add(attr['dataset'])
        
        # Check level_attributes at dimension root
        if 'level_attributes' in dimension_info:
            for attr in dimension_info['level_attributes']:
                if 'dataset' in attr and attr['dataset']:
                    datasets.add(attr['dataset'])
        
        return datasets
    
    def _get_primary_dataset(self, dataset_refs):
        """Determine the primary dataset from a set of dataset references"""
        if not dataset_refs:
            return ""
        
        # If there's only one dataset, use it
        if len(dataset_refs) == 1:
            return list(dataset_refs)[0]
        
        # Look for a dataset that doesn't have "fact" in the name as primary
        non_fact_datasets = [ds for ds in dataset_refs if 'fact' not in ds.lower()]
        if non_fact_datasets:
            return non_fact_datasets[0]
        
        # Otherwise return the first one
        return list(dataset_refs)[0]
    
    def _build_comprehensive_report(self, all_projects_data):
        """Build comprehensive Excel-like report data"""
        
        # Find common dimensions across projects (only pure dimension table based)
        common_dimensions = self._find_common_dimensions(all_projects_data)
        
        # Find composite model candidates
        composite_candidates = self._find_composite_model_candidates(all_projects_data)
        
        # Get all fact tables
        all_fact_tables = self._get_all_fact_tables(all_projects_data)
        
        return {
            'common_dimensions': common_dimensions,
            'composite_candidates': composite_candidates,
            'all_fact_tables': all_fact_tables
        }
    
    def _find_common_dimensions(self, all_projects_data):
        """Find dimensions that are common across multiple projects and use ONLY dimension tables"""
        dimension_occurrences = {}  # {(dim_unique_name, dim_label): {projects_data}}
        
        for project_name, project_data in all_projects_data.items():
            for dim_filename, dim_info in project_data['dimensions'].items():
                # Skip dimensions that use ANY fact tables
                if dim_info['uses_fact_table']:
                    continue
                
                primary_dataset_ref = dim_info['primary_dataset']
                if not primary_dataset_ref:
                    continue
                
                # Get dataset info
                dataset_name = primary_dataset_ref.replace('.dataset', '')
                connection_info = self._get_connection_info(primary_dataset_ref, project_data)
                
                key = (dim_info['unique_name'], dim_info['label'])
                if key not in dimension_occurrences:
                    dimension_occurrences[key] = {
                        'projects': [],
                        'best_version': None,
                        'datasets': set()
                    }
                
                # Store project data for this dimension
                project_dim_data = {
                    'project_name': project_name,
                    'dataset_name': dataset_name,
                    'connection_id': connection_info,
                    'hierarchies_count': dim_info['hierarchies_count'],
                    'levels_count': dim_info['levels_count'],
                    'attributes_count': dim_info['attributes_count'],
                    'file_path': dim_info['file_path'],
                    'total_score': dim_info['hierarchies_count'] * 1000 + 
                                   dim_info['levels_count'] * 100 + 
                                   dim_info['attributes_count']
                }
                
                dimension_occurrences[key]['projects'].append(project_dim_data)
                
                # Track all datasets used by this dimension
                for ds_ref in dim_info['dataset_refs']:
                    ds_name = ds_ref.replace('.dataset', '')
                    ds_info = project_data['datasets'].get(ds_ref, {})
                    dimension_occurrences[key]['datasets'].add((
                        ds_name,
                        ds_info.get('connection_id', 'Unknown'),
                        ds_info.get('file_path', '')
                    ))
                
                # Update best version if this one is better
                current_best = dimension_occurrences[key]['best_version']
                if (not current_best or 
                    project_dim_data['total_score'] > current_best['total_score']):
                    dimension_occurrences[key]['best_version'] = project_dim_data
        
        # Build final common dimensions list
        common_dimensions = []
        for (dim_unique_name, dim_label), data in dimension_occurrences.items():
            if len(data['projects']) > 1:  # Shared across multiple projects
                best_version = data['best_version']
                
                # Prepare dataset info
                datasets_info = []
                for ds_name, ds_conn, ds_path in data['datasets']:
                    datasets_info.append({
                        'dataset_name': ds_name,
                        'connection_id': ds_conn.replace('.connection', ''),
                        'file_path': ds_path
                    })
                
                common_dimensions.append({
                    'dimension_unique_name': dim_unique_name,
                    'dimension_label': dim_label,
                    'dataset_name': best_version['dataset_name'],
                    'connection_id': best_version['connection_id'].replace('.connection', ''),
                    'count': len(data['projects']),
                    'best_version': best_version,
                    'hierarchies_count': best_version['hierarchies_count'],
                    'levels_count': best_version['levels_count'],
                    'attributes_count': best_version['attributes_count'],
                    'datasets': datasets_info,
                    'projects': [p['project_name'] for p in data['projects']]
                })
        
        # Sort by count descending
        common_dimensions.sort(key=lambda x: x['count'], reverse=True)
        return common_dimensions
    
    def _get_connection_info(self, dataset_ref, project_data):
        """Get connection information for a dataset from project data"""
        if dataset_ref and dataset_ref in project_data['datasets']:
            conn_id = project_data['datasets'][dataset_ref].get('connection_id', 'Unknown')
            return conn_id
        return "Unknown"
    
    def _find_composite_model_candidates(self, all_projects_data):
        """Find projects that use multiple fact tables"""
        composite_candidates = []
        
        for project_name, project_data in all_projects_data.items():
            fact_count = len(project_data['fact_datasets'])
            if fact_count > 1:
                # Get readable fact table names
                fact_tables = []
                for fact_ref in project_data['fact_datasets']:
                    if fact_ref in project_data['datasets']:
                        fact_tables.append(project_data['datasets'][fact_ref].get('table', fact_ref))
                    else:
                        fact_tables.append(fact_ref.replace('.dataset', ''))
                
                composite_candidates.append({
                    'project_name': project_name,
                    'fact_table_count': fact_count,
                    'fact_tables': fact_tables
                })
        
        return composite_candidates
    
    def _get_all_fact_tables(self, all_projects_data):
        """Get all fact tables across all projects"""
        all_fact_tables = set()
        for project_data in all_projects_data.values():
            for fact_ref in project_data['fact_datasets']:
                if fact_ref in project_data['datasets']:
                    table_name = project_data['datasets'][fact_ref].get('table', fact_ref)
                    all_fact_tables.add(table_name)
                else:
                    all_fact_tables.add(fact_ref.replace('.dataset', ''))
        return sorted(list(all_fact_tables))
        
    def _read_yaml_file(self, file_path):
        """Read entire YAML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error reading {file_path}: {e}")
            return {}
# [file content end]