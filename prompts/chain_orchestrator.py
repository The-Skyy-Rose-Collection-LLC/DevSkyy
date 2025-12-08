"""
Prompt Chain Orchestrator
Manages prompt chaining for multi-agent workflows

This module handles the orchestration of prompts across multiple agents,
implementing the Prompt Chaining technique for complex workflows.

Workflow Types:
- Sequential: A → B → C
- Parallel: [A, B] → C
- Conditional: A → (if X then B else C) → D
- Loop: A → B → (repeat if condition) → C
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .base_system_prompt import BaseAgentSystemPrompt
from .technique_engine import PromptTechniqueEngine

logger = logging.getLogger(__name__)


class ChainStepType(Enum):
    """Types of chain steps"""
    
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    AGGREGATE = "aggregate"


class ChainStatus(Enum):
    """Status of a chain execution"""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ChainStep:
    """A step in the prompt chain"""
    
    step_id: str
    agent_name: str
    step_type: ChainStepType = ChainStepType.SEQUENTIAL
    task_template: Optional[str] = None
    input_mapping: Dict[str, str] = field(default_factory=dict)  # Maps previous outputs to this step's inputs
    condition: Optional[str] = None  # For conditional steps
    max_iterations: int = 1  # For loop steps
    timeout_seconds: int = 300
    retry_count: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "step_id": self.step_id,
            "agent_name": self.agent_name,
            "step_type": self.step_type.value,
            "task_template": self.task_template,
            "input_mapping": self.input_mapping,
            "condition": self.condition,
            "max_iterations": self.max_iterations,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass
class ChainResult:
    """Result from a chain step execution"""
    
    step_id: str
    agent_name: str
    status: ChainStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "step_id": self.step_id,
            "agent_name": self.agent_name,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class WorkflowDefinition:
    """Defines a complete workflow"""
    
    workflow_id: str
    name: str
    description: str
    steps: List[ChainStep]
    initial_context: Dict[str, Any] = field(default_factory=dict)
    final_aggregation: Optional[str] = None  # How to combine results
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "initial_context": self.initial_context,
            "final_aggregation": self.final_aggregation,
        }


class PromptChainOrchestrator:
    """
    Orchestrates prompt chains across multiple agents.
    
    Supports:
    - Sequential chains
    - Parallel execution
    - Conditional branching
    - Loop/iteration patterns
    - Context passing between steps
    - Error handling and retry
    
    Usage:
        orchestrator = PromptChainOrchestrator()
        
        # Define a workflow
        workflow = orchestrator.create_workflow(
            name="Product Launch",
            steps=[
                ChainStep("analyze", "ScannerAgent", task_template="Analyze product data"),
                ChainStep("price", "DynamicPricingAgent", input_mapping={"analysis": "analyze.output"}),
                ChainStep("describe", "ProductManagerAgent", input_mapping={"pricing": "price.output"}),
            ]
        )
        
        # Generate chain prompts
        prompts = orchestrator.generate_chain_prompts(workflow)
        
        # Execute workflow (requires executor implementation)
        results = await orchestrator.execute_workflow(workflow, executor_func)
    """
    
    def __init__(self):
        self.base_prompt_generator = BaseAgentSystemPrompt()
        self.technique_engine = PromptTechniqueEngine()
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._predefined_workflows = self._initialize_predefined_workflows()
        logger.info("🔗 PromptChainOrchestrator initialized")
    
    def _initialize_predefined_workflows(self) -> Dict[str, WorkflowDefinition]:
        """Initialize common predefined workflows"""
        
        workflows = {}
        
        # Product Launch Workflow
        workflows["product_launch"] = WorkflowDefinition(
            workflow_id="wf_product_launch",
            name="Product Launch Workflow",
            description="Complete workflow for launching a new product",
            steps=[
                ChainStep(
                    step_id="analyze",
                    agent_name="ScannerAgent",
                    task_template="Analyze the product data and identify key features, target audience, and competitive positioning."
                ),
                ChainStep(
                    step_id="price",
                    agent_name="DynamicPricingAgent",
                    task_template="Based on the analysis, determine optimal pricing strategy.",
                    input_mapping={"product_analysis": "analyze.output"}
                ),
                ChainStep(
                    step_id="describe",
                    agent_name="ProductManagerAgent",
                    task_template="Generate compelling product descriptions using the analysis and pricing.",
                    input_mapping={
                        "analysis": "analyze.output",
                        "pricing": "price.output"
                    }
                ),
                ChainStep(
                    step_id="seo",
                    agent_name="SEOOptimizerAgent",
                    task_template="Optimize the product content for search engines.",
                    input_mapping={"product_content": "describe.output"}
                ),
                ChainStep(
                    step_id="theme",
                    agent_name="WordPressThemeBuilderAgent",
                    task_template="Create a landing page for the product.",
                    input_mapping={
                        "content": "describe.output",
                        "seo": "seo.output"
                    }
                ),
            ],
            final_aggregation="Combine all outputs into a complete product launch package."
        )
        
        # Security Audit Workflow
        workflows["security_audit"] = WorkflowDefinition(
            workflow_id="wf_security_audit",
            name="Security Audit Workflow",
            description="Comprehensive security audit and remediation",
            steps=[
                ChainStep(
                    step_id="scan",
                    agent_name="ScannerAgent",
                    task_template="Perform comprehensive security scan of the codebase."
                ),
                ChainStep(
                    step_id="analyze",
                    agent_name="SelfHealingAgent",
                    task_template="Analyze scan results and prioritize vulnerabilities.",
                    input_mapping={"vulnerabilities": "scan.output"}
                ),
                ChainStep(
                    step_id="fix",
                    agent_name="FixerAgent",
                    step_type=ChainStepType.LOOP,
                    task_template="Fix each vulnerability in priority order.",
                    input_mapping={"issues": "analyze.output"},
                    max_iterations=10
                ),
                ChainStep(
                    step_id="verify",
                    agent_name="ScannerAgent",
                    task_template="Re-scan to verify all fixes are complete.",
                    input_mapping={"previous_scan": "scan.output"}
                ),
            ]
        )
        
        # Customer Analysis Workflow
        workflows["customer_analysis"] = WorkflowDefinition(
            workflow_id="wf_customer_analysis",
            name="Customer Analysis Workflow",
            description="Comprehensive customer segmentation and analysis",
            steps=[
                ChainStep(
                    step_id="segment",
                    agent_name="CustomerIntelligenceAgent",
                    task_template="Segment customers based on RFM analysis."
                ),
                ChainStep(
                    step_id="analyze_segments",
                    agent_name="CustomerIntelligenceAgent",
                    step_type=ChainStepType.PARALLEL,
                    task_template="Deep-dive analysis for each segment.",
                    input_mapping={"segments": "segment.output"}
                ),
                ChainStep(
                    step_id="personalize",
                    agent_name="ProductManagerAgent",
                    task_template="Create personalized recommendations for each segment.",
                    input_mapping={"segment_analysis": "analyze_segments.output"}
                ),
                ChainStep(
                    step_id="dashboard",
                    agent_name="AnalyticsDashboardAgent",
                    task_template="Generate customer insights dashboard.",
                    input_mapping={
                        "segments": "segment.output",
                        "analysis": "analyze_segments.output",
                        "recommendations": "personalize.output"
                    }
                ),
            ]
        )
        
        # Content Pipeline Workflow
        workflows["content_pipeline"] = WorkflowDefinition(
            workflow_id="wf_content_pipeline",
            name="Content Pipeline Workflow",
            description="End-to-end content creation and optimization",
            steps=[
                ChainStep(
                    step_id="research",
                    agent_name="ClaudeAIAgent",
                    task_template="Research the topic and outline key points."
                ),
                ChainStep(
                    step_id="write",
                    agent_name="ClaudeAIAgent",
                    task_template="Write the content based on research.",
                    input_mapping={"research": "research.output"}
                ),
                ChainStep(
                    step_id="optimize",
                    agent_name="SEOOptimizerAgent",
                    task_template="Optimize content for SEO.",
                    input_mapping={"content": "write.output"}
                ),
                ChainStep(
                    step_id="format",
                    agent_name="WordPressThemeBuilderAgent",
                    task_template="Format content for WordPress publication.",
                    input_mapping={
                        "content": "write.output",
                        "seo": "optimize.output"
                    }
                ),
            ]
        )
        
        return workflows
    
    # =========================================================================
    # WORKFLOW MANAGEMENT
    # =========================================================================
    
    def create_workflow(
        self,
        name: str,
        steps: List[ChainStep],
        description: str = "",
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowDefinition:
        """
        Create a new workflow definition.
        
        Args:
            name: Workflow name
            steps: List of chain steps
            description: Workflow description
            initial_context: Initial context data
            
        Returns:
            WorkflowDefinition
        """
        import uuid
        
        workflow = WorkflowDefinition(
            workflow_id=f"wf_{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            steps=steps,
            initial_context=initial_context or {},
        )
        
        self._workflows[workflow.workflow_id] = workflow
        logger.info(f"Created workflow: {name} ({workflow.workflow_id})")
        
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow by ID"""
        return self._workflows.get(workflow_id) or self._predefined_workflows.get(workflow_id)
    
    def list_workflows(self) -> List[Dict[str, str]]:
        """List all available workflows"""
        workflows = []
        
        for wf in self._predefined_workflows.values():
            workflows.append({
                "id": wf.workflow_id,
                "name": wf.name,
                "description": wf.description,
                "type": "predefined"
            })
        
        for wf in self._workflows.values():
            workflows.append({
                "id": wf.workflow_id,
                "name": wf.name,
                "description": wf.description,
                "type": "custom"
            })
        
        return workflows
    
    # =========================================================================
    # PROMPT GENERATION
    # =========================================================================
    
    def generate_chain_prompts(
        self,
        workflow: WorkflowDefinition,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """
        Generate prompts for all steps in a workflow.
        
        Args:
            workflow: Workflow definition
            context: Runtime context to inject
            
        Returns:
            Dictionary mapping step_id to complete prompt
        """
        prompts = {}
        merged_context = {**workflow.initial_context, **(context or {})}
        
        for i, step in enumerate(workflow.steps):
            prompt = self._generate_step_prompt(
                step=step,
                step_index=i,
                total_steps=len(workflow.steps),
                workflow=workflow,
                context=merged_context,
            )
            prompts[step.step_id] = prompt
        
        return prompts
    
    def _generate_step_prompt(
        self,
        step: ChainStep,
        step_index: int,
        total_steps: int,
        workflow: WorkflowDefinition,
        context: Dict[str, Any],
    ) -> str:
        """Generate prompt for a single step"""
        
        # Create chain context header
        chain_header = f"""
# CHAIN EXECUTION CONTEXT

## Workflow: {workflow.name}
## Step: {step_index + 1} of {total_steps}
## Agent: {step.agent_name}
## Step ID: {step.step_id}
## Step Type: {step.step_type.value}

---
"""
        
        # Create input mapping section
        input_section = ""
        if step.input_mapping:
            input_section = """
## INPUTS FROM PREVIOUS STEPS
The following data has been passed from previous steps in the chain:

```json
{inputs}
```

USE THESE INPUTS to inform your processing. Reference specific fields as needed.

---
""".format(inputs=json.dumps(self._resolve_input_mapping(step.input_mapping, context), indent=2))
        
        # Create task section
        task_section = f"""
## YOUR TASK
{step.task_template or "[Task will be provided at runtime]"}

---
"""
        
        # Create output expectations section
        output_section = """
## OUTPUT REQUIREMENTS
Your output will be passed to subsequent steps in the chain. Ensure:

1. **Structured Format**: Return JSON with clear keys
2. **Complete Information**: Include all data needed by downstream steps
3. **Quality Standards**: Follow production quality guidelines
4. **Metadata**: Include execution metadata

### Output Schema
```json
{{
    "step_id": "{step_id}",
    "agent": "{agent_name}",
    "status": "success" | "error",
    "output": {{
        // Your step-specific output
    }},
    "metadata": {{
        "timestamp": "ISO 8601",
        "execution_time_ms": number,
        "confidence": number | null
    }},
    "for_next_step": {{
        // Data specifically prepared for the next step
    }}
}}
```

---
""".format(step_id=step.step_id, agent_name=step.agent_name)
        
        # Create step-type specific sections
        type_section = self._generate_type_specific_section(step)
        
        # Combine all sections
        full_prompt = chain_header + input_section + task_section + output_section + type_section
        
        # Add execution instruction
        full_prompt += """
# BEGIN CHAIN STEP EXECUTION

Process this step according to the chain protocol. Your output will feed into subsequent steps.
"""
        
        return full_prompt
    
    def _generate_type_specific_section(self, step: ChainStep) -> str:
        """Generate step-type specific prompt sections"""
        
        if step.step_type == ChainStepType.CONDITIONAL:
            return f"""
## CONDITIONAL EXECUTION
This step has a condition: `{step.condition}`

Evaluate the condition based on inputs and:
- If TRUE: Execute the task normally
- If FALSE: Return `{{"skipped": true, "reason": "Condition not met"}}`

---
"""
        
        elif step.step_type == ChainStepType.LOOP:
            return f"""
## LOOP EXECUTION
This step may iterate up to {step.max_iterations} times.

For each iteration:
1. Process the current item/batch
2. Update the iteration context
3. Check if more iterations needed
4. Continue or exit

Track iteration progress in output:
```json
{{
    "iteration": current_number,
    "total_processed": count,
    "remaining": count,
    "continue": boolean
}}
```

---
"""
        
        elif step.step_type == ChainStepType.PARALLEL:
            return """
## PARALLEL EXECUTION
This step runs in parallel with other steps.

- Process independently
- Do not assume outputs from other parallel steps
- Include timing for coordination

---
"""
        
        elif step.step_type == ChainStepType.AGGREGATE:
            return """
## AGGREGATION STEP
This step aggregates outputs from previous steps.

Combine all inputs into a unified output:
- Merge data structures
- Resolve conflicts
- Summarize findings
- Prepare final deliverable

---
"""
        
        return ""
    
    def _resolve_input_mapping(
        self,
        mapping: Dict[str, str],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Resolve input mapping references to actual values"""
        resolved = {}
        
        for key, ref in mapping.items():
            # Parse reference like "step_id.output" or "step_id.output.field"
            parts = ref.split(".")
            value = context
            
            try:
                for part in parts:
                    if isinstance(value, dict):
                        value = value.get(part, f"[Unresolved: {ref}]")
                    else:
                        value = f"[Unresolved: {ref}]"
                        break
                resolved[key] = value
            except Exception:
                resolved[key] = f"[Error resolving: {ref}]"
        
        return resolved
    
    # =========================================================================
    # HANDOFF PROMPT GENERATION
    # =========================================================================
    
    def generate_handoff_prompt(
        self,
        source_step: ChainStep,
        target_step: ChainStep,
        source_output: Dict[str, Any],
        workflow: WorkflowDefinition,
    ) -> str:
        """
        Generate a handoff prompt between two steps.
        
        Args:
            source_step: The step that just completed
            target_step: The step that will receive the handoff
            source_output: Output from the source step
            workflow: The workflow definition
            
        Returns:
            Handoff prompt string
        """
        return self.base_prompt_generator.generate_chain_handoff(
            source_agent=source_step.agent_name,
            target_agent=target_step.agent_name,
            payload=source_output,
            chain_position=workflow.steps.index(target_step) + 1,
            chain_length=len(workflow.steps),
        )
    
    # =========================================================================
    # EXECUTION HELPERS
    # =========================================================================
    
    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        executor: Callable[[str, str, Dict[str, Any]], Any],
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, ChainResult]:
        """
        Execute a workflow using the provided executor function.
        
        Args:
            workflow: Workflow to execute
            executor: Async function(agent_name, prompt, context) -> result
            initial_context: Initial context data
            
        Returns:
            Dictionary mapping step_id to ChainResult
        """
        results: Dict[str, ChainResult] = {}
        context = {**workflow.initial_context, **(initial_context or {})}
        
        for i, step in enumerate(workflow.steps):
            logger.info(f"Executing step {i+1}/{len(workflow.steps)}: {step.step_id}")
            
            start_time = datetime.now()
            
            try:
                # Generate prompt for this step
                prompt = self._generate_step_prompt(
                    step=step,
                    step_index=i,
                    total_steps=len(workflow.steps),
                    workflow=workflow,
                    context=context,
                )
                
                # Execute the step
                output = await executor(step.agent_name, prompt, context)
                
                # Record result
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                result = ChainResult(
                    step_id=step.step_id,
                    agent_name=step.agent_name,
                    status=ChainStatus.COMPLETED,
                    output=output,
                    execution_time_ms=execution_time,
                )
                
                # Update context with this step's output
                context[step.step_id] = {"output": output}
                
            except Exception as e:
                logger.error(f"Step {step.step_id} failed: {e}")
                
                result = ChainResult(
                    step_id=step.step_id,
                    agent_name=step.agent_name,
                    status=ChainStatus.FAILED,
                    error=str(e),
                )
            
            results[step.step_id] = result
            
            # Stop on failure unless configured otherwise
            if result.status == ChainStatus.FAILED:
                break
        
        return results
    
    def get_execution_plan(self, workflow: WorkflowDefinition) -> List[Dict[str, Any]]:
        """
        Get the execution plan for a workflow.
        
        Returns:
            List of step execution details
        """
        plan = []
        
        for i, step in enumerate(workflow.steps):
            plan.append({
                "order": i + 1,
                "step_id": step.step_id,
                "agent": step.agent_name,
                "type": step.step_type.value,
                "depends_on": list(step.input_mapping.keys()) if step.input_mapping else [],
                "timeout": step.timeout_seconds,
            })
        
        return plan


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def create_chain_orchestrator() -> PromptChainOrchestrator:
    """Factory function to create PromptChainOrchestrator"""
    return PromptChainOrchestrator()


def create_sequential_workflow(
    name: str,
    agents: List[str],
    tasks: List[str],
) -> WorkflowDefinition:
    """
    Quick helper to create a simple sequential workflow.
    
    Example:
        workflow = create_sequential_workflow(
            name="Simple Pipeline",
            agents=["AgentA", "AgentB", "AgentC"],
            tasks=["Task 1", "Task 2", "Task 3"]
        )
    """
    if len(agents) != len(tasks):
        raise ValueError("Number of agents must match number of tasks")
    
    steps = []
    for i, (agent, task) in enumerate(zip(agents, tasks)):
        step = ChainStep(
            step_id=f"step_{i+1}",
            agent_name=agent,
            task_template=task,
        )
        
        # Add input mapping from previous step
        if i > 0:
            step.input_mapping = {"previous": f"step_{i}.output"}
        
        steps.append(step)
    
    orchestrator = PromptChainOrchestrator()
    return orchestrator.create_workflow(name=name, steps=steps)


# Export
__all__ = [
    "PromptChainOrchestrator",
    "ChainStep",
    "ChainStepType",
    "ChainResult",
    "ChainStatus",
    "WorkflowDefinition",
    "create_chain_orchestrator",
    "create_sequential_workflow",
]

