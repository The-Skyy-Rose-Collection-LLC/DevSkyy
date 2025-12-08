"""
Prompt Technique Engine
Implements all 10 advanced prompting techniques used by OpenAI, Anthropic, and Google

Based on: Louis Gleeson's "10 Secret Prompting Techniques" (Dec 2025)
- @godofprompt original: x.com/godofprompt/status/1996966423181365497
- Anthropic COSTARD Framework: docs.anthropic.com
- OpenAI Six-Strategy Framework: platform.openai.com

References:
- Kojima et al. (2022) "Large Language Models are Zero-Shot Reasoners" - NeurIPS 2022
- Wei et al. (2022) "Chain-of-Thought Prompting Elicits Reasoning"
- Yao et al. (2023) "Tree of Thoughts: Deliberate Problem Solving"
- Bai et al. (2022) "Constitutional AI: Harmlessness from AI Feedback"
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class PromptTechnique(Enum):
    """Available prompting techniques"""
    
    ROLE_BASED_CONSTRAINT = "role_based_constraint"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    FEW_SHOT = "few_shot"
    SELF_CONSISTENCY = "self_consistency"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    REACT = "react"
    RAG = "rag"
    PROMPT_CHAINING = "prompt_chaining"
    GENERATED_KNOWLEDGE = "generated_knowledge"
    NEGATIVE_PROMPTING = "negative_prompting"
    CONSTITUTIONAL_AI = "constitutional_ai"


class TaskComplexity(Enum):
    """Task complexity levels for technique selection"""
    
    SIMPLE = "simple"           # Single-step, direct answer
    MODERATE = "moderate"       # Multi-step reasoning
    COMPLEX = "complex"         # Multiple approaches needed
    CRITICAL = "critical"       # High-stakes, requires validation


@dataclass
class RoleDefinition:
    """Defines an expert role for Role-Based Constraint Prompting"""
    
    title: str
    years_experience: int
    domain: str
    expertise_areas: List[str]
    persona_traits: Optional[List[str]] = None
    nickname: Optional[str] = None  # e.g., "The Code Whisperer"
    
    def to_prompt(self) -> str:
        """Convert role definition to prompt text"""
        prompt = f"You are a {self.title} with {self.years_experience}+ years experience in {self.domain}."
        
        if self.nickname:
            prompt += f' Known as "{self.nickname}" for your exceptional abilities.'
        
        if self.expertise_areas:
            prompt += f"\n\nYour expertise includes: {', '.join(self.expertise_areas)}."
        
        if self.persona_traits:
            prompt += f"\n\nYour approach: {', '.join(self.persona_traits)}."
        
        return prompt


@dataclass
class Constraint:
    """Defines a constraint for the task"""
    
    type: str  # "must", "must_not", "prefer", "avoid"
    description: str
    priority: int = 1  # 1=highest
    
    def to_prompt(self) -> str:
        """Convert constraint to prompt text"""
        type_mapping = {
            "must": "MUST",
            "must_not": "MUST NOT",
            "prefer": "SHOULD",
            "avoid": "SHOULD AVOID"
        }
        return f"- {type_mapping.get(self.type, self.type.upper())}: {self.description}"


@dataclass
class OutputFormat:
    """Defines expected output format"""
    
    format_type: str  # "json", "markdown", "code", "structured", "prose"
    schema: Optional[Dict[str, Any]] = None
    example: Optional[str] = None
    max_length: Optional[int] = None
    required_sections: Optional[List[str]] = None
    
    def to_prompt(self) -> str:
        """Convert output format to prompt text"""
        prompt = f"\n# OUTPUT FORMAT\nFormat: {self.format_type.upper()}"
        
        if self.required_sections:
            prompt += f"\nRequired sections: {', '.join(self.required_sections)}"
        
        if self.max_length:
            prompt += f"\nMaximum length: {self.max_length} tokens"
        
        if self.example:
            prompt += f"\n\nExample output:\n```\n{self.example}\n```"
        
        if self.schema:
            import json
            prompt += f"\n\nJSON Schema:\n```json\n{json.dumps(self.schema, indent=2)}\n```"
        
        return prompt


@dataclass
class FewShotExample:
    """Example for few-shot prompting"""
    
    input_text: str
    output_text: str
    reasoning: Optional[str] = None  # For CoT few-shot
    
    def to_prompt(self, include_reasoning: bool = False) -> str:
        """Convert to prompt format"""
        prompt = f"Input: {self.input_text}\n"
        
        if include_reasoning and self.reasoning:
            prompt += f"Reasoning: {self.reasoning}\n"
        
        prompt += f"Output: {self.output_text}"
        return prompt


@dataclass
class ThoughtBranch:
    """A branch in the Tree of Thoughts"""
    
    approach_name: str
    description: str
    steps: List[str]
    evaluation_criteria: List[str]
    
    def to_prompt(self) -> str:
        """Convert to prompt format"""
        prompt = f"\n### Approach: {self.approach_name}\n"
        prompt += f"Description: {self.description}\n"
        prompt += "Steps:\n"
        for i, step in enumerate(self.steps, 1):
            prompt += f"  {i}. {step}\n"
        prompt += "Evaluation criteria:\n"
        for criterion in self.evaluation_criteria:
            prompt += f"  - {criterion}\n"
        return prompt


@dataclass
class ReActStep:
    """A step in the ReAct framework (Reasoning + Acting)"""
    
    thought: str
    action: str
    action_input: Dict[str, Any]
    observation: Optional[str] = None
    
    def to_prompt(self) -> str:
        """Convert to prompt format"""
        prompt = f"Thought: {self.thought}\n"
        prompt += f"Action: {self.action}\n"
        prompt += f"Action Input: {self.action_input}\n"
        if self.observation:
            prompt += f"Observation: {self.observation}\n"
        return prompt


class PromptTechniqueEngine:
    """
    Main engine for applying prompting techniques.
    
    Usage:
        engine = PromptTechniqueEngine()
        
        # Build a prompt with multiple techniques
        prompt = engine.build_prompt(
            task="Generate product descriptions",
            techniques=[
                PromptTechnique.ROLE_BASED_CONSTRAINT,
                PromptTechnique.CHAIN_OF_THOUGHT,
                PromptTechnique.NEGATIVE_PROMPTING
            ],
            role=RoleDefinition(
                title="Senior E-Commerce Content Strategist",
                years_experience=12,
                domain="luxury fashion marketing",
                expertise_areas=["SEO copywriting", "brand voice", "conversion optimization"]
            ),
            constraints=[
                Constraint("must", "Include 3 emotional triggers", 1),
                Constraint("must_not", "Use placeholder text or TODO comments", 1)
            ],
            output_format=OutputFormat(format_type="json")
        )
    """
    
    def __init__(self):
        self.technique_builders: Dict[PromptTechnique, Callable] = {
            PromptTechnique.ROLE_BASED_CONSTRAINT: self._build_role_based,
            PromptTechnique.CHAIN_OF_THOUGHT: self._build_chain_of_thought,
            PromptTechnique.FEW_SHOT: self._build_few_shot,
            PromptTechnique.SELF_CONSISTENCY: self._build_self_consistency,
            PromptTechnique.TREE_OF_THOUGHTS: self._build_tree_of_thoughts,
            PromptTechnique.REACT: self._build_react,
            PromptTechnique.RAG: self._build_rag,
            PromptTechnique.PROMPT_CHAINING: self._build_prompt_chaining,
            PromptTechnique.GENERATED_KNOWLEDGE: self._build_generated_knowledge,
            PromptTechnique.NEGATIVE_PROMPTING: self._build_negative_prompting,
            PromptTechnique.CONSTITUTIONAL_AI: self._build_constitutional,
        }
        
        logger.info("🧠 PromptTechniqueEngine initialized with 11 techniques")
    
    def build_prompt(
        self,
        task: str,
        techniques: List[PromptTechnique],
        role: Optional[RoleDefinition] = None,
        constraints: Optional[List[Constraint]] = None,
        output_format: Optional[OutputFormat] = None,
        few_shot_examples: Optional[List[FewShotExample]] = None,
        thought_branches: Optional[List[ThoughtBranch]] = None,
        rag_context: Optional[str] = None,
        negative_examples: Optional[List[str]] = None,
        constitutional_principles: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Build a complete prompt using specified techniques.
        
        Args:
            task: The main task description
            techniques: List of techniques to apply
            role: Role definition for role-based prompting
            constraints: List of constraints
            output_format: Expected output format
            few_shot_examples: Examples for few-shot learning
            thought_branches: Branches for Tree of Thoughts
            rag_context: Retrieved context for RAG
            negative_examples: Examples of what NOT to do
            constitutional_principles: AI safety principles
            
        Returns:
            Complete prompt string
        """
        prompt_sections = []
        
        # Apply each technique in order
        for technique in techniques:
            builder = self.technique_builders.get(technique)
            if builder:
                section = builder(
                    task=task,
                    role=role,
                    constraints=constraints,
                    output_format=output_format,
                    few_shot_examples=few_shot_examples,
                    thought_branches=thought_branches,
                    rag_context=rag_context,
                    negative_examples=negative_examples,
                    constitutional_principles=constitutional_principles,
                    **kwargs
                )
                if section:
                    prompt_sections.append(section)
        
        # Combine all sections
        final_prompt = "\n\n".join(prompt_sections)
        
        # Add task if not already included
        if task not in final_prompt:
            final_prompt = f"# TASK\n{task}\n\n{final_prompt}"
        
        return final_prompt
    
    def auto_select_techniques(
        self,
        task: str,
        complexity: TaskComplexity,
        has_examples: bool = False,
        requires_tools: bool = False,
        requires_validation: bool = False
    ) -> List[PromptTechnique]:
        """
        Automatically select optimal techniques based on task characteristics.
        
        Args:
            task: Task description
            complexity: Task complexity level
            has_examples: Whether examples are available
            requires_tools: Whether external tools/APIs are needed
            requires_validation: Whether output needs validation
            
        Returns:
            Ordered list of recommended techniques
        """
        techniques = [PromptTechnique.ROLE_BASED_CONSTRAINT]  # Always use
        
        # Add based on complexity
        if complexity in [TaskComplexity.MODERATE, TaskComplexity.COMPLEX, TaskComplexity.CRITICAL]:
            techniques.append(PromptTechnique.CHAIN_OF_THOUGHT)
        
        if complexity in [TaskComplexity.COMPLEX, TaskComplexity.CRITICAL]:
            techniques.append(PromptTechnique.TREE_OF_THOUGHTS)
        
        # Add based on characteristics
        if has_examples:
            techniques.append(PromptTechnique.FEW_SHOT)
        
        if requires_tools:
            techniques.append(PromptTechnique.REACT)
        
        if requires_validation:
            techniques.append(PromptTechnique.SELF_CONSISTENCY)
            techniques.append(PromptTechnique.CONSTITUTIONAL_AI)
        
        # Always add negative prompting for quality
        techniques.append(PromptTechnique.NEGATIVE_PROMPTING)
        
        return techniques
    
    # =========================================================================
    # TECHNIQUE 1: ROLE-BASED CONSTRAINT PROMPTING
    # =========================================================================
    
    def _build_role_based(
        self,
        task: str,
        role: Optional[RoleDefinition] = None,
        constraints: Optional[List[Constraint]] = None,
        output_format: Optional[OutputFormat] = None,
        **kwargs
    ) -> str:
        """
        Build Role-Based Constraint Prompt.
        
        Structure:
        - Expert role with quantified experience
        - Domain expertise areas
        - Specific constraints (MUST/MUST NOT)
        - Exact output format
        
        Reference: @aigleeson thread, Gleeson framework
        """
        sections = []
        
        # Role definition
        if role:
            sections.append(f"# ROLE & AUTHORITY\n{role.to_prompt()}")
        else:
            # Default role
            sections.append(
                "# ROLE & AUTHORITY\n"
                "You are a SENIOR AI SPECIALIST with 15+ years experience in your domain.\n"
                "You have FULL AUTHORITY to make decisions and deliver production-ready outputs."
            )
        
        # Task
        sections.append(f"# TASK\n{task}")
        
        # Constraints
        if constraints:
            sections.append("# CONSTRAINTS")
            sorted_constraints = sorted(constraints, key=lambda c: c.priority)
            for constraint in sorted_constraints:
                sections.append(constraint.to_prompt())
        
        # Output format
        if output_format:
            sections.append(output_format.to_prompt())
        
        return "\n\n".join(sections)
    
    # =========================================================================
    # TECHNIQUE 2: CHAIN-OF-THOUGHT (CoT)
    # =========================================================================
    
    def _build_chain_of_thought(
        self,
        task: str,
        **kwargs
    ) -> str:
        """
        Build Chain-of-Thought prompt.
        
        Forces explicit step-by-step reasoning before conclusion.
        
        Reference: Wei et al. (2022), Kojima et al. (2022)
        Performance: 17.7% → 78.7% on MultiArith with Zero-shot-CoT
        """
        return """# REASONING PROTOCOL
Before providing your final answer, you MUST:
1. Break down the problem into distinct components
2. Analyze each component step-by-step
3. Show your reasoning explicitly
4. Consider potential edge cases
5. Validate your logic before concluding

Use this structure:
<thinking>
Step 1: [First analysis step]
Step 2: [Second analysis step]
Step 3: [Continue as needed]
Validation: [Verify logic is sound]
</thinking>

<answer>
[Your final answer based on the reasoning above]
</answer>

Think step by step. Let's work through this carefully."""
    
    # =========================================================================
    # TECHNIQUE 3: FEW-SHOT PROMPTING
    # =========================================================================
    
    def _build_few_shot(
        self,
        task: str,
        few_shot_examples: Optional[List[FewShotExample]] = None,
        **kwargs
    ) -> str:
        """
        Build Few-Shot prompt with examples.
        
        Optimal: 3-5 diverse, relevant examples
        Performance: 32 examples sufficient to beat fine-tuned BERT++ on SuperGLUE
        
        Reference: Brown et al. (2020), Gao et al. (2021) "LM-BFF"
        """
        if not few_shot_examples:
            return ""
        
        sections = ["# EXAMPLES\nLearn from these examples to understand the expected format and quality:\n"]
        
        for i, example in enumerate(few_shot_examples, 1):
            sections.append(f"## Example {i}")
            sections.append(example.to_prompt(include_reasoning=True))
            sections.append("")  # Blank line
        
        sections.append("# NOW YOUR TURN")
        sections.append("Apply the same pattern and quality to the following task.")
        
        return "\n".join(sections)
    
    # =========================================================================
    # TECHNIQUE 4: SELF-CONSISTENCY
    # =========================================================================
    
    def _build_self_consistency(
        self,
        task: str,
        num_paths: int = 3,
        **kwargs
    ) -> str:
        """
        Build Self-Consistency prompt.
        
        Generates multiple reasoning paths and selects most consistent answer.
        Best for: High-stakes decisions needing validation
        
        Reference: Wang et al. (2022) "Self-Consistency Improves CoT Reasoning"
        """
        return f"""# SELF-CONSISTENCY VALIDATION
Generate {num_paths} independent reasoning paths, then identify the most consistent answer.

## Reasoning Path 1
<path_1>
[First complete reasoning approach]
Conclusion 1: [Answer from path 1]
</path_1>

## Reasoning Path 2
<path_2>
[Second complete reasoning approach - use different method if possible]
Conclusion 2: [Answer from path 2]
</path_2>

## Reasoning Path 3
<path_3>
[Third complete reasoning approach - validate against first two]
Conclusion 3: [Answer from path 3]
</path_3>

## Consistency Analysis
<consistency_check>
- Agreement between paths: [Analyze where paths agree/disagree]
- Most consistent answer: [Identify the answer supported by majority]
- Confidence level: [High/Medium/Low based on agreement]
</consistency_check>

## FINAL ANSWER
[The answer supported by the most reasoning paths, with confidence level]"""
    
    # =========================================================================
    # TECHNIQUE 5: TREE OF THOUGHTS (ToT)
    # =========================================================================
    
    def _build_tree_of_thoughts(
        self,
        task: str,
        thought_branches: Optional[List[ThoughtBranch]] = None,
        num_branches: int = 3,
        **kwargs
    ) -> str:
        """
        Build Tree of Thoughts prompt.
        
        Explores multiple solution paths, evaluates each, selects best.
        Best for: Problems with multiple valid approaches
        
        Reference: Yao et al. (2023) "Tree of Thoughts: Deliberate Problem Solving"
        """
        sections = [
            "# TREE OF THOUGHTS EXPLORATION",
            f"Explore {num_branches} distinct approaches, evaluate each, then select the optimal solution.\n"
        ]
        
        if thought_branches:
            for branch in thought_branches:
                sections.append(branch.to_prompt())
        else:
            # Default branch structure
            sections.append("""
## Branch Generation
For each approach, document:
1. **Approach Name**: Descriptive title
2. **Strategy**: How this approach works
3. **Implementation Steps**: Concrete steps to execute
4. **Pros**: Advantages of this approach
5. **Cons**: Disadvantages or risks
6. **Estimated Success Rate**: X/10

## Approach A
<branch_a>
[Document approach A using the structure above]
</branch_a>

## Approach B
<branch_b>
[Document approach B - should be distinctly different from A]
</branch_b>

## Approach C
<branch_c>
[Document approach C - should offer a third perspective]
</branch_c>

## Evaluation Matrix
| Approach | Effectiveness | Feasibility | Risk | Score |
|----------|--------------|-------------|------|-------|
| A        | ?/10         | ?/10        | ?/10 | ?/30  |
| B        | ?/10         | ?/10        | ?/10 | ?/30  |
| C        | ?/10         | ?/10        | ?/10 | ?/30  |

## Selected Approach
[Choose the approach with highest score and explain why]

## Implementation
[Provide the full implementation using the selected approach]
""")
        
        return "\n".join(sections)
    
    # =========================================================================
    # TECHNIQUE 6: ReAct (REASONING + ACTING)
    # =========================================================================
    
    def _build_react(
        self,
        task: str,
        available_tools: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Build ReAct prompt for tool-using agents.
        
        Interleaves reasoning with actions/tool calls.
        Best for: Agent tasks, tool use, external API calls
        
        Reference: Yao et al. (2022) "ReAct: Synergizing Reasoning and Acting"
        """
        tools_list = available_tools or ["search", "calculate", "lookup", "execute"]
        
        return f"""# ReAct FRAMEWORK
You will solve this task by interleaving Thought, Action, and Observation steps.

## Available Tools
{chr(10).join(f'- {tool}' for tool in tools_list)}

## ReAct Loop Structure
For each step:

**Thought**: Analyze the current state and decide what to do next.
**Action**: Choose a tool and specify the input.
**Observation**: [This will be filled with the tool's output]

Continue the loop until you have enough information to provide a final answer.

## Example Format
```
Thought 1: I need to understand [X] before I can solve this.
Action 1: search[relevant query]
Observation 1: [Results from search]

Thought 2: Based on the search results, I now know [Y]. Next I need to [Z].
Action 2: calculate[expression]
Observation 2: [Calculation result]

Thought 3: Now I have all the information needed.
Final Answer: [Complete answer based on reasoning and observations]
```

## BEGIN ReAct LOOP
Start with your first Thought about this task."""
    
    # =========================================================================
    # TECHNIQUE 7: RAG (RETRIEVAL-AUGMENTED GENERATION)
    # =========================================================================
    
    def _build_rag(
        self,
        task: str,
        rag_context: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Build RAG prompt with retrieved context.
        
        Grounds generation in retrieved factual information.
        Best for: Tasks requiring current data or domain knowledge
        
        Reference: Lewis et al. (2020) "RAG: Retrieval-Augmented Generation"
        """
        if not rag_context:
            return ""
        
        return f"""# RETRIEVED CONTEXT
The following information has been retrieved from authoritative sources.
Use this context to inform your response. Cite specific facts when used.

<retrieved_context>
{rag_context}
</retrieved_context>

## CONTEXT USAGE RULES
1. Prioritize information from the retrieved context over general knowledge
2. If the context contradicts your training data, trust the context
3. Cite specific passages when making claims: "According to the context..."
4. If information is not in the context, explicitly state: "This is not covered in the provided context"
5. Do not hallucinate facts not present in the context

## CONFIDENCE INDICATORS
- HIGH: Directly stated in context
- MEDIUM: Inferred from context
- LOW: From general knowledge (flag as such)"""
    
    # =========================================================================
    # TECHNIQUE 8: PROMPT CHAINING
    # =========================================================================
    
    def _build_prompt_chaining(
        self,
        task: str,
        chain_steps: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Build Prompt Chaining structure.
        
        Breaks complex tasks into sequential prompts.
        Best for: Tasks too large for single prompt
        
        Reference: Wu et al. (2022) "AI Chains: Transparent and Controllable"
        """
        if not chain_steps:
            # Default chain for development tasks
            chain_steps = [
                "ANALYZE: Understand requirements and constraints",
                "DESIGN: Create architecture and approach",
                "IMPLEMENT: Build the solution",
                "VALIDATE: Test and verify",
                "DOCUMENT: Create documentation"
            ]
        
        sections = [
            "# EXECUTION CHAIN",
            "Complete each phase in sequence. Each phase's output feeds into the next.\n"
        ]
        
        for i, step in enumerate(chain_steps, 1):
            step_parts = step.split(":", 1)
            phase_name = step_parts[0].strip()
            phase_desc = step_parts[1].strip() if len(step_parts) > 1 else ""
            
            sections.append(f"""## Phase {i}: {phase_name}
{phase_desc}

<phase_{i}_output>
[Complete this phase before proceeding]
</phase_{i}_output>
""")
        
        sections.append("""## CHAIN RULES
- Complete each phase fully before moving to the next
- Reference previous phase outputs explicitly
- If a phase fails validation, return to previous phase
- Final output must synthesize all phase results""")
        
        return "\n".join(sections)
    
    # =========================================================================
    # TECHNIQUE 9: GENERATED KNOWLEDGE
    # =========================================================================
    
    def _build_generated_knowledge(
        self,
        task: str,
        knowledge_domains: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Build Generated Knowledge prompt.
        
        Primes the model by generating relevant knowledge before answering.
        Best for: Complex tasks requiring domain expertise
        
        Reference: Liu et al. (2022) "Generated Knowledge Prompting"
        """
        domains = knowledge_domains or ["relevant concepts", "best practices", "common pitfalls"]
        
        return f"""# KNOWLEDGE GENERATION PHASE
Before answering, generate relevant knowledge to prime your response.

## Generate Knowledge For:
{chr(10).join(f'- {domain}' for domain in domains)}

<generated_knowledge>
## Relevant Concepts
[Generate 3-5 key concepts relevant to this task]

## Best Practices
[Generate 3-5 industry best practices that apply]

## Common Pitfalls
[Generate 3-5 mistakes to avoid]

## Expert Insights
[Generate 2-3 insights an expert would know]
</generated_knowledge>

## APPLY KNOWLEDGE
Now use the generated knowledge above to inform your response.
Ensure your answer reflects this expertise."""
    
    # =========================================================================
    # TECHNIQUE 10: NEGATIVE PROMPTING
    # =========================================================================
    
    def _build_negative_prompting(
        self,
        task: str,
        negative_examples: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Build Negative Prompting section.
        
        Explicitly states what NOT to do.
        Best for: Preventing common failures, removing defaults
        """
        default_negatives = [
            "Use placeholder text, 'TODO', or 'FIXME' comments",
            "Include incomplete or stub implementations",
            "Hardcode credentials, API keys, or secrets",
            "Skip error handling or input validation",
            "Use deprecated methods or libraries",
            "Ignore edge cases or error scenarios",
            "Provide vague or generic responses",
            "Make assumptions without validation",
        ]
        
        negatives = negative_examples or default_negatives
        
        sections = [
            "# WHAT NOT TO DO",
            "The following are STRICTLY FORBIDDEN. Violating these will result in rejection.\n",
            "❌ DO NOT:"
        ]
        
        for negative in negatives:
            sections.append(f"  - {negative}")
        
        return "\n".join(sections)
    
    # =========================================================================
    # BONUS: CONSTITUTIONAL AI
    # =========================================================================
    
    def _build_constitutional(
        self,
        task: str,
        constitutional_principles: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Build Constitutional AI principles.
        
        Embeds ethical guidelines and safety constraints.
        
        Reference: Bai et al. (2022) "Constitutional AI: Harmlessness from AI Feedback"
        Performance: Reduces Attack Success Rate by 40.8% (Llama 3-8B)
        """
        default_principles = [
            "Ensure outputs are helpful, harmless, and honest",
            "Avoid generating code that could be used maliciously",
            "Protect user data and privacy",
            "Be transparent about limitations and uncertainties",
            "Follow security best practices",
        ]
        
        principles = constitutional_principles or default_principles
        
        return f"""# CONSTITUTIONAL PRINCIPLES
These principles MUST guide all outputs. Self-critique against these before responding.

## Core Principles
{chr(10).join(f'{i}. {p}' for i, p in enumerate(principles, 1))}

## Self-Critique Protocol
Before finalizing your response, ask:
1. Does this response help the user achieve their legitimate goal?
2. Could this response cause harm if misused?
3. Is this response honest about uncertainties and limitations?
4. Does this follow security and ethical best practices?

If any answer is concerning, revise the response accordingly."""
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_technique_description(self, technique: PromptTechnique) -> str:
        """Get description of a specific technique."""
        descriptions = {
            PromptTechnique.ROLE_BASED_CONSTRAINT: 
                "Assigns expert role with quantified experience and specific constraints",
            PromptTechnique.CHAIN_OF_THOUGHT:
                "Forces step-by-step reasoning before conclusion (17.7% → 78.7% on math)",
            PromptTechnique.FEW_SHOT:
                "Provides examples to learn from (3-5 examples optimal)",
            PromptTechnique.SELF_CONSISTENCY:
                "Generates multiple paths, selects most consistent answer",
            PromptTechnique.TREE_OF_THOUGHTS:
                "Explores multiple approaches, evaluates each, selects best",
            PromptTechnique.REACT:
                "Interleaves reasoning with tool/action calls",
            PromptTechnique.RAG:
                "Grounds generation in retrieved factual context",
            PromptTechnique.PROMPT_CHAINING:
                "Breaks task into sequential phases",
            PromptTechnique.GENERATED_KNOWLEDGE:
                "Primes model with self-generated domain knowledge",
            PromptTechnique.NEGATIVE_PROMPTING:
                "Explicitly states what NOT to do",
            PromptTechnique.CONSTITUTIONAL_AI:
                "Embeds ethical principles and self-critique",
        }
        return descriptions.get(technique, "Unknown technique")
    
    def get_all_techniques(self) -> Dict[str, str]:
        """Get all available techniques with descriptions."""
        return {t.value: self.get_technique_description(t) for t in PromptTechnique}


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def create_agent_prompt(
    agent_name: str,
    role: RoleDefinition,
    task: str,
    constraints: List[Constraint],
    output_format: OutputFormat,
    complexity: TaskComplexity = TaskComplexity.MODERATE
) -> str:
    """
    Convenience function to create a complete agent prompt.
    
    Example:
        prompt = create_agent_prompt(
            agent_name="ProductDescriptionAgent",
            role=RoleDefinition(
                title="Senior E-Commerce Copywriter",
                years_experience=10,
                domain="luxury fashion",
                expertise_areas=["SEO", "brand voice", "conversion optimization"]
            ),
            task="Generate product descriptions for luxury handbags",
            constraints=[
                Constraint("must", "Include 3 emotional triggers"),
                Constraint("must_not", "Use generic phrases")
            ],
            output_format=OutputFormat(format_type="json"),
            complexity=TaskComplexity.MODERATE
        )
    """
    engine = PromptTechniqueEngine()
    
    # Auto-select techniques based on complexity
    techniques = engine.auto_select_techniques(
        task=task,
        complexity=complexity
    )
    
    return engine.build_prompt(
        task=task,
        techniques=techniques,
        role=role,
        constraints=constraints,
        output_format=output_format
    )


# Export for use in DevSkyy
__all__ = [
    "PromptTechniqueEngine",
    "PromptTechnique",
    "TaskComplexity",
    "RoleDefinition",
    "Constraint",
    "OutputFormat",
    "FewShotExample",
    "ThoughtBranch",
    "ReActStep",
    "create_agent_prompt",
]

