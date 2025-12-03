# [file name]: support_zip_ui_components.py
import tkinter as tk
from tkinter import ttk

class UIComponents:
    """Reusable UI components for support zip UI"""
    
    @staticmethod
    def create_labeled_frame(parent, text, padding=5):
        """Create a labeled frame"""
        return ttk.LabelFrame(parent, text=text, padding=padding)
    
    @staticmethod
    def create_action_button(parent, text, command, width=15, side=tk.LEFT, padx=(0, 10)):
        """Create a standardized action button"""
        btn = ttk.Button(parent, text=text, command=command, width=width)
        btn.pack(side=side, padx=padx)
        return btn
    
    @staticmethod
    def create_status_label(parent, text="", foreground="black"):
        """Create a status label"""
        label = ttk.Label(parent, text=text, foreground=foreground)
        return label
    
    @staticmethod
    def create_scrollable_frame(parent):
        """Create a scrollable frame"""
        # Create main frame
        main_frame = ttk.Frame(parent)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        
        # Create scrollable frame inside canvas
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure canvas
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack everything
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return main_frame, scrollable_frame