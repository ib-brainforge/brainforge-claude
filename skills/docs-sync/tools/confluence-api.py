#!/usr/bin/env python3
"""
Confluence REST API wrapper for documentation sync.

TODO: Implement these functions with your Confluence setup.
This provides the foundation - customize for your auth method and space structure.

Environment variables required:
- CONFLUENCE_BASE_URL: e.g., https://your-domain.atlassian.net/wiki
- CONFLUENCE_API_TOKEN: API token for authentication
- CONFLUENCE_USER_EMAIL: Email associated with token

Usage:
    from confluence_api import ConfluenceAPI
    api = ConfluenceAPI()
    page = api.get_page("Page Title", "SPACE_KEY")
"""

import os
import sys
import json
import base64
from typing import Optional, Dict, List, Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode, quote


class ConfluenceAPI:
    """Confluence REST API client."""

    def __init__(self):
        self.base_url = os.environ.get("CONFLUENCE_BASE_URL", "").rstrip("/")
        self.api_token = os.environ.get("CONFLUENCE_API_TOKEN", "")
        self.user_email = os.environ.get("CONFLUENCE_USER_EMAIL", "")

        if not all([self.base_url, self.api_token, self.user_email]):
            raise EnvironmentError(
                "Missing required environment variables: "
                "CONFLUENCE_BASE_URL, CONFLUENCE_API_TOKEN, CONFLUENCE_USER_EMAIL"
            )

        # Basic auth header
        credentials = f"{self.user_email}:{self.api_token}"
        self.auth_header = base64.b64encode(credentials.encode()).decode()

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Confluence API."""

        url = f"{self.base_url}/rest/api{endpoint}"
        if params:
            url = f"{url}?{urlencode(params)}"

        headers = {
            "Authorization": f"Basic {self.auth_header}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, headers=headers, method=method)

        try:
            with urlopen(req) as response:
                return json.loads(response.read().decode())
        except HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            raise Exception(f"Confluence API error {e.code}: {error_body}")

    # -------------------------------------------------------------------------
    # Page Operations
    # -------------------------------------------------------------------------

    def get_page_by_title(
        self,
        title: str,
        space_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get page by title in a space.

        TODO: Handle duplicate titles if your space allows them.

        Returns:
            Page dict with id, title, version, body, etc. or None if not found.
        """
        params = {
            "title": title,
            "spaceKey": space_key,
            "expand": "body.storage,version,ancestors"
        }
        result = self._request("GET", "/content", params=params)
        pages = result.get("results", [])
        return pages[0] if pages else None

    def get_page_by_id(self, page_id: str) -> Dict[str, Any]:
        """
        Get page by ID.

        Returns:
            Full page dict with body content.
        """
        return self._request(
            "GET",
            f"/content/{page_id}",
            params={"expand": "body.storage,version,ancestors"}
        )

    def create_page(
        self,
        space_key: str,
        title: str,
        body_html: str,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new page.

        TODO: Add labels support if you use them for categorization.

        Args:
            space_key: Space to create page in
            title: Page title
            body_html: HTML content (Confluence storage format)
            parent_id: Optional parent page ID for hierarchy

        Returns:
            Created page dict with id.
        """
        data = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": body_html,
                    "representation": "storage"
                }
            }
        }

        if parent_id:
            data["ancestors"] = [{"id": parent_id}]

        return self._request("POST", "/content", data=data)

    def update_page(
        self,
        page_id: str,
        title: str,
        body_html: str,
        current_version: int
    ) -> Dict[str, Any]:
        """
        Update existing page.

        TODO: Add minor edit support (version.minorEdit) if needed.

        Args:
            page_id: ID of page to update
            title: Page title (can be same or changed)
            body_html: New HTML content
            current_version: Current version number (for optimistic locking)

        Returns:
            Updated page dict.
        """
        data = {
            "type": "page",
            "title": title,
            "version": {"number": current_version + 1},
            "body": {
                "storage": {
                    "value": body_html,
                    "representation": "storage"
                }
            }
        }

        return self._request("PUT", f"/content/{page_id}", data=data)

    def delete_page(self, page_id: str) -> None:
        """
        Delete a page (moves to trash).

        TODO: Add permanent delete option if needed.
        """
        self._request("DELETE", f"/content/{page_id}")

    # -------------------------------------------------------------------------
    # Space & Navigation
    # -------------------------------------------------------------------------

    def get_space(self, space_key: str) -> Dict[str, Any]:
        """Get space details."""
        return self._request("GET", f"/space/{space_key}")

    def get_child_pages(
        self,
        parent_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get child pages of a parent.

        TODO: Add pagination if you have many child pages.
        """
        result = self._request(
            "GET",
            f"/content/{parent_id}/child/page",
            params={"limit": limit, "expand": "version"}
        )
        return result.get("results", [])

    def find_page_id_by_title(
        self,
        title: str,
        space_key: str
    ) -> Optional[str]:
        """Helper to get just the page ID."""
        page = self.get_page_by_title(title, space_key)
        return page["id"] if page else None

    # -------------------------------------------------------------------------
    # Content Conversion
    # -------------------------------------------------------------------------

    def convert_markdown_to_storage(self, markdown: str) -> str:
        """
        Convert markdown to Confluence storage format.

        TODO: This is a placeholder. Options:
        1. Use Confluence's built-in conversion (if available in your version)
        2. Use a library like markdown2confluence
        3. Implement custom conversion for your markdown style

        For now, wraps in preformatted block. Replace with proper conversion.
        """
        # Placeholder - replace with actual markdown conversion
        # Consider using: https://github.com/RittmanMead/md_to_conf
        escaped = markdown.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"<ac:structured-macro ac:name=\"code\"><ac:plain-text-body><![CDATA[{escaped}]]></ac:plain-text-body></ac:structured-macro>"

    def convert_storage_to_markdown(self, storage_html: str) -> str:
        """
        Convert Confluence storage format to markdown.

        TODO: Implement based on your needs. Options:
        1. Use html2text library
        2. Custom XSLT transformation
        3. Regex-based extraction for simple content

        For now, returns raw HTML. Replace with proper conversion.
        """
        # Placeholder - replace with actual conversion
        return storage_html


# -----------------------------------------------------------------------------
# CLI Interface
# -----------------------------------------------------------------------------

def main():
    """CLI interface for testing API operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Confluence API CLI")
    parser.add_argument("action", choices=["get", "create", "update", "delete", "children"])
    parser.add_argument("--space", "-s", required=True, help="Space key")
    parser.add_argument("--title", "-t", help="Page title")
    parser.add_argument("--id", help="Page ID")
    parser.add_argument("--parent", help="Parent page ID")
    parser.add_argument("--body", help="Body content (HTML) or @filename")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    args = parser.parse_args()

    api = ConfluenceAPI()
    result = None

    if args.action == "get":
        if args.id:
            result = api.get_page_by_id(args.id)
        elif args.title:
            result = api.get_page_by_title(args.title, args.space)
        else:
            parser.error("--title or --id required for get")

    elif args.action == "create":
        if not args.title or not args.body:
            parser.error("--title and --body required for create")
        body = open(args.body[1:]).read() if args.body.startswith("@") else args.body
        result = api.create_page(args.space, args.title, body, args.parent)

    elif args.action == "update":
        if not args.id or not args.body:
            parser.error("--id and --body required for update")
        page = api.get_page_by_id(args.id)
        body = open(args.body[1:]).read() if args.body.startswith("@") else args.body
        result = api.update_page(
            args.id,
            args.title or page["title"],
            body,
            page["version"]["number"]
        )

    elif args.action == "delete":
        if not args.id:
            parser.error("--id required for delete")
        api.delete_page(args.id)
        result = {"status": "deleted", "id": args.id}

    elif args.action == "children":
        if not args.id:
            parser.error("--id required for children")
        result = api.get_child_pages(args.id)

    # Output
    output = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
