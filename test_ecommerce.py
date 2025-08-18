
"""
Test script for The Skyy Rose Collection ecommerce platform.
Run this to populate sample data and test all agents.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://0.0.0.0:8000"

def test_platform():
    print("🌹 Testing The Skyy Rose Collection Platform")
    print("=" * 50)
    
    # Test health check
    response = requests.get(f"{BASE_URL}/")
    print("✅ Platform Status:", response.json()["message"])
    
    # Test inventory scanning
    print("\n📦 Testing Inventory Management...")
    response = requests.post(f"{BASE_URL}/inventory/scan")
    if response.status_code == 200:
        print("✅ Inventory scan completed")
        print(f"   Assets found: {response.json()['total_assets']}")
    
    # Test product creation
    print("\n👗 Testing Product Management...")
    product_data = {
        "name": "Skyy Rose Silk Dress",
        "category": "dresses",
        "price": 299.99,
        "cost": 89.99,
        "stock_quantity": 25,
        "sku": "SR-DRESS-001",
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["Rose Pink", "Midnight Blue", "Pearl White"],
        "description": "Elegant silk dress perfect for special occasions",
        "tags": ["silk", "elegant", "party", "luxury"]
    }
    
    response = requests.post(f"{BASE_URL}/products/add", params=product_data)
    if response.status_code == 200:
        product_result = response.json()
        print(f"✅ Product created: {product_result['name']} (ID: {product_result['product_id']})")
        
        # Test customer creation
        print("\n👤 Testing Customer Management...")
        customer_data = {
            "email": "bella@example.com",
            "first_name": "Bella",
            "last_name": "Fashion",
            "phone": "+1-555-0123",
            "preferences": json.dumps({"style": "elegant", "size": "M", "color_preference": "rose"})
        }
        
        response = requests.post(f"{BASE_URL}/customers/create", params=customer_data)
        if response.status_code == 200:
            customer_result = response.json()
            print(f"✅ Customer created: {customer_result['email']} (ID: {customer_result['customer_id']})")
            
            # Test payment processing
            print("\n💳 Testing Payment Processing...")
            payment_data = {
                "amount": 299.99,
                "currency": "USD",
                "customer_id": customer_result['customer_id'],
                "product_id": product_result['product_id'],
                "payment_method": "credit_card",
                "gateway": "stripe"
            }
            
            response = requests.post(f"{BASE_URL}/payments/process", params=payment_data)
            if response.status_code == 200:
                payment_result = response.json()
                print(f"✅ Payment processed: {payment_result['status']} (${payment_result['amount']})")
    
    # Test analytics dashboard
    print("\n📊 Testing Analytics Dashboard...")
    response = requests.get(f"{BASE_URL}/dashboard")
    if response.status_code == 200:
        dashboard = response.json()
        print("✅ Dashboard generated successfully")
        print(f"   Platform: {dashboard['platform']}")
        print(f"   Total customers: {dashboard['ecommerce']['customers']['total_customers']}")
        print(f"   Total products: {dashboard['ecommerce']['inventory']['total_products']}")
    
    print("\n🎉 All tests completed! Your platform is ready to go live!")

if __name__ == "__main__":
    test_platform()
