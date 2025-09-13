Project Familiarization
	•	Parse README.md and surface missing setup instructions (dependencies, env vars, required services).
	•	Crawl through codebase and auto-generate a high-level architecture map (modules, dependencies, relationships).
	•	Flag any unused dependencies or imports.

2. Code Quality & Standards
	•	Enforce consistent formatting with Prettier/ESLint (JS/TS) or Black/Flake8 (Python) depending on detected languages.
	•	Scan for TODO/FIXME comments and consolidate into a task report.
	•	Suggest refactors for repeated logic blocks (e.g. DRY violations).

3. Security & Secrets Management
	•	Detect hard-coded secrets or API keys.
	•	Propose .env.example updates to reflect required environment variables.
	•	Check for outdated or vulnerable npm/pip packages with automated audit.

4. Documentation Enhancement
	•	Auto-generate or refresh API documentation using docstrings + OpenAPI spec (if backend endpoints exist).
	•	Suggest adding inline comments for complex functions with >15 lines.
	•	Create a CONTRIBUTING.md with coding guidelines and workflow steps.

5. Testing Infrastructure
	•	Identify untested files/functions.
	•	Auto-generate starter unit tests for key services/utilities.
	•	Set up GitHub Actions CI workflow to run tests on PRs.

6. Developer Experience
	•	Add boilerplate CLI commands (e.g. dev:setup, dev:start, dev:test).
	•	Generate Dockerfile and docker-compose setup for local dev parity.
	•	Propose VSCode launch configurations for debugging.

7. Advanced Copilot Hacks
	•	Generate function usage examples for each export in the repo.
	•	Suggest performance optimizations (async/await, caching, batching calls).
	•	Detect places where TypeScript types could eliminate runtime errors.
	•	Draft code snippets to demonstrate integration with external APIs (GitHub, Slack, etc.).
