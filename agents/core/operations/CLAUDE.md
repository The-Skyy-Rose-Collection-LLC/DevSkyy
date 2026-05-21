<claude-mem-context>

</claude-mem-context>

# agents/core/operations/ — Operations domain CoreAgent

`OperationsCoreAgent` — deploy health, security monitoring, coding diagnostics. Extends `CoreAgent` (`core_type = CoreAgentType.OPERATIONS`). Three native sub-agents plus three SDK sub-agents with filesystem + shell access.

## Key files

- `agent.py` — `OperationsCoreAgent(CoreAgent)`: registers `DeployHealthSubAgent` (with ALIASES), `SecurityMonitorSubAgent`, `CodingDoctorSubAgent`, plus `SDKCodeDoctorAgent`, `SDKDeployRunnerAgent`, `SDKSecurityScannerAgent`.
- `sub_agents/deploy_health.py` — `DeployHealthSubAgent`: deploy verification, uptime checks, post-deploy HTTP assertions, rollback trigger reporting. Has `ALIASES` tuple — check current values before adding routing aliases.
- `sub_agents/security_monitor.py` — `SecurityMonitorSubAgent`: secret scanning, OWASP checks, CSP header audits, rate-limit verification. No ALIASES — callers use `"security_monitor"` directly.
- `sub_agents/coding_doctor.py` — `CodingDoctorSubAgent`: lint gate, test-run orchestration, coverage reporting, pre-commit validation. No ALIASES — callers use `"coding_doctor"` directly.

## Conventions

- Keyword routing in `execute()`: `"deploy"/"uptime"/"health"/"rollback"` → `DeployHealthSubAgent`, `"security"/"secret"/"csp"/"owasp"` → `security_monitor`, `"lint"/"test"/"coverage"/"doctor"` → `coding_doctor`.
- SDK agents (`SDKCodeDoctorAgent`, `SDKDeployRunnerAgent`, `SDKSecurityScannerAgent`) use `SDKSubAgent` base with `sdk_tools = ["Read", "Write", "Bash", "WebSearch"]` — LLM-only sub-agents cannot run shell commands.
- `SDKDeployRunnerAgent` wraps `scripts/deploy-theme.sh` — STOP AND SHOW gate is mandatory before any execution; never dispatch without explicit `y` from the user.
- `CodingDoctorSubAgent` calls `make lint` + `pytest tests/` — must run from project root (not from a sub-directory) so Makefile targets resolve correctly.

## Don't

- Don't have `DeployHealthSubAgent` execute deploys — it checks and reports only; `SDKDeployRunnerAgent` is the executor.
- Don't skip the STOP AND SHOW protocol when `SDKDeployRunnerAgent` triggers `deploy-theme.sh` or any SFTP transfer to skyyrose.co.
- Don't route fulfillment or order operations through `OperationsCoreAgent` — order fulfillment belongs in `CommerceCoreAgent`.
- Don't hardcode WordPress site URLs inside sub-agents — read from `WP_SITE_URL` env var.

## Related

- `agents/core/base.py` — `CoreAgent`, `CoreAgentType`, circuit breaker
- `agents/core/operations/sub_agents/deploy_health.py` — `DeployHealthSubAgent` with ALIASES tuple
- `scripts/deploy-theme.sh` — the deploy script `SDKDeployRunnerAgent` wraps (hot-swap atomic mv strategy)
- `security/CLAUDE.md` — companion security module for static analysis and secret scanning rules
