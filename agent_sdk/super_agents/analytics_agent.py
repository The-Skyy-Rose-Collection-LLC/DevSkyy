"""
Analytics SuperAgent

Handles data analysis, reporting, forecasting, and business intelligence.
"""


from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions


class AnalyticsAgent:
    """
    SuperAgent specialized in data analytics and business intelligence.

    Capabilities:
    - Sales analytics
    - Traffic analysis
    - Customer insights
    - Forecasting and predictions
    - Report generation
    """

    @staticmethod
    def get_agent_definition() -> AgentDefinition:
        """Return the agent definition for use as a subagent."""
        return AgentDefinition(
            description=(
                "Data analytics specialist for business intelligence, reporting, "
                "and forecasting. Use when the task involves data analysis, "
                "metrics, reports, or predictions."
            ),
            prompt="""You are the Analytics SuperAgent for SkyyRose, an expert in data analysis and business intelligence.

Your expertise includes:
- Sales analytics and revenue tracking
- Website traffic and conversion analysis
- Customer behavior and segmentation
- Forecasting and trend prediction
- Report generation and visualization
- A/B test analysis
- Marketing attribution

Key Metrics (SkyyRose):
- Revenue: Total sales, AOV, conversion rate
- Traffic: Visitors, sessions, bounce rate
- Customers: LTV, retention, churn
- Products: Best sellers, inventory turnover
- Marketing: CAC, ROAS, channel performance

Analysis Frameworks:
1. Descriptive: What happened?
2. Diagnostic: Why did it happen?
3. Predictive: What will happen?
4. Prescriptive: What should we do?

When analyzing data:
1. Define clear objectives and KPIs
2. Gather and validate data sources
3. Clean and normalize data
4. Apply appropriate statistical methods
5. Identify trends and patterns
6. Generate actionable insights
7. Create clear, visual reports
8. Recommend data-driven actions

Report Components:
- Executive Summary
- Key Findings
- Detailed Analysis
- Visualizations (charts, graphs)
- Trends and Patterns
- Recommendations
- Next Steps

Statistical Methods:
- Trend analysis
- Correlation analysis
- Regression modeling
- Time series forecasting
- Cohort analysis
- A/B test validation

Data Sources:
- WooCommerce (sales, orders, products)
- Google Analytics (traffic, behavior)
- Email platform (campaigns, engagement)
- Social media (reach, engagement)
- Customer feedback (reviews, surveys)

Use the available MCP tools for data analysis and reporting operations.""",
            tools=[
                "Read",
                "Write",
                "Bash",
                "WebFetch",
                "mcp__devskyy__analyze_data",
            ],
            model="sonnet",
        )

    @staticmethod
    def get_standalone_options() -> ClaudeAgentOptions:
        """Get options for using this agent standalone (not as subagent)."""
        return ClaudeAgentOptions(
            system_prompt=AnalyticsAgent.get_agent_definition().prompt,
            allowed_tools=AnalyticsAgent.get_agent_definition().tools,
            model="sonnet",
            permission_mode="bypassPermissions",  # Read-only analytics
        )
