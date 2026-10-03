#!/usr/bin/env bash
set -euo pipefail

# Pre-validate a machine-generated main commit under the same required check
# used by protected pull requests, then push the exact checked SHA to main.
# No bypass token or force push is used.
#
# Usage:
#   GH_TOKEN="${{ github.token }}" scripts/push-main-with-check-all.sh [main]

target_branch="${1:-main}"
workflow_file="${VELVET_CHECK_WORKFLOW:-check-all.yml}"
repo="${GITHUB_REPOSITORY:-}"
run_id="${GITHUB_RUN_ID:-local}"
run_attempt="${GITHUB_RUN_ATTEMPT:-1}"
max_attempts="${VELVET_MACHINE_PUSH_ATTEMPTS:-2}"

if [[ "$target_branch" != "main" ]]; then
  echo "::error::prechecked machine push is restricted to main"
  exit 2
fi
if [[ -z "$repo" ]]; then
  echo "::error::GITHUB_REPOSITORY is required"
  exit 2
fi
if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "::error::GH_TOKEN is required"
  exit 2
fi
if ! command -v gh >/dev/null 2>&1; then
  echo "::error::gh CLI is required"
  exit 2
fi

stage_branch=""
cleanup_stage() {
  if [[ -n "$stage_branch" ]]; then
    git push origin --delete "$stage_branch" >/dev/null 2>&1 || true
    stage_branch=""
  fi
}
trap cleanup_stage EXIT

for ((attempt=1; attempt<=max_attempts; attempt++)); do
  cleanup_stage
  git fetch origin "$target_branch"

  if ! git rebase "origin/$target_branch"; then
    git rebase --abort || true
    echo "::error::machine writer could not rebase onto current $target_branch"
    exit 1
  fi

  head_sha="$(git rev-parse HEAD)"
  stage_branch="machine-check/${run_id}-${run_attempt}-${attempt}"

  echo "MACHINE_PRECHECK staging=$stage_branch head=$head_sha attempt=$attempt/$max_attempts"
  git push origin "HEAD:refs/heads/$stage_branch"

  gh workflow run "$workflow_file" --repo "$repo" --ref "$stage_branch"

  check_run_id=""
  for _ in {1..30}; do
    check_run_id="$(
      gh run list         --repo "$repo"         --workflow "$workflow_file"         --branch "$stage_branch"         --event workflow_dispatch         --limit 5         --json databaseId,headSha         --jq ".[] | select(.headSha == \"$head_sha\") | .databaseId"         | head -n 1
    )"
    if [[ -n "$check_run_id" ]]; then
      break
    fi
    sleep 2
  done

  if [[ -z "$check_run_id" ]]; then
    echo "::error::no workflow_dispatch check-all run appeared for $head_sha"
    exit 1
  fi

  echo "MACHINE_PRECHECK run_id=$check_run_id"
  gh run watch "$check_run_id" --repo "$repo" --exit-status

  observed="$(
    gh run view "$check_run_id" --repo "$repo"       --json headSha,conclusion       --jq '.headSha + " " + (.conclusion // "")'
  )"
  if [[ "$observed" != "$head_sha success" ]]; then
    echo "::error::precheck run did not finish success on exact head: $observed"
    exit 1
  fi

  check_count="$(
    gh api "repos/$repo/commits/$head_sha/check-runs"       --jq '[.check_runs[] | select(.name == "check-all" and .conclusion == "success" and .app.slug == "github-actions")] | length'
  )"
  if [[ "$check_count" -lt 1 ]]; then
    echo "::error::exact head lacks successful GitHub Actions check-all"
    exit 1
  fi

  status_count="$(
    gh api "repos/$repo/commits/$head_sha/status" \
      --jq '[.statuses[] | select(.context == "check-all" and .state == "success")] | length'
  )"
  if [[ "$status_count" -lt 1 ]]; then
    echo "::error::exact head lacks verified check-all commit status for branch protection"
    exit 1
  fi

  # A concurrent main update invalidates the checked ancestry. Rebase and
  # dispatch a new exact-SHA check rather than reusing stale evidence.
  git fetch origin "$target_branch"
  if ! git merge-base --is-ancestor "origin/$target_branch" "$head_sha"; then
    echo "::notice::$target_branch advanced during precheck; retrying on fresh base"
    continue
  fi

  if git push origin "HEAD:refs/heads/$target_branch"; then
    echo "MACHINE_PRECHECK_PUSH_OK branch=$target_branch head=$head_sha check_run=$check_run_id"
    cleanup_stage
    exit 0
  fi

  echo "::notice::push raced or protection rejected the checked SHA; retrying"
done

echo "::error::machine writer exhausted $max_attempts prechecked push attempts"
exit 1
