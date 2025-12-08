"""
DevSkyy Prompt Injection System - Integration Layer

This module bridges the Elon Musk Thinking Framework (10 techniques) with 
DevSkyy's 54-agent ecosystem. It provides automated prompt injection into
agents at runtime, enabling enterprise-grade LLM interactions.

Integration Points:
1. BaseAgent - System prompt injection on initialization
2. Orchestrator - Chain prompt injection for multi-agent workflows
3. Registry - Prompt library discovery and management
4. MCP Server - External LLM prompt formatting

Techniques Implemented:
1. Role-Based Constraint Prompting
2. Chain-of-Thought (CoT)
3. Few-Shot Prompting
4. Self-Consistency
5. Tree of Thoughts
6. ReAct (Reasoning + Acting)
7. RAG (Retrieval-Augmented Generation)
8. Prompt Chaining
9. Generated Knowledge
10. Negative Prompting
+ Constitutional AI
+ COSTARD Framework
+ OpenAI Six-Strategy Framework

Version: 1.0.0
Python: 3.11+
"""

import hashlib
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Add prompts module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prompts.agent_prompts import AgentPromptLibrary
from prompts.base_system_prompt import AgentCategory, OutputStandard
from prompts.chain_orchestrator import PromptChainOrchestrator
from prompts.meta_prompts import MetaPromptFactory, MetaPromptType
from prompts.task_templates import (TaskCategory, TaskContext, TaskPriority,
                                    TaskTemplateFactory)
from prompts.technique_engine import (Constraint, OutputFormat,
                                      PromptTechnique, PromptTechniqueEngine,
                                      RoleDefinition)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class PromptInjectionMode(str, Enum):
    """How prompts are injected into agents."""
    SYSTEM_PROMPT = "system_prompt"      # Inject as system message
    CONTEXT_PREFIX = "context_prefix"    # Prepend to user message
    HYBRID = "hybrid"                    # Both system and context
    DYNAMIC = "dynamic"                  # Select based on task


class PromptCacheStrategy(str, Enum):
    """Caching strategy for generated prompts."""
    NONE = "none"                        # No caching
    AGENT_LEVEL = "agent_level"          # Cache per agent type
    TASK_LEVEL = "task_level"            # Cache per agent + task
    FULL = "full"                        # Cache everything


@dataclass
class PromptInjectionConfig:
    """Configuration for prompt injection system."""
    mode: PromptInjectionMode = PromptInjectionMode.HYBRID
    cache_strategy: PromptCacheStrategy = PromptCacheStrategy.TASK_LEVEL
    max_prompt_tokens: int = 4096
    include_chain_of_thought: bool = True
    include_few_shot_examples: bool = True
    include_negative_prompts: bool = True
    include_constitutional_ai: bool = True
    auto_select_techniques: bool = True
    debug_mode: bool = False


# =============================================================================
# Agent Profile Mapping
# =============================================================================

