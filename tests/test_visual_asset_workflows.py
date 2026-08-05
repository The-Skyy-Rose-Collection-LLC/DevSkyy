from adk.visual_asset_workflows import (
    ADK_VISUAL_WORKFLOW_AVAILABLE,
    VisualAssetWorkflowType,
    create_tripo_release_workflow,
    create_visual_asset_intake_workflow,
    create_visual_asset_verification_workflow,
    get_visual_asset_workflow,
)


def test_workflow_factories_are_available():
    assert ADK_VISUAL_WORKFLOW_AVAILABLE is True
    assert create_visual_asset_intake_workflow() is not None
    assert create_visual_asset_verification_workflow() is not None
    assert create_tripo_release_workflow() is not None


def test_workflow_names_and_types_are_distinct():
    assert len(set(VisualAssetWorkflowType)) == 3
    assert get_visual_asset_workflow(VisualAssetWorkflowType.INTAKE).name == (
        "visual_asset_intake_workflow"
    )
    assert get_visual_asset_workflow(VisualAssetWorkflowType.VERIFICATION).name == (
        "visual_asset_verification_workflow"
    )
    assert get_visual_asset_workflow(VisualAssetWorkflowType.TRIPO_RELEASE).name == (
        "tripo_release_candidate_workflow"
    )


def test_unknown_workflow_is_rejected():
    try:
        get_visual_asset_workflow("not-a-workflow")
    except ValueError as exc:
        assert "Unknown visual asset workflow" in str(exc)
    else:
        raise AssertionError("unknown workflow unexpectedly accepted")
