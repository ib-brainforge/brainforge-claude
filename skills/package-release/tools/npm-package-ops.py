#!/usr/bin/env python3
"""
NPM package operations for React/TypeScript repositories.

Handles:
- Querying npm registry for versions
- Scanning repos for package usage in package.json
- Updating package.json with new versions
- Verifying npm builds

TODO: Customize for your npm scope and registry.

Usage:
    python npm-package-ops.py get-version --package @your-org/core-react
    python npm-package-ops.py scan-repos --repos-root /path --package @your-org/core-react
    python npm-package-ops.py update-package --repo-path /path --package @your-org/core-react --version 1.3.0
"""

import os
import sys
import json
import argparse
import subprocess
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import quote
import base64


# -----------------------------------------------------------------------------
# Configuration
# TODO: Customize for your organization
# -----------------------------------------------------------------------------

NPM_REGISTRY = "https://registry.npmjs.org"
GITHUB_API = "https://api.github.com"

# Your npm scope
ORG_SCOPE = "@your-org"  # TODO: Set your npm scope

# Directories to skip when scanning
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "coverage"}


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
# NPM Registry Operations
# -----------------------------------------------------------------------------

def get_npm_version(package: str) -> Dict[str, Any]:
    """Get package info from npm registry."""
    encoded = quote(package, safe="")
    url = f"{NPM_REGISTRY}/{encoded}"

    headers = {"Accept": "application/json"}

    # Add auth if NPM_TOKEN is set (for private packages)
    npm_token = os.environ.get("NPM_TOKEN")
    if npm_token:
        headers["Authorization"] = f"Bearer {npm_token}"

    req = Request(url, headers=headers)

    try:
        with urlopen(req) as response:
            data = json.loads(response.read().decode())

            dist_tags = data.get("dist-tags", {})
            versions = list(data.get("versions", {}).keys())

            return {
                "package": package,
                "latest": dist_tags.get("latest"),
                "next": dist_tags.get("next"),
                "all_tags": dist_tags,
                "versions": versions[-10:],  # Last 10
                "total_versions": len(versions),
                "success": True,
            }
    except HTTPError as e:
        return {"package": package, "success": False, "error": f"HTTP {e.code}"}


# -----------------------------------------------------------------------------
# Repository Scanning
# -----------------------------------------------------------------------------

def scan_package_json(pkg_json_path: Path, package: str) -> Optional[Dict[str, Any]]:
    """Scan a package.json for package usage."""
    try:
        with open(pkg_json_path) as f:
            pkg = json.load(f)

        result = None
        for dep_type in ["dependencies", "devDependencies", "peerDependencies"]:
            deps = pkg.get(dep_type, {})
            if package in deps:
                if result is None:
                    result = {
                        "file": str(pkg_json_path),
                        "package_name": pkg.get("name", "unknown"),
                        "usages": []
                    }
                result["usages"].append({
                    "dep_type": dep_type,
                    "version": deps[package],
                })

        return result
    except Exception:
        return None


def scan_repos_for_package(repos_root: Path, package: str) -> List[Dict[str, Any]]:
    """Scan all repos for npm package usage."""
    results = []

    for repo_dir in repos_root.iterdir():
        if not repo_dir.is_dir() or repo_dir.name in SKIP_DIRS:
            continue
        if repo_dir.name.startswith("."):
            continue

        # Check root package.json
        pkg_json = repo_dir / "package.json"
        if pkg_json.exists():
            scan_result = scan_package_json(pkg_json, package)
            if scan_result:
                results.append({
                    "repo": repo_dir.name,
                    "path": str(repo_dir),
                    **scan_result
                })

        # Check workspace packages if monorepo
        packages_dir = repo_dir / "packages"
        if packages_dir.is_dir():
            for workspace in packages_dir.iterdir():
                if workspace.is_dir():
                    ws_pkg = workspace / "package.json"
                    if ws_pkg.exists():
                        scan_result = scan_package_json(ws_pkg, package)
                        if scan_result:
                            results.append({
                                "repo": repo_dir.name,
                                "workspace": workspace.name,
                                "path": str(workspace),
                                **scan_result
                            })

    return results


# -----------------------------------------------------------------------------
# Package Updates
# -----------------------------------------------------------------------------

def parse_version_spec(version_spec: str) -> Tuple[str, str]:
    """Parse version spec into (prefix, version)."""
    match = re.match(r'^([~^]|>=?|<=?)?(.+)$', version_spec)
    if match:
        return match.group(1) or "", match.group(2)
    return "", version_spec


