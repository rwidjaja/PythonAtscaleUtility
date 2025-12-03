import tkinter as tk
from tkinter import ttk

MAX_LOG_LINES = 1000  # limit memory usage

def append_log(text_widget, message):
    """Append a message to the log, trimming old lines if too many."""
    text_widget.insert("end", message + "\n")
    if int(text_widget.index("end-1c").split(".")[0]) > MAX_LOG_LINES:
        text_widget.delete("1.0", "2.0")
    text_widget.see("end")

def make_tab_with_log(notebook, title, content_builder):
    frame = ttk.Frame(notebook, padding=12)
    notebook.add(frame, text=title)

    frame.rowconfigure(0, weight=1)
    frame.rowconfigure(1, weight=0, minsize=200)  # log fixed height
    frame.columnconfigure(0, weight=1)

    # Content area
    content = ttk.Frame(frame)
    content.grid(row=0, column=0, sticky="nsew")
    content_builder(content)

    # Log area
    log_frame = ttk.Frame(frame)
    log_frame.grid(row=1, column=0, sticky="nsew")

    scrollbar = ttk.Scrollbar(log_frame)
    scrollbar.pack(side="right", fill="y")

    log_text = tk.Text(log_frame, wrap="none", yscrollcommand=scrollbar.set)
    log_text.pack(fill="both", expand=True)
    scrollbar.config(command=log_text.yview)

    return log_text

def main():
    root = tk.Tk()
    root.title("Tabbed Window")
    root.geometry("1200x1000")

    style = ttk.Style(root)
    for theme in ("aqua", "default"):
        try:
            style.theme_use(theme)
            break
        except tk.TclError:
            continue

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # Tab 1: Project Overview (unchanged from your version)
    def build_tab1(content):
        content.rowconfigure(0, weight=3)
        content.rowconfigure(1, weight=2)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)

        listbox1 = tk.Listbox(content)
        for i in range(1, 21):
            listbox1.insert("end", f"Category {i}")
        listbox1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        listbox2 = tk.Listbox(content)
        listbox2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        result_text = tk.Text(content, height=10)
        result_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        def on_select1(event):
            if listbox1.curselection():
                category = listbox1.get(listbox1.curselection()[0])
                listbox2.delete(0, "end")
                for j in range(1, 6):
                    listbox2.insert("end", f"{category} - Option {j}")
                append_log(log1, f"Selected category: {category}")

        listbox1.bind("<<ListboxSelect>>", on_select1)

        def on_select2(event):
            if listbox2.curselection():
                item = listbox2.get(listbox2.curselection()[0])
                result_text.delete("1.0", "end")
                result_text.insert("end", f"Results for {item}\n")
                append_log(log1, f"Selected item: {item}")

        listbox2.bind("<<ListboxSelect>>", on_select2)

    log1 = make_tab_with_log(notebook, "Project Overview", build_tab1)

    # Tab 2: Migrations
    def build_tab2(content):
        content.rowconfigure(1, weight=1)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)

        # Top controls: checkbox + button
        top_frame = ttk.Frame(content)
        top_frame.grid(row=0, column=0, columnspan=2, sticky="w", pady=5)

        mode_var = tk.BooleanVar(value=False)  # False = Installer->Container, True = Container->Installer
        mode_label = ttk.Label(top_frame, text="Installer to Container")
        mode_label.pack(side="left")

        def toggle_mode():
            if mode_var.get():
                mode_label.config(text="Container to Installer")
                append_log(log2, "Mode set: Container to Installer")
            else:
                mode_label.config(text="Installer to Container")
                append_log(log2, "Mode set: Installer to Container")

        mode_check = ttk.Checkbutton(top_frame, variable=mode_var, command=toggle_mode)
        mode_check.pack(side="left", padx=5)

        migrate_btn = ttk.Button(top_frame, text="Migrate", command=lambda: append_log(log2, "Migration triggered"))
        migrate_btn.pack(side="left", padx=10)

        # Two side-by-side listboxes
        listbox_left = tk.Listbox(content)
        listbox_left.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        for i in range(1, 11):
            listbox_left.insert("end", f"Installer Item {i}")

        listbox_right = tk.Listbox(content)
        listbox_right.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        for i in range(1, 11):
            listbox_right.insert("end", f"Container Item {i}")

        # Selection logic
        def on_select_left(event):
            if not mode_var.get() and listbox_left.curselection():
                item = listbox_left.get(listbox_left.curselection()[0])
                append_log(log2, f"Selected from Installer: {item}")

        def on_select_right(event):
            if mode_var.get() and listbox_right.curselection():
                item = listbox_right.get(listbox_right.curselection()[0])
                append_log(log2, f"Selected from Container: {item}")

        listbox_left.bind("<<ListboxSelect>>", on_select_left)
        listbox_right.bind("<<ListboxSelect>>", on_select_right)

    log2 = make_tab_with_log(notebook, "Migrations", build_tab2)

    # Tab 3: Logs
    def build_tab3(content):
        ttk.Label(content, text="Logs tab content area").pack(anchor="w")

    log3 = make_tab_with_log(notebook, "Queries", build_tab3)

    # Example logs
    append_log(log1, "Project Overview initialized.")
    append_log(log2, "Migrations loaded.")
    append_log(log3, "Queries tab ready.")

    root.mainloop()

if __name__ == "__main__":
    main()
