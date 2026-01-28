#!/usr/bin/env python3
"""
Git operations utility for multi-repo management.

Handles:
- Discovering changed repositories
- Analyzing changes for commit classification
- Executing commits with generated messages
- Pushing to remotes

TODO: Customize commit conventions for your organization.

Usage:
    python git-operations.py discover-changes --repos-root /path/to/repos
    python git-operations.py analyze-changes --repo-path /path/to/repo
    python git-operations.py commit --repo-path /path/to/repo --message "msg"
"""

import os
import sys
import json
import argparse
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


# -----------------------------------------------------------------------------
# Configuration
# TODO: Customize for your organization
# -----------------------------------------------------------------------------

# Conventional commit types with detection patterns
COMMIT_TYPES = {
    "feat": {
        "description": "New feature",
        "patterns": [
            r"^src/.*\.(ts|tsx|js|jsx|cs|py)$",  # New source files
        ],
        "keywords": ["add", "new", "create", "implement"],
    },
    "fix": {
        "description": "Bug fix",
        "patterns": [],
        "keywords": ["fix", "bug", "issue", "error", "correct", "patch"],
    },
    "refactor": {
        "description": "Code refactoring",
        "patterns": [],
        "keywords": ["refactor", "restructure", "reorganize", "rename"],
    },
    "perf": {
        "description": "Performance improvement",
        "patterns": [],
        "keywords": ["perf", "performance", "optimize", "speed", "cache"],
    },
    "test": {
        "description": "Test changes",
        "patterns": [
            r"^tests?/",
            r"__tests__/",
            r"\.test\.(ts|tsx|js|jsx)$",
            r"\.spec\.(ts|tsx|js|jsx)$",
            r"_test\.go$",
            r"Tests?\.cs$",
        ],
    },
    "docs": {
        "description": "Documentation",
        "patterns": [
            r"^docs/",
            r"\.md$",
            r"^README",
            r"^CHANGELOG",
        ],
    },
    "style": {
        "description": "Code style/formatting",
        "patterns": [
            r"\.(css|scss|sass|less)$",
            r"\.prettierrc",
            r"\.eslintrc",
        ],
        "keywords": ["format", "style", "lint", "whitespace"],
    },
    "chore": {
        "description": "Maintenance tasks",
        "patterns": [
            r"package\.json$",
            r"package-lock\.json$",
            r"yarn\.lock$",
            r"\.csproj$",
            r"requirements\.txt$",
            r"go\.mod$",
            r"Dockerfile",
            r"docker-compose",
        ],
        "keywords": ["update", "upgrade", "bump", "deps", "dependencies"],
    },
    "ci": {
        "description": "CI/CD changes",
        "patterns": [
            r"^\.github/",
            r"^\.gitlab-ci",
            r"^\.circleci/",
            r"^Jenkinsfile",
            r"^azure-pipelines",
        ],
    },
    "build": {
        "description": "Build system changes",
        "patterns": [
            r"webpack",
            r"rollup",
            r"vite\.config",
            r"tsconfig",
            r"\.csproj$",
            r"Makefile",
        ],
    },
}

# Patterns indicating breaking changes
BREAKING_PATTERNS = [
    r"BREAKING",
    r"migration",
    r"schema.*change",
]

# Files that should never be committed
FORBIDDEN_FILES = [
    r"\.env$",
    r"\.env\.local$",
    r"credentials",
    r"secrets?\.json$",
    r"\.pem$",
    r"\.key$",
    r"id_rsa",
]

# Directories to skip when discovering repos
SKIP_DIRS = {"node_modules", ".git", "vendor", "dist", "build", "__pycache__"}


# -----------------------------------------------------------------------------
# Git Helpers
# -----------------------------------------------------------------------------

def run_git(repo_path: Path, *args) -> Tuple[int, str, str]:
    """Run git command and return (returncode, stdout, stderr)."""
    cmd = ["git", "-C", str(repo_path)] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def is_git_repo(path: Path) -> bool:
    """Check if path is a git repository."""
    return (path / ".git").is_dir()


def get_current_branch(repo_path: Path) -> str:
    """Get current branch name."""
    code, out, _ = run_git(repo_path, "rev-parse", "--abbrev-ref", "HEAD")
    return out if code == 0 else "unknown"


def get_remote_url(repo_path: Path) -> Optional[str]:
    """Get remote origin URL."""
    code, out, _ = run_git(repo_path, "remote", "get-url", "origin")
    return out if code == 0 else None


# -----------------------------------------------------------------------------
# Discovery
# -----------------------------------------------------------------------------

def discover_repos(repos_root: Path) -> List[Dict[str, Any]]:
    """Discover all git repositories under repos_root."""
    repos = []

    for item in repos_root.iterdir():
        if not item.is_dir() or item.name in SKIP_DIRS or item.name.startswith("."):
            continue

        if is_git_repo(item):
            repos.append({
                "name": item.name,
                "path": str(item),
                "branch": get_current_branch(item),
                "remote": get_remote_url(item),
            })

    return repos


