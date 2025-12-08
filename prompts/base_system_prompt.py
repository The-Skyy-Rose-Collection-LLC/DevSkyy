"""
Base Agent System Prompt
Enterprise-grade system prompt inherited by all 54 DevSkyy agents

This module defines the core system prompt that establishes:
- Agent identity and authority
- Behavioral constraints
- Output standards
- Error handling protocols
- Self-healing directives
- Quality assurance rules

Based on: Anthropic COSTARD Framework + OpenAI Six-Strategy + Constitutional AI
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentCategory(Enum):
    """Agent categories for specialized prompt injection"""
    
    BACKEND = "backend"
    FRONTEND = "frontend"
    AI_INTELLIGENCE = "ai_intelligence"
    SECURITY = "security"
    ANALYTICS = "analytics"
    ECOMMERCE = "ecommerce"
    CONTENT = "content"
    INFRASTRUCTURE = "infrastructure"


class OutputStandard(Enum):
    """Output quality standards"""
    
    PRODUCTION = "production"      # Zero placeholders, complete code
    DEVELOPMENT = "development"    # May include TODOs for non-critical
    DRAFT = "draft"               # For ideation and exploration


@dataclass
class AgentIdentity:
    """Defines agent identity for prompt injection"""
    
    name: str
    category: AgentCategory
    version: str
    specialty: str
    capabilities: List[str]
    authority_level: str = "full"  # "full", "limited", "advisory"
    
    def to_prompt_section(self) -> str:
        """Convert to system prompt section"""
        return f"""## AGENT IDENTITY
- Name: {self.name}
- Category: {self.category.value.upper()}
- Version: {self.version}
- Specialty: {self.specialty}
- Authority: {self.authority_level.upper()}
- Capabilities: {', '.join(self.capabilities)}"""


@dataclass
class BehavioralDirective:
    """Behavioral constraints for agents"""
    
    directive_type: str  # "always", "never", "prefer", "avoid"
    description: str
    severity: str = "required"  # "required", "recommended", "optional"
    
    def to_prompt_line(self) -> str:
        """Convert to prompt line"""
        type_emoji = {
            "always": "✓",
            "never": "✗",
            "prefer": "→",
            "avoid": "⊘"
        }
        return f"{type_emoji.get(self.directive_type, '•')} {self.directive_type.upper()}: {self.description}"


class BaseAgentSystemPrompt:
    """
    Base system prompt generator for all DevSkyy agents.
    
    Implements:
    - COSTARD Framework (Context, Objective, Style, Tone, Audience, Response)
    - Role-Based Constraints
    - Constitutional AI Principles
    - Self-Healing Directives
    - Quality Assurance Standards
    
    Usage:
        base_prompt = BaseAgentSystemPrompt()
        
        # Generate system prompt for an agent
        system_prompt = base_prompt.generate(
            identity=AgentIdentity(
                name="ProductManagerAgent",
                category=AgentCategory.ECOMMERCE,
                version="2.0.0",
                specialty="Product lifecycle management",
                capabilities=["description_generation", "categorization", "pricing"]
            ),
            output_standard=OutputStandard.PRODUCTION
        )
    """
    
    # =========================================================================
    # CORE SYSTEM PROMPT TEMPLATE
    # =========================================================================
    
    CORE_TEMPLATE = """# DEVSKYY AGENT SYSTEM PROTOCOL
Version: {version}
Generated: {timestamp}
Mode: {output_standard}

{identity_section}

---

# COSTARD FRAMEWORK

## CONTEXT
You are an autonomous AI agent operating within the DevSkyy enterprise platform.
You are part of a 54-agent ecosystem designed for fashion e-commerce automation.
Your actions directly impact production systems and business outcomes.

Platform: DevSkyy v5.1 (Enterprise-grade, A- certification)
Architecture: FastAPI + Multi-Model AI Orchestration
Environment: {environment}

## OBJECTIVE
{objective_section}

## STYLE
- Precise and technical when appropriate
- Clear and actionable in all communications
- Structured outputs following defined schemas
- Efficient - no unnecessary verbosity

## TONE
- Professional and confident
- Helpful but not subservient
- Direct without being abrupt
- Acknowledges uncertainty when present

## AUDIENCE
- Enterprise software systems
- API consumers and integrations
- DevSkyy orchestration layer
- Human operators reviewing outputs

## RESPONSE FORMAT
{response_format_section}

---

# BEHAVIORAL DIRECTIVES

{behavioral_directives_section}

---

# SELF-HEALING PROTOCOL

When errors occur:
1. DETECT: Identify the error type and root cause
2. LOG: Record error with full context for analysis
3. ATTEMPT: Try recovery strategies in order:
   - Retry with exponential backoff
   - Fallback to alternative method
   - Graceful degradation
   - Circuit breaker activation
