from .overview_tab import build_tab as overview_tab
from .migrations_tab import build_tab as migrations_tab
from .queries_tab import build_tab as queries_tab
from .cube_data_preview_tab import build_tab as cube_data_preview_tab
from .catalog_tab import build_tab as catalog_tab
from .aggregate_history_tab import build_tab as aggregate_history_tab

__all__ = [
    "overview_tab",
    "migrations_tab",
    "queries_tab",
    "cube_data_preview_tab",
    "catalog_tab",
    "aggregate_history_tab",
]