AGENT_PROFILES: Dict[str, Dict[str, Any]] = {
    # Infrastructure Agents
    "ScannerAgent": {
        "category": AgentCategory.BACKEND,
        "techniques": [
            PromptTechnique.ROLE_BASED_CONSTRAINT,
            PromptTechnique.CHAIN_OF_THOUGHT,
            PromptTechnique.NEGATIVE_PROMPTING,
        ],
        "role": {
            "title": "Senior Security Analyst",
            "years_experience": 12,
            "domain": "cybersecurity",
            "expertise_areas": ["OWASP Top 10", "SAST", "DAST", "CVE analysis"],
            "nickname": "The Code X-Ray",
        },
        "output_standard": OutputStandard.PRODUCTION,
    },
    "FixerAgent": {
        "category": AgentCategory.BACKEND,
        "techniques": [
            PromptTechnique.ROLE_BASED_CONSTRAINT,
            PromptTechnique.TREE_OF_THOUGHTS,
            PromptTechnique.SELF_CONSISTENCY,
        ],
        "role": {
            "title": "Principal Software Engineer",
            "years_experience": 15,
            "domain": "code repair",
            "expertise_areas": ["debugging", "refactoring", "regression prevention"],
            "nickname": "The Code Surgeon",
        },
        "output_standard": OutputStandard.PRODUCTION,
    },
    "AuthenticationAgent": {
        "category": AgentCategory.SECURITY,
        "techniques": [
            PromptTechnique.ROLE_BASED_CONSTRAINT,
            PromptTechnique.CONSTITUTIONAL_AI,
            PromptTechnique.NEGATIVE_PROMPTING,
        ],
        "role": {
            "title": "Security Architect",
            "years_experience": 14,
            "domain": "authentication",
            "expertise_areas": ["OAuth2", "JWT", "RBAC", "zero-trust"],
            "nickname": "The Gatekeeper",
        },
        "output_standard": OutputStandard.PRODUCTION,
    },
    # E-commerce Agents
    "ProductManagerAgent": {
        "category": AgentCategory.ECOMMERCE,
        "techniques": [
            PromptTechnique.ROLE_BASED_CONSTRAINT,
            PromptTechnique.FEW_SHOT,
            PromptTechnique.GENERATED_KNOWLEDGE,
        ],
        "role": {
            "title": "Senior E-Commerce Copywriter",
            "years_experience": 10,
            "domain": "fashion e-commerce",
            "expertise_areas": ["SEO", "conversion optimization", "brand voice"],
            "nickname": "The Product Whisperer",
        },
        "output_standard": OutputStandard.PRODUCTION,
    },
    "DynamicPricingAgent": {
        "category": AgentCategory.ECOMMERCE,
        "techniques": [
            PromptTechnique.ROLE_BASED_CONSTRAINT,
            PromptTechnique.CHAIN_OF_THOUGHT,
            PromptTechnique.SELF_CONSISTENCY,
        ],
        "role": {
            "title": "Revenue Optimization Specialist",
            "years_experience": 12,
            "domain": "pricing strategy",
            "expertise_areas": ["elasticity modeling", "competitive analysis", "margin optimization"],
            "nickname": "The Price Oracle",
        },
        "output_standard": OutputStandard.PRODUCTION,
    },
    "InventoryOptimizerAgent": {
        "category": AgentCategory.ECOMMERCE,
        "techniques": [
            PromptTechnique.ROLE_BASED_CONSTRAINT,
            PromptTechnique.CHAIN_OF_THOUGHT,
            PromptTechnique.RAG,
        ],
        "role": {
            "title": "Supply Chain Analyst",
            "years_experience": 11,
            "domain": "inventory management",
            "expertise_areas": ["demand forecasting", "safety stock", "reorder optimization"],
            "nickname": "The Stock Seer",
        },
        "output_standard": OutputStandard.PRODUCTION,
    },
    # AI Agents
    "ClaudeAIAgent": {
        "category": AgentCategory.AI_INTELLIGENCE,
        "techniques": [
            PromptTechnique.ROLE_BASED_CONSTRAINT,
            PromptTechnique.CONSTITUTIONAL_AI,
            PromptTechnique.CHAIN_OF_THOUGHT,
        ],
        "role": {
            "title": "AI Integration Specialist",
            "years_experience": 8,
            "domain": "LLM orchestration",
            "expertise_areas": ["Anthropic API", "prompt engineering", "context optimization"],
            "nickname": "The Claude Conductor",
        },
        "output_standard": OutputStandard.PRODUCTION,
    },
    "MultiModelOrchestrator": {
        "category": AgentCategory.AI_INTELLIGENCE,
        "techniques": [
            PromptTechnique.ROLE_BASED_CONSTRAINT,
            PromptTechnique.TREE_OF_THOUGHTS,
            PromptTechnique.SELF_CONSISTENCY,
        ],
        "role": {
            "title": "Multi-Model AI Architect",
            "years_experience": 10,
            "domain": "AI orchestration",
            "expertise_areas": ["model routing", "ensemble methods", "cost optimization"],
            "nickname": "The AI Conductor",
        },
        "output_standard": OutputStandard.PRODUCTION,
    },
    # Content Agents
    "WordPressThemeBuilderAgent": {
        "category": AgentCategory.CONTENT,
        "techniques": [
            PromptTechnique.ROLE_BASED_CONSTRAINT,
            PromptTechnique.PROMPT_CHAINING,
            PromptTechnique.FEW_SHOT,
        ],
        "role": {
            "title": "Senior WordPress Developer",
            "years_experience": 12,
            "domain": "WordPress development",
            "expertise_areas": ["Elementor", "Divi", "theme development", "PHP"],
            "nickname": "The Theme Wizard",
        },
        "output_standard": OutputStandard.PRODUCTION,
    },
    "SEOOptimizerAgent": {
        "category": AgentCategory.CONTENT,
        "techniques": [
            PromptTechnique.ROLE_BASED_CONSTRAINT,
            PromptTechnique.RAG,
            PromptTechnique.GENERATED_KNOWLEDGE,
        ],
        "role": {
            "title": "SEO Director",
            "years_experience": 11,
            "domain": "search optimization",
            "expertise_areas": ["technical SEO", "content strategy", "schema markup"],
            "nickname": "The Search Whisperer",
        },
        "output_standard": OutputStandard.PRODUCTION,
    },
    # Advanced Agents
    "SelfHealingAgent": {
        "category": AgentCategory.INFRASTRUCTURE,
        "techniques": [
            PromptTechnique.ROLE_BASED_CONSTRAINT,
            PromptTechnique.REACT,
            PromptTechnique.TREE_OF_THOUGHTS,
        ],
        "role": {
            "title": "Site Reliability Engineer",
            "years_experience": 13,
            "domain": "system reliability",
            "expertise_areas": ["auto-recovery", "anomaly detection", "incident response"],
            "nickname": "The System Doctor",
        },
        "output_standard": OutputStandard.PRODUCTION,
    },
    "CustomerIntelligenceAgent": {
        "category": AgentCategory.ANALYTICS,
        "techniques": [
            PromptTechnique.ROLE_BASED_CONSTRAINT,
            PromptTechnique.CHAIN_OF_THOUGHT,
            PromptTechnique.CONSTITUTIONAL_AI,
        ],
        "role": {
            "title": "Customer Analytics Lead",
            "years_experience": 10,
            "domain": "customer intelligence",
            "expertise_areas": ["RFM analysis", "segmentation", "churn prediction"],
            "nickname": "The Customer Mind Reader",
        },
        "output_standard": OutputStandard.PRODUCTION,
    },
}


