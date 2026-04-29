"""Regression tests for VisionAuditAgent's raw-JSON parsing path.

These tests patch gemini_analyze_vision directly to exercise the
violation-building loop in VisionAuditAgent.audit() — the layer
that audit_filter tests never reach (they mock VisionAuditAgent
at the class level).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from skyyrose.elite_studio.agents.vision_audit_agent import VisionAuditAgent

_PATCH = "skyyrose.elite_studio.agents.vision_audit_agent.gemini_analyze_vision"
_DOSSIER = {"name": "Black Rose Crewneck"}


def _png(tmp_path):
    img = tmp_path / "render.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    return img


# ── Severity coercion ────────────────────────────────────────────────────────


def test_audit_coerces_unknown_severity_to_high(tmp_path):
    payload = {
        "success": True,
        "text": (
            '{"matches_dossier": false, "violations": ['
            '{"element": "mystery-badge", "region": "front-chest", "severity": "critical"}]}'
        ),
    }
    with patch(_PATCH, return_value=payload):
        result = VisionAuditAgent(model="test-model").audit(_png(tmp_path), _DOSSIER)
    assert len(result.violations) == 1
    assert result.violations[0].severity == "high"
    assert result.violations[0].is_blocking is True
    assert result.has_blocking_violations is True


def test_audit_coerces_empty_severity_to_high(tmp_path):
    payload = {
        "success": True,
        "text": (
            '{"matches_dossier": false, "violations": ['
            '{"element": "unknown-element", "region": "back-yoke", "severity": ""}]}'
        ),
    }
    with patch(_PATCH, return_value=payload):
        result = VisionAuditAgent(model="test-model").audit(_png(tmp_path), _DOSSIER)
    assert result.violations[0].severity == "high"
    assert result.violations[0].is_blocking is True


def test_audit_preserves_valid_severities(tmp_path):
    payload = {
        "success": True,
        "text": (
            '{"matches_dossier": false, "violations": ['
            '{"element": "a", "region": "r1", "severity": "low"},'
            '{"element": "b", "region": "r2", "severity": "medium"},'
            '{"element": "c", "region": "r3", "severity": "high"}]}'
        ),
    }
    with patch(_PATCH, return_value=payload):
        result = VisionAuditAgent(model="test-model").audit(_png(tmp_path), _DOSSIER)
    sevs = [v.severity for v in result.violations]
    assert sevs == ["low", "medium", "high"]


# ── Non-dict violation entries ───────────────────────────────────────────────


def test_audit_skips_non_dict_violation_entries(tmp_path):
    payload = {
        "success": True,
        "text": (
            '{"matches_dossier": false, "violations": ['
            '"unexpected-string",'
            '{"element": "logo", "region": "front-chest", "severity": "high"}]}'
        ),
    }
    with patch(_PATCH, return_value=payload):
        result = VisionAuditAgent(model="test-model").audit(_png(tmp_path), _DOSSIER)
    assert len(result.violations) == 1
    assert result.violations[0].element == "logo"
