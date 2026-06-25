"""Protocol definitions for orchestration consumers.

Defines the minimal contracts that the asset pipeline depends on, allowing
agents to be injected without `orchestration → agents` coupling at module
import time.

The dependency direction is: agents conform to a protocol that orchestration
owns. This satisfies the project's layer rule (orchestration is L3, agents
is L4 — orchestration must not depend on agent classes).

Backward compatibility: the existing concrete agents already satisfy these
protocols structurally. No changes to agent code are required.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AssetWorkflowAgent(Protocol):
    """SuperAgent-compatible `run()` interface used by the asset pipeline.

    All three of `TripoAssetAgent`, `FashnTryOnAgent`, and `WordPressAssetAgent`
    inherit this signature from `SuperAgent.run` in `agents/base_legacy.py`.
    The `context` parameter is typed as `Any` here so the protocol does not
    leak `agents.*` types back into orchestration.
    """

    async def run(
        self,
        request: dict[str, Any],
        context: Any | None = None,
    ) -> dict[str, Any]: ...

    async def close(self) -> None: ...


@runtime_checkable
class WordPressUploadAgent(AssetWorkflowAgent, Protocol):
    """WordPress asset agent — `run()` plus a direct 3D upload entry point.

    Note: `upload_3d_model` uses `*args/**kwargs` to remain decoupled from
    the concrete agent's evolving parameter list.  The pipeline passes named
    kwargs (`glb_path`, `usdz_path`, `thumbnail_path`, `product_id`, `title`,
    `alt_text`) and the concrete agent may accept fewer of them — excess kwargs
    are silently ignored by the implementation.  Static type-checkers will flag
    call sites, but at runtime the duck-typed dispatch is safe.
    """

    async def upload_3d_model(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any: ...


@runtime_checkable
class PreviewGateAgent(Protocol):
    """Cheap preview-fidelity gate agent (Meshy-style)."""

    async def generate_preview(
        self,
        image_url: str,
        product_name: str = ...,
        minimum_fidelity: float = ...,
    ) -> dict[str, Any]: ...

    async def close(self) -> None: ...
