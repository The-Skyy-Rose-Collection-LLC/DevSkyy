"""Source-level security remediation for SAST findings.

Companion to ``security/code_analysis.py`` (which *detects*) and the ``/code/fix``
endpoint (which *applies*). Applies SAFE, deterministic, line-targeted rewrites
for the small subset of security findings that can be auto-fixed WITHOUT semantic
understanding of the program:

    CWE-396  bare ``except:``   →  ``except Exception:``   (SEC011)
    CWE-489  ``DEBUG = True``   →  ``DEBUG = False``       (SEC012)

Everything else the scanner emits — SQL injection, ``eval``/``exec``, hardcoded
secrets, command injection, weak hashes, ``password ==`` — requires human
judgement and is reported as "manual review required". It is NEVER silently
skipped and NEVER falsely reported as "fixed". A regex "fix" for SQL injection
would be dangerous theatre; the honesty about what cannot be auto-fixed is the
point of this module.

Design (advisor-locked):
    * AST-CONFIRM is PRIMARY. The scanner is line-regex based and string/comment
      blind, so a ``except:`` inside a triple-quoted string or a ``# DEBUG = True``
      comment can be flagged. Before touching anything, this module parses the file
      and only treats a target line as eligible if it is a REAL AST node of that
      kind — an ``ast.ExceptHandler`` with no exception type, or an ``ast.Assign``
      whose target is ``DEBUG`` and value is the literal ``True``. This inherently
      excludes matches inside strings/comments and variant symbols (``MY_DEBUG``),
      which regex-on-the-line cannot. A regex hit on a non-eligible line is a
      failure ("manual review required"), never a fake success.
    * The regex (``vulnerable`` + ``repl``) only performs the textual edit on an
      already-AST-confirmed line, and a post-edit pattern-confirm asserts the
      vulnerable token is actually gone.
    * ``ast.parse`` of the EDITED file is a SECONDARY backstop — broken edits are
      discarded and reported failed. (A file that does not parse at all up front
      yields a failure for every target: we cannot confirm AST targets in it.)
    * IDEMPOTENT. A line that is the AST construct but not in its vulnerable form
      (e.g. an already-fixed ``except Exception:``) is reported success / no-op,
      distinct from a line that is not the construct at all (failure / manual).
    * Edits to one file are staged in memory and written ONCE (atomically).

Returns the shared ``HealingResult`` (one per attempted target) so the endpoint
maps security outcomes through the same response shape as the tool healers.
"""

from __future__ import annotations

import ast
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from agents.coding_doctor_agent import HealingAction, HealingResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SecurityTarget:
    """One security finding to attempt to remediate.

    ``line_number`` is 1-indexed, exactly as emitted by CodeSecurityAnalyzer.
    """

    cwe_id: str
    line_number: int


def _bare_except_nodes(tree: ast.AST) -> tuple[set[int], set[int]]:
    """(vulnerable lines, all-construct lines) for bare ``except:`` handlers."""
    vuln: set[int] = set()
    family: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            family.add(node.lineno)
            if node.type is None:  # bare ``except:`` — the vulnerable form
                vuln.add(node.lineno)
    return vuln, family


def _debug_true_nodes(tree: ast.AST) -> tuple[set[int], set[int]]:
    """(vulnerable lines, all-construct lines) for ``DEBUG = <literal>`` assigns."""
    vuln: set[int] = set()
    family: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Constant):
            continue
        for tgt in node.targets:
            name = (
                tgt.id
                if isinstance(tgt, ast.Name)
                else tgt.attr if isinstance(tgt, ast.Attribute) else None
            )
            if name == "DEBUG":
                family.add(node.lineno)
                if node.value.value is True:  # literal True only (bool is its own singleton)
                    vuln.add(node.lineno)
    return vuln, family


@dataclass(frozen=True)
class _Rule:
    """A safe, line-local remediation keyed by CWE id.

    ``collect`` returns (vulnerable_lines, construct_lines) from a parsed AST —
    this is the primary eligibility gate. ``vulnerable``/``repl`` perform the
    textual edit on an AST-confirmed line.
    """

    cwe_id: str
    name: str
    collect: Callable[[ast.AST], tuple[set[int], set[int]]]
    vulnerable: re.Pattern[str]
    repl: str


# Curated set of findings that are safe to rewrite by rule. Adding a rule here is
# a deliberate act: the fix must be line-local, behaviour-correcting, AST-confirmable,
# and provable via pattern-confirm. md5→sha256, ``usedforsecurity=False``, and
# ``password ==``→hmac were considered and REJECTED — they change external behaviour,
# assert intent that cannot be verified, or are not line-local. See module docstring.
_RULES: dict[str, _Rule] = {
    "CWE-396": _Rule(
        cwe_id="CWE-396",
        name="bare except",
        collect=_bare_except_nodes,
        vulnerable=re.compile(r"^(\s*)except\s*:"),
        repl=r"\1except Exception:",
    ),
    "CWE-489": _Rule(
        cwe_id="CWE-489",
        name="debug mode enabled",
        collect=_debug_true_nodes,
        vulnerable=re.compile(r"(\bDEBUG\s*=\s*)True\b"),
        repl=r"\1False",
    ),
}


