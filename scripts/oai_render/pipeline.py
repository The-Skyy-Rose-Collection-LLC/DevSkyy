"""Pipeline orchestration — resolve, plan, manifest, and render SKUs.

Dry-run by default: planning resolves references + builds prompts + a cost
manifest with ZERO API calls. Live generation requires an explicit caller
(cli `generate --yes`) and passes the hard cost cap.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from . import config, cost, references
from .cost import CostManifest, ManifestEntry
from .prompt import SceneError, build_pair_prompt, build_prompt, extract_view_branding, read_dossier
from .references import MissingReferenceError, Pair, ReferenceImage
from .scene_schema import build_scene

if TYPE_CHECKING:
    from .client import RenderClient
    from .cost import SpendTracker
    from .qc import QCGate
    from .runlog import RunLog

log = logging.getLogger(__name__)


@dataclass
class SkuPlan:
    """Everything needed to render one SKU (or the reason it cannot be rendered)."""

    sku: str
    name: str
    collection: str
    output_slug: str
    style: str = "ghost"  # presentation: "ghost" | "on-model" | "flatlay"
    view: str = "front"  # "front" | "back"; back is ghost-only, when a back source exists
    references: list[ReferenceImage] = field(default_factory=list)
    prompt: str = ""
    is_patch: bool = False
    branding_spec: str = ""  # dossier's per-view branding bullets, ground truth for the QC judge
    is_pair: bool = False  # True for a paired-look on-model (two garments, one model)
    pair_id: str | None = None
    pair_skus: tuple[str, ...] | None = None
    error: str | None = None  # set when the SKU is unrenderable (missing refs)

    @property
    def renderable(self) -> bool:
        return self.error is None and bool(self.references)


@dataclass
class RenderResult:
    sku: str
    status: str  # "rendered" | "skipped" | "error" | "qc_failed" | "needs_review"
    reason: str = ""
    output_path: Path | None = None


def resolve_targets(
    catalog: dict[str, dict],
    *,
    sku: str | None = None,
    skus: list[str] | None = None,
    collection: str | None = None,
    all_skus: bool = False,
) -> list[str]:
    """Resolve the requested SKU set from the catalog."""
    if sku:
        if sku not in catalog:
            raise KeyError(f"SKU {sku} not in catalog.")
        return [sku]
    if skus:
        missing = [s for s in skus if s not in catalog]
        if missing:
            raise KeyError(f"SKU(s) not in catalog: {', '.join(missing)}")
        return list(skus)
    if collection:
        return _drop_excluded(
            [s for s, info in sorted(catalog.items()) if info["collection"] == collection]
        )
    if all_skus:
        return _drop_excluded(sorted(catalog.keys()))
    return []


def _keeper_skips() -> dict[tuple[str, str, str], str]:
    """(sku, style, view) -> founder note, from render-keepers.json. Empty when absent.

    A keeper only suppresses its render plan if the surviving asset it names
    still exists on disk. If the file was renamed or deleted, the keeper is
    IGNORED (the plan re-renders) and a warning is logged — otherwise the
    keeper would silently block the re-render of a product whose "kept" image
    is gone.
    """
    import json

    try:
        data = json.loads(config.KEEPERS_JSON.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    repo_root = config.PROJECT_ROOT
    out: dict[tuple[str, str, str], str] = {}
    for k in data.get("keepers", []):
        sku, style = k.get("sku"), k.get("style")
        if not (sku and style):
            continue
        asset = k.get("asset")
        if not asset:
            # A keeper with no asset path cannot be existence-checked; honoring
            # it blind re-creates the silent-block bug. Skip + warn so the SKU
            # re-renders rather than being suppressed by an unverifiable claim.
            log.warning(
                "Keeper for %s %s has no 'asset' path — cannot verify; will re-render.",
                sku,
                style,
            )
            continue
        if not (repo_root / asset).exists():
            log.warning(
                "Keeper for %s %s ignored — asset no longer on disk (%s); will re-render.",
                sku,
                style,
                asset,
            )
            continue
        out[(sku, style, k.get("view", "front"))] = k.get("founder_note", "keeper")
    return out


def _drop_excluded(skus: list[str]) -> list[str]:
    """Filter known-bad-source SKUs from a batch, logging each skip + reason."""
    kept: list[str] = []
    for s in skus:
        reason = config.EXCLUDED_SKUS.get(s)
        if reason:
            log.warning("Excluding %s from batch: %s", s, reason)
        else:
            kept.append(s)
    return kept


def plan_sku(
    sku: str,
    catalog: dict[str, dict],
    dossier_index: dict[str, Path],
    *,
    style: str = "ghost",
    view: str = "front",
    style_reference: Path | None = None,
) -> SkuPlan:
    """Resolve references + dossier + prompt for a (SKU, style, view). Never raises for missing refs.

    ``style_reference`` is an optional environment/mood anchor image (e.g. a lookbook
    frame). When given, it is appended as the FINAL reference and the prompt restricts
    it to scene/lighting/mood — never a garment source.
    """
    info = catalog.get(sku, {})
    name = info.get("name", sku)
    collection = info.get("collection", "")
    slug = info.get("output_slug", sku)

    try:
        refs = references.build_references(sku, collection, view=view)
        use_style_ref = style_reference is not None and Path(style_reference).is_file()
        if use_style_ref:
            refs = [
                *refs,
                ReferenceImage(
                    label="STYLE & COMPOSITION REFERENCE (environment / lighting / mood only "
                    "— NOT a garment source)",
                    path=Path(style_reference),
                    kind="style",
                ),
            ]
        is_patch = references.requires_patch(sku)
        dossier_text = read_dossier(dossier_index.get(sku))
        scene = build_scene(sku=sku, name=name, collection=collection, style=style)
        prompt = build_prompt(
            name=name,
            sku=sku,
            collection=collection,
            reference_labels=[r.label for r in refs],
            dossier_text=dossier_text,
            is_patch=is_patch,
            style=style,
            view=view,
            scene=scene,
            style_reference=use_style_ref,
        )
    except (MissingReferenceError, SceneError) as exc:
        return SkuPlan(
            sku=sku,
            name=name,
            collection=collection,
            output_slug=slug,
            style=style,
            view=view,
            error=str(exc),
        )

    return SkuPlan(
        sku=sku,
        name=name,
        collection=collection,
        output_slug=slug,
        style=style,
        view=view,
        references=refs,
        prompt=prompt,
        is_patch=is_patch,
        branding_spec=extract_view_branding(dossier_text, view),
    )


def plan_pair(pair: Pair, catalog: dict[str, dict], dossier_index: dict[str, Path]) -> SkuPlan:
    """Plan a paired-look on-model render (two garments, one model). Front-only refs per garment."""
    slug = "pair__" + "__".join(pair.skus)
    per_garment_cap = max(1, config.MAX_REFERENCE_IMAGES // len(pair.skus))
    garments: list[dict] = []
    combined: list[ReferenceImage] = []
    try:
        for member in pair.skus:
            mname = catalog.get(member, {}).get("name", member)
            refs = references.build_references(member, pair.collection, include_back=False)
            refs = refs[:per_garment_cap]
            combined.extend(refs)
            garments.append(
                {
                    "name": mname,
                    "sku": member,
                    "reference_labels": [r.label for r in refs],
                    "dossier_text": read_dossier(dossier_index.get(member)),
                    "is_patch": references.requires_patch(member),
                }
            )
        pair_branding = "\n".join(
            f"{g['name']} ({g['sku']}) FRONT:\n{spec}"
            for g in garments
            if (spec := extract_view_branding(g["dossier_text"], "front"))
        )
        prompt = build_pair_prompt(
            pair_label=pair.label, collection=pair.collection, garments=garments
        )
    except (MissingReferenceError, SceneError) as exc:
        return SkuPlan(
            sku=pair.skus[0],
            name=pair.label,
            collection=pair.collection,
            output_slug=slug,
            style="on-model",
            view="front",
            is_pair=True,
            pair_id=pair.pair_id,
            pair_skus=pair.skus,
            error=str(exc),
        )

    return SkuPlan(
        sku=pair.skus[0],
        name=pair.label,
        collection=pair.collection,
        output_slug=slug,
        style="on-model",
        view="front",
        is_pair=True,
        pair_id=pair.pair_id,
        pair_skus=pair.skus,
        references=combined,
        prompt=prompt,
        is_patch=any(g["is_patch"] for g in garments),
        branding_spec=pair_branding,
    )


def build_manifest(plans: list[SkuPlan]) -> CostManifest:
    """Build the cost manifest. Renderable SKUs cost 1 image; skipped show 0 + reason."""
    entries: list[ManifestEntry] = []
    for p in plans:
        if p.is_pair:
            label = f"{p.name} · on-model (paired)"
        else:
            view_tag = "" if p.view == "front" else " (back)"
            label = f"{p.name} · {p.style}{view_tag}"
        if p.renderable:
            entries.append(
                ManifestEntry(sku=p.sku, name=label, n_images=config.N, ref_count=len(p.references))
            )
        else:
            short = (p.error or "no references").split(";")[0][:48]
            entries.append(
                ManifestEntry(sku=p.sku, name=label, n_images=0, ref_count=0, note=f"SKIP: {short}")
            )
    return CostManifest(entries=entries)


def _output_filename(plan: SkuPlan) -> str:
    if plan.is_pair:
        return "on-model.png"
    suffix = "" if plan.view == "front" else "-back"
    return f"{plan.style}{suffix}.png"


def _quarantine(plan: SkuPlan, data: bytes, attempt: int, verdict) -> Path:
    """Write a QC-rejected render + its verdict to the quarantine dir for review."""
    qdir = config.REJECTED_DIR / plan.output_slug
    qdir.mkdir(parents=True, exist_ok=True)
    stem = _output_filename(plan).removesuffix(".png")
    img_path = qdir / f"{stem}.attempt{attempt}.png"
    img_path.write_bytes(data)
    meta = {
        "sku": plan.sku,
        "style": plan.style,
        "view": plan.view,
        "is_pair": plan.is_pair,
        "attempt": attempt,
        "failure_tags": list(verdict.failure_tags),
        "reason": verdict.reason,
    }
    (qdir / f"{stem}.attempt{attempt}.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    return img_path


# Per-failure-tag corrective guidance fed back into the next render attempt. The QC
# judge already says WHY a render failed; replaying the identical prompt ignores that
# signal and pays full price for a coin-flip. Injecting it makes each retry targeted.
_RETRY_TAG_GUIDANCE = {
    "branding_drift": "A logo, patch, or text was missing, invented, garbled, or misplaced. "
    "Reproduce EVERY mark EXACTLY as in the references — correct content, position, and size; "
    "render NO mark on a panel its reference leaves blank.",
    "wrong_garment": "The garment did not match the references. Match silhouette, fabric, colour, "
    "and every graphic to the reference images exactly.",
    "wrong_view": "The wrong face of the garment was shown. Render ONLY the requested view.",
    "flat_render": "The output looked flat, vector, or illustrated. Render a photorealistic, "
    "dimensional garment with real drape, seams, texture, and studio lighting.",
    "collage_panels": "The output had multiple panels / a collage. Produce ONE single full-bleed "
    "photograph — no grid, no split-screen, no reference sheet.",
    "missing_pair_garment": "A required garment was missing. BOTH garments must be worn and "
    "visible on the one model.",
    "wrong_dimensions": "Render at the exact portrait framing requested; do not crop the garment.",
}


def _retry_correction(verdict) -> str:
    """Build a targeted correction block from a rejected QC verdict for the next attempt.

    The judge already explained the defect; feeding it back turns a blind re-render
    (a full-price coin-flip) into a targeted fix.
    """
    lines = [_RETRY_TAG_GUIDANCE[t] for t in verdict.failure_tags if t in _RETRY_TAG_GUIDANCE]
    block = [
        "",
        "",
        "PREVIOUS ATTEMPT REJECTED BY QC — you MUST correct these specific problems now:",
    ]
    reason = (getattr(verdict, "reason", "") or "").strip()
    if reason:
        block.append(f"  - Reviewer feedback: {reason}")
    block.extend(f"  - {ln}" for ln in lines)
    return "\n".join(block)


def render_sku(
    plan: SkuPlan,
    client: RenderClient,
    *,
    gate: QCGate | None = None,
    spend: SpendTracker | None = None,
    runlog: RunLog | None = None,
) -> RenderResult:
    """Render one renderable SKU; QC-gate the output before accepting it.

    Loop: budget check → paid render → QC verdict. A failing verdict quarantines
    the attempt and re-renders, up to ``config.QC_MAX_RENDER_RETRIES`` extra
    attempts; exhaustion returns status ``qc_failed`` (needs human review) — the
    batch continues. Without a gate the first successful render is accepted
    (legacy behavior, used by tests and judge-disabled runs).
    """

    def _emit(event: str, **fields) -> None:
        if runlog is not None:
            if spend is not None:
                fields.setdefault("spent_usd", round(spend.spent_usd, 2))
            runlog.emit(event, sku=plan.sku, slug=plan.output_slug, **fields)

    if not plan.renderable:
        _emit("skipped", reason=plan.error or "no references")
        return RenderResult(sku=plan.sku, status="skipped", reason=plan.error or "no references")

    max_attempts = 1 + config.QC_MAX_RENDER_RETRIES
    last_verdict = None
    for attempt in range(max_attempts):
        if spend is not None and not spend.can_afford(config.EST_COST_PER_IMAGE_USD):
            _emit("budget_stop", cap_usd=spend.cap_usd)
            return RenderResult(
                sku=plan.sku,
                status="error",
                reason=f"budget: ${spend.spent_usd:.2f} spent, cap ${spend.cap_usd:.2f} — "
                "refusing further paid calls",
            )
        _emit(
            "attempt",
            name=plan.name,
            style=plan.style,
            view=plan.view,
            attempt=attempt + 1,
            max_attempts=max_attempts,
        )
        attempt_prompt = plan.prompt
        if last_verdict is not None:
            attempt_prompt += _retry_correction(last_verdict)
        try:
            data = client.edit(prompt=attempt_prompt, image_paths=[r.path for r in plan.references])
        except Exception as exc:  # surfaced, never swallowed
            log.error("Render failed for %s: %s", plan.sku, exc)
            reason = f"{type(exc).__name__}: {str(exc)[:300]}"
            _emit("render_error", reason=reason)
            return RenderResult(sku=plan.sku, status="error", reason=reason)
        if spend is not None:
            spend.add(config.EST_COST_PER_IMAGE_USD)

        if gate is None:
            verdict = None
        else:
            verdict = gate.check(data, expectation_for(plan))
            if spend is not None and verdict.judge_cost_usd:
                spend.add(verdict.judge_cost_usd)
            _emit(
                "qc_verdict",
                attempt=attempt + 1,
                passed=verdict.passed,
                tags=list(verdict.failure_tags),
                reason=verdict.reason,
                analysis=verdict.analysis,
            )

        if verdict is not None and verdict.needs_review:
            # Q-unavail: the QC judge was unavailable, so this render is UNJUDGED.
            # Never auto-accept it, and never burn paid retries — re-rendering cannot
            # fix a down judge. Quarantine the bytes for mandatory human sign-off and
            # stop here.
            _quarantine(plan, data, attempt + 1, verdict)
            _emit(
                "qc_needs_review",
                attempt=attempt + 1,
                tags=list(verdict.failure_tags),
                reason=verdict.reason,
            )
            return RenderResult(sku=plan.sku, status="needs_review", reason=verdict.summary)

        if verdict is None or verdict.passed:
            return _accept_render(plan, data, attempt + 1, _emit)

        _reject_render(plan, data, attempt + 1, max_attempts, verdict, _emit)
        # Early-abort: the SAME failure mode twice running means the references +
        # corrective feedback still didn't fix it — a further identical-failure render
        # is wasted spend. Stop and quarantine for human review.
        if (
            attempt + 1 < max_attempts
            and last_verdict is not None
            and verdict.failure_tags
            and verdict.failure_tags == last_verdict.failure_tags
        ):
            _emit(
                "retry_aborted",
                attempt=attempt + 1,
                tags=list(verdict.failure_tags),
                reason="same QC failure twice — aborting retries to avoid wasted spend",
            )
            last_verdict = verdict
            break
        last_verdict = verdict

    _emit("qc_exhausted", reason=last_verdict.summary if last_verdict else "qc failed")
    return RenderResult(
        sku=plan.sku,
        status="qc_failed",
        reason=last_verdict.summary if last_verdict else "qc failed",
    )


def _accept_render(plan: SkuPlan, data: bytes, attempt: int, _emit) -> RenderResult:
    """Persist an accepted render to the output tree (disk errors captured, not raised)."""
    try:
        out_dir = config.OUTPUT_DIR / plan.output_slug
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / _output_filename(plan)
        out_path.write_bytes(data)
    except OSError as exc:  # disk error after a paid call — capture, don't abort
        log.error("Disk write failed for %s: %s", plan.sku, exc)
        _emit("render_error", reason=f"disk: {exc}")
        return RenderResult(sku=plan.sku, status="error", reason=f"disk: {exc}")
    log.info("Rendered %s → %s (%d bytes)", plan.sku, out_path, len(data))
    _emit("accepted", attempt=attempt, path=str(out_path))
    return RenderResult(sku=plan.sku, status="rendered", output_path=out_path)


def _reject_render(plan: SkuPlan, data: bytes, attempt: int, max_attempts: int, verdict, _emit):
    """Quarantine a QC-rejected attempt for human review; the caller decides on retry."""
    try:
        _quarantine(plan, data, attempt, verdict)
    except OSError as exc:
        log.error("Quarantine write failed for %s: %s", plan.sku, exc)
    _emit("quarantined", attempt=attempt, tags=list(verdict.failure_tags))
    log.warning(
        "QC rejected %s attempt %d/%d [%s] — %s",
        plan.sku,
        attempt,
        max_attempts,
        ",".join(verdict.failure_tags),
        verdict.reason,
    )


def expectation_for(plan: SkuPlan):
    from .qc import RenderExpectation

    return RenderExpectation(
        sku=plan.sku,
        name=plan.name,
        style=plan.style,
        view=plan.view,
        is_pair=plan.is_pair,
        is_patch=plan.is_patch,
        branding_spec=plan.branding_spec,
        reference_paths=tuple(r.path for r in plan.references),
    )


def run(
    targets: list[str],
    catalog: dict[str, dict],
    dossier_index: dict[str, Path],
    *,
    styles: list[str] | None = None,
    dry_run: bool = True,
    client=None,
    verify_assets: bool = True,
    front_only: bool = False,
    style_reference: Path | None = None,
) -> dict:
    """Plan the render matrix for all targets; render them when not dry-run (client required).

    Matrix rules (founder-locked):
      - ghost-front:  always (feeds the product card)
      - ghost-back:   only when the SKU has a dedicated back source (also a product-card image)
      - on-model:     if the SKU is in a pair → ONE paired-look render per unique pair (two
                      garments, one model), deduped; else a solo on-model. Front only, with a
                      collection-specific scene background (hero image).

    ``front_only=True`` renders ONLY ghost-front (the product card) — no ghost-back,
    no on-model/paired looks. Used for a fast, cheap product-card-coverage pass when
    the back-view and paired renders are the expensive, low-yield cases.
    """
    use_styles = ["ghost"] if front_only else (styles or ["ghost"])
    plans: list[SkuPlan] = []
    seen_pairs: set[str] = set()
    for s in targets:
        for st in use_styles:
            if st == "ghost":
                plans.append(
                    plan_sku(
                        s,
                        catalog,
                        dossier_index,
                        style="ghost",
                        view="front",
                        style_reference=style_reference,
                    )
                )
                if not front_only and references.has_back_source(s):
                    plans.append(
                        plan_sku(
                            s,
                            catalog,
                            dossier_index,
                            style="ghost",
                            view="back",
                            style_reference=style_reference,
                        )
                    )
            elif st == "on-model":
                # A pair is only renderable when NO member is excluded — an excluded
                # member's dossier is known-bad and would corrupt the paired look.
                all_pairs = references.get_pairs_for_sku(s)
                pairs = [
                    pr for pr in all_pairs if not any(m in config.EXCLUDED_SKUS for m in pr.skus)
                ]
                for pr in all_pairs:
                    excluded = [m for m in pr.skus if m in config.EXCLUDED_SKUS]
                    if excluded:
                        log.warning(
                            "Skipping paired look %s: member(s) %s excluded (%s)",
                            pr.pair_id,
                            ", ".join(excluded),
                            "; ".join(config.EXCLUDED_SKUS[m] for m in excluded)[:120],
                        )
                if pairs:
                    for pr in pairs:  # paired SKU: one paired look per pair, no solo on-model
                        if pr.pair_id in seen_pairs:
                            continue
                        seen_pairs.add(pr.pair_id)
                        plans.append(plan_pair(pr, catalog, dossier_index))
                else:  # no renderable pair → solo on-model so the SKU still gets a hero
                    plans.append(
                        plan_sku(
                            s,
                            catalog,
                            dossier_index,
                            style="on-model",
                            view="front",
                            style_reference=style_reference,
                        )
                    )
            else:  # flatlay or any other explicit style
                plans.append(
                    plan_sku(
                        s,
                        catalog,
                        dossier_index,
                        style=st,
                        view="front",
                        style_reference=style_reference,
                    )
                )

    keepers = _keeper_skips()
    if keepers:
        kept_plans: list[SkuPlan] = []
        for pl in plans:
            note = None if pl.is_pair else keepers.get((pl.sku, pl.style, pl.view))
            if note:
                log.info(
                    "Skipping %s %s/%s — founder keeper asset exists (%s)",
                    pl.sku,
                    pl.style,
                    pl.view,
                    note,
                )
            else:
                kept_plans.append(pl)
        plans = kept_plans
    manifest = build_manifest(plans)

    if dry_run:
        return {"plans": plans, "manifest": manifest, "results": []}

    cost.enforce_cap(manifest)  # defense-in-depth (cli also enforces before --yes)
    if client is None:
        raise ValueError("Live run requires an image client.")

    results = render_all(plans, client, verify_assets=verify_assets)
    return {"plans": plans, "manifest": manifest, "results": results}


class AssetIntegrityError(RuntimeError):
    """A planned SKU's source asset drifted from the committed manifest.

    Carries the drift findings so the caller can report which files changed.
    Raised before any paid API call — the bug-119 wrong-product prevention.
    """

    def __init__(self, findings: list):
        self.findings = findings
        super().__init__(f"{len(findings)} asset(s) drifted from the manifest")


def verify_plan_assets(plans: list[SkuPlan]) -> list:
    """Return manifest-drift findings for every SKU the plans will render.

    Fail-closed: if the committed manifest is ABSENT, the gate has no oracle and
    cannot tell "assets OK" from "no idea" — it returns a ``manifest_missing``
    finding so a paid run blocks rather than proceeding with zero protection
    (the same silent pass-through that caused bug-119).
    """
    from skyyrose.core.asset_manifest import MANIFEST_PATH, AssetManifest, DriftFinding

    if not MANIFEST_PATH.exists():
        return [
            DriftFinding(
                sku="*",
                role="-",
                path=str(MANIFEST_PATH),
                kind="manifest_missing",
                detail="asset manifest not found — run scripts/build_asset_manifest.py",
            )
        ]
    skus: set[str] = set()
    for p in plans:
        skus.add(p.sku)
        skus.update(p.pair_skus or ())
    return AssetManifest.load().verify(sorted(skus))


def render_all(
    plans: list[SkuPlan],
    client: RenderClient,
    *,
    verify_assets: bool = True,
    runlog: RunLog | None = None,
) -> list[RenderResult]:
    """Render every plan in order; per-SKU skips/errors are captured, not raised.

    Before any paid call, every planned SKU's source assets are verified against
    the committed manifest (unless ``verify_assets=False``); drift raises
    :class:`AssetIntegrityError`. This guard lives here — the single choke point
    every paid caller routes through — so no entry point can bypass it.

    One QC gate + one runtime spend tracker per batch: every paid call (render,
    judged retry, judge) draws from the same HARD_COST_CAP_USD budget.
    """
    if verify_assets:
        drift = verify_plan_assets(plans)
        if drift:
            raise AssetIntegrityError(drift)

    from .cost import SpendTracker
    from .qc import QCGate

    gate = QCGate() if config.QC_ENABLED else None
    spend = SpendTracker()
    if runlog is not None:
        runlog.emit(
            "run_start",
            n_plans=len(plans),
            skus=[p.sku for p in plans],
            est_cost_usd=round(len(plans) * config.EST_COST_PER_IMAGE_USD, 2),
            cap_usd=spend.cap_usd,
            judge=(
                config.QC_JUDGE_MODEL_ANTHROPIC
                if config.QC_JUDGE_PROVIDER == "anthropic"
                else config.QC_JUDGE_MODEL
            ),
        )
    results = [render_sku(p, client, gate=gate, spend=spend, runlog=runlog) for p in plans]
    if runlog is not None:
        statuses = [r.status for r in results]
        runlog.emit(
            "run_end",
            rendered=statuses.count("rendered"),
            skipped=statuses.count("skipped"),
            errored=statuses.count("error"),
            qc_failed=statuses.count("qc_failed"),
            spent_usd=round(spend.spent_usd, 2),
            cap_usd=spend.cap_usd,
        )
    log.info("Batch spend (estimated): $%.2f of $%.2f cap", spend.spent_usd, spend.cap_usd)
    return results
