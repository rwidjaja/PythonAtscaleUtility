# tabs/queries_history.py
import pandas as pd

class QueryHistory:
    def __init__(self):
        self.history = []
        self.current_index = -1
    
    def add_query(self, query, query_type, catalog, cube):
        """Add query to history"""
        self.history.append({
            'query': query,
            'type': query_type,
            'catalog': catalog,
            'cube': cube,
            'timestamp': pd.Timestamp.now()
        })
        self.current_index = len(self.history) - 1
    
    def get_previous(self):
        """Get previous query from history"""
        if self.history and self.current_index > 0:
            self.current_index -= 1
            return self.history[self.current_index]
        return None
    
    def get_next(self):
        """Get next query from history"""
        if self.history and self.current_index < len(self.history) - 1:
            self.current_index += 1
            return self.history[self.current_index]
        return None
    
    def get_current(self):
        """Get current query from history"""
        if 0 <= self.current_index < len(self.history):
            return self.history[self.current_index]
        return None
    
    def clear_history(self):
        """Clear query history"""
        self.history.clear()
        self.current_index = -1
    
    def get_history_count(self):
        """Get total number of queries in history"""
        return len(self.history)
    
    def get_current_position(self):
        """Get current position in history"""
        return self.current_index + 1 if self.history else 0