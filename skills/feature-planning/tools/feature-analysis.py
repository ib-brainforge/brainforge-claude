#!/usr/bin/env python3
"""
Feature Analysis Script
Supports feature discovery, plan synthesis, and task generation.
Used by feature-planner agent for deterministic operations.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def discover_affected_services(
    feature_name: str,
    description: str,
    repos_root: str,
    output_file: str
) -> Dict[str, Any]:
    """
    Analyze feature description and scan repos to find affected services.
    """
    repos_path = Path(repos_root)

    # Extract keywords from description for matching
    keywords = extract_keywords(description)

    affected = {
        "frontend_services": [],
        "backend_services": [],
        "shared_libraries": [],
        "infrastructure": []
    }

    if not repos_path.exists():
        result = {
            "success": False,
            "error": f"Repos root not found: {repos_root}",
            "affected_services": affected
        }
        write_output(output_file, result)
        return result

    # Scan each repository
    for repo_dir in repos_path.iterdir():
        if not repo_dir.is_dir() or repo_dir.name.startswith('.'):
            continue

        service_type = classify_service(repo_dir)
        relevance = calculate_relevance(repo_dir, keywords, description)

        if relevance["score"] > 0.3:  # Threshold for inclusion
            service_info = {
                "name": repo_dir.name,
                "path": str(repo_dir),
                "relevance_score": relevance["score"],
                "matched_keywords": relevance["matched_keywords"],
                "matched_files": relevance["matched_files"][:5]  # Top 5
            }

            if service_type == "frontend":
                affected["frontend_services"].append(service_info)
            elif service_type == "backend":
                affected["backend_services"].append(service_info)
            elif service_type == "shared":
                affected["shared_libraries"].append(service_info)
            elif service_type == "infra":
                affected["infrastructure"].append(service_info)

    # Sort by relevance
    for key in affected:
        affected[key].sort(key=lambda x: x["relevance_score"], reverse=True)

    result = {
        "success": True,
        "feature_name": feature_name,
        "keywords_extracted": keywords,
        "affected_services": affected,
        "total_affected": sum(len(v) for v in affected.values())
    }

    write_output(output_file, result)
    return result


def extract_keywords(description: str) -> List[str]:
    """Extract relevant keywords from feature description."""
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
        'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'and', 'or', 'but', 'if', 'then', 'else', 'when', 'where', 'why',
        'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
        'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
        'than', 'too', 'very', 'just', 'also', 'now', 'here', 'there', 'this',
        'that', 'these', 'those', 'i', 'we', 'you', 'he', 'she', 'it', 'they',
        'user', 'users', 'system', 'feature', 'implement', 'add', 'create',
        'make', 'want', 'need', 'able', 'allow', 'should', 'must'
    }

    # Extract words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', description.lower())

    # Filter and dedupe
    keywords = list(set(w for w in words if w not in stop_words))

    return keywords[:20]  # Limit to top 20


def classify_service(repo_dir: Path) -> str:
    """Classify a repository by its type."""
    # Check for frontend indicators
    if (repo_dir / "package.json").exists():
        pkg_json = repo_dir / "package.json"
        try:
            with open(pkg_json) as f:
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                if any(k in deps for k in ["react", "vue", "angular", "@angular/core", "svelte"]):
                    return "frontend"
        except:
            pass

    # Check for backend indicators
    if (repo_dir / "requirements.txt").exists() or (repo_dir / "setup.py").exists():
        return "backend"
    if any((repo_dir / f).exists() for f in ["go.mod", "Cargo.toml"]):
        return "backend"
    if (repo_dir / "pom.xml").exists() or (repo_dir / "build.gradle").exists():
        return "backend"
    if any(f.suffix == ".csproj" for f in repo_dir.glob("**/*.csproj")):
        return "backend"

    # Check for shared library indicators
    if "core" in repo_dir.name.lower() or "shared" in repo_dir.name.lower():
        return "shared"
    if "common" in repo_dir.name.lower() or "lib" in repo_dir.name.lower():
        return "shared"

    # Check for infrastructure indicators
    if (repo_dir / "terraform").exists() or (repo_dir / "pulumi").exists():
        return "infra"
    if (repo_dir / "kubernetes").exists() or (repo_dir / "k8s").exists():
        return "infra"
    if (repo_dir / "helm").exists():
        return "infra"
    if any(f.name in ["Dockerfile", "docker-compose.yml"] for f in repo_dir.iterdir()):
        if "infra" in repo_dir.name.lower() or "deploy" in repo_dir.name.lower():
            return "infra"

    return "backend"  # Default


def calculate_relevance(repo_dir: Path, keywords: List[str], description: str) -> Dict[str, Any]:
    """Calculate how relevant a repo is to the feature."""
    matched_keywords = []
    matched_files = []
    score = 0.0

    # Check repo name
    repo_name_lower = repo_dir.name.lower()
    for kw in keywords:
        if kw in repo_name_lower:
            matched_keywords.append(kw)
            score += 0.2

    # Scan source files (limited depth for performance)
    source_extensions = {'.ts', '.tsx', '.js', '.jsx', '.py', '.cs', '.go', '.java'}

    try:
        for file_path in repo_dir.rglob("*"):
            if file_path.suffix in source_extensions:
                # Skip node_modules, vendor, etc.
                if any(p in str(file_path) for p in ['node_modules', 'vendor', 'dist', 'build', '.git']):
                    continue

                try:
                    content = file_path.read_text(errors='ignore').lower()
                    file_matches = []

                    for kw in keywords:
                        if kw in content:
                            file_matches.append(kw)
                            if kw not in matched_keywords:
                                matched_keywords.append(kw)

                    if file_matches:
                        matched_files.append({
                            "file": str(file_path.relative_to(repo_dir)),
                            "keywords": file_matches
                        })
                        score += 0.05 * len(file_matches)

                except Exception:
                    continue

                # Limit files scanned
                if len(matched_files) > 50:
                    break

    except Exception:
        pass

    # Normalize score
    score = min(score, 1.0)

    return {
        "score": round(score, 2),
        "matched_keywords": matched_keywords,
        "matched_files": matched_files
    }


def synthesize_inputs(
    master_input: str,
    frontend_input: str,
    backend_input: str,
    core_input: str,
    infra_input: str,
    output_file: str
) -> Dict[str, Any]:
    """
    Combine inputs from all architectural validators into unified requirements.
    """
    inputs = {}

    # Load each input file
    input_files = {
        "master_architect": master_input,
        "frontend": frontend_input,
        "backend": backend_input,
        "core": core_input,
        "infrastructure": infra_input
    }

    for name, filepath in input_files.items():
        if filepath and os.path.exists(filepath):
            try:
                with open(filepath) as f:
                    inputs[name] = json.load(f)
            except Exception as e:
                inputs[name] = {"error": str(e), "status": "failed"}
        else:
            inputs[name] = {"status": "not_provided"}

    # Synthesize requirements
    synthesized = {
        "architectural_constraints": [],
        "frontend_requirements": [],
        "backend_requirements": [],
        "core_library_impacts": [],
        "infrastructure_changes": [],
        "cross_cutting_concerns": [],
        "risks": [],
        "dependencies": []
    }

    # Extract from master architect
    if "constraints" in inputs.get("master_architect", {}):
        synthesized["architectural_constraints"] = inputs["master_architect"]["constraints"]
    if "concerns" in inputs.get("master_architect", {}):
        synthesized["risks"].extend(inputs["master_architect"]["concerns"])

    # Extract from frontend
    if "patterns" in inputs.get("frontend", {}):
        synthesized["frontend_requirements"] = inputs["frontend"]["patterns"]
    if "components" in inputs.get("frontend", {}):
        synthesized["frontend_requirements"].extend(inputs["frontend"]["components"])

    # Extract from backend
    if "requirements" in inputs.get("backend", {}):
        synthesized["backend_requirements"] = inputs["backend"]["requirements"]
    if "api_design" in inputs.get("backend", {}):
        synthesized["backend_requirements"].append(inputs["backend"]["api_design"])

    # Extract from core
    if "impacts" in inputs.get("core", {}):
        synthesized["core_library_impacts"] = inputs["core"]["impacts"]
    if "breaking_changes" in inputs.get("core", {}):
        synthesized["risks"].extend(inputs["core"]["breaking_changes"])

    # Extract from infrastructure
    if "changes" in inputs.get("infrastructure", {}):
        synthesized["infrastructure_changes"] = inputs["infrastructure"]["changes"]
    if "deployment" in inputs.get("infrastructure", {}):
        synthesized["infrastructure_changes"].append(inputs["infrastructure"]["deployment"])

    result = {
        "success": True,
        "inputs_received": list(inputs.keys()),
        "synthesized_requirements": synthesized,
        "timestamp": datetime.now().isoformat()
    }

    write_output(output_file, result)
    return result


def generate_tasks(plan_file: str, output_file: str) -> Dict[str, Any]:
    """
    Generate detailed task breakdown from implementation plan.
    """
    try:
        with open(plan_file) as f:
            plan = json.load(f)
    except Exception as e:
        result = {"success": False, "error": f"Failed to read plan: {e}"}
        write_output(output_file, result)
        return result

    tasks = []
    task_id = 1

    phases = plan.get("phases", [])

    for phase_idx, phase in enumerate(phases, 1):
        phase_name = phase.get("name", f"Phase {phase_idx}")
        phase_tasks = phase.get("tasks", [])

        for task in phase_tasks:
            tasks.append({
                "id": f"TASK-{task_id:03d}",
                "phase": phase_idx,
                "phase_name": phase_name,
                "title": task.get("title", "Untitled task"),
                "description": task.get("description", ""),
                "type": task.get("type", "implementation"),
                "service": task.get("service", "unknown"),
                "estimated_hours": task.get("estimated_hours", 2),
                "dependencies": task.get("dependencies", []),
                "acceptance_criteria": task.get("acceptance_criteria", []),
                "labels": generate_labels(task)
            })
            task_id += 1

    # Calculate dependency graph
    dependency_order = calculate_dependency_order(tasks)

    result = {
        "success": True,
        "total_tasks": len(tasks),
        "tasks": tasks,
        "dependency_order": dependency_order,
        "estimated_total_hours": sum(t.get("estimated_hours", 0) for t in tasks),
        "phases_summary": [
            {
                "phase": p.get("name", f"Phase {i}"),
                "task_count": len(p.get("tasks", []))
            }
            for i, p in enumerate(phases, 1)
        ]
    }

    write_output(output_file, result)
    return result


def generate_labels(task: Dict) -> List[str]:
    """Generate labels for a task based on its properties."""
    labels = []

    task_type = task.get("type", "")
    if task_type:
        labels.append(f"type:{task_type}")

    service = task.get("service", "")
    if service:
        if "frontend" in service.lower():
            labels.append("frontend")
        elif "backend" in service.lower() or "api" in service.lower():
            labels.append("backend")

    if task.get("database_change"):
        labels.append("database")

    if task.get("breaking_change"):
        labels.append("breaking-change")

    return labels


def calculate_dependency_order(tasks: List[Dict]) -> List[str]:
    """Calculate execution order based on dependencies."""
    # Simple topological sort
    order = []
    remaining = {t["id"]: t for t in tasks}
    completed = set()

    max_iterations = len(tasks) * 2
    iteration = 0

    while remaining and iteration < max_iterations:
        iteration += 1

        # Find tasks with all dependencies met
        ready = []
        for task_id, task in remaining.items():
            deps = task.get("dependencies", [])
            if all(d in completed for d in deps):
                ready.append(task_id)

        if not ready:
            # Circular dependency or missing dependency
            ready = list(remaining.keys())[:1]  # Force progress

        for task_id in ready:
            order.append(task_id)
            completed.add(task_id)
            del remaining[task_id]

    return order


def write_plan(
    feature_name: str,
    plan_file: str,
    output_file: str
) -> Dict[str, Any]:
    """
    Write formatted plan document.
    """
    try:
        with open(plan_file) as f:
            plan = json.load(f)
    except Exception as e:
        result = {"success": False, "error": f"Failed to read plan: {e}"}
        write_output(output_file.replace('.md', '.json'), result)
        return result

    # Generate markdown
    md_content = generate_plan_markdown(feature_name, plan)

    # Write markdown file
    with open(output_file, 'w') as f:
        f.write(md_content)

    result = {
        "success": True,
        "output_file": output_file,
        "sections": ["overview", "decisions", "phases", "dependencies", "risks", "estimates"]
    }

    # Also write JSON result
    json_output = output_file.replace('.md', '-meta.json')
    write_output(json_output, result)

    return result


def generate_plan_markdown(feature_name: str, plan: Dict) -> str:
    """Generate markdown content for the plan."""
    lines = [
        f"# Feature Implementation Plan: {feature_name}",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
        "## Overview",
        "",
        plan.get("overview", "No overview provided."),
        "",
        "## Architectural Decisions",
        ""
    ]

    decisions = plan.get("decisions", [])
    if decisions:
        for decision in decisions:
            lines.append(f"### {decision.get('title', 'Decision')}")
            lines.append("")
            lines.append(f"**Decision:** {decision.get('decision', 'N/A')}")
            lines.append("")
            lines.append(f"**Rationale:** {decision.get('rationale', 'N/A')}")
            lines.append("")
    else:
        lines.append("No architectural decisions documented.")
        lines.append("")

    lines.append("## Implementation Phases")
    lines.append("")

    phases = plan.get("phases", [])
    for phase_idx, phase in enumerate(phases, 1):
        lines.append(f"### Phase {phase_idx}: {phase.get('name', 'Unnamed')}")
        lines.append("")

        for task in phase.get("tasks", []):
            lines.append(f"- [ ] **{task.get('title', 'Task')}**")
            if task.get("description"):
                lines.append(f"  - {task['description']}")
            if task.get("service"):
                lines.append(f"  - Service: `{task['service']}`")
            lines.append("")

    lines.append("## Dependencies")
    lines.append("")

    deps = plan.get("dependencies", [])
    if deps:
        for dep in deps:
            lines.append(f"- {dep}")
    else:
        lines.append("No external dependencies identified.")
    lines.append("")

    lines.append("## Risk Assessment")
    lines.append("")

    risks = plan.get("risks", [])
    if risks:
        for risk in risks:
            lines.append(f"- **{risk.get('risk', 'Risk')}**")
            lines.append(f"  - Impact: {risk.get('impact', 'Unknown')}")
            lines.append(f"  - Mitigation: {risk.get('mitigation', 'None specified')}")
            lines.append("")
    else:
        lines.append("No significant risks identified.")
    lines.append("")

    lines.append("## Estimated Effort")
    lines.append("")
    lines.append(f"- **Total Tasks:** {plan.get('total_tasks', 'N/A')}")
    lines.append(f"- **Estimated Hours:** {plan.get('estimated_hours', 'N/A')}")
    lines.append(f"- **Complexity:** {plan.get('complexity', 'N/A')}")
    lines.append("")

    return "\n".join(lines)


def export_tasks(
    plan_file: str,
    export_format: str,
    output_file: str
) -> Dict[str, Any]:
    """
    Export tasks in various formats for external systems.
    """
    try:
        with open(plan_file) as f:
            plan = json.load(f)
    except Exception as e:
        result = {"success": False, "error": f"Failed to read plan: {e}"}
        write_output(output_file, result)
        return result

    tasks = plan.get("tasks", [])

    if export_format == "github-issues":
        exported = export_github_issues(tasks)
    elif export_format == "jira":
        exported = export_jira(tasks)
    elif export_format == "linear":
        exported = export_linear(tasks)
    else:
        exported = tasks  # Raw format

    result = {
        "success": True,
        "format": export_format,
        "task_count": len(exported),
        "tasks": exported
    }

    write_output(output_file, result)
    return result


def export_github_issues(tasks: List[Dict]) -> List[Dict]:
    """Format tasks as GitHub issues."""
    issues = []
    for task in tasks:
        issues.append({
            "title": task.get("title", "Untitled"),
            "body": format_github_body(task),
            "labels": task.get("labels", []),
            "milestone": task.get("phase_name")
        })
    return issues


def format_github_body(task: Dict) -> str:
    """Format task as GitHub issue body."""
    lines = [
        "## Description",
        task.get("description", "No description"),
        "",
        "## Acceptance Criteria",
    ]

    for ac in task.get("acceptance_criteria", []):
        lines.append(f"- [ ] {ac}")

    if task.get("dependencies"):
        lines.append("")
        lines.append("## Dependencies")
        for dep in task["dependencies"]:
            lines.append(f"- {dep}")

    return "\n".join(lines)


def export_jira(tasks: List[Dict]) -> List[Dict]:
    """Format tasks as Jira issues."""
    issues = []
    for task in tasks:
        issues.append({
            "summary": task.get("title", "Untitled"),
            "description": task.get("description", ""),
            "issuetype": {"name": "Task"},
            "labels": task.get("labels", []),
            "timetracking": {
                "originalEstimate": f"{task.get('estimated_hours', 2)}h"
            }
        })
    return issues


def export_linear(tasks: List[Dict]) -> List[Dict]:
    """Format tasks as Linear issues."""
    issues = []
    for task in tasks:
        issues.append({
            "title": task.get("title", "Untitled"),
            "description": task.get("description", ""),
            "estimate": task.get("estimated_hours", 2),
            "labels": task.get("labels", [])
        })
    return issues


def write_output(filepath: str, data: Dict[str, Any]) -> None:
    """Write JSON output to file."""
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def main():
    if len(sys.argv) < 2:
        print("Usage: feature-analysis.py <command> [options]")
        print("Commands: discover, synthesize, generate-tasks, write-plan, export-tasks")
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

    if command == "discover":
        result = discover_affected_services(
            feature_name=args.get("feature", "unknown"),
            description=args.get("description", ""),
            repos_root=args.get("repos_root", "."),
            output_file=args.get("output", "/tmp/affected-services.json")
        )

    elif command == "synthesize":
        result = synthesize_inputs(
            master_input=args.get("master_input", ""),
            frontend_input=args.get("frontend_input", ""),
            backend_input=args.get("backend_input", ""),
            core_input=args.get("core_input", ""),
            infra_input=args.get("infra_input", ""),
            output_file=args.get("output", "/tmp/synthesized.json")
        )

    elif command == "generate-tasks":
        result = generate_tasks(
            plan_file=args.get("plan", ""),
            output_file=args.get("output", "/tmp/tasks.json")
        )

    elif command == "write-plan":
        result = write_plan(
            feature_name=args.get("feature", "unknown"),
            plan_file=args.get("plan", ""),
            output_file=args.get("output", "/tmp/plan.md")
        )

    elif command == "export-tasks":
        result = export_tasks(
            plan_file=args.get("plan", ""),
            export_format=args.get("format", "github-issues"),
            output_file=args.get("output", "/tmp/exported-tasks.json")
        )

    else:
        result = {"error": f"Unknown command: {command}"}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
