# tabs/queries_input.py (updated)
import tkinter as tk
from tkinter import ttk, scrolledtext
from queries.query_history_window import QueryHistoryWindow
from queries.query_history_service import QueryHistoryService

class QueryInput:
    def __init__(self, parent, on_query_type_change=None, on_execute=None):
        self.parent = parent
        self.on_query_type_change = on_query_type_change
        self.on_execute = on_execute
        self.history_service = None
        self.history_window = None  # Store reference to history window
        
        self.query_type_var = tk.StringVar(value="MDX")
        self.use_agg_var = tk.BooleanVar(value=True)  # Default checked
        self.use_cache_var = tk.BooleanVar(value=True)  # Default checked
        self.query_text = None
        self.current_catalog = ""
        self.current_cube = ""
        self.current_catalog_id = ""
        self.current_cube_id = ""
        
        self.create_widgets()
        self.setup_bindings()
    
    def create_widgets(self):
        """Create query input widgets using grid geometry manager"""
        # Main frame
        self.main_frame = ttk.Frame(self.parent)
        
        # Configure grid weights for main frame
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)  # Text area row
        
        # Query type selection and options in one row
        options_frame = ttk.Frame(self.main_frame)
        options_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # Configure options_frame columns
        options_frame.columnconfigure(0, weight=0)  # Query Type label
        options_frame.columnconfigure(1, weight=0)  # MDX radio
        options_frame.columnconfigure(2, weight=0)  # SQL radio
        options_frame.columnconfigure(3, weight=0)  # Separator
        options_frame.columnconfigure(4, weight=0)  # Use Agg checkbox
        options_frame.columnconfigure(5, weight=0)  # Use Cache checkbox
        options_frame.columnconfigure(6, weight=1)  # Spacer
        
        # Query Type label and radio buttons
        ttk.Label(options_frame, text="Query Type:").grid(row=0, column=0, padx=(0, 5))
        
        self.mdx_radio = ttk.Radiobutton(options_frame, text="MDX", 
                                       variable=self.query_type_var, 
                                       value="MDX")
        self.mdx_radio.grid(row=0, column=1, padx=(0, 10))
        
        self.sql_radio = ttk.Radiobutton(options_frame, text="SQL", 
                                       variable=self.query_type_var, 
                                       value="SQL")
        self.sql_radio.grid(row=0, column=2, padx=(0, 20))
        
        # Add separator
        ttk.Separator(options_frame, orient="vertical").grid(row=0, column=3, padx=10, sticky="ns")
        
        # Use Agg checkbox
        self.use_agg_checkbox = ttk.Checkbutton(
            options_frame, 
            text="Use Agg", 
            variable=self.use_agg_var
        )
        self.use_agg_checkbox.grid(row=0, column=4, padx=(0, 10))
        
        # Use Cache checkbox
        self.use_cache_checkbox = ttk.Checkbutton(
            options_frame, 
            text="Use Cache", 
            variable=self.use_cache_var
        )
        self.use_cache_checkbox.grid(row=0, column=5)
        
        # Query label
        ttk.Label(self.main_frame, text="Query:").grid(row=1, column=0, sticky="w", pady=(0, 5))
        
        # Query text area
        text_frame = ttk.Frame(self.main_frame)
        text_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 5))
        
        # Configure text frame to expand
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.query_text = tk.Text(text_frame, wrap=tk.WORD, height=15)
        self.query_text.grid(row=0, column=0, sticky="nsew")
        
        # Add scrollbars
        text_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.query_text.yview)
        text_scrollbar.grid(row=0, column=1, sticky="ns")
        self.query_text.configure(yscrollcommand=text_scrollbar.set)
        
        # Button frame for execute and history
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=3, column=0, pady=10)
        
        self.execute_btn = ttk.Button(button_frame, text="Execute Query", 
                                    command=self.execute_query)
        self.execute_btn.pack(side="left", padx=(0, 10))
        
        # Add history button next to Execute
        self.history_btn = ttk.Button(
            button_frame,
            text="Query History",
            command=self.show_query_history
        )
        self.history_btn.pack(side="left")
    
    # Add new methods to get checkbox values
    def get_use_agg(self):
        """Get Use Agg checkbox value"""
        return self.use_agg_var.get()
    
    def get_use_cache(self):
        """Get Use Cache checkbox value"""
        return self.use_cache_var.get()
    
    def set_use_agg(self, value):
        """Set Use Agg checkbox value"""
        self.use_agg_var.set(value)
    
    def set_use_cache(self, value):
        """Set Use Cache checkbox value"""
        self.use_cache_var.set(value)
    
    def setup_bindings(self):
        """Setup event bindings"""
        if self.on_query_type_change:
            self.mdx_radio.configure(command=self.on_query_type_change)
            self.sql_radio.configure(command=self.on_query_type_change)
    
    def show_query_history(self):
        """Show query history window - allow multiple windows"""
        # Initialize history service if not already done
        if not self.history_service:
            self.history_service = QueryHistoryService()
        
        # Check if there's already a history window
        # We'll store a reference on the parent window
        parent_window = self.main_frame.winfo_toplevel()
        
        # Try to reuse existing window if it exists
        if hasattr(parent_window, 'history_window_reference'):
            try:
                # Check if window still exists
                if parent_window.history_window_reference.window.winfo_exists():
                    parent_window.history_window_reference.window.lift()
                    parent_window.history_window_reference.window.focus_set()
              #      print("[DEBUG] Reusing existing history window")
                    return
            except:
                # Window was closed, clear reference
                parent_window.history_window_reference = None
        
        # Create and show new history window
       #print("[DEBUG] Creating new query history window")
        history_window = QueryHistoryWindow(
            parent_window,
            self.history_service,
            on_re_run_query=self.re_run_query_from_history
        )
        
        # Store reference on parent window
        parent_window.history_window_reference = history_window
        
        # Refresh with current IDs if available
        if self.current_catalog_id and self.current_cube_id:
            history_window.refresh_history(
                catalog_name=self.current_catalog,
                cube_name=self.current_cube,
                catalog_id=self.current_catalog_id,
                cube_id=self.current_cube_id
            )
        else:
            # Fallback to just names
            history_window.refresh_history(
                catalog_name=self.current_catalog,
                cube_name=self.current_cube
            )
    
