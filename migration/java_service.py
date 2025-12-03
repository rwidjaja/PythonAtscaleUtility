import os
import subprocess
import time
import threading
from common import append_log

class JavaServiceManager:
    def __init__(self, config, log_ref_container):
        self.config = config
        self.log_ref_container = log_ref_container
        self.java_process = None
        self.java_log_file = None
        
    def ensure_java_service_running(self):
        """Ensure the Java ML service is running - run as background daemon"""
        # Check if port 8000 is already listening
        if self._is_port_listening(8000):
            append_log(self.log_ref_container[0], "Java ML service is already running on port 8000")
            return True
        
        # Start the Java service as background daemon
        try:
            # Look for JAR in the root directory (where config.json and main.py are located)
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            jar_path = os.path.join(root_dir, "atscale-sml-service-1.0-SNAPSHOT_2025_7.jar")
            
            if not os.path.exists(jar_path):
                append_log(self.log_ref_container[0], f"Java JAR not found at: {jar_path}")
                append_log(self.log_ref_container[0], "Please ensure atscale-sml-service-1.0-SNAPSHOT_2025_7.jar is in the root directory with config.json")
                return False
            
            append_log(self.log_ref_container[0], f"Found Java JAR at: {jar_path}")
            
            # Create log directory and file
            log_dir = os.path.join(root_dir, "logs")
            os.makedirs(log_dir, exist_ok=True)
            self.java_log_file = os.path.join(log_dir, "java_service.log")
            
            cmd = [
                "java", "-jar", jar_path,
                "--server.port=8000",
                "--trigger.api.username=admin",
                "--trigger.api.password=@scale800"
            ]
            
            # Start as background daemon process
            with open(self.java_log_file, 'w') as log_file:
                self.java_process = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    start_new_session=True  # Run as background process group
                )
            
            append_log(self.log_ref_container[0], f"Java service started as background process (PID: {self.java_process.pid})")
            append_log(self.log_ref_container[0], f"Java service logs: {self.java_log_file}")
            
            # Wait for service to start (just check port)
            append_log(self.log_ref_container[0], "Waiting for Java service to start listening on port 8000...")
            for i in range(30):  # Wait up to 30 seconds
                if self._is_port_listening(8000):
                    append_log(self.log_ref_container[0], "Java ML service is now listening on port 8000")
                    return True
                time.sleep(1)
            
            append_log(self.log_ref_container[0], "Java service failed to start listening on port 8000")
            return False
            
        except Exception as e:
            append_log(self.log_ref_container[0], f"Error starting Java service: {e}")
            return False

    def _is_port_listening(self, port):
        """Check if a port is listening (simple socket check)"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result == 0
        except:
            return False

    def _is_java_process_running(self):
        """Check if our Java process is still running"""
        if self.java_process is None:
            return False
        return self.java_process.poll() is None