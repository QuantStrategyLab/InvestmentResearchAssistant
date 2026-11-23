"""Static repository contracts. These do not exercise a live model."""

import json
import re
import unittest
from pathlib import Path

from ira.card import REQUIRED_FIELDS, validate_card

ROOT = Path(__file__).resolve().parents[1]
SHA = re.compile(r"^[0-9a-f]{40}$")
USES = re.compile(r"(?m)^\s*(?:-\s*)?uses:\s*(\S+)")


class RepoContractTest(unittest.TestCase):
    def test_schema_required_fields_match_the_validator(self):
        schema = json.loads((ROOT / "schema" / "research-card.schema.json").read_text())
        self.assertEqual(tuple(schema["required"]), REQUIRED_FIELDS)
        properties = schema["properties"]
        self.assertNotIn("order", properties)
        self.assertNotIn("account", properties)
        self.assertNotIn("target_shares", properties)
        self.assertEqual(properties["execution_allowed"]["const"], False)

    def test_synthetic_example_validates_and_is_labeled(self):
        example = json.loads(
            (ROOT / "examples" / "synthetic-research-card.json").read_text()
        )
        self.assertIs(example["synthetic"], True)
        self.assertTrue(
            all("example.test" in item["url"] for item in example["primary_evidence"])
        )
        self.assertEqual(validate_card(example), [])

    def test_readme_states_the_bot_gap_and_research_boundary(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("尚未在 Grok Bot 中测试", readme)
        self.assertIn("execution_allowed", readme)
        self.assertIn("false", readme)
        self.assertIn("美国股票和 ETF", readme)
        for example in (
            "请只做研究",
            "不要形成交易指令",
            "从公开讨论里做一次有边界的主题发现",
        ):
            self.assertIn(example, readme)

    def test_workflows_document_both_paths_and_optional_x(self):
        text = (ROOT / "docs" / "workflows.md").read_text(encoding="utf-8")
        self.assertIn("流程 A", text)
        self.assertIn("流程 B", text)
        self.assertIn("不是每项研究的必经步骤", text)
        self.assertIn("execution_allowed", text)

    def test_adapters_keep_upstream_files_unmodified(self):
        adapter = (ROOT / "adapters" / "research-only.md").read_text(encoding="utf-8")
        self.assertIn("third_party/", adapter)
        self.assertIn("简体中文", (ROOT / "adapters" / "simplified-chinese.md").read_text())
        self.assertIn("execution_allowed", (ROOT / "adapters" / "research-card.md").read_text())
        self.assertFalse((ROOT / "third_party").joinpath("ADAPTER.md").exists())

    def test_governance_workflows_are_pinned_and_unprivileged(self):
        workflow_dir = ROOT / ".github" / "workflows"
        names = {path.name for path in workflow_dir.glob("*.yml")}
        self.assertTrue(
            {
                "risk-gate.yml",
                "pr-review-signal.yml",
                "codex-nudge.yml",
                "gitleaks.yml",
                "required-gitleaks.yml",
                "weekly-gitleaks.yml",
                "tests.yml",
            }.issubset(names)
        )
        privileged = []
        for path in sorted(workflow_dir.glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("contents: write", text, path.name)
            self.assertNotIn("pull_request_target", text) if path.name != "risk-gate.yml" else None
            if path.name != "risk-gate.yml" and "pull_request_target" in text:
                privileged.append(path.name)
            if path.name == "risk-gate.yml":
                self.assertIn("pull_request_target", text)
                self.assertNotIn("actions/checkout", text)
            for match in USES.findall(text):
                pin = match.rsplit("@", 1)
                self.assertEqual(len(pin), 2, match)
                self.assertRegex(pin[1], SHA)
            self.assertNotIn("SECRET_SCAN_BASELINE_B64", text)
        self.assertEqual(privileged, [])
        gitleaks = (workflow_dir / "gitleaks.yml").read_text(encoding="utf-8")
        self.assertIn("name: Gitleaks", gitleaks)
        required = (workflow_dir / "required-gitleaks.yml").read_text(encoding="utf-8")
        self.assertIn("name: Secret scan", required)
        self.assertIn(
            "0da4da68433b803cda17d3f84e29875a94a32273",
            required,
        )
        self.assertIn(
            "3d44e3d057681d5ae2730ad76af2f53b72d26767",
            (workflow_dir / "risk-gate.yml").read_text(encoding="utf-8"),
        )
        tests = (workflow_dir / "tests.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request:", tests)
        self.assertNotIn("pull_request_target", tests)

    def test_policy_carries_no_account_identity(self):
        policy = json.loads((ROOT / ".github" / "governance" / "policy.json").read_text())
        self.assertEqual(policy["version"], "pr-governance/v3")
        self.assertEqual(policy["mode"], "enforce")
        self.assertNotIn("reviewer", policy)
        self.assertNotIn("owner", policy)
        self.assertNotIn("user_id", json.dumps(policy))

    def test_activation_gaps_are_explicit(self):
        text = (ROOT / "docs" / "activation-gaps.md").read_text(encoding="utf-8")
        for phrase in (
            "branch protection",
            "secret scanning",
            "尚未",
            "Grok Bot",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
