## sqlite-todo

A tiny, dependency-free command-line To-Do application using SQLite.

Files
- `app.py` — CLI entrypoint. Parses arguments and calls the database layer.
- `todo_db.py` — Minimal SQLite-backed data access layer. Provides add, list, complete, and delete operations.
- `test_app.py` — Unit tests for the CLI application.
- `test_todo_db.py` — Unit tests for the database layer.

Quick summary

- Default database file: `todo_tasks.db` (created in the current working directory).
- No external packages required — uses Python standard library (sqlite3, argparse, dataclasses).
- Recommended Python: 3.8+ (works on 3.7+, but 3.8+ is recommended).

Contract (CLI)
- Inputs: command-line arguments (commands: `add`, `list`, `complete`, `delete`). Optional flags: `--db` to specify DB path, `--log-level`.
- Outputs: human-readable status messages printed to stdout; `list` prints a table of tasks.
- Error modes: prints `[ERROR]` messages for validation, DB errors, or invalid IDs.

Database schema

Table `todos` (created by `TodoDB.setup()`):

```
id INTEGER PRIMARY KEY AUTOINCREMENT
task TEXT NOT NULL
status TEXT NOT NULL CHECK (status IN ('Pending','Completed'))
created_at TEXT NOT NULL DEFAULT (datetime('now'))
updated_at TEXT
```

Usage examples (PowerShell)

Create a virtual environment (optional):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

Add a task (uses `todo_tasks.db` by default):

```powershell
python .\app.py add "Buy groceries"
```

List tasks:

```powershell
python .\app.py list
python .\app.py list --limit 10 --status Pending --query groceries
```

Mark a task complete (replace 1 with the task ID):

```powershell
python .\app.py complete 1
```

Delete a task by ID:

```powershell
python .\app.py delete 1
```

Specify a different database file:

```powershell
python .\app.py --db .\data\mydb.db add "Call mom"
```

Configure logging verbosity:

```powershell
python .\app.py --log-level DEBUG list
```

Edge cases and notes
- Empty or whitespace-only tasks are rejected by `add_task` (ValueError).
- `list --status` accepts `Pending` or `Completed` exactly.
- `complete` will return an error message if the task is not found or already completed.
- Concurrent access: TodoDB enables WAL by default and sets a busy timeout, but database locks can still occur on heavily concurrent uses.

Troubleshooting
- If you see SQLite busy/locked errors, try using a different path for the DB or ensure no other long-running transactions are holding the DB.
- If `created_at` looks empty in listing, ensure your SQLite build supports the `datetime('now')` default (standard SQLite does).

Testing

Run all unit tests:

```powershell
python -m unittest discover -s . -p "test_*.py" -v
```

The project includes comprehensive unit tests with 100% pass rate:
- 24 tests for the database layer
- 33 tests for the CLI application
- See `TEST_SUMMARY.md` for detailed test coverage information

Next steps (suggestions)
- Add a simple shell completion file or a help alias for common commands.
- Add packaging (console_scripts entry point) if you want `todo` to be globally installed.
- Add integration tests for concurrent access scenarios.

License

Use or modify the code as you like. No license file is included.
