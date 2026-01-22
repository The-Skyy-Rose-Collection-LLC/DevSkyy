"""
CrewAI Integration
==================

Integration with CrewAI v1.6.1 - Role-based agent collaboration framework.

Features:
- Role-based agent teams (crews)
- Task delegation and execution
- Sequential and hierarchical workflows
- Memory and learning
- Tool integration

Reference: https://docs.crewai.com/
"""

import logging
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from adk.base import (
    ADKProvider,
    AgentConfig,
    AgentResult,
    AgentStatus,
    BaseDevSkyyAgent,
    agent_factory,
    estimate_cost,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CrewAI Role Definitions for SkyyRose
# =============================================================================


class AgentRole(BaseModel):
    """Role definition for a crew member"""

    role: str = Field(..., description="Agent's role title")
    goal: str = Field(..., description="Agent's primary goal")
    backstory: str = Field(..., description="Agent's backstory and expertise")
    tools: list[str] = Field(default_factory=list, description="Available tools")
    allow_delegation: bool = Field(True, description="Can delegate to other agents")
    verbose: bool = Field(False, description="Verbose output")


class TaskDefinition(BaseModel):
    """Task definition for crew execution"""

    description: str = Field(..., description="Task description")
    expected_output: str = Field(..., description="Expected output format")
    agent_role: str = Field(..., description="Role of agent to execute")
    context: list[str] = Field(default_factory=list, description="Context from other tasks")
    async_execution: bool = Field(False, description="Execute asynchronously")


# Pre-defined roles for SkyyRose
SKYYROSE_ROLES = {
    "brand_strategist": AgentRole(
        role="Brand Strategist",
        goal="Develop and maintain SkyyRose's luxury streetwear brand identity",
        backstory="""You are a senior brand strategist with 15 years of experience
        in luxury fashion. You've worked with top brands like Off-White, Fear of God,
        and Balenciaga. You understand the intersection of streetwear and luxury,
        and how to create emotional connections with customers.""",
        tools=["web_search", "trend_analysis"],
        allow_delegation=True,
    ),
    "content_creator": AgentRole(
        role="Content Creator",
        goal="Create compelling content that resonates with SkyyRose's audience",
        backstory="""You are a creative content specialist who excels at storytelling
        for luxury brands. You understand social media algorithms, SEO, and how to
        craft messages that drive engagement and conversions.""",
        tools=["image_generator", "copywriter"],
        allow_delegation=False,
    ),
    "ecommerce_analyst": AgentRole(
        role="E-commerce Analyst",
        goal="Optimize SkyyRose's online store performance and conversions",
        backstory="""You are a data-driven e-commerce expert with deep knowledge
        of WooCommerce, conversion optimization, and customer journey analysis.
        You've helped brands achieve 200%+ revenue growth.""",
        tools=["analytics", "ab_testing", "woocommerce"],
        allow_delegation=True,
    ),
    "customer_advocate": AgentRole(
        role="Customer Success Advocate",
        goal="Ensure exceptional customer experiences at every touchpoint",
        backstory="""You are passionate about customer satisfaction. You understand
        luxury customer expectations and know how to turn complaints into loyalty.
        You prioritize the human element in every interaction.""",
        tools=["crm", "email", "chat"],
        allow_delegation=False,
    ),
    "tech_lead": AgentRole(
        role="Technical Lead",
        goal="Maintain and improve SkyyRose's technical infrastructure",
        backstory="""You are a full-stack engineer specializing in e-commerce
        platforms. You have expertise in WordPress, WooCommerce, Python, and
        AI integration. You ensure systems are secure, fast, and scalable.""",
        tools=["code_executor", "wordpress_api", "deployment"],
        allow_delegation=True,
    ),
    "creative_director": AgentRole(
        role="Creative Director",
        goal="Lead visual and creative direction for SkyyRose brand assets",
        backstory="""You are an award-winning creative director with a background
        in fashion photography and 3D design. You understand how to create
        visuals that evoke emotion and drive desire for luxury products.""",
        tools=["image_generator", "3d_generator", "virtual_tryon"],
        allow_delegation=True,
    ),
}


# =============================================================================
# CrewAI Agent
# =============================================================================


class CrewAIAgent(BaseDevSkyyAgent):
    """
    Agent using CrewAI framework.

    Features:
    - Role-based specialization
    - Team collaboration
    - Task delegation
    - Memory integration
    - Tool sharing

    Example:
        agent = CrewAIAgent(config, role=SKYYROSE_ROLES["brand_strategist"])
        result = await agent.run("Develop Q1 marketing strategy")
    """

    def __init__(self, config: AgentConfig, role: AgentRole | None = None):
        super().__init__(config)
        self.role = role or AgentRole(
            role="Assistant",
            goal="Help with SkyyRose operations",
            backstory="You are a helpful AI assistant for SkyyRose luxury streetwear.",
        )
        self._crew_agent = None
        self._llm = None

    async def initialize(self) -> None:
        """Initialize CrewAI agent"""
        try:
            from crewai import LLM, Agent

            # Configure LLM
            self._llm = LLM(
                model=self._get_model_string(),
                temperature=self.config.temperature,
            )

            # Create CrewAI agent
            self._crew_agent = Agent(
                role=self.role.role,
                goal=self.role.goal,
                backstory=self.role.backstory,
                llm=self._llm,
                verbose=self.role.verbose,
                allow_delegation=self.role.allow_delegation,
                memory=self.config.enable_memory,
            )

            logger.info(f"CrewAI agent initialized: {self.name} ({self.role.role})")

        except ImportError as e:
            logger.warning(f"CrewAI not available: {e}")
            raise ImportError("CrewAI not installed. Install with: pip install crewai") from e
        except Exception as e:
            logger.error(f"Failed to initialize CrewAI agent: {e}")
            raise

    def _get_model_string(self) -> str:
        """Get CrewAI model string"""
        model = self.config.model.lower()

        # CrewAI uses provider/model format
        if "/" in self.config.model:
            return self.config.model

        # Map to CrewAI format
        if "gpt-4o" in model and "mini" not in model:
            return "openai/gpt-4o"
        elif "gpt-4o-mini" in model:
            return "openai/gpt-4o-mini"
        elif "claude" in model:
            if "sonnet" in model:
                return "anthropic/claude-3-5-sonnet-20241022"
            elif "opus" in model:
                return "anthropic/claude-3-opus-20240229"
            return "anthropic/claude-3-5-sonnet-20241022"
        elif "gemini" in model:
            return "google/gemini-pro"

        return "openai/gpt-4o-mini"

    async def execute(self, prompt: str, **kwargs) -> AgentResult:
        """Execute CrewAI agent"""
        start_time = datetime.now(UTC)

        try:
            from crewai import Crew, Task

            # Create task
            task = Task(
                description=prompt,
                expected_output=kwargs.get("expected_output", "A detailed response"),
                agent=self._crew_agent,
            )

            # Create single-agent crew
            crew = Crew(
                agents=[self._crew_agent],
                tasks=[task],
                verbose=self.role.verbose,
            )

            # Execute
            result = crew.kickoff()

            # Extract content
            content = str(result) if result else ""

            # Estimate tokens
            input_tokens = int(len(prompt.split()) * 1.3)
            output_tokens = int(len(content.split()) * 1.3)

            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.CREWAI,
                content=content,
                status=AgentStatus.COMPLETED,
                iterations=1,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost_usd=estimate_cost(
                    self.config.model,
                    input_tokens,
                    output_tokens,
                ),
                started_at=start_time,
            )

        except Exception as e:
            logger.error(f"CrewAI execution failed: {e}")
            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.CREWAI,
                content="",
                status=AgentStatus.FAILED,
                error=str(e),
                error_type=type(e).__name__,
                started_at=start_time,
            )


