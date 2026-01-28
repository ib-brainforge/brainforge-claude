#!/usr/bin/env python3
"""
Pattern Scanner
Scans code for design pattern usage and violations.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# Pattern detection rules
FRONTEND_PATTERNS = {
    "container_presenter": {
        "indicators": [
            r"Container\s*\(",
            r"Presenter\s*\(",
            r"\.container\.",
            r"\.presenter\.",
        ],
        "positive": True,
    },
    "custom_hooks": {
        "indicators": [r"function\s+use[A-Z]", r"const\s+use[A-Z].*=.*\("],
        "positive": True,
    },
    "direct_fetch": {
        "indicators": [
            r"fetch\s*\(",
            r"axios\.",
            r"XMLHttpRequest",
        ],
        "positive": False,  # Anti-pattern
        "suggestion": "Use @core/api-client instead of direct fetch/axios",
    },
    "prop_drilling": {
        "indicators": [],  # Detected by AST analysis
        "positive": False,
    },
    "error_boundary": {
        "indicators": [
            r"ErrorBoundary",
            r"componentDidCatch",
        ],
        "positive": True,
    },
    "inline_styles": {
        "indicators": [r"style\s*=\s*\{\s*\{"],
        "positive": False,
        "suggestion": "Use Tailwind CSS or CSS modules",
    },
}

BACKEND_PATTERNS = {
    "repository_pattern": {
        "indicators": [
            r"IRepository<",
            r"Repository<",
            r": IRepository",
        ],
        "positive": True,
    },
    "direct_dbcontext": {
        "indicators": [
            r"DbContext\s+_",
            r"private.*DbContext",
            r"\.DbContext\.",
        ],
        "positive": False,
        "suggestion": "Use IRepository<T> instead of direct DbContext",
    },
    "result_pattern": {
        "indicators": [
            r"Result<",
            r"Result\.Success",
            r"Result\.Failure",
        ],
        "positive": True,
    },
    "throwing_exceptions": {
        "indicators": [
            r"throw\s+new\s+\w*Exception",
            r"throw\s+new\s+ApplicationException",
        ],
        "positive": False,
        "suggestion": "Use Result<T> pattern instead of throwing exceptions",
    },
    "cqrs_pattern": {
        "indicators": [
            r"IRequest<",
            r"IRequestHandler<",
            r": IRequest<",
            r"Command\s*:",
            r"Query\s*:",
        ],
        "positive": True,
    },
    "options_pattern": {
        "indicators": [
            r"IOptions<",
            r"IOptionsSnapshot<",
            r"\.Configure<",
        ],
        "positive": True,
    },
    "magic_strings": {
        "indicators": [
            r'Configuration\["[^"]+"\]',
            r'GetSection\("[^"]+"\)',
        ],
        "positive": False,
        "suggestion": "Use Options pattern with strongly-typed configuration",
    },
}


def scan_file(file_path: Path, patterns: Dict) -> Dict[str, Any]:
    """Scan a single file for pattern usage."""
    try:
        content = file_path.read_text(errors="ignore")
    except Exception as e:
        return {"error": str(e)}

    findings = {
        "file": str(file_path),
        "patterns_found": [],
        "anti_patterns": [],
        "line_count": len(content.splitlines()),
    }

    for pattern_name, pattern_def in patterns.items():
        for indicator in pattern_def.get("indicators", []):
            matches = list(re.finditer(indicator, content))
            if matches:
                finding = {
                    "pattern": pattern_name,
                    "count": len(matches),
                    "locations": [],
                }

                # Get line numbers for matches
                for match in matches[:5]:  # Limit to first 5
                    line_num = content[: match.start()].count("\n") + 1
                    finding["locations"].append(
                        {"line": line_num, "match": match.group()[:50]}
                    )

                if pattern_def.get("positive", True):
                    findings["patterns_found"].append(finding)
                else:
                    finding["suggestion"] = pattern_def.get("suggestion", "")
                    findings["anti_patterns"].append(finding)

    return findings


def detect_tech_stack(target: str) -> Dict[str, Any]:
    """Detect the technology stack of the target."""
    target_path = Path(target)
    stack = {
        "frontend": None,
        "backend": None,
        "frameworks": [],
        "files_by_type": {},
    }

    if not target_path.exists():
        return stack

    # Count file types
    extensions = {}
    for f in target_path.rglob("*"):
        if f.is_file() and not any(
            p in str(f) for p in ["node_modules", "bin", "obj", ".git"]
        ):
            ext = f.suffix.lower()
            extensions[ext] = extensions.get(ext, 0) + 1

    stack["files_by_type"] = extensions

    # Detect frontend
    if any(ext in extensions for ext in [".tsx", ".jsx"]):
        stack["frontend"] = "react"
    elif ".vue" in extensions:
        stack["frontend"] = "vue"
    elif ".svelte" in extensions:
        stack["frontend"] = "svelte"

    # Detect backend
    if ".cs" in extensions:
        stack["backend"] = "dotnet"
    elif ".py" in extensions:
        stack["backend"] = "python"
    elif ".go" in extensions:
        stack["backend"] = "go"
    elif ".java" in extensions:
        stack["backend"] = "java"

    # Detect frameworks from package.json
    package_json = target_path / "package.json"
    if not package_json.exists():
        package_json = target_path.parent / "package.json"

    if package_json.exists():
        try:
            with open(package_json) as f:
                pkg = json.load(f)
                deps = {
                    **pkg.get("dependencies", {}),
                    **pkg.get("devDependencies", {}),
                }
                if "react-query" in deps or "@tanstack/react-query" in deps:
                    stack["frameworks"].append("react-query")
                if "zustand" in deps:
                    stack["frameworks"].append("zustand")
                if "redux" in deps:
                    stack["frameworks"].append("redux")
                if "tailwindcss" in deps:
                    stack["frameworks"].append("tailwind")
        except Exception:
            pass

    return stack


def scan_directory(
    target: str, output_file: str, tech_stack: Optional[str] = None
) -> Dict[str, Any]:
    """Scan a directory for pattern usage."""
    target_path = Path(target)

    if not target_path.exists():
        result = {"success": False, "error": f"Target not found: {target}"}
        write_output(output_file, result)
        return result

    # Detect stack if not specified
    stack = detect_tech_stack(target)

    # Determine which patterns to use
    patterns_to_check = {}
    if tech_stack == "frontend" or stack.get("frontend"):
        patterns_to_check.update(FRONTEND_PATTERNS)
    if tech_stack == "backend" or stack.get("backend"):
        patterns_to_check.update(BACKEND_PATTERNS)
    if not patterns_to_check:
        patterns_to_check = {**FRONTEND_PATTERNS, **BACKEND_PATTERNS}

    # Scan files
    all_findings = []
    files_scanned = 0

    extensions = {".ts", ".tsx", ".js", ".jsx", ".cs", ".py", ".go", ".java"}

    if target_path.is_file():
        files_to_scan = [target_path]
    else:
        files_to_scan = [
            f
            for f in target_path.rglob("*")
            if f.suffix in extensions
            and not any(
                p in str(f) for p in ["node_modules", "bin", "obj", ".git", "dist"]
            )
        ]

    for file_path in files_to_scan[:100]:  # Limit to 100 files
        finding = scan_file(file_path, patterns_to_check)
        if finding.get("patterns_found") or finding.get("anti_patterns"):
            all_findings.append(finding)
        files_scanned += 1

    # Aggregate results
    patterns_summary = {}
    anti_patterns_summary = {}

    for finding in all_findings:
        for p in finding.get("patterns_found", []):
            name = p["pattern"]
            if name not in patterns_summary:
                patterns_summary[name] = {"count": 0, "files": []}
            patterns_summary[name]["count"] += p["count"]
            patterns_summary[name]["files"].append(finding["file"])

        for ap in finding.get("anti_patterns", []):
            name = ap["pattern"]
            if name not in anti_patterns_summary:
                anti_patterns_summary[name] = {
                    "count": 0,
                    "files": [],
                    "suggestion": ap.get("suggestion", ""),
                }
            anti_patterns_summary[name]["count"] += ap["count"]
            anti_patterns_summary[name]["files"].append(
                {"file": finding["file"], "locations": ap.get("locations", [])}
            )

    # Calculate score
    total_patterns = len(patterns_summary)
    total_anti_patterns = len(anti_patterns_summary)

    if total_patterns + total_anti_patterns > 0:
        score = int(
            (total_patterns / (total_patterns + total_anti_patterns * 2)) * 100
        )
    else:
        score = 100

    result = {
        "success": True,
        "target": target,
        "tech_stack": stack,
        "files_scanned": files_scanned,
        "patterns_found": patterns_summary,
        "anti_patterns_found": anti_patterns_summary,
        "score": {
            "pattern_compliance": score,
            "anti_pattern_count": total_anti_patterns,
        },
        "status": "PASS" if total_anti_patterns == 0 else ("WARN" if score >= 70 else "FAIL"),
    }

    write_output(output_file, result)
    return result


def check_core_components(
    target: str, core_components_file: str, output_file: str
) -> Dict[str, Any]:
    """Check usage of core components vs custom implementations."""
    target_path = Path(target)

    # Define expected core component patterns
    core_patterns = {
        # Frontend
        "@core/ui": {
            "should_use": ["Button", "Modal", "DataGrid", "Input", "Form"],
            "instead_of": [
                r"<button",
                r"custom.*modal",
                r"custom.*table",
                r"<input\s",
            ],
        },
        "@core/api-client": {
            "should_use": ["userApi", "orderApi"],
            "instead_of": [r"fetch\(", r"axios\."],
        },
        "@core/hooks": {
            "should_use": ["useAuth", "useQuery"],
            "instead_of": [],
        },
        # Backend
        "Core.Data": {
            "should_use": ["IRepository", "IUnitOfWork"],
            "instead_of": [r"DbContext\s"],
        },
        "Core.Common": {
            "should_use": ["Result<", "Result.Success"],
            "instead_of": [r"throw new.*Exception"],
        },
    }

    used_correctly = []
    should_use = []

    if target_path.exists():
        if target_path.is_file():
            files = [target_path]
        else:
            files = list(target_path.rglob("*"))
            files = [
                f
                for f in files
                if f.suffix in {".ts", ".tsx", ".js", ".jsx", ".cs"}
                and "node_modules" not in str(f)
            ][:50]

        for file_path in files:
            try:
                content = file_path.read_text(errors="ignore")

                for package, patterns in core_patterns.items():
                    # Check if using core package
                    if package.startswith("@"):
                        if f'from "{package}' in content or f"from '{package}" in content:
                            used_correctly.append(
                                {"package": package, "file": str(file_path)}
                            )

                    # Check for patterns that should use core
                    for bad_pattern in patterns.get("instead_of", []):
                        if re.search(bad_pattern, content, re.IGNORECASE):
                            should_use.append(
                                {
                                    "file": str(file_path),
                                    "instead_of": bad_pattern,
                                    "use": package,
                                }
                            )
            except Exception:
                continue

    result = {
        "success": True,
        "used_correctly": used_correctly,
        "should_use": should_use[:20],  # Limit
        "score": 100 - (len(should_use) * 5),  # Deduct 5 points per violation
    }

    write_output(output_file, result)
    return result


def write_output(filepath: str, data: Dict[str, Any]) -> None:
    """Write JSON output to file."""
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def main():
    if len(sys.argv) < 2:
        print("Usage: pattern-scanner.py <command> [options]")
        print("Commands: scan, detect-stack, check-components")
        sys.exit(1)

    command = sys.argv[1]

    # Parse arguments
    args = {}
    i = 2
    while i < len(sys.argv):
        if sys.argv[i].startswith("--"):
            key = sys.argv[i][2:].replace("-", "_")
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
                args[key] = sys.argv[i + 1]
                i += 2
            else:
                args[key] = True
                i += 1
        else:
            i += 1

    if command == "scan":
        result = scan_directory(
            target=args.get("target", "."),
            output_file=args.get("output", "/tmp/pattern-scan.json"),
            tech_stack=args.get("tech_stack"),
        )

    elif command == "detect-stack":
        result = detect_tech_stack(args.get("target", "."))
        write_output(args.get("output", "/tmp/stack-info.json"), result)

    elif command == "check-components":
        result = check_core_components(
            target=args.get("target", "."),
            core_components_file=args.get("core_components", ""),
            output_file=args.get("output", "/tmp/component-check.json"),
        )

    else:
        result = {"error": f"Unknown command: {command}"}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
