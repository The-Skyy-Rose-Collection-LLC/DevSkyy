"""Google ADK workflows for mandatory SkyyRose visual asset verification.

The workflows orchestrate evidence collection and independent review. They do
not replace the deterministic gate in ``asset_gate.py`` and they cannot grant
approval by producing persuasive text. A release consumer must still execute
the gate and receive ``approved`` from a signed founder record.
"""

from __future__ import annotations

import logging
from enum import StrEnum
from pathlib import Path
from typing import Any

from skyyrose.elite_studio.platform.fidelity.asset_gate import (
    AssetVerificationRequest,
    verify_visual_asset,
)

logger = logging.getLogger(__name__)

try:
    from google.adk.agents import LlmAgent, SequentialAgent
    from google.adk.tools import FunctionTool

    ADK_VISUAL_WORKFLOW_AVAILABLE = True
except ImportError:
    ADK_VISUAL_WORKFLOW_AVAILABLE = False
    LlmAgent = None
    SequentialAgent = None
    FunctionTool = None


class VisualAssetWorkflowType(StrEnum):
    """Supported visual-asset ADK workflow entry points."""

    INTAKE = "visual_asset_intake"
    VERIFICATION = "visual_asset_verification"
    TRIPO_RELEASE = "tripo_release_candidate"


def run_visual_asset_gate(
    sku: str,
    model_path: str,
    reference_root: str,
    provenance_path: str,
    trust_manifest_path: str,
    approval_path: str = "",
    policy_attestation_path: str = "",
    report_root: str = "renders/fidelity-reports",
) -> dict[str, Any]:
    """ADK tool: execute the deterministic, fail-closed visual asset gate."""

    report = verify_visual_asset(
        AssetVerificationRequest(
            sku=sku,
            model_path=Path(model_path),
            reference_root=Path(reference_root),
            provenance_path=Path(provenance_path),
            trust_manifest_path=Path(trust_manifest_path),
            approval_path=Path(approval_path) if approval_path else None,
            policy_attestation_path=(
                Path(policy_attestation_path) if policy_attestation_path else None
            ),
            report_root=Path(report_root),
        )
    )
    return report.to_dict()


def _gate_tool() -> Any:
    return FunctionTool(run_visual_asset_gate)


_NON_BYPASSABLE_POLICY = (
    "The deterministic visual asset gate is the authority. Never infer product identity, "
    "never fill missing angles, never approve from prose, and never treat a generated or "
    "Tripo model as identical without the tool returning approved. Any tool error, missing "
    "reference, missing signature, score below threshold, or incomplete coverage is BLOCKED."
)


def create_visual_asset_intake_workflow() -> Any | None:
    """Collect exact-SKU provenance before any expensive render or API call."""

    if not ADK_VISUAL_WORKFLOW_AVAILABLE:
        return None
    intake = LlmAgent(
        name="visual_asset_provenance_intake",
        model="gemini-2.0-flash",
        instruction=(
            _NON_BYPASSABLE_POLICY
            + "\nParse the supplied request into sku, model_path, reference_root, "
            "provenance_path, trust_manifest_path, optional approval_path, "
            "policy_attestation_path, and report_root. "
            "Call run_visual_asset_gate exactly once. Return its JSON unchanged under "
            "the key visual_asset_intake. Do not call Tripo, Meshy, Blender, or any paid API.\n"
            "Request: {input_context}"
        ),
        tools=[_gate_tool()],
        description="Binds a candidate model to the exact SKU and approved references.",
        output_key="visual_asset_intake",
    )
    return SequentialAgent(
        name="visual_asset_intake_workflow",
        sub_agents=[intake],
        description="Fail-closed SKU/provenance intake before visual asset generation.",
    )


