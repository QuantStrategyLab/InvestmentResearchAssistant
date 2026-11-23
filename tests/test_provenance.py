"""Lock vendored skills to the reviewed upstream commits and byte digests."""

import hashlib
import json
import unittest
from pathlib import Path

from ira.provenance import verify_manifest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "upstream" / "manifest.json"

INVEST_COMMIT = "4d61af4ae5545a8fae8a78642c4f1a56ea3a20ec"
GROK_COMMIT = "d3d4b493d4d66cc08c31e13626ac3e750613c8b2"
ORG_DOCS_COMMIT = "1de428f00aeef77ba939edfd3420b202c7166953"
GOVERNANCE_COMMIT = "3d44e3d057681d5ae2730ad76af2f53b72d26767"

INVEST_SKILLS = (
    "plugins/us-stock-analysis/skills/fact-check/SKILL.md",
    "plugins/us-stock-analysis/skills/earnings-preview/SKILL.md",
    "plugins/us-stock-analysis/skills/catalyst-calendar/SKILL.md",
    "plugins/us-stock-analysis/skills/bear-case/SKILL.md",
    "plugins/us-stock-analysis/skills/etf-analysis/SKILL.md",
)


class ProvenanceTest(unittest.TestCase):
    def test_manifest_matches_bytes_and_approved_pins(self):
        errors = verify_manifest(ROOT, MANIFEST)
        self.assertEqual(errors, [])
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        by_name = {source["name"]: source for source in manifest["sources"]}
        invest = by_name["InvestSkill"]
        grok = by_name["grok-research"]
        self.assertEqual(invest["commit"], INVEST_COMMIT)
        self.assertEqual(grok["commit"], GROK_COMMIT)
        self.assertEqual(invest["license"], "MIT")
        self.assertEqual(grok["license"], "MIT")
        self.assertIn("Copyright (c) 2026 yennanliu", (ROOT / invest["license_path"]).read_text())
        grok_license = (ROOT / grok["license_path"]).read_text()
        self.assertIn("Copyright (c) 2026 Kun Chen", grok_license)
        self.assertIn("Copyright (c) 2026 grok-research", grok_license)
        invest_paths = [item["upstream_path"] for item in invest["files"] if item["upstream_path"].endswith("SKILL.md")]
        self.assertEqual(invest_paths, list(INVEST_SKILLS))
        self.assertEqual(
            [item["upstream_path"] for item in grok["files"]],
            ["skills/adversarial-review/SKILL.md"],
        )
        self.assertEqual(manifest["org_docs_commit"], ORG_DOCS_COMMIT)
        self.assertEqual(manifest["pr_governance_commit"], GOVERNANCE_COMMIT)
        for source in manifest["sources"]:
            self.assertEqual(len(source["commit"]), 40)
            for item in source["files"]:
                blob = (ROOT / item["vendor_path"]).read_bytes()
                self.assertEqual(hashlib.sha256(blob).hexdigest(), item["sha256"])
                header = f"blob {len(blob)}\0".encode()
                self.assertEqual(hashlib.sha1(header + blob).hexdigest(), item["git_blob_sha1"])

    def test_vendor_tree_has_no_unlisted_file(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        listed = set()
        for source in manifest["sources"]:
            listed.add(source["license_path"])
            for item in source["files"]:
                listed.add(item["vendor_path"])
        on_disk = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "third_party").rglob("*")
            if path.is_file()
        }
        self.assertEqual(on_disk, listed)


if __name__ == "__main__":
    unittest.main()
