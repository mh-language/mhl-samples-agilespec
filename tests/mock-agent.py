#!/usr/bin/env python3
"""Offline CLI double; accepts the same -p PROMPT contract as the default CLI."""

import json
import pathlib
import sys

prompt = sys.argv[sys.argv.index("-p") + 1]
task = prompt.splitlines()[0].split(": ", 1)[1]
data = json.loads(
    next(
        line.removeprefix("INPUT_JSON: ")
        for line in prompt.splitlines()
        if line.startswith("INPUT_JSON: ")
    )
)
mode_file = pathlib.Path(".mock-mode")
mode = mode_file.read_text().strip() if mode_file.exists() else ""

if mode == "invalid-json":
    print("This is not JSON")
    sys.exit(0)

acceptance = "# Story\n## Normal Case\n- Deliver the feature.\n## Edge Cases\n- Reject invalid data.\n"

if task == "INCEPTION":
    result = {
        "files": {
            "backlog.md": "# Backlog\n1. [ ] Deliver the feature.\n2. [ ] Next feature.\n",
            "definition-of-done.md": "# Done\nTests, human review and approved consolidation.\n",
            "architecture.md": "# Architecture\nKeep modules independent.\n",
            "database.md": "# Database\nNot applicable.\n",
            "ui.md": "# UI\nNot applicable.\n",
        }
    }
elif task == "SPECIFICATION":
    files = {
        "acceptance.md": acceptance,
        "design.md": "# Design\nImplement src/feature.txt.\n",
    }
    existing = data["existing_story"]

    if data["ui_changes"] or existing.get("views.md"):
        files["views.md"] = "# Views\nA simple feature view.\n"

    if data["database_changes"] or existing.get("tables.md"):
        files["tables.md"] = "# Tables\nA feature table.\n"

    result = {"files": files}
elif task == "IMPLEMENTATION":
    pathlib.Path("src").mkdir(exist_ok=True)
    pathlib.Path("src/feature.txt").write_text("implemented\n")

    if mode == "mutate-spec":
        pathlib.Path("AgileSpec/project/architecture.md").write_text(
            "unauthorized edit"
        )

    result = {
        "status": "blocked" if mode == "blocked" else "ready",
        "summary": "Implemented and tested feature.",
        "manual_validation": "Open and inspect the feature.",
        "limitations": [],
        "pending_dod": [],
        "consolidation_context": "src/feature.txt",
    }
elif task == "CONSOLIDATION":
    files = {name: data["project"][name] for name in ("backlog.md", "architecture.md")}
    files["architecture.md"] += "\nFeature implemented in src/feature.txt.\n"

    if "views.md" in data["story"]:
        files["ui.md"] = data["project"]["ui.md"] + "\nFeature view.\n"

    if "tables.md" in data["story"]:
        files["database.md"] = data["project"]["database.md"] + "\nFeature table.\n"

    if mode == "premature-done":
        files["backlog.md"] = files["backlog.md"].replace("1. [ ]", "1. [x]")

    result = {
        "files": files,
        "discrepancies": ["code disagrees"] if mode == "discrepancy" else [],
        "pending_dod": ["missing security review"] if mode == "pending-dod" else [],
    }
else:
    raise ValueError(task)

print(json.dumps(result))
