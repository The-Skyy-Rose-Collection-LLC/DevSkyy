#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  DEVSKYY MULTI-TECHNIQUE ENSEMBLE PROMPTING                                  ║
║  Plan → Execute → Analyze → Select Best → Implement                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Each agent runs 3 parallel reasoning paths using different techniques,     ║
║  self-analyzes outputs, and implements the best solution.                   ║
║                                                                              ║
║  VERIFIED TECHNIQUES COMBINED:                                               ║
║  - Self-Consistency (Wang et al. 2022) - Multiple reasoning paths            ║
║  - Self-Critique/Reflexion (Shinn et al. 2023) - Analyze own outputs         ║
║  - Best-of-N Selection - Choose optimal path with reasoning                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class TechniqueType(str, Enum):
    """Available reasoning techniques for ensemble."""
    REACT = "react"
    COT = "chain_of_thought"
    TOT = "tree_of_thoughts"
    GENERATED_KNOWLEDGE = "generated_knowledge"
    DIRECT = "direct"


@dataclass
class TechniqueConfig:
    """Configuration for a specific technique."""
    technique: TechniqueType
    name: str
    prompt_template: str
    best_for: List[str]


TECHNIQUE_PROMPTS: Dict[TechniqueType, TechniqueConfig] = {
    TechniqueType.REACT: TechniqueConfig(
        technique=TechniqueType.REACT,
        name="ReAct (Reasoning + Acting)",
        prompt_template="""
<approach name="ReAct">
Use the ReAct framework: interleave thinking with tool actions.

For this task, follow this loop:
THOUGHT: [What do I need to figure out? What's my approach?]
ACTION: [Which tool to use from: {tools}]
ACTION_INPUT: [Parameters for the tool]
OBSERVATION: [What did the tool return?]
... repeat until solved ...
THOUGHT: I now have enough information.
ACTION: finish
ACTION_INPUT: [Your final answer/solution]

Begin your ReAct reasoning:
</approach>
""",
        best_for=["tool_orchestration", "api_calls", "data_retrieval", "multi_step_operations"],
    ),
    TechniqueType.COT: TechniqueConfig(
        technique=TechniqueType.COT,
        name="Chain-of-Thought",
        prompt_template="""
<approach name="Chain-of-Thought">
Think through this step-by-step, showing your reasoning at each stage.

<thinking>
Step 1: [First consideration]
Step 2: [Build on step 1]
Step 3: [Continue logical progression]
...
Final Step: [Conclude reasoning]
</thinking>

<answer>
[Your final solution based on the reasoning above]
</answer>
</approach>
""",
        best_for=["analysis", "reasoning", "math", "logic", "explanations"],
    ),
    TechniqueType.TOT: TechniqueConfig(
        technique=TechniqueType.TOT,
        name="Tree of Thoughts",
        prompt_template="""
<approach name="Tree-of-Thoughts">
Explore multiple solution paths before committing to one.

<branch id="1">
  <thought>[First approach to solving this]</thought>
  <evaluation>[promising/neutral/unpromising]</evaluation>
  <reasoning>[Why this rating?]</reasoning>
</branch>

<branch id="2">
  <thought>[Alternative approach]</thought>
  <evaluation>[promising/neutral/unpromising]</evaluation>
  <reasoning>[Why this rating?]</reasoning>
</branch>

<branch id="3">
  <thought>[Third approach]</thought>
  <evaluation>[promising/neutral/unpromising]</evaluation>
  <reasoning>[Why this rating?]</reasoning>
</branch>

<selected_branch>[Which branch number and why]</selected_branch>

<answer>
[Execute the selected branch's approach]
</answer>
</approach>
""",
        best_for=["creative", "complex_decisions", "strategy", "design", "planning"],
    ),
    TechniqueType.GENERATED_KNOWLEDGE: TechniqueConfig(
        technique=TechniqueType.GENERATED_KNOWLEDGE,
        name="Generated Knowledge",
        prompt_template="""
<approach name="Generated-Knowledge">
First generate relevant background knowledge, then use it to solve the task.

<knowledge_generation>
Generate 3-5 relevant facts or background information:
1. [Relevant fact about this domain/task]
2. [Another relevant fact]
3. [Technical detail that helps]
4. [Context that matters]
5. [Additional insight]
</knowledge_generation>

<answer_with_knowledge>
Using the knowledge above, here is my solution:
[Your answer incorporating the generated knowledge]
</answer_with_knowledge>
</approach>
""",
        best_for=["content_creation", "research", "explanations", "domain_specific"],
    ),
    TechniqueType.DIRECT: TechniqueConfig(
        technique=TechniqueType.DIRECT,
        name="Direct Response",
        prompt_template="""
<approach name="Direct">
Provide a direct, concise response to the task.

<answer>
[Your solution]
</answer>
</approach>
""",
        best_for=["simple_tasks", "factual_queries", "baseline"],
    ),
}


