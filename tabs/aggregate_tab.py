# tabs/aggregate_tab.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import tkinter.simpledialog as sd
from typing import Dict, List

from common import append_log, confirm_dialog
from aggregate.ui_components import AggregatesTreeview
from aggregate.operations import AggregateOperations
from aggregate.report_generator import ReportGenerator
from aggregate.rebuild_manager import RebuildManager
from aggregate.build_history import BuildHistory
from aggregate.common_selector import ProjectCubeSelector


def build_tab(parent, log_widget):
    """Build function for the aggregate tab"""
    tab = AggregateTab(parent, log_widget)
    return tab


class AggregateTab:
    def __init__(self, parent, log_widget):
        self.parent = parent
        # Extract Text widget from log_ref_container list
        self.log_widget = log_widget[0] if isinstance(log_widget, list) else log_widget
        self.selected_cube = None
        self.api_client = None
        self.rebuild_manager = RebuildManager()
        self.operations = AggregateOperations()
        self.report_generator = ReportGenerator()
        self.build_history = BuildHistory()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the aggregate management UI"""
        # Main container with grid layout
        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(1, weight=1)
        
        # Top frame for controls
        top_frame = ttk.Frame(self.parent)
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # Project/Cube selector
        selector_frame = ttk.LabelFrame(top_frame, text="Project & Cube Selection", padding=5)
        selector_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Refresh button
        ttk.Button(selector_frame, text="⟳", 
                  command=self.refresh_cubes, width=3).pack(side="left", padx=(0, 5))
        
        # Create selector
        self.selector = ProjectCubeSelector(selector_frame, [self.log_widget], 
                                           self.on_cube_selected)
        self.selector.get_selector_widget().pack(side="left", fill="x", expand=True)
        
        # Control buttons frame (2 rows)
        button_frame = ttk.Frame(top_frame)
        button_frame.pack(side="right")
        
        # Create two rows for buttons
        top_button_frame = ttk.Frame(button_frame)
        top_button_frame.pack(side="top", pady=(0, 2))
        
        bottom_button_frame = ttk.Frame(button_frame)
        bottom_button_frame.pack(side="top")
        
        # First row of buttons
        row1_buttons = [
            ("Rebuild Cube", self.rebuild_cube),
            ("List Aggregates", self.list_aggregates),
            ("Activate", self.activate_selected),
        ]
        
        for i, (text, command) in enumerate(row1_buttons):
            btn = ttk.Button(top_button_frame, text=text, command=command, width=15)
            btn.grid(row=0, column=i, padx=2)
        
        # Second row of buttons
        row2_buttons = [
            ("Deactivate", self.deactivate_selected),
            ("Report", self.generate_report),
            ("History", self.show_build_history),
        ]
        
        for i, (text, command) in enumerate(row2_buttons):
            btn = ttk.Button(bottom_button_frame, text=text, command=command, width=15)
            btn.grid(row=0, column=i, padx=2)
        
        # Status label
        self.status_label = ttk.Label(self.parent, text="No cube selected")
        self.status_label.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        
        # Selection count label
        self.selection_label = ttk.Label(self.parent, text="Selected: 0 aggregates")
        self.selection_label.grid(row=3, column=0, sticky="ew", pady=(0, 5))
        
        # Main content area (split view)
        content_frame = ttk.Frame(self.parent)
        content_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        
        # Configure grid weights for split view
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # Left panel: Aggregates list
        left_frame = ttk.LabelFrame(content_frame, text="Aggregates", padding=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Treeview for aggregates
        self.aggregates_tree = AggregatesTreeview(left_frame, self)
        self.aggregates_tree.pack(fill="both", expand=True)
        
        # Right panel: Details/Results
        right_frame = ttk.LabelFrame(content_frame, text="Details", padding=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # Text widget for displaying results
        self.details_text = tk.Text(right_frame, wrap="word", height=20)
        details_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)
        
        self.details_text.pack(side="left", fill="both", expand=True)
        details_scrollbar.pack(side="right", fill="y")
    
    def refresh_cubes(self):
        """Refresh list of cubes from API"""
        self.selector.refresh_data()
    
    def on_cube_selected(self, cube_data):
        """Handle cube selection from selector"""
        if not cube_data:
            return
            
        self.selected_cube = cube_data
        display_text = f"{cube_data['project_name']} -> {cube_data['cube_name']}"
        
        # Update status label
        self._safe_gui_update(lambda: self.status_label.config(text=f"Selected: {display_text}"))
        
        # Clear aggregates tree and details
        self._safe_gui_update(lambda: self.aggregates_tree.clear())
        self._safe_gui_update(lambda: self.details_text.delete(1.0, tk.END))
        
        # Reset selection count
        self.update_selection_count(0)
        
        self.log(f"✓ Selected: {display_text}")
    
    def update_selection_count(self, count):
        """Update selection count label"""
        self._safe_gui_update(lambda: self.selection_label.config(text=f"Selected: {count} aggregates"))
    
    def rebuild_cube(self):
        """Rebuild selected cube"""
        if not self.selected_cube:
            messagebox.showwarning("No Cube Selected", "Please select a cube first.")
            return
        
        if confirm_dialog("Confirm Rebuild", f"Rebuild cube '{self.selected_cube['cube_name']}'?\nThis may take several minutes."):
            thread = threading.Thread(target=self._rebuild_thread, daemon=True)
            thread.start()
    
    def _rebuild_thread(self):
        """Thread function for rebuild"""
        try:
            self.log(f"Starting rebuild for: {self.selected_cube['cube_name']}")
            result = self.rebuild_manager.execute_rebuild(
                self.selected_cube["project_id"],
                self.selected_cube["cube_id"]
            )
            self.log(f"✓ Rebuild completed: {result}")
        except Exception as e:
            self.log(f"✗ Rebuild failed: {e}")
    
    def list_aggregates(self):
        """List aggregates for selected cube"""
        if not self.selected_cube:
            messagebox.showwarning("No Cube Selected", "Please select a cube first.")
            return
        
        thread = threading.Thread(target=self._list_aggregates_thread, daemon=True)
        thread.start()
    
    def _list_aggregates_thread(self):
        """Thread function to list aggregates"""
        try:
            self.log(f"Fetching aggregates for: {self.selected_cube['cube_name']}")
            
            if not self.api_client:
                from aggregate.api_client import AtScaleAPIClient
                self.api_client = AtScaleAPIClient()
            
            # Clear treeview
            self._safe_gui_update(lambda: self.aggregates_tree.clear())
            
            # Fetch aggregates
            response = self.api_client.get_aggregates_by_cube(
                self.selected_cube["project_id"],
                self.selected_cube["cube_id"]
            )
            
            aggregates_data = response.get("response", {}).get("data", [])
            
            if not aggregates_data:
                self.log("No aggregates found.")
                self._safe_gui_update(lambda: self.details_text.delete(1.0, tk.END))
                self._safe_gui_update(lambda: self.details_text.insert(tk.END, "No aggregates found."))
                return
            
            # Prepare data for GUI update
            tree_data = []
            for agg in aggregates_data:
                agg_id = agg.get("id", "N/A")
                agg_name = agg.get("name", "Unnamed")
                agg_type = agg.get("type", "unknown")
                
                latest_instance = agg.get("latest_instance", {})
                status = latest_instance.get("status", "unknown")
                stats = latest_instance.get("stats", {})
                rows = stats.get("number_of_rows", 0)
                build_time = stats.get("build_duration", 0)
                
                # Format build time
                build_time_str = f"{build_time}ms"
                if build_time > 1000:
                    build_time_str = f"{build_time/1000:.1f}s"
                
                tree_data.append({
                    "id": agg_id,
                    "name": agg_name,
                    "type": agg_type,
                    "status": status,
                    "rows": rows,
                    "build_time": build_time_str,
                    "full_data": agg
                })
            
            # Update GUI in main thread
            self._safe_gui_update(lambda: self._update_aggregates_tree(tree_data))
            
            self.log(f"✓ Loaded {len(aggregates_data)} aggregates")
            
        except Exception as e:
            self.log(f"✗ Error listing aggregates: {e}")
    
    def _update_aggregates_tree(self, tree_data):
        """Update aggregates treeview (called in main thread)"""
        for agg_data in tree_data:
            self.aggregates_tree.add_aggregate(agg_data)
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, f"Found {len(tree_data)} aggregates for {self.selected_cube['cube_name']}")
    
    def activate_selected(self):
        """Activate selected aggregates"""
        selected = self.aggregates_tree.get_selected_aggregates()
        if not selected:
            messagebox.showwarning("No Selection", "Please select aggregates to activate.")
            return
        
        if confirm_dialog("Confirm Activation", f"Activate {len(selected)} aggregates?"):
            thread = threading.Thread(target=self._activate_thread, args=(selected,), daemon=True)
            thread.start()
    
    def _activate_thread(self, selected):
        """Thread function for activation"""
        try:
            aggregate_ids = [agg["id"] for agg in selected]
            results = self.operations.activate_aggregates(aggregate_ids)
            
            success_count = sum(1 for r in results if r["status"] == "success")
            self.log(f"✓ Activated {success_count}/{len(selected)} aggregates")
            
            # Refresh the list to show updated status
            self.list_aggregates()
            
        except Exception as e:
            self.log(f"✗ Error activating aggregates: {e}")
    
    def deactivate_selected(self):
        """Deactivate selected aggregates"""
        selected = self.aggregates_tree.get_selected_aggregates()
        if not selected:
            messagebox.showwarning("No Selection", "Please select aggregates to deactivate.")
            return
        
        if confirm_dialog("Confirm Deactivation", f"Deactivate {len(selected)} aggregates?"):
            thread = threading.Thread(target=self._deactivate_thread, args=(selected,), daemon=True)
            thread.start()
    
    def _deactivate_thread(self, selected):
        """Thread function for deactivation"""
        try:
            aggregate_ids = [agg["id"] for agg in selected]
            results = self.operations.deactivate_aggregates(aggregate_ids)
            
            success_count = sum(1 for r in results if r["status"] == "success")
            self.log(f"✓ Deactivated {success_count}/{len(selected)} aggregates")
            
            # Refresh the list to show updated status
            self.list_aggregates()
            
        except Exception as e:
            self.log(f"✗ Error deactivating aggregates: {e}")
    
    def generate_report(self):
        """Generate aggregate report"""
        if not self.selected_cube:
            messagebox.showwarning("No Cube Selected", "Please select a cube first.")
            return
        
        # Create a simple dialog for report type selection
        report_types = [
            ("Statistics", "statistics"),
            ("Health Check", "health"),
            ("Detailed Analysis", "analysis"),
            ("Export CSV", "csv")
        ]
        
        # Create dialog window
        dialog = tk.Toplevel(self.parent)
        dialog.title("Select Report Type")
        dialog.geometry("300x300")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select Report Type:", 
                 font=("Arial", 10, "bold")).pack(pady=(20, 10))
        
        selected_type = tk.StringVar(value="statistics")
        
        for display_text, value in report_types:
            rb = ttk.Radiobutton(dialog, text=display_text, 
                                variable=selected_type, value=value)
            rb.pack(anchor="w", padx=30, pady=5)
        
        def on_generate():
            report_type = selected_type.get()
            dialog.destroy()
            thread = threading.Thread(target=self._generate_report_thread, 
                                     args=(report_type,), daemon=True)
            thread.start()
        
        ttk.Button(dialog, text="Generate", command=on_generate).pack(pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=(0, 10))
    
    def _generate_report_thread(self, report_type):
        """Thread function for report generation"""
        try:
            if report_type == 'statistics':
                self.log("Generating aggregate statistics...")
                statistics = self.report_generator.show_cube_aggregate_statistics(self.selected_cube)
                self._safe_gui_update(lambda: self._update_details_text(statistics))
                self.log("✓ Statistics generated")
                
            elif report_type == 'health':
                self.log("Checking aggregate health...")
                health_report = self.report_generator.check_cube_aggregate_health(self.selected_cube)
                self._safe_gui_update(lambda: self._update_details_text(health_report))
                self.log("✓ Health check completed")
                
            elif report_type == 'analysis':
                self.log("Generating detailed analysis...")
                analysis = self.report_generator.show_detailed_analysis(self.selected_cube)
                self._safe_gui_update(lambda: self._update_details_text(analysis))
                self.log("✓ Analysis generated")
                
            elif report_type == 'csv':
                self.log("Exporting aggregates to CSV...")
                filename = self.report_generator.export_cube_aggregates_csv(self.selected_cube)
                self.log(f"✓ Report exported to: {filename}")
                self._safe_gui_update(lambda: messagebox.showinfo(
                    "Export Complete", 
                    f"Report exported to:\n{filename}"
                ))
                
        except Exception as e:
            self.log(f"✗ Error generating report: {e}")
    
    def _update_details_text(self, content):
        """Update details text widget (called in main thread)"""
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, content)
    
    def show_build_history(self):
        """Show build history for selected cube"""
        if not self.selected_cube:
            messagebox.showwarning("No Cube Selected", "Please select a cube first.")
            return
        
        thread = threading.Thread(target=self._show_build_history_thread, daemon=True)
        thread.start()
    
    def _show_build_history_thread(self):
        """Thread function to show build history"""
        try:
            self.log(f"Fetching build history for: {self.selected_cube['cube_name']}")
            
            history_data = self.build_history.get_build_history(self.selected_cube)
            
            if not history_data:
                self.log("No build history found.")
                return
            
            # Prepare display text
            from datetime import datetime
            lines = []
            lines.append(f"BUILD HISTORY - {self.selected_cube['cube_name']}")
            lines.append("=" * 60 + "\n")
            
            for batch in history_data:
                batch_id = batch.get("id", "N/A")
                status = batch.get("status", "unknown")
                start_time = batch.get("startTime", "")
                end_time = batch.get("endTime", "")
                is_full = batch.get("isFullBuild", False)
                
                # Calculate duration
                if start_time and end_time:
                    try:
                        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                        duration = (end - start).total_seconds()
                        duration_str = f"{duration:.1f}s"
                    except:
                        duration_str = "N/A"
                else:
                    duration_str = "N/A"
                
                lines.append(f"Batch: {batch_id[:12]}...")
                lines.append(f"  Status: {status}")
                lines.append(f"  Type: {'Full' if is_full else 'Incremental'}")
                lines.append(f"  Duration: {duration_str}")
                lines.append(f"  Started: {start_time[:19]}")
                lines.append(f"  Ended: {end_time[:19]}")
                lines.append("")
            
            # Update GUI
            self._safe_gui_update(lambda: self._update_details_text("\n".join(lines)))
            self.log(f"✓ Loaded {len(history_data)} build history records")
            
        except Exception as e:
            self.log(f"✗ Error fetching build history: {e}")
    
    def log(self, message):
        """Thread-safe logging"""
        self._safe_gui_update(lambda: append_log(self.log_widget, message))
    
    def _safe_gui_update(self, func):
        """Execute GUI update in main thread"""
        try:
            if self.parent and self.parent.winfo_exists():
                self.parent.after(0, func)
        except Exception as e:
            print(f"GUI update error: {e}")