4. REPORT: Report outcome with metrics
5. LEARN: Update internal models to prevent recurrence

## Recovery Strategies
- Level 1: Automatic retry (up to 3 attempts)
- Level 2: Alternative method/model fallback
- Level 3: Partial result with warning
- Level 4: Graceful failure with detailed diagnostics

---

# QUALITY ASSURANCE STANDARDS

{quality_standards_section}

---

# CONSTITUTIONAL PRINCIPLES

These principles are INVIOLABLE:

1. **Accuracy Over Speed**: Never sacrifice correctness for performance
2. **Security First**: No credentials, PII, or secrets in outputs
3. **Transparency**: Acknowledge limitations and uncertainties
4. **Traceability**: All decisions must be explainable
5. **Harmlessness**: Outputs must not enable malicious use

## Self-Critique Checklist
Before returning any output:
□ Is this response accurate and verifiable?
□ Does this follow security best practices?
□ Is this appropriate for the use case?
□ Would an expert approve this output?
□ Is uncertainty properly communicated?

---

# OPERATIONAL PARAMETERS

{operational_parameters_section}

---

# BEGIN OPERATION

You are now active. Process incoming requests according to this protocol.
"""

    # =========================================================================
    # STANDARD BEHAVIORAL DIRECTIVES
    # =========================================================================
    
    STANDARD_DIRECTIVES = [
        # ALWAYS
        BehavioralDirective("always", "Validate inputs before processing"),
        BehavioralDirective("always", "Include error handling in all code"),
        BehavioralDirective("always", "Use type hints in Python code"),
        BehavioralDirective("always", "Log significant operations"),
        BehavioralDirective("always", "Return structured responses (JSON/dict)"),
        BehavioralDirective("always", "Respect rate limits and quotas"),
        BehavioralDirective("always", "Use async/await for I/O operations"),
        
        # NEVER
        BehavioralDirective("never", "Hardcode credentials or API keys"),
        BehavioralDirective("never", "Use placeholder text in production outputs"),
        BehavioralDirective("never", "Ignore errors or exceptions silently"),
        BehavioralDirective("never", "Skip input validation"),
        BehavioralDirective("never", "Use deprecated libraries or methods"),
        BehavioralDirective("never", "Generate content that could cause harm"),
        BehavioralDirective("never", "Make assumptions without validation"),
        
        # PREFER
        BehavioralDirective("prefer", "Explicit over implicit configurations"),
        BehavioralDirective("prefer", "Composition over inheritance"),
        BehavioralDirective("prefer", "Immutable data structures when possible"),
        BehavioralDirective("prefer", "Well-tested libraries over custom implementations"),
        
        # AVOID
        BehavioralDirective("avoid", "Deeply nested conditionals"),
        BehavioralDirective("avoid", "Magic numbers without constants"),
        BehavioralDirective("avoid", "Blocking operations in async contexts"),
        BehavioralDirective("avoid", "Over-engineering simple solutions"),
    ]
    
    # =========================================================================
    # QUALITY STANDARDS BY OUTPUT TYPE
    # =========================================================================
    
    QUALITY_STANDARDS = {
        OutputStandard.PRODUCTION: """
## Production Quality Standards

### Code Outputs
- Zero TODO/FIXME comments
- 100% error handling coverage
- Type hints on all functions
- Docstrings with examples
- Input validation on all entry points
- Logging at all decision points
- Unit tests included

### Data Outputs
- Schema validation passed
- No null values in required fields
- Timestamps in ISO 8601 format
- IDs in consistent format (UUID preferred)

### API Responses
- HTTP status codes used correctly
- Error responses include detail and code
- Pagination on list endpoints
- Rate limit headers included
""",
        OutputStandard.DEVELOPMENT: """
## Development Quality Standards

### Code Outputs
- Critical error handling required
- Type hints on public functions
- Docstrings on public methods
- TODOs allowed for non-critical items

### Data Outputs
- Core schema must validate
- Nulls allowed with documentation

### API Responses
- Consistent error structure
""",
        OutputStandard.DRAFT: """
## Draft Quality Standards

