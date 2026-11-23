"""Obvious secret and private-path checks.

A clean result does not prove the tree has no personal data or hidden
instructions. It only shows these patterns were absent.
"""

import unittest
from pathlib import Path

from ira.hygiene import find_obvious_secrets, private_path_findings, scan_tracked_text

ROOT = Path(__file__).resolve().parents[1]


class HygieneTest(unittest.TestCase):
    def test_obvious_secret_shapes_are_detected(self):
        key = "AKIA" + "IOSFODNN7EXAMPLE"
        self.assertTrue(find_obvious_secrets(key))
        self.assertTrue(find_obvious_secrets("-----BEGIN " + "RSA PRIVATE KEY-----"))
        self.assertTrue(find_obvious_secrets("github_pat_" + ("a" * 22)))
        self.assertEqual(find_obvious_secrets("the word token is not a credential"), [])

    def test_private_research_paths_are_rejected(self):
        findings = private_path_findings(
            [
                "watchlists/names.txt",
                "holdings/account.json",
                "decision-logs/today.md",
                "preferences/follows.json",
                ".env",
                "README.md",
            ]
        )
        self.assertEqual(len(findings), 5)
        self.assertFalse(any("README.md" in finding for finding in findings))

    def test_tracked_tree_has_no_obvious_secret_or_private_path(self):
        self.assertEqual(scan_tracked_text(ROOT), [])


if __name__ == "__main__":
    unittest.main()
