#!/usr/bin/env python3
"""Create a compact Markdown and JSON report from GitHub Actions outcomes."""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def build_report():
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_repository": os.getenv("SOURCE_REPOSITORY", "loslam-del/K.A.P.R.И"),
        "source_commit": os.getenv("SOURCE_COMMIT", "unknown"),
        "lab_unit_tests": os.getenv("LAB_TEST_OUTCOME", "not-run"),
        "android_build_and_unit_tests": os.getenv("ANDROID_BUILD_OUTCOME", "not-run"),
        "apk_variant": os.getenv("APK_VARIANT", "debug"),
        "update_installation_ready": False,
        "workflow_run": os.getenv("WORKFLOW_RUN", ""),
        "device_testing_required": True,
        "note": (
            "The lab artifact is a debug APK for testing. It is not guaranteed "
            "to update an installed app: Android requires the same package ID "
            "and compatible signing certificate. Physical-device testing is "
            "still required."
        ),
    }


def markdown(report):
    return "\n".join([
        "# KAPRI-LAB report", "",
        f"- Generated (UTC): {report['generated_at']}",
        f"- Source: `{report['source_repository']}`",
        f"- Source commit: `{report['source_commit']}`",
        f"- Lab unit tests: **{report['lab_unit_tests']}**",
        f"- Android build + unit tests: **{report['android_build_and_unit_tests']}**",
        f"- APK variant: **{report['apk_variant']}**",
        f"- Update installation ready: **{report['update_installation_ready']}**",
        f"- Device testing required: **{report['device_testing_required']}**", "",
        "## Manual verification",
        "- [ ] Install the generated APK on a test device.",
        "- [ ] Check launch, permissions, and basic navigation.",
        "- [ ] Verify relevant features in the intended app/game.",
        "- [ ] Review logs and investigate unexpected behavior.", "",
        f"> {report['note']}", "",
        f"Workflow: {report['workflow_run'] or 'not available'}", ""
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="reports/report.md")
    parser.add_argument("--json-output", default="reports/report.json")
    args = parser.parse_args()
    report = build_report()
    md_path, json_path = Path(args.output), Path(args.json_output)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