def update_package_json(
    repo_path: Path,
    package: str,
    new_version: str,
    preserve_prefix: bool = True,
    dry_run: bool = True
) -> Dict[str, Any]:
    """Update package version in package.json."""
    pkg_json = repo_path / "package.json"

    if not pkg_json.exists():
        return {"success": False, "error": "package.json not found"}

    with open(pkg_json) as f:
        pkg = json.load(f)

    original_content = json.dumps(pkg, indent=2)
    updates = []

    for dep_type in ["dependencies", "devDependencies", "peerDependencies"]:
        if dep_type in pkg and package in pkg[dep_type]:
            old_spec = pkg[dep_type][package]
            prefix, old_version = parse_version_spec(old_spec)

            if preserve_prefix and prefix:
                new_spec = f"{prefix}{new_version}"
            else:
                new_spec = new_version

            pkg[dep_type][package] = new_spec
            updates.append({
                "dep_type": dep_type,
                "old_version": old_spec,
                "new_version": new_spec,
            })

    if not updates:
        return {"success": False, "error": f"Package {package} not found"}

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "updates": updates,
        }

    # Write updated package.json
    with open(pkg_json, "w") as f:
        json.dump(pkg, f, indent=2)
        f.write("\n")

    return {
        "success": True,
        "dry_run": False,
        "file": "package.json",
        "updates": updates,
    }


# -----------------------------------------------------------------------------
# Build Verification
# -----------------------------------------------------------------------------

def verify_npm_build(repo_path: Path) -> Dict[str, Any]:
    """Verify npm install and build work."""
    steps = []

    # npm install
    result = subprocess.run(
        ["npm", "install"],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    steps.append({
        "step": "npm install",
        "success": result.returncode == 0,
        "error": result.stderr if result.returncode != 0 else None
    })

    if result.returncode != 0:
        return {"success": False, "steps": steps}

    # Check for build script
    pkg_json = repo_path / "package.json"
    if pkg_json.exists():
        pkg = json.loads(pkg_json.read_text())
        scripts = pkg.get("scripts", {})

        # Try build
        if "build" in scripts:
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            steps.append({
                "step": "npm run build",
                "success": result.returncode == 0,
                "error": result.stderr if result.returncode != 0 else None
            })

            if result.returncode != 0:
                return {"success": False, "steps": steps}

        # Try typecheck
        if "typecheck" in scripts or "type-check" in scripts:
            script_name = "typecheck" if "typecheck" in scripts else "type-check"
            result = subprocess.run(
                ["npm", "run", script_name],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            steps.append({
                "step": f"npm run {script_name}",
                "success": result.returncode == 0,
                "error": result.stderr if result.returncode != 0 else None
            })

    return {
        "success": all(s["success"] for s in steps),
        "steps": steps
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
    clean_pkg = package.replace("@", "").replace("/", "-")
    branch_name = f"chore/update-{clean_pkg}-{version}"

    # Create branch
    subprocess.run(["git", "checkout", "-b", branch_name], cwd=repo_path)

    # Stage and commit
    subprocess.run(["git", "add", "package.json", "package-lock.json"], cwd=repo_path)
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
            "--body", f"Automated update of `{package}` to version `{version}`\n\nGenerated by npm-package-manager",
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
    parser = argparse.ArgumentParser(description="NPM package operations")
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
    update_parser.add_argument("--preserve-prefix", action="store_true", default=True)
    update_parser.add_argument("--exact", action="store_true")
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
            # This command needs repo from parent, get from env or error
            print("Error: --run-id required (get from check-workflow first)", file=sys.stderr)
            sys.exit(1)
        result = wait_for_workflow(args.repo, run_id, args.timeout, args.poll_interval)

    elif args.command == "get-version":
        result = get_npm_version(args.package)

    elif args.command == "scan-repos":
        repos = scan_repos_for_package(Path(args.repos_root), args.package)
        result = {
            "package": args.package,
            "repos_found": len(repos),
            "repos": repos,
        }

    elif args.command == "update-package":
        result = update_package_json(
            Path(args.repo_path),
            args.package,
            args.version,
            preserve_prefix=not args.exact,
            dry_run=args.dry_run
        )

    elif args.command == "verify-build":
        result = verify_npm_build(Path(args.repo_path))

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
