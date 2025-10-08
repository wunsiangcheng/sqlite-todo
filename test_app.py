"""
Unit tests for app.py module.
Tests CLI argument parsing and command functions.
"""
import unittest
import tempfile
import os
import sys
from io import StringIO
from unittest.mock import patch, MagicMock
import argparse

from app import (
    build_parser,
    cmd_add,
    cmd_list,
    cmd_complete,
    cmd_delete,
    configure_logging,
    main,
)
from todo_db import TodoDB, Task, STATUS_PENDING, STATUS_COMPLETED


class TestArgumentParser(unittest.TestCase):
    """Test suite for CLI argument parsing."""

    def setUp(self):
        """Create parser for each test."""
        self.parser = build_parser()

    def test_parser_add_command(self):
        """Test parsing add command."""
        args = self.parser.parse_args(["add", "Test task"])
        self.assertEqual(args.command, "add")
        self.assertEqual(args.content, "Test task")
        self.assertEqual(args.func, cmd_add)

    def test_parser_add_command_with_quotes(self):
        """Test parsing add command with quoted content."""
        args = self.parser.parse_args(["add", "Task with spaces"])
        self.assertEqual(args.content, "Task with spaces")

    def test_parser_list_command(self):
        """Test parsing list command."""
        args = self.parser.parse_args(["list"])
        self.assertEqual(args.command, "list")
        self.assertIsNone(args.limit)
        self.assertIsNone(args.status)
        self.assertIsNone(args.query)
        self.assertEqual(args.func, cmd_list)

    def test_parser_list_with_limit(self):
        """Test parsing list command with limit."""
        args = self.parser.parse_args(["list", "--limit", "5"])
        self.assertEqual(args.limit, 5)

    def test_parser_list_with_status_pending(self):
        """Test parsing list command with status filter."""
        args = self.parser.parse_args(["list", "--status", "Pending"])
        self.assertEqual(args.status, "Pending")

    def test_parser_list_with_status_completed(self):
        """Test parsing list command with completed status."""
        args = self.parser.parse_args(["list", "--status", "Completed"])
        self.assertEqual(args.status, "Completed")

    def test_parser_list_with_query(self):
        """Test parsing list command with query filter."""
        args = self.parser.parse_args(["list", "--query", "groceries"])
        self.assertEqual(args.query, "groceries")

    def test_parser_list_with_all_options(self):
        """Test parsing list command with all options."""
        args = self.parser.parse_args([
            "list", "--limit", "10", "--status", "Pending", "--query", "buy"
        ])
        self.assertEqual(args.limit, 10)
        self.assertEqual(args.status, "Pending")
        self.assertEqual(args.query, "buy")

    def test_parser_complete_command(self):
        """Test parsing complete command."""
        args = self.parser.parse_args(["complete", "5"])
        self.assertEqual(args.command, "complete")
        self.assertEqual(args.id, 5)
        self.assertEqual(args.func, cmd_complete)

    def test_parser_delete_command(self):
        """Test parsing delete command."""
        args = self.parser.parse_args(["delete", "3"])
        self.assertEqual(args.command, "delete")
        self.assertEqual(args.id, 3)
        self.assertEqual(args.func, cmd_delete)

    def test_parser_custom_db_path(self):
        """Test parsing custom database path."""
        args = self.parser.parse_args(["--db", "custom.db", "list"])
        self.assertEqual(args.db, "custom.db")

    def test_parser_custom_log_level(self):
        """Test parsing custom log level."""
        args = self.parser.parse_args(["--log-level", "DEBUG", "list"])
        self.assertEqual(args.log_level, "DEBUG")

    def test_parser_no_command_raises_error(self):
        """Test that parser requires a command."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args([])


class TestCommandFunctions(unittest.TestCase):
    """Test suite for command handler functions."""

    def setUp(self):
        """Create temporary database file for each test."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.db_path = self.temp_file.name
        self.temp_file.close()
        
        self.db = TodoDB(db_path=self.db_path, enable_wal=False)
        self.db.setup()
        self.output = StringIO()

    def tearDown(self):
        """Clean up output capture and temp file."""
        self.output.close()
        try:
            if os.path.exists(self.db_path):
                os.unlink(self.db_path)
        except Exception:
            pass

    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_add_success(self, mock_stdout):
        """Test cmd_add with valid input."""
        args = argparse.Namespace(content="Test task")
        cmd_add(self.db, args)

        output = mock_stdout.getvalue()
        self.assertIn("[SUCCESS]", output)
        self.assertIn("Task added", output)
        self.assertIn("Test task", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_add_empty_task(self, mock_stdout):
        """Test cmd_add with empty task."""
        args = argparse.Namespace(content="")
        cmd_add(self.db, args)

        output = mock_stdout.getvalue()
        self.assertIn("[ERROR]", output)
        self.assertIn("Failed to add task", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_list_empty(self, mock_stdout):
        """Test cmd_list with empty database."""
        args = argparse.Namespace(limit=None, status=None, query=None)
        cmd_list(self.db, args)

        output = mock_stdout.getvalue()
        self.assertIn("[INFO]", output)
        self.assertIn("To-Do list is empty", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_list_with_tasks(self, mock_stdout):
        """Test cmd_list with tasks."""
        self.db.add_task("Task 1")
        self.db.add_task("Task 2")

        args = argparse.Namespace(limit=None, status=None, query=None)
        cmd_list(self.db, args)

        output = mock_stdout.getvalue()
        self.assertIn("Task 1", output)
        self.assertIn("Task 2", output)
        self.assertIn("ID", output)
        self.assertIn("STATUS", output)
        self.assertIn("PENDING", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_list_shows_completed_status(self, mock_stdout):
        """Test cmd_list displays completed status correctly."""
        task_id = self.db.add_task("Task to complete")
        self.db.complete_task(task_id)

        args = argparse.Namespace(limit=None, status=None, query=None)
        cmd_list(self.db, args)

        output = mock_stdout.getvalue()
        self.assertIn("COMPLETED", output)
        self.assertIn("Task to complete", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_list_with_invalid_status(self, mock_stdout):
        """Test cmd_list with invalid status filter."""
        args = argparse.Namespace(limit=None, status="Invalid", query=None)
        cmd_list(self.db, args)

        output = mock_stdout.getvalue()
        self.assertIn("[ERROR]", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_complete_success(self, mock_stdout):
        """Test cmd_complete with valid task ID."""
        task_id = self.db.add_task("Task to complete")
        args = argparse.Namespace(id=task_id)
        cmd_complete(self.db, args)

        output = mock_stdout.getvalue()
        self.assertIn("[SUCCESS]", output)
        self.assertIn("marked as Completed", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_complete_nonexistent_id(self, mock_stdout):
        """Test cmd_complete with nonexistent task ID."""
        args = argparse.Namespace(id=9999)
        cmd_complete(self.db, args)

        output = mock_stdout.getvalue()
        self.assertIn("[ERROR]", output)
        self.assertIn("not found", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_complete_already_completed(self, mock_stdout):
        """Test cmd_complete with already completed task."""
        task_id = self.db.add_task("Task")
        self.db.complete_task(task_id)

        args = argparse.Namespace(id=task_id)
        cmd_complete(self.db, args)

        output = mock_stdout.getvalue()
        self.assertIn("[ERROR]", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_delete_success(self, mock_stdout):
        """Test cmd_delete with valid task ID."""
        task_id = self.db.add_task("Task to delete")
        args = argparse.Namespace(id=task_id)
        cmd_delete(self.db, args)

        output = mock_stdout.getvalue()
        self.assertIn("[SUCCESS]", output)
        self.assertIn("deleted", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_delete_nonexistent_id(self, mock_stdout):
        """Test cmd_delete with nonexistent task ID."""
        args = argparse.Namespace(id=9999)
        cmd_delete(self.db, args)

        output = mock_stdout.getvalue()
        self.assertIn("[ERROR]", output)
        self.assertIn("not found", output)


class TestMainFunction(unittest.TestCase):
    """Test suite for main function."""

    def setUp(self):
        """Create temporary database file."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.db_path = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        """Clean up temporary database file."""
        try:
            if os.path.exists(self.db_path):
                os.unlink(self.db_path)
            for ext in ['-wal', '-shm']:
                wal_file = self.db_path + ext
                if os.path.exists(wal_file):
                    os.unlink(wal_file)
        except Exception:
            pass

    @patch('sys.stdout', new_callable=StringIO)
    def test_main_add_task(self, mock_stdout):
        """Test main function with add command."""
        exit_code = main(["--db", self.db_path, "add", "Test task"])
        self.assertEqual(exit_code, 0)

        output = mock_stdout.getvalue()
        self.assertIn("[SUCCESS]", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_main_list_tasks(self, mock_stdout):
        """Test main function with list command."""
        # Add a task first
        main(["--db", self.db_path, "add", "Task 1"])
        mock_stdout.truncate(0)
        mock_stdout.seek(0)

        # List tasks
        exit_code = main(["--db", self.db_path, "list"])
        self.assertEqual(exit_code, 0)

        output = mock_stdout.getvalue()
        self.assertIn("Task 1", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_main_complete_task(self, mock_stdout):
        """Test main function with complete command."""
        # Add a task first
        main(["--db", self.db_path, "add", "Task to complete"])
        
        # Complete the task (ID should be 1)
        exit_code = main(["--db", self.db_path, "complete", "1"])
        self.assertEqual(exit_code, 0)

    @patch('sys.stdout', new_callable=StringIO)
    def test_main_delete_task(self, mock_stdout):
        """Test main function with delete command."""
        # Add a task first
        main(["--db", self.db_path, "add", "Task to delete"])
        
        # Delete the task
        exit_code = main(["--db", self.db_path, "delete", "1"])
        self.assertEqual(exit_code, 0)

    @patch('sys.stdout', new_callable=StringIO)
    def test_main_returns_success_code(self, mock_stdout):
        """Test that main returns 0 on success."""
        exit_code = main(["--db", self.db_path, "add", "Test"])
        self.assertEqual(exit_code, 0)

    def test_main_with_invalid_db_path(self):
        """Test main with invalid database path (directory)."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # Try to use a directory as database path
            invalid_path = tempfile.gettempdir()
            exit_code = main(["--db", invalid_path, "add", "Test"])
            
            # Should return error code
            self.assertNotEqual(exit_code, 0)


class TestConfigureLogging(unittest.TestCase):
    """Test suite for logging configuration."""

    def test_configure_logging_info(self):
        """Test configuring logging with INFO level."""
        # Just verify it doesn't raise an error
        configure_logging("INFO")

    def test_configure_logging_debug(self):
        """Test configuring logging with DEBUG level."""
        configure_logging("DEBUG")

    def test_configure_logging_invalid_level(self):
        """Test configuring logging with invalid level defaults to INFO."""
        # Should not raise an error, defaults to INFO
        configure_logging("INVALID")


if __name__ == "__main__":
    unittest.main()
