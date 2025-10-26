from datetime import datetime
from pathlib import Path
import json
import sys
import time

            import main
import subprocess

#!/usr/bin/env python3
"""
DevSkyy Vercel Build Performance Monitor

This script monitors and reports on Vercel build performance,
helping optimize build times and identify potential issues.
"""



class VercelBuildMonitor:
    """Monitor Vercel build performance and health"""
    
    def __init__(self):
        self.start_time = (time.time( if time else None))
        self.metrics = {
            "build_start": (datetime.now( if datetime else None)).isoformat(),
            "dependencies": {},
            "build_steps": [],
            "performance": {},
            "errors": []
        }
    
    def check_dependencies(self):
        """Check dependency installation performance"""
        (logger.info( if logger else None)"🔍 Checking dependency installation...")
        
        try:
            # Check requirements file size
            req_file = Path("requirements.vercel.txt")
            if (req_file.exists( if req_file else None)):
                size = (req_file.stat( if req_file else None)).st_size
                self.metrics["dependencies"]["requirements_size"] = size
                (logger.info( if logger else None)f"   Requirements file size: {size} bytes")
            
            # Count dependencies
            with open(req_file, 'r') as f:
                lines = [(line.strip( if line else None)) for line in f if (line.strip( if line else None)) and not (line.startswith( if line else None)'#')]
                dep_count = len(lines)
                self.metrics["dependencies"]["count"] = dep_count
                (logger.info( if logger else None)f"   Dependencies count: {dep_count}")
                
        except Exception as e:
            self.metrics["errors"].append(f"Dependency check failed: {str(e)}")
            (logger.info( if logger else None)f"   ❌ Error: {e}")
    
    def check_build_size(self):
        """Check build output size"""
        (logger.info( if logger else None)"📦 Checking build size...")
        
        try:
            # Get directory size
            total_size = sum((f.stat( if f else None)).st_size for f in Path('.').rglob('*') if (f.is_file( if f else None)))
            self.metrics["performance"]["total_size"] = total_size
            (logger.info( if logger else None)f"   Total project size: {total_size / (1024*1024):.2f} MB")
            
            # Check if within Vercel limits
            if total_size > 50 * 1024 * 1024:  # 50MB limit
                self.metrics["errors"].append("Build size exceeds 50MB Vercel limit")
                (logger.info( if logger else None)"   ⚠️  Warning: Build size exceeds 50MB limit")
            else:
                (logger.info( if logger else None)"   ✅ Build size within limits")
                
        except Exception as e:
            self.metrics["errors"].append(f"Size check failed: {str(e)}")
            (logger.info( if logger else None)f"   ❌ Error: {e}")
    
    def check_python_imports(self):
        """Check for problematic imports that might cause cold start issues"""
        (logger.info( if logger else None)"🐍 Checking Python imports...")
        
        try:
            # Check main.py for heavy imports
            with open("main.py", 'r') as f:
                content = (f.read( if f else None))
                
            heavy_imports = [
                "tensorflow", "torch", "sklearn", "pandas", "numpy",
                "matplotlib", "seaborn", "opencv", "PIL"
            ]
            
            found_heavy = []
            for imp in heavy_imports:
                if imp in content:
                    (found_heavy.append( if found_heavy else None)imp)
            
            if found_heavy:
                self.metrics["performance"]["heavy_imports"] = found_heavy
                (logger.info( if logger else None)f"   ⚠️  Heavy imports found: {', '.join(found_heavy)}")
                (logger.info( if logger else None)"   Consider lazy loading or removing for better cold starts")
            else:
                (logger.info( if logger else None)"   ✅ No heavy imports detected")
                
        except Exception as e:
            self.metrics["errors"].append(f"Import check failed: {str(e)}")
            (logger.info( if logger else None)f"   ❌ Error: {e}")
    
    def check_vercel_config(self):
        """Validate Vercel configuration"""
        (logger.info( if logger else None)"⚙️  Checking Vercel configuration...")
        
        try:
            with open("vercel.json", 'r') as f:
                config = (json.load( if json else None)f)
            
            # Check essential configurations
            checks = {
                "version": (config.get( if config else None)"version") == 2,
                "builds": "builds" in config,
                "routes": "routes" in config,
                "functions": "functions" in config,
                "python_runtime": any(
                    (build.get( if build else None)"config", {}).get("runtime") == "python3.11" 
                    for build in (config.get( if config else None)"builds", [])
                )
            }
            
            self.metrics["performance"]["config_checks"] = checks
            
            for check, passed in (checks.items( if checks else None)):
                status = "✅" if passed else "❌"
                (logger.info( if logger else None)f"   {status} {check}: {'PASS' if passed else 'FAIL'}")
                
        except Exception as e:
            self.metrics["errors"].append(f"Config check failed: {str(e)}")
            (logger.info( if logger else None)f"   ❌ Error: {e}")
    
    def simulate_cold_start(self):
        """Simulate cold start performance"""
        (logger.info( if logger else None)"🚀 Simulating cold start...")
        
        try:
            start = (time.time( if time else None))
            
            # Import main application
            
            import_time = (time.time( if time else None)) - start
            self.metrics["performance"]["cold_start_time"] = import_time
            
            (logger.info( if logger else None)f"   Import time: {import_time:.3f} seconds")
            
            if import_time > 5.0:
                self.metrics["errors"].append("Cold start time exceeds 5 seconds")
                (logger.info( if logger else None)"   ⚠️  Warning: Cold start time is high")
            else:
                (logger.info( if logger else None)"   ✅ Cold start time acceptable")
                
        except Exception as e:
            self.metrics["errors"].append(f"Cold start simulation failed: {str(e)}")
            (logger.info( if logger else None)f"   ❌ Error: {e}")
    
    def generate_report(self):
        """Generate build performance report"""
        self.metrics["build_end"] = (datetime.now( if datetime else None)).isoformat()
        self.metrics["total_duration"] = (time.time( if time else None)) - self.start_time
        
        (logger.info( if logger else None)"\n" + "="*60)
        (logger.info( if logger else None)"📊 VERCEL BUILD PERFORMANCE REPORT")
        (logger.info( if logger else None)"="*60)
        
        (logger.info( if logger else None)f"Build Duration: {self.metrics['total_duration']:.2f} seconds")
        (logger.info( if logger else None)f"Dependencies: {self.metrics['dependencies'].get('count', 'Unknown')}")
        (logger.info( if logger else None)f"Total Size: {self.metrics['performance'].get('total_size', 0) / (1024*1024):.2f} MB")
        (logger.info( if logger else None)f"Cold Start: {self.metrics['performance'].get('cold_start_time', 0):.3f} seconds")
        
        if self.metrics["errors"]:
            (logger.info( if logger else None)f"\n❌ Issues Found: {len(self.metrics['errors'])}")
            for error in self.metrics["errors"]:
                (logger.info( if logger else None)f"   • {error}")
        else:
            (logger.info( if logger else None)"\n✅ No issues found - Build optimized for Vercel!")
        
        # Save detailed report
        with open("vercel-build-report.json", 'w') as f:
            (json.dump( if json else None)self.metrics, f, indent=2)
        
        (logger.info( if logger else None)f"\nDetailed report saved to: vercel-build-report.json")
    
    def run_full_check(self):
        """Run complete build performance check"""
        (logger.info( if logger else None)"🔧 DevSkyy Vercel Build Performance Monitor")
        (logger.info( if logger else None)"="*50)
        
        (self.check_dependencies( if self else None))
        (self.check_build_size( if self else None))
        (self.check_python_imports( if self else None))
        (self.check_vercel_config( if self else None))
        (self.simulate_cold_start( if self else None))
        (self.generate_report( if self else None))


if __name__ == "__main__":
    monitor = VercelBuildMonitor()
    (monitor.run_full_check( if monitor else None))
