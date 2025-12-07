# DevSkyy Repository - File Map (Current)
**Generated:** 2025-12-07

IMPORTANT: This repository snapshot contains only the application entrypoint (main.py) used for packaging/testing in this workspace. Many architecture docs reference a full multi-file project (agents, api/, ml/, etc.) — main.py performs conditional imports and will work when those optional modules are present. The comprehensive repository map in other published docs describes the full product but is NOT accurate for this trimmed repository snapshot.

## Present files in this repository snapshot
- main.py

## Notes
- main.py includes graceful ImportError handling for numerous optional subsystems (agents, ml, monitoring, webhooks, etc.). Those modules may exist in other branches or the full product release, but they are not part of this minimal snapshot.
- If you expect the full project layout (agent/, api/, ml/, security/, etc.), obtain the full repository or switch to the integration branch that contains all modules.

## Recommendation for documentation authors
- Mark architecture docs as describing the full product (not the trimmed snapshot) and add a top-level note explaining that this repo snapshot may only contain main.py and that features are conditionally imported at runtime.
