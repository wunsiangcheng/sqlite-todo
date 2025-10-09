# sqlite-todo

A tiny command-line To‑Do application using SQLite.

This repository contains a minimal CLI that stores tasks in a local SQLite database.

Files
- `app.py` - CLI front-end. Uses `argparse` and exposes commands: `add`, `list`, `complete`, `delete`.
- `todo_db.py` - Database layer. Implements `TodoDB` for managing tasks in a SQLite DB (`todo_tasks.db` by default).

Features
- Add tasks
- List tasks (with optional limit, status filter, and substring query)
- Mark tasks completed
- Delete tasks

Requirements
- Python 3.8+
- No external Python packages required; uses the standard library and SQLite.

Quick setup (Linux)

1. Open a terminal and change into the project directory:

```bash
cd /home/vincent/Documents/sqlite-todo
```

2. (Optional) Create a virtual environment and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Run the CLI. The first run will create the SQLite database file (by default `todo_tasks.db`) and schema.

Basic usage examples (Linux)

- Show help:

```bash
python3 app.py --help
```

- Add a task:

```bash
python3 app.py add "Buy groceries"
# Output: [SUCCESS] Task added (id=1): Buy groceries
```

- List all tasks:

```bash
python3 app.py list
# Example output:
# ID   STATUS     CREATED_AT           TASK
# ----------------------------------------------------------------------
# 1    PENDING    2025-10-10 12:34:56  Buy groceries
```

- List only completed tasks:

```bash
python3 app.py list --status Completed
```

- Search tasks by substring (case-insensitive):

```bash
python3 app.py list --query groceries
```

- Limit number of tasks shown:

```bash
python3 app.py list --limit 5
```

- Mark a task completed (by ID):

```bash
python3 app.py complete 1
# Output: [SUCCESS] Task [1] marked as Completed.
```

- Delete a task (by ID):

```bash
python3 app.py delete 1
# Output: [SUCCESS] Task [1] deleted.
```

Advanced options
- Use a custom database file:

```bash
python3 app.py --db /path/to/my.db add "Use custom DB"
```

- Change logging level (DEBUG, INFO, WARNING, ERROR):

```bash
python3 app.py --log-level DEBUG list
```

Notes
- The default database file is `todo_tasks.db` in the current working directory unless you pass `--db`.
- The `todo_db.py` module enables SQLite WAL mode by default for better concurrency; you can disable it by creating `TodoDB` with `enable_wal=False` if embedding in another app.
- Tasks have the following minimal schema: `id`, `task`, `status` (Pending|Completed), `created_at`, `updated_at`.

Troubleshooting
- If you see SQLite errors about file permissions, ensure the directory is writable and the path passed to `--db` is correct.
- For an empty list output, `app.py` prints `[INFO] To-Do list is empty.`

License
- This project is provided as-is; add a license file if you plan to distribute it.
