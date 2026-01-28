#!/usr/bin/env python3
"""
NuGet package operations for C#/.NET repositories.

Handles:
- Querying NuGet registry for versions
- Scanning repos for package usage in .csproj files
- Updating PackageReference versions
- Verifying dotnet builds

TODO: Customize for your NuGet prefix and feeds.

Usage:
    python nuget-package-ops.py get-version --package YourOrg.Core
    python nuget-package-ops.py scan-repos --repos-root /path --package YourOrg.Core
    python nuget-package-ops.py update-package --repo-path /path --package YourOrg.Core --version 1.3.0
"""

import os
import sys
import json
import argparse
import subprocess
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from urllib.request import Request, urlopen
from urllib.error import HTTPError


# -----------------------------------------------------------------------------
# Configuration
# TODO: Customize for your organization
# -----------------------------------------------------------------------------

NUGET_V3_INDEX = "https://api.nuget.org/v3/index.json"
GITHUB_API = "https://api.github.com"

# Your NuGet package prefix
ORG_PREFIX = "YourOrg"  # TODO: Set your NuGet prefix

# Directories to skip when scanning
SKIP_DIRS = {"bin", "obj", ".git", "node_modules", "packages"}


# -----------------------------------------------------------------------------
# GitHub API Helpers
# -----------------------------------------------------------------------------

