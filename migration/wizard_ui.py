# [file name]: wizard_ui.py
# [file content begin]
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

class WizardUI:
    def __init__(self, controller, log_ref_container):
        self.controller = controller
        self.log_ref_container = log_ref_container
        self.wizard_window = None
        self.progress_var = None
        self.common_tree = None
        self.other_text = None
        self.create_common_btn = None
        self.common_dimensions_data = []
        self.common_name_entry = None
        
    def create_wizard_window(self, parent):
        """Create and return the wizard window"""
        self.wizard_window = tk.Toplevel(parent)
        self.wizard_window.title("Migration Analysis Wizard")
        self.wizard_window.geometry("1200x800")
        self.wizard_window.resizable(True, True)
        
        # Make it modal
        self.wizard_window.transient(parent)
        self.wizard_window.grab_set()
        
        self._build_wizard_ui()
        return self.wizard_window
        
    def _build_wizard_ui(self):
        """Build the wizard user interface"""
        main_frame = ttk.Frame(self.wizard_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title only
        title_label = ttk.Label(main_frame, text="Migration Analysis Wizard", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="5")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.StringVar(value="Starting analysis...")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        progress_label.pack(anchor=tk.W)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Tab 1: Common Dimensions
        common_frame = ttk.Frame(notebook)
        notebook.add(common_frame, text="Common Dimensions")
        self._build_common_dimensions_tab(common_frame)
        
        # Tab 2: Fact Tables & Composite Models
        other_frame = ttk.Frame(notebook)
        notebook.add(other_frame, text="Fact Tables & Composite Models")
        self._build_other_results_tab(other_frame)
        
        # Common Dimensions Creation Frame (at the bottom)
        creation_frame = ttk.LabelFrame(main_frame, text="Create Common Dimensions", padding="10")
        creation_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Name input
        name_frame = ttk.Frame(creation_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(name_frame, text="Common Dimensions Name:").pack(side=tk.LEFT, padx=(0, 10))
        self.common_name_entry = ttk.Entry(name_frame, width=40)
        self.common_name_entry.pack(side=tk.LEFT, padx=(0, 20))
        self.common_name_entry.insert(0, "CommonDimensions")  # Default value
        
        # Info label
        self.creation_info = ttk.Label(name_frame, text="Select dimensions above, enter name, then click Create")
        self.creation_info.pack(side=tk.LEFT)
        
        # Create button
        self.create_common_btn = ttk.Button(creation_frame, text="Create Common Dimensions", 
                                          state="disabled",
                                          command=self.controller.create_common_dimensions)
        self.create_common_btn.pack(side=tk.RIGHT)
        
        # Close button frame
        close_frame = ttk.Frame(main_frame)
        close_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(close_frame, text="Close", 
                  command=self.controller.close_wizard).pack(side=tk.RIGHT)
        
    def _build_common_dimensions_tab(self, parent):
        """Build the common dimensions tab with selectable treeview"""
        # Frame for treeview and scrollbars
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview with checkboxes
        columns = ('selected', 'dataset', 'dimension', 'connection', 'count', 'hier', 'lvl', 'attr')
        self.common_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode='extended')
        
        # Define column headings
        self.common_tree.heading('selected', text='Select')
        self.common_tree.heading('dataset', text='Dataset')
        self.common_tree.heading('dimension', text='Dimension')
        self.common_tree.heading('connection', text='Connection')
        self.common_tree.heading('count', text='Count')
        self.common_tree.heading('hier', text='Hier')
        self.common_tree.heading('lvl', text='Lvl')
        self.common_tree.heading('attr', text='Attr')
        
        # Define column widths
        self.common_tree.column('selected', width=60, anchor='center')
        self.common_tree.column('dataset', width=150, anchor='w')
        self.common_tree.column('dimension', width=200, anchor='w')
        self.common_tree.column('connection', width=120, anchor='w')
        self.common_tree.column('count', width=60, anchor='center')
        self.common_tree.column('hier', width=50, anchor='center')
        self.common_tree.column('lvl', width=50, anchor='center')
        self.common_tree.column('attr', width=50, anchor='center')
        
        # Add scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.common_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.common_tree.xview)
        self.common_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.common_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind click on checkbox column to toggle selection
        self.common_tree.bind('<Button-1>', self._on_tree_click)
        
        # Buttons for selection control
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Select All", 
                  command=self._select_all_dimensions).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Deselect All", 
                  command=self._deselect_all_dimensions).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Invert Selection", 
                  command=self._invert_selection).pack(side=tk.LEFT)
        
        # Label showing count
        self.selection_count_var = tk.StringVar(value="Selected: 0 / 0")
        ttk.Label(button_frame, textvariable=self.selection_count_var).pack(side=tk.RIGHT)
        
    def _build_other_results_tab(self, parent):
        """Build the tab for fact tables and composite models"""
        # Create notebook for subtabs
        sub_notebook = ttk.Notebook(parent)
        sub_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Fact Tables subtab
        fact_frame = ttk.Frame(sub_notebook)
        sub_notebook.add(fact_frame, text="Fact Tables")
        
        fact_text = tk.Text(fact_frame, wrap=tk.WORD, font=("Courier", 10))
        fact_scroll = ttk.Scrollbar(fact_frame, orient="vertical", command=fact_text.yview)
        fact_text.configure(yscrollcommand=fact_scroll.set)
        
        fact_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        fact_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.fact_text = fact_text
        
        # Composite Models subtab
        composite_frame = ttk.Frame(sub_notebook)
        sub_notebook.add(composite_frame, text="Composite Models")
        
        composite_text = tk.Text(composite_frame, wrap=tk.WORD, font=("Courier", 10))
        composite_scroll = ttk.Scrollbar(composite_frame, orient="vertical", command=composite_text.yview)
        composite_text.configure(yscrollcommand=composite_scroll.set)
        
        composite_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        composite_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.composite_text = composite_text
        
    def _on_tree_click(self, event):
        """Handle click on treeview to toggle checkbox"""
        region = self.common_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.common_tree.identify_column(event.x)
            if column == "#1":  # Clicked on the checkbox column
                item = self.common_tree.identify_row(event.y)
                if item:
                    current_value = self.common_tree.set(item, 'selected')
                    new_value = "☐" if current_value == "☑" else "☑"
                    self.common_tree.set(item, 'selected', new_value)
                    self._update_selection_count()
    
    def _select_all_dimensions(self):
        """Select all dimensions in the tree"""
        for item in self.common_tree.get_children():
            self.common_tree.set(item, 'selected', '☑')
        self._update_selection_count()
    
    def _deselect_all_dimensions(self):
        """Deselect all dimensions in the tree"""
        for item in self.common_tree.get_children():
            self.common_tree.set(item, 'selected', '☐')
        self._update_selection_count()
    
    def _invert_selection(self):
        """Invert the current selection"""
        for item in self.common_tree.get_children():
            current_value = self.common_tree.set(item, 'selected')
            new_value = "☐" if current_value == "☑" else "☑"
            self.common_tree.set(item, 'selected', new_value)
        self._update_selection_count()
    
    def _update_selection_count(self):
        """Update the selection count label"""
        total = len(self.common_tree.get_children())
        selected = 0
        for item in self.common_tree.get_children():
            if self.common_tree.set(item, 'selected') == '☑':
                selected += 1
        self.selection_count_var.set(f"Selected: {selected} / {total}")
        
        # Enable/disable create button based on selection
        if selected > 0 and self.common_name_entry.get().strip():
            self.create_common_btn.config(state="normal")
            self.creation_info.config(text=f"Ready to create with {selected} selected dimension(s)")
        else:
            self.create_common_btn.config(state="disabled")
            if selected == 0:
                self.creation_info.config(text="Please select at least one dimension")
            else:
                self.creation_info.config(text="Please enter a name for common dimensions")
        
    def load_selected_projects(self, project_names):
        """Load the selected projects - now just update progress"""
        self.update_progress(f"Analyzing {len(project_names)} projects...")
            
    def update_progress(self, message):
        """Update the progress message"""
        self.progress_var.set(message)
        
    def disable_controls(self):
        """Disable UI controls during analysis"""
        if self.create_common_btn:
            self.create_common_btn.config(state="disabled")
        self.creation_info.config(text="Analysis in progress...")
        
    def enable_controls(self):
        """Enable the UI controls"""
        # Enable button if we have common dimensions and selections
        if self.common_dimensions_data:
            # Check if we have any selections
            if self.common_tree and self.common_name_entry.get().strip():
                selected = 0
                for item in self.common_tree.get_children():
                    if self.common_tree.set(item, 'selected') == '☑':
                        selected += 1
                if selected > 0:
                    self.create_common_btn.config(state="normal")
                    self.creation_info.config(text=f"Ready to create with {selected} selected dimension(s)")
                else:
                    self.creation_info.config(text="Please select at least one dimension")
            else:
                self.creation_info.config(text="Please select dimensions and enter a name")
        
    def display_results(self, analysis_results):
        """Display the analysis results with selectable dimensions"""
        self.progress_var.set("Analysis complete!")
        
        # Clear previous data
        self.common_dimensions_data = []
        if self.common_tree:
            for item in self.common_tree.get_children():
                self.common_tree.delete(item)
        
        # Store analysis results for later use
        self.analysis_results = analysis_results
        
        # Process common dimensions
        common_dimensions = analysis_results.get('common_dimensions', [])
        composite_candidates = analysis_results.get('composite_candidates', [])
        all_fact_tables = analysis_results.get('all_fact_tables', [])
        
        # Store common dimensions data
        self.common_dimensions_data = common_dimensions
        
        # Display Common Dimensions in treeview
        if common_dimensions and self.common_tree:
            for idx, data in enumerate(common_dimensions):
                dataset = data['dataset_name'] or 'Unknown'
                dimension = data['dimension_label']
                connection = data['connection_id'].replace('.connection', '')
                count = str(data['count'])
                hierarchies = str(data.get('hierarchies_count', 0))
                levels = str(data.get('levels_count', 0))
                attributes = str(data.get('attributes_count', 0))
                
                # Insert with checkbox unchecked by default
                item_id = str(idx)
                self.common_tree.insert('', 'end', iid=item_id,
                    values=('☐', dataset, dimension, connection, count, 
                           hierarchies, levels, attributes))
            
            # Auto-select all by default
            self._select_all_dimensions()
        
        # Display Fact Tables
        if all_fact_tables and hasattr(self, 'fact_text'):
            self.fact_text.delete(1.0, tk.END)
            self.fact_text.insert(tk.END, "FACT TABLES FOUND\n")
            self.fact_text.insert(tk.END, "=" * 50 + "\n\n")
            for fact_table in all_fact_tables:
                self.fact_text.insert(tk.END, f"• {fact_table}\n")
            
            if not all_fact_tables:
                self.fact_text.insert(tk.END, "No fact tables found.\n")
        
        # Display Composite Model Candidates
        if hasattr(self, 'composite_text'):
            self.composite_text.delete(1.0, tk.END)
            
            if composite_candidates:
                self.composite_text.insert(tk.END, "COMPOSITE MODEL CANDIDATES\n")
                self.composite_text.insert(tk.END, "=" * 80 + "\n\n")
                
                for candidate in composite_candidates:
                    self.composite_text.insert(tk.END, f"Project: {candidate['project_name']}\n")
                    self.composite_text.insert(tk.END, f"Fact Tables Count: {candidate['fact_table_count']}\n")
                    self.composite_text.insert(tk.END, f"Fact Tables: {', '.join(candidate['fact_tables'])}\n")
                    self.composite_text.insert(tk.END, "→ This project uses multiple fact tables and may benefit from a composite model.\n\n")
            else:
                self.composite_text.insert(tk.END, "No candidate for semantic modeling (no projects with multiple fact tables)\n")
        
        # Enable controls if we have common dimensions
        self.enable_controls()
    
    def get_selected_dimensions(self):
        """Get list of selected dimension data"""
        selected_dimensions = []
        
        if not self.common_tree:
            return selected_dimensions
        
        for item in self.common_tree.get_children():
            if self.common_tree.set(item, 'selected') == '☑':
                # Get the index from item id
                try:
                    idx = int(item)
                    if idx < len(self.common_dimensions_data):
                        selected_dimensions.append(self.common_dimensions_data[idx])
                except ValueError:
                    pass
        
        return selected_dimensions
    
    def get_common_name(self):
        """Get the common dimensions name from entry"""
        return self.common_name_entry.get().strip()
    
    def update_creation_info(self, message, is_error=False):
        """Update the creation info label"""
        if is_error:
            self.creation_info.config(text=f"Error: {message}", foreground="red")
        else:
            self.creation_info.config(text=message, foreground="black")
    
    def set_create_button_state(self, state):
        """Set the state of the create button"""
        self.create_common_btn.config(state=state)
# [file content end]