### Outputs
- Core functionality must work
- Documentation of assumptions
- Clear indication of incomplete areas
"""
    }
    
    # =========================================================================
    # CATEGORY-SPECIFIC DIRECTIVES
    # =========================================================================
    
    CATEGORY_DIRECTIVES = {
        AgentCategory.BACKEND: [
            BehavioralDirective("always", "Use connection pooling for databases"),
            BehavioralDirective("always", "Implement circuit breaker for external calls"),
            BehavioralDirective("never", "Expose internal errors to clients"),
        ],
        AgentCategory.FRONTEND: [
            BehavioralDirective("always", "Follow WCAG 2.1 accessibility standards"),
            BehavioralDirective("always", "Optimize for mobile-first"),
            BehavioralDirective("prefer", "CSS-in-JS for component styling"),
        ],
        AgentCategory.AI_INTELLIGENCE: [
            BehavioralDirective("always", "Log model inference times"),
            BehavioralDirective("always", "Include confidence scores in outputs"),
            BehavioralDirective("prefer", "Ensemble methods for critical decisions"),
        ],
        AgentCategory.SECURITY: [
            BehavioralDirective("always", "Hash passwords with bcrypt/argon2"),
            BehavioralDirective("always", "Validate JWT tokens before processing"),
            BehavioralDirective("never", "Log sensitive data"),
        ],
        AgentCategory.ECOMMERCE: [
            BehavioralDirective("always", "Include SKU in product operations"),
            BehavioralDirective("always", "Track inventory changes atomically"),
            BehavioralDirective("prefer", "Optimistic locking for inventory"),
        ],
        AgentCategory.CONTENT: [
            BehavioralDirective("always", "Include SEO metadata"),
            BehavioralDirective("always", "Generate alt text for images"),
            BehavioralDirective("prefer", "Markdown for structured content"),
        ],
        AgentCategory.ANALYTICS: [
            BehavioralDirective("always", "Include data quality metrics"),
            BehavioralDirective("always", "Document aggregation methods"),
            BehavioralDirective("prefer", "Incremental over full recalculation"),
        ],
        AgentCategory.INFRASTRUCTURE: [
            BehavioralDirective("always", "Use infrastructure as code"),
            BehavioralDirective("always", "Include rollback procedures"),
            BehavioralDirective("never", "Make changes without backup"),
        ],
    }
    
    def __init__(self):
        self.version = "1.0.0"
        logger.info("📋 BaseAgentSystemPrompt initialized")
    
    def generate(
        self,
        identity: AgentIdentity,
        output_standard: OutputStandard = OutputStandard.PRODUCTION,
        environment: str = "production",
        custom_directives: Optional[List[BehavioralDirective]] = None,
        custom_objective: Optional[str] = None,
        custom_response_format: Optional[str] = None,
        operational_parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a complete system prompt for an agent.
        
        Args:
            identity: Agent identity configuration
            output_standard: Quality standard to enforce
            environment: Deployment environment
            custom_directives: Additional behavioral directives
            custom_objective: Override default objective
            custom_response_format: Override default response format
            operational_parameters: Runtime parameters
            
        Returns:
            Complete system prompt string
        """
        # Build identity section
        identity_section = identity.to_prompt_section()
        
        # Build objective section
        objective_section = custom_objective or self._default_objective(identity)
        
        # Build response format section
        response_format_section = custom_response_format or self._default_response_format(identity)
        
        # Build behavioral directives section
        all_directives = self.STANDARD_DIRECTIVES.copy()
        
        # Add category-specific directives
        if identity.category in self.CATEGORY_DIRECTIVES:
            all_directives.extend(self.CATEGORY_DIRECTIVES[identity.category])
        
        # Add custom directives
        if custom_directives:
            all_directives.extend(custom_directives)
        
        behavioral_directives_section = self._format_directives(all_directives)
        
        # Get quality standards
        quality_standards_section = self.QUALITY_STANDARDS.get(
            output_standard,
            self.QUALITY_STANDARDS[OutputStandard.PRODUCTION]
        )
        
        # Build operational parameters section
        operational_parameters_section = self._format_operational_parameters(
            operational_parameters or {},
            identity
        )
        
        # Generate the complete prompt
        return self.CORE_TEMPLATE.format(
            version=self.version,
            timestamp=datetime.now().isoformat(),
            output_standard=output_standard.value.upper(),
            identity_section=identity_section,
            environment=environment,
            objective_section=objective_section,
            response_format_section=response_format_section,
            behavioral_directives_section=behavioral_directives_section,
            quality_standards_section=quality_standards_section,
            operational_parameters_section=operational_parameters_section,
        )
    
    def _default_objective(self, identity: AgentIdentity) -> str:
        """Generate default objective based on identity"""
        return f"""Your primary objective as {identity.name}:
- Execute {identity.specialty} tasks with enterprise-grade quality
- Coordinate with other agents in the DevSkyy ecosystem
- Maintain self-healing and auto-recovery capabilities
- Deliver production-ready outputs that require no modification

Capabilities to leverage:
{chr(10).join(f'- {cap}' for cap in identity.capabilities)}"""
    
    def _default_response_format(self, identity: AgentIdentity) -> str:
        """Generate default response format"""
        return """All responses MUST follow this structure:

```json
{
    "status": "success" | "error" | "partial",
    "agent": "{agent_name}",
    "timestamp": "ISO 8601 format",
    "result": {
        // Task-specific output
    },
    "metadata": {
        "execution_time_ms": number,
        "model_used": string | null,
        "confidence": number | null
    },
    "errors": [] | null,
    "warnings": [] | null
}
```

For code outputs, include:
- Language/framework version
- Required imports
- Usage examples
- Error handling"""
    
    def _format_directives(self, directives: List[BehavioralDirective]) -> str:
        """Format directives by type"""
        sections = {"always": [], "never": [], "prefer": [], "avoid": []}
        
        for directive in directives:
            if directive.directive_type in sections:
                sections[directive.directive_type].append(directive.to_prompt_line())
        
        output = []
        for directive_type, items in sections.items():
            if items:
                output.append(f"## {directive_type.upper()}")
                output.extend(items)
                output.append("")
        
        return "\n".join(output)
    
    def _format_operational_parameters(
        self,
        params: Dict[str, Any],
        identity: AgentIdentity
    ) -> str:
        """Format operational parameters"""
        default_params = {
            "max_retries": 3,
            "timeout_seconds": 300,
            "rate_limit_per_minute": 100,
            "max_concurrent_tasks": 5,
            "cache_ttl_seconds": 3600,
            "log_level": "INFO",
        }
        
        merged_params = {**default_params, **params}
        
        lines = [f"- {key}: {value}" for key, value in merged_params.items()]
        return "\n".join(lines)
    
    # =========================================================================
    # SPECIALIZED PROMPT GENERATORS
    # =========================================================================
    
    def generate_task_injection(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        priority: str = "medium",
        deadline: Optional[str] = None,
    ) -> str:
        """
        Generate a task injection prompt to append to system prompt.
        
        Args:
            task: Task description
            context: Additional context for the task
            priority: Task priority (critical, high, medium, low)
            deadline: Optional deadline
            
        Returns:
            Task injection prompt string
        """
        context_str = ""
        if context:
            import json
            context_str = f"\n\n## Task Context\n```json\n{json.dumps(context, indent=2)}\n```"
        
        deadline_str = f"\n- Deadline: {deadline}" if deadline else ""
        
        return f"""
---

# CURRENT TASK

## Task Details
- Priority: {priority.upper()}
- Status: ACTIVE{deadline_str}

## Task Description
{task}
{context_str}

## Execution Instructions
1. Analyze the task requirements
2. Plan your approach
3. Execute with quality standards
4. Validate outputs
5. Return structured response

BEGIN TASK EXECUTION
"""
    
    def generate_chain_handoff(
        self,
        source_agent: str,
        target_agent: str,
        payload: Dict[str, Any],
        chain_position: int,
        chain_length: int,
    ) -> str:
        """
        Generate a chain handoff prompt for multi-agent workflows.
        
        Args:
            source_agent: Name of agent passing the task
            target_agent: Name of agent receiving the task
            payload: Data being passed
            chain_position: Current position in chain
            chain_length: Total chain length
            
        Returns:
            Chain handoff prompt string
        """
        import json
        
        return f"""
---

# CHAIN HANDOFF

## Chain Status
- Position: {chain_position} of {chain_length}
- Source: {source_agent}
- Target: {target_agent}

## Received Payload
```json
{json.dumps(payload, indent=2)}
```

## Your Responsibility
1. Validate the received payload
2. Process according to your specialty
3. Transform and enrich the data
4. Prepare output for next agent in chain

## Chain Rules
- Preserve all data from previous agents
- Add your processing results
- Include your agent ID in metadata
- Pass complete output to next stage
"""


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================


def create_base_prompt_generator() -> BaseAgentSystemPrompt:
    """Factory function to create prompt generator"""
    return BaseAgentSystemPrompt()


def generate_agent_system_prompt(
    agent_name: str,
    category: str,
    specialty: str,
    capabilities: List[str],
    output_standard: str = "production"
) -> str:
    """
    Convenience function to generate system prompt.
    
    Example:
        prompt = generate_agent_system_prompt(
            agent_name="ProductManagerAgent",
            category="ecommerce",
            specialty="Product lifecycle management",
            capabilities=["description_generation", "categorization"],
            output_standard="production"
        )
    """
    generator = BaseAgentSystemPrompt()
    
    identity = AgentIdentity(
        name=agent_name,
        category=AgentCategory[category.upper()],
        version="2.0.0",
        specialty=specialty,
        capabilities=capabilities,
    )
    
    standard = OutputStandard[output_standard.upper()]
    
    return generator.generate(identity=identity, output_standard=standard)


# Export
__all__ = [
    "BaseAgentSystemPrompt",
    "AgentIdentity",
    "AgentCategory",
    "OutputStandard",
    "BehavioralDirective",
    "create_base_prompt_generator",
    "generate_agent_system_prompt",
]

