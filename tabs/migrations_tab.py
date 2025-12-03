# tabs/migrations_tab.py
from migration.migrations_tab_ui import MigrationsTabUI
from migration.migrations_tab_logic import MigrationsTabLogic

def build_tab(content, log_ref_container):
    # Create UI
    ui = MigrationsTabUI(content)

    # Create Logic and wire it to the UI
    logic = MigrationsTabLogic(ui, content, log_ref_container)

    # Return references if needed (UI + Logic)
    return ui, logic
