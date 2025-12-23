import tkinter as tk
from tkinter import ttk
from common import make_tab_with_log, append_log
from tabs.overview_tab import build_tab as overview_tab
from tabs.migrations_tab import build_tab as migrations_tab
from tabs.queries_tab import build_tab as queries_tab
from tabs.cube_data_preview_tab import build_tab as cube_data_preview_tab
from tabs.catalog_tab import build_tab as catalog_tab
from tabs.aggregate_tab import build_tab as aggregate_tab


def main():
    root = tk.Tk()
    root.title("Tabbed Window")
    root.geometry("1300x1000")

    style = ttk.Style(root)
    for theme in ("aqua", "default"):
        try:
            style.theme_use(theme)
            break
        except tk.TclError:
            continue

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # Create seven log containers (one per tab)
    log1, log2, log3, log4, log5, log6, log7 = [None], [None], [None], [None], [None], [None], [None]

    make_tab_with_log(notebook, "Project Overview", overview_tab, log1)
    make_tab_with_log(notebook, "Migrations", migrations_tab, log2)
    make_tab_with_log(notebook, "Queries", queries_tab, log3)
    make_tab_with_log(notebook, "Cube Data Preview", cube_data_preview_tab, log4)
    make_tab_with_log(notebook, "Catalog", catalog_tab, log5)
    make_tab_with_log(notebook, "Aggregates", aggregate_tab, log6)

    append_log(log1[0], "Project Overview initialized.")
    append_log(log2[0], "Migrations loaded.")
    append_log(log3[0], "Queries tab ready.")
    append_log(log4[0], "Cube Data Preview ready.")
    append_log(log5[0], "Catalog ready.")
    append_log(log6[0], "Aggregate ready.")

    root.mainloop()


if __name__ == "__main__":
    main()