# tabs/queries_input.py
    def re_run_query_from_history(self, query_text, query_language):
        """Re-run query from history"""
        #print(f"[DEBUG] Received query from history:")
        #print(f"Language: {query_language}")
        #print(f"Query text length: {len(query_text)} chars")
        
        if query_text and query_text.strip():
            # Store the query text for comparison
            old_query = self.get_query()
            
            # Load the query into the input area WITHOUT triggering sample update
            self.set_query(query_text)
            
            # Get the new query to verify it was set
            new_query = self.get_query()
           # print(f"[DEBUG] Old query (first 50 chars): {old_query[:50]}...")
           # print(f"[DEBUG] New query (first 50 chars): {new_query[:50]}...")
            
            if new_query != query_text.strip():
            #    print("[ERROR] Query not properly set in text widget!")
                # Try alternative method
                self.query_text.delete("1.0", "end")
                self.query_text.insert("1.0", query_text)
                self.query_text.update_idletasks()
            
            # Set query type based on language WITHOUT triggering sample update
            current_type = self.get_query_type()
            new_type = "MDX" if query_language == "MDX" else "SQL"
            
            if current_type != new_type:
                # Set the type without calling the callback
                self.query_type_var.set(new_type)
               # print(f"[DEBUG] Changed query type from {current_type} to {new_type}")
            else:
               # print("[DEBUG] Query type unchanged: {current_type}")
               pass
            
            # Force the parent window to update
            self.main_frame.update()
            
            # Execute the query through the main execute function
            # This will use the current catalog/cube selection
           #print("[DEBUG] About to execute query...")
            self.execute_query()
        else:
            print("[ERROR] No query text received from history")
    
    def execute_query(self):
        """Execute query callback"""
       # print(f"[DEBUG] execute_query called from QueryInput")
       # print(f"[DEBUG] Current query in text widget (first 100 chars): {self.get_query()[:100]}...")
        
        if self.on_execute:
        #    print(f"[DEBUG] Calling on_execute callback")
            self.on_execute()
        else:
            print("[ERROR] on_execute callback not set!")
    
    def get_query(self):
        """Get the current query text"""
        try:
            query = self.query_text.get("1.0", "end-1c").strip()
            return query
        except Exception as e:
            print(f"[ERROR] Failed to get query text: {e}")
            return ""
    
    def set_query(self, query):
        """Set the query text"""
        self.query_text.delete("1.0", "end")
        self.query_text.insert("1.0", query)
        
        # Force update and focus
        self.query_text.update()
        self.query_text.focus_set()
        self.query_text.see("1.0")  # Scroll to top
    
    def get_query_type(self):
        """Get the current query type"""
        return self.query_type_var.get()
    
    def set_query_type(self, query_type):
        """Set the query type"""
        self.query_type_var.set(query_type)
    
    # tabs/queries_input.py
    def set_sample_queries(self, mdx_sample, sql_sample):
        """Set sample queries for both types"""
        self.mdx_sample = mdx_sample
        self.sql_sample = sql_sample
        
        # Only set sample query if current query is empty or is a sample query
        current_query = self.get_query()
        if not current_query or current_query.strip() == "" or "Sample" in current_query:
            # Set initial sample based on current type
            if self.get_query_type() == "MDX":
                self.set_query(mdx_sample)
            else:
                self.set_query(sql_sample)
    
    def update_sample_for_cube(self, catalog, cube, catalog_id=None, cube_id=None):
        """Update sample queries with actual cube name"""
        self.current_catalog = catalog
        self.current_cube = cube
        self.current_catalog_id = catalog_id or ""
        self.current_cube_id = cube_id or ""
        
        if hasattr(self, 'mdx_sample') and hasattr(self, 'sql_sample'):
            mdx_updated = self.mdx_sample.replace("YourCubeName", cube)
            sql_updated = self.sql_sample.replace("YourCubeName", cube)
            self.set_sample_queries(mdx_updated, sql_updated)
    
    def get_widget(self):
        """Get the main widget"""
        return self.main_frame