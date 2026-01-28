#!/usr/bin/env python3
"""
Aggregate validation results from multiple validators.

Combines results from subagent validations into a unified report.

Usage:
    python aggregate-results.py result1.json result2.json --output report.json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


def aggregate_results(result_files: List[Path]) -> Dict[str, Any]:
    """
    Aggregate multiple validation results into unified report.
    """
    report = {
        "generated_at": datetime.now().isoformat(),
        "overall_status": "PASS",
        "summary": {
            "total_validators": 0,
            "passed": 0,
            "warned": 0,
            "failed": 0,
            "total_issues": 0,
            "errors": 0,
            "warnings": 0
        },
        "validators": [],
        "all_issues": [],
        "by_severity": {
            "ERROR": [],
            "WARNING": [],
            "INFO": []
        },
        "by_category": {}
    }

    for result_file in result_files:
        if not result_file.exists():
            report["validators"].append({
                "source": str(result_file),
                "status": "ERROR",
                "error": "File not found"
            })
            report["summary"]["failed"] += 1
            continue

        try:
            with open(result_file) as f:
                result = json.load(f)
        except json.JSONDecodeError as e:
            report["validators"].append({
                "source": str(result_file),
                "status": "ERROR",
                "error": f"Invalid JSON: {e}"
            })
            report["summary"]["failed"] += 1
            continue

        report["summary"]["total_validators"] += 1

        # Extract validator info
        validator_entry = {
            "source": str(result_file),
            "agent": result.get("agent", "unknown"),
            "status": result.get("status", "UNKNOWN"),
            "service": result.get("service") or result.get("service_path"),
        }

        # Count status
        status = result.get("status", "UNKNOWN")
        if status == "PASS":
            report["summary"]["passed"] += 1
        elif status == "WARN":
            report["summary"]["warned"] += 1
        else:
            report["summary"]["failed"] += 1

        # Extract issues
        issues = result.get("issues", [])
        if not issues and "issue_count" in result:
            # Some validators put issues in nested structures
            for key in result:
                if isinstance(result[key], dict) and "issues" in result[key]:
                    issues.extend(result[key]["issues"])

        validator_entry["issue_count"] = len(issues)
        report["validators"].append(validator_entry)

        for issue in issues:
            # Normalize issue format
            normalized = {
                "source": str(result_file),
                "agent": result.get("agent", "unknown"),
                "service": result.get("service") or result.get("service_path"),
                "severity": issue.get("severity", "WARNING"),
                "type": issue.get("type", "unknown"),
                "message": issue.get("message") or issue.get("reason") or str(issue),
                "path": issue.get("path"),
                "details": issue
            }

            report["all_issues"].append(normalized)

            # Categorize by severity
            severity = normalized["severity"]
            if severity in report["by_severity"]:
                report["by_severity"][severity].append(normalized)

            # Categorize by type
            issue_type = normalized["type"]
            if issue_type not in report["by_category"]:
                report["by_category"][issue_type] = []
            report["by_category"][issue_type].append(normalized)

            # Update counts
            report["summary"]["total_issues"] += 1
            if severity == "ERROR":
                report["summary"]["errors"] += 1
            elif severity == "WARNING":
                report["summary"]["warnings"] += 1

    # Determine overall status
    if report["summary"]["failed"] > 0 or report["summary"]["errors"] > 0:
        report["overall_status"] = "FAIL"
    elif report["summary"]["warned"] > 0 or report["summary"]["warnings"] > 0:
        report["overall_status"] = "WARN"

    return report


def format_text_report(report: Dict[str, Any]) -> str:
    """Format report as human-readable text."""
    lines = [
        "=" * 60,
        "ARCHITECTURE VALIDATION REPORT",
        f"Generated: {report['generated_at']}",
        "=" * 60,
        "",
        f"Overall Status: {report['overall_status']}",
        "",
        "Summary:",
        f"  Validators run: {report['summary']['total_validators']}",
        f"    Passed: {report['summary']['passed']}",
        f"    Warned: {report['summary']['warned']}",
        f"    Failed: {report['summary']['failed']}",
        "",
        f"  Total issues: {report['summary']['total_issues']}",
        f"    Errors: {report['summary']['errors']}",
        f"    Warnings: {report['summary']['warnings']}",
        "",
    ]

    if report["summary"]["errors"] > 0:
        lines.append("-" * 40)
        lines.append("ERRORS (must fix):")
        for issue in report["by_severity"]["ERROR"]:
            lines.append(f"  ❌ [{issue['agent']}] {issue['message']}")
            if issue["path"]:
                lines.append(f"     Path: {issue['path']}")
        lines.append("")

    if report["summary"]["warnings"] > 0:
        lines.append("-" * 40)
        lines.append("WARNINGS (should fix):")
        for issue in report["by_severity"]["WARNING"][:10]:  # Limit to first 10
            lines.append(f"  ⚠️  [{issue['agent']}] {issue['message']}")
        if len(report["by_severity"]["WARNING"]) > 10:
            lines.append(f"  ... and {len(report['by_severity']['WARNING']) - 10} more warnings")
        lines.append("")

    lines.append("-" * 40)
    lines.append("Validator Results:")
    for v in report["validators"]:
        status_icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(v["status"], "❓")
        lines.append(f"  {status_icon} {v['agent']}: {v['status']} ({v['issue_count']} issues)")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate validation results"
    )
    parser.add_argument(
        "results",
        nargs="+",
        help="Result JSON files to aggregate"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "text"],
        default="json",
        help="Output format"
    )

    args = parser.parse_args()
    result_files = [Path(f) for f in args.results]

    report = aggregate_results(result_files)

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = format_text_report(report)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(output)

    # Exit with appropriate code
    sys.exit(0 if report["overall_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