@dataclass
class EvaluationCriteria:
    """Criteria for evaluating outputs."""
    name: str
    description: str
    weight: float


DEFAULT_CRITERIA: List[EvaluationCriteria] = [
    EvaluationCriteria(
        name="task_completion",
        description="Does this output fully address what was asked?",
        weight=0.30,
    ),
    EvaluationCriteria(
        name="accuracy",
        description="Is the information/logic correct and verifiable?",
        weight=0.25,
    ),
    EvaluationCriteria(
        name="brand_alignment",
        description="Does it match SkyyRose luxury brand voice and standards?",
        weight=0.15,
    ),
    EvaluationCriteria(
        name="feasibility",
        description="Can this actually be implemented/executed?",
        weight=0.15,
    ),
    EvaluationCriteria(
        name="completeness",
        description="Is anything missing? Are edge cases handled?",
        weight=0.15,
    ),
]


@dataclass
class AgentTechniqueMapping:
    """Maps an agent to its 3 techniques for ensemble."""
    agent_name: str
    primary: TechniqueType
    secondary: TechniqueType
    tertiary: TechniqueType


AGENT_TECHNIQUE_MAPPINGS: Dict[str, AgentTechniqueMapping] = {
    "commerce": AgentTechniqueMapping(
        agent_name="Commerce Agent",
        primary=TechniqueType.REACT,
        secondary=TechniqueType.COT,
        tertiary=TechniqueType.DIRECT,
    ),
    "creative": AgentTechniqueMapping(
        agent_name="Creative Agent",
        primary=TechniqueType.TOT,
        secondary=TechniqueType.GENERATED_KNOWLEDGE,
        tertiary=TechniqueType.COT,
    ),
    "marketing": AgentTechniqueMapping(
        agent_name="Marketing Agent",
        primary=TechniqueType.GENERATED_KNOWLEDGE,
        secondary=TechniqueType.COT,
        tertiary=TechniqueType.TOT,
    ),
    "support": AgentTechniqueMapping(
        agent_name="Support Agent",
        primary=TechniqueType.REACT,
        secondary=TechniqueType.COT,
        tertiary=TechniqueType.DIRECT,
    ),
    "operations": AgentTechniqueMapping(
        agent_name="Operations Agent",
        primary=TechniqueType.REACT,
        secondary=TechniqueType.COT,
        tertiary=TechniqueType.TOT,
    ),
    "analytics": AgentTechniqueMapping(
        agent_name="Analytics Agent",
        primary=TechniqueType.COT,
        secondary=TechniqueType.GENERATED_KNOWLEDGE,
        tertiary=TechniqueType.TOT,
    ),
}


def build_ensemble_prompt(
    agent_type: str,
    agent_role: str,
    agent_domain: str,
    tools: List[str],
    task: str,
    constraints: List[str],
    success_criteria: List[str],
    custom_techniques: Optional[List[TechniqueType]] = None,
    custom_evaluation_criteria: Optional[List[EvaluationCriteria]] = None,
) -> str:
    """Build a complete Multi-Technique Ensemble prompt for an agent."""
    mapping = AGENT_TECHNIQUE_MAPPINGS.get(agent_type)
    if custom_techniques and len(custom_techniques) >= 3:
        techniques = custom_techniques[:3]
    elif mapping:
        techniques = [mapping.primary, mapping.secondary, mapping.tertiary]
    else:
        techniques = [TechniqueType.COT, TechniqueType.REACT, TechniqueType.DIRECT]

    criteria = custom_evaluation_criteria or DEFAULT_CRITERIA
    tools_str = ", ".join(tools) if tools else "None"
    constraints_str = "\n".join([f"  ✗ {c}" for c in constraints])
    success_str = "\n".join([f"  ☐ {s}" for s in success_criteria])
    criteria_str = "\n".join(
        [f"  • {c.name} ({int(c.weight*100)}%): {c.description}" for c in criteria]
    )

    technique_sections = []
    for i, tech in enumerate(techniques, 1):
        config = TECHNIQUE_PROMPTS[tech]
        tech_prompt = config.prompt_template.format(tools=tools_str)
        technique_sections.append(
            f"""
═══════════════════════════════════════════════════════════════════════════════
PATH {i}: {config.name}
═══════════════════════════════════════════════════════════════════════════════
{tech_prompt}
"""
        )

    techniques_block = "\n".join(technique_sections)

    return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  {agent_role.upper():^74}  ║
