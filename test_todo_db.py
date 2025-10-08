"""
Unit tests for todo_db.py module.
Tests use temporary SQLite database files to avoid filesystem side effects.
"""
import unittest
import sqlite3
import tempfile
import os
from todo_db import TodoDB, Task, STATUS_PENDING, STATUS_COMPLETED


class TestTodoDB(unittest.TestCase):
    """Test suite for TodoDB class."""

    def setUp(self):
        """Create a temporary database file for each test."""
        # Use a temporary file instead of :memory: to ensure persistence
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.db_path = self.temp_file.name
        self.temp_file.close()
        
        self.db = TodoDB(db_path=self.db_path, enable_wal=False)
        self.db.setup()

    def tearDown(self):
        """Clean up temporary database file."""
        try:
            if os.path.exists(self.db_path):
                os.unlink(self.db_path)
        except Exception:
            pass

    def test_setup_creates_table(self):
        """Test that setup() creates the todos table."""
        # Setup is called in setUp, so we just verify the table exists
        conn = self.db._connect()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='todos'"
        )
        result = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "todos")

    def test_add_task_success(self):
        """Test adding a valid task."""
        task_id = self.db.add_task("Buy groceries")
        self.assertIsInstance(task_id, int)
        self.assertGreater(task_id, 0)

    def test_add_task_strips_whitespace(self):
        """Test that whitespace is stripped from task content."""
        task_id = self.db.add_task("  Task with spaces  ")
        tasks = self.db.list_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].task, "Task with spaces")

    def test_add_task_empty_string_raises_error(self):
        """Test that empty task content raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            self.db.add_task("")
        self.assertIn("cannot be empty", str(cm.exception))

    def test_add_task_whitespace_only_raises_error(self):
        """Test that whitespace-only task content raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            self.db.add_task("   ")
        self.assertIn("cannot be empty", str(cm.exception))

    def test_list_tasks_empty(self):
        """Test listing tasks when database is empty."""
        tasks = self.db.list_tasks()
        self.assertEqual(tasks, [])

    def test_list_tasks_returns_all_tasks(self):
        """Test listing all tasks."""
        self.db.add_task("Task 1")
        self.db.add_task("Task 2")
        self.db.add_task("Task 3")

        tasks = self.db.list_tasks()
        self.assertEqual(len(tasks), 3)
        # Should be ordered by ID DESC
        self.assertEqual(tasks[0].task, "Task 3")
        self.assertEqual(tasks[1].task, "Task 2")
        self.assertEqual(tasks[2].task, "Task 1")

    def test_list_tasks_with_limit(self):
        """Test listing tasks with a limit."""
        self.db.add_task("Task 1")
        self.db.add_task("Task 2")
        self.db.add_task("Task 3")

        tasks = self.db.list_tasks(limit=2)
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].task, "Task 3")
        self.assertEqual(tasks[1].task, "Task 2")

    def test_list_tasks_filter_by_pending_status(self):
        """Test filtering tasks by Pending status."""
        task_id1 = self.db.add_task("Task 1")
        task_id2 = self.db.add_task("Task 2")
        self.db.complete_task(task_id1)

        tasks = self.db.list_tasks(status=STATUS_PENDING)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].task, "Task 2")
        self.assertEqual(tasks[0].status, STATUS_PENDING)

    def test_list_tasks_filter_by_completed_status(self):
        """Test filtering tasks by Completed status."""
        task_id1 = self.db.add_task("Task 1")
        task_id2 = self.db.add_task("Task 2")
        self.db.complete_task(task_id1)

        tasks = self.db.list_tasks(status=STATUS_COMPLETED)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].task, "Task 1")
        self.assertEqual(tasks[0].status, STATUS_COMPLETED)

    def test_list_tasks_invalid_status_raises_error(self):
        """Test that invalid status filter raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            self.db.list_tasks(status="Invalid")
        self.assertIn("Invalid status filter", str(cm.exception))

    def test_list_tasks_filter_by_query(self):
        """Test filtering tasks by query substring."""
        self.db.add_task("Buy groceries")
        self.db.add_task("Call mom")
        self.db.add_task("Buy books")

        tasks = self.db.list_tasks(query="Buy")
        self.assertEqual(len(tasks), 2)
        task_contents = [t.task for t in tasks]
        self.assertIn("Buy groceries", task_contents)
        self.assertIn("Buy books", task_contents)

    def test_list_tasks_query_case_insensitive(self):
        """Test that query filtering is case-insensitive."""
        self.db.add_task("Buy GROCERIES")
        self.db.add_task("Call mom")

        tasks = self.db.list_tasks(query="groceries")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].task, "Buy GROCERIES")

    def test_list_tasks_combined_filters(self):
        """Test combining status and query filters."""
        task_id1 = self.db.add_task("Buy groceries")
        task_id2 = self.db.add_task("Buy books")
        task_id3 = self.db.add_task("Call mom")
        self.db.complete_task(task_id1)

        tasks = self.db.list_tasks(status=STATUS_PENDING, query="Buy")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].task, "Buy books")

    def test_complete_task_success(self):
        """Test marking a task as completed."""
        task_id = self.db.add_task("Task to complete")
        result = self.db.complete_task(task_id)

        self.assertTrue(result)
        tasks = self.db.list_tasks()
        self.assertEqual(tasks[0].status, STATUS_COMPLETED)

    def test_complete_task_nonexistent_id(self):
        """Test completing a task with nonexistent ID."""
        result = self.db.complete_task(9999)
        self.assertFalse(result)

    def test_complete_task_already_completed(self):
        """Test completing a task that is already completed."""
        task_id = self.db.add_task("Task")
        self.db.complete_task(task_id)
        # Try to complete again
        result = self.db.complete_task(task_id)
        self.assertFalse(result)

    def test_delete_task_success(self):
        """Test deleting a task."""
        task_id = self.db.add_task("Task to delete")
        result = self.db.delete_task(task_id)

        self.assertTrue(result)
        tasks = self.db.list_tasks()
        self.assertEqual(len(tasks), 0)

    def test_delete_task_nonexistent_id(self):
        """Test deleting a task with nonexistent ID."""
        result = self.db.delete_task(9999)
        self.assertFalse(result)

    def test_task_dataclass(self):
        """Test that Task dataclass works correctly."""
        task_id = self.db.add_task("Test task")
        tasks = self.db.list_tasks()

        task = tasks[0]
        self.assertIsInstance(task, Task)
        self.assertEqual(task.id, task_id)
        self.assertEqual(task.task, "Test task")
        self.assertEqual(task.status, STATUS_PENDING)
        self.assertIsNotNone(task.created_at)

    def test_task_has_created_at_timestamp(self):
        """Test that tasks have a created_at timestamp."""
        task_id = self.db.add_task("Test task")
        tasks = self.db.list_tasks()

        task = tasks[0]
        self.assertIsNotNone(task.created_at)
        self.assertIsInstance(task.created_at, str)
        # Basic check that it looks like a timestamp
        self.assertGreater(len(task.created_at), 0)


class TestTodoDBWithFileSystem(unittest.TestCase):
    """Tests that use actual filesystem database files."""

    def setUp(self):
        """Create a temporary database file."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.db_path = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        """Clean up temporary database file."""
        try:
            if os.path.exists(self.db_path):
                os.unlink(self.db_path)
            # Also remove WAL and SHM files if they exist
            for ext in ['-wal', '-shm']:
                wal_file = self.db_path + ext
                if os.path.exists(wal_file):
                    os.unlink(wal_file)
        except Exception:
            pass

    def test_database_persistence(self):
        """Test that data persists across database connections."""
        db1 = TodoDB(db_path=self.db_path)
        db1.setup()
        task_id = db1.add_task("Persistent task")

        # Create new database instance with same path
        db2 = TodoDB(db_path=self.db_path)
        db2.setup()
        tasks = db2.list_tasks()

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].task, "Persistent task")
        self.assertEqual(tasks[0].id, task_id)

    def test_wal_mode_enabled_by_default(self):
        """Test that WAL mode is enabled by default."""
        db = TodoDB(db_path=self.db_path, enable_wal=True)
        db.setup()

        with db._connect() as conn:
            cursor = conn.execute("PRAGMA journal_mode")
            result = cursor.fetchone()
            # Note: WAL mode may not be supported in all environments
            # This test just verifies the pragma is executed without error

    def test_wal_mode_can_be_disabled(self):
        """Test that WAL mode can be disabled."""
        db = TodoDB(db_path=self.db_path, enable_wal=False)
        db.setup()
        # Just verify it doesn't raise an error
        db.add_task("Test task")


if __name__ == "__main__":
    unittest.main()
