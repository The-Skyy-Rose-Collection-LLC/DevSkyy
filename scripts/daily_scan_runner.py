#!/usr/bin/env python3
"""
Daily Scan Runner for CI/CD
Properly handles async functions for daily scanning
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import from agent modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from agent.modules.scanner import scan_site
    from agent.modules.performance_agent import PerformanceAgent
    from agent.modules.security_agent import SecurityAgent
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


async def run_daily_scan():
    """Run the daily scan with proper async handling."""
    try:
        print("🔍 Starting daily website scan...")
        
        # Run comprehensive scan (this is synchronous)
        scan_results = scan_site()
        print("✅ Site scan completed")
        
        # Performance analysis (this is async)
        perf_agent = PerformanceAgent()
        perf_results = await perf_agent.analyze_site_performance()
        print("✅ Performance analysis completed")
        
        # Security analysis (this is async) 
        sec_agent = SecurityAgent()
        sec_results = await sec_agent.security_assessment()
        print("✅ Security analysis completed")
        
        # Compile report
        report = {
            'timestamp': datetime.now().isoformat(),
            'scan_results': scan_results,
            'performance_analysis': perf_results,
            'security_assessment': sec_results,
            'status': 'completed'
        }
        
        # Save report
        with open('daily-scan-report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print("✅ Daily scan completed successfully")
        return report
        
    except Exception as e:
        print(f"❌ Daily scan failed: {str(e)}")
        error_report = {
            'timestamp': datetime.now().isoformat(),
            'status': 'failed',
            'error': str(e)
        }
        
        with open('daily-scan-report.json', 'w') as f:
            json.dump(error_report, f, indent=2)
        
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_daily_scan())