class SecurityRemediator:
    """Applies safe, deterministic security fixes to source files.

    Driven off-thread by the ``/code/fix`` endpoint exactly like SelfHealingEngine,
    but unlike the tool healers it edits specific lines, so it MUST run before any
    formatter that would reflow the file and invalidate scan line numbers.
    """

    SUPPORTED_CWES: frozenset[str] = frozenset(_RULES)

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    @staticmethod
    def supports(cwe_id: str | None) -> bool:
        """True if a safe automated remediation exists for this CWE."""
        return cwe_id in _RULES

    def remediate_file(
        self, rel_path: str, targets: list[SecurityTarget], dry_run: bool
    ) -> list[HealingResult]:
        """Attempt every target against one file; write once. One result per target."""
        abs_path = (self.repo_root / rel_path).resolve()
        try:
            original = abs_path.read_text(encoding="utf-8")
        except Exception as exc:  # unreadable file → every target fails honestly
            return [self._fail(rel_path, f"cannot read file: {exc}") for _ in targets]

        # PRIMARY gate is AST-based: a file that does not parse cannot have its
        # targets confirmed as real nodes, so every target fails (not faked).
        try:
            tree = ast.parse(original)
        except SyntaxError as exc:
            return [
                self._fail(rel_path, f"file does not parse, cannot confirm target: {exc}")
                for _ in targets
            ]

        lines = original.split("\n")
        node_cache: dict[str, tuple[set[int], set[int]]] = {}
        results: list[HealingResult] = []
        # staged edits: (rule, line_index, before, after) applied only if all parse
        pending: list[tuple[_Rule, int, str, str]] = []

        for target in targets:
            rule = _RULES.get(target.cwe_id)
            if rule is None:
                results.append(
                    self._fail(
                        rel_path,
                        f"{target.cwe_id}: no safe automated remediation; manual review required",
                    )
                )
                continue

            idx = target.line_number - 1
            if idx < 0 or idx >= len(lines):
                results.append(
                    self._fail(rel_path, f"line {target.line_number} out of range; stale scan?")
                )
                continue

            if target.cwe_id not in node_cache:
                node_cache[target.cwe_id] = rule.collect(tree)
            vuln_lines, construct_lines = node_cache[target.cwe_id]

            if target.line_number in vuln_lines:
                line = lines[idx]
                new_line = rule.vulnerable.sub(rule.repl, line)
                # post-edit pattern-confirm: the vulnerable token must be gone
                if rule.vulnerable.search(new_line):
                    results.append(
                        self._fail(
                            rel_path,
                            f"line {target.line_number}: remediation did not clear the "
                            f"{rule.name} pattern; manual review required",
                        )
                    )
                    continue
                pending.append((rule, idx, line, new_line))
            elif target.line_number in construct_lines:
                # the construct, but not its vulnerable form → already remediated
                results.append(
                    self._ok(
                        rel_path,
                        [
                            f"line {target.line_number}: already remediated / not in "
                            f"vulnerable form ({rule.name})"
                        ],
                    )
                )
            else:
                # NOT a real AST node of this kind on that line: a match inside a
                # string/comment, a variant symbol (MY_DEBUG), or a stale line number.
                results.append(
                    self._fail(
                        rel_path,
                        f"line {target.line_number} does not match a {rule.name} statement "
                        f"(string/comment/variant or stale line); manual review required",
                    )
                )

        if not pending:
            return results

        new_lines = list(lines)
        for _, idx, _, new_line in pending:
            new_lines[idx] = new_line
        new_content = "\n".join(new_lines)

        # SECONDARY backstop: never write Python that does not parse.
        try:
            ast.parse(new_content)
        except SyntaxError as exc:
            for rule, _, _, _ in pending:
                results.append(
                    self._fail(rel_path, f"edit produced invalid syntax, reverted: {exc}")
                )
            return results

        if not dry_run:
            try:
                tmp = abs_path.with_suffix(abs_path.suffix + ".sectmp")
                tmp.write_text(new_content, encoding="utf-8")
                tmp.replace(abs_path)  # atomic on POSIX
            except Exception as exc:
                for rule, _, _, _ in pending:
                    results.append(self._fail(rel_path, f"write failed: {exc}"))
                return results

        verb = "would fix" if dry_run else "fixed"
        for rule, idx, before, after in pending:
            results.append(
                self._ok(
                    rel_path,
                    [f"line {idx + 1}: {verb} {rule.name}: {before.strip()} -> {after.strip()}"],
                )
            )
        return results

    @staticmethod
    def _ok(rel_path: str, changes: list[str]) -> HealingResult:
        return HealingResult(
            action=HealingAction.FIX_SECURITY,
            file_path=rel_path,
            success=True,
            changes_made=changes,
            error=None,
        )

    @staticmethod
    def _fail(rel_path: str, error: str) -> HealingResult:
        return HealingResult(
            action=HealingAction.FIX_SECURITY,
            file_path=rel_path,
            success=False,
            changes_made=[],
            error=error,
        )
