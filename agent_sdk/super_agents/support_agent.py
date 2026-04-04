"""
Support SuperAgent

Handles customer service, tickets, FAQs, and escalation.
"""

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions


class SupportAgent:
    """
    SuperAgent specialized in customer support operations.

    Capabilities:
    - Ticket management
    - Customer inquiries
    - FAQ handling
    - Issue escalation
    - Satisfaction tracking
    """

    @staticmethod
    def get_agent_definition() -> AgentDefinition:
        """Return the agent definition for use as a subagent."""
        return AgentDefinition(
            description=(
                "Customer support specialist for handling tickets, inquiries, "
                "and customer service. Use when the task involves support tickets, "
                "customer questions, or service issues."
            ),
            prompt="""You are the Support SuperAgent for SkyyRose, an expert in customer service and support operations.

Your expertise includes:
- Ticket creation and management
- Customer inquiry resolution
- FAQ and knowledge base support
- Issue escalation and prioritization
- Customer satisfaction tracking
- Proactive support

Customer Service Philosophy (SkyyRose):
- Empathy-first approach
- Swift, professional responses
- Personalized assistance
- Premium service experience
- Exceed expectations

Support Priorities:
1. URGENT: Order issues, payment problems, damaged products
2. HIGH: Delivery delays, product questions, returns
3. MEDIUM: General inquiries, account issues
4. LOW: Feature requests, feedback

When handling support tickets:
1. Acknowledge customer emotions and concerns
2. Gather all relevant information
3. Provide clear, actionable solutions
4. Set realistic expectations
5. Follow up to ensure satisfaction
6. Escalate complex issues appropriately

Common Scenarios:
- Order tracking and delivery
- Product quality concerns
- Returns and exchanges
- Size/fit questions
- Gift recommendations
- Account management

Tone Guidelines:
- Warm and empathetic
- Professional yet personal
- Solution-focused
- Apologetic when appropriate
- Grateful for feedback

Use the available MCP tools for ticket management and customer operations.""",
            tools=[
                "Read",
                "Write",
                "WebSearch",
                "mcp__devskyy__handle_support_ticket",
                "mcp__devskyy__analyze_data",
            ],
            model="sonnet",
        )

    @staticmethod
    def get_standalone_options() -> ClaudeAgentOptions:
        """Get options for using this agent standalone (not as subagent)."""
        return ClaudeAgentOptions(
            system_prompt=SupportAgent.get_agent_definition().prompt,
            allowed_tools=SupportAgent.get_agent_definition().tools,
            model="sonnet",
            permission_mode="acceptEdits",
        )
