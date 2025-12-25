"""
SkyyRose Collection Content Agent
==================================

SuperAgent specialized for managing collection pages, product content,
and 3D experience integration with WordPress.

Part of the 6 SuperAgent system with integrated design templates
for recovery and consistency.

Usage:
    agent = CollectionContentAgent()
    response = await agent.manage_collection(
        collection_type="black_rose",
        task="Create collection page with products"
    )
"""

from __future__ import annotations

import json
from typing import Any

import structlog

from agents.base_super_agent import EnhancedSuperAgent, SuperAgentType, TaskCategory
from orchestration.prompt_engineering import PromptTechnique
from wordpress.collection_page_manager import CollectionDesignTemplates, CollectionType

logger = structlog.get_logger(__name__)


class CollectionContentAgent(EnhancedSuperAgent):
    """
    SuperAgent for managing SkyyRose collection pages.

    Capabilities:
    - Create/update collection pages with 3D experiences
    - Manage product content and metadata
    - Ensure design consistency across collections
    - Recovery using stored design templates
    - Integration with WordPress API

    Design Templates Built-In:
    - BLACK ROSE: Dark elegance, gothic luxury
    - LOVE HURTS: Emotional expression, castle environment
    - SIGNATURE: Premium essentials, runway showcase
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize Collection Content Agent.

        Args:
            config: Optional configuration overrides
        """
        super().__init__(
            agent_type=SuperAgentType.OPERATIONS,
            config=config or {},
        )

        self.name = "Collection Content Agent"
        self.description = "Manages SkyyRose collection pages and 3D experiences"

        # Load design templates for reference
        self.design_templates = CollectionDesignTemplates.get_all_templates()

        logger.info(
            "collection_content_agent_initialized",
            templates_loaded=len(self.design_templates),
        )

    async def manage_collection(
        self,
        collection_type: str,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Manage collection page content and structure.

        Args:
            collection_type: Type of collection (black_rose, love_hurts, signature)
            task: Task to perform (create, update, validate, etc.)
            context: Additional context for the task

        Returns:
            Result of the management task

        Raises:
            ValueError: If collection type not found
        """
        try:
            # Get collection template for reference
            collection_enum = CollectionType[collection_type.upper()]
            template = CollectionDesignTemplates.get_template(collection_enum)

            logger.info(
                "manage_collection_start",
                collection=collection_type,
                task=task,
                template=template.name,
            )

            # Build agent prompt with design template context
            prompt = self._build_collection_prompt(
                template=template,
                task=task,
                context=context or {},
            )

            # Use appropriate technique based on task
            technique = self._select_technique(task)

            # Execute with LLM
            response = await self.use_technique(
                technique=technique,
                prompt=prompt,
                task_category=TaskCategory.CONTENT_GENERATION,
                collection_type=collection_type,
                template=(
                    template.to_dict()
                    if hasattr(template, "to_dict")
                    else {
                        "name": template.name,
                        "theme": template.theme,
                        "colors": template.colors,
                    }
                ),
            )

            logger.info(
                "manage_collection_success",
                collection=collection_type,
                task=task,
            )

            return {
                "status": "success",
                "collection": collection_type,
                "task": task,
                "result": response,
                "template_reference": template.name,
            }

        except KeyError:
            error_msg = f"Collection type not found: {collection_type}"
            logger.error("manage_collection_invalid_type", error=error_msg)
            raise ValueError(error_msg)

        except Exception as e:
            logger.error(
                "manage_collection_failed",
                collection=collection_type,
                task=task,
                error=str(e),
            )

            # RECOVERY: Return template reference for manual recovery
            return {
                "status": "error",
                "collection": collection_type,
                "task": task,
                "error": str(e),
                "recovery_template": CollectionDesignTemplates.to_agent_reference(
                    CollectionType[collection_type.upper()]
                ),
            }

    def _build_collection_prompt(
        self,
        template: Any,
        task: str,
        context: dict[str, Any],
    ) -> str:
        """Build prompt with design template context for consistency"""
        return f"""
You are the SkyyRose Collection Content Agent managing the {template.name}.

=== COLLECTION TEMPLATE (REFERENCE FOR CONSISTENCY) ===
Name: {template.name}
Theme: {template.theme}
Description: {template.description}

Color Palette:
- Primary: {template.colors.get('primary')}
- Secondary: {template.colors.get('secondary')}
- Accent: {template.colors.get('accent')}

Design Characteristics:
{json.dumps(template.metadata or {}, indent=2)}

HTML Experience File: {template.html_file_path}

=== RECOVERY PROTOCOL ===
If you notice any design inconsistencies or breaks:
1. Reference the color palette above (exact HEX values)
2. Verify theme consistency: "{template.theme}"
3. Check product descriptions match the target audience
4. Restore from original HTML file if needed: {template.html_file_path}

=== YOUR TASK ===
{task}

Additional Context:
{json.dumps(context, indent=2)}

REQUIREMENTS:
- Maintain exact colors from palette above
- Keep content aligned with "{template.theme}" theme
- Use professional copy consistent with luxury brand voice
- Ensure technical accuracy for WordPress integration
- Flag any design inconsistencies immediately

OUTPUT FORMAT:
Return a structured response with:
1. Status (success/error)
2. Content created/updated
3. WordPress integration details if applicable
4. Any design warnings or notes
5. Next steps
"""

    def _select_technique(self, task: str) -> PromptTechnique:
        """Select appropriate prompt technique based on task"""
        task_lower = task.lower()

        # Content creation → Role-based prompting
        if "create" in task_lower or "write" in task_lower:
            return PromptTechnique.ROLE_BASED

        # Validation → Structured output
        if "validate" in task_lower or "check" in task_lower:
            return PromptTechnique.STRUCTURED_OUTPUT

        # Complex structure → Chain of thought
        if "structure" in task_lower or "design" in task_lower:
            return PromptTechnique.CHAIN_OF_THOUGHT

        # Default: Few-shot for consistency
        return PromptTechnique.FEW_SHOT

    async def validate_collection_design(
        self,
        collection_type: str,
        design_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validate collection design for consistency and compliance.

        Args:
            collection_type: Type of collection
            design_data: Design data to validate

        Returns:
            Validation result with issues and recommendations
        """
        template = CollectionDesignTemplates.get_template(CollectionType[collection_type.upper()])

        validation_prompt = f"""
Validate this {template.name} design against the template:

TEMPLATE STANDARDS:
Colors: {json.dumps(template.colors)}
Theme: {template.theme}

DESIGN TO VALIDATE:
{json.dumps(design_data, indent=2)}

Check for:
1. Color consistency (exact HEX values)
2. Theme alignment
3. Brand voice/tone
4. Product descriptions accuracy
5. Technical requirements (size, format, etc.)

Return validation with:
- Is valid: yes/no
- Issues found (if any)
- Recommendations for fixes
- Recovery steps if needed
"""

        result = await self.manage_collection(
            collection_type=collection_type,
            task="Validate design consistency",
            context={"validation_prompt": validation_prompt},
        )

        return result

    async def recover_collection_design(
        self,
        collection_type: str,
        issue_description: str,
    ) -> dict[str, Any]:
        """
        Recover collection design from stored template.

        Used when design breaks or becomes inconsistent.

        Args:
            collection_type: Type of collection
            issue_description: Description of the issue

        Returns:
            Recovery instructions and template reference
        """
        template = CollectionDesignTemplates.get_template(CollectionType[collection_type.upper()])

        recovery_prompt = f"""
COLLECTION DESIGN RECOVERY NEEDED

Collection: {template.name}
Issue: {issue_description}

RESTORE FROM TEMPLATE:
{json.dumps(CollectionDesignTemplates.to_agent_reference(CollectionType[collection_type.upper()]), indent=2)}

RECOVERY STEPS:
1. Restore exact colors: {json.dumps(template.colors)}
2. Reset theme to: {template.theme}
3. Use HTML template: {template.html_file_path}
4. Verify all metadata: {json.dumps(template.metadata or {})}

Provide step-by-step instructions to restore this collection to a consistent state.
Include exact commands and values to use.
"""

        result = await self.manage_collection(
            collection_type=collection_type,
            task="Recover design from template",
            context={"recovery_prompt": recovery_prompt},
        )

        logger.info(
            "collection_design_recovery",
            collection=collection_type,
            status=result.get("status"),
        )

        return result

    def get_design_template(self, collection_type: str) -> dict[str, Any]:
        """
        Get design template for agent reference.

        Can be called anytime agent needs to verify consistency.

        Args:
            collection_type: Type of collection

        Returns:
            Design template as dict
        """
        CollectionDesignTemplates.get_template(CollectionType[collection_type.upper()])

        return CollectionDesignTemplates.to_agent_reference(CollectionType[collection_type.upper()])

    def get_all_templates(self) -> dict[str, Any]:
        """Get all collection design templates"""
        return {
            key.value: CollectionDesignTemplates.to_agent_reference(key) for key in CollectionType
        }


def create_collection_content_agent(
    config: dict[str, Any] | None = None,
) -> CollectionContentAgent:
    """Factory function to create CollectionContentAgent"""
    return CollectionContentAgent(config)


__all__ = [
    "CollectionContentAgent",
    "create_collection_content_agent",
]
