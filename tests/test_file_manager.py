from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.utils.file_manager import WorkspaceFileManager, WorkspacePathError


class FileManagerTests(unittest.TestCase):
    def test_write_and_read(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            manager = WorkspaceFileManager(td)
            manager.write_text("a/b.txt", "hello")
            self.assertEqual(manager.read_text("a/b.txt"), "hello")

    def test_path_traversal_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            manager = WorkspaceFileManager(td)
            with self.assertRaises(WorkspacePathError):
                manager.read_text("../outside.txt")

    def test_list_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            manager = WorkspaceFileManager(td)
            manager.write_text("x.txt", "1")
            manager.write_text("d/y.txt", "2")
            files = manager.list_files(".")
            self.assertEqual(files, ["d/y.txt", "x.txt"])


if __name__ == "__main__":
    unittest.main()
