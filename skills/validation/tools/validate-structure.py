#!/usr/bin/env python3
"""
Validate service directory structure against architectural standards.

TODO: Customize required structure for your organization.

Usage:
    python validate-structure.py /path/to/service --type backend
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any


# -----------------------------------------------------------------------------
# Structure Requirements
# TODO: Define required structure for each service type
# -----------------------------------------------------------------------------

STRUCTURE_REQUIREMENTS = {
    "frontend": {
        "required_files": [
            "package.json",
            "README.md",
            # TODO: Add your required files
            # "tsconfig.json",
            # ".eslintrc.js",
        ],
        "required_dirs": [
            "src",
            # TODO: Add your required directories
            # "src/components",
            # "src/pages",
            # "public",
        ],
        "recommended_files": [
            "ARCHITECTURE.md",
            ".env.example",
            "Dockerfile",
        ],
        "recommended_dirs": [
            "tests",
            "docs",
        ]
    },
    "backend": {
        "required_files": [
            "README.md",
            # TODO: Add your required files
            # "Dockerfile",
            # "docker-compose.yml",
        ],
        "required_dirs": [
            "src",
            # TODO: Add your required directories
            # "src/controllers",
            # "src/services",
            # "src/models",
        ],
        "recommended_files": [
            "ARCHITECTURE.md",
            ".env.example",
            "Makefile",
        ],
        "recommended_dirs": [
            "tests",
            "docs",
            "migrations",
        ]
    },
    "infrastructure": {
        "required_files": [
            "README.md",
            # TODO: Add your required files
        ],
        "required_dirs": [
            # TODO: Add your required directories
            # "modules",
            # "environments",
        ],
        "recommended_files": [
            "ARCHITECTURE.md",
        ],
        "recommended_dirs": [
            "docs",
        ]
    },
    "core_library": {
        "required_files": [
            "README.md",
            # TODO: Add your required files
            # "CHANGELOG.md",
        ],
        "required_dirs": [
            "src",
            # TODO: Add your required directories
        ],
        "recommended_files": [
            "ARCHITECTURE.md",
            "CONTRIBUTING.md",
        ],
        "recommended_dirs": [
            "tests",
            "docs",
            "examples",
        ]
    }
}


# -----------------------------------------------------------------------------
# Validation Logic
# -----------------------------------------------------------------------------

def validate_structure(
    service_path: Path,
    service_type: str
) -> Dict[str, Any]:
    """
    Validate service structure against requirements.

    Returns:
        {
            "status": "PASS|WARN|FAIL",
            "required": {"missing_files": [], "missing_dirs": []},
            "recommended": {"missing_files": [], "missing_dirs": []},
            "extra_info": {}
        }
    """
    if service_type not in STRUCTURE_REQUIREMENTS:
        return {
            "status": "FAIL",
            "error": f"Unknown service type: {service_type}",
            "valid_types": list(STRUCTURE_REQUIREMENTS.keys())
        }

    reqs = STRUCTURE_REQUIREMENTS[service_type]
    result = {
        "service_path": str(service_path),
        "service_type": service_type,
        "status": "PASS",
        "required": {
            "missing_files": [],
            "missing_dirs": [],
            "present_files": [],
            "present_dirs": []
        },
        "recommended": {
            "missing_files": [],
            "missing_dirs": [],
            "present_files": [],
            "present_dirs": []
        }
    }

    # Check required files
    for filename in reqs.get("required_files", []):
        filepath = service_path / filename
        if filepath.exists():
            result["required"]["present_files"].append(filename)
        else:
            result["required"]["missing_files"].append(filename)
            result["status"] = "FAIL"

    # Check required directories
    for dirname in reqs.get("required_dirs", []):
        dirpath = service_path / dirname
        if dirpath.is_dir():
            result["required"]["present_dirs"].append(dirname)
        else:
            result["required"]["missing_dirs"].append(dirname)
            result["status"] = "FAIL"

    # Check recommended files
    for filename in reqs.get("recommended_files", []):
        filepath = service_path / filename
        if filepath.exists():
            result["recommended"]["present_files"].append(filename)
        else:
            result["recommended"]["missing_files"].append(filename)
            if result["status"] == "PASS":
                result["status"] = "WARN"

    # Check recommended directories
    for dirname in reqs.get("recommended_dirs", []):
        dirpath = service_path / dirname
        if dirpath.is_dir():
            result["recommended"]["present_dirs"].append(dirname)
        else:
            result["recommended"]["missing_dirs"].append(dirname)
            if result["status"] == "PASS":
                result["status"] = "WARN"

    # Generate issues list
    issues = []
    for f in result["required"]["missing_files"]:
        issues.append({
            "severity": "ERROR",
            "type": "missing_file",
            "path": f,
            "message": f"Required file missing: {f}"
        })
    for d in result["required"]["missing_dirs"]:
        issues.append({
            "severity": "ERROR",
            "type": "missing_dir",
            "path": d,
            "message": f"Required directory missing: {d}"
        })
    for f in result["recommended"]["missing_files"]:
        issues.append({
            "severity": "WARNING",
            "type": "missing_file",
            "path": f,
            "message": f"Recommended file missing: {f}"
        })
    for d in result["recommended"]["missing_dirs"]:
        issues.append({
            "severity": "WARNING",
            "type": "missing_dir",
            "path": d,
            "message": f"Recommended directory missing: {d}"
        })

    result["issues"] = issues
    result["issue_count"] = {
        "errors": len([i for i in issues if i["severity"] == "ERROR"]),
        "warnings": len([i for i in issues if i["severity"] == "WARNING"])
    }

    return result


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validate service directory structure"
    )
    parser.add_argument(
        "service_path",
        help="Path to service directory"
    )
    parser.add_argument(
        "--type", "-t",
        choices=list(STRUCTURE_REQUIREMENTS.keys()),
        help="Service type (auto-detected if not provided)"
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

    # Auto-detect type if not provided
    service_type = args.type
    if not service_type:
        # Import discover script for detection
        sys.path.insert(0, str(Path(__file__).parent))
        try:
            from discover_services import detect_service_type
            service_type = detect_service_type(service_path)
        except:
            pass

        if not service_type:
            print("Error: Could not detect service type. Use --type to specify.", file=sys.stderr)
            sys.exit(1)

    result = validate_structure(service_path, service_type)

    if args.format == "json":
        output = json.dumps(result, indent=2)
    else:
        # Text format
        lines = [
            f"Structure Validation: {result['status']}",
            f"Service: {service_path.name}",
            f"Type: {service_type}",
            ""
        ]
        if result["issues"]:
            lines.append("Issues:")
            for issue in result["issues"]:
                prefix = "❌" if issue["severity"] == "ERROR" else "⚠️"
                lines.append(f"  {prefix} {issue['message']}")
        else:
            lines.append("✅ All structure requirements met")
        output = "\n".join(lines)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        print(output)

    # Exit with error code if validation failed
    sys.exit(0 if result["status"] != "FAIL" else 1)


if __name__ == "__main__":
    main()
