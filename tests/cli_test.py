#!/usr/bin/env python3
"""Drive the `agilespec` CLI end to end with the offline agent double.

Covers the scripted commands (approve, revise, reject, decide) and the guided
`next`, answered through stdin.
"""

import json
import os
from pathlib import Path
import subprocess
import tempfile

WORKFLOW_DIR = Path(__file__).resolve().parents[1]
CLI = str(WORKFLOW_DIR / "agilespec")
MOCK = str(WORKFLOW_DIR / "tests/mock-agent.py")


def cli(project, *args, stdin="", fails=False):
    env = dict(os.environ, AGILESPEC_SPEC_CMD=MOCK, AGILESPEC_CODE_CMD=MOCK, AGILESPEC_PROJECT=str(project), NO_COLOR="1")
    proc = subprocess.run([CLI, *args], env=env, input=stdin, text=True, capture_output=True, timeout=60)
    assert (proc.returncode != 0) == fails, (args, proc.returncode, proc.stdout, proc.stderr)
    return proc.stdout + proc.stderr


def sessions(project):
    return json.loads(cli(project, "status", "--json"))


def last(project, name):
    return json.loads((project / ".agilespec-mhl/cli" / f"{name}.json").read_text())


def backlog(project):
    return (project / "AgileSpec/project/backlog.md").read_text()


with tempfile.TemporaryDirectory(prefix="agilespec-cli-") as tmp:
    project = Path(tmp)

    assert "Nenhuma sessão" in cli(project, "status")
    assert "Nenhuma sessão aguardando" in cli(project, "next", fails=True)

    # Inception: pause, then approve.
    out = cli(project, "inception", "--brief", "One feature; a second feature next")
    assert "Aprovar a iniciação" in out and "project-proposal.json" in out, out
    assert sessions(project)["inception"]["status"] == "paused"
    assert "aceita correção" in cli(project, "revise", "x", fails=True)
    cli(project, "approve")
    assert sessions(project)["inception"]["status"] == "done"
    assert "1. [ ]" in backlog(project)

    # The test command is the Implementation stage's input: the first story
    # starts without it, and the run asks for it on entering Implementation.
    out = cli(project, "story", "1", "--draft")
    assert "Aprovar a especificação" in out, out
    assert sessions(project)["story-1"]["status"] == "paused"
    assert "em andamento" in cli(project, "story", "1", fails=True)

    # Guided: ask for another spec (an empty feedback is asked again), approve
    # it; the run then asks for the test command — leave it paused there.
    out = cli(project, "next", stdin="2\n\nMais casos de borda\n1\nq\n")
    assert "Informar os inputs da fase Implementation" in out and "Comando de testes" in out, out
    assert "continua pausada" in out, out
    state = last(project, "story-1")
    assert state["awaiting_inputs"]["inputs"] == ["verify_command"], state
    assert state["vars"]["spec_round"] == 2 and state["vars"]["attempt"] == 0, state["vars"]
    assert "aguardando inputs: Implementation (verify_command)" in cli(project, "status")

    # A decision does not answer it; giving nothing, with no default, is refused.
    assert "agilespec input" in cli(project, "approve", fails=True)
    assert "Falta informar verify_command" in cli(project, "input", fails=True)
    assert "não pede" in cli(project, "input", "story_id=3", fails=True)

    # Scripted: only that input is sent, and the project remembers it.
    out = cli(project, "input", "verify_command=python3 -c pass")
    assert "Revisar a implementação" in out, out
    assert "Testes: python3 -c pass" in cli(project, "status")
    assert sessions(project)["story-1"]["inputs"]["verify_command"] == ["python3", "-c", "pass"]

    # Guided again: ask for a code fix, then leave the session paused.
    out = cli(project, "next", stdin="2\nCorrigir a borda\nn\nq\n")
    assert "continua pausada" in out, out
    state = last(project, "story-1")
    assert state["awaiting"]["step"] == "ReviewImplementation", state["awaiting"]
    assert state["vars"]["spec_round"] == 2 and state["vars"]["attempt"] == 2, state["vars"]
    assert "Tentativa: 2 de 3" in cli(project, "show")

    # A decision mhl refuses leaves the session at the same pause.
    assert "Nope" in cli(project, "decide", '{"action": "Nope"}', fails=True)
    assert sessions(project)["story-1"]["status"] == "paused"

    # Consolidation needs the Definition of Done confirmed.
    cli(project, "approve")
    assert last(project, "story-1")["awaiting"]["step"] == "ApproveConsolidation"
    assert "--dod" in cli(project, "approve", fails=True)
    assert "concluída" in cli(project, "approve", "--dod")
    assert sessions(project)["story-1"]["status"] == "done"
    assert "1. [x]" in backlog(project) and "2. [ ]" in backlog(project)

    # A spec round cannot be rejected; a reviewed implementation can. The
    # remembered test command goes up front: nothing waits for it.
    cli(project, "story", "2", "--draft")
    assert sessions(project)["story-2"]["inputs"]["verify_command"] == ["python3", "-c", "pass"]
    assert "não aceita rejeição" in cli(project, "reject", fails=True)
    cli(project, "approve")
    out = cli(project, "next", stdin="3\ns\n")
    assert "rejeitada" in out, out
    assert sessions(project)["story-2"]["status"] == "rejected"
    assert "2. [ ]" in backlog(project)

    # A story again after it ended gets a session of its own.
    cli(project, "story", "2", "--draft")
    assert sessions(project)["story-2-2"]["status"] == "paused"
    assert "mais de uma" not in cli(project, "show")

    # A failed step is recorded; with two sessions open, the session must be named.
    out = cli(project, "story", "9")
    assert "falhou em LoadContext" in out, out
    assert sessions(project)["story-9"]["status"] == "failed"
    assert "-s <sessão>" in cli(project, "next", fails=True)

print("CLI: inception, guided and scripted decisions and stage inputs, refused decisions, DoD confirmation, rejection and failures passed.")
