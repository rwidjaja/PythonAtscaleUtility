# tabs/query_history_window.py (updated)
"""
Window for displaying and selecting from query history.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext


class QueryHistoryWindow:
    def __init__(self, parent, history_service, on_re_run_query=None):
        self.parent = parent
        self.history_service = history_service
        self.on_re_run_query = on_re_run_query
        self.queries = []
        self.selected_query = None
        
        # Store filter parameters
        self.current_catalog_name = ""
        self.current_cube_name = ""
        self.current_catalog_id = ""
        self.current_cube_id = ""
        
        self.create_window()
        self.create_widgets()
    
    def create_window(self):
        """Create the main window - non-modal"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Query History")
        self.window.geometry("1200x700")
        self.window.minsize(800, 500)
        
        # Configure grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=0)  # Info frame
        self.window.rowconfigure(1, weight=1)  # Treeview
        self.window.rowconfigure(2, weight=0)  # Query text
        self.window.rowconfigure(3, weight=0)  # Buttons
        
        # Make window stay on top but not modal
        self.window.transient(self.parent)  # This keeps it on top of parent
        # REMOVED: self.window.grab_set()  # This makes it modal
        self.window.focus_set()  # Give it focus but don't grab
        
        # Bind to window close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
    def on_window_close(self):
        """Handle window close event"""
        # Clean up any resources if needed
        self.window.destroy()
        # Remove reference to allow reopening
        if hasattr(self.parent, 'history_window_reference'):
            self.parent.history_window_reference = None
    
    def create_widgets(self):
        """Create all widgets in the window"""
        # Info frame
        info_frame = ttk.Frame(self.window)
        info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        info_frame.columnconfigure(0, weight=1)
        
        # Add refresh button at the top
        self.refresh_btn = ttk.Button(info_frame, text="Refresh", command=self.refresh_history)
        self.refresh_btn.pack(side="left", padx=(0, 10))
        
        self.loading_label = ttk.Label(info_frame, text="Click Refresh to load history")
        self.loading_label.pack(side="left")
        
        # Treeview with scrollbars
        tree_frame = ttk.Frame(self.window)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Create scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Create treeview
        columns = [
            "cube_name", "query_id", "user_id", "query_language",
            "query_pre_planning", "query_wall_time", "subquery_count",
            "subqueries_wall", "use_aggregate"
        ]
        
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            height=20
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # Configure scrollbars
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)
        
        # Define column headings and widths
        column_config = {
            "cube_name": ("Cube Name", 150),
            "query_id": ("Query ID", 200),
            "user_id": ("User ID", 100),
            "query_language": ("Language", 80),
            "query_pre_planning": ("Pre-Planning (ms)", 120),
            "query_wall_time": ("Wall Time (ms)", 100),
            "subquery_count": ("# Subqueries", 90),
            "subqueries_wall": ("Subqueries Wall (ms)", 130),
            "use_aggregate": ("Use Aggregate", 100)
        }
        
        for col, (heading, width) in column_config.items():
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, minwidth=80)
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        # Double-click to re-run
        self.tree.bind("<Double-Button-1>", self.on_double_click)
        
        # Query text display
        text_frame = ttk.LabelFrame(self.window, text="Selected Query", padding=10)
        text_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.query_text_display = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=8)
        self.query_text_display.grid(row=0, column=0, sticky="nsew")
        
        # Button frame
        button_frame = ttk.Frame(self.window)
        button_frame.grid(row=3, column=0, sticky="e", padx=10, pady=(0, 10))
        
        self.re_run_btn = ttk.Button(
            button_frame,
            text="Re-Run Query",
            command=self.re_run_selected_query,
            state="disabled"
        )
        self.re_run_btn.pack(side="right", padx=(5, 0))
        
        self.close_btn = ttk.Button(
            button_frame,
            text="Close",
            command=self.window.destroy
        )
        self.close_btn.pack(side="right")
    
    def on_double_click(self, event):
        """Handle double-click on tree item"""
        self.re_run_selected_query()
    
    def refresh_history(self, catalog_name=None, cube_name=None, catalog_id=None, cube_id=None):
        """Refresh the query history list with preserved parameters"""
        # Update stored parameters if provided
        if catalog_name is not None:
            self.current_catalog_name = catalog_name
        if cube_name is not None:
            self.current_cube_name = cube_name
        if catalog_id is not None:
            self.current_catalog_id = catalog_id
        if cube_id is not None:
            self.current_cube_id = cube_id
        
        self.loading_label.config(text="Loading...")
        self.window.update()
        
        # Clear current selection
        self.selected_query = None
        self.re_run_btn.config(state="disabled")
        self.query_text_display.delete("1.0", "end")
        
        # Clear existing items in treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Fetch history with current parameters
        self.queries = self.history_service.fetch_query_history(
            catalog_name=self.current_catalog_name,
            cube_name=self.current_cube_name,
            catalog_id=self.current_catalog_id,
            cube_id=self.current_cube_id
        )
        
        # Update treeview
        self.update_treeview()
        
        if self.current_cube_name:
            self.loading_label.config(text=f"Loaded {len(self.queries)} queries for cube: {self.current_cube_name}")
        else:
            self.loading_label.config(text=f"Loaded {len(self.queries)} queries")
    
    def update_treeview(self):
        """Update treeview with current queries"""
        # Insert new items
        for i, query in enumerate(self.queries):
            values = [
                query["cube_name"],
                query["query_id"][:30] + "..." if len(query["query_id"]) > 30 else query["query_id"],
                query["user_id"],
                query["query_language"],
                f"{query['query_pre_planning']:.2f}",
                f"{query['query_wall_time']:.2f}",
                query["subquery_count"],
                f"{query['subqueries_wall']:.2f}",
                query["use_aggregate"]
            ]
            self.tree.insert("", "end", iid=i, values=values, tags=(query["query_id"],))
    
    def on_tree_select(self, event):
        """Handle tree selection"""
        selection = self.tree.selection()
        if not selection:
            self.re_run_btn.config(state="disabled")
            return
        
        try:
            idx = int(selection[0])
            if 0 <= idx < len(self.queries):
                self.selected_query = self.queries[idx]
                
                # Display query text
                self.query_text_display.delete("1.0", "end")
                query_text = self.selected_query["query_text"]
                if query_text and query_text.strip():
                    self.query_text_display.insert("1.0", query_text)
                    self.re_run_btn.config(state="normal")
                else:
                    self.query_text_display.insert("1.0", "No query text available")
                    self.re_run_btn.config(state="disabled")
        except (ValueError, IndexError) as e:
            print(f"Error selecting query: {e}")
            self.re_run_btn.config(state="disabled")
    
    def re_run_selected_query(self):
        """Re-run selected query"""
        if self.selected_query and self.on_re_run_query:
            query_text = self.selected_query["query_text"]
            query_language = self.selected_query["query_language"]
            
            if not query_text or not query_text.strip():
                # Show error if no query text
                self.loading_label.config(text="Error: No query text available")
                return
            
            # DEBUG: Print what we're about to send
            #print(f"[DEBUG] Sending query to re-run:")
            #print(f"Language: {query_language}")
            #print(f"Query text (first 200 chars): {query_text[:200]}...")
            
            # Call the re-run function
            try:
                self.on_re_run_query(query_text, query_language)
                self.loading_label.config(text="Query sent to main window for execution")
            except Exception as e:
                self.loading_label.config(text=f"Error: {str(e)}")
                print(f"[ERROR] Failed to re-run query: {e}")