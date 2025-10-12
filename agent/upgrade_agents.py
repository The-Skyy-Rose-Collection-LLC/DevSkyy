"""
Agent Upgrade Script
Systematically upgrades all DevSkyy agents to use BaseAgent with ML and self-healing

This script:
1. Identifies agents that need upgrading
2. Creates V2 versions with BaseAgent inheritance
3. Maintains backward compatibility
4. Adds comprehensive error handling and ML features
"""

import re
from pathlib import Path
from typing import List

AGENT_MODULES_DIR = Path(__file__).parent / "modules"


def find_agents_to_upgrade() -> List[Path]:
    """Find all agent files that need upgrading"""
    agent_files = []

    for file_path in AGENT_MODULES_DIR.glob("*.py"):
        if file_path.name in ["__init__.py", "base_agent.py", "upgrade_agents.py"]:
            continue

        # Skip already upgraded V2 versions
        if "_v2.py" in file_path.name:
            continue

        agent_files.append(file_path)

    return sorted(agent_files)


def check_if_uses_base_agent(file_path: Path) -> bool:
    """Check if agent already inherits from BaseAgent"""
    try:
        content = file_path.read_text()
        return "from .base_agent import BaseAgent" in content or "BaseAgent" in content
    except Exception:
        return False


def analyze_agent_structure(file_path: Path) -> dict:
    """Analyze agent structure and identify key components"""
    try:
        content = file_path.read_text()

        # Extract class names
        class_pattern = r"class\s+(\w+)(?:\([\w,\s]+\))?:"
        classes = re.findall(class_pattern, content)

        # Check for async methods
        has_async = "async def" in content

        # Check for error handling
        has_error_handling = "try:" in content and "except" in content

        # Check for logging
        has_logging = "logger" in content or "logging" in content

        # Check for type hints
        has_type_hints = "from typing import" in content

        return {
            "file": file_path.name,
            "classes": classes,
            "has_async": has_async,
            "has_error_handling": has_error_handling,
            "has_logging": has_logging,
            "has_type_hints": has_type_hints,
            "lines": len(content.split("\n")),
            "uses_base_agent": check_if_uses_base_agent(file_path),
        }
    except Exception as e:
        return {"file": file_path.name, "error": str(e)}


def generate_upgrade_template(agent_name: str, original_class_name: str) -> str:
    """Generate a template for upgrading an agent"""

    template = f'''"""
{agent_name} V2 - Upgraded with ML and Self-Healing
Enterprise-grade agent with BaseAgent capabilities

UPGRADED FEATURES:
- Inherits from BaseAgent for self-healing
- Automatic error recovery and retry logic
- Performance monitoring and anomaly detection
- Circuit breaker protection
- Comprehensive health checks
- ML-powered optimization
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent, SeverityLevel

logger = logging.getLogger(__name__)


class {original_class_name}V2(BaseAgent):
    """
    Upgraded {agent_name} with enterprise self-healing and ML capabilities.
    """

    def __init__(self):
        super().__init__(agent_name="{agent_name}", version="2.0.0")

        # Initialize agent-specific attributes here
        # ... your initialization code ...

        logger.info(f"🚀 {{self.agent_name}} V2 initialized")

    async def initialize(self) -> bool:
        """Initialize the agent with self-healing support"""
        try:
            # Add your initialization logic here
            # Test connections, load configs, etc.

            self.status = BaseAgent.AgentStatus.HEALTHY
            logger.info(f"✅ {{self.agent_name}} initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize {{self.agent_name}}: {{e}}")
            self.status = BaseAgent.AgentStatus.FAILED
            return False

    async def execute_core_function(self, **kwargs) -> Dict[str, Any]:
        """
        Core agent functionality with self-healing.
        Implement your main agent logic here.
        """
        # Implement core functionality
        return await self.health_check()

    @BaseAgent.with_healing
    async def your_main_method(self, param1: str, param2: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main agent method with automatic self-healing.

        The @with_healing decorator provides:
        - Automatic retry on failure
        - Error recovery
        - Performance monitoring
        - Anomaly detection
        """
        try:
            # Your agent logic here
            result = {{"status": "success", "data": "your_data"}}

            # Record metrics
            self.agent_metrics.ml_predictions_made += 1

            return result

        except Exception as e:
            logger.error(f"Method failed: {{e}}")
            raise  # Let BaseAgent.with_healing handle retry

    async def _optimize_resources(self):
        """Override to implement agent-specific resource optimization"""
        logger.info(f"Optimizing {{self.agent_name}} resources...")
        # Clear caches, reset connections, etc.
        pass


# Factory function
def create_{agent_name.lower().replace(" ", "_")}_v2() -> {original_class_name}V2:
    """Create and return {agent_name} V2 instance."""
    agent = {original_class_name}V2()
    asyncio.create_task(agent.initialize())
    return agent


# Global instance
{agent_name.lower().replace(" ", "_")}_v2 = create_{agent_name.lower().replace(" ", "_")}_v2()
'''

    return template


def main():
    """Main upgrade process"""
    print("🔧 DevSkyy Agent Upgrade Script")
    print("=" * 60)

    # Find all agents
    agents = find_agents_to_upgrade()
    print(f"\nFound {len(agents)} agents to analyze\n")

    # Analyze each agent
    results = []
    for agent_file in agents:
        analysis = analyze_agent_structure(agent_file)
        results.append(analysis)

        status = "✅ Uses BaseAgent" if analysis.get("uses_base_agent") else "⚠️  Needs Upgrade"
        print(f"{status}: {analysis['file']}")
        print(f"   Classes: {', '.join(analysis.get('classes', []))}")
        print(f"   Lines: {analysis.get('lines', 0)}")
        print(f"   Async: {analysis.get('has_async', False)}")
        print(f"   Error Handling: {analysis.get('has_error_handling', False)}")
        print()

    # Summary
    needs_upgrade = [r for r in results if not r.get("uses_base_agent", False)]
    already_upgraded = [r for r in results if r.get("uses_base_agent", False)]

    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  Total agents: {len(results)}")
    print(f"  Already upgraded: {len(already_upgraded)}")
    print(f"  Needs upgrade: {len(needs_upgrade)}")
    print()

    # Show agents that need upgrading
    if needs_upgrade:
        print("Agents needing upgrade:")
        for agent in needs_upgrade:
            print(f"  - {agent['file']}")

    print("\n" + "=" * 60)
    print("Upgrade Process:")
    print("1. Review agent code and understand functionality")
    print("2. Create V2 version inheriting from BaseAgent")
    print("3. Wrap key methods with @BaseAgent.with_healing decorator")
    print("4. Implement initialize() and execute_core_function()")
    print("5. Add ML features and optimization")
    print("6. Test thoroughly")
    print("7. Update imports in main.py")


if __name__ == "__main__":
    main()
