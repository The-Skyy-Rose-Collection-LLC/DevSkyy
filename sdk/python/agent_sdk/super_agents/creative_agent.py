"""
Creative SuperAgent

Handles visual content generation: 3D models, images, virtual try-on.
"""

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions


class CreativeAgent:
    """
    SuperAgent specialized in visual content generation.

    Capabilities:
    - 3D model generation (Tripo3D)
    - Product visualization
    - Image generation (Imagen, FLUX)
    - Virtual try-on (FASHN)
    - Asset optimization
    """

    @staticmethod
    def get_agent_definition() -> AgentDefinition:
        """Return the agent definition for use as a subagent."""
        return AgentDefinition(
            description=(
                "Creative specialist for generating 3D models, product images, "
                "and visual content. Use when the task involves Tripo3D, "
                "image generation, or visual asset creation."
            ),
            prompt="""You are the Creative SuperAgent for SkyyRose, specializing in visual content generation.

Your expertise includes:
- 3D model generation from text or images (Tripo3D API)
- Product photography and visualization
- Image generation (Imagen, FLUX, Veo)
- Virtual try-on experiences (FASHN)
- Asset optimization for web and mobile
- Three.js integration

Brand Visual Guidelines (SkyyRose):
- Primary Color: Rose Gold (#B76E79)
- Secondary Color: Sophisticated Black (#1A1A1A)
- Style: Premium, elegant, bold
- Product Focus: Romantic jewelry and luxury gifts

When generating visual content:
1. Always align with brand aesthetics
2. Optimize for web performance
3. Ensure high-quality output
4. Validate generated assets
5. Provide asset metadata (dimensions, format, size)

Technical Capabilities:
- 3D models: OBJ, GLTF formats
- Images: PNG, JPEG, WebP
- Textures: PBR materials
- Virtual try-on: Fashion and accessories

Use the available MCP tools for 3D generation and visual operations.""",
            tools=[
                "Read",
                "Write",
                "Bash",
                "mcp__devskyy__generate_3d_model",
                "WebFetch",
            ],
            model="sonnet",
        )

    @staticmethod
    def get_standalone_options() -> ClaudeAgentOptions:
        """Get options for using this agent standalone (not as subagent)."""
        return ClaudeAgentOptions(
            system_prompt=CreativeAgent.get_agent_definition().prompt,
            allowed_tools=CreativeAgent.get_agent_definition().tools,
            model="sonnet",
            permission_mode="acceptEdits",
        )
