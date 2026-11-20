#!/usr/bin/env python3
"""Exercise actual on-disk checkpoints; Name.run() cannot test --resume."""

import json
import os
from pathlib import Path
import subprocess
import tempfile

WORKFLOW_DIR = Path(__file__).resolve().parents[1]
MOCK = str(WORKFLOW_DIR / "tests/mock-agent.py")
ENV = dict(os.environ, AGILESPEC_SPEC_CMD=MOCK, AGILESPEC_CODE_CMD=MOCK)


def run(repo, file, session, resume=False, expect_failure=False, **inputs):
    argv = [
        "mhl",
        "run",
        str(WORKFLOW_DIR / file),
        "--session",
        session,
        "--format",
        "json",
    ]

    if resume:
        argv.append("--resume")

    for key, value in inputs.items():
        value = json.dumps(value) if not isinstance(value, str) else value
        argv.extend(["--input", f"{key}={value}"])

    proc = subprocess.run(
        argv, cwd=repo, env=ENV, text=True, capture_output=True, timeout=45
    )

    assert (proc.returncode != 0) == expect_failure, (
        proc.returncode,
        proc.stdout,
        proc.stderr,
    )

    # Runtime emits JSON to stderr on a workflow failure in some versions.
    if expect_failure:
        return proc.stdout + proc.stderr

    return json.loads(proc.stdout)


def paused(result, step):
    assert result.get("paused") is True, result
    assert result["executed"][-1] == step, result


def backlog(repo):
    return (repo / "AgileSpec/project/backlog.md").read_text()


with tempfile.TemporaryDirectory(prefix="agilespec-mhl-resume-") as tmp:
    repo = Path(tmp)

    first = run(
        repo,
        "inception.mh",
        "inception",
        project_dir=str(repo),
        brief="One feature; a second feature next",
    )
    paused(first, "ApproveInception")
    assert not (repo / "AgileSpec/project").exists()

    approved = run(repo, "inception.mh", "inception", resume=True, approved=True)
    assert approved["ok"] and not approved.get("paused"), approved
    assert "DraftInception" not in approved["executed"], approved
    assert "1. [ ]" in backlog(repo)

    command = [
        "python3",
        "-c",
        "from pathlib import Path; assert Path('src/feature.txt').read_text().strip() == 'implemented'",
    ]
    story = run(
        repo,
        "story.mh",
        "story1",
        project_dir=str(repo),
        story_id="1",
        verify_command=command,
        specification_mode="Draft",
        ui_changes=True,
        database_changes=True,
    )
    paused(story, "ApproveSpecification")
    assert not (repo / "AgileSpec/stories/story1/acceptance.md").exists()

    # A failed agent response resumes Implement without counting another attempt.
    (repo / ".mock-mode").write_text("invalid-json")
    run(
        repo,
        "story.mh",
        "story1",
        resume=True,
        specs_approved_round=1,
        expect_failure=True,
    )
    (repo / ".mock-mode").unlink()
    implemented = run(repo, "story.mh", "story1", resume=True)
    paused(implemented, "ReviewImplementation")
    assert implemented["vars"]["attempt"] == 1
    assert "StartAttempt" not in implemented["executed"], implemented

    # A specification defect requires a fresh human approval, before more coding.
    revised = run(
        repo,
        "story.mh",
        "story1",
        resume=True,
        review_action="Revise",
        review_round=1,
        feedback="Clarify invalid input handling",
        revise_specs=True,
    )
    paused(revised, "ApproveSpecification")
    assert revised["vars"]["spec_round"] == 2
    assert revised["vars"]["attempt"] == 1

    second = run(repo, "story.mh", "story1", resume=True, specs_approved_round=2)
    paused(second, "ReviewImplementation")
    assert second["vars"]["attempt"] == 2
    assert "1. [ ]" in backlog(repo)

    consolidation = run(
        repo, "story.mh", "story1", resume=True, review_action="Approve", review_round=2
    )
    paused(consolidation, "ApproveConsolidation")
    assert "1. [ ]" in backlog(repo)
    assert "Feature view" not in (repo / "AgileSpec/project/ui.md").read_text()

    # Old decisions cannot approve a newer implementation/consolidation.
    stale = run(
        repo,
        "story.mh",
        "story1",
        resume=True,
        consolidation_approved_round=1,
        dod_confirmed_round=1,
    )
    paused(stale, "ApproveConsolidation")

    done = run(
        repo,
        "story.mh",
        "story1",
        resume=True,
        consolidation_approved_round=2,
        dod_confirmed_round=2,
    )
    assert done["ok"] and not done.get("paused"), done
    assert done["vars"]["status"] == "done", done
    assert done["vars"]["attempts"] == 2
    assert "Implement" not in done["executed"], done
    assert "1. [x]" in backlog(repo) and "2. [ ]" in backlog(repo)
    assert (repo / "AgileSpec/stories/story1/tables.md").exists()
    assert "Feature table" in (repo / "AgileSpec/project/database.md").read_text()

    # Reopening a completed story is refused before any agent call.
    failure = run(
        repo,
        "story.mh",
        "reopen",
        project_dir=str(repo),
        story_id="1",
        verify_command=command,
        expect_failure=True,
    )
    assert "already complete" in failure, failure

print(
    "CLI integration: inception + story pause/resume, specification rework, stale approvals, consolidation and completion passed."
)
