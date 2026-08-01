from __future__ import annotations

from pathlib import PureWindowsPath
import unittest

from pc_connection.path_policy import (
    PathPolicyError,
    resolve_remote_read,
    resolve_runtime_write,
)


class PathPolicyTests(unittest.TestCase):
    def test_read_root_alias_resolves_normal_path(self) -> None:
        result = resolve_remote_read("VERA_ROOT", r"models\base\config.json")
        self.assertEqual(
            result.absolute_path,
            PureWindowsPath(r"C:\VERA\models\base\config.json"),
        )

    def test_user_vera_root_is_distinct(self) -> None:
        result = resolve_remote_read(
            "USER_VERA_ROOT",
            r"v0.3.2-release\receipt.json",
        )
        self.assertEqual(
            result.absolute_path,
            PureWindowsPath(
                r"C:\Users\patri\VERA\v0.3.2-release\receipt.json"
            ),
        )

    def test_unknown_root_alias_fails(self) -> None:
        with self.assertRaisesRegex(PathPolicyError, "unknown"):
            resolve_remote_read("C_DRIVE", "Windows")

    def test_remote_read_cannot_expose_writable_runtime(self) -> None:
        for value in (r"PCCC\state.db", r"pccc\logs\agent.log"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(PathPolicyError, "runtime"):
                    resolve_remote_read("VERA_ROOT", value)

    def test_write_is_confined_to_pccc(self) -> None:
        result = resolve_runtime_write(r"artifacts\staging\part-0001")
        self.assertEqual(
            result.absolute_path,
            PureWindowsPath(
                r"C:\VERA\PCCC\artifacts\staging\part-0001"
            ),
        )

    def test_traversal_is_rejected(self) -> None:
        for value in (
            r"..\Windows\system.ini",
            r"models\..\..\Windows",
            "../escape",
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(PathPolicyError, "dot"):
                    resolve_remote_read("VERA_ROOT", value)

    def test_absolute_unc_device_and_ads_paths_are_rejected(self) -> None:
        cases = (
            r"C:\Windows\win.ini",
            r"\\server\share\file",
            r"\\?\C:\VERA\file",
            r"\\.\PhysicalDrive0",
            r"file.txt:secret",
        )
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(PathPolicyError):
                    resolve_remote_read("VERA_ROOT", value)

    def test_reserved_names_and_trailing_characters_are_rejected(self) -> None:
        for value in (r"CON.txt", r"folder\NUL", "name. ", "name."):
            with self.subTest(value=value):
                with self.assertRaises(PathPolicyError):
                    resolve_runtime_write(value)

    def test_mixed_separator_escape_is_rejected(self) -> None:
        with self.assertRaisesRegex(PathPolicyError, "dot"):
            resolve_remote_read("VERA_ROOT", r"models/../../Windows")


if __name__ == "__main__":
    unittest.main()
