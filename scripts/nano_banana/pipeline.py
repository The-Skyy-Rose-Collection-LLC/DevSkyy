"""Production pipeline orchestrator — 5-step image generation.

Coordinates vision analysis, model routing, generation, refinement,
and QA scoring into a single production-quality workflow.

Usage:
    from nano_banana.pipeline import ProductionPipeline
    pipe = ProductionPipeline.from_env()
    result = pipe.run_single(product, source_path, view="front")
    results = pipe.run_batch(products, views=["front", "back", "branding"])
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from nano_banana.vision_context import VisionContext

if TYPE_CHECKING:
    from nano_banana.tournament import TournamentResult

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class PipelineResult:
    """Result from a single product + view generation run."""

    sku: str
    view: str
    output_path: Path | None = None
    engine_used: str = ""
    vision_desc: dict = field(default_factory=dict)
    route_decision: str = ""
    qa_score: float = 0.0
    qa_passed: bool = False
    attempts: int = 0
    cost_usd: float = 0.0
    issues: list[str] = field(default_factory=list)
    refinement_applied: bool = False

    def to_dict(self) -> dict:
        return {
            "sku": self.sku,
            "view": self.view,
            "output_path": str(self.output_path) if self.output_path else None,
            "engine_used": self.engine_used,
            "route_decision": self.route_decision,
            "qa_score": self.qa_score,
            "qa_passed": self.qa_passed,
            "attempts": self.attempts,
            "cost_usd": self.cost_usd,
            "issues": self.issues,
            "refinement_applied": self.refinement_applied,
        }


class ProductionPipeline:
    """Full production pipeline with retry logic and model fallback."""

    def __init__(
        self,
        genai_client,
        openai_client=None,
        anthropic_client=None,
        fal_available: bool = False,
        config=None,
    ):
        from nano_banana.config import PipelineConfig

        self.genai = genai_client
        self.openai = openai_client
        self.anthropic = anthropic_client
        self.fal_available = fal_available
        self.config = config or PipelineConfig.production()
        self._vision_cache: dict[str, dict] = {}

    @classmethod
    def from_env(cls) -> ProductionPipeline:
        """Create pipeline from environment variables.

        Loads API keys from .env.secrets in the project root or parent.
        """
        from nano_banana.client import get_genai_client, get_openai_client
        from nano_banana.config import PipelineConfig

        # Source .env.secrets if it exists
        for env_path in [
            PROJECT_ROOT / ".env.secrets",
            PROJECT_ROOT.parent / ".env.secrets",
        ]:
            if env_path.exists():
                _source_env_file(env_path)
                break

        genai = get_genai_client()
        openai_client = get_openai_client()

        anthropic_client = None
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if anthropic_key:
            try:
                import anthropic

                anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
            except ImportError:
                log.warning("anthropic package not installed — Claude judge unavailable")

        fal_available = bool(os.getenv("FAL_KEY", "") or os.getenv("FAL_AI_KEY", ""))

        # Load config from file if exists, else production default
        config_path = PROJECT_ROOT / "data" / "pipeline-config.json"
        if config_path.exists():
            config = PipelineConfig.from_json(config_path)
            log.info("Loaded config from %s", config_path)
        else:
            config = PipelineConfig.production()

        return cls(
            genai_client=genai,
            openai_client=openai_client,
            anthropic_client=anthropic_client,
            fal_available=fal_available,
            config=config,
        )

    def run_single(
        self,
        product: dict,
        source_path: Path,
        view: str = "front",
    ) -> PipelineResult:
        """Run the full 5-step pipeline for one product + one view."""
        from nano_banana.engine_fal import generate_flux_fal, refine_with_kontext
        from nano_banana.generate import (
            GEMINI_FAST,
            GEMINI_PRO,
            composite_gemini,
            generate_gemini,
            generate_gpt,
        )
        from nano_banana.prompt_registry import PromptRegistry
        from nano_banana.router import route_product
        from nano_banana.tournament import run_tournament
        from nano_banana.utils import quality_gate, save_image

        sku = product.get("sku", "unknown")
        name = product.get("name", "garment")
        collection = product.get("collection", "black-rose")
        cfg = self.config
        result = PipelineResult(sku=sku, view=view)

        log.info("=" * 60)
        log.info("PIPELINE: %s — %s (%s)", sku, name, view)
        log.info("=" * 60)

        # ── Step 1: DESCRIBE ─────────────────────────────────────────
        vision_desc = self._get_or_cache_vision(product, source_path)

        # Inject canonical dossier spec for the tournament. Routing and
        # prompt-builder code still use inferred fields. Soft-fail when
        # a dossier is missing so SKUs mid-authoring still render.
        try:
            from nano_banana.spec_builder import build_dna_from_sku

            canonical = build_dna_from_sku(sku)
            # Attribute writes on VisionContext — typed contract instead
            # of the previous string-keyed mutation. Spec and dossier are
            # always populated together (they come from the same load),
            # which matches VisionContext's co-presence invariant.
            vision_desc.spec = canonical.spec
            vision_desc.dossier = canonical.dossier
            log.info(
                "DOSSIER: loaded canonical spec for %s (%dc spec text)",
                sku,
                len(canonical.spec) if canonical.spec else 0,
            )
        except Exception as exc:
            log.warning(
                "DOSSIER: no canonical spec for %s — falling back to inferred DNA. Reason: %s",
                sku,
                exc,
            )

        # Store flat-dict view for JSON serialization & downstream readers.
        # The Dossier object is intentionally dropped here (large, not
        # JSON-safe); spec text is preserved.
        result.vision_desc = vision_desc.to_dict()

        # ── Step 1b: GATHER BUNDLE REFERENCES ────────────────────────
        # Load COMPLETE product bundle — every available asset
        extra_refs = _load_bundle_refs(name, sku, source_path, view)
        log.info("BUNDLE: %d reference images loaded for %s", len(extra_refs) + 1, name)

        # ── Step 2: ROUTE ────────────────────────────────────────────
        decisions = route_product(product, vision_desc, view)
        if not decisions:
            log.error("Router returned no decisions for %s", sku)
            result.issues.append("Router returned no engine decisions")
            return result

        log.info(
            "ROUTE: %s (fallback: %s)",
            decisions[0].reason,
            decisions[1].engine if len(decisions) > 1 else "none",
        )
        result.route_decision = decisions[0].reason

        # ── Step 3: GENERATE ─────────────────────────────────────────
        # Build prompt from registry (A/B tested templates) — based on
        # inferred Gemini-vision DNA. When the on-disk image carries
        # defects, this DNA reflects the defects; the canonical positives
        # below override that.
        registry = PromptRegistry.load()
        model_hint = decisions[0].engine if decisions else ""
        prompt, template_id = registry.get_prompt(vision_desc, product, view, model_hint)

        # Layer 3: prepend authored dossier POSITIVES so the generator
        # sees the canonical garment_type_lock + branding_block at the
        # front of the prompt (highest attention weight). Breaks the
        # self-reinforcing defect loop where vision-describe of a
        # defective render produces inferred DNA matching the defect,
        # which the generator then faithfully reproduces.
        # Layer 2: append authored dossier NEGATIVES so authored
        # "DO NOT render X" rules flow through to the generator,
        # not just the judges.
        from nano_banana.spec_builder import (
            augment_prompt_with_dossier_negatives,
            augment_prompt_with_dossier_positives,
        )

        prompt = augment_prompt_with_dossier_positives(prompt, vision_desc)
        prompt = augment_prompt_with_dossier_negatives(prompt, vision_desc)

        img_bytes = None
        engine_used = ""
        total_cost = 0.0

        for attempt in range(cfg.max_attempts):
            # Pick engine: primary on first attempt, fallback on subsequent
            decision_idx = min(attempt, len(decisions) - 1)
            decision = decisions[decision_idx]
            engine = decision.engine
            model_id = decision.model_id

            log.info(
                "  Attempt %d/%d — engine: %s, template: %s",
                attempt + 1,
                cfg.max_attempts,
                engine,
                template_id,
            )

            try:
                if engine in ("gemini-pro", "gemini-flash"):
                    actual_model = GEMINI_PRO if engine == "gemini-pro" else GEMINI_FAST
                    img_bytes = generate_gemini(
                        self.genai,
                        source_path,
                        prompt,
                        model=actual_model,
                        aspect_ratio=cfg.aspect_ratio,
                        enhanced=(attempt > 0),
                        extra_refs=extra_refs,
                    )
                elif engine == "gpt-image" and self.openai:
                    img_bytes = generate_gpt(self.openai, prompt, source_path)
                elif engine == "flux-pro" and self.fal_available:
                    img_bytes = generate_flux_fal(source_path, prompt)
                else:
                    log.warning("  Engine %s unavailable, trying next", engine)
                    continue

            except Exception as exc:
                log.error("  Generation error: %s", exc)
                img_bytes = None

            total_cost += decision.estimated_cost
            result.attempts = attempt + 1

            if img_bytes and quality_gate(img_bytes, sku, view):
                engine_used = engine
                break

            log.warning("  Attempt %d failed or rejected by quality gate", attempt + 1)
            img_bytes = None

            if attempt < cfg.max_attempts - 1:
                time.sleep(cfg.retry_delay_seconds)

        if not img_bytes:
            log.error("GENERATE FAILED: %s %s after %d attempts", sku, view, cfg.max_attempts)
            result.issues.append(f"Generation failed after {cfg.max_attempts} attempts")
            result.cost_usd = total_cost
            return result

        # Save generated image
        output_dir = PROJECT_ROOT / cfg.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        output_filename = f"{sku}-{view}-render.webp"
        output_path = output_dir / output_filename
        save_image(img_bytes, output_path)
        result.output_path = output_path
        result.engine_used = engine_used
        result.cost_usd = total_cost

        # ── Step 4: QA ──────────────────────────────────────────────
        tournament_clients = {
            "openai": self.openai,
            "anthropic": self.anthropic,
            "gemini": self.genai,
        }

        # Use real product photo for QA when available (not techflat)
        qa_source = source_path
        bundle_dir = _find_bundle_dir(name, sku)
        if bundle_dir:
            for tag in ("photo-front", "source-photo"):
                for f in bundle_dir.glob(f"{tag}.*"):
                    if f.exists():
                        qa_source = f
                        break
                if qa_source != source_path:
                    break

        qa_result: TournamentResult | None = None
        try:
            qa_result = run_tournament(
                clients=tournament_clients,
                source_path=qa_source,
                candidate_path=output_path,
                dna=vision_desc,
                passing_threshold=cfg.qa_auto_approve,
            )
            result.qa_score = qa_result.aggregate_score
            result.qa_passed = qa_result.passed_98  # uses passing_threshold
            result.issues = qa_result.top_issues

            log.info(
                "QA: %.1f/100 — %s",
                qa_result.aggregate_score,
                "PASS" if qa_result.passed_98 else "NEEDS WORK",
            )

            # Feed score back to prompt registry (A/B testing loop)
            registry.record_score(template_id, qa_result.aggregate_score)
            registry.save()

            # Save QA results
            qa_dir = PROJECT_ROOT / cfg.qa_results_dir
            qa_dir.mkdir(parents=True, exist_ok=True)
            qa_file = qa_dir / f"{sku}_{view}_{int(time.time())}.json"
            qa_file.write_text(json.dumps(qa_result.to_dict(), indent=2))

        except Exception as exc:
            log.error("QA tournament failed: %s", exc)
            result.issues.append(f"QA failed: {exc}")

        # ── Step 5: REFINE (conditional) ─────────────────────────────
        # Three independent triggers: vision-judge text/logo thresholds
        # AND the synthesis judge's hallucination veto. The veto is
        # luxury-brand-disqualifying — even renders with high text/logo
        # scores must be refined if Opus says they hallucinated.
        needs_refine = False
        if qa_result is not None and hasattr(qa_result, "judges"):
            for judge in qa_result.judges:
                if judge.text_accuracy < cfg.qa_refine_text_threshold:
                    needs_refine = True
                    log.info(
                        "REFINE triggered: %s text_accuracy=%d < %d",
                        judge.judge,
                        judge.text_accuracy,
                        cfg.qa_refine_text_threshold,
                    )
                    break
                if judge.logo_accuracy < cfg.qa_refine_logo_threshold:
                    needs_refine = True
                    log.info(
                        "REFINE triggered: %s logo_accuracy=%d < %d",
                        judge.judge,
                        judge.logo_accuracy,
                        cfg.qa_refine_logo_threshold,
                    )
                    break

        # Hallucination-veto override — synthesis judge sees what vision
        # pair averaged-out. Veto fires regardless of threshold triggers.
        synth_judge = qa_result.synthesis_judge if hasattr(qa_result, "synthesis_judge") else None
        if synth_judge and getattr(synth_judge, "hallucination_veto", False):
            log.info("REFINE triggered: synthesis hallucination_veto=True")
            needs_refine = True

        if needs_refine and result.qa_score < cfg.qa_auto_approve:
            log.info("Attempting refinement...")
            refined_bytes = None

            refine_prompt = _build_refinement_prompt(name, sku, qa_result)
            log.info("REFINE prompt:\n%s", refine_prompt)

            if self.fal_available:
                refined_bytes = refine_with_kontext(output_path, refine_prompt)

            # Fallback: Gemini composite — same synthesis-aware prompt.
            if not refined_bytes and source_path.exists():
                refined_bytes = composite_gemini(
                    self.genai, output_path, source_path, refine_prompt
                )

            if refined_bytes and quality_gate(refined_bytes, sku, f"{view}-refined"):
                save_image(refined_bytes, output_path)
                result.refinement_applied = True
                total_cost += 0.04  # approximate refinement cost
                result.cost_usd = total_cost

                # Re-run QA
                try:
                    qa2 = run_tournament(
                        clients=tournament_clients,
                        source_path=source_path,
                        candidate_path=output_path,
                        dna=vision_desc,
                        passing_threshold=cfg.qa_auto_approve,
                    )
                    result.qa_score = qa2.aggregate_score
                    result.qa_passed = qa2.passed_98
                    result.issues = qa2.top_issues
                    log.info(
                        "QA (post-refine): %.1f/100 — %s",
                        qa2.aggregate_score,
                        "PASS" if qa2.passed_98 else "NEEDS WORK",
                    )
                except Exception as exc:
                    log.error("Post-refine QA failed: %s", exc)

        # Auto-reject check
        if result.qa_score < cfg.qa_auto_reject:
            log.warning(
                "AUTO-REJECT: %s %s scored %.1f (< %.1f threshold)",
                sku,
                view,
                result.qa_score,
                cfg.qa_auto_reject,
            )
            result.qa_passed = False

        log.info(
            "RESULT: %s %s — engine=%s score=%.1f passed=%s cost=$%.3f attempts=%d refined=%s",
            sku,
            view,
            engine_used,
            result.qa_score,
            result.qa_passed,
            result.cost_usd,
            result.attempts,
            result.refinement_applied,
        )

        return result

    def run_batch(
        self,
        products: list[dict],
        views: list[str] | None = None,
        output_dir: Path | None = None,
    ) -> list[PipelineResult]:
        """Run pipeline for multiple products. Rate-limited."""
        if views is None:
            views = self.config.default_views

        if output_dir:
            self.config.output_dir = str(output_dir)

        results = []
        total = len(products) * len(views)
        idx = 0

        for product in products:
            sku = product.get("sku", "unknown")
            source = product.get("source_image")

            if not source or not Path(source).exists():
                log.warning("SKIP %s — no source image", sku)
                for view in views:
                    results.append(
                        PipelineResult(
                            sku=sku,
                            view=view,
                            issues=["No source image available"],
                        )
                    )
                    idx += 1
                continue

            for view in views:
                idx += 1
                log.info("\n[%d/%d] %s %s", idx, total, sku, view)

                result = self.run_single(product, Path(source), view)
                results.append(result)

                # Rate limiting between calls
                if idx < total:
                    time.sleep(self.config.retry_delay_seconds)

        # Summary
        passed = sum(1 for r in results if r.qa_passed)
        failed = sum(1 for r in results if r.output_path and not r.qa_passed)
        skipped = sum(1 for r in results if not r.output_path)
        total_cost = sum(r.cost_usd for r in results)

        log.info("\n" + "=" * 60)
        log.info("BATCH COMPLETE: %d passed / %d need review / %d skipped", passed, failed, skipped)
        log.info("Total cost: $%.2f", total_cost)
        log.info("=" * 60)

        # Save batch report
        report_path = (
            PROJECT_ROOT / self.config.qa_results_dir / f"batch-report-{int(time.time())}.json"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(
                {
                    "summary": {
                        "passed": passed,
                        "needs_review": failed,
                        "skipped": skipped,
                        "total_cost": total_cost,
                    },
                    "results": [r.to_dict() for r in results],
                },
                indent=2,
            )
        )
        log.info("Batch report: %s", report_path)

        return results

    def _get_or_cache_vision(self, product: dict, source_path: Path) -> VisionContext:
        """Get vision description from cache or generate new.

        Returns a VisionContext with inferred Gemini-vision fields
        populated. The spec/dossier slots remain None — those get filled
        by the canonical-dossier merge in `run_single` after this call.

        Disk cache stores the raw inferred dict (JSON-safe); the
        VisionContext wrapper is reconstructed on read.
        """
        from nano_banana.vision_describe import describe_product

        sku = product.get("sku", "unknown")

        # Check memory cache — VisionContext objects round-trip directly
        if sku in self._vision_cache:
            log.info("DESCRIBE: using cached vision for %s", sku)
            return self._vision_cache[sku]

        # Check disk cache (stores plain dict — Dossier objects aren't
        # JSON-serializable, and cached vision pre-dates the dossier merge)
        cache_dir = PROJECT_ROOT / self.config.vision_cache_dir
        cache_file = cache_dir / f"{sku}-vision.json"
        if cache_file.exists():
            try:
                desc = json.loads(cache_file.read_text())
                ctx = VisionContext(inferred=desc)
                self._vision_cache[sku] = ctx
                log.info("DESCRIBE: loaded from disk cache for %s", sku)
                return ctx
            except (json.JSONDecodeError, OSError):
                pass

        # Generate new description
        log.info("DESCRIBE: analyzing %s with vision model...", sku)
        desc = describe_product(
            self.genai,
            source_path,
            product,
            model=self.config.gemini_vision_model,
        )

        ctx = VisionContext(inferred=desc or {})
        if desc:
            self._vision_cache[sku] = ctx
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(desc, indent=2))
            log.info("DESCRIBE: cached vision for %s", sku)

        return ctx


def _build_refinement_prompt(name: str, sku: str, qa_result: TournamentResult) -> str:
    """Construct a refinement prompt that consumes the synthesis judge's fixes.

    Three tiers, strictly more informative as judge data quality improves:

    1. **Synthesis-aware** (preferred): Opus 4.7 ran successfully and
       produced consensus-filtered fixes via its `suggested_fixes` and
       severity-prioritized issues via its `issues`. We pass these
       directly. If `hallucination_veto` fired, we prepend a hard
       negative constraint — hallucinations are luxury-brand-disqualifying
       and need explicit removal direction.

    2. **Vision-pair fallback**: synthesis judge unavailable or failed.
       Fall back to `qa_result.all_fixes` (deduped union from the vision
       pair). Noisier than synthesis output but still better than
       generic.

    3. **Catchall**: no fix data at all. Use the original generic prompt.

    The model needs both negative space (what's wrong) and positive
    direction (what to do); image gen models do better with both signals.
    """
    synth = qa_result.synthesis_judge if hasattr(qa_result, "synthesis_judge") else None

    parts = [
        f"This is a {name} ({sku}) product render that scored "
        f"{qa_result.aggregate_score:.0f}/100 in QA review and needs correction."
    ]

    if synth and synth.overall > 0:
        # Tier 1 — synthesis-aware
        if getattr(synth, "hallucination_veto", False):
            parts.append(
                "CRITICAL: This render contains hallucinated decorative elements "
                "not in the spec. These must be completely removed. Do not "
                "introduce any new decorations, motifs, logos, text, or details "
                "that are not explicitly listed in the corrections below."
            )
        if synth.issues:
            issues_block = "\n".join(f"  - {issue}" for issue in synth.issues[:5])
            parts.append(f"DEFECTS PRESENT IN CURRENT RENDER:\n{issues_block}")
        if synth.suggested_fixes:
            fixes_block = "\n".join(f"  - {fix}" for fix in synth.suggested_fixes[:5])
            parts.append(f"REQUIRED CORRECTIONS:\n{fixes_block}")
        parts.append(
            "Apply these corrections precisely. Preserve all unrelated elements "
            "unchanged. Do not add any decorations, text, logos, or details "
            "beyond what is explicitly required."
        )
    elif qa_result.all_fixes:
        # Tier 2 — vision-pair union fallback
        fixes_block = "\n".join(f"  - {fix}" for fix in qa_result.all_fixes[:5])
        parts.append(f"REQUIRED CORRECTIONS:\n{fixes_block}\n\nKeep all other elements identical.")
    else:
        # Tier 3 — catchall (original generic prompt)
        parts.append(
            f"Fix the text and logo accuracy on this {name}. "
            "Make all branding crisp and legible. Keep everything else identical."
        )

    return "\n\n".join(parts)


def _find_bundle_dir(name: str, sku: str) -> Path | None:
    """Find the bundle directory by product name (primary) or SKU (fallback)."""
    bundle_root = PROJECT_ROOT / "data" / "product-bundles"
    # Primary: match by product name (directory name = product name)
    name_dir = bundle_root / name.replace("—", "-").replace("'", "").replace('"', "").strip()
    if name_dir.exists():
        return name_dir
    # Fallback: search manifests for matching SKU
    for d in bundle_root.iterdir():
        if not d.is_dir():
            continue
        manifest = d / "manifest.json"
        if manifest.exists():
            try:
                data = json.loads(manifest.read_text())
                if data.get("sku") == sku:
                    return d
            except (json.JSONDecodeError, OSError):
                continue
    return None


def _load_bundle_refs(name: str, sku: str, source_path: Path, view: str) -> list[tuple[str, Path]]:
    """Load reference images from the product bundle directory.

    Bundles are named by product name (not SKU).
    Returns list of (label, Path) tuples for generate_gemini() extra_refs.
    """
    bundle_dir = _find_bundle_dir(name, sku)
    if not bundle_dir:
        log.warning("No bundle directory for %s (%s)", name, sku)
        return []

    TAG_LABELS = {
        # Logo/patch refs EXCLUDED — they cause the model to hallucinate
        # brand text onto garments. The source photo already shows the branding.
        "source-photo": "REFERENCE — REAL PRODUCT PHOTO",
        "photo-front": "REFERENCE — REAL PRODUCT PHOTO",
        "photo-back": "REFERENCE — REAL PRODUCT PHOTO (back)",
        "techflat-front": "REFERENCE — PRODUCT FLAT",
        "techflat-back": "REFERENCE — PRODUCT FLAT (back)",
    }

    refs: list[tuple[str, Path]] = []

    # Include source/product photo ONLY — no logo or patch refs
    for tag in ("source-photo", "photo-front"):
        for f in bundle_dir.glob(f"{tag}.*"):
            if f.exists() and f != source_path:
                refs.append((TAG_LABELS.get(tag, tag), f))

    # Include techflat for the requested view
    if view == "front":
        for f in bundle_dir.glob("techflat-front.*"):
            if f.exists() and f != source_path:
                refs.append((TAG_LABELS["techflat-front"], f))
    elif view == "back":
        for f in bundle_dir.glob("techflat-back.*"):
            if f.exists() and f != source_path:
                refs.append((TAG_LABELS["techflat-back"], f))

    # Cap at 5 references
    return refs[:5]


def _source_env_file(path: Path) -> None:
    """Load environment variables from a file."""
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and value:
            os.environ.setdefault(key, value)
