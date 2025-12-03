import tkinter as tk
from tkinter import ttk
from common import append_log, load_config
from api.folders import get_folders
from overview.overview_semantic import SemanticParser

def build_tab(content, log_ref_container):
    config = load_config()
    host = config["host"]
    org = config["organization"]

    content.rowconfigure(0, weight=3)
    content.rowconfigure(1, weight=2)
    content.columnconfigure(0, weight=1)
    content.columnconfigure(1, weight=1)

    # Window 1: Treeview (folders/subfolders/projects)
    tree = ttk.Treeview(content)
    tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    

    # Window 2: Listbox (cubes for selected project)
    listbox_opts = tk.Listbox(content)
    listbox_opts.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

    # Window 3: Results pane
    result_text = tk.Frame(content)   # use a Frame so we can pack a Treeview inside
    result_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
    result_text.grid_propagate(False)   # prevent auto-resize
    result_text.config(height=400, width=600)  # pick a stable size
    tree_inside = ttk.Treeview(result_text, height=15)
    tree_inside.pack(fill="both", expand=True)

    
    # ✅ Checkbox for export
    export_var = tk.BooleanVar(value=False)
    export_chk = tk.Checkbutton(content, text="Export to Excel", variable=export_var)
    export_chk.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)

    node_meta = {}
    cube_id_map = {}
    project_id_map = {}

    # Fetch data
    try:
        from common import get_jwt
        jwt = get_jwt()
        append_log(log_ref_container[0], "JWT acquired.")
        folders_json = get_folders(host, org, jwt)
        append_log(log_ref_container[0], "Folders retrieved.")
    except Exception as e:
        append_log(log_ref_container[0], f"Error fetching data: {e}")
        return

    # Build tree
    root_obj = folders_json.get("response", {})
    def add_folder(parent_id, folder_obj):
        for cf in folder_obj.get("child_folders", []) or []:
            fid = tree.insert(parent_id, "end", text=cf.get("name", "Unnamed"), open=False)
            node_meta[fid] = {"type": "folder", "data": cf}
            add_folder(fid, cf)
        for item in folder_obj.get("items", []) or []:
            if item.get("type") == "Project":
                proj_name = item.get("caption") or item.get("name") or "Project"
                pid = tree.insert(parent_id, "end", text=proj_name, open=False)
                node_meta[pid] = {"type": "project", "data": item}

    root_id = tree.insert("", "end", text=root_obj.get("name", "ROOT"), open=True)
    node_meta[root_id] = {"type": "folder", "data": root_obj}
    add_folder(root_id, root_obj)

    # Initialize semantic parser
    semantic_parser = SemanticParser(host, org, log_ref_container)

    # Handlers
    def on_tree_select(_event):
        sel = tree.selection()
        if not sel:
            return
        item_id = sel[0]
        meta = node_meta.get(item_id, {})
        listbox_opts.delete(0, "end")

        if meta.get("type") == "project":
            project = meta["data"]
            cubes = project.get("cubes", []) or []
            if not cubes:
                append_log(log_ref_container[0], f"Project '{tree.item(item_id,'text')}' has no cubes.")
                return
            for c in cubes:
                label = c.get("caption") or c.get("name") or "Cube"
                listbox_opts.insert("end", label)
                cube_id_map[label] = c.get("id")
                project_id_map[label] = project.get("id")
            append_log(log_ref_container[0], f"Project selected: {tree.item(item_id,'text')}; cubes listed.")
        else:
            append_log(log_ref_container[0], f"Folder selected: {tree.item(item_id,'text')}")

    def on_option_select(event):
        sel = listbox_opts.curselection()
        if not sel:
            return
            
        cube_label = listbox_opts.get(sel[0])
        cube_id = cube_id_map.get(cube_label)
        project_id = project_id_map.get(cube_label)
        
        if not cube_id or not project_id:
            append_log(log_ref_container[0], "Missing cube_id or project_id.")
            return
            
        semantic_parser.process_cube_data(
            cube_label, 
            cube_id, 
            project_id, 
            jwt, 
            export_var.get(), 
            result_text
        )
    
    tree.bind("<<TreeviewSelect>>", on_tree_select)
    listbox_opts.bind("<<ListboxSelect>>", on_option_select)