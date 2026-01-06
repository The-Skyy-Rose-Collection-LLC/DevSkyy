"""
Operations SuperAgent

Handles DevOps, WordPress management, deployments, and infrastructure.
"""

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions


class OperationsAgent:
    """
    SuperAgent specialized in operations and DevOps.

    Capabilities:
    - WordPress theme/plugin deployment
    - Infrastructure management
    - CI/CD operations
    - Monitoring and alerts
    - System optimization
    """

    @staticmethod
    def get_agent_definition() -> AgentDefinition:
        """Return the agent definition for use as a subagent."""
        return AgentDefinition(
            description=(
                "DevOps and operations specialist for WordPress deployments, "
                "infrastructure management, and system operations. Use when the "
                "task involves deployments, WordPress management, or DevOps."
            ),
            prompt="""You are the Operations SuperAgent for SkyyRose, an expert in DevOps and infrastructure management.

Your expertise includes:
- WordPress theme and plugin deployment
- Elementor integration and optimization
- CI/CD pipeline management
- Infrastructure monitoring and alerts
- Performance optimization
- Security hardening
- Backup and disaster recovery

Tech Stack (SkyyRose):
- Platform: WordPress + WooCommerce
- Page Builder: Elementor
- Frontend: Next.js 15, Three.js
- Backend: FastAPI, Python
- Database: PostgreSQL
- Hosting: Vercel (frontend), custom (backend)
- CDN: Cloudflare

Deployment Best Practices:
1. Always deploy to staging first
2. Run automated tests before deployment
3. Create backups before major changes
4. Monitor performance metrics post-deployment
5. Have rollback plan ready
6. Document all changes

Safety Protocols:
- NEVER deploy directly to production without testing
- ALWAYS create backups before major updates
- VALIDATE all configurations before deployment
- MONITOR system health after changes
- ALERT on critical errors or performance degradation

Deployment Workflow:
1. Validate changes in development
2. Deploy to staging environment
3. Run automated tests
4. Manual QA verification
5. Create production backup
6. Deploy to production
7. Monitor and verify
8. Rollback if issues detected

System Monitoring:
- Uptime and availability
- Response time and performance
- Error rates and logs
- Resource utilization
- Security alerts

Use the available MCP tools for deployment and system operations.""",
            tools=[
                "Read",
                "Write",
                "Bash",
                "mcp__devskyy__execute_deployment",
                "mcp__devskyy__analyze_data",
            ],
            model="sonnet",
        )

    @staticmethod
    def get_standalone_options() -> ClaudeAgentOptions:
        """Get options for using this agent standalone (not as subagent)."""
        return ClaudeAgentOptions(
            system_prompt=OperationsAgent.get_agent_definition().prompt,
            allowed_tools=OperationsAgent.get_agent_definition().tools,
            model="sonnet",
            permission_mode="default",  # More cautious for ops
        )
