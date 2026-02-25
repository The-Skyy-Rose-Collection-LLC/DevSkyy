#!/usr/bin/env python3
"""
DevSkyy Pipeline Verification Script

Verifies both imagery pipelines before mascot generation:
  Pipeline 1: Visual Generation (agents/visual_generation/)
  Pipeline 2: Elite Web Builder (agents/elite_web_builder/)

Usage:
    python3 scripts/verify_pipelines.py
"""

import importlib
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class Colors:
    GREEN = "\033[0;32m"
    RED = "\033[0;31m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    NC = "\033[0m"


def header(text: str):
    print(f"\n{Colors.BLUE}{'=' * 80}{Colors.NC}")
    print(f"{Colors.BLUE}{text.center(80)}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 80}{Colors.NC}\n")


def ok(text: str):
    print(f"  {Colors.GREEN}[PASS]{Colors.NC} {text}")


def fail(text: str):
    print(f"  {Colors.RED}[FAIL]{Colors.NC} {text}")


def warn(text: str):
    print(f"  {Colors.YELLOW}[WARN]{Colors.NC} {text}")


def info(text: str):
    print(f"  {Colors.CYAN}[INFO]{Colors.NC} {text}")


def load_env():
    """Load .env files in priority order (same as elite_web_builder/run.py)."""
    try:
        from dotenv import load_dotenv
        for p in ["skyyrose/.env", ".env", "gemini/.env"]:
            full = project_root / p
            if full.exists():
                load_dotenv(full, override=True)
    except ImportError:
        pass


def check_api_keys() -> dict[str, bool]:
    """Check which API keys are available."""
    header("API Key Verification")
    keys = {
        "ANTHROPIC_API_KEY": "Anthropic (Claude Opus/Sonnet/Haiku)",
        "GEMINI_API_KEY": "Google Gemini (Design System + Performance)",
        "GOOGLE_API_KEY": "Google (Imagen 3, Veo 2, Gemini Native)",
        "OPENAI_API_KEY": "OpenAI (GPT-4o, SEO Content)",
        "XAI_API_KEY": "xAI Grok-3 (QA agent, optional)",
        "HUGGINGFACE_API_KEY": "HuggingFace (FLUX.1, optional)",
        "REPLICATE_API_TOKEN": "Replicate (LoRA, optional)",
    }
    results = {}
    for var, desc in keys.items():
        val = os.getenv(var, "")
        results[var] = bool(val)
        if val:
            masked = f"{val[:8]}...{val[-4:]}" if len(val) > 12 else "***"
            ok(f"{var}: {masked} ({desc})")
        else:
            warn(f"{var}: NOT SET ({desc})")
    return results


def verify_visual_generation() -> tuple[bool, list[str]]:
    """Verify Pipeline 1: Visual Generation."""
    header("Pipeline 1: Visual Generation (agents/visual_generation/)")
    issues = []
    all_ok = True

    # Check files exist
    required_files = [
        "agents/visual_generation/__init__.py",
        "agents/visual_generation/visual_generation.py",
        "agents/visual_generation/reference_manager.py",
        "agents/visual_generation/prompt_optimizer.py",
        "agents/visual_generation/conversation_editor.py",
        "agents/visual_generation/gemini_native.py",
    ]
    for f in required_files:
        p = project_root / f
        if p.exists():
            ok(f"{f} ({p.stat().st_size:,} bytes)")
        else:
            fail(f"{f} NOT FOUND")
            issues.append(f"Missing: {f}")
            all_ok = False

    # Check imports
    print()
    try:
        from agents.visual_generation import (  # noqa: F401
            VisualGenerationRouter,
            VisualProvider,
            GenerationType,
            GenerationRequest,
            GenerationResult,
            GoogleImagenClient,
            GoogleVeoClient,
            HuggingFaceFluxClient,
            ReplicateLoRAClient,
            ConversationEditor,
            SKYYROSE_BRAND_DNA,
        )
        ok("All core classes imported successfully")

        # Verify enums
        providers = [p.value for p in VisualProvider]
        info(f"Visual providers: {', '.join(providers)}")
        gen_types = [g.value for g in GenerationType]
        info(f"Generation types: {', '.join(gen_types)}")
    except ImportError as e:
        fail(f"Import error: {e}")
        issues.append(f"Import error: {e}")
        all_ok = False

    # Check reference image
    print()
    ref_path = project_root / "assets/branding/mascot/skyyrose-mascot-reference.png"
    if ref_path.exists():
        size_mb = ref_path.stat().st_size / (1024 * 1024)
        ok(f"Mascot reference image: {size_mb:.1f} MB")
    else:
        fail("Mascot reference image NOT FOUND")
        issues.append("Missing: assets/branding/mascot/skyyrose-mascot-reference.png")
        all_ok = False

    # Check ReferenceImageManager
    try:
        from agents.visual_generation.reference_manager import (  # noqa: F401
            ReferenceImageManager,
            ThoughtSignatureManager,
            ReferenceImage,
            ReferenceType,
        )
        ok("ReferenceImageManager imported (validates up to 14 images)")
    except ImportError as e:
        fail(f"ReferenceImageManager import: {e}")
        issues.append(f"ReferenceImageManager: {e}")
        all_ok = False

    # Check prompt optimizer
    try:
        from agents.visual_generation.prompt_optimizer import (  # noqa: F401
            GeminiPromptOptimizer,
            GeminiTreeOfThoughtsVisual,
            GeminiNegativePromptEngine,
            CollectionPromptBuilder,
        )
        ok("GeminiPromptOptimizer imported (4 prompt patterns)")
    except ImportError as e:
        fail(f"Prompt optimizer import: {e}")
        issues.append(f"Prompt optimizer: {e}")
        all_ok = False

    # Check gemini native
    try:
        from agents.visual_generation.gemini_native import (  # noqa: F401
            GeminiNativeImageClient,
            GeminiFlashImageClient,
            GeminiProImageClient,
        )
        ok("Gemini native clients imported (Flash + Pro)")
    except ImportError as e:
        fail(f"Gemini native import: {e}")
        issues.append(f"Gemini native: {e}")
        all_ok = False

    # Dry instantiation of router
    print()
    try:
        router = VisualGenerationRouter()
        ok(f"VisualGenerationRouter instantiated (history: {len(router.get_history())})")
    except Exception as e:
        fail(f"Router instantiation: {e}")
        issues.append(f"Router: {e}")
        all_ok = False

    return all_ok, issues


def _run_in_ewb(code: str) -> tuple[bool, str]:
    """Run Python code with EWB root as CWD (matching how run.py works)."""
    import subprocess
    ewb_root = str(project_root / "agents" / "elite_web_builder")
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ewb_root,
        capture_output=True,
        text=True,
        timeout=15,
    )
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


