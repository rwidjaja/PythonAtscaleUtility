# queries/query_input_logic.py
from queries.query_history_window import QueryHistoryWindow
from queries.query_history_service import QueryHistoryService

class QueryInputLogic:
    def __init__(self, ui: "QueryInputUI"):
        self.ui = ui
        self.history_service = None
        self.current_catalog = ""
        self.current_cube = ""
        self.current_catalog_id = ""
        self.current_cube_id = ""

    def show_query_history(self):
        if not self.history_service:
            self.history_service = QueryHistoryService()

        parent_window = self.ui.main_frame.winfo_toplevel()
        if hasattr(parent_window, 'history_window_reference'):
            try:
                if parent_window.history_window_reference.window.winfo_exists():
                    parent_window.history_window_reference.window.lift()
                    parent_window.history_window_reference.window.focus_set()
                    return
            except:
                parent_window.history_window_reference = None

        history_window = QueryHistoryWindow(
            parent_window,
            self.history_service,
            on_re_run_query=self.re_run_query_from_history
        )
        parent_window.history_window_reference = history_window

        if self.current_catalog_id and self.current_cube_id:
            history_window.refresh_history(
                catalog_name=self.current_catalog,
                cube_name=self.current_cube,
                catalog_id=self.current_catalog_id,
                cube_id=self.current_cube_id
            )
        else:
            history_window.refresh_history(
                catalog_name=self.current_catalog,
                cube_name=self.current_cube
            )

    def re_run_query_from_history(self, query_text, query_language):
        if query_text and query_text.strip():
            self.ui.query_text.delete("1.0", "end")
            self.ui.query_text.insert("1.0", query_text)
            self.ui.query_text.update_idletasks()

            new_type = "MDX" if query_language == "MDX" else "SQL"
            if self.ui.query_type_var.get() != new_type:
                self.ui.query_type_var.set(new_type)

            self.ui.main_frame.update()
            if self.ui.on_execute:
                self.ui.on_execute()
        else:
            print("[ERROR] No query text received from history")

    def set_sample_queries(self, mdx_sample, sql_sample):
        self.mdx_sample = mdx_sample
        self.sql_sample = sql_sample
        current_query = self.ui.query_text.get("1.0", "end-1c").strip()
        if not current_query or "Sample" in current_query:
            if self.ui.query_type_var.get() == "MDX":
                self.ui.query_text.insert("1.0", mdx_sample)
            else:
                self.ui.query_text.insert("1.0", sql_sample)

    def update_sample_for_cube(self, catalog, cube, catalog_id=None, cube_id=None):
        self.current_catalog = catalog
        self.current_cube = cube
        self.current_catalog_id = catalog_id or ""
        self.current_cube_id = cube_id or ""
        if hasattr(self, 'mdx_sample') and hasattr(self, 'sql_sample'):
            mdx_updated = self.mdx_sample.replace("YourCubeName", cube)
            sql_updated = self.sql_sample.replace("YourCubeName", cube)
            self.set_sample_queries(mdx_updated, sql_updated)
