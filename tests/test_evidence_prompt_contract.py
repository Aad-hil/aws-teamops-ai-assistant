"""Static guardrails for source-controlled Harness prompt, no AWS or pytest needed."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROMPT = (ROOT / "prompts/evidence-grounded-rca-system.md").read_text(encoding="utf-8")

class EvidencePromptContract(unittest.TestCase):
    def test_budget(self):
        self.assertLess(len(PROMPT), 20000)
    def test_scope_and_tool_routing(self):
        for value in ("CloudWatch logs not retrieved", "Glue diagnostics", "customer-ingestion", "synthetic", "read-only"):
            self.assertIn(value, PROMPT)
    def test_grounded_demo(self):
        for value in ("--demo-mode", "DEMO_ETL_VALIDATION_FAILURE", "Python shell", "earlier SUCCEEDED", "SSM"):
            self.assertIn(value, PROMPT)
    def test_no_hallucinated_recovery(self):
        for value in ("Do not invent CloudWatch alarms", "Do not invent SSM", "no customer-data writes", "Requires authorization"):
            self.assertIn(value, PROMPT)

if __name__ == "__main__":
    unittest.main()
