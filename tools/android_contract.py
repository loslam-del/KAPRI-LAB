"""Validate KAPRI Android identity before building an update APK."""
from pathlib import Path
import re
import sys

GRADLE_FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("source/app/build.gradle.kts")
EXPECTED_APPLICATION_ID = "com.example.screenai"

def main() -> int:
    if not GRADLE_FILE.is_file():
        print(f"ERROR: Gradle config not found: {GRADLE_FILE}")
        return 2
    source = GRADLE_FILE.read_text(encoding="utf-8")
    app_id = re.search(r'applicationId\s*=\s*"([^"]+)"', source)
    version_code = re.search(r"versionCode\s*=\s*(\d+)", source)
    version_name = re.search(r'versionName\s*=\s*"([^"]+)"', source)
    errors = []
    if not app_id:
        errors.append("applicationId is missing")
    elif app_id.group(1) != EXPECTED_APPLICATION_ID:
        errors.append(f"applicationId changed: expected {EXPECTED_APPLICATION_ID}, found {app_id.group(1)}")
    if not version_code:
        errors.append("versionCode is missing")
    elif int(version_code.group(1)) < 1:
        errors.append("versionCode must be >= 1")
    if not version_name:
        errors.append("versionName is missing")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Android identity OK: {app_id.group(1)}, versionCode={version_code.group(1)}, versionName={version_name.group(1)}")
    print("NOTE: update installation also requires the same signing certificate as the installed app.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