# =============================================================================
# Prompt Injector - Main Class
# =============================================================================

class PromptInjector:
    """
    Main integration class that injects optimized prompts into DevSkyy agents.
    
    This class bridges the Elon Musk Thinking Framework with the DevSkyy
    agent ecosystem, providing:
    
    1. System prompt generation for each agent type
    2. Task-specific prompt injection
    3. Chain prompt orchestration for workflows
    4. Caching and optimization
    
    Usage:
        injector = PromptInjector()
        
        # Get system prompt for an agent
        system_prompt = injector.get_agent_system_prompt("ScannerAgent")
        
        # Get task injection prompt
        task_prompt = injector.get_task_prompt(
            agent_name="ProductManagerAgent",
            task_type="product_description",
            context={"product": {...}}
        )
        
        # Get full prompt (system + task)
        full_prompt = injector.get_full_prompt(
            agent_name="FixerAgent",
            task_type="bug_fix",
            context={"code": "...", "error": "..."}
        )
    """
    
    def __init__(self, config: Optional[PromptInjectionConfig] = None):
        """Initialize the prompt injector."""
        self.config = config or PromptInjectionConfig()
        
        # Initialize sub-systems
        self.technique_engine = PromptTechniqueEngine()
        self.task_factory = TaskTemplateFactory()
        self.agent_library = AgentPromptLibrary()
        self.chain_orchestrator = PromptChainOrchestrator()
        self.meta_factory = MetaPromptFactory()
        
        # Caching
        self._system_prompt_cache: Dict[str, str] = {}
        self._task_prompt_cache: Dict[str, str] = {}
        
        # Metrics
        self.injection_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        logger.info("PromptInjector initialized with Elon Musk Thinking Framework")
    
    # =========================================================================
    # System Prompt Generation
    # =========================================================================
    
    def get_agent_system_prompt(
        self,
        agent_name: str,
        override_techniques: Optional[List[PromptTechnique]] = None,
        custom_constraints: Optional[List[Constraint]] = None,
    ) -> str:
        """
        Generate the system prompt for a specific agent.
        
        Args:
            agent_name: Name of the DevSkyy agent
            override_techniques: Override the default techniques
            custom_constraints: Add custom constraints
            
        Returns:
            Complete system prompt string
        """
        cache_key = f"system_{agent_name}"
        
        # Check cache
        if self.config.cache_strategy != PromptCacheStrategy.NONE:
            if cache_key in self._system_prompt_cache:
                self.cache_hits += 1
                return self._system_prompt_cache[cache_key]
        
        self.cache_misses += 1
        
        # Get agent profile
        profile = AGENT_PROFILES.get(agent_name, self._get_default_profile(agent_name))
        
        # Build role definition
        role = RoleDefinition(
            title=profile["role"]["title"],
            years_experience=profile["role"]["years_experience"],
            domain=profile["role"]["domain"],
            expertise_areas=profile["role"]["expertise_areas"],
            nickname=profile["role"].get("nickname"),
        )
        
        # Get techniques
        techniques = override_techniques or profile.get("techniques", [
            PromptTechnique.ROLE_BASED_CONSTRAINT,
            PromptTechnique.CHAIN_OF_THOUGHT,
        ])
        
        # Build constraints
        constraints = self._build_agent_constraints(agent_name, profile)
        if custom_constraints:
            constraints.extend(custom_constraints)
        
        # Build output format
        output_format = OutputFormat(
            format_type="json",
            required_sections=["result", "confidence", "reasoning"],
        )
        
        # Generate system prompt
        system_prompt = self.technique_engine.build_prompt(
            task=f"You are the {agent_name} for DevSkyy enterprise platform.",
            techniques=techniques,
            role=role,
            constraints=constraints,
            output_format=output_format,
        )
        
        # Add Constitutional AI if enabled
        if self.config.include_constitutional_ai:
            system_prompt = self._add_constitutional_ai(system_prompt)
        
        # Cache
        if self.config.cache_strategy != PromptCacheStrategy.NONE:
            self._system_prompt_cache[cache_key] = system_prompt
        
        self.injection_count += 1
        return system_prompt
    
    def _build_agent_constraints(
        self,
        agent_name: str,
        profile: Dict[str, Any],
    ) -> List[Constraint]:
        """Build constraints for an agent based on its profile."""
        constraints = []
        
        # Universal constraints
        constraints.extend([
            Constraint("must", "Always validate all inputs before processing"),
            Constraint("must", "Include comprehensive error handling with specific error codes"),
            Constraint("must", "Return structured JSON responses with status, data, and metadata"),
            Constraint("must", "Log all operations with correlation IDs for traceability"),
            Constraint("must_not", "Never include hardcoded credentials or secrets"),
            Constraint("must_not", "Never use placeholder implementations (TODO/FIXME) in production"),
            Constraint("must_not", "Never skip input validation or sanitization"),
            Constraint("prefer", "Use async/await for all I/O operations"),
            Constraint("prefer", "Implement circuit breaker patterns for external calls"),
            Constraint("avoid", "Blocking operations in async contexts"),
            Constraint("avoid", "Magic numbers without named constants"),
        ])
        
        # Category-specific constraints
        category = profile.get("category", AgentCategory.BACKEND)
        
        if category == AgentCategory.SECURITY:
            constraints.extend([
                Constraint("must", "Follow OWASP Top 10 security guidelines"),
                Constraint("must", "Implement defense-in-depth strategies"),
                Constraint("must", "Use cryptographically secure random generators"),
                Constraint("must_not", "Log sensitive data (PII, credentials, tokens)"),
            ])
        elif category == AgentCategory.ECOMMERCE:
            constraints.extend([
                Constraint("must", "Comply with PCI-DSS for payment data"),
                Constraint("must", "Include audit trails for all transactions"),
                Constraint("prefer", "Optimize for conversion rate"),
            ])
        elif category == AgentCategory.AI_INTELLIGENCE:
            constraints.extend([
                Constraint("must", "Implement rate limiting for API calls"),
                Constraint("must", "Track token usage and costs"),
                Constraint("prefer", "Use streaming for long responses"),
            ])
        elif category == AgentCategory.CONTENT:
            constraints.extend([
                Constraint("must", "Ensure content accessibility (WCAG 2.1)"),
                Constraint("must", "Include SEO metadata in all content"),
                Constraint("prefer", "Generate mobile-first designs"),
            ])
        
        return constraints
    
    def _add_constitutional_ai(self, prompt: str) -> str:
        """Add Constitutional AI principles to prompt."""
        constitutional_section = """

## CONSTITUTIONAL AI PRINCIPLES

You must adhere to these inviolable principles:

1. **TRUTH**: Never fabricate information. If uncertain, explicitly state "I cannot confirm this without verification."

2. **SAFETY**: Refuse to generate content that could cause harm, including malicious code, security exploits, or privacy violations.

3. **TRANSPARENCY**: Always disclose limitations, assumptions, and confidence levels in your outputs.

4. **COMPLIANCE**: Adhere to GDPR, CCPA, PCI-DSS, and other relevant regulations based on the data being processed.

5. **QUALITY**: Never output placeholder implementations (TODO/FIXME). Every output must be production-ready.

### Self-Critique Checklist

Before finalizing any response, verify:
- [ ] All claims are factually accurate and verifiable
- [ ] No security vulnerabilities introduced
- [ ] All edge cases handled appropriately
- [ ] Error handling is comprehensive
- [ ] Output format matches specification
"""
        return prompt + constitutional_section
    
    def _get_default_profile(self, agent_name: str) -> Dict[str, Any]:
        """Get a default profile for unregistered agents."""
        return {
            "category": AgentCategory.BACKEND,
            "techniques": [
                PromptTechnique.ROLE_BASED_CONSTRAINT,
                PromptTechnique.CHAIN_OF_THOUGHT,
            ],
            "role": {
                "title": "DevSkyy AI Agent",
                "years_experience": 10,
                "domain": "automation",
                "expertise_areas": ["task execution", "error handling", "optimization"],
                "nickname": None,
            },
            "output_standard": OutputStandard.PRODUCTION,
        }
    
    # =========================================================================
    # Task Prompt Generation
    # =========================================================================
    
    def get_task_prompt(
        self,
        agent_name: str,
        task_type: str,
        context: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> str:
        """
        Generate a task-specific prompt injection.
        
        Args:
            agent_name: Name of the agent executing the task
            task_type: Type of task (e.g., "product_description", "scan", "fix")
            context: Task context and parameters
            priority: Task priority level
            
        Returns:
            Task injection prompt string
        """
        cache_key = f"task_{agent_name}_{task_type}_{hashlib.md5(json.dumps(context, sort_keys=True, default=str).encode()).hexdigest()[:8]}"
        
        # Check cache
        if self.config.cache_strategy == PromptCacheStrategy.FULL:
            if cache_key in self._task_prompt_cache:
                self.cache_hits += 1
                return self._task_prompt_cache[cache_key]
        
        self.cache_misses += 1
        
        # Create task context
        task_context = TaskContext(
            task_id=f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            category=self._get_task_category(task_type),
            priority=priority,
            requester=context.get("requester", "system"),
            deadline=context.get("deadline"),
            metadata=context,
        )
        
        # Generate task prompt based on type
        task_prompt = self._generate_task_prompt(task_type, task_context, context)
        
        # Add few-shot examples if enabled
        if self.config.include_few_shot_examples:
            task_prompt = self._add_few_shot_examples(task_prompt, task_type)
        
        # Cache
        if self.config.cache_strategy == PromptCacheStrategy.FULL:
            self._task_prompt_cache[cache_key] = task_prompt
        
        return task_prompt
    
    def _get_task_category(self, task_type: str) -> TaskCategory:
        """Map task type to category."""
        category_mapping = {
            "product_description": TaskCategory.ECOMMERCE,
            "pricing_optimization": TaskCategory.ECOMMERCE,
            "inventory_forecast": TaskCategory.ECOMMERCE,
            "order_processing": TaskCategory.ECOMMERCE,
            "customer_segmentation": TaskCategory.ANALYTICS,
            "blog_post": TaskCategory.CONTENT,
            "social_media": TaskCategory.CONTENT,
            "email_campaign": TaskCategory.CONTENT,
            "wordpress_theme": TaskCategory.CONTENT,
            "scan": TaskCategory.SECURITY,
            "fix": TaskCategory.INFRASTRUCTURE,
            "authenticate": TaskCategory.SECURITY,
            "ml_prediction": TaskCategory.AI_ML,
        }
        return category_mapping.get(task_type, TaskCategory.CUSTOM)
    
    def _generate_task_prompt(
        self,
        task_type: str,
        task_context: TaskContext,
        context: Dict[str, Any],
    ) -> str:
        """Generate the task-specific prompt."""
        
        # E-commerce tasks
        if task_type == "product_description":
            return self.task_factory.create_ecommerce_task(
                task_type=task_type,
                product_data=context.get("product", {}),
                requirements=context.get("requirements", []),
            )
        elif task_type == "pricing_optimization":
            return self.task_factory.create_ecommerce_task(
                task_type=task_type,
                product_data=context.get("product", {}),
                market_data=context.get("market_data", {}),
            )
        elif task_type == "inventory_forecast":
            return self.task_factory.create_ecommerce_task(
                task_type=task_type,
                product_data=context.get("product", {}),
                historical_data=context.get("historical_data", []),
            )
        
        # Content tasks
        elif task_type == "blog_post":
            return self.task_factory.create_content_task(
                task_type=task_type,
                topic=context.get("topic", ""),
                keywords=context.get("keywords", []),
            )
        elif task_type == "social_media":
            return self.task_factory.create_content_task(
                task_type=task_type,
                platform=context.get("platform", "instagram"),
                content_theme=context.get("theme", ""),
            )
        elif task_type == "wordpress_theme":
            return self.task_factory.create_content_task(
                task_type=task_type,
                theme_spec=context.get("spec", {}),
                builder=context.get("builder", "elementor"),
            )
        
        # Security/Infrastructure tasks
        elif task_type == "scan":
            return self._generate_scan_task_prompt(context)
        elif task_type == "fix":
            return self._generate_fix_task_prompt(context)
        
        # Generic task
        else:
            return self._generate_generic_task_prompt(task_type, context)
    
    def _generate_scan_task_prompt(self, context: Dict[str, Any]) -> str:
        """Generate security scan task prompt."""
        return f"""
## TASK: Security Scan

### Target
{json.dumps(context.get('target', {}), indent=2)}

### Scan Configuration
- Scan Type: {context.get('scan_type', 'full')}
- Depth: {context.get('depth', 'comprehensive')}
- OWASP Categories: {', '.join(context.get('owasp_categories', ['all']))}

### Requirements
1. Identify all security vulnerabilities categorized by OWASP Top 10
2. Provide CVE references where applicable
3. Rate each finding by severity (Critical, High, Medium, Low)
4. Include remediation recommendations for each finding
5. Generate a compliance report (GDPR, PCI-DSS if applicable)

### Output Format
```json
{{
    "scan_id": "string",
    "timestamp": "ISO8601",
    "summary": {{
        "total_findings": number,
        "critical": number,
        "high": number,
        "medium": number,
        "low": number
    }},
    "findings": [
        {{
            "id": "string",
            "category": "OWASP category",
            "severity": "Critical|High|Medium|Low",
            "title": "string",
            "description": "string",
            "cve": "CVE-XXXX-XXXXX or null",
            "location": "file:line",
            "remediation": "string",
            "confidence": 0.0-1.0
        }}
    ],
    "compliance": {{
        "gdpr": {{"compliant": boolean, "issues": []}},
        "pci_dss": {{"compliant": boolean, "issues": []}}
    }}
}}
```
"""
    
    def _generate_fix_task_prompt(self, context: Dict[str, Any]) -> str:
        """Generate code fix task prompt."""
        return f"""
## TASK: Code Fix

### Issue
```
{context.get('error', 'No error provided')}
```

### Code Context
```{context.get('language', 'python')}
{context.get('code', 'No code provided')}
```

### Scan Findings (if applicable)
{json.dumps(context.get('scan_findings', []), indent=2)}

### Requirements
1. Fix the identified issue while preserving existing functionality
2. Do NOT introduce new vulnerabilities or regressions
3. Follow language-specific best practices and coding standards
4. Include inline comments explaining the fix
5. Provide unit tests to verify the fix

### Tree of Thoughts Approach
Consider multiple approaches:
- Approach A: [Minimal change fix]
- Approach B: [Refactored solution]
- Approach C: [Alternative implementation]

Evaluate each approach for:
- Correctness
- Performance impact
- Maintainability
- Side effects

Select the optimal approach with justification.

### Output Format
```json
{{
    "fix_id": "string",
    "approach_selected": "A|B|C",
    "justification": "string",
    "fixed_code": "string",
    "changes": [
        {{
            "line": number,
            "before": "string",
            "after": "string",
            "reason": "string"
        }}
    ],
    "tests": [
        {{
            "name": "string",
            "code": "string",
            "expected_result": "string"
        }}
    ],
    "verification": {{
        "syntax_valid": boolean,
        "tests_pass": boolean,
        "no_new_issues": boolean
    }}
}}
```
"""
    
    def _generate_generic_task_prompt(
        self,
        task_type: str,
        context: Dict[str, Any],
    ) -> str:
        """Generate a generic task prompt."""
        return f"""
## TASK: {task_type.replace('_', ' ').title()}

### Context
{json.dumps(context, indent=2, default=str)}

### Instructions
Execute the {task_type} task using the provided context. Apply the following techniques:

1. **Chain-of-Thought**: Break down the task into logical steps
2. **Self-Consistency**: Validate your reasoning at each step
3. **Quality Assurance**: Ensure output meets production standards

### Output Format
Return a structured JSON response with:
- `status`: "success" or "error"
- `result`: The task output
- `reasoning`: Step-by-step explanation
- `confidence`: Confidence score (0.0-1.0)
- `metadata`: Execution metadata
"""
    
    def _add_few_shot_examples(self, prompt: str, task_type: str) -> str:
        """Add few-shot examples to the prompt."""
        examples = self._get_few_shot_examples(task_type)
        if not examples:
            return prompt
        
        examples_section = "\n\n### Few-Shot Examples\n"
        for i, example in enumerate(examples, 1):
            examples_section += f"""
**Example {i}:**
Input: {example['input']}
Output: {example['output']}
Reasoning: {example.get('reasoning', 'N/A')}
"""
        
        return prompt + examples_section
    
    def _get_few_shot_examples(self, task_type: str) -> List[Dict[str, str]]:
        """Get few-shot examples for a task type."""
        examples_db = {
            "product_description": [
                {
                    "input": "Silk evening gown, navy blue, size S-XL, $299",
                    "output": "Embrace timeless elegance with our Navy Silk Evening Gown. Crafted from 100% pure mulberry silk, this floor-length masterpiece drapes beautifully over your silhouette...",
                    "reasoning": "Started with emotional hook, included material quality, implied exclusivity",
                },
            ],
            "scan": [
                {
                    "input": "Scan Python file with SQL queries",
                    "output": '{"findings": [{"category": "A03:2021 Injection", "severity": "Critical", "title": "SQL Injection", "location": "db.py:45"}]}',
                    "reasoning": "Identified string concatenation in SQL, classified as OWASP A03",
                },
            ],
        }
        return examples_db.get(task_type, [])[:3]  # Max 3 examples
    
    # =========================================================================
    # Full Prompt Generation
    # =========================================================================
    
    def get_full_prompt(
        self,
        agent_name: str,
        task_type: str,
        context: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        include_system: bool = True,
    ) -> Dict[str, str]:
        """
        Get the complete prompt package for an agent task.
        
        Args:
            agent_name: Name of the agent
            task_type: Type of task
            context: Task context
            priority: Task priority
            include_system: Whether to include system prompt
            
        Returns:
            Dict with 'system_prompt' and 'user_prompt' keys
        """
        result = {}
        
        if include_system:
            result["system_prompt"] = self.get_agent_system_prompt(agent_name)
        
        result["user_prompt"] = self.get_task_prompt(
            agent_name=agent_name,
            task_type=task_type,
            context=context,
            priority=priority,
        )
        
        return result
    
    # =========================================================================
    # Chain/Workflow Prompts
    # =========================================================================
    
    def get_workflow_prompts(
        self,
        workflow_name: str,
        initial_context: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """
        Get all prompts for a multi-agent workflow.
        
        Args:
            workflow_name: Name of predefined workflow
            initial_context: Initial workflow context
            
        Returns:
            List of prompt dicts for each step
        """
        workflow = self.chain_orchestrator.get_workflow(workflow_name)
        if not workflow:
            logger.warning(f"Workflow not found: {workflow_name}")
            return []
        
        return self.chain_orchestrator.generate_chain_prompts(
            workflow=workflow,
            context=initial_context,
        )
    
    async def execute_workflow(
        self,
        workflow_name: str,
        initial_context: Dict[str, Any],
        executor: Callable,
    ) -> Dict[str, Any]:
        """
        Execute a workflow using the provided executor function.
        
        Args:
            workflow_name: Name of predefined workflow
            initial_context: Initial workflow context
            executor: Async function to execute each step
            
        Returns:
            Workflow execution results
        """
        workflow = self.chain_orchestrator.get_workflow(workflow_name)
        if not workflow:
            return {"error": f"Workflow not found: {workflow_name}"}
        
        return await self.chain_orchestrator.execute_workflow(
            workflow=workflow,
            executor=executor,
        )
    
    # =========================================================================
    # Meta Prompts (for repo-building LLMs)
    # =========================================================================
    
    def get_meta_prompt(
        self,
        prompt_type: MetaPromptType,
        **kwargs,
    ) -> str:
        """
        Get a meta-prompt for LLMs building the DevSkyy repository.
        
        Args:
            prompt_type: Type of meta-prompt
            **kwargs: Prompt-specific parameters
            
        Returns:
            Meta-prompt string
        """
        return self.meta_factory.create(prompt_type, **kwargs)
    
    # =========================================================================
    # Metrics & Debugging
    # =========================================================================
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get prompt injection metrics."""
        return {
            "injection_count": self.injection_count,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hits / max(1, self.cache_hits + self.cache_misses),
            "system_prompts_cached": len(self._system_prompt_cache),
            "task_prompts_cached": len(self._task_prompt_cache),
        }
    
    def clear_cache(self):
        """Clear all prompt caches."""
        self._system_prompt_cache.clear()
        self._task_prompt_cache.clear()
        logger.info("Prompt caches cleared")


# =============================================================================
# Decorator for Agent Methods
# =============================================================================

def with_prompt_injection(
    task_type: str,
    priority: TaskPriority = TaskPriority.MEDIUM,
):
    """
    Decorator that automatically injects prompts into agent method calls.
    
    Usage:
        @with_prompt_injection(task_type="scan")
        async def scan(self, target: str) -> Dict[str, Any]:
            # self.injected_prompt contains the generated prompt
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get the injector (assume it's on the agent instance)
            injector = getattr(self, '_prompt_injector', None)
            if not injector:
                injector = PromptInjector()
                self._prompt_injector = injector
            
            # Generate prompt
            context = {
                "args": args,
                "kwargs": kwargs,
            }
            
            prompts = injector.get_full_prompt(
                agent_name=self.__class__.__name__,
                task_type=task_type,
                context=context,
                priority=priority,
            )
            
            # Inject into instance
            self.injected_system_prompt = prompts.get("system_prompt", "")
            self.injected_task_prompt = prompts.get("user_prompt", "")
            
            # Call original method
            return await func(self, *args, **kwargs)
        
        return wrapper
    return decorator


# =============================================================================
# Factory Functions
# =============================================================================

_global_injector: Optional[PromptInjector] = None


def get_prompt_injector(config: Optional[PromptInjectionConfig] = None) -> PromptInjector:
    """Get or create the global prompt injector instance."""
    global _global_injector
    if _global_injector is None:
        _global_injector = PromptInjector(config)
    return _global_injector


def inject_prompt(
    agent_name: str,
    task_type: str,
    context: Dict[str, Any],
    priority: TaskPriority = TaskPriority.MEDIUM,
) -> Dict[str, str]:
    """
    Convenience function to inject prompts.
    
    Usage:
        prompts = inject_prompt("ScannerAgent", "scan", {"target": "/src"})
        system_prompt = prompts["system_prompt"]
        user_prompt = prompts["user_prompt"]
    """
    injector = get_prompt_injector()
    return injector.get_full_prompt(
        agent_name=agent_name,
        task_type=task_type,
        context=context,
        priority=priority,
    )


# =============================================================================
# Main - Testing
# =============================================================================

if __name__ == "__main__":
    # Test the prompt injector
    logging.basicConfig(level=logging.INFO)
    
    injector = PromptInjector()
    
    # Test system prompt generation
    print("=" * 80)
    print("SCANNER AGENT SYSTEM PROMPT")
    print("=" * 80)
    system_prompt = injector.get_agent_system_prompt("ScannerAgent")
    print(system_prompt[:2000] + "..." if len(system_prompt) > 2000 else system_prompt)
    
    # Test task prompt generation
    print("\n" + "=" * 80)
    print("SCAN TASK PROMPT")
    print("=" * 80)
    task_prompt = injector.get_task_prompt(
        agent_name="ScannerAgent",
        task_type="scan",
        context={"target": "/src", "scan_type": "security", "depth": "comprehensive"},
    )
    print(task_prompt)
    
    # Test full prompt
    print("\n" + "=" * 80)
    print("FULL PROMPT PACKAGE")
    print("=" * 80)
    full = injector.get_full_prompt(
        agent_name="ProductManagerAgent",
        task_type="product_description",
        context={
            "product": {
                "name": "Silk Evening Gown",
                "price": 299.00,
                "category": "dresses",
            }
        },
    )
    print(f"System prompt length: {len(full['system_prompt'])} chars")
    print(f"User prompt length: {len(full['user_prompt'])} chars")
    
    # Metrics
    print("\n" + "=" * 80)
    print("METRICS")
    print("=" * 80)
    print(json.dumps(injector.get_metrics(), indent=2))