def create_visual_asset_verification_workflow() -> Any | None:
    """Run deterministic verification plus an independent ADK challenge review."""

    if not ADK_VISUAL_WORKFLOW_AVAILABLE:
        return None
    gate_runner = LlmAgent(
        name="visual_asset_gate_runner",
        model="gemini-2.0-flash",
        instruction=(
            _NON_BYPASSABLE_POLICY
            + "\nCall run_visual_asset_gate using the request in {input_context}. "
            "Return the tool JSON unchanged under visual_asset_gate."
        ),
        tools=[_gate_tool()],
        description="Executes the canonical visual comparison and release gate.",
        output_key="visual_asset_gate",
    )
    adversarial_review = LlmAgent(
        name="visual_asset_adversarial_reviewer",
        model="gemini-2.0-flash",
        instruction=(
            _NON_BYPASSABLE_POLICY
            + "\nIndependently re-run run_visual_asset_gate from the original request, then "
            "compare the returned evidence with the first result: {visual_asset_gate}. "
            "If the two results differ, return BLOCKED. A result is clean only when the "
            "tool itself returns approved. Return structured JSON with verdict, "
            "recommend_ship, and evidence.\nRequest: {input_context}"
        ),
        tools=[_gate_tool()],
        description="Independent skeptical re-check of visual identity evidence.",
        output_key="visual_asset_adversarial_review",
    )
    disposition = LlmAgent(
        name="visual_asset_release_disposition",
        model="gemini-2.0-flash",
        instruction=(
            _NON_BYPASSABLE_POLICY
            + "\nSynthesize the two tool-backed records below. Only emit APPROVED when both "
            "records say approved and contain complete canonical angle evidence plus a "
            "verified founder signature. Otherwise emit BLOCKED and list exact reasons. "
            "This stage does not modify files or authorize deployment.\n"
            "Gate record: {visual_asset_gate}\n"
            "Adversarial record: {visual_asset_adversarial_review}"
        ),
        description="Produces a release disposition without granting approval authority.",
        output_key="visual_asset_release_disposition",
    )
    return SequentialAgent(
        name="visual_asset_verification_workflow",
        sub_agents=[gate_runner, adversarial_review, disposition],
        description=(
            "Mandatory primary render verification, sequential independent challenge review, "
            "and disposition."
        ),
    )


def create_tripo_release_workflow() -> Any | None:
    """Verify a Tripo candidate without allowing generation to bypass identity QA."""

    if not ADK_VISUAL_WORKFLOW_AVAILABLE:
        return None
    tripo_intake = LlmAgent(
        name="tripo_candidate_intake",
        model="gemini-2.0-flash",
        instruction=(
            _NON_BYPASSABLE_POLICY
            + "\nTreat the Tripo output as untrusted. Confirm the exact SKU and approved "
            "reference set in the request, then pass the request unchanged to the next "
            "stage under tripo_candidate_context. Never publish or copy the model.\n"
            "Request: {input_context}"
        ),
        description="Receives an untrusted Tripo candidate for verification.",
        output_key="tripo_candidate_context",
    )
    verify = LlmAgent(
        name="tripo_candidate_visual_gate",
        model="gemini-2.0-flash",
        instruction=(
            _NON_BYPASSABLE_POLICY
            + "\nCall run_visual_asset_gate for the candidate in {tripo_candidate_context}. "
            "Return the tool record unchanged under tripo_visual_gate."
        ),
        tools=[_gate_tool()],
        description="Applies the same exact-product gate to Tripo output.",
        output_key="tripo_visual_gate",
    )
    return SequentialAgent(
        name="tripo_release_candidate_workflow",
        sub_agents=[tripo_intake, verify],
        description="Tripo candidate intake followed by mandatory exact-product verification.",
    )


def get_visual_asset_workflow(workflow_type: VisualAssetWorkflowType) -> Any | None:
    """Factory for the visual asset ADK workflow family."""

    factories = {
        VisualAssetWorkflowType.INTAKE: create_visual_asset_intake_workflow,
        VisualAssetWorkflowType.VERIFICATION: create_visual_asset_verification_workflow,
        VisualAssetWorkflowType.TRIPO_RELEASE: create_tripo_release_workflow,
    }
    try:
        return factories[workflow_type]()
    except KeyError as exc:
        raise ValueError(f"Unknown visual asset workflow: {workflow_type}") from exc


__all__ = [
    "ADK_VISUAL_WORKFLOW_AVAILABLE",
    "VisualAssetWorkflowType",
    "create_tripo_release_workflow",
    "create_visual_asset_intake_workflow",
    "create_visual_asset_verification_workflow",
    "get_visual_asset_workflow",
    "run_visual_asset_gate",
]