║  Multi-Technique Ensemble Reasoning                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

You are the {agent_role}, an AI agent specializing in {agent_domain}.

═══════════════════════════════════════════════════════════════════════════════
AVAILABLE TOOLS
═══════════════════════════════════════════════════════════════════════════════
{tools_str}

═══════════════════════════════════════════════════════════════════════════════
CONSTRAINTS (MUST FOLLOW)
═══════════════════════════════════════════════════════════════════════════════
{constraints_str}

═══════════════════════════════════════════════════════════════════════════════
SUCCESS CRITERIA
═══════════════════════════════════════════════════════════════════════════════
{success_str}

═══════════════════════════════════════════════════════════════════════════════
YOUR TASK
═══════════════════════════════════════════════════════════════════════════════
{task}

╔══════════════════════════════════════════════════════════════════════════════╗
║  PHASE 1: PLAN - Generate 3 Solutions Using Different Techniques             ║
╚══════════════════════════════════════════════════════════════════════════════╝

Generate THREE different solutions to this task, each using a different 
reasoning technique. Complete ALL THREE before moving to Phase 2.

{techniques_block}

╔══════════════════════════════════════════════════════════════════════════════╗
║  PHASE 2: ANALYZE - Self-Critique Each Output                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Now analyze each of the 3 outputs you generated. Score each on these criteria:

{criteria_str}

<analysis>
<output_1_score>
  task_completion: [1-10]
  accuracy: [1-10]
  brand_alignment: [1-10]
  feasibility: [1-10]
  completeness: [1-10]
  weighted_total: [calculated]
  strengths: [what this approach did well]
  weaknesses: [what this approach missed]
</output_1_score>

<output_2_score>
  task_completion: [1-10]
  accuracy: [1-10]
  brand_alignment: [1-10]
  feasibility: [1-10]
  completeness: [1-10]
  weighted_total: [calculated]
  strengths: [what this approach did well]
  weaknesses: [what this approach missed]
</output_2_score>

<output_3_score>
  task_completion: [1-10]
  accuracy: [1-10]
  brand_alignment: [1-10]
  feasibility: [1-10]
  completeness: [1-10]
  weighted_total: [calculated]
  strengths: [what this approach did well]
  weaknesses: [what this approach missed]
</output_3_score>
</analysis>

╔══════════════════════════════════════════════════════════════════════════════╗
║  PHASE 3: SELECT & EXECUTE - Implement the Best Solution                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

<selection>
  chosen_output: [1, 2, or 3]
  reasoning: [Why this output best serves the task]
  improvements: [Any refinements to make before final execution]
</selection>

<final_implementation>
[Execute the selected approach with any improvements noted above]
[This is your FINAL OUTPUT that will be used]
</final_implementation>

<confidence>
  score: [0-100]%
  reasoning: [Why this confidence level]
