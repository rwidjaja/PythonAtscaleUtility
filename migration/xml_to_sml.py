import os
import requests
import time
from common import append_log

class XmlToSmlConverter:
    def __init__(self, config, log_ref_container):
        self.config = config
        self.log_ref_container = log_ref_container

    def save_xml(self, xml_content, filename):
        """Save XML content to workspace"""
        try:
            # Use root directory as base for workspace
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.config.get("workspace", "working_dir")
            
            # If workspace is relative, make it relative to root directory
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
                
            xml_dir = os.path.join(workspace, "xml")
            os.makedirs(xml_dir, exist_ok=True)
            
            xml_path = os.path.join(xml_dir, filename)
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            append_log(self.log_ref_container[0], f"Saved XML to {xml_path}")
            return xml_path
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error saving XML: {e}")
            return None

    def convert_xml_to_sml(self, xml_filename, formatted_xml_filename, project_name):
        """Convert XML to SML using Java service - with better file detection and Java log tailing"""
        
        try:
            # Use root directory as base for workspace
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.config.get("workspace", "working_dir")
            
            # If workspace is relative, make it relative to root directory
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
                
            xml_dir = os.path.join(workspace, "xml")
            sml_dir = os.path.join(workspace, "sml")
            
            # Create project-specific SML directory
            project_sml_dir = os.path.join(sml_dir, project_name)
            # In the convert_xml_to_sml method, add this after creating the project_sml_dir:
            
            import re
            # Sanitize project name for directory to match Git repo naming
            sanitized_project_name = re.sub(r'[^\w\s-]', '', project_name)
            sanitized_project_name = re.sub(r'[-\s]+', '-', sanitized_project_name)
            sanitized_project_name = sanitized_project_name.lower().strip('-')

            # Use sanitized name for the directory
            project_sml_dir = os.path.join(sml_dir, sanitized_project_name)
            os.makedirs(project_sml_dir, exist_ok=True)
            
            # Construct JSON payload similar to bash script
            payload = {
                "atscale-server": {
                    "apihost": self.config["host"],
                    "dchost": self.config["host"],
                    "authhost": self.config["host"],
                    "authport": 10500,
                    "dcport": 10500,
                    "apiport": 10502,
                    "username": self.config["username"],
                    "password": self.config["password"],
                    "disablessl": True,
                    "organizationfilterguid": self.config["organization"],
                    "organizationfiltername": self.config["organization"]
                },
                "inbound-resource": {
                    "location_type": "file",
                    "location": os.path.join(xml_dir, xml_filename),
                    "source_type": "atscale",
                    "hash_type": "short",
                    "write_formatted": os.path.join(xml_dir, formatted_xml_filename)
                },
                "outbound-resource": {
                    "location_type": "directory",
                    "location": project_sml_dir,  # Use project-specific directory
                    "source_type": "sml"
                }
            }
            
            append_log(self.log_ref_container[0], f"Converting XML to SML for {project_name}, output to {project_sml_dir}")
            
            # Get initial Java log position to tail new messages
            java_log_path = os.path.join(root_dir, "logs", "java_service.log")
            initial_log_position = self._get_file_size(java_log_path)
            
            response = requests.post(
                "http://localhost:8000/atscale-sml-service/convert",
                json=payload,
                auth=('admin', '@scale800'),
                timeout=120  # Increase timeout for large conversions
            )
            
            # Wait a moment for Java service to complete file operations
            time.sleep(2)
            
            # Tail Java service logs for this conversion
            self._tail_java_logs(java_log_path, initial_log_position)
            
            if response.status_code == 200:
                # Check if SML files were actually created - look for ANY files, not just .sml
                all_files = []
                for root, dirs, files in os.walk(project_sml_dir):
                    for file in files:
                        all_files.append(os.path.join(root, file))
                
                # Also check for any files in subdirectories
                if all_files:
                    append_log(self.log_ref_container[0], f"Java service reported success. Found {len(all_files)} files in output directory:")
                    for file_path in all_files:
                        file_size = os.path.getsize(file_path)
                        append_log(self.log_ref_container[0], f"  - {os.path.basename(file_path)} ({file_size} bytes)")
                    
                    # Count .sml files specifically
                    sml_files = [f for f in all_files if f.lower().endswith('.sml')]
                    append_log(self.log_ref_container[0], f"Successfully converted XML to SML for {project_name}. Found {len(sml_files)} .sml files out of {len(all_files)} total files")
                    return True
                else:
                    append_log(self.log_ref_container[0], f"Java service reported success but no files found in {project_sml_dir}")
                    # Check if the directory structure was created
                    dir_contents = list(os.walk(project_sml_dir))
                    if len(dir_contents) > 1 or (len(dir_contents) == 1 and dir_contents[0][1]):  # Has subdirectories
                        append_log(self.log_ref_container[0], f"Directory structure created with subfolders: {[d for d in dir_contents[0][1]]}")
                        return True
                    else:
                        append_log(self.log_ref_container[0], "No files or subdirectories found, conversion may have failed")
                        return False
            else:
                append_log(self.log_ref_container[0], f"Conversion failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error converting XML to SML: {e}")
            return False

    def _get_file_size(self, file_path):
        """Get current file size for tailing"""
        try:
            if os.path.exists(file_path):
                return os.path.getsize(file_path)
            return 0
        except:
            return 0

    def _tail_java_logs(self, log_path, start_position):
        """Tail Java service logs from the given position"""
        try:
            if not os.path.exists(log_path):
                append_log(self.log_ref_container[0], f"Java log file not found: {log_path}")
                return
                
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(start_position)
                new_content = f.read().strip()
                if new_content:
                    append_log(self.log_ref_container[0], "Java Service Logs (from conversion):")
                    for line in new_content.split('\n'):
                        if line.strip():
                            append_log(self.log_ref_container[0], f"  Java: {line.strip()}")
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error reading Java logs: {e}")