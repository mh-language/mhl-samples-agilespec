#!/usr/bin/env python3
"""Exercise actual on-disk checkpoints; Name.run() cannot test --resume.

The human gates are typed (`pause(..., decision: T)`): each resume below
answers the gate the run waits at with `--decision '<json>'`.
"""

import json
import os
from pathlib import Path
import subprocess
import tempfile

WORKFLOW_DIR = Path(__file__).resolve().parents[1]
MOCK = str(WORKFLOW_DIR / "tests/mock-agent.py")
ENV = dict(os.environ, AGILESPEC_SPEC_CMD=MOCK, AGILESPEC_CODE_CMD=MOCK)


def run(repo, file, session, resume=False, expect_failure=False, decision=None, from_stage=None, **inputs):
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

    if decision is not None:
        argv.extend(["--decision", json.dumps(decision)])

    if from_stage is not None:
        argv.extend(["--from", from_stage])

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


def awaiting_inputs(result, stage, *inputs):
    assert result.get("paused") is True, result
    assert result["awaiting_inputs"]["stage"] == stage, result
    assert result["awaiting_inputs"]["inputs"] == list(inputs), result
    assert "awaiting" not in result, result


def paused(result, step):
    assert result.get("paused") is True, result
    assert result["executed"][-1] == step, result
    assert result["awaiting"]["step"] == step, result


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
    assert first["awaiting"]["type"] == "bool", first
    assert not (repo / "AgileSpec/project").exists()

    approved = run(repo, "inception.mh", "inception", resume=True, decision=True)
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
        decision={"approved": True},
        expect_failure=True,
    )
    (repo / ".mock-mode").unlink()
    implemented = run(repo, "story.mh", "story1", resume=True)
    paused(implemented, "ReviewImplementation")
    assert implemented["vars"]["attempt"] == 1
    assert "StartAttempt" not in implemented["executed"], implemented

    # A decision of another gate's shape is refused before anything runs.
    wrong = run(
        repo, "story.mh", "story1", resume=True, decision={"approved": True}, expect_failure=True
    )
    assert "invalid_decision" in wrong, wrong

    # A specification defect requires a fresh human approval, before more coding.
    revised = run(
        repo,
        "story.mh",
        "story1",
        resume=True,
        decision={
            "action": "Revise",
            "feedback": "Clarify invalid input handling",
            "revise_specs": True,
        },
    )
    paused(revised, "ApproveSpecification")
    assert revised["vars"]["spec_round"] == 2
    assert revised["vars"]["attempt"] == 1

    second = run(repo, "story.mh", "story1", resume=True, decision={"approved": True})
    paused(second, "ReviewImplementation")
    assert second["vars"]["attempt"] == 2
    assert "1. [ ]" in backlog(repo)

    consolidation = run(
        repo, "story.mh", "story1", resume=True, decision={"action": "Approve"}
    )
    paused(consolidation, "ApproveConsolidation")
    assert "1. [ ]" in backlog(repo)
    assert "Feature view" not in (repo / "AgileSpec/project/ui.md").read_text()

    # A plain resume never approves: the gate asks again.
    still = run(repo, "story.mh", "story1", resume=True)
    paused(still, "ApproveConsolidation")

    # Approval without confirming the Definition of Done asks again, saying why.
    unconfirmed = run(
        repo, "story.mh", "story1", resume=True, decision={"action": "Approve"}
    )
    paused(unconfirmed, "ApproveConsolidation")
    assert "dod_confirmed" in unconfirmed["pause_reason"], unconfirmed

    # Redo only the consolidation phase: a new proposal, same attempt.
    redone = run(repo, "story.mh", "story1", resume=True, from_stage="Consolidation")
    paused(redone, "ApproveConsolidation")
    assert redone["executed"][0] == "DraftConsolidation", redone
    assert redone["vars"]["attempt"] == 2

    done = run(
        repo,
        "story.mh",
        "story1",
        resume=True,
        decision={"action": "Approve", "dod_confirmed": True},
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
        expect_failure=True,
    )
    assert "already complete" in failure, failure

    # Each phase asks for its own inputs: story 2 starts with the story's only
    # (plus a Specification option, given up front), and the test command is
    # asked for on entering Implementation, once the specs are approved.
    story2 = run(
        repo,
        "story.mh",
        "story2",
        project_dir=str(repo),
        story_id="2",
        specification_mode="Draft",
    )
    paused(story2, "ApproveSpecification")

    specs = run(repo, "story.mh", "story2", resume=True, decision={"approved": True})
    awaiting_inputs(specs, "Implementation", "verify_command")
    assert specs["executed"][-1] == "PublishStorySpecs", specs
    assert (repo / "AgileSpec/stories/story2/acceptance.md").exists()

    # Resuming without it is refused before anything runs; the run stays paused.
    missing = run(repo, "story.mh", "story2", resume=True, expect_failure=True)
    assert "invalid_inputs" in missing and '"stage": "Implementation"' in missing, missing

    # A decision does not answer an input gate either.
    decided = run(
        repo, "story.mh", "story2", resume=True, decision={"action": "Approve"}, expect_failure=True
    )
    assert "invalid_decision" in decided, decided

    # Given only that input, the phase runs up to the human code review.
    coded = run(repo, "story.mh", "story2", resume=True, verify_command=command)
    paused(coded, "ReviewImplementation")
    assert coded["executed"][0] == "StartAttempt", coded
    assert coded["vars"]["attempt"] == 1
    assert "2. [ ]" in backlog(repo)

print(
    "CLI integration: inception + story pause/resume with typed decisions, specification rework, "
    "refused decisions, redoing a stage, consolidation and completion, "
    "and a stage asking for its own inputs passed."
)