def discover_changed_repos(repos_root: Path) -> Dict[str, Any]:
    """Discover repos with uncommitted changes."""
    all_repos = discover_repos(repos_root)
    changed = []

    for repo in all_repos:
        repo_path = Path(repo["path"])

        # Check for staged changes
        code, staged, _ = run_git(repo_path, "diff", "--cached", "--name-only")
        staged_files = staged.split("\n") if staged else []

        # Check for unstaged changes
        code, unstaged, _ = run_git(repo_path, "diff", "--name-only")
        unstaged_files = unstaged.split("\n") if unstaged else []

        # Check for untracked files
        code, untracked, _ = run_git(repo_path, "ls-files", "--others", "--exclude-standard")
        untracked_files = untracked.split("\n") if untracked else []

        # Filter empty strings
        staged_files = [f for f in staged_files if f]
        unstaged_files = [f for f in unstaged_files if f]
        untracked_files = [f for f in untracked_files if f]

        if staged_files or unstaged_files or untracked_files:
            changed.append({
                **repo,
                "staged": staged_files,
                "unstaged": unstaged_files,
                "untracked": untracked_files,
                "total_changes": len(staged_files) + len(unstaged_files) + len(untracked_files),
            })

    return {
        "repos_root": str(repos_root),
        "total_repos": len(all_repos),
        "changed_repos": len(changed),
        "repositories": changed,
    }


# -----------------------------------------------------------------------------
# Analysis
# -----------------------------------------------------------------------------

def categorize_file(filepath: str) -> str:
    """Categorize a file path into a change category."""
    for commit_type, config in COMMIT_TYPES.items():
        for pattern in config.get("patterns", []):
            if re.search(pattern, filepath, re.IGNORECASE):
                return commit_type
    return "chore"  # Default


def extract_scope(files: List[str]) -> Optional[str]:
    """Extract scope from changed files (common directory or component)."""
    if not files:
        return None

    # Get first-level directories
    dirs = set()
    for f in files:
        parts = f.split("/")
        if len(parts) > 1:
            dirs.add(parts[0])

    # If all in same directory, use that as scope
    if len(dirs) == 1:
        return dirs.pop()

    # Check for component patterns
    components = set()
    for f in files:
        # Extract component name from common patterns
        match = re.search(r"(?:components?|features?|modules?)/([^/]+)", f)
        if match:
            components.add(match.group(1))

    if len(components) == 1:
        return components.pop()

    return None


def analyze_changes(repo_path: Path) -> Dict[str, Any]:
    """Analyze changes in a repository for commit message generation."""

    # Get diff stats
    code, diff_stat, _ = run_git(repo_path, "diff", "--cached", "--stat")
    code, diff_numstat, _ = run_git(repo_path, "diff", "--cached", "--numstat")

    # Get changed files
    code, staged, _ = run_git(repo_path, "diff", "--cached", "--name-status")

    files_changed = []
    insertions = 0
    deletions = 0

    # Parse numstat for line counts
    if diff_numstat:
        for line in diff_numstat.split("\n"):
            parts = line.split("\t")
            if len(parts) >= 3:
                ins = int(parts[0]) if parts[0] != "-" else 0
                dels = int(parts[1]) if parts[1] != "-" else 0
                insertions += ins
                deletions += dels

    # Parse name-status for file changes
    categories = {}
    if staged:
        for line in staged.split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                status, filepath = parts[0], parts[-1]
                category = categorize_file(filepath)

                files_changed.append({
                    "path": filepath,
                    "status": status,  # A=added, M=modified, D=deleted, R=renamed
                    "category": category,
                })

                categories[category] = categories.get(category, 0) + 1

    # Determine primary commit type
    if categories:
        primary_type = max(categories, key=categories.get)
    else:
        primary_type = "chore"

    # Check for breaking changes
    code, diff_content, _ = run_git(repo_path, "diff", "--cached")
    is_breaking = any(
        re.search(pattern, diff_content, re.IGNORECASE)
        for pattern in BREAKING_PATTERNS
    )

    # Check for forbidden files
    forbidden = [
        f["path"] for f in files_changed
        if any(re.search(p, f["path"], re.IGNORECASE) for p in FORBIDDEN_FILES)
    ]

    # Extract scope
    scope = extract_scope([f["path"] for f in files_changed])

    return {
        "repo_path": str(repo_path),
        "repo_name": repo_path.name,
        "branch": get_current_branch(repo_path),
        "changes": {
            "files": files_changed,
            "files_count": len(files_changed),
            "insertions": insertions,
            "deletions": deletions,
            "categories": categories,
        },
        "classification": {
            "primary_type": primary_type,
            "scope": scope,
            "is_breaking": is_breaking,
            "type_description": COMMIT_TYPES.get(primary_type, {}).get("description", ""),
        },
        "warnings": {
            "forbidden_files": forbidden,
            "has_forbidden": len(forbidden) > 0,
        },
    }


