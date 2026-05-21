<claude-mem-context>

</claude-mem-context>

# agents/core/operations/sub_agents/ — Operations sub-agents

Three sub-agents registered by `OperationsCoreAgent`. All extend `SubAgent` with `parent_type = CoreAgentType.OPERATIONS`.

## Key files

- `deploy_health.py` — `DeployHealthSubAgent`: deployment orchestration and health monitoring. Consolidates `deployment_manager` and `health_checker`. `ALIASES = ("deployment_manager", "health_checker")`. 8 capabilities: `deploy`, `rollback`, `blue_green`, `canary_release`, `health_check`, `uptime_monitor`, `endpoint_probe`, `resource_usage`. Stack scope: FastAPI on Vercel (serverless), WordPress on shared hosting, Next.js frontend on Vercel.
- `security_monitor.py` — `SecurityMonitorSubAgent`: vulnerability scanning and compliance. `name = "security_monitor"` — no ALIASES. 4 capabilities: `scan_vulnerabilities`, `update_dependencies`, `compliance_report`, `auto_patch`. Returns findings with CRITICAL/HIGH/MEDIUM/LOW severity levels. Scope includes OWASP Top 10, PCI-DSS (WooCommerce), GDPR (EU customers).
- `coding_doctor.py` — `CodingDoctorSubAgent`: code quality analysis and lint-fix. `name = "coding_doctor"` — no ALIASES. 4 capabilities: `lint_fix`, `type_check`, `code_review`, `health_report`. Standards: ruff + mypy + black (Python), ESLint + TypeScript strict (JS/TS). Returns fixes with file paths and line numbers.

## Conventions

- All three classes set `parent_type = CoreAgentType.OPERATIONS`.
- `DeployHealthSubAgent.ALIASES = ("deployment_manager", "health_checker")` — used by parent at registration time. Do not change without updating `OperationsCoreAgent._register_sub_agents()` callers.
- `DeployHealthSubAgent` reports deploy plans and checks — it does NOT execute deploys. Execution is `SDKDeployRunnerAgent`'s responsibility (SDK sub-agent with shell access).
- `CodingDoctorSubAgent` is an LLM-only sub-agent — it cannot run `make lint` itself. Lint execution requires `SDKCodeDoctorAgent` (SDK variant with `Bash` tool).
- `SecurityMonitorSubAgent` findings at CRITICAL severity must block the task and surface to the user — do not auto-patch CRITICAL findings without STOP AND SHOW.

## Don't

- Don't merge `security_monitor.py` and `coding_doctor.py` — security scanning and code quality are audited independently.
- Don't add WooCommerce or WordPress write operations to any of these sub-agents — they are read/analyze only.
- Don't raise raw `RuntimeError` — use exception classes from `agents/errors.py`.

## Related

- `agents/core/operations/agent.py` — parent that registers these sub-agents and the SDK variants
- `agents/core/base.py` — `SubAgent` base class
- `security/CLAUDE.md` — static analysis rules and secret scanning policy
- `scripts/deploy-theme.sh` — the script that `SDKDeployRunnerAgent` wraps (not called by these LLM-only sub-agents)