</confidence>
"""


def build_commerce_prompt(task: str) -> str:
    """Build ensemble prompt for Commerce Agent."""
    return build_ensemble_prompt(
        agent_type="commerce",
        agent_role="Senior E-Commerce Operations Director",
        agent_domain="products, inventory, pricing, orders, and WooCommerce integration",
        tools=[
            "woocommerce_products_api", "woocommerce_orders_api", "inventory_tracker",
            "price_optimizer", "fulfillment_tracker", "stock_predictor", "margin_calculator",
        ],
        task=task,
        constraints=[
            "Never oversell inventory (sell more than available stock)",
            "Never process orders without inventory verification",
            "Never change prices without margin analysis (maintain >60% gross margin)",
            "Never expose customer payment data",
            "Never delete product data without backup confirmation",
        ],
        success_criteria=[
            "Inventory accuracy > 99.5%",
            "Order processing time < 30 seconds",
            "Pricing changes maintain > 60% gross margin",
            "API response time < 200ms",
            "Zero data inconsistencies",
        ],
    )


def build_creative_prompt(task: str) -> str:
    """Build ensemble prompt for Creative Agent."""
    return build_ensemble_prompt(
        agent_type="creative",
        agent_role="Creative Director, AI Visual Production",
        agent_domain="3D assets (Tripo3D), virtual try-on (FASHN), and media content",
        tools=[
            "tripo3d_api", "fashn_api", "image_generator", "mesh_validator",
            "texture_optimizer", "background_remover", "wordpress_media_api",
        ],
        task=task,
        constraints=[
            "Never generate images without brand aesthetic guidelines",
            "Never output low-resolution images (<2048x2048 for products)",
            "Never skip quality validation on 3D models",
            "Never exceed polycount limits (100K for web)",
            "Never generate offensive or inappropriate imagery",
        ],
        success_criteria=[
            "Image resolution >= 2048x2048",
            "3D model polycount < 100K for web display",
            "Brand aesthetic alignment > 90%",
            "Virtual try-on accuracy > 85%",
            "Asset generation success rate > 95%",
        ],
    )


def build_marketing_prompt(task: str) -> str:
    """Build ensemble prompt for Marketing Agent."""
    return build_ensemble_prompt(
        agent_type="marketing",
        agent_role="Chief Marketing Officer AI",
        agent_domain="content creation, SEO optimization, social media, and campaigns",
        tools=[
            "content_generator", "brand_voice_checker", "keyword_analyzer",
            "schema_generator", "social_scheduler", "campaign_planner", "ab_tester",
        ],
        task=task,
        constraints=[
            "Never use discount-focused language (luxury brand positioning)",
            "Never plagiarize content",
            "Never make false product claims",
            "Never reference competitor brands negatively",
            "Never publish without SEO optimization",
        ],
        success_criteria=[
            "Brand voice consistency > 95%",
            "SEO optimization score > 85%",
            "Content uniqueness > 95%",
            "Social engagement rate > industry average",
            "Campaign ROI > 3.0x",
        ],
    )


def build_support_prompt(task: str) -> str:
    """Build ensemble prompt for Support Agent."""
    return build_ensemble_prompt(
        agent_type="support",
        agent_role="Customer Experience Director",
        agent_domain="customer service, tickets, FAQ management, and live chat",
        tools=[
            "ticket_system", "knowledge_base", "chat_interface",
            "escalation_handler", "customer_history", "sentiment_analyzer",
        ],
        task=task,
        constraints=[
            "Never share customer data with unauthorized parties",
            "Never make promises outside policy guidelines",
            "Never use informal or non-luxury tone",
            "Never leave tickets unresolved beyond SLA",
            "Never escalate without attempting resolution first",
        ],
        success_criteria=[
            "First response time < 60 seconds",
            "Resolution rate > 85%",
            "Customer satisfaction > 4.5/5",
            "Escalation rate < 15%",
            "Luxury tone maintained in all interactions",
        ],
    )


def build_operations_prompt(task: str) -> str:
    """Build ensemble prompt for Operations Agent."""
    return build_ensemble_prompt(
        agent_type="operations",
        agent_role="Platform Operations Engineer",
        agent_domain="WordPress, Elementor Pro, deployment, and system monitoring",
        tools=[
            "wordpress_rest_api", "elementor_api", "deployment_manager",
            "prometheus_api", "grafana_api", "health_checker", "backup_manager",
        ],
        task=task,
        constraints=[
            "Never deploy without backup verification",
            "Never modify production during peak hours without approval",
            "Never skip health checks between deployment steps",
            "Never disable monitoring during operations",
            "Never override Shoptimizer 2.9.0 / Elementor Pro 3.32.2 compatibility",
        ],
        success_criteria=[
            "Zero downtime deployments",
            "Deployment success rate > 99%",
            "System uptime > 99.9%",
            "API latency p99 < 200ms",
            "All health checks passing",
        ],
    )


def build_analytics_prompt(task: str) -> str:
    """Build ensemble prompt for Analytics Agent."""
    return build_ensemble_prompt(
        agent_type="analytics",
        agent_role="Chief Data Officer AI",
        agent_domain="reports, forecasting, ML predictions, and business intelligence",
        tools=[
            "data_warehouse", "ml_predictor", "report_generator",
            "forecast_engine", "trend_analyzer", "visualization_builder",
        ],
        task=task,
        constraints=[
            "Never make predictions without sufficient data backing",
            "Never present statistics without confidence intervals",
            "Never claim causation from correlation alone",
            "Never hide uncertainty in forecasts",
            "Never use outdated data for current analysis",
        ],
        success_criteria=[
            "Prediction accuracy > 85%",
            "All forecasts include confidence intervals",
            "Report generation time < 30 seconds",
            "Data freshness < 1 hour",
            "Statistical significance cited for all claims",
        ],
    )


__all__ = [
    "TechniqueType", "TechniqueConfig", "EvaluationCriteria", "AgentTechniqueMapping",
    "TECHNIQUE_PROMPTS", "DEFAULT_CRITERIA", "AGENT_TECHNIQUE_MAPPINGS",
    "build_ensemble_prompt", "build_commerce_prompt", "build_creative_prompt",
    "build_marketing_prompt", "build_support_prompt", "build_operations_prompt",
    "build_analytics_prompt",
]