def generate_commit_message(
    analysis: Dict[str, Any],
    ticket_id: Optional[str] = None,
    custom_subject: Optional[str] = None
) -> str:
    """Generate a conventional commit message from analysis."""

    commit_type = analysis["classification"]["primary_type"]
    scope = analysis["classification"]["scope"]
    is_breaking = analysis["classification"]["is_breaking"]

    # Build type with scope
    type_str = commit_type
    if scope:
        type_str = f"{commit_type}({scope})"
    if is_breaking:
        type_str = f"{type_str}!"

    # Generate subject if not provided
    if custom_subject:
        subject = custom_subject
    else:
        # Auto-generate based on changes
        files = analysis["changes"]["files"]
        if len(files) == 1:
            action = "add" if files[0]["status"] == "A" else "update"
            subject = f"{action} {files[0]['path'].split('/')[-1]}"
        else:
            subject = f"{commit_type} changes to {len(files)} files"

    # Build message
    lines = [f"{type_str}: {subject}"]

    # Body
    if analysis["changes"]["files_count"] > 1:
        lines.append("")
        lines.append("Changes:")
        for f in analysis["changes"]["files"][:10]:  # Limit to 10
            status_map = {"A": "Add", "M": "Update", "D": "Remove", "R": "Rename"}
            action = status_map.get(f["status"], "Change")
            lines.append(f"- {action} {f['path']}")
        if len(analysis["changes"]["files"]) > 10:
            lines.append(f"- ... and {len(analysis['changes']['files']) - 10} more files")

    # Footer
    if is_breaking:
        lines.append("")
        lines.append("BREAKING CHANGE: This commit includes breaking changes.")

    if ticket_id:
        lines.append("")
        lines.append(f"Refs: {ticket_id}")

    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Operations
# -----------------------------------------------------------------------------

def commit_changes(
    repo_path: Path,
    message: str,
    stage_all: bool = False,
    files: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Commit changes to repository."""

    # Stage files
    if stage_all:
        code, _, err = run_git(repo_path, "add", "-A")
        if code != 0:
            return {"success": False, "error": f"Failed to stage: {err}"}
    elif files:
        for f in files:
            run_git(repo_path, "add", f)

    # Commit
    code, out, err = run_git(repo_path, "commit", "-m", message)
    if code != 0:
        return {"success": False, "error": err}

    # Get commit SHA
    code, sha, _ = run_git(repo_path, "rev-parse", "HEAD")

    return {
        "success": True,
        "commit_sha": sha,
        "message": message,
    }


def push_changes(
    repo_path: Path,
    branch: Optional[str] = None,
    set_upstream: bool = True
) -> Dict[str, Any]:
    """Push changes to remote."""

    if not branch:
        branch = get_current_branch(repo_path)

    args = ["push"]
    if set_upstream:
        args.extend(["-u", "origin", branch])
    else:
        args.extend(["origin", branch])

    code, out, err = run_git(repo_path, *args)

    if code != 0:
        return {"success": False, "error": err}

    return {"success": True, "branch": branch, "output": out}


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Git operations for multi-repo")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # discover-changes
    discover_parser = subparsers.add_parser("discover-changes")
    discover_parser.add_argument("--repos-root", "-r", required=True)
    discover_parser.add_argument("--output", "-o")

    # analyze-changes
    analyze_parser = subparsers.add_parser("analyze-changes")
    analyze_parser.add_argument("--repo-path", "-r", required=True)
    analyze_parser.add_argument("--output", "-o")

    # generate-message
    message_parser = subparsers.add_parser("generate-message")
    message_parser.add_argument("--repo-path", "-r", required=True)
    message_parser.add_argument("--ticket", "-t")
    message_parser.add_argument("--subject", "-s")
    message_parser.add_argument("--output", "-o")

    # commit
    commit_parser = subparsers.add_parser("commit")
    commit_parser.add_argument("--repo-path", "-r", required=True)
    commit_parser.add_argument("--message", "-m", required=True)
    commit_parser.add_argument("--stage-all", action="store_true")
    commit_parser.add_argument("--files", nargs="+")
    commit_parser.add_argument("--output", "-o")

    # push
    push_parser = subparsers.add_parser("push")
    push_parser.add_argument("--repo-path", "-r", required=True)
    push_parser.add_argument("--branch", "-b")
    push_parser.add_argument("--output", "-o")

    args = parser.parse_args()
    result = None

    if args.command == "discover-changes":
        result = discover_changed_repos(Path(args.repos_root))

    elif args.command == "analyze-changes":
        result = analyze_changes(Path(args.repo_path))

    elif args.command == "generate-message":
        analysis = analyze_changes(Path(args.repo_path))
        message = generate_commit_message(analysis, args.ticket, args.subject)
        result = {"message": message, "analysis": analysis}

    elif args.command == "commit":
        result = commit_changes(
            Path(args.repo_path),
            args.message,
            args.stage_all,
            args.files
        )

    elif args.command == "push":
        result = push_changes(Path(args.repo_path), args.branch)

    # Output
    output = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