# =============================================================================
# CrewAI Crew (Multi-Agent Team)
# =============================================================================


class CrewAICrew(BaseDevSkyyAgent):
    """
    Multi-agent crew using CrewAI.

    Features:
    - Multiple specialized agents
    - Task orchestration
    - Sequential or parallel execution
    - Shared context and memory

    Example:
        crew = CrewAICrew(
            config,
            roles=[SKYYROSE_ROLES["brand_strategist"], SKYYROSE_ROLES["content_creator"]],
            tasks=[task1, task2]
        )
        result = await crew.run("Launch new collection")
    """

    def __init__(
        self,
        config: AgentConfig,
        roles: list[AgentRole],
        tasks: list[TaskDefinition] | None = None,
        process: str = "sequential",  # sequential, hierarchical
    ):
        super().__init__(config)
        self.roles = roles
        self.task_definitions = tasks or []
        self.process = process
        self._agents: dict[str, Any] = {}
        self._crew = None

    async def initialize(self) -> None:
        """Initialize crew with all agents"""
        try:
            from crewai import LLM, Agent

            # Create LLM
            llm = LLM(
                model=self._get_model_string(),
                temperature=self.config.temperature,
            )

            # Create agents for each role
            for role in self.roles:
                agent = Agent(
                    role=role.role,
                    goal=role.goal,
                    backstory=role.backstory,
                    llm=llm,
                    verbose=role.verbose,
                    allow_delegation=role.allow_delegation,
                    memory=self.config.enable_memory,
                )
                self._agents[role.role] = agent

            logger.info(f"CrewAI crew initialized with {len(self._agents)} agents")

        except ImportError as e:
            raise ImportError("CrewAI not installed") from e

    def _get_model_string(self) -> str:
        """Get model string for CrewAI"""
        model = self.config.model.lower()
        if "gpt" in model:
            return f"openai/{self.config.model}"
        elif "claude" in model:
            return f"anthropic/{self.config.model}"
        return f"openai/{self.config.model}"

    async def execute(self, prompt: str, **kwargs) -> AgentResult:
        """Execute crew with tasks"""
        start_time = datetime.now(UTC)

        try:
            from crewai import Crew, Process, Task

            # Build tasks
            tasks = []

            if self.task_definitions:
                # Use predefined tasks
                for task_def in self.task_definitions:
                    agent = self._agents.get(task_def.agent_role)
                    if agent:
                        task = Task(
                            description=task_def.description,
                            expected_output=task_def.expected_output,
                            agent=agent,
                            async_execution=task_def.async_execution,
                        )
                        tasks.append(task)
            else:
                # Create task from prompt for first agent
                first_agent = list(self._agents.values())[0]
                task = Task(
                    description=prompt,
                    expected_output=kwargs.get("expected_output", "Detailed response"),
                    agent=first_agent,
                )
                tasks.append(task)

            # Determine process type
            process = Process.sequential
            if self.process == "hierarchical":
                process = Process.hierarchical

            # Create and execute crew
            crew = Crew(
                agents=list(self._agents.values()),
                tasks=tasks,
                process=process,
                verbose=True,
                memory=self.config.enable_memory,
            )

            result = crew.kickoff()
            content = str(result) if result else ""

            # Token estimation
            input_tokens = int(len(prompt.split()) * 1.3 * len(tasks))
            output_tokens = int(len(content.split()) * 1.3)

            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.CREWAI,
                content=content,
                status=AgentStatus.COMPLETED,
                iterations=len(tasks),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost_usd=estimate_cost(
                    self.config.model,
                    input_tokens,
                    output_tokens,
                ),
                started_at=start_time,
            )

        except Exception as e:
            logger.error(f"CrewAI crew execution failed: {e}")
            return AgentResult(
                agent_name=self.name,
                agent_provider=ADKProvider.CREWAI,
                content="",
                status=AgentStatus.FAILED,
                error=str(e),
                error_type=type(e).__name__,
                started_at=start_time,
            )


