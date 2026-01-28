#!/usr/bin/env python3
"""
Extract documentation from repositories for sync.

Scans repositories for documentation files matching configured patterns
and creates a manifest for synchronization.

TODO: Customize patterns and metadata extraction for your doc structure.

Usage:
    python extract-docs.py --repos-root /path/to/repos --output manifest.json
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import fnmatch
import re


# -----------------------------------------------------------------------------
# Configuration
# TODO: Customize these patterns for your repository structure
# -----------------------------------------------------------------------------

DOC_PATTERNS = {
    "adr": {
        "pattern": "**/docs/adr/*.md",
        "confluence_parent": "Architecture Decision Records",
        "title_extractor": "adr_title",  # Function name for title extraction
        "metadata_extractor": "adr_metadata"
    },
    "architecture": {
        "pattern": "**/ARCHITECTURE.md",
        "confluence_parent": "Service Architecture",
        "title_extractor": "service_title",
        "metadata_extractor": "frontmatter_metadata"
    },
    "runbook": {
        "pattern": "**/docs/runbooks/*.md",
        "confluence_parent": "Runbooks",
        "title_extractor": "h1_title",
        "metadata_extractor": "frontmatter_metadata"
    },
    "api": {
        "pattern": "**/docs/api/*.md",
        "confluence_parent": "API Documentation",
        "title_extractor": "h1_title",
        "metadata_extractor": "frontmatter_metadata"
    }
}

# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", "vendor", "dist", "build",
    "__pycache__", ".venv", "venv", ".terraform"
}


# -----------------------------------------------------------------------------
# Title Extractors
# TODO: Add more extractors or customize existing ones
# -----------------------------------------------------------------------------

def adr_title(filepath: Path, content: str) -> str:
    """
    Extract title from ADR file.
    Expects format: NNNN-title-with-dashes.md or # ADR-NNNN: Title
    """
    # Try H1 first
    match = re.search(r"^#\s+(?:ADR[-\s]*\d+[:\s]+)?(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()

    # Fall back to filename
    name = filepath.stem  # NNNN-title-with-dashes
    parts = name.split("-", 1)
    if len(parts) > 1:
        return f"ADR-{parts[0]}: {parts[1].replace('-', ' ').title()}"
    return name


def service_title(filepath: Path, content: str) -> str:
    """
    Extract title from service ARCHITECTURE.md.
    Uses parent directory name as service name.
    """
    service_name = filepath.parent.name
    # Try H1 for custom title
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return f"{service_name.replace('-', ' ').title()} Architecture"


def h1_title(filepath: Path, content: str) -> str:
    """Extract first H1 heading or use filename."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return filepath.stem.replace("-", " ").title()


# -----------------------------------------------------------------------------
# Metadata Extractors
# TODO: Customize for your frontmatter format
# -----------------------------------------------------------------------------

def adr_metadata(filepath: Path, content: str) -> Dict[str, Any]:
    """
    Extract ADR-specific metadata.
    Looks for status, date, deciders, etc.
    """
    metadata = {"type": "adr"}

    # Status (common ADR formats)
    status_match = re.search(
        r"(?:^|\n)\*?\*?Status\*?\*?:?\s*(.+?)(?:\n|$)",
        content, re.IGNORECASE
    )
    if status_match:
        metadata["status"] = status_match.group(1).strip()

    # Date
    date_match = re.search(
        r"(?:^|\n)\*?\*?Date\*?\*?:?\s*(\d{4}-\d{2}-\d{2})",
        content, re.IGNORECASE
    )
    if date_match:
        metadata["date"] = date_match.group(1)

    # Deciders
    deciders_match = re.search(
        r"(?:^|\n)\*?\*?Deciders?\*?\*?:?\s*(.+?)(?:\n|$)",
        content, re.IGNORECASE
    )
    if deciders_match:
        metadata["deciders"] = deciders_match.group(1).strip()

    return metadata


def frontmatter_metadata(filepath: Path, content: str) -> Dict[str, Any]:
    """
    Extract YAML frontmatter metadata.
    Expects --- delimited block at start of file.
    """
    metadata = {}

    frontmatter_match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
    if frontmatter_match:
        # Simple YAML parsing (for complex YAML, use pyyaml)
        for line in frontmatter_match.group(1).split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip().strip('"\'')

    return metadata


# -----------------------------------------------------------------------------
# Core Logic
# -----------------------------------------------------------------------------

def find_docs(repos_root: Path) -> List[Dict[str, Any]]:
    """
    Find all documentation files matching configured patterns.

    Returns list of doc entries with:
    - path: relative path from repos_root
    - absolute_path: full filesystem path
    - doc_type: which pattern matched
    - title: extracted title
    - metadata: extracted metadata
    - content_hash: MD5 for change detection
    """
    docs = []

    for doc_type, config in DOC_PATTERNS.items():
        pattern = config["pattern"]

        # Walk all repos
        for root, dirs, files in os.walk(repos_root):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for filename in files:
                filepath = Path(root) / filename
                rel_path = filepath.relative_to(repos_root)

                # Check if matches pattern
                if fnmatch.fnmatch(str(rel_path), pattern):
                    content = filepath.read_text(encoding="utf-8", errors="replace")

                    # Get extractors
                    title_fn = globals().get(config["title_extractor"], h1_title)
                    meta_fn = globals().get(config["metadata_extractor"], lambda p, c: {})

                    docs.append({
                        "path": str(rel_path),
                        "absolute_path": str(filepath),
                        "doc_type": doc_type,
                        "confluence_parent": config["confluence_parent"],
                        "title": title_fn(filepath, content),
                        "metadata": meta_fn(filepath, content),
                        "content_hash": hashlib.md5(content.encode()).hexdigest(),
                        "last_modified": datetime.fromtimestamp(
                            filepath.stat().st_mtime
                        ).isoformat()
                    })

    return docs


def main():
    parser = argparse.ArgumentParser(
        description="Extract documentation from repositories"
    )
    parser.add_argument(
        "--repos-root", "-r",
        required=True,
        help="Root directory containing repositories"
    )
    parser.add_argument(
        "--output", "-o",
        default="docs-manifest.json",
        help="Output manifest file (default: docs-manifest.json)"
    )
    parser.add_argument(
        "--doc-types",
        nargs="+",
        choices=list(DOC_PATTERNS.keys()),
        help="Only extract specific doc types"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print found docs"
    )

    args = parser.parse_args()
    repos_root = Path(args.repos_root).resolve()

    if not repos_root.is_dir():
        print(f"Error: {repos_root} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Filter patterns if specific types requested
    if args.doc_types:
        global DOC_PATTERNS
        DOC_PATTERNS = {k: v for k, v in DOC_PATTERNS.items() if k in args.doc_types}

    print(f"Scanning {repos_root} for documentation...", file=sys.stderr)
    docs = find_docs(repos_root)

    # Build manifest
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "repos_root": str(repos_root),
        "doc_count": len(docs),
        "by_type": {},
        "documents": docs
    }

    # Count by type
    for doc in docs:
        doc_type = doc["doc_type"]
        manifest["by_type"][doc_type] = manifest["by_type"].get(doc_type, 0) + 1

    # Output
    with open(args.output, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Found {len(docs)} documents", file=sys.stderr)
    for doc_type, count in manifest["by_type"].items():
        print(f"  {doc_type}: {count}", file=sys.stderr)
    print(f"Manifest written to {args.output}", file=sys.stderr)

    if args.verbose:
        for doc in docs:
            print(f"  [{doc['doc_type']}] {doc['title']} - {doc['path']}")


if __name__ == "__main__":
    main()