def verify_elite_web_builder() -> tuple[bool, list[str]]:
    """Verify Pipeline 2: Elite Web Builder."""
    header("Pipeline 2: Elite Web Builder (agents/elite_web_builder/)")
    issues = []
    all_ok = True

    # Check core files
    required_files = [
        "agents/elite_web_builder/__init__.py",
        "agents/elite_web_builder/run.py",
        "agents/elite_web_builder/director.py",
        "agents/elite_web_builder/agents/provider_adapters.py",
        "agents/elite_web_builder/core/model_router.py",
        "agents/elite_web_builder/config/provider_routing.json",
        "agents/elite_web_builder/config/quality_gates.json",
    ]
    for f in required_files:
        p = project_root / f
        if p.exists():
            ok(f"{f} ({p.stat().st_size:,} bytes)")
        else:
            fail(f"{f} NOT FOUND")
            issues.append(f"Missing: {f}")
            all_ok = False

    # Check imports via subprocess (EWB uses CWD-relative absolute imports)
    print()
    passed, output = _run_in_ewb(
        "from agents.provider_adapters import get_adapter, LLMMessage, LLMResponse; "
        "from agents.base import AgentRole, AgentSpec; "
        "print('OK')"
    )
    if passed and "OK" in output:
        ok("Core agent classes imported")
    else:
        fail(f"Agent imports: {output}")
        issues.append(f"Agent imports: {output}")
        all_ok = False

    # Check model router
    passed, output = _run_in_ewb(
        "from core.model_router import ModelRouter, ProviderStatus, RoutingConfig; "
        "print('OK')"
    )
    if passed and "OK" in output:
        ok("ModelRouter imported (health-aware routing)")
    else:
        fail(f"ModelRouter import: {output}")
        issues.append(f"ModelRouter: {output}")
        all_ok = False

    # Check routing config
    import json
    routing_path = project_root / "agents/elite_web_builder/config/provider_routing.json"
    if routing_path.exists():
        config = json.loads(routing_path.read_text())
        routes = config.get("routes", config.get("agents", {}))
        fallbacks = list(config.get("fallbacks", {}).keys())
        ok(f"Routing config: {len(routes)} agents, {len(fallbacks)} fallback chains")
        for agent, spec in routes.items():
            info(f"  {agent}: {spec['provider']}/{spec['model']}")
    else:
        fail("Routing config missing")
        issues.append("Missing routing config")
        all_ok = False

    # Check provider adapters (dry — no API calls)
    print()
    providers_to_test = {
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "xai": "XAI_API_KEY",
    }
    for provider, env_var in providers_to_test.items():
        passed, output = _run_in_ewb(
            f"from agents.provider_adapters import get_adapter; "
            f"a = get_adapter('{provider}'); "
            f"print(type(a).__name__)"
        )
        has_key = bool(os.getenv(env_var, ""))
        key_status = "key present" if has_key else "no key (will fail on call)"
        if passed and output:
            adapter_name = output.split("\n")[-1].strip()
            ok(f"{provider} adapter: {adapter_name} ({key_status})")
        else:
            fail(f"{provider} adapter: {output}")
            issues.append(f"{provider} adapter: {output}")
            all_ok = False

    # Check specialist agents
    print()
    passed, output = _run_in_ewb(
        "from agents.accessibility import ACCESSIBILITY_SPEC; "
        "from agents.frontend_dev import FRONTEND_DEV_SPEC; "
        "from agents.backend_dev import BACKEND_DEV_SPEC; "
        "from agents.design_system import DESIGN_SYSTEM_SPEC; "
        "from agents.performance import PERFORMANCE_SPEC; "
        "from agents.seo_content import SEO_CONTENT_SPEC; "
        "from agents.qa import QA_SPEC; "
        "specs = [DESIGN_SYSTEM_SPEC, FRONTEND_DEV_SPEC, BACKEND_DEV_SPEC, "
        "ACCESSIBILITY_SPEC, PERFORMANCE_SPEC, SEO_CONTENT_SPEC, QA_SPEC]; "
        "print('\\n'.join(f'{s.role.value}: {s.name}' for s in specs))"
    )
    if passed and output:
        lines = [l for l in output.strip().split("\n") if ":" in l]
        ok(f"Specialist agents loaded: {len(lines)} total")
        for line in lines:
            info(f"  {line}")
    else:
        fail(f"Specialist agents: {output}")
        issues.append(f"Specialist agents: {output}")
        all_ok = False

    return all_ok, issues


