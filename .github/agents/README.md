# GitHub Task Agents for DevSkyy

These agent definitions power GitHub's task agent runtime and are focused on stabilizing the Python backend test suite. The repo currently experiences `ModuleNotFoundError: fastapi` when running the default pytest entrypoint, so both agents orchestrate dependency repair and targeted smoke verification.

## Available agents

### python-dependency-doctor.json
* **Purpose:** Triage missing Python dependencies (such as FastAPI) and update requirement files consistently.
* **Typical trigger:** `/agent run python-dependency-doctor` comment or manual workflow dispatch.
* **Workflow summary:**
  1. Install project dependencies.
  2. Reproduce the failing pytest node to capture the stack trace.
  3. Patch the relevant requirements files with the missing dependency pin.
  4. Re-run pytest to confirm the ModuleNotFoundError has been resolved.

### python-test-smoke.json
* **Purpose:** Execute a fast regression suite once dependencies have been corrected.
* **Typical trigger:** `/agent run python-test-smoke` or applying the `run-python-smoke` label to a pull request.
* **Workflow summary:**
  1. Install development dependencies.
  2. Seed SQLite fixtures when needed and enable the lightweight test configuration.
  3. Run the targeted smoke suites (`tests/test_sqlite_setup.py`, `tests/test_quality_processing.py`).
  4. Report results back to the invoking issue or pull request.

## Usage notes

* Both agents assume Python 3.11 and rely on `pip` for dependency management.
* Commands executed by the agents are designed to operate inside the repository root.
* When run through manual dispatch, additional pytest arguments can be supplied via `extra_pytest_args` input.
* Make sure to merge dependency updates and test fixes in the same pull request to keep the suite green.
