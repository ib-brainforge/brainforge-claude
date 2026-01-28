#!/usr/bin/env python3
"""
Synchronize documentation between repositories and Confluence.

Orchestrates the sync process using extract-docs.py output and Confluence API.

TODO:
- Implement markdown-to-confluence conversion for your content
- Add conflict resolution strategy
- Add support for attachments/images

Usage:
    # Preview changes
    python sync-docs.py --manifest docs-manifest.json --space ARCH --dry-run

    # Apply changes
    python sync-docs.py --manifest docs-manifest.json --space ARCH --apply
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import sibling module
sys.path.insert(0, str(Path(__file__).parent))
from confluence_api import ConfluenceAPI


# -----------------------------------------------------------------------------
# Sync State Tracking
# TODO: Customize storage location and format
# -----------------------------------------------------------------------------

SYNC_STATE_FILE = ".docs-sync-state.json"


def load_sync_state(state_file: Path) -> Dict[str, Any]:
    """Load previous sync state for change detection."""
    if state_file.exists():
        with open(state_file) as f:
            return json.load(f)
    return {"synced_docs": {}, "last_sync": None}


def save_sync_state(state_file: Path, state: Dict[str, Any]) -> None:
    """Save sync state after successful sync."""
    state["last_sync"] = datetime.now().isoformat()
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


# -----------------------------------------------------------------------------
# Sync Logic
# -----------------------------------------------------------------------------

def compute_changes(
    manifest: Dict[str, Any],
    sync_state: Dict[str, Any],
    api: ConfluenceAPI,
    space_key: str
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Compare manifest against sync state and Confluence to determine changes.

    Returns:
        {
            "create": [docs to create in Confluence],
            "update": [docs to update in Confluence],
            "unchanged": [docs with no changes],
            "conflicts": [docs changed both locally and in Confluence]
        }
    """
    changes = {
        "create": [],
        "update": [],
        "unchanged": [],
        "conflicts": []
    }

    synced = sync_state.get("synced_docs", {})

    for doc in manifest["documents"]:
        doc_path = doc["path"]
        doc_hash = doc["content_hash"]
        doc_title = doc["title"]

        # Check if we've synced this before
        prev_sync = synced.get(doc_path)

        if prev_sync is None:
            # Never synced - check if page exists in Confluence
            existing = api.get_page_by_title(doc_title, space_key)
            if existing:
                # Page exists but we didn't create it - potential conflict
                changes["conflicts"].append({
                    **doc,
                    "reason": "Page exists in Confluence but not in sync state",
                    "confluence_id": existing["id"]
                })
            else:
                # New doc to create
                changes["create"].append(doc)

        elif prev_sync["content_hash"] == doc_hash:
            # No local changes
            changes["unchanged"].append(doc)

        else:
            # Local changes - check Confluence for conflicts
            confluence_id = prev_sync.get("confluence_id")
            if confluence_id:
                try:
                    current_page = api.get_page_by_id(confluence_id)
                    confluence_version = current_page["version"]["number"]

                    if confluence_version > prev_sync.get("confluence_version", 0):
                        # Confluence was also modified - conflict
                        changes["conflicts"].append({
                            **doc,
                            "reason": "Both local and Confluence modified since last sync",
                            "confluence_id": confluence_id,
                            "local_hash": doc_hash,
                            "synced_hash": prev_sync["content_hash"]
                        })
                    else:
                        # Only local changes - safe to update
                        changes["update"].append({
                            **doc,
                            "confluence_id": confluence_id,
                            "confluence_version": confluence_version
                        })
                except Exception as e:
                    # Page might have been deleted
                    changes["create"].append({
                        **doc,
                        "note": f"Previous page not found: {e}"
                    })
            else:
                # No Confluence ID recorded - treat as create
                changes["create"].append(doc)

    return changes


