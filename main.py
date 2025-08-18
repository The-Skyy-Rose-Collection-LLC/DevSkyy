
from fastapi import FastAPI
from agent.modules.scanner import scan_site
from agent.modules.fixer import fix_code
from agent.modules.financial import monitor_financial_health
from agent.modules.inventory import manage_inventory
from agent.modules.customer_service import handle_customer_service
from agent.modules.marketing import optimize_marketing
from agent.scheduler.cron import schedule_hourly_job
from agent.git_commit import commit_fixes
from datetime import datetime
import json

app = FastAPI(title="DevSkyy E-commerce Agent Suite", version="2.0.0")

def run_agent() -> dict:
    """Execute the full DevSkyy agent workflow."""
    try:
        # Original workflow
        raw_code = scan_site()
        fixed_code = fix_code(raw_code)
        commit_fixes(fixed_code)
        
        # New agent workflows
        financial_status = monitor_financial_health()
        inventory_status = manage_inventory()
        customer_service_status = handle_customer_service()
        marketing_status = optimize_marketing()
        
        # Schedule next run
        schedule_hourly_job()
        
        # Compile comprehensive status report
        status_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "code_scanning": "completed",
            "financial": financial_status,
            "inventory": inventory_status,
            "customer_service": customer_service_status,
            "marketing": marketing_status,
            "overall_health": _calculate_overall_health([
                financial_status,
                inventory_status,
                customer_service_status,
                marketing_status
            ])
        }
        
        # Save detailed report
        commit_fixes(json.dumps(status_report, indent=2), "agent_status_report.json")
        
        return {"status": "completed", "summary": status_report}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

def _calculate_overall_health(agent_statuses) -> str:
    """Calculate overall system health based on agent reports."""
    critical_issues = 0
    
    # Check financial health
    if agent_statuses[0].get("overall_status") == "NEEDS_ATTENTION":
        critical_issues += 1
    
    # Check inventory issues
    if agent_statuses[1].get("action_required"):
        critical_issues += 1
    
    # Check customer service performance
    if agent_statuses[2].get("overall_status") == "NEEDS_ATTENTION":
        critical_issues += 1
    
    # Check marketing performance
    if agent_statuses[3].get("action_required"):
        critical_issues += 1
    
    if critical_issues == 0:
        return "EXCELLENT"
    elif critical_issues <= 1:
        return "GOOD"
    elif critical_issues <= 2:
        return "FAIR"
    else:
        return "CRITICAL"

@app.post("/run")
def run() -> dict:
    """Endpoint to trigger the complete DevSkyy agent workflow."""
    return run_agent()

@app.get("/")
def root() -> dict:
    """Health check endpoint."""
    return {
        "message": "DevSkyy E-commerce Agent Suite online",
        "agents": [
            "Code Scanner & Fixer",
            "Financial Monitor",
            "Inventory Manager", 
            "Customer Service Automation",
            "Marketing Optimizer"
        ],
        "version": "2.0.0"
    }

@app.get("/financial/status")
def financial_status() -> dict:
    """Get current financial status."""
    return monitor_financial_health()

@app.get("/inventory/status")
def inventory_status() -> dict:
    """Get current inventory status."""
    return manage_inventory()

@app.get("/customer-service/status")
def customer_service_status() -> dict:
    """Get customer service metrics."""
    return handle_customer_service()

@app.get("/marketing/status")
def marketing_status() -> dict:
    """Get marketing performance data."""
    return optimize_marketing()

@app.post("/customer-service/auto-respond")
def auto_respond(ticket_content: str, customer_name: str = "Valued Customer") -> dict:
    """Generate automated customer service response."""
    from agent.modules.customer_service import CustomerServiceAgent
    
    agent = CustomerServiceAgent()
    categorization = agent.auto_categorize_tickets(ticket_content)
    
    if categorization["auto_response_available"]:
        response = agent.generate_auto_response(categorization["category"], customer_name)
        return {
            "category": categorization["category"],
            "confidence": categorization["confidence"],
            "auto_response": response,
            "priority": categorization["suggested_priority"]
        }
    else:
        return {
            "category": categorization["category"],
            "message": "Ticket requires human attention",
            "priority": categorization["suggested_priority"]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
