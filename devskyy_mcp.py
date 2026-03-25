"""
DevSkyy MCP Server v2.0 - Advanced Tool Use Integration

Thin entry point that imports the mcp_tools package and runs the server.
All tool handlers, models, and configuration live in the mcp_tools/ package.

Usage:
    python devskyy_mcp.py

    # Or use with Claude Desktop - add to config:
    {
      "mcpServers": {
        "devskyy": {
          "command": "python",
          "args": ["/path/to/devskyy_mcp.py"],
          "env": {
            "DEVSKYY_API_URL": "https://api.devskyy.com",
            "DEVSKYY_API_KEY": "your-api-key-here"
          }
        }
      }
    }
"""

from mcp_tools import mcp  # noqa: F401 - re-export for deploy script compatibility
from mcp_tools.server import API_BASE_URL, API_KEY

if __name__ == "__main__":
    # Validate configuration
    if not API_KEY:
        print("\u26a0\ufe0f  Warning: DEVSKYY_API_KEY not set. Using empty key for testing.")
        print("   Set it with: export DEVSKYY_API_KEY='your-key-here'")

    print(f"""
\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557
\u2551                                                                  \u2551
\u2551   DevSkyy MCP Server v2.0.0 - Advanced Tool Use                 \u2551
\u2551   Industry-First Multi-Agent AI Platform Integration            \u2551
\u2551                                                                  \u2551
\u2551   54 AI Agents \u2022 Enterprise Security \u2022 Multi-Model AI           \u2551
\u2551                                                                  \u2551
\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d

\u2705 Configuration:
   API URL: {API_BASE_URL}
   API Key: {"Set ✓" if API_KEY else "Not Set ⚠️"}

\ud83d\udd27 Tools Available:
   \u2022 devskyy_scan_code - Code analysis and quality checking
   \u2022 devskyy_fix_code - Automated code fixing
   \u2022 devskyy_self_healing - System health monitoring and auto-repair
   \u2022 devskyy_generate_wordpress_theme - WordPress theme generation
   \u2022 devskyy_ml_prediction - Machine learning predictions
   \u2022 devskyy_manage_products - E-commerce product management
   \u2022 devskyy_dynamic_pricing - ML-powered price optimization
   \u2022 devskyy_generate_3d_from_description - 3D generation (text-to-3D)
   \u2022 devskyy_generate_3d_from_image - 3D generation (image-to-3D)
   \u2022 devskyy_virtual_tryon - Virtual try-on for fashion products
   \u2022 devskyy_batch_virtual_tryon - Batch virtual try-on processing
   \u2022 devskyy_generate_ai_model - AI fashion model generation
   \u2022 devskyy_virtual_tryon_status - Try-on pipeline status
   \u2022 devskyy_marketing_campaign - Multi-channel marketing automation
   \u2022 devskyy_multi_agent_workflow - Complex workflow orchestration
   \u2022 devskyy_system_monitoring - Real-time platform monitoring
   \u2022 devskyy_train_lora_from_products - Train LoRA from WooCommerce products
   \u2022 devskyy_lora_dataset_preview - Preview LoRA training dataset
   \u2022 devskyy_lora_version_info - Get LoRA version information
   \u2022 devskyy_lora_product_history - Get product LoRA training history
   \u2022 devskyy_list_agents - View all 54 agents

\ud83d\udcda Documentation: https://docs.devskyy.com/mcp
\ud83d\udd17 API Reference: {API_BASE_URL}/docs

Starting MCP server on stdio...
""")

    # Run the server
    mcp.run()
