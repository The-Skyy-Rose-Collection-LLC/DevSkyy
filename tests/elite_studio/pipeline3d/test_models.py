from pathlib import Path

from skyyrose.elite_studio.pipeline3d.models import (
    STAGE_ORDER,
    Artifact,
    JobSpec,
    PipelineResult,
    Stage,
    StageResult,
    TaskStatus,
    ordered_stages,
)


def test_stage_values():
    assert Stage.IMAGE_TO_3D.value == "image_to_3d"
    assert Stage.EXPORT.value == "export"


def test_stage_order_is_canonical():
    assert STAGE_ORDER == (Stage.IMAGE_TO_3D, Stage.TEXTURE, Stage.REMESH, Stage.EXPORT)


def test_ordered_stages_sorts_and_filters():
    # requested out of order + missing TEXTURE -> canonical order, TEXTURE dropped
    got = ordered_stages((Stage.EXPORT, Stage.IMAGE_TO_3D, Stage.REMESH))
    assert got == (Stage.IMAGE_TO_3D, Stage.REMESH, Stage.EXPORT)


def test_artifact_is_frozen():
    a = Artifact(provider="tripo", task_id="t1", path=Path("x.glb"))
    assert a.fmt == "glb"
    try:
        a.provider = "meshy"  # type: ignore[misc]
        raised = False
    except Exception:
        raised = True
    assert raised


def test_jobspec_defaults():
    j = JobSpec(sku="br-001", source_image=Path("src.png"), stages=(Stage.IMAGE_TO_3D,))
    assert j.formats == ("glb",)
    assert j.budget_ceiling_usd == 5.0
    assert j.output_dir == Path("renders/3d")


def test_pipeline_result_holds_results():
    art = Artifact(provider="tripo", path=Path("o.glb"))
    r = StageResult(stage=Stage.IMAGE_TO_3D, artifact=art, cost_usd=0.4, duration_ms=10)
    pr = PipelineResult(
        job_id="abc",
        sku="br-001",
        status=TaskStatus.SUCCEEDED,
        results=(r,),
        final_artifact=art,
        total_cost_usd=0.4,
    )
    assert pr.status is TaskStatus.SUCCEEDED
    assert pr.results[0].cost_usd == 0.4
