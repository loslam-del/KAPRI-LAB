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
        self.assertEqual(result["apk_variant"], "debug")
        self.assertFalse(result["update_installation_ready"])
        self.assertTrue(result["device_testing_required"])

    def test_markdown_contains_device_checklist_and_update_warning(self):
        result = {
            "generated_at": "2026-01-01T00:00:00+00:00",
            "source_repository": "owner/repo",
            "source_commit_or_trigger_sha": "abc",
            "lab_unit_tests": "success",
            "android_build_and_unit_tests": "success",
            "apk_variant": "debug",
            "update_installation_ready": False,
            "device_testing_required": True,
            "note": "Manual test still needed.",
            "workflow_run": "",
        }
        output = markdown(result)
        self.assertIn("Install the generated APK", output)
        self.assertIn("APK variant: **debug**", output)
        self.assertIn("Update installation ready: **False**", output)
        self.assertIn("Manual test still needed.", output)


if __name__ == "__main__":
    unittest.main()