def execute_sync(
    changes: Dict[str, List[Dict[str, Any]]],
    api: ConfluenceAPI,
    space_key: str,
    parent_pages: Dict[str, str],  # doc_type -> parent page ID
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Execute sync operations.

    Args:
        changes: Output from compute_changes
        api: Confluence API client
        space_key: Target Confluence space
        parent_pages: Mapping of doc types to parent page IDs
        dry_run: If True, don't actually make changes

    Returns:
        Sync report with results
    """
    report = {
        "created": [],
        "updated": [],
        "skipped": [],
        "conflicts": changes["conflicts"],
        "errors": []
    }

    # Process creates
    for doc in changes["create"]:
        if dry_run:
            report["created"].append({
                "title": doc["title"],
                "path": doc["path"],
                "action": "would_create"
            })
            continue

        try:
            # Read content
            content = Path(doc["absolute_path"]).read_text()

            # Convert to Confluence format
            # TODO: Implement proper markdown conversion
            html_content = api.convert_markdown_to_storage(content)

            # Get parent page ID
            parent_id = parent_pages.get(doc["doc_type"])

            # Create page
            result = api.create_page(
                space_key,
                doc["title"],
                html_content,
                parent_id
            )

            report["created"].append({
                "title": doc["title"],
                "path": doc["path"],
                "confluence_id": result["id"],
                "confluence_url": f"{api.base_url}{result['_links']['webui']}"
            })

        except Exception as e:
            report["errors"].append({
                "title": doc["title"],
                "path": doc["path"],
                "error": str(e)
            })

    # Process updates
    for doc in changes["update"]:
        if dry_run:
            report["updated"].append({
                "title": doc["title"],
                "path": doc["path"],
                "action": "would_update"
            })
            continue

        try:
            content = Path(doc["absolute_path"]).read_text()
            html_content = api.convert_markdown_to_storage(content)

            result = api.update_page(
                doc["confluence_id"],
                doc["title"],
                html_content,
                doc["confluence_version"]
            )

            report["updated"].append({
                "title": doc["title"],
                "path": doc["path"],
                "confluence_id": doc["confluence_id"],
                "new_version": result["version"]["number"]
            })

        except Exception as e:
            report["errors"].append({
                "title": doc["title"],
                "path": doc["path"],
                "error": str(e)
            })

    # Skip unchanged
    for doc in changes["unchanged"]:
        report["skipped"].append({
            "title": doc["title"],
            "path": doc["path"],
            "reason": "unchanged"
        })

    return report


def resolve_parent_pages(
    api: ConfluenceAPI,
    space_key: str,
    manifest: Dict[str, Any]
) -> Dict[str, str]:
    """
    Find or create parent pages for each doc type.

    TODO: Customize parent page creation strategy
    """
    parent_pages = {}
    doc_types = set(doc["confluence_parent"] for doc in manifest["documents"])

    for parent_title in doc_types:
        page = api.get_page_by_title(parent_title, space_key)
        if page:
            # Find doc_type for this parent
            for doc in manifest["documents"]:
                if doc["confluence_parent"] == parent_title:
                    parent_pages[doc["doc_type"]] = page["id"]
                    break
        else:
            print(f"Warning: Parent page '{parent_title}' not found in space {space_key}", file=sys.stderr)

    return parent_pages


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Sync documentation to Confluence"
    )
    parser.add_argument(
        "--manifest", "-m",
        required=True,
        help="Path to docs-manifest.json from extract-docs.py"
    )
    parser.add_argument(
        "--space", "-s",
        required=True,
        help="Confluence space key"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually apply changes to Confluence"
    )
    parser.add_argument(
        "--state-file",
        default=SYNC_STATE_FILE,
        help=f"Sync state file (default: {SYNC_STATE_FILE})"
    )
    parser.add_argument(
        "--output", "-o",
        help="Write report to file (default: stdout)"
    )

    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        parser.error("Must specify --dry-run or --apply")

    # Load manifest
    with open(args.manifest) as f:
        manifest = json.load(f)

    print(f"Loaded manifest with {manifest['doc_count']} documents", file=sys.stderr)

    # Initialize API
    api = ConfluenceAPI()

    # Load sync state
    state_file = Path(args.state_file)
    sync_state = load_sync_state(state_file)

    # Resolve parent pages
    print("Resolving parent pages...", file=sys.stderr)
    parent_pages = resolve_parent_pages(api, args.space, manifest)

    # Compute changes
    print("Computing changes...", file=sys.stderr)
    changes = compute_changes(manifest, sync_state, api, args.space)

    print(f"  Create: {len(changes['create'])}", file=sys.stderr)
    print(f"  Update: {len(changes['update'])}", file=sys.stderr)
    print(f"  Unchanged: {len(changes['unchanged'])}", file=sys.stderr)
    print(f"  Conflicts: {len(changes['conflicts'])}", file=sys.stderr)

    # Execute sync
    dry_run = not args.apply
    if dry_run:
        print("\n=== DRY RUN MODE ===", file=sys.stderr)

    report = execute_sync(changes, api, args.space, parent_pages, dry_run)

    # Update sync state if not dry run
    if args.apply and not report["errors"]:
        new_synced = sync_state.get("synced_docs", {})
        for doc in report["created"] + report["updated"]:
            if "confluence_id" in doc:
                new_synced[doc["path"]] = {
                    "confluence_id": doc["confluence_id"],
                    "content_hash": next(
                        d["content_hash"]
                        for d in manifest["documents"]
                        if d["path"] == doc["path"]
                    ),
                    "confluence_version": doc.get("new_version", 1)
                }
        sync_state["synced_docs"] = new_synced
        save_sync_state(state_file, sync_state)
        print(f"Sync state saved to {state_file}", file=sys.stderr)

    # Output report
    report_json = json.dumps(report, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(report_json)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(report_json)


if __name__ == "__main__":
    main()
