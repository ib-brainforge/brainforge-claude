#!/usr/bin/env python3
"""
Check dependencies for issues: circular deps, banned packages, version conflicts.

TODO: Customize banned packages and version rules for your organization.

Usage:
    python check-dependencies.py /path/to/service
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set


# -----------------------------------------------------------------------------
# Configuration
# TODO: Customize for your organization
# -----------------------------------------------------------------------------

# Packages that should not be used
BANNED_PACKAGES = {
    # Example banned packages with reasons
    # "lodash": "Use native ES6+ methods or lodash-es for tree-shaking",
    # "moment": "Use date-fns or dayjs instead",
    # "request": "Deprecated, use axios or node-fetch",
}

# Packages that require approval for specific reasons
REQUIRES_APPROVAL = {
    # "puppeteer": "Heavy dependency, needs security review",
}

# Version constraints (package -> constraint)
VERSION_CONSTRAINTS = {
    # "typescript": ">=4.5.0",
    # "react": ">=17.0.0",
}

# Internal package prefixes (for circular dependency detection)
INTERNAL_PREFIXES = [
    "@your-org/",  # TODO: Set your org scope
]


# -----------------------------------------------------------------------------
# Dependency Parsing
# -----------------------------------------------------------------------------

def parse_package_json(filepath: Path) -> Dict[str, Any]:
    """Parse package.json and extract dependencies."""
    with open(filepath) as f:
        pkg = json.load(f)

    return {
        "name": pkg.get("name", "unknown"),
        "version": pkg.get("version", "0.0.0"),
        "dependencies": pkg.get("dependencies", {}),
        "devDependencies": pkg.get("devDependencies", {}),
        "peerDependencies": pkg.get("peerDependencies", {}),
    }


def parse_requirements_txt(filepath: Path) -> Dict[str, str]:
    """Parse requirements.txt and extract dependencies."""
    deps = {}
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            # Handle various formats: pkg, pkg==1.0, pkg>=1.0, pkg[extra]
            match = re.match(r"^([a-zA-Z0-9_-]+)(?:\[.*\])?(?:([<>=!]+)(.+))?", line)
            if match:
                pkg = match.group(1).lower()
                version = f"{match.group(2) or ''}{match.group(3) or ''}".strip()
                deps[pkg] = version or "*"
    return deps


def parse_go_mod(filepath: Path) -> Dict[str, str]:
    """Parse go.mod and extract dependencies."""
    deps = {}
    content = filepath.read_text()
    in_require = False

    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("require ("):
            in_require = True
            continue
        if in_require and line == ")":
            in_require = False
            continue
        if in_require or line.startswith("require "):
            parts = line.replace("require ", "").split()
            if len(parts) >= 2:
                deps[parts[0]] = parts[1]

    return deps


# -----------------------------------------------------------------------------
# Validation Logic
# -----------------------------------------------------------------------------

def check_banned_packages(
    deps: Dict[str, str],
    dep_type: str = "dependencies"
) -> List[Dict[str, Any]]:
    """Check for banned packages."""
    issues = []
    for pkg, version in deps.items():
        pkg_lower = pkg.lower()
        if pkg_lower in BANNED_PACKAGES:
            issues.append({
                "severity": "ERROR",
                "type": "banned_package",
                "package": pkg,
                "version": version,
                "dep_type": dep_type,
                "reason": BANNED_PACKAGES[pkg_lower]
            })
        elif pkg_lower in REQUIRES_APPROVAL:
            issues.append({
                "severity": "WARNING",
                "type": "requires_approval",
                "package": pkg,
                "version": version,
                "dep_type": dep_type,
                "reason": REQUIRES_APPROVAL[pkg_lower]
            })
    return issues


def check_version_constraints(
    deps: Dict[str, str],
    dep_type: str = "dependencies"
) -> List[Dict[str, Any]]:
    """
    Check version constraints.

    TODO: Implement proper semver comparison if needed.
    """
    issues = []
    for pkg, version in deps.items():
        if pkg in VERSION_CONSTRAINTS:
            constraint = VERSION_CONSTRAINTS[pkg]
            # Simple check - you may want more sophisticated semver comparison
            issues.append({
                "severity": "INFO",
                "type": "version_check",
                "package": pkg,
                "version": version,
                "constraint": constraint,
                "dep_type": dep_type,
                "message": f"Version {version} should satisfy {constraint}"
            })
    return issues


def find_internal_deps(
    deps: Dict[str, str],
    prefixes: List[str]
) -> Set[str]:
    """Find internal/org dependencies."""
    internal = set()
    for pkg in deps:
        for prefix in prefixes:
            if pkg.startswith(prefix):
                internal.add(pkg)
                break
    return internal


def check_circular_dependencies(
    service_path: Path,
    internal_deps: Set[str]
) -> List[Dict[str, Any]]:
    """
    Check for potential circular dependencies.

    TODO: This is a simplified check. For full circular detection,
    you'd need to analyze the dependency graph across all services.
    """
    issues = []

    # For now, just flag if internal deps exist (actual circular check
    # requires analyzing multiple repos)
    if internal_deps:
        issues.append({
            "severity": "INFO",
            "type": "internal_deps",
            "packages": list(internal_deps),
            "message": "Internal dependencies found - verify no circular dependencies"
        })

    return issues


def validate_dependencies(service_path: Path) -> Dict[str, Any]:
    """
    Run all dependency validations.
    """
    result = {
        "service_path": str(service_path),
        "status": "PASS",
        "dependencies_found": False,
        "issues": [],
        "summary": {}
    }

    all_deps = {}

    # Check package.json (Node.js)
    pkg_json = service_path / "package.json"
    if pkg_json.exists():
        result["dependencies_found"] = True
        pkg_data = parse_package_json(pkg_json)

        for dep_type in ["dependencies", "devDependencies", "peerDependencies"]:
            deps = pkg_data.get(dep_type, {})
            if deps:
                result["summary"][f"npm_{dep_type}"] = len(deps)
                all_deps.update(deps)

                result["issues"].extend(check_banned_packages(deps, dep_type))
                result["issues"].extend(check_version_constraints(deps, dep_type))

        # Check for internal deps
        all_npm_deps = {
            **pkg_data.get("dependencies", {}),
            **pkg_data.get("devDependencies", {}),
            **pkg_data.get("peerDependencies", {})
        }
        internal = find_internal_deps(all_npm_deps, INTERNAL_PREFIXES)
        result["issues"].extend(check_circular_dependencies(service_path, internal))

    # Check requirements.txt (Python)
    requirements = service_path / "requirements.txt"
    if requirements.exists():
        result["dependencies_found"] = True
        deps = parse_requirements_txt(requirements)
        result["summary"]["pip_dependencies"] = len(deps)

        result["issues"].extend(check_banned_packages(deps, "pip"))
        result["issues"].extend(check_version_constraints(deps, "pip"))

    # Check go.mod (Go)
    go_mod = service_path / "go.mod"
    if go_mod.exists():
        result["dependencies_found"] = True
        deps = parse_go_mod(go_mod)
        result["summary"]["go_dependencies"] = len(deps)

        result["issues"].extend(check_banned_packages(deps, "go"))

    # Determine overall status
    error_count = len([i for i in result["issues"] if i["severity"] == "ERROR"])
    warning_count = len([i for i in result["issues"] if i["severity"] == "WARNING"])

    if error_count > 0:
        result["status"] = "FAIL"
    elif warning_count > 0:
        result["status"] = "WARN"

    result["issue_count"] = {
        "errors": error_count,
        "warnings": warning_count,
        "info": len([i for i in result["issues"] if i["severity"] == "INFO"])
    }

    return result


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Check dependencies for issues"
    )
    parser.add_argument(
        "service_path",
        help="Path to service directory"
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
    service_path = Path(args.service_path).resolve()

    if not service_path.is_dir():
        print(f"Error: {service_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    result = validate_dependencies(service_path)

    if args.format == "json":
        output = json.dumps(result, indent=2)
    else:
        lines = [
            f"Dependency Check: {result['status']}",
            f"Service: {service_path.name}",
            ""
        ]
        if result["summary"]:
            lines.append("Dependencies found:")
            for key, count in result["summary"].items():
                lines.append(f"  {key}: {count}")
            lines.append("")

        if result["issues"]:
            lines.append("Issues:")
            for issue in result["issues"]:
                if issue["severity"] == "ERROR":
                    prefix = "❌"
                elif issue["severity"] == "WARNING":
                    prefix = "⚠️"
                else:
                    prefix = "ℹ️"
                msg = issue.get("reason") or issue.get("message", str(issue))
                lines.append(f"  {prefix} [{issue['type']}] {issue.get('package', '')}: {msg}")
        else:
            lines.append("✅ No dependency issues found")

        output = "\n".join(lines)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        print(output)

    sys.exit(0 if result["status"] != "FAIL" else 1)


if __name__ == "__main__":
    main()
