"""
Test package marker for agents-focused suites.

Having this file ensures pytest assigns unique module names, preventing
import mismatches when similarly named test files exist in different
directories (e.g., test_orchestrator suites).
"""
