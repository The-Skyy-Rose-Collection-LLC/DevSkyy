#!/usr/bin/env python3
"""
DevSkyy LLM Client Verification Script

Verifies that all 6 LLM provider clients are properly implemented and configured.

Usage:
    python scripts/verify_llm_clients.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class Colors:
    """ANSI color codes"""

    GREEN = "\033[0;32m"
    RED = "\033[0;31m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    NC = "\033[0m"


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BLUE}{'=' * 80}{Colors.NC}")
    print(f"{Colors.BLUE}{text.center(80)}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 80}{Colors.NC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.NC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.NC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.NC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.NC}")


def verify_imports():
    """Verify all LLM clients can be imported"""
    print_header("Verifying LLM Client Imports")

    clients = {
        "OpenAIClient": None,
        "AnthropicClient": None,
        "GoogleClient": None,
        "MistralClient": None,
        "CohereClient": None,
        "GroqClient": None,
    }

    all_ok = True

    try:
        from orchestration.llm_clients import (  # noqa: F401
            AnthropicClient,
            BaseLLMClient,
            CohereClient,
            CompletionResponse,
            GoogleClient,
            GroqClient,
            Message,
            MessageRole,
            MistralClient,
            OpenAIClient,
        )

        clients["OpenAIClient"] = OpenAIClient
        clients["AnthropicClient"] = AnthropicClient
        clients["GoogleClient"] = GoogleClient
        clients["MistralClient"] = MistralClient
        clients["CohereClient"] = CohereClient
        clients["GroqClient"] = GroqClient

        for name, client_class in clients.items():
            if client_class:
                print_success(f"{name} imported successfully")
            else:
                print_error(f"{name} import failed")
                all_ok = False

        # Verify base classes
        print_success("BaseLLMClient imported successfully")
        print_success("Message, MessageRole, CompletionResponse imported successfully")

    except ImportError as e:
        print_error(f"Import error: {e}")
        all_ok = False

    return all_ok, clients


def verify_environment_variables():
    """Verify environment variables are configured"""
    print_header("Verifying Environment Variables")

    env_vars = {
        "OPENAI_API_KEY": "OpenAI (GPT-4o, o1)",
        "ANTHROPIC_API_KEY": "Anthropic (Claude 3.5 Sonnet)",
        "GOOGLE_API_KEY": "Google (Gemini 1.5/2.0)",
        "MISTRAL_API_KEY": "Mistral (Large, Medium, Small)",
        "COHERE_API_KEY": "Cohere (Command R+)",
        "GROQ_API_KEY": "Groq (Llama 3.1, Mixtral)",
    }

    configured = {}

    for var, description in env_vars.items():
        value = os.getenv(var)
        configured[var] = bool(value)

        if value:
            # Mask the key for security
            masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            print_success(f"{var} is set ({description}) - {masked}")
        else:
            print_warning(f"{var} is NOT set ({description})")

    return configured


def verify_client_instantiation(clients: dict):
    """Verify clients can be instantiated"""
    print_header("Verifying Client Instantiation")

    results = {}

    for name, client_class in clients.items():
        if not client_class:
            print_error(f"{name} - Class not available")
            results[name] = False
            continue

        try:
            # Try to instantiate without API key (should not fail)
            client = client_class(api_key="test-key")
            print_success(f"{name} - Instantiated successfully")

            # Check provider attribute
            if hasattr(client, "provider"):
                print_info(f"  Provider: {client.provider}")

            # Check base_url attribute
            if hasattr(client, "base_url"):
                print_info(f"  Base URL: {client.base_url}")

            results[name] = True

        except Exception as e:
            print_error(f"{name} - Instantiation failed: {e}")
            results[name] = False

    return results


def verify_orchestrator():
    """Verify LLM Orchestrator integration"""
    print_header("Verifying LLM Orchestrator Integration")

    try:
        from orchestration import LLMOrchestrator, RoutingStrategy, TaskType

        print_success("LLMOrchestrator imported successfully")

        # Try to instantiate
        LLMOrchestrator()
        print_success("LLMOrchestrator instantiated successfully")

        # Check available task types
        print_info(f"Available task types: {', '.join([t.value for t in TaskType])}")

        # Check routing strategies
        print_info(f"Routing strategies: {', '.join([s.value for s in RoutingStrategy])}")

        return True

    except Exception as e:
        print_error(f"Orchestrator verification failed: {e}")
        return False


def verify_registry():
    """Verify LLM Registry"""
    print_header("Verifying LLM Registry")

    try:
        from orchestration import LLMRegistry, ModelProvider

        print_success("LLMRegistry imported successfully")

        registry = LLMRegistry()
        print_success("LLMRegistry instantiated successfully")

        # List all providers
        providers = [p.value for p in ModelProvider]
        print_info(f"Registered providers: {', '.join(providers)}")

        # Count total models
        total_models = len(registry.models)
        print_info(f"Total models registered: {total_models}")

        # Check available providers (with API keys)
        available = registry.get_available_providers()
        if available:
            print_success(
                f"Available providers (with API keys): {', '.join([p.value for p in available])}"
            )
        else:
            print_warning("No providers have API keys configured")

        return True

    except Exception as e:
        print_error(f"Registry verification failed: {e}")
        return False


def verify_file_structure():
    """Verify file structure"""
    print_header("Verifying File Structure")

    required_files = {
        "orchestration/llm_clients.py": "LLM client implementations",
        "orchestration/llm_orchestrator.py": "LLM orchestrator",
        "orchestration/llm_registry.py": "Model registry",
        "orchestration/__init__.py": "Package initialization",
    }

    all_ok = True

    for file_path, description in required_files.items():
        full_path = project_root / file_path
        if full_path.exists():
            # Get file size
            size = full_path.stat().st_size
            lines = len(full_path.read_text().splitlines())
            print_success(f"{file_path} exists - {description} ({lines} lines, {size:,} bytes)")
        else:
            print_error(f"{file_path} NOT found - {description}")
            all_ok = False

    return all_ok


def print_summary(results: dict):
    """Print summary of verification"""
    print_header("Verification Summary")

    total_checks = len(results)
    passed = sum(1 for v in results.values() if v)

    for check, result in results.items():
        if result:
            print_success(f"{check}: PASSED")
        else:
            print_error(f"{check}: FAILED")

    print(f"\n{Colors.BLUE}Results: {passed}/{total_checks} checks passed{Colors.NC}\n")

    if passed == total_checks:
        print_success("All verifications passed! LLM clients are fully integrated.")
        print_info("\nYou have access to 6 LLM providers:")
        print_info("  1. OpenAI (GPT-4o, GPT-4o-mini, o1-preview, o1-mini)")
        print_info("  2. Anthropic (Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku)")
        print_info("  3. Google (Gemini 1.5 Pro, Gemini 1.5 Flash, Gemini 2.0 Flash)")
        print_info("  4. Mistral (Mistral Large, Medium, Small, Codestral)")
        print_info("  5. Cohere (Command R+, Command R)")
        print_info("  6. Groq (Llama 3.1 70B, Llama 3.1 8B, Mixtral 8x7B)")
        print_info("\nNext steps:")
        print_info("  1. Set environment variables for the providers you want to use")
        print_info("  2. Test with: python -m orchestration.llm_clients")
        print_info("  3. Use LLMOrchestrator for intelligent model selection")
        return 0
    else:
        print_error("Some verifications failed. Please review the errors above.")
        return 1


def main():
    """Run all verifications"""
    print_header("DevSkyy LLM Client Verification Suite")

    results = {}

    # Verify imports
    imports_ok, clients = verify_imports()
    results["LLM Client Imports"] = imports_ok

    # Verify environment variables (informational only, not required)
    verify_environment_variables()
    # Don't fail if no env vars are set - they're optional
    results["Environment Variables (Optional)"] = True

    # Verify client instantiation
    if imports_ok:
        instantiation = verify_client_instantiation(clients)
        results["Client Instantiation"] = all(instantiation.values())
    else:
        results["Client Instantiation"] = False

    # Verify orchestrator
    results["LLM Orchestrator"] = verify_orchestrator()

    # Verify registry
    results["LLM Registry"] = verify_registry()

    # Verify file structure
    results["File Structure"] = verify_file_structure()

    # Print summary
    return print_summary(results)


if __name__ == "__main__":
    sys.exit(main())
