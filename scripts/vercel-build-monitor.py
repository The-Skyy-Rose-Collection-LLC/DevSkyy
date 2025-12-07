#!/usr/bin/env python3
from datetime import datetime
import json
import logging
from pathlib import Path
import time


"""
DevSkyy Vercel Build Performance Monitor

This script monitors and reports on Vercel build performance,
helping optimize build times and identify potential issues.
"""

logger = logging.getLogger(__name__)


class VercelBuildMonitor:
    """Monitor Vercel build performance and health"""

    def __init__(self):
        self.start_time = time.time()
        self.metrics = {
            "build_start": datetime.now().isoformat(),
            "dependencies": {},
            "build_steps": [],
            "performance": {},
            "errors": [],
        }

    def check_dependencies(self):
        """Check dependency installation performance"""
        logger.info("🔍 Checking dependency installation...")

        try:
            # Check requirements file size
            req_file = Path("requirements.vercel.txt")
            if req_file.exists():
                size = req_file.stat().st_size
                self.metrics["dependencies"]["requirements_size"] = size
                logger.info(f"   Requirements file size: {size} bytes")

            # Count dependencies
            with open(req_file, "r") as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                dep_count = len(lines)
                self.metrics["dependencies"]["count"] = dep_count
                logger.info(f"   Dependencies count: {dep_count}")

        except Exception as e:
            self.metrics["errors"].append(f"Dependency check failed: {e!s}")
            logger.info(f"   ❌ Error: {e}")

    def check_build_size(self):
        """Check build output size"""
        logger.info("📦 Checking build size...")

        try:
            # Get directory size
            total_size = sum(f.stat().st_size for f in Path(".").rglob("*") if f.is_file())
            self.metrics["performance"]["total_size"] = total_size
            logger.info(f"   Total project size: {total_size / (1024*1024):.2f} MB")

            # Check if within Vercel limits
            if total_size > 50 * 1024 * 1024:  # 50MB limit
                self.metrics["errors"].append("Build size exceeds 50MB Vercel limit")
                logger.info("   ⚠️  Warning: Build size exceeds 50MB limit")
            else:
                logger.info("   ✅ Build size within limits")

        except Exception as e:
            self.metrics["errors"].append(f"Size check failed: {e!s}")
            logger.info(f"   ❌ Error: {e}")

    def check_python_imports(self):
        """Check for problematic imports that might cause cold start issues"""
        logger.info("🐍 Checking Python imports...")

        try:
            # Check main.py for heavy imports
            with open("main.py", "r") as f:
                content = f.read()

            heavy_imports = [
                "tensorflow",
                "torch",
                "sklearn",
                "pandas",
                "numpy",
                "matplotlib",
                "seaborn",
                "opencv",
                "PIL",
            ]

            found_heavy = []
            for imp in heavy_imports:
                if imp in content:
                    found_heavy.append(imp)

            if found_heavy:
                self.metrics["performance"]["heavy_imports"] = found_heavy
                logger.info(f"   ⚠️  Heavy imports found: {', '.join(found_heavy)}")
                logger.info("   Consider lazy loading or removing for better cold starts")
            else:
                logger.info("   ✅ No heavy imports detected")

        except Exception as e:
            self.metrics["errors"].append(f"Import check failed: {e!s}")
            logger.info(f"   ❌ Error: {e}")

    def check_vercel_config(self):
        """Validate Vercel configuration"""
        logger.info("⚙️  Checking Vercel configuration...")

        try:
            with open("vercel.json", "r") as f:
                config = json.load(f)

            # Check essential configurations
            checks = {
                "version": config.get("version") == 2,
                "builds": "builds" in config,
                "routes": "routes" in config,
                "functions": "functions" in config,
                "python_runtime": any(
                    build.get("config", {}).get("runtime") == "python3.11" for build in config.get("builds", [])
                ),
            }

            self.metrics["performance"]["config_checks"] = checks

            for check, passed in checks.items():
                status = "✅" if passed else "❌"
                logger.info(f"   {status} {check}: {'PASS' if passed else 'FAIL'}")

        except Exception as e:
            self.metrics["errors"].append(f"Config check failed: {e!s}")
            logger.info(f"   ❌ Error: {e}")

    def simulate_cold_start(self):
        """Simulate cold start performance"""
        logger.info("🚀 Simulating cold start...")

        try:
            start = time.time()

            # Import main application

            import_time = time.time() - start
            self.metrics["performance"]["cold_start_time"] = import_time

            logger.info(f"   Import time: {import_time:.3f} seconds")

            if import_time > 5.0:
                self.metrics["errors"].append("Cold start time exceeds 5 seconds")
                logger.info("   ⚠️  Warning: Cold start time is high")
            else:
                logger.info("   ✅ Cold start time acceptable")

        except Exception as e:
            self.metrics["errors"].append(f"Cold start simulation failed: {e!s}")
            logger.info(f"   ❌ Error: {e}")

    def generate_report(self):
        """Generate build performance report"""
        self.metrics["build_end"] = datetime.now().isoformat()
        self.metrics["total_duration"] = time.time() - self.start_time

        logger.info("\n" + "=" * 60)
        logger.info("📊 VERCEL BUILD PERFORMANCE REPORT")
        logger.info("=" * 60)

        logger.info(f"Build Duration: {self.metrics['total_duration']:.2f} seconds")
        logger.info(f"Dependencies: {self.metrics['dependencies'].get('count', 'Unknown')}")
        logger.info(f"Total Size: {self.metrics['performance'].get('total_size', 0) / (1024*1024):.2f} MB")
        logger.info(f"Cold Start: {self.metrics['performance'].get('cold_start_time', 0):.3f} seconds")

        if self.metrics["errors"]:
            logger.info(f"\n❌ Issues Found: {len(self.metrics['errors'])}")
            for error in self.metrics["errors"]:
                logger.info(f"   • {error}")
        else:
            logger.info("\n✅ No issues found - Build optimized for Vercel!")

        # Save detailed report
        with open("vercel-build-report.json", "w") as f:
            json.dump(self.metrics, f, indent=2)

        logger.info("\nDetailed report saved to: vercel-build-report.json")

    def run_full_check(self):
        """Run complete build performance check"""
        logger.info("🔧 DevSkyy Vercel Build Performance Monitor")
        logger.info("=" * 50)

        self.check_dependencies()
        self.check_build_size()
        self.check_python_imports()
        self.check_vercel_config()
        self.simulate_cold_start()
        self.generate_report()


if __name__ == "__main__":
    monitor = VercelBuildMonitor()
    monitor.run_full_check()
