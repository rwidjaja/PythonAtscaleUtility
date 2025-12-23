# common.py (add these functions)
import os, json, requests, urllib3
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MAX_LOG_LINES = 1000
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

# --- UI helpers ---
def append_log(text_widget, message):
    """Append message to log widget"""
    text_widget.insert("end", message + "\n")
    if int(text_widget.index("end-1c").split(".")[0]) > MAX_LOG_LINES:
        text_widget.delete("1.0", "2.0")
    text_widget.see("end")

def get_instance_type():
    """Return the instance_type from config.json"""
    config = load_config()
    return config.get("instance_type", "installer")

def get_credentials():
    """Return username and password from config.json"""
    config = load_config()
    return config["username"], config["password"]

def make_tab_with_log(notebook, title, content_builder, log_ref_container):
    """Create a tab with content area and log area"""
    frame = ttk.Frame(notebook, padding=12)
    notebook.add(frame, text=title)

    frame.rowconfigure(0, weight=1)
    frame.rowconfigure(1, weight=0, minsize=200)
    frame.columnconfigure(0, weight=1)

    # Content area
    content = ttk.Frame(frame)
    content.grid(row=0, column=0, sticky="nsew")

    # Log area
    log_frame = ttk.Frame(frame)
    log_frame.grid(row=1, column=0, sticky="nsew")

    scrollbar = ttk.Scrollbar(log_frame)
    scrollbar.pack(side="right", fill="y")

    log_text = tk.Text(log_frame, wrap="none", yscrollcommand=scrollbar.set)
    log_text.pack(fill="both", expand=True)
    scrollbar.config(command=log_text.yview)

    # Assign log widget before calling content_builder
    log_ref_container[0] = log_text

    # Now build the tab content
    content_builder(content, log_ref_container)

    return log_text

# --- Config + JWT helpers ---
def load_config():
    """Load configuration from config.json"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

_jwt_cache = None

def get_jwt(force_refresh=False):
    """
    Returns a JWT depending on instance_type (installer vs container).
    Caches the token unless force_refresh=True.
    """
    global _jwt_cache
    if _jwt_cache and not force_refresh:
        return _jwt_cache

    config = load_config()
    host = config["host"]
    username = config["username"]
    password = config["password"]

    if config.get("instance_type") == "installer":
        # Installer flow
        org = config["organization"]
        url = f"https://{host}:10500/{org}/auth"
        resp = requests.get(url, auth=(username, password), verify=False, timeout=15)
        resp.raise_for_status()
        _jwt_cache = resp.text.strip()

    elif config.get("instance_type") == "container":
        # Container flow (OpenID Connect token endpoint)
        url = f"https://{host}/auth/realms/atscale/protocol/openid-connect/token"
        data = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "username": username,
            "password": password,
            "grant_type": "password",
        }
        resp = requests.post(url, data=data, verify=False, timeout=15)
        resp.raise_for_status()
        _jwt_cache = resp.json().get("access_token")

    else:
        raise ValueError(f"Unknown instance_type: {config.get('instance_type')}")

    return _jwt_cache

def clear_jwt_cache():
    """Clear the cached JWT token"""
    global _jwt_cache
    _jwt_cache = None

def show_error(message):
    """Show error message box"""
    messagebox.showerror("Error", message)

def show_info(message):
    """Show info message box"""
    messagebox.showinfo("Information", message)

def show_warning(message):
    """Show warning message box"""
    messagebox.showwarning("Warning", message)

def confirm_dialog(title, message):
    """Show confirmation dialog"""
    return messagebox.askyesno(title, message)