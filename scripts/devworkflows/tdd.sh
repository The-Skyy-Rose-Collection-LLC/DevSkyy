#!/usr/bin/env bash
# TDD gate — RED / GREEN / coverage enforcement via pytest
# Usage:
#   tdd.sh                          # full suite must pass
#   tdd.sh --red  TESTS...          # tests MUST fail (RED phase, pre-impl)
#   tdd.sh --green TESTS...         # tests MUST pass (GREEN phase)
#   tdd.sh --cov  [N]               # full suite + coverage >= N (default 85)
#   tdd.sh -- <extra pytest args>   # passthrough (any mode, place last)
#
# Exit 0 = phase satisfied. Exit 1 = phase violated.
#
# pytest exit codes the gate relies on:
#   0 = all passed   1 = test failures   5 = no tests collected
#   2/3/4 = interrupt / internal / usage error (never a valid RED)

set -uo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

MODE="full"
COV_MIN=85
TARGETS=()
PASSTHRU=()

while [[ $# -gt 0 ]]; do
  case $1 in
    --red)   MODE="red";   shift; while [[ $# -gt 0 && "$1" != --* ]]; do TARGETS+=("$1"); shift; done ;;
    --green) MODE="green"; shift; while [[ $# -gt 0 && "$1" != --* ]]; do TARGETS+=("$1"); shift; done ;;
    --cov)   MODE="cov";   shift; if [[ $# -gt 0 && "$1" =~ ^[0-9]+$ ]]; then COV_MIN="$1"; shift; fi ;;
    --)      shift; PASSTHRU=("$@"); break ;;
    *)       TARGETS+=("$1"); shift ;;
  esac
done

PYTEST=(python3 -m pytest -q)
[[ ${#PASSTHRU[@]} -gt 0 ]] && PYTEST+=("${PASSTHRU[@]}")

# Run pytest with the collected targets, empty-array safe (bash 3 + set -u).
run_targets() {
  if [[ ${#TARGETS[@]} -gt 0 ]]; then
    "${PYTEST[@]}" "${TARGETS[@]}"
  else
    "${PYTEST[@]}"
  fi
}

echo ""
echo "┌────────────────────────────────────────┐"
echo "│           DEVWORKFLOW TDD              │"
echo "└────────────────────────────────────────┘"
echo ""

case $MODE in
  red)
    if [[ ${#TARGETS[@]} -eq 0 ]]; then
      echo "tdd --red: name the test file(s) that must fail. exit: 1"
      exit 1
    fi
    echo "RED phase — expecting FAILURE on: ${TARGETS[*]}"
    echo ""
    run_targets
    rc=$?
    echo ""
    case $rc in
      1) echo "RED confirmed — test fails as expected. Write the implementation now. exit: 0"; exit 0 ;;
      0) echo "RED violated — test PASSES with no implementation. The test asserts nothing, or the code already exists. exit: 1"; exit 1 ;;
      5) echo "RED invalid — pytest exit 5 (no tests collected). Write the failing test first. exit: 1"; exit 1 ;;
      *) echo "RED invalid — pytest exit $rc (collection/usage error, not a real failure). Fix the test harness. exit: 1"; exit 1 ;;
    esac
    ;;

  green)
    if [[ ${#TARGETS[@]} -eq 0 ]]; then
      echo "tdd --green: name the test file(s) that must pass. exit: 1"
      exit 1
    fi
    echo "GREEN phase — expecting PASS on: ${TARGETS[*]}"
    echo ""
    run_targets
    rc=$?
    echo ""
    if [[ $rc -eq 0 ]]; then
      echo "GREEN confirmed — all target tests pass. exit: 0"
      exit 0
    fi
    echo "GREEN violated — pytest exit $rc. Implementation incomplete. exit: 1"
    exit 1
    ;;

  cov)
    echo "Coverage gate — threshold ${COV_MIN}%"
    echo ""
    if [[ ${#TARGETS[@]} -gt 0 ]]; then
      "${PYTEST[@]}" --cov --cov-report=term-missing --cov-fail-under="$COV_MIN" "${TARGETS[@]}"
    else
      "${PYTEST[@]}" --cov --cov-report=term-missing --cov-fail-under="$COV_MIN"
    fi
    rc=$?
    echo ""
    if [[ $rc -eq 0 ]]; then
      echo "Coverage gate passed (>= ${COV_MIN}%). exit: 0"
      exit 0
    fi
    echo "Coverage gate failed (< ${COV_MIN}% or test failures, pytest exit $rc). exit: 1"
    exit 1
    ;;

  full)
    echo "Full suite gate"
    echo ""
    run_targets
    rc=$?
    echo ""
    if [[ $rc -eq 0 ]]; then
      echo "Suite passed. exit: 0"
      exit 0
    fi
    if [[ $rc -eq 5 ]]; then
      echo "No tests collected (pytest exit 5). exit: 1"
      exit 1
    fi
    echo "Suite failed (pytest exit $rc). exit: 1"
    exit 1
    ;;
esac
