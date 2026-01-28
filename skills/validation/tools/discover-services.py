#!/usr/bin/env python3
"""
Discover microservices in a multi-repo setup.

Scans directories for service indicators and outputs service registry.

TODO: Customize detection patterns for your repository structure.

Usage:
    python discover-services.py /path/to/repos --output services.json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional


# -----------------------------------------------------------------------------
# Service Detection Patterns
# TODO: Customize these for your repository structure
# -----------------------------------------------------------------------------

SERVICE_INDICATORS = {
    "frontend": {
        "files": ["package.json", "tsconfig.json"],
        "dirs": ["src/components", "src/pages", "app"],
        "content_patterns": {
            "package.json": ["react", "vue", "angular", "next", "nuxt"]
        }
    },
    "backend": {
        "files": ["requirements.txt", "go.mod", "pom.xml", "build.gradle", "Cargo.toml"],
        "dirs": ["src/main", "cmd", "internal", "app/controllers"],
        "content_patterns": {
            "package.json": ["express", "fastify", "nestjs", "koa"],
            "requirements.txt": ["flask", "django", "fastapi"]
        }
    },
    "infrastructure": {
        "files": ["main.tf", "Pulumi.yaml", "cloudformation.yaml"],
        "dirs": ["terraform", "pulumi", "k8s", "helm"]
    },
    "core_library": {
        "files": ["setup.py", "pyproject.toml"],
        "dirs": ["src", "lib"],
        "content_patterns": {
            "package.json": ["\"private\": false", "\"main\":"]
        }
    }
}

# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", "vendor", "dist", "build",
    "__pycache__", ".venv", "venv", ".terraform", ".next"
}


# -----------------------------------------------------------------------------
# Detection Logic
# -----------------------------------------------------------------------------

def detect_service_type(repo_path: Path) -> Optional[str]:
    """
    Detect what type of service/repo this is.

    TODO: Add more sophisticated detection if needed.
    """
    scores = {stype: 0 for stype in SERVICE_INDICATORS}

    for stype, indicators in SERVICE_INDICATORS.items():
        # Check for indicator files
        for filename in indicators.get("files", []):
            if (repo_path / filename).exists():
                scores[stype] += 2

        # Check for indicator directories
        for dirname in indicators.get("dirs", []):
            if (repo_path / dirname).is_dir():
                scores[stype] += 1

        # Check content patterns
        for filename, patterns in indicators.get("content_patterns", {}).items():
            filepath = repo_path / filename
            if filepath.exists():
                try:
                    content = filepath.read_text().lower()
                    for pattern in patterns:
                        if pattern.lower() in content:
                            scores[stype] += 3
                except:
                    pass

    # Return highest scoring type if above threshold
    max_score = max(scores.values())
    if max_score >= 2:
        return max(scores, key=scores.get)
    return None


def detect_framework(repo_path: Path, service_type: str) -> Optional[str]:
    """
    Detect specific framework used.

    TODO: Expand framework detection.
    """
    if service_type == "frontend":
        pkg_json = repo_path / "package.json"
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text())
                deps = {
                    **pkg.get("dependencies", {}),
                    **pkg.get("devDependencies", {})
                }
                if "react" in deps or "react-dom" in deps:
                    if "next" in deps:
                        return "nextjs"
                    return "react"
                if "vue" in deps:
                    if "nuxt" in deps:
                        return "nuxt"
                    return "vue"
                if "@angular/core" in deps:
                    return "angular"
            except:
                pass

    elif service_type == "backend":
        # Python
        requirements = repo_path / "requirements.txt"
        if requirements.exists():
            try:
                content = requirements.read_text().lower()
                if "fastapi" in content:
                    return "fastapi"
                if "django" in content:
                    return "django"
                if "flask" in content:
                    return "flask"
            except:
                pass

        # Node.js
        pkg_json = repo_path / "package.json"
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text())
                deps = pkg.get("dependencies", {})
                if "express" in deps:
                    return "express"
                if "@nestjs/core" in deps:
                    return "nestjs"
                if "fastify" in deps:
                    return "fastify"
            except:
                pass

        # Go
        if (repo_path / "go.mod").exists():
            return "go"

        # Java
        if (repo_path / "pom.xml").exists():
            return "spring"  # Assume Spring, customize as needed

    return None


def get_service_metadata(repo_path: Path) -> Dict[str, Any]:
    """
    Extract service metadata from various sources.

    TODO: Customize metadata extraction for your conventions.
    """
    metadata = {}

    # Try package.json
    pkg_json = repo_path / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text())
            metadata["name"] = pkg.get("name", repo_path.name)
            metadata["version"] = pkg.get("version")
            metadata["description"] = pkg.get("description")
        except:
            pass

    # Try pyproject.toml (basic parsing)
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists() and "name" not in metadata:
        try:
            content = pyproject.read_text()
            for line in content.split("\n"):
                if line.strip().startswith("name"):
                    metadata["name"] = line.split("=")[1].strip().strip('"\'')
                    break
        except:
            pass

    # Default name from directory
    if "name" not in metadata:
        metadata["name"] = repo_path.name

    return metadata


def discover_services(repos_root: Path) -> List[Dict[str, Any]]:
    """
    Discover all services in the repos root directory.

    Assumes each subdirectory is a separate repository/service.
    """
    services = []

    for item in repos_root.iterdir():
        if not item.is_dir():
            continue
        if item.name in SKIP_DIRS or item.name.startswith("."):
            continue

        service_type = detect_service_type(item)
        if service_type:
            metadata = get_service_metadata(item)
            framework = detect_framework(item, service_type)

            services.append({
                "name": metadata.get("name", item.name),
                "path": str(item.relative_to(repos_root)),
                "absolute_path": str(item),
                "type": service_type,
                "framework": framework,
                "metadata": metadata,
                "has_architecture_doc": (item / "ARCHITECTURE.md").exists(),
                "has_readme": (item / "README.md").exists(),
                "has_tests": any([
                    (item / "tests").is_dir(),
                    (item / "test").is_dir(),
                    (item / "__tests__").is_dir(),
                    (item / "spec").is_dir()
                ])
            })

    return services


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Discover microservices in a multi-repo setup"
    )
    parser.add_argument(
        "repos_root",
        help="Root directory containing repositories"
    )
    parser.add_argument(
        "--output", "-o",
        default="services.json",
        help="Output file (default: services.json)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "table"],
        default="json",
        help="Output format"
    )

    args = parser.parse_args()
    repos_root = Path(args.repos_root).resolve()

    if not repos_root.is_dir():
        print(f"Error: {repos_root} is not a directory", file=sys.stderr)
        sys.exit(1)

    print(f"Discovering services in {repos_root}...", file=sys.stderr)
    services = discover_services(repos_root)

    # Build registry
    registry = {
        "repos_root": str(repos_root),
        "service_count": len(services),
        "by_type": {},
        "services": services
    }

    for service in services:
        stype = service["type"]
        registry["by_type"][stype] = registry["by_type"].get(stype, 0) + 1

    if args.format == "json":
        output = json.dumps(registry, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Registry written to {args.output}", file=sys.stderr)
        else:
            print(output)
    else:
        # Table format
        print(f"\nDiscovered {len(services)} services:\n")
        print(f"{'Name':<30} {'Type':<15} {'Framework':<12} {'Arch Doc':<10}")
        print("-" * 70)
        for s in sorted(services, key=lambda x: x["type"]):
            has_arch = "✓" if s["has_architecture_doc"] else "✗"
            fw = s["framework"] or "-"
            print(f"{s['name']:<30} {s['type']:<15} {fw:<12} {has_arch:<10}")

    print(f"\nBy type:", file=sys.stderr)
    for stype, count in registry["by_type"].items():
        print(f"  {stype}: {count}", file=sys.stderr)


if __name__ == "__main__":
    main()
