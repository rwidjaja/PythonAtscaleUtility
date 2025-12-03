import tkinter as tk
from tkinter import ttk
from common import append_log

def build_tab(content, log_ref_container):
    content.columnconfigure(0, weight=1)
    ttk.Label(content, text="Aggregate History").grid(row=0, column=0, sticky="w", padx=8, pady=8)

    log_widget = log_ref_container[0]
    if log_widget is not None:
        append_log(log_widget, "Aggregate History tab created.")
