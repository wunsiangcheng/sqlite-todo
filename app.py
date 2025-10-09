import argparse
import logging
import sys
from typing import Optional

from todo_db import TodoDB, DEFAULT_DB

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"


def configure_logging(level: str) -> None:
    numeric = getattr(logging, level.upper(), None)
    if numeric is None:
        numeric = logging.INFO
    logging.basicConfig(level=numeric, format=LOG_FORMAT)


def cmd_add(db: TodoDB, args: argparse.Namespace) -> None:
    try:
        task_id = db.add_task(args.content)
        print(f"[SUCCESS] Task added (id={task_id}): {args.content}")
    except Exception as e:
        print(f"[ERROR] Failed to add task: {e}")


def cmd_list(db: TodoDB, args: argparse.Namespace) -> None:
    try:
        tasks = db.list_tasks(limit=args.limit, status=args.status, query=args.query)
        if not tasks:
            print("[INFO] To-Do list is empty.")
            return
        print(f"{'ID':<4} {'STATUS':<10} {'CREATED_AT':<20} TASK")
        print("-" * 70)
        for t in tasks:
            status = "COMPLETED" if t.status == "Completed" else "PENDING"
            created = t.created_at or ""
            print(f"{t.id:<4} {status:<10} {created:<20} {t.task}")
    except ValueError as ve:
        print(f"[ERROR] {ve}")
    except Exception as e:
        print(f"[ERROR] Failed to list tasks: {e}")


def cmd_complete(db: TodoDB, args: argparse.Namespace) -> None:
    try:
        ok = db.complete_task(args.id)
        if ok:
            print(f"[SUCCESS] Task [{args.id}] marked as Completed.")
        else:
            print(f"[ERROR] Task with ID {args.id} not found or already completed.")
    except Exception as e:
        print(f"[ERROR] Failed to complete task: {e}")


def cmd_delete(db: TodoDB, args: argparse.Namespace) -> None:
    try:
        ok = db.delete_task(args.id)
        if ok:
            print(f"[SUCCESS] Task [{args.id}] deleted.")
        else:
            print(f"[ERROR] Task with ID {args.id} not found.")
    except Exception as e:
        print(f"[ERROR] Failed to delete task: {e}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="todo", description="Simple To-Do CLI (SQLite)")
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to SQLite database file")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a new task")
    p_add.add_argument("content", help="Task content (quoted if spaces)")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List tasks")
    p_list.add_argument("--limit", type=int, default=None, help="Limit number of tasks shown")
    p_list.add_argument(
        "--status",
        choices=["Pending", "Completed"],
        default=None,
        help="Filter tasks by status (Pending or Completed)",
    )
    p_list.add_argument(
        "--query",
        default=None,
        help="Filter tasks by substring match in the task content (case-insensitive)",
    )
    p_list.set_defaults(func=cmd_list)

    p_complete = sub.add_parser("complete", help="Mark a task as completed")
    p_complete.add_argument("id", type=int, help="Task ID to mark completed")
    p_complete.set_defaults(func=cmd_complete)

    p_delete = sub.add_parser("delete", help="Delete a task by ID")
    p_delete.add_argument("id", type=int, help="Task ID to delete")
    p_delete.set_defaults(func=cmd_delete)

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.log_level)

    db = TodoDB(db_path=args.db)
    try:
        db.setup()
    except Exception as e:
        logging.exception("Database setup failed.")
        print(f"[ERROR] Database setup failed: {e}")
        return 2

    try:
        args.func(db, args)
    except Exception:
        logging.exception("Unhandled error in command.")
        print("[ERROR] An unexpected error occurred.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())



    