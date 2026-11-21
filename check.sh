#!/bin/sh
set -eu

workflow_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
check_tmp=$(mktemp -d "${TMPDIR:-/tmp}/agilespec-mhl-check.XXXXXX")

trap 'rm -rf "$check_tmp"' 0
trap 'exit 1' HUP INT TERM

cd "$check_tmp"

export AGILESPEC_TEST_MODE=offline
export AGILESPEC_SPEC_CMD="$workflow_dir/tests/mock-agent.py"
export AGILESPEC_CODE_CMD="$workflow_dir/tests/mock-agent.py"

mhl lint "$workflow_dir"
mhl test "$workflow_dir"

mhl run "$workflow_dir/inception.mh" --dry-run \
  --input project_dir=/tmp/example \
  --input 'brief=Example backlog'

mhl run "$workflow_dir/story.mh" --dry-run \
  --input project_dir=/tmp/example \
  --input story_id=1 \
  --input 'verify_command=["python3","-m","pytest"]'

python3 "$workflow_dir/tests/resume_test.py"
python3 "$workflow_dir/tests/cli_test.py"