def github_request(endpoint: str, method: str = "GET") -> Dict:
    """Make authenticated GitHub API request."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError("GITHUB_TOKEN required")

    url = f"{GITHUB_API}{endpoint}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    req = Request(url, headers=headers, method=method)
    with urlopen(req) as response:
        return json.loads(response.read().decode())


def get_workflow_runs(repo: str, workflow: str, limit: int = 5) -> List[Dict]:
    """Get recent workflow runs."""
    endpoint = f"/repos/{repo}/actions/workflows/{workflow}/runs?per_page={limit}"
    result = github_request(endpoint)
    return result.get("workflow_runs", [])


def get_workflow_run(repo: str, run_id: int) -> Dict:
    """Get specific workflow run."""
    return github_request(f"/repos/{repo}/actions/runs/{run_id}")


def wait_for_workflow(
    repo: str,
    run_id: int,
    timeout: int = 600,
    poll_interval: int = 30
) -> Dict[str, Any]:
    """Wait for workflow completion."""
    start = time.time()

    while time.time() - start < timeout:
        run = get_workflow_run(repo, run_id)
        status = run.get("status")
        conclusion = run.get("conclusion")

        if status == "completed":
            return {
                "completed": True,
                "conclusion": conclusion,
                "success": conclusion == "success",
                "run_url": run.get("html_url"),
                "duration": time.time() - start,
            }

        print(f"Workflow status: {status}, waiting {poll_interval}s...", file=sys.stderr)
        time.sleep(poll_interval)

    return {"completed": False, "error": "Timeout", "duration": timeout}


# -----------------------------------------------------------------------------
# NuGet Registry Operations
# -----------------------------------------------------------------------------

def get_nuget_service_url(service_type: str) -> Optional[str]:
    """Get NuGet service URL from v3 index."""
    with urlopen(NUGET_V3_INDEX) as response:
        index = json.loads(response.read().decode())

    for resource in index.get("resources", []):
        if service_type in resource.get("@type", ""):
            return resource.get("@id")

    return None


def get_nuget_version(package: str) -> Dict[str, Any]:
    """Get package info from NuGet registry."""
    try:
        # Get registration base URL
        reg_base = get_nuget_service_url("RegistrationsBaseUrl")
        if not reg_base:
            return {"package": package, "success": False, "error": "No registration URL"}

        # Get package registration (lowercase required)
        pkg_url = f"{reg_base.rstrip('/')}/{package.lower()}/index.json"

        with urlopen(pkg_url) as response:
            data = json.loads(response.read().decode())

        # Extract versions from pages
        versions = []
        for page in data.get("items", []):
            # Page might be inline or need fetching
            items = page.get("items", [])
            if not items and "@id" in page:
                # Need to fetch page
                with urlopen(page["@id"]) as page_response:
                    page_data = json.loads(page_response.read().decode())
                    items = page_data.get("items", [])

            for item in items:
                catalog_entry = item.get("catalogEntry", {})
                ver = catalog_entry.get("version")
                listed = catalog_entry.get("listed", True)
                if ver and listed:
                    versions.append(ver)

        # Separate stable and prerelease
        stable = [v for v in versions if "-" not in v]
        prerelease = [v for v in versions if "-" in v]

        latest_stable = stable[-1] if stable else None
        latest_prerelease = prerelease[-1] if prerelease else None

        return {
            "package": package,
            "latest": latest_stable,
            "latest_prerelease": latest_prerelease,
            "stable_versions": stable[-10:],
            "prerelease_versions": prerelease[-5:],
            "total_versions": len(versions),
            "success": True,
        }

    except HTTPError as e:
        return {"package": package, "success": False, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"package": package, "success": False, "error": str(e)}


# -----------------------------------------------------------------------------
# Repository Scanning
# -----------------------------------------------------------------------------

def scan_csproj(csproj_path: Path, package: str) -> Optional[Dict[str, Any]]:
    """Scan a .csproj file for package reference."""
    try:
        tree = ET.parse(csproj_path)
        root = tree.getroot()

        # Handle both with and without namespace
        namespaces = {"": ""}  # Default no namespace

        references = []

        # Find PackageReference elements
        for pkg_ref in root.iter():
            if pkg_ref.tag.endswith("PackageReference"):
                include = pkg_ref.get("Include", "")
                if include.lower() == package.lower():
                    version = pkg_ref.get("Version")
                    # Version might be in child element
                    if not version:
                        ver_elem = pkg_ref.find("Version")
                        if ver_elem is not None:
                            version = ver_elem.text

                    references.append({
                        "version": version,
                        "include": include,
                    })

        if references:
            return {
                "file": str(csproj_path),
                "references": references,
            }

        return None

    except Exception as e:
        return None


def scan_directory_packages_props(repo_path: Path, package: str) -> Optional[Dict[str, Any]]:
    """Scan Directory.Packages.props for centralized package management."""
    props_file = repo_path / "Directory.Packages.props"
    if not props_file.exists():
        return None

    try:
        tree = ET.parse(props_file)
        root = tree.getroot()

        for pkg_ver in root.iter():
            if pkg_ver.tag.endswith("PackageVersion"):
                include = pkg_ver.get("Include", "")
                if include.lower() == package.lower():
                    return {
                        "file": str(props_file),
                        "type": "central_package_management",
                        "version": pkg_ver.get("Version"),
                    }

        return None
    except Exception:
        return None


def scan_repos_for_package(repos_root: Path, package: str) -> List[Dict[str, Any]]:
    """Scan all repos for NuGet package usage."""
    results = []

    for repo_dir in repos_root.iterdir():
        if not repo_dir.is_dir() or repo_dir.name in SKIP_DIRS:
            continue
        if repo_dir.name.startswith("."):
            continue

        repo_result = {
            "repo": repo_dir.name,
            "path": str(repo_dir),
            "projects": [],
            "central_management": None,
        }

        # Check for central package management
        central = scan_directory_packages_props(repo_dir, package)
        if central:
            repo_result["central_management"] = central

        # Scan all .csproj files
        for csproj in repo_dir.rglob("*.csproj"):
            # Skip bin/obj directories
            if any(part in SKIP_DIRS for part in csproj.parts):
                continue

            scan_result = scan_csproj(csproj, package)
            if scan_result:
                scan_result["relative_path"] = str(csproj.relative_to(repo_dir))
                repo_result["projects"].append(scan_result)

        # Only include if package found
        if repo_result["projects"] or repo_result["central_management"]:
            results.append(repo_result)

    return results


# -----------------------------------------------------------------------------
# Package Updates
# -----------------------------------------------------------------------------

def update_csproj(
    csproj_path: Path,
    package: str,
    new_version: str,
    dry_run: bool = True
) -> Dict[str, Any]:
    """Update PackageReference version in .csproj file."""
    try:
        content = csproj_path.read_text()
        original = content

        # Pattern for PackageReference with Version attribute
        pattern = rf'(<PackageReference\s+Include="{re.escape(package)}"[^>]*Version=")[^"]+(")'
        replacement = rf'\g<1>{new_version}\g<2>'

        new_content, count = re.subn(pattern, replacement, content, flags=re.IGNORECASE)

        if count == 0:
            # Try pattern with Version as child element
            pattern2 = rf'(<PackageReference\s+Include="{re.escape(package)}"[^>]*>[\s\S]*?<Version>)[^<]+(</Version>)'
            new_content, count = re.subn(pattern2, rf'\g<1>{new_version}\g<2>', content, flags=re.IGNORECASE)

        if count == 0:
            return {"success": False, "error": "Package reference not found"}

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "file": str(csproj_path),
                "replacements": count,
            }

        csproj_path.write_text(new_content)

        return {
            "success": True,
            "dry_run": False,
            "file": str(csproj_path),
            "replacements": count,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def update_directory_packages_props(
    repo_path: Path,
    package: str,
    new_version: str,
    dry_run: bool = True
) -> Dict[str, Any]:
    """Update version in Directory.Packages.props."""
    props_file = repo_path / "Directory.Packages.props"

    if not props_file.exists():
        return {"success": False, "error": "Directory.Packages.props not found"}

    try:
        content = props_file.read_text()

        pattern = rf'(<PackageVersion\s+Include="{re.escape(package)}"[^>]*Version=")[^"]+(")'
        new_content, count = re.subn(pattern, rf'\g<1>{new_version}\g<2>', content, flags=re.IGNORECASE)

        if count == 0:
            return {"success": False, "error": "Package not found in props file"}

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "file": str(props_file),
                "type": "central_package_management",
            }

        props_file.write_text(new_content)

        return {
            "success": True,
            "dry_run": False,
            "file": str(props_file),
            "type": "central_package_management",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def update_package_in_repo(
    repo_path: Path,
    package: str,
    new_version: str,
    dry_run: bool = True
) -> Dict[str, Any]:
    """Update package version across entire repo."""
    repo_path = Path(repo_path)
    updates = []
    errors = []

    # Check for central package management first
    props_file = repo_path / "Directory.Packages.props"
    if props_file.exists():
        result = update_directory_packages_props(repo_path, package, new_version, dry_run)
        if result["success"]:
            updates.append(result)
        elif "not found" not in result.get("error", "").lower():
            errors.append(result)

    # Update individual .csproj files
    for csproj in repo_path.rglob("*.csproj"):
        if any(part in SKIP_DIRS for part in csproj.parts):
            continue

        result = update_csproj(csproj, package, new_version, dry_run)
        if result["success"]:
            result["relative_path"] = str(csproj.relative_to(repo_path))
            updates.append(result)
        elif "not found" not in result.get("error", "").lower():
            errors.append(result)

    if not updates and not errors:
        return {"success": False, "error": f"Package {package} not found in any project"}

    return {
        "success": len(errors) == 0 and len(updates) > 0,
        "dry_run": dry_run,
        "updates": updates,
        "errors": errors,
        "projects_updated": len(updates),
    }


# -----------------------------------------------------------------------------
# Build Verification
# -----------------------------------------------------------------------------

def verify_dotnet_build(repo_path: Path) -> Dict[str, Any]:
    """Verify dotnet restore and build work."""
    steps = []

    # Find solution file or use repo root
    sln_files = list(repo_path.glob("*.sln"))
    build_path = str(sln_files[0]) if sln_files else str(repo_path)

    # dotnet restore
    result = subprocess.run(
        ["dotnet", "restore", build_path],
        capture_output=True,
        text=True
    )

    # Check for warnings in restore
    restore_warnings = []
    if "warning" in result.stdout.lower() or "warning" in result.stderr.lower():
        for line in (result.stdout + result.stderr).split("\n"):
            if "warning" in line.lower():
                restore_warnings.append(line.strip())

    steps.append({
        "step": "dotnet restore",
        "success": result.returncode == 0,
        "warnings": restore_warnings[:5],  # Limit warnings
        "error": result.stderr if result.returncode != 0 else None
    })

    if result.returncode != 0:
        return {"success": False, "steps": steps}

    # dotnet build
    result = subprocess.run(
        ["dotnet", "build", build_path, "--no-restore"],
        capture_output=True,
        text=True
    )

    steps.append({
        "step": "dotnet build",
        "success": result.returncode == 0,
        "error": result.stderr if result.returncode != 0 else None
    })

    if result.returncode != 0:
        return {"success": False, "steps": steps}

    # dotnet test (if test projects exist)
    test_projects = list(repo_path.rglob("*Tests*.csproj")) + list(repo_path.rglob("*Test*.csproj"))
    if test_projects:
        result = subprocess.run(
            ["dotnet", "test", build_path, "--no-build"],
            capture_output=True,
            text=True
        )
        steps.append({
            "step": "dotnet test",
            "success": result.returncode == 0,
            "error": result.stderr if result.returncode != 0 else None
        })

    return {
        "success": all(s["success"] for s in steps),
        "steps": steps,
        "restore_warnings": restore_warnings,
    }


# -----------------------------------------------------------------------------
# PR Creation
# -----------------------------------------------------------------------------

def create_update_pr(
    repo_path: Path,
    package: str,
    version: str,
    base_branch: str = "main"
) -> Dict[str, Any]:
    """Create PR for package update using gh CLI."""

    # Clean package name for branch
    clean_pkg = package.replace(".", "-").lower()
    branch_name = f"chore/update-{clean_pkg}-{version}"

    # Create branch
    subprocess.run(["git", "checkout", "-b", branch_name], cwd=repo_path)

    # Stage .csproj and props files
    subprocess.run(["git", "add", "*.csproj"], cwd=repo_path)
    subprocess.run(["git", "add", "Directory.Packages.props"], cwd=repo_path)

    # Commit
    subprocess.run(
        ["git", "commit", "-m", f"chore(deps): update {package} to {version}"],
        cwd=repo_path
    )

    # Push
    subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=repo_path)

    # Create PR
    result = subprocess.run(
        [
            "gh", "pr", "create",
            "--title", f"chore(deps): update {package} to {version}",
            "--body", f"Automated update of `{package}` to version `{version}`\n\nGenerated by nuget-package-manager",
            "--base", base_branch,
        ],
        cwd=repo_path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {"success": False, "error": result.stderr}

    return {
        "success": True,
        "branch": branch_name,
        "pr_url": result.stdout.strip(),
    }


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="NuGet package operations")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # check-workflow
    wf_parser = subparsers.add_parser("check-workflow")
    wf_parser.add_argument("--repo", "-r", required=True, help="owner/repo")
    wf_parser.add_argument("--workflow", "-w", required=True)
    wf_parser.add_argument("--output", "-o")

    # wait-workflow
    wait_parser = subparsers.add_parser("wait-workflow")
    wait_parser.add_argument("--repo", "-r", required=True)
    wait_parser.add_argument("--run-id", type=int)
    wait_parser.add_argument("--timeout", type=int, default=600)
    wait_parser.add_argument("--poll-interval", type=int, default=30)
    wait_parser.add_argument("--output", "-o")

    # get-version
    ver_parser = subparsers.add_parser("get-version")
    ver_parser.add_argument("--package", "-p", required=True)
    ver_parser.add_argument("--output", "-o")

    # scan-repos
    scan_parser = subparsers.add_parser("scan-repos")
    scan_parser.add_argument("--repos-root", "-r", required=True)
    scan_parser.add_argument("--package", "-p", required=True)
    scan_parser.add_argument("--output", "-o")

    # update-package
    update_parser = subparsers.add_parser("update-package")
    update_parser.add_argument("--repo-path", "-r", required=True)
    update_parser.add_argument("--package", "-p", required=True)
    update_parser.add_argument("--version", "-v", required=True)
    update_parser.add_argument("--dry-run", action="store_true")
    update_parser.add_argument("--output", "-o")

    # verify-build
    build_parser = subparsers.add_parser("verify-build")
    build_parser.add_argument("--repo-path", "-r", required=True)
    build_parser.add_argument("--output", "-o")

    # create-pr
    pr_parser = subparsers.add_parser("create-pr")
    pr_parser.add_argument("--repo-path", "-r", required=True)
    pr_parser.add_argument("--package", "-p", required=True)
    pr_parser.add_argument("--version", "-v", required=True)
    pr_parser.add_argument("--base", default="develop")  # GitFlow: PRs target develop, not main
    pr_parser.add_argument("--output", "-o")

    args = parser.parse_args()
    result = None

    if args.command == "check-workflow":
        runs = get_workflow_runs(args.repo, args.workflow)
        result = {
            "repo": args.repo,
            "workflow": args.workflow,
            "latest_run": runs[0] if runs else None,
            "runs": [
                {
                    "id": r["id"],
                    "status": r["status"],
                    "conclusion": r["conclusion"],
                    "created_at": r["created_at"],
                    "url": r["html_url"],
                }
                for r in runs
            ],
        }

    elif args.command == "wait-workflow":
        run_id = args.run_id
        if not run_id:
            print("Error: --run-id required", file=sys.stderr)
            sys.exit(1)
        result = wait_for_workflow(args.repo, run_id, args.timeout, args.poll_interval)

    elif args.command == "get-version":
        result = get_nuget_version(args.package)

    elif args.command == "scan-repos":
        repos = scan_repos_for_package(Path(args.repos_root), args.package)
        result = {
            "package": args.package,
            "repos_found": len(repos),
            "total_projects": sum(len(r["projects"]) for r in repos),
            "repos": repos,
        }

    elif args.command == "update-package":
        result = update_package_in_repo(
            Path(args.repo_path),
            args.package,
            args.version,
            args.dry_run
        )

    elif args.command == "verify-build":
        result = verify_dotnet_build(Path(args.repo_path))

    elif args.command == "create-pr":
        result = create_update_pr(
            Path(args.repo_path),
            args.package,
            args.version,
            args.base
        )

    # Output
    output = json.dumps(result, indent=2)
    if hasattr(args, 'output') and args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
