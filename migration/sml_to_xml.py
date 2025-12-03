import os
import requests
from common import append_log, get_jwt

class SmlToXmlConverter:
    def __init__(self, config, log_ref_container):
        self.config = config
        self.log_ref_container = log_ref_container

    def convert_sml_to_xml(self, project_name, output_xml_filename):
        """Convert SML to XML using Java service (reverse conversion)"""
        try:
            # Use root directory as base for workspace
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.config.get("workspace", "working_dir")
            
            # If workspace is relative, make it relative to root directory
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
                
            git_dir = os.path.join(workspace, "git_repos")
            sml_dir = os.path.join(git_dir, project_name)
            xml_dir = os.path.join(workspace, "xml")
            os.makedirs(xml_dir, exist_ok=True)
            
            # Construct JSON payload for reverse conversion
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
                    "location_type": "directory",
                    "location": sml_dir,
                    "source_type": "sml"
                },
                "outbound-resource": {
                    "location_type": "file",
                    "location": os.path.join(xml_dir, output_xml_filename),
                    "source_type": "atscale",
                    "hash_type": "short-hash"
                }
            }
            
            append_log(self.log_ref_container[0], f"Converting SML to XML for {project_name}, output to {os.path.join(xml_dir, output_xml_filename)}")
            
            response = requests.post(
                "http://localhost:8000/atscale-sml-service/convert",
                json=payload,
                auth=('admin', '@scale800'),
                timeout=120
            )
            
            if response.status_code == 200:
                # Check if XML file was created
                xml_path = os.path.join(xml_dir, output_xml_filename)
                if os.path.exists(xml_path):
                    append_log(self.log_ref_container[0], f"Successfully converted SML to XML for {project_name}")
                    return True
                else:
                    append_log(self.log_ref_container[0], f"Conversion succeeded but XML file not found at {xml_path}")
                    return False
            else:
                append_log(self.log_ref_container[0], f"Reverse conversion failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error converting SML to XML: {e}")
            return False

    def import_xml_to_atscale(self, project_name):
        """Import XML file to AtScale"""
        try:
            # Use root directory as base for workspace
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace = self.config.get("workspace", "working_dir")
            
            # If workspace is relative, make it relative to root directory
            if not os.path.isabs(workspace):
                workspace = os.path.join(root_dir, workspace)
                
            xml_dir = os.path.join(workspace, "xml")
            xml_file = os.path.join(xml_dir, f"{project_name}.xml")
            
            if not os.path.exists(xml_file):
                append_log(self.log_ref_container[0], f"XML file not found: {xml_file}")
                return False
            
            jwt = get_jwt()
            host = self.config["host"]
            org = self.config["organization"]
            
            url = f"https://{host}:10500/api/1.0/org/{org}/file/import"
            headers = {
                "Authorization": f"Bearer {jwt}",
            }
            
            # Prepare multipart form data
            files = {
                'file': (f"{project_name}.xml", open(xml_file, 'rb'), 'application/xml')
            }
            data = {
                'key': 'key1=value1'
            }
            
            response = requests.post(url, headers=headers, files=files, data=data, verify=False, timeout=30)
            response.raise_for_status()
            
            append_log(self.log_ref_container[0], f"Successfully imported XML for project {project_name}")
            return True
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error importing XML to AtScale: {e}")
            return False