# To-Do (SQLite) — User Guide

This small command-line To‑Do application stores tasks in a local SQLite database. It provides a simple CRUD-style interface to add, list, complete, and delete tasks.

This guide explains how to install, run, and extend the app, documents the CLI options and database schema, and covers common troubleshooting steps.

## Quick facts

- Project files: `app.py` (CLI entrypoint), `todo_db.py` (database layer)
- Language: Python (standard library only; no external dependencies required for core usage)
- Default database file: `todo_tasks.db` (created in the current working directory)
- Default journaling mode: WAL (Write-Ahead Log) is enabled by default for better concurrency

## Minimal requirements

- Python 3.8+ (the code uses standard library only)
- On Windows, use PowerShell or Command Prompt; examples below use PowerShell syntax.

## Running the CLI

All commands are executed by running `app.py` with Python. From the project root (where `app.py` and `todo_db.py` live):

```powershell
python app.py add "Buy groceries"
python app.py list
python app.py complete 3
python app.py delete 5
```

If you prefer a different database file location, pass `--db` before the subcommand (or after — argparse will accept it as a global argument):

```powershell
python app.py --db C:\temp\my-todos.db add "Call Alice"
python app.py --db C:\temp\my-todos.db list
```

You can increase logging verbosity for debugging:

```powershell
python app.py --log-level DEBUG list
```

## CLI reference

The CLI uses subcommands. Each subcommand prints a short success or error message.

- add
  - Usage: `python app.py add "task content"`
  - Adds a new task with status `Pending`.
  - Returns the auto-generated task id on success.

- list
  - Usage: `python app.py list [--limit N] [--status Pending|Completed] [--query text]`
  - Shows tasks in descending order by id.
  - `--limit` restricts the number of rows returned.
  - `--status` filters by `Pending` or `Completed` (case-sensitive value expected by the argument parser but the values are precisely `Pending` or `Completed`).
  - `--query` does a case-insensitive substring search against the task text.

- complete
  - Usage: `python app.py complete <id>`
  - Marks the task with the given id as `Completed` (if it exists and isn't already completed).

- delete
  - Usage: `python app.py delete <id>`
  - Permanently removes the task with the given id.

Global options:

- `--db <path>`: path to the SQLite database file. Default: `todo_tasks.db`.
- `--log-level <level>`: set logging level (e.g., `DEBUG`, `INFO`, `WARNING`, `ERROR`). Default: `INFO`.

Exit codes (how `app.py` returns codes):

- `0` — success
- `1` — unexpected error in command execution
- `2` — database setup error

## Examples

- Add a task and then list recent tasks:

```powershell
python app.py add "Pay electric bill"
python app.py list --limit 10
```

- Search for tasks containing "book":

```powershell
python app.py list --query book
```

- Mark task #7 completed and confirm:

```powershell
python app.py complete 7
python app.py list --status Completed
```

## Database internals

The application stores tasks in a single SQLite table named `todos`. The schema (created by `TodoDB.setup()`) is:

```sql
CREATE TABLE IF NOT EXISTS todos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('Pending','Completed')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);
```

Fields:

- `id` — integer primary key automatically assigned.
- `task` — the task description (non-empty text).
- `status` — one of `Pending` or `Completed`.
- `created_at` — timestamp string set by SQLite using `datetime('now')` when the row is created.
- `updated_at` — timestamp string updated when a row is modified (used by `complete` to set completion time).

By default, the DB connection config uses `PRAGMA journal_mode = WAL` and `PRAGMA busy_timeout = 5000` (ms). WAL helps concurrent readers/writers; busy timeout makes DB operations retry briefly on lock contention.

## Error messages & common behaviors

- Trying to add an empty task will raise `ValueError: Task content cannot be empty.` and the CLI will show an error message.
- If `complete` or `delete` specify a non-existent id, the CLI prints an error-style message indicating the id was not found.
- If the database file cannot be created or schema setup fails, `app.py` will print a message and exit with code `2`.

## Troubleshooting

- Permission errors when creating or writing the DB file:
  - Ensure the directory where the DB will be created is writable. Use `--db` to point to a writable location (e.g., `%TEMP%` or `C:\Users\<you>\Documents`).

- Locked database errors on Windows:
  - SQLite can report a locked database if another process holds a long transaction. WAL mode reduces contention, but if you see lock errors, close other programs that might access the DB or use a different DB file for concurrent processes.

- Unexpected exceptions or stack traces:
  - Run with `--log-level DEBUG` to collect more information. Logs are printed to stdout/stderr via the Python logging configuration.

## Testing (developer)

The project includes unit test artifacts in the repository structure; if source tests are present, run them with `pytest`.

Install pytest (only needed if you run tests):

```powershell
pip install pytest
```

Run tests from the project root:

```powershell
pytest -q
```

If tests are missing but you want a quick check, use the CLI to add/list/delete tasks against a temporary database file to confirm behavior:

```powershell
python app.py --db C:\temp\todo_test.db add "temporary task"
python app.py --db C:\temp\todo_test.db list
python app.py --db C:\temp\todo_test.db delete 1
```

## Developer notes and extension ideas

- Code layout:
  - `todo_db.py` contains `TodoDB`, `Task` dataclass, and STATUS constants.
  - `app.py` contains the CLI logic and argument parsing; each subcommand delegates into `TodoDB` methods.

- Where to add new features:
  - Add a `due_date` column to the `todos` table and update `add_task`/`list_tasks` accordingly.
  - Add tagging by creating a `tags` table and a many-to-many relation table.
  - Add an export command to dump tasks as CSV or JSON.

- Tests: add unit tests around `TodoDB` methods using a temporary in-memory SQLite database by passing `db_path=':memory:'` or using a temp file.

## Security & data integrity notes

- The app uses parameterized SQL queries to avoid SQL injection in user-supplied task content.
- Back up your `.db` file if it contains important information; it's a plain SQLite file.

## FAQ

- Q: Can multiple instances of the CLI safely write to the same DB?
  - A: WAL mode improves concurrency for this use case, but SQLite is still not a full database server. For heavy concurrent writes, use a client/server RDBMS.

- Q: Why is `created_at` a TEXT column instead of a native datetime type?
  - A: The schema stores timestamps using SQLite's `datetime('now')` textual representation. This is portable and human-readable.

## Contact / Next steps

If you want, I can:

- Add a tiny `README.md` with a quick-start snippet.
- Create example tests that assert basic `TodoDB` behaviors with an in-memory DB.
- Add a GitHub Actions workflow to run tests on push.

Pick one and I'll add it.
