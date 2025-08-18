
from fastapi import FastAPI, HTTPException
from agent.modules.scanner import scan_site
from agent.modules.fixer import fix_code
from agent.modules.inventory_agent import InventoryAgent
from agent.modules.financial_agent import FinancialAgent, ChargebackReason
from agent.modules.ecommerce_agent import EcommerceAgent, ProductCategory, OrderStatus
from agent.scheduler.cron import schedule_hourly_job
from agent.git_commit import commit_fixes
from typing import Dict, Any, List
import json


app = FastAPI(title="The Skyy Rose Collection - Ecommerce Platform", version="1.0.0")

# Initialize agents
inventory_agent = InventoryAgent()
financial_agent = FinancialAgent()
ecommerce_agent = EcommerceAgent()


def run_agent() -> dict:
    """Execute the full DevSkyy agent workflow."""
    raw_code = scan_site()
    fixed_code = fix_code(raw_code)
    commit_fixes(fixed_code)
    schedule_hourly_job()
    return {"status": "completed"}


@app.post("/run")
def run() -> dict:
    """Endpoint to trigger the DevSkyy agent workflow."""
    return run_agent()


@app.get("/")
def root() -> dict:
    """Health check endpoint."""
    return {"message": "The Skyy Rose Collection Platform Online ✨"}


# Inventory Management Endpoints
@app.post("/inventory/scan")
def scan_inventory() -> Dict[str, Any]:
    """Scan and analyze all digital assets."""
    assets = inventory_agent.scan_assets()
    duplicates = inventory_agent.find_duplicates()
    
    return {
        "total_assets": len(assets),
        "duplicate_groups": len(duplicates),
        "scan_completed": True
    }


@app.get("/inventory/report")
def get_inventory_report() -> Dict[str, Any]:
    """Get comprehensive inventory report."""
    return inventory_agent.generate_report()


@app.post("/inventory/cleanup")
def cleanup_duplicates(keep_strategy: str = "latest") -> Dict[str, Any]:
    """Remove duplicate assets."""
    if keep_strategy not in ["latest", "largest", "first"]:
        raise HTTPException(status_code=400, detail="Invalid keep_strategy")
    
    result = inventory_agent.remove_duplicates(keep_strategy)
    return result


@app.get("/inventory/visualize")
def visualize_similarities() -> Dict[str, str]:
    """Get visual representation of asset similarities."""
    visualization = inventory_agent.visualize_similarities()
    return {"visualization": visualization}


# Financial Management Endpoints
@app.post("/payments/process")
def process_payment(amount: float, currency: str, customer_id: str, 
                   product_id: str, payment_method: str, gateway: str = "stripe") -> Dict[str, Any]:
    """Process a payment transaction."""
    return financial_agent.process_payment(
        amount, currency, customer_id, product_id, payment_method, gateway
    )


@app.post("/chargebacks/create")
def create_chargeback(transaction_id: str, reason: str, amount: float = None) -> Dict[str, Any]:
    """Create a chargeback case."""
    try:
        chargeback_reason = ChargebackReason(reason.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chargeback reason")
    
    return financial_agent.create_chargeback(transaction_id, chargeback_reason, amount)


@app.post("/chargebacks/{chargeback_id}/evidence")
def submit_chargeback_evidence(chargeback_id: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Submit evidence for a chargeback dispute."""
    return financial_agent.submit_chargeback_evidence(chargeback_id, evidence)


@app.get("/financial/dashboard")
def get_financial_dashboard() -> Dict[str, Any]:
    """Get comprehensive financial dashboard."""
    return financial_agent.get_financial_dashboard()


# Ecommerce Management Endpoints
@app.post("/products/add")
def add_product(name: str, category: str, price: float, cost: float, 
               stock_quantity: int, sku: str, sizes: List[str], colors: List[str],
               description: str, images: List[str] = None, tags: List[str] = None) -> Dict[str, Any]:
    """Add a new product to the catalog."""
    try:
        product_category = ProductCategory(category.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product category")
    
    return ecommerce_agent.add_product(
        name, product_category, price, cost, stock_quantity, sku, 
        sizes, colors, description, images, tags
    )


@app.post("/inventory/{product_id}/update")
def update_inventory(product_id: str, quantity_change: int) -> Dict[str, Any]:
    """Update product inventory levels."""
    return ecommerce_agent.update_inventory(product_id, quantity_change)


@app.post("/customers/create")
def create_customer(email: str, first_name: str, last_name: str, 
                   phone: str = "", preferences: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create a new customer profile."""
    return ecommerce_agent.create_customer(email, first_name, last_name, phone, None, preferences)


@app.post("/orders/create")
def create_order(customer_id: str, items: List[Dict[str, Any]], 
                shipping_address: Dict[str, str], billing_address: Dict[str, str] = None) -> Dict[str, Any]:
    """Create a new order."""
    return ecommerce_agent.create_order(customer_id, items, shipping_address, billing_address)


@app.get("/customers/{customer_id}/recommendations")
def get_recommendations(customer_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get product recommendations for a customer."""
    return ecommerce_agent.get_product_recommendations(customer_id, limit)


@app.get("/analytics/report")
def get_analytics_report() -> Dict[str, Any]:
    """Get comprehensive analytics report."""
    return ecommerce_agent.generate_analytics_report()


# Combined Dashboard Endpoint
@app.get("/dashboard")
def get_complete_dashboard() -> Dict[str, Any]:
    """Get comprehensive platform dashboard."""
    return {
        "platform": "The Skyy Rose Collection",
        "timestamp": "2024-01-20T12:00:00Z",
        "inventory": inventory_agent.generate_report(),
        "financial": financial_agent.get_financial_dashboard(),
        "ecommerce": ecommerce_agent.generate_analytics_report()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