# =============================================================================
# Pre-built Crews for SkyyRose
# =============================================================================


def create_marketing_crew() -> CrewAICrew:
    """Create marketing-focused crew"""
    config = AgentConfig(
        name="marketing_crew",
        provider=ADKProvider.CREWAI,
        model="openai/gpt-4o-mini",
        system_prompt="SkyyRose marketing team",
    )

    roles = [
        SKYYROSE_ROLES["brand_strategist"],
        SKYYROSE_ROLES["content_creator"],
    ]

    tasks = [
        TaskDefinition(
            description="Analyze current market trends and competitor positioning",
            expected_output="Market analysis report with opportunities",
            agent_role="Brand Strategist",
        ),
        TaskDefinition(
            description="Create content plan based on market analysis",
            expected_output="Detailed content calendar with posts",
            agent_role="Content Creator",
            context=["Market analysis"],
        ),
    ]

    return CrewAICrew(config, roles, tasks, process="sequential")


def create_operations_crew() -> CrewAICrew:
    """Create operations-focused crew"""
    config = AgentConfig(
        name="operations_crew",
        provider=ADKProvider.CREWAI,
        model="openai/gpt-4o-mini",
        system_prompt="SkyyRose operations team",
    )

    roles = [
        SKYYROSE_ROLES["ecommerce_analyst"],
        SKYYROSE_ROLES["tech_lead"],
    ]

    return CrewAICrew(config, roles, process="sequential")


def create_customer_crew() -> CrewAICrew:
    """Create customer-focused crew"""
    config = AgentConfig(
        name="customer_crew",
        provider=ADKProvider.CREWAI,
        model="openai/gpt-4o-mini",
        system_prompt="SkyyRose customer success team",
    )

    roles = [
        SKYYROSE_ROLES["customer_advocate"],
        SKYYROSE_ROLES["brand_strategist"],
    ]

    return CrewAICrew(config, roles, process="sequential")


# =============================================================================
# Factory Functions
# =============================================================================


def create_crew(
    name: str,
    roles: list[AgentRole | dict],
    tasks: list[TaskDefinition | dict] | None = None,
    process: str = "sequential",
    model: str = "openai/gpt-4o-mini",
    **kwargs,
) -> CrewAICrew:
    """
    Create a CrewAI crew.

    Args:
        name: Crew name
        roles: List of AgentRole or dicts
        tasks: List of TaskDefinition or dicts
        process: "sequential" or "hierarchical"
        model: Model to use
        **kwargs: Additional config

    Returns:
        CrewAICrew instance
    """
    # Convert dicts to models
    role_objs = []
    for role in roles:
        if isinstance(role, dict):
            role_objs.append(AgentRole(**role))
        else:
            role_objs.append(role)

    task_objs = []
    if tasks:
        for task in tasks:
            if isinstance(task, dict):
                task_objs.append(TaskDefinition(**task))
            else:
                task_objs.append(task)

    config = AgentConfig(
        name=name,
        provider=ADKProvider.CREWAI,
        model=model,
        **kwargs,
    )

    return CrewAICrew(config, role_objs, task_objs, process)


# Register with factory
agent_factory.register(ADKProvider.CREWAI, CrewAIAgent)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Models
    "AgentRole",
    "TaskDefinition",
    # Roles
    "SKYYROSE_ROLES",
    # Agents
    "CrewAIAgent",
    "CrewAICrew",
    # Pre-built crews
    "create_marketing_crew",
    "create_operations_crew",
    "create_customer_crew",
    # Factory
    "create_crew",
]
