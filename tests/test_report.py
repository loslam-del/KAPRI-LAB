import unittest
from unittest.mock import patch
from tools.report import build_report, markdown

class ReportTests(unittest.TestCase):
    @patch.dict("os.environ", {
        "LAB_TEST_OUTCOME": "success",
        "ANDROID_BUILD_OUTCOME": "failure",
        "SOURCE_REPOSITORY": "loslam-del/K.A.P.R.I",
        "SOURCE_COMMIT": "abc123",
        "WORKFLOW_RUN": "https://example.invalid/run/1",
    }, clear=True)
    def test_report_captures_workflow_outcomes(self):
        result = build_report()
        self.assertEqual(result["lab_unit_tests"], "success")
        self.assertEqual(result["android_build_and_unit_tests"], "failure")
        self.assertEqual(result["source_commit_or_trigger_sha"], "abc123")
        self.assertTrue(result["device_testing_required"])

    def test_markdown_contains_manual_device_checklist(self):
        result = {
            "generated_at": "2026-01-01T00:00:00+00:00",
            "source_repository": "owner/repo",
            "source_commit_or_trigger_sha": "abc",
            "lab_unit_tests": "success",
            "android_build_and_unit_tests": "success",
            "device_testing_required": True,
            "note": "Manual test still needed.",
            "workflow_run": "",
        }
        output = markdown(result)
        self.assertIn("Install the generated APK", output)
        self.assertIn("Manual test still needed.", output)

if __name__ == "__main__":
    unittest.main()
