
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import json


class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class ProductCategory(Enum):
    TOPS = "tops"
    BOTTOMS = "bottoms"
    DRESSES = "dresses"
    OUTERWEAR = "outerwear"
    ACCESSORIES = "accessories"
    FOOTWEAR = "footwear"
    LINGERIE = "lingerie"


@dataclass
class Product:
    id: str
    name: str
    category: ProductCategory
    price: float
    cost: float
    stock_quantity: int
    sku: str
    sizes: List[str]
    colors: List[str]
    description: str
    images: List[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class Customer:
    id: str
    email: str
    first_name: str
    last_name: str
    phone: str
    birthdate: Optional[datetime]
    loyalty_tier: str
    total_spent: float
    order_count: int
    created_at: datetime
    preferences: Dict[str, Any]


@dataclass
class Order:
    id: str
    customer_id: str
    status: OrderStatus
    items: List[Dict[str, Any]]
    subtotal: float
    tax: float
    shipping: float
    total: float
    shipping_address: Dict[str, str]
    billing_address: Dict[str, str]
    created_at: datetime
    updated_at: datetime


class EcommerceAgent:
    """Comprehensive ecommerce agent for fashion brand operations."""
    
    def __init__(self):
        self.products: List[Product] = []
        self.customers: List[Customer] = []
        self.orders: List[Order] = []
        self.analytics_data = {}
    
    def add_product(self, name: str, category: ProductCategory, price: float, 
                   cost: float, stock_quantity: int, sku: str, sizes: List[str],
                   colors: List[str], description: str, images: List[str] = None,
                   tags: List[str] = None) -> Dict[str, Any]:
        """Add a new product to the catalog."""
        
        product_id = f"prod_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.products)}"
        
        product = Product(
            id=product_id,
            name=name,
            category=category,
            price=price,
            cost=cost,
            stock_quantity=stock_quantity,
            sku=sku,
            sizes=sizes,
            colors=colors,
            description=description,
            images=images or [],
            tags=tags or [],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.products.append(product)
        
        return {
            "product_id": product_id,
            "status": "created",
            "sku": sku,
            "name": name
        }
    
    def update_inventory(self, product_id: str, quantity_change: int) -> Dict[str, Any]:
        """Update product inventory levels."""
        
        product = next((p for p in self.products if p.id == product_id), None)
        if not product:
            return {"error": "Product not found"}
        
        old_quantity = product.stock_quantity
        product.stock_quantity += quantity_change
        product.updated_at = datetime.now()
        
        # Check for low stock alerts
        alerts = []
        if product.stock_quantity <= 5 and product.stock_quantity > 0:
            alerts.append(f"Low stock warning: {product.name} ({product.stock_quantity} remaining)")
        elif product.stock_quantity <= 0:
            alerts.append(f"Out of stock: {product.name}")
        
        return {
            "product_id": product_id,
            "old_quantity": old_quantity,
            "new_quantity": product.stock_quantity,
            "change": quantity_change,
            "alerts": alerts
        }
    
    def create_customer(self, email: str, first_name: str, last_name: str,
                       phone: str = "", birthdate: datetime = None,
                       preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new customer profile."""
        
        # Check if customer already exists
        existing = next((c for c in self.customers if c.email == email), None)
        if existing:
            return {"error": "Customer with this email already exists"}
        
        customer_id = f"cust_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.customers)}"
        
        customer = Customer(
            id=customer_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            birthdate=birthdate,
            loyalty_tier="bronze",
            total_spent=0.0,
            order_count=0,
            created_at=datetime.now(),
            preferences=preferences or {}
        )
        
        self.customers.append(customer)
        
        return {
            "customer_id": customer_id,
            "status": "created",
            "email": email,
            "loyalty_tier": "bronze"
        }
    
    def create_order(self, customer_id: str, items: List[Dict[str, Any]],
                    shipping_address: Dict[str, str], billing_address: Dict[str, str] = None,
                    tax_rate: float = 0.08, shipping_cost: float = 9.99) -> Dict[str, Any]:
        """Create a new order."""
        
        customer = next((c for c in self.customers if c.id == customer_id), None)
        if not customer:
            return {"error": "Customer not found"}
        
        # Validate and calculate order totals
        order_items = []
        subtotal = 0.0
        
        for item in items:
            product = next((p for p in self.products if p.id == item["product_id"]), None)
            if not product:
                return {"error": f"Product {item['product_id']} not found"}
            
            quantity = item["quantity"]
            if product.stock_quantity < quantity:
                return {"error": f"Insufficient stock for {product.name}"}
            
            item_total = product.price * quantity
            subtotal += item_total
            
            order_items.append({
                "product_id": product.id,
                "name": product.name,
                "sku": product.sku,
                "price": product.price,
                "quantity": quantity,
                "size": item.get("size", ""),
                "color": item.get("color", ""),
                "total": item_total
            })
            
            # Update inventory
            product.stock_quantity -= quantity
        
        tax = subtotal * tax_rate
        total = subtotal + tax + shipping_cost
        
        order_id = f"ord_{datetime.now().strftime('%Y%m%d%H%M%S')}_{customer_id[-8:]}"
        
        order = Order(
            id=order_id,
            customer_id=customer_id,
            status=OrderStatus.PENDING,
            items=order_items,
            subtotal=subtotal,
            tax=tax,
            shipping=shipping_cost,
            total=total,
            shipping_address=shipping_address,
            billing_address=billing_address or shipping_address,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.orders.append(order)
        
        # Update customer metrics
        customer.total_spent += total
        customer.order_count += 1
        self._update_loyalty_tier(customer)
        
        return {
            "order_id": order_id,
            "status": "created",
            "total": total,
            "items_count": len(order_items)
        }
    
    def _update_loyalty_tier(self, customer: Customer):
        """Update customer loyalty tier based on spending."""
        if customer.total_spent >= 1000:
            customer.loyalty_tier = "gold"
        elif customer.total_spent >= 500:
            customer.loyalty_tier = "silver"
        else:
            customer.loyalty_tier = "bronze"
    
    def get_product_recommendations(self, customer_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Generate product recommendations for a customer."""
        
        customer = next((c for c in self.customers if c.id == customer_id), None)
        if not customer:
            return []
        
        # Get customer's order history
        customer_orders = [o for o in self.orders if o.customer_id == customer_id]
        
        # Analyze purchase patterns
        purchased_categories = set()
        preferred_price_range = []
        
        for order in customer_orders:
            for item in order.items:
                product = next((p for p in self.products if p.id == item["product_id"]), None)
                if product:
                    purchased_categories.add(product.category)
                    preferred_price_range.append(product.price)
        
        if preferred_price_range:
            avg_price = sum(preferred_price_range) / len(preferred_price_range)
            price_tolerance = avg_price * 0.3  # 30% tolerance
        else:
            avg_price = 100  # Default
            price_tolerance = 30
        
        # Find recommendations
        recommendations = []
        for product in self.products:
            if product.stock_quantity > 0:
                score = 0
                
                # Category match
                if product.category in purchased_categories:
                    score += 3
                
                # Price range match
                if abs(product.price - avg_price) <= price_tolerance:
                    score += 2
                
                # New arrivals boost
                if (datetime.now() - product.created_at).days <= 30:
                    score += 1
                
                if score > 0:
                    recommendations.append({
                        "product_id": product.id,
                        "name": product.name,
                        "price": product.price,
                        "category": product.category.value,
                        "score": score,
                        "images": product.images[:1]  # First image only
                    })
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:limit]
    
    def generate_analytics_report(self) -> Dict[str, Any]:
        """Generate comprehensive analytics report."""
        now = datetime.now()
        last_30_days = now - timedelta(days=30)
        
        # Sales metrics
        recent_orders = [o for o in self.orders if o.created_at >= last_30_days]
        total_revenue = sum(o.total for o in recent_orders)
        total_orders = len(recent_orders)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Product performance
        product_sales = {}
        for order in recent_orders:
            for item in order.items:
                if item["product_id"] not in product_sales:
                    product_sales[item["product_id"]] = 0
                product_sales[item["product_id"]] += item["quantity"]
        
        top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Customer metrics
        new_customers = [c for c in self.customers if c.created_at >= last_30_days]
        repeat_customers = [c for c in self.customers if c.order_count > 1]
        
        # Inventory alerts
        low_stock = [p for p in self.products if 0 < p.stock_quantity <= 5]
        out_of_stock = [p for p in self.products if p.stock_quantity == 0]
        
        return {
            "report_period": "Last 30 days",
            "generated_at": now.isoformat(),
            "sales": {
                "total_revenue": round(total_revenue, 2),
                "total_orders": total_orders,
                "average_order_value": round(avg_order_value, 2)
            },
            "products": {
                "top_selling": [
                    {
                        "product_id": pid,
                        "name": next((p.name for p in self.products if p.id == pid), "Unknown"),
                        "units_sold": units
                    } for pid, units in top_products
                ]
            },
            "customers": {
                "new_customers": len(new_customers),
                "repeat_customers": len(repeat_customers),
                "total_customers": len(self.customers)
            },
            "inventory": {
                "low_stock_items": len(low_stock),
                "out_of_stock_items": len(out_of_stock),
                "total_products": len(self.products)
            },
            "alerts": {
                "low_stock": [{"id": p.id, "name": p.name, "quantity": p.stock_quantity} for p in low_stock],
                "out_of_stock": [{"id": p.id, "name": p.name} for p in out_of_stock]
            }
        }
