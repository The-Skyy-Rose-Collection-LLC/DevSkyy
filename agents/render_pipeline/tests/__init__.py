"""Mock-based unit tests for the RenderPipeline tool functions.

Runs on every PR — no paid API calls, no google-adk required. Tests verify:
  - State writes happen with the right keys
  - Return shape matches the contract documented in tools/__init__.py
  - Error paths handle missing prerequisites gracefully
  - Learning recorders fire when expected
"""
