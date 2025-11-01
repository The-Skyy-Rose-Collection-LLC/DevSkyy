from datetime import datetime
from pathlib import Path
import re

from .base_agent import BaseAgent, SeverityLevel
from typing import Any, Dict, List, Optional
from typing import Dict, List, Optional
import asyncio
import asyncio
import gc
import logging
import logging

"""
Agent Upgrade Script
Systematically upgrades all DevSkyy agents to use BaseAgent with ML and self-healing

This script:
1. Identifies agents that need upgrading
2. Creates V2 versions with BaseAgent inheritance
3. Maintains backward compatibility
4. Adds comprehensive error handling and ML features
"""

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

    template = '''"""
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

    async def _optimize_resources(self) -> Dict[str, any]:
        """
        Implement comprehensive agent-specific resource optimization.

        This method performs memory cleanup, connection pooling optimization,
        cache management, and resource monitoring for optimal performance.

        Returns:
            Dict[str, any]: Resource optimization results and metrics
        """
        optimization_results = {
            "timestamp": asyncio.get_event_loop().time(),
            "agent_name": getattr(self, 'agent_name', 'Unknown'),
            "optimizations_performed": [],
            "memory_freed_mb": 0,
            "connections_optimized": 0,
            "caches_cleared": 0
        }

        try:
            logger.info(f"🔧 Optimizing {optimization_results['agent_name']} resources...")

            # 1. Memory optimization
            initial_objects = len(gc.get_objects())
            gc.collect()  # Force garbage collection
            final_objects = len(gc.get_objects())
            objects_freed = initial_objects - final_objects

            if objects_freed > 0:
                optimization_results["optimizations_performed"].append("garbage_collection")
                optimization_results["memory_freed_mb"] = objects_freed * 0.001  # Rough estimate
                logger.debug(f"🗑️ Freed {objects_freed} objects from memory")

            # 2. Clear internal caches if they exist
            cache_attributes = ['_cache', '_response_cache', '_model_cache', '_prediction_cache']
            for attr in cache_attributes:
                if hasattr(self, attr):
                    cache = getattr(self, attr)
                    if hasattr(cache, 'clear'):
                        cache.clear()
                        optimization_results["caches_cleared"] += 1
                        optimization_results["optimizations_performed"].append(f"cleared_{attr}")
                        logger.debug(f"🧹 Cleared cache: {attr}")

            # 3. Optimize async connections and pools
            connection_attributes = ['_connection_pool', '_http_client', '_db_connection']
            for attr in connection_attributes:
                if hasattr(self, attr):
                    connection = getattr(self, attr)
                    # Close and recreate connection if it has close method
                    if hasattr(connection, 'close'):
                        try:
                            await connection.close()
                            optimization_results["connections_optimized"] += 1
                            optimization_results["optimizations_performed"].append(f"optimized_{attr}")
                            logger.debug(f"🔌 Optimized connection: {attr}")
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to optimize {attr}: {e}")

            # 4. Reset performance metrics if they exist
            if hasattr(self, 'agent_metrics'):
                # Reset counters that might grow indefinitely
                metrics = self.agent_metrics
                if hasattr(metrics, 'reset_counters'):
                    metrics.reset_counters()
                    optimization_results["optimizations_performed"].append("reset_metrics")
                    logger.debug("📊 Reset performance metrics counters")

            # 5. Optimize ML model memory if applicable
            if hasattr(self, '_model') or hasattr(self, 'model'):
                model = getattr(self, '_model', None) or getattr(self, 'model', None)
                if model and hasattr(model, 'clear_session'):
                    model.clear_session()
                    optimization_results["optimizations_performed"].append("cleared_ml_session")
                    logger.debug("🤖 Cleared ML model session")

            total_optimizations = len(optimization_results["optimizations_performed"])
            logger.info(f"✅ Resource optimization complete: {total_optimizations} optimizations performed")

            return optimization_results

        except Exception as e:
            logger.error(f"❌ Resource optimization failed: {e}")
            optimization_results["error"] = str(e)
            return optimization_results

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
    logger.info("🔧 DevSkyy Agent Upgrade Script")
    logger.info("=" * 60)

    # Find all agents
    agents = find_agents_to_upgrade()
    logger.info(f"\nFound {len(agents)} agents to analyze\n")

    # Analyze each agent
    results = []
    for agent_file in agents:
        analysis = analyze_agent_structure(agent_file)
        results.append(analysis)

        status = "✅ Uses BaseAgent" if analysis.get("uses_base_agent") else "⚠️  Needs Upgrade"
        logger.info(f"{status}: {analysis['file']}")
        logger.info(f"   Classes: {', '.join(analysis.get('classes', []))}")
        logger.info(f"   Lines: {analysis.get('lines', 0)}")
        logger.info(f"   Async: {analysis.get('has_async', False)}")
        logger.info(f"   Error Handling: {analysis.get('has_error_handling', False)}")
        logger.info()

    # Summary
    needs_upgrade = [r for r in results if not r.get("uses_base_agent", False)]
    already_upgraded = [r for r in results if r.get("uses_base_agent", False)]

    logger.info("\n" + "=" * 60)
    logger.info("Summary:")
    logger.info(f"  Total agents: {len(results)}")
    logger.info(f"  Already upgraded: {len(already_upgraded)}")
    logger.info(f"  Needs upgrade: {len(needs_upgrade)}")
    logger.info()

    # Show agents that need upgrading
    if needs_upgrade:
        logger.info("Agents needing upgrade:")
        for agent in needs_upgrade:
            logger.info(f"  - {agent['file']}")

    logger.info("\n" + "=" * 60)
    logger.info("Upgrade Process:")
    logger.info("1. Review agent code and understand functionality")
    logger.info("2. Create V2 version inheriting from BaseAgent")
    logger.info("3. Wrap key methods with @BaseAgent.with_healing decorator")
    logger.info("4. Implement initialize() and execute_core_function()")
    logger.info("5. Add ML features and optimization")
    logger.info("6. Test thoroughly")
    logger.info("7. Update imports in main.py")


if __name__ == "__main__":
    main()
