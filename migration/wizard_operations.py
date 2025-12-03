# [file name]: wizard_operations.py
# [file content begin]
import os
from common import append_log

class WizardOperations:
    def __init__(self, config, log_ref_container):
        self.config = config
        self.log_ref_container = log_ref_container
        
    def convert_project_to_sml_only(self, migration_ops, project_id, project_name, callback):
        """Convert project to SML only, without committing to Git"""
        try:
            # Clean up any existing artifacts for this project first
            migration_ops.cleanup_project_artifacts(project_name)
            
            # Ensure Java service is running
            if not migration_ops.ensure_java_service_running():
                append_log(self.log_ref_container[0], "Cannot proceed without Java ML service")
                callback(False, project_name)
                return

            append_log(self.log_ref_container[0], f"Converting project '{project_name}' to SML (no Git commit)")
            
            # Step 1: Export XML from AtScale
            xml_content = migration_ops._export_xml(project_id)
            if not xml_content:
                append_log(self.log_ref_container[0], f"✗ Failed to export XML for project {project_name}")
                callback(False, project_name)
                return
            
            # Step 2: Save XML to workspace
            xml_filename = f"{project_id}.xml"
            formatted_xml_filename = f"{project_id}_formatted.xml"
            xml_path = migration_ops.xml_to_sml.save_xml(xml_content, xml_filename)
            
            # Step 3: Convert XML to SML using Java service
            sml_success = migration_ops.xml_to_sml.convert_xml_to_sml(
                xml_filename, formatted_xml_filename, project_name
            )
            
            if sml_success:
                callback(True, project_name)
            else:
                callback(False, project_name)
                
        except Exception as e:
            append_log(self.log_ref_container[0], f"✗ Error converting project to SML: {e}")
            callback(False, project_name)
# [file content end]