def verify_mascot_integration():
    """Verify mascot system files are in place."""
    header("Mascot System Integration")
    checks = {
        "frontend/app/admin/mascot/page.tsx": "Admin mascot page",
        "frontend/app/api/mascot/route.ts": "Mascot API route",
        "wordpress-theme/skyyrose-flagship/template-parts/mascot.php": "Walking mascot widget",
        "wordpress-theme/skyyrose-flagship/assets/css/mascot.css": "Mascot styles",
        "wordpress-theme/skyyrose-flagship/assets/js/mascot.js": "Mascot interactivity",
        "assets/branding/mascot/skyyrose-mascot-reference.png": "Reference image",
    }
    all_ok = True
    for path, desc in checks.items():
        p = project_root / path
        if p.exists():
            ok(f"{desc}: {path}")
        else:
            fail(f"{desc}: {path} NOT FOUND")
            all_ok = False
    return all_ok


def main():
    header("DevSkyy Pipeline Verification Suite")
    info("Verifying both imagery pipelines before mascot generation")
    print()

    load_env()
    api_keys = check_api_keys()

    vg_ok, vg_issues = verify_visual_generation()
    ewb_ok, ewb_issues = verify_elite_web_builder()
    mascot_ok = verify_mascot_integration()

    # Summary
    header("VERIFICATION SUMMARY")
    results = {
        "Pipeline 1 — Visual Generation": vg_ok,
        "Pipeline 2 — Elite Web Builder": ewb_ok,
        "Mascot System Integration": mascot_ok,
    }

    required_keys = ["ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"]
    missing_required = [k for k in required_keys if not api_keys.get(k)]

    for name, passed in results.items():
        if passed:
            ok(f"{name}: ALL CHECKS PASSED")
        else:
            fail(f"{name}: HAS ISSUES")

    print()
    if missing_required:
        warn(f"Missing required API keys: {', '.join(missing_required)}")
        warn("Set these in .env before running actual generation")
    else:
        ok("All required API keys are set")

    all_issues = vg_issues + ewb_issues
    if all_issues:
        print(f"\n  {Colors.RED}Issues found:{Colors.NC}")
        for issue in all_issues:
            print(f"    - {issue}")
        return 1

    print(f"\n  {Colors.GREEN}Both pipelines verified. Ready for mascot generation.{Colors.NC}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
