# PythonAtscaleUtility

PythonAtscaleUtility is a convenience utility for working with AtScale projects. It provides tools for querying, migrating, exporting, and interacting with project repositories. The repo contains CLI-style entry points and modular packages for API actions, migration workflows, query management, and UI tab logic used by a larger application.

**Quick status**: Core files include `main.py` (entrypoint), `config.json` / `sample.config.json` (configuration), `requirements.txt` (dependencies), and several packages: `api/`, `migration/`, `queries/`, `tabs/`, plus helpers for export and installers.

**How to run**
- **Run main application**: `python3 main.py` (use `config.json` or `sample.config.json` to configure runtime options).
- **Run single modules / tests**: use the included `test-*.py` scripts, e.g. `python3 test-connect-jdbc.py`.

**Dependencies**
- See `requirements.txt` for Python package dependencies.

**Project layout & functionality summary**

- `main.py`
	- Application entrypoint that wires configuration and launches the utility's main behavior.

- Root utilities
	- `config.json` / `sample.config.json`: runtime configuration templates.
	- `check_dependencies.py`: verifies required system packages or Python dependencies are available.
	- `common.py`: shared helpers used across modules.
	- `json-viewer.py`, `nested.json`, `testtab.py`: smaller utilities and development aids.

- `api/`
	- Purpose: helpers that interact with repositories and filesystem structures.
	- `folders.py`: functions that manage folder paths, create/scan project folders, and help prepare workspace structure.
	- `git_operations.py`: wrappers and helpers for performing Git operations used throughout the toolset (clone, commit, push, branch operations).

- `migration/`
	- Purpose: core migration logic and supporting tools for migrating AtScale projects, building metadata, and interacting with source control.
	- Key modules:
		- `migration_controller.py`, `migration_runner.py`: orchestrate migration flows and execute step-by-step migration tasks.
		- `migration_fromGit.py`, `migration_toGit.py`: import/export flows between Git and the internal project format.
		- `sml_analyzer.py`, `xml_to_sml.py`, `sml_to_xml.py`: conversion and analysis of SML/XML project formats.
		- `support_zip_*`: helpers to build, inspect, and process distributable ZIP packages.
		- `installer_data_manager.py`, `git_data_manager.py`, `project_deletion_manager.py`: helpers to manage migration data, installer-specific state, and project deletion.
	- The folder contains specialized utilities used by migration wizards and UI components (wizard_*.py).

- `queries/`
	- Purpose: run, map, and persist queries and their history; includes utilities for converting IDs and executing query batches.
	- Key modules:
		- `queries_executor.py`: executes queries against a configured backend (JDBC/SQL endpoint helpers present elsewhere in repo).
		- `queries_input.py`, `queries_results.py`: accept and normalize input, collect and render results.
		- `query_history_*`: several modules provide persistence and UI-friendly structures for saving query history, mapping IDs, and loading previous runs.
		- `id_converter.py` / `id_mapping_helper.py`: work with AtScale-specific identifier formats.

- `tabs/`
	- Purpose: UI logic and view components (likely used by a GUI or TUI) for viewing catalogs, query results, and migration status.
	- Notable files:
		- `catalog_*`: load and display catalog data.
		- `cube_data_*`: drilldown, preview, and parse cube/query results.
		- `queries_tab.py`, `queries_history.py`: UI flows for running queries and browsing history.
		- `mdx_parser.py`, `common_xmla.py`: helpers for parsing queries and working with XMLA protocol messages.

- `excel_export/`
	- Purpose: utilities for exporting data to Excel formats (used by reporting and export features).

- `working_dir/`
	- Workspace used by the application for checkout areas: `git_repos/`, `sml/`, `xml/` where imported and exported artifacts are stored.

**Developer notes & tests**
- There are several test scripts in the repo root (`test-connect-jdbc.py`, `test-installer-sql-api.py`) which you can run directly for quick checks.
- Use `check_dependencies.py` before running heavier flows to ensure required tools are present.


