"""frozen vs 개발 경로 스모크 (unittest, 외부 의존 없음)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from macro_studio import storage


class FrozenPathTests(unittest.TestCase):
    def test_dev_not_frozen(self) -> None:
        self.assertFalse(storage.is_frozen())

    def test_dev_project_root_contains_package(self) -> None:
        root = storage.get_project_root()
        self.assertTrue((root / "macro_studio").is_dir())
        self.assertEqual(storage.get_macros_dir(), root / "macros")

    def test_frozen_uses_exe_parent_not_meipass(self) -> None:
        # 절대 경로(플랫폼 공통) — Path.resolve() 가 cwd 에 붙지 않도록
        with tempfile.TemporaryDirectory() as td:
            app_dir = Path(td) / "MacroStudio"
            app_dir.mkdir()
            fake_exe = app_dir / "MacroStudio.exe"
            fake_exe.write_bytes(b"")
            fake_meipass = Path(td) / "_MEI123"
            fake_meipass.mkdir()
            with mock.patch.object(sys, "frozen", True, create=True), mock.patch.object(
                sys, "executable", str(fake_exe)
            ), mock.patch.object(sys, "_MEIPASS", str(fake_meipass), create=True):
                root = storage.get_project_root()
                macros = storage.get_macros_dir()
            self.assertEqual(root, app_dir.resolve())
            self.assertEqual(macros, app_dir.resolve() / "macros")
            self.assertNotEqual(root, fake_meipass.resolve())
            self.assertFalse(str(macros).startswith(str(fake_meipass.resolve())))


if __name__ == "__main__":
    unittest.main()
