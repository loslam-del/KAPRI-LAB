import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import android_contract


class AndroidContractTests(unittest.TestCase):
    def run_check(self, text):
        with tempfile.TemporaryDirectory() as directory:
            gradle_file = Path(directory) / "build.gradle.kts"
            gradle_file.write_text(text, encoding="utf-8")
            with patch.object(android_contract, "GRADLE_FILE", gradle_file):
                return android_contract.main()

    def test_accepts_fixed_package_identity(self):
        self.assertEqual(
            self.run_check(
                'applicationId = "com.example.screenai"\\n'
                'versionCode = 2\\n'
                'versionName = "1.1"\\n'
            ),
            0,
        )

    def test_accepts_environment_driven_version(self):
        self.assertEqual(
            self.run_check(
                'applicationId = "com.example.screenai"\\n'
                'versionCode = (System.getenv("KAPRI_VERSION_CODE")?.toIntOrNull() ?: 1)\\n'
                'versionName = System.getenv("KAPRI_VERSION_NAME") ?: "1.0"\\n'
            ),
            0,
        )

    def test_rejects_changed_package_identity(self):
        self.assertEqual(
            self.run_check(
                'applicationId = "com.other.package"\\n'
                'versionCode = 2\\n'
                'versionName = "1.1"\\n'
            ),
            1,
        )

    def test_rejects_missing_version_code(self):
        self.assertEqual(
            self.run_check(
                'applicationId = "com.example.screenai"\\n'
                'versionName = "1.1"\\n'
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()
