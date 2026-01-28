#!/usr/bin/env python3
"""
Plan Validation Script
Validates implementation plans against architectural rules.
Used by plan-validator agent for deterministic checks.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def check_boundaries(plan_file: str, rules_file: str, output_file: str) -> Dict[str, Any]:
    """
    Check if plan respects service boundaries defined in rules.
    """
    try:
        with open(plan_file) as f:
            plan = json.load(f)
    except Exception as e:
        return write_result(output_file, {
            "success": False,
            "error": f"Failed to read plan: {e}"
        })

    # Load rules if available
    rules = load_rules(rules_file)

    issues = []
    warnings = []

    # Extract service interactions from plan
    phases = plan.get("phases", [])

    for phase in phases:
        for task in phase.get("tasks", []):
            service = task.get("service", "")
            interactions = task.get("interacts_with", [])
            changes = task.get("changes", [])

            # Check direct database access violations
            if task.get("direct_db_access") and service not in rules.get("db_owners", []):
                issues.append({
                    "severity": "error",
                    "task": task.get("title"),
                    "issue": f"Service '{service}' has direct DB access but is not a DB owner",
                    "rule": "service-boundaries#database-access"
                })

            # Check cross-service calls
            for interaction in interactions:
                allowed = rules.get("allowed_interactions", {}).get(service, [])
                if interaction not in allowed and interaction != service:
                    if interaction in rules.get("restricted_services", []):
                        issues.append({
                            "severity": "error",
                            "task": task.get("title"),
                            "issue": f"Service '{service}' cannot interact with restricted service '{interaction}'",
                            "rule": "service-boundaries#restricted-services"
                        })
                    else:
                        warnings.append({
                            "severity": "warning",
                            "task": task.get("title"),
                            "issue": f"Service '{service}' interacts with '{interaction}' - not in allowed list",
                            "rule": "service-boundaries#service-interactions"
                        })

            # Check for boundary-crossing changes
            for change in changes:
                if change.get("type") == "schema" and service not in rules.get("schema_owners", [service]):
                    issues.append({
                        "severity": "error",
                        "task": task.get("title"),
                        "issue": f"Service '{service}' modifying schema it doesn't own",
                        "rule": "service-boundaries#schema-ownership"
                    })

    status = "PASS"
    if issues:
        status = "FAIL"
    elif warnings:
        status = "WARN"

    result = {
        "success": True,
        "check": "service_boundaries",
        "status": status,
        "issues": issues,
        "warnings": warnings,
        "total_issues": len(issues),
        "total_warnings": len(warnings)
    }

    return write_result(output_file, result)


def check_security(plan_file: str, output_file: str) -> Dict[str, Any]:
    """
    Check plan for security compliance.
    """
    try:
        with open(plan_file) as f:
            plan = json.load(f)
    except Exception as e:
        return write_result(output_file, {
            "success": False,
            "error": f"Failed to read plan: {e}"
        })

    issues = []
    warnings = []

    security_checklist = {
        "authentication": False,
        "authorization": False,
        "input_validation": False,
        "rate_limiting": False,
        "audit_logging": False,
        "data_encryption": False
    }

    phases = plan.get("phases", [])

    for phase in phases:
        for task in phase.get("tasks", []):
            title_lower = task.get("title", "").lower()
            desc_lower = task.get("description", "").lower()
            combined = title_lower + " " + desc_lower

            # Check for security measures
            if any(k in combined for k in ["auth", "login", "session", "token", "jwt"]):
                security_checklist["authentication"] = True

            if any(k in combined for k in ["permission", "role", "access control", "rbac", "authorize"]):
                security_checklist["authorization"] = True

            if any(k in combined for k in ["validate", "sanitize", "escape", "xss", "injection"]):
                security_checklist["input_validation"] = True

            if any(k in combined for k in ["rate limit", "throttle", "ddos"]):
                security_checklist["rate_limiting"] = True

            if any(k in combined for k in ["audit", "log", "track"]):
                security_checklist["audit_logging"] = True

            if any(k in combined for k in ["encrypt", "ssl", "tls", "https"]):
                security_checklist["data_encryption"] = True

            # Check for security anti-patterns
            if "password" in combined and "hash" not in combined and "bcrypt" not in combined:
                warnings.append({
                    "severity": "warning",
                    "task": task.get("title"),
                    "issue": "Password handling mentioned without hashing",
                    "suggestion": "Ensure passwords are hashed with bcrypt/argon2"
                })

            if "log" in combined and any(k in combined for k in ["pii", "personal", "email", "phone", "ssn"]):
                issues.append({
                    "severity": "error",
                    "task": task.get("title"),
                    "issue": "Logging PII data detected",
                    "suggestion": "Use PII masking utilities for logging"
                })

            if task.get("public_endpoint") and not task.get("rate_limited"):
                warnings.append({
                    "severity": "warning",
                    "task": task.get("title"),
                    "issue": "Public endpoint without rate limiting",
                    "suggestion": "Add rate limiting middleware"
                })

    # Check for missing security measures in features that need them
    has_user_data = any(
        "user" in str(phase).lower() or "account" in str(phase).lower()
        for phase in phases
    )

    if has_user_data:
        if not security_checklist["authentication"]:
            issues.append({
                "severity": "error",
                "task": "Overall Plan",
                "issue": "User data feature without authentication planning",
                "suggestion": "Add authentication implementation tasks"
            })

        if not security_checklist["authorization"]:
            warnings.append({
                "severity": "warning",
                "task": "Overall Plan",
                "issue": "User data feature without explicit authorization planning",
                "suggestion": "Consider adding role-based access control"
            })

    has_api = any(
        "api" in str(phase).lower() or "endpoint" in str(phase).lower()
        for phase in phases
    )

    if has_api and not security_checklist["input_validation"]:
        warnings.append({
            "severity": "warning",
            "task": "Overall Plan",
            "issue": "API feature without explicit input validation",
            "suggestion": "Add input validation tasks for all endpoints"
        })

    status = "PASS"
    if issues:
        status = "FAIL"
    elif warnings:
        status = "WARN"

    result = {
        "success": True,
        "check": "security",
        "status": status,
        "security_checklist": security_checklist,
        "issues": issues,
        "warnings": warnings,
        "total_issues": len(issues),
        "total_warnings": len(warnings)
    }

    return write_result(output_file, result)


def check_dependencies(plan_file: str, output_file: str) -> Dict[str, Any]:
    """
    Check task dependencies for correctness and ordering.
    """
    try:
        with open(plan_file) as f:
            plan = json.load(f)
    except Exception as e:
        return write_result(output_file, {
            "success": False,
            "error": f"Failed to read plan: {e}"
        })

    issues = []
    warnings = []

    # Build task graph
    tasks = {}
    phases = plan.get("phases", [])

    for phase_idx, phase in enumerate(phases):
        for task in phase.get("tasks", []):
            task_id = task.get("id", task.get("title", f"task-{len(tasks)}"))
            tasks[task_id] = {
                "phase": phase_idx,
                "dependencies": task.get("dependencies", []),
                "title": task.get("title", task_id)
            }

    # Check for missing dependencies
    for task_id, task_info in tasks.items():
        for dep in task_info["dependencies"]:
            if dep not in tasks:
                issues.append({
                    "severity": "error",
                    "task": task_info["title"],
                    "issue": f"Dependency '{dep}' not found in plan",
                    "suggestion": "Add missing task or remove dependency"
                })

    # Check for circular dependencies
    circular = find_circular_dependencies(tasks)
    if circular:
        for cycle in circular:
            issues.append({
                "severity": "error",
                "task": "Dependency Graph",
                "issue": f"Circular dependency detected: {' -> '.join(cycle)}",
                "suggestion": "Break the circular dependency"
            })

    # Check phase ordering
    for task_id, task_info in tasks.items():
        for dep in task_info["dependencies"]:
            if dep in tasks:
                dep_phase = tasks[dep]["phase"]
                if dep_phase > task_info["phase"]:
                    issues.append({
                        "severity": "error",
                        "task": task_info["title"],
                        "issue": f"Depends on '{dep}' which is in a later phase",
                        "suggestion": "Reorder phases or move task"
                    })

    # Check for implicit dependencies (heuristic)
    for task_id, task_info in tasks.items():
        title_lower = task_info["title"].lower()

        # Frontend tasks usually depend on API tasks
        if "frontend" in title_lower or "ui" in title_lower or "component" in title_lower:
            has_api_dep = any(
                "api" in tasks.get(d, {}).get("title", "").lower()
                for d in task_info["dependencies"]
            )
            # Check if there's an API task in earlier phase
            api_tasks_earlier = [
                t for t_id, t in tasks.items()
                if "api" in t["title"].lower() and t["phase"] < task_info["phase"]
            ]
            if api_tasks_earlier and not has_api_dep:
                warnings.append({
                    "severity": "warning",
                    "task": task_info["title"],
                    "issue": "Frontend task may need API dependency",
                    "suggestion": "Consider if this depends on API endpoints"
                })

    status = "PASS"
    if issues:
        status = "FAIL"
    elif warnings:
        status = "WARN"

    result = {
        "success": True,
        "check": "dependencies",
        "status": status,
        "total_tasks": len(tasks),
        "issues": issues,
        "warnings": warnings,
        "total_issues": len(issues),
        "total_warnings": len(warnings),
        "dependency_graph_valid": len([i for i in issues if "Circular" in i.get("issue", "")]) == 0
    }

    return write_result(output_file, result)


def find_circular_dependencies(tasks: Dict) -> List[List[str]]:
    """Find circular dependencies using DFS."""
    cycles = []
    visited = set()
    rec_stack = set()

    def dfs(node: str, path: List[str]) -> bool:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for dep in tasks.get(node, {}).get("dependencies", []):
            if dep not in tasks:
                continue

            if dep not in visited:
                if dfs(dep, path):
                    return True
            elif dep in rec_stack:
                # Found cycle
                cycle_start = path.index(dep)
                cycles.append(path[cycle_start:] + [dep])
                return True

        path.pop()
        rec_stack.remove(node)
        return False

    for task_id in tasks:
        if task_id not in visited:
            dfs(task_id, [])

    return cycles


def aggregate(
    arch_result: str,
    boundary_result: str,
    frontend_result: str,
    backend_result: str,
    core_result: str,
    infra_result: str,
    security_result: str,
    dependency_result: str,
    output_file: str
) -> Dict[str, Any]:
    """
    Aggregate all validation results into final verdict.
    """
    results = {}
    files = {
        "architectural_fit": arch_result,
        "service_boundaries": boundary_result,
        "frontend_patterns": frontend_result,
        "backend_patterns": backend_result,
        "core_library": core_result,
        "infrastructure": infra_result,
        "security": security_result,
        "dependencies": dependency_result
    }

    total_issues = 0
    total_warnings = 0
    blocking_issues = []

    for name, filepath in files.items():
        if filepath and os.path.exists(filepath):
            try:
                with open(filepath) as f:
                    data = json.load(f)
                    results[name] = {
                        "status": data.get("status", "UNKNOWN"),
                        "issues": data.get("issues", []),
                        "warnings": data.get("warnings", [])
                    }
                    total_issues += len(data.get("issues", []))
                    total_warnings += len(data.get("warnings", []))

                    # Collect blocking issues
                    for issue in data.get("issues", []):
                        if issue.get("severity") == "error":
                            blocking_issues.append({
                                "dimension": name,
                                **issue
                            })
            except Exception as e:
                results[name] = {
                    "status": "ERROR",
                    "error": str(e)
                }
        else:
            results[name] = {
                "status": "NOT_CHECKED"
            }

    # Determine overall status
    statuses = [r.get("status") for r in results.values()]

    if "FAIL" in statuses or "ERROR" in statuses:
        overall_status = "FAIL"
    elif "WARN" in statuses:
        overall_status = "WARN"
    elif all(s == "PASS" for s in statuses if s not in ["NOT_CHECKED", "UNKNOWN"]):
        overall_status = "PASS"
    else:
        overall_status = "UNKNOWN"

    result = {
        "success": True,
        "overall_status": overall_status,
        "approved_for_implementation": overall_status == "PASS",
        "summary": {
            "total_checks": len([s for s in statuses if s not in ["NOT_CHECKED"]]),
            "passed": statuses.count("PASS"),
            "warnings": statuses.count("WARN"),
            "failures": statuses.count("FAIL") + statuses.count("ERROR"),
            "not_checked": statuses.count("NOT_CHECKED")
        },
        "dimensions": results,
        "total_issues": total_issues,
        "total_warnings": total_warnings,
        "blocking_issues": blocking_issues,
        "recommendations": generate_recommendations(results, blocking_issues)
    }

    return write_result(output_file, result)


def generate_recommendations(results: Dict, blocking_issues: List) -> List[str]:
    """Generate actionable recommendations from validation results."""
    recommendations = []

    # Address blocking issues first
    for issue in blocking_issues[:5]:  # Top 5 blockers
        suggestion = issue.get("suggestion", "Review and fix this issue")
        recommendations.append(f"[BLOCKER] {issue.get('issue', 'Unknown issue')}: {suggestion}")

    # Dimension-specific recommendations
    if results.get("security", {}).get("status") in ["FAIL", "WARN"]:
        recommendations.append("Review security checklist and ensure all security measures are planned")

    if results.get("dependencies", {}).get("status") == "FAIL":
        recommendations.append("Fix dependency ordering before proceeding with implementation")

    if results.get("service_boundaries", {}).get("status") == "FAIL":
        recommendations.append("Revise service interactions to respect boundaries")

    return recommendations


def load_rules(rules_file: str) -> Dict:
    """Load boundary rules from file."""
    default_rules = {
        "db_owners": [],
        "schema_owners": [],
        "restricted_services": [],
        "allowed_interactions": {}
    }

    if not rules_file or not os.path.exists(rules_file):
        return default_rules

    try:
        # Try JSON first
        if rules_file.endswith('.json'):
            with open(rules_file) as f:
                return json.load(f)

        # Parse markdown rules file
        with open(rules_file) as f:
            content = f.read()

        # Extract rules from markdown (simplified parsing)
        # TODO: Implement proper markdown rule parsing
        return default_rules

    except Exception:
        return default_rules


def write_result(filepath: str, data: Dict) -> Dict:
    """Write result to file and return it."""
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    return data


def main():
    if len(sys.argv) < 2:
        print("Usage: plan-validation.py <command> [options]")
        print("Commands: check-boundaries, check-security, check-dependencies, aggregate")
        sys.exit(1)

    command = sys.argv[1]

    # Parse arguments
    args = {}
    i = 2
    while i < len(sys.argv):
        if sys.argv[i].startswith('--'):
            key = sys.argv[i][2:].replace('-', '_')
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--'):
                args[key] = sys.argv[i + 1]
                i += 2
            else:
                args[key] = True
                i += 1
        else:
            i += 1

    if command == "check-boundaries":
        result = check_boundaries(
            plan_file=args.get("plan", ""),
            rules_file=args.get("rules", ""),
            output_file=args.get("output", "/tmp/boundary-validation.json")
        )

    elif command == "check-security":
        result = check_security(
            plan_file=args.get("plan", ""),
            output_file=args.get("output", "/tmp/security-validation.json")
        )

    elif command == "check-dependencies":
        result = check_dependencies(
            plan_file=args.get("plan", ""),
            output_file=args.get("output", "/tmp/dependency-validation.json")
        )

    elif command == "aggregate":
        result = aggregate(
            arch_result=args.get("arch_result", ""),
            boundary_result=args.get("boundary_result", ""),
            frontend_result=args.get("frontend_result", ""),
            backend_result=args.get("backend_result", ""),
            core_result=args.get("core_result", ""),
            infra_result=args.get("infra_result", ""),
            security_result=args.get("security_result", ""),
            dependency_result=args.get("dependency_result", ""),
            output_file=args.get("output", "/tmp/aggregated-validation.json")
        )

    else:
        result = {"error": f"Unknown command: {command}"}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
