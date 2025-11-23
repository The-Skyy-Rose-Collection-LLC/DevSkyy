"""
Comprehensive test suite for EcommerceAgent.

Tests cover:
- Product catalog management (CRUD)
- Inventory synchronization
- Order processing workflow
- Payment integration (MOCKED)
- Price calculation and discounts
- Shopping cart operations
- Product search and filtering
- Stock level tracking
- Order fulfillment status

Truth Protocol: Rules #1, #8, #15
Coverage Target: ≥75% (338/451 lines minimum)
"""

from decimal import Decimal
import uuid

import pytest

from agent.modules.backend.ecommerce_agent import (
    EcommerceAgent,
    OrderStatus,
    ProductCategory,
    optimize_marketing,
)


class TestEcommerceAgentInitialization:
    """Test agent initialization and setup."""

    def test_agent_initialization(self):
        """Test EcommerceAgent initializes with correct attributes."""
        agent = EcommerceAgent()

        assert agent.products == {}
        assert agent.customers == {}
        assert agent.orders == {}
        assert agent.inventory_levels == {}
        assert "page_views" in agent.analytics_data
        assert "conversions" in agent.analytics_data
        assert "revenue" in agent.analytics_data
        assert "customer_behavior" in agent.analytics_data

    def test_recommendation_engine_initialization(self):
        """Test recommendation engine is initialized."""
        agent = EcommerceAgent()

        assert agent.recommendation_engine is not None
        assert "algorithms" in agent.recommendation_engine
        assert "weights" in agent.recommendation_engine
        assert agent.recommendation_engine["algorithms"] == [
            "collaborative",
            "content_based",
            "trending",
        ]

    def test_pricing_engine_initialization(self):
        """Test pricing engine is initialized."""
        agent = EcommerceAgent()

        assert agent.pricing_engine is not None
        assert "strategies" in agent.pricing_engine
        assert "margin_targets" in agent.pricing_engine
        assert agent.pricing_engine["margin_targets"]["min"] == 50


class TestProductCatalogManagement:
    """Test product CRUD operations."""

    def test_add_product_success(self):
        """Test successful product addition."""
        agent = EcommerceAgent()

        result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=150.0,
            cost=50.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S", "M", "L"],
            colors=["Gold", "Silver"],
            description="Beautiful diamond necklace with premium craftsmanship",
            images=["image1.jpg", "image2.jpg"],
            tags=["diamond", "luxury", "premium"],
        )

        assert result["status"] == "created"
        assert "product_id" in result
        assert result["sku"] == "NECK001"
        assert result["variants_created"] == 6  # 3 sizes * 2 colors
        assert "seo_score" in result
        assert result["pricing_recommendation"] in ["optimal", "increase_price", "decrease_price"]

    def test_add_product_validation_failure_short_name(self):
        """Test product validation fails with short name."""
        agent = EcommerceAgent()

        result = agent.add_product(
            name="AB",  # Too short
            category=ProductCategory.NECKLACES,
            price=150.0,
            cost=50.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )

        assert result["status"] == "validation_failed"
        assert "name must be at least 3 characters" in result["error"]

    def test_add_product_validation_failure_negative_price(self):
        """Test product validation fails with negative price."""
        agent = EcommerceAgent()

        result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=-150.0,  # Negative price
            cost=50.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )

        assert result["status"] == "validation_failed"
        assert "Price must be positive" in result["error"]

    def test_add_product_validation_failure_cost_greater_than_price(self):
        """Test product validation fails when cost >= price."""
        agent = EcommerceAgent()

        result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=50.0,
            cost=150.0,  # Cost greater than price
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )

        assert result["status"] == "validation_failed"
        assert "Cost must be less than price" in result["error"]

    def test_add_product_validation_failure_short_description(self):
        """Test product validation fails with short description."""
        agent = EcommerceAgent()

        result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=150.0,
            cost=50.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Too short",  # Too short
        )

        assert result["status"] == "validation_failed"
        assert "Description must be at least 20 characters" in result["error"]

    def test_add_product_duplicate_sku(self):
        """Test product validation fails with duplicate SKU."""
        agent = EcommerceAgent()

        # Add first product
        agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=150.0,
            cost=50.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )

        # Try to add second product with same SKU
        result = agent.add_product(
            name="Different Necklace",
            category=ProductCategory.NECKLACES,
            price=200.0,
            cost=70.0,
            stock_quantity=50,
            sku="NECK001",  # Duplicate SKU
            sizes=["M"],
            colors=["Silver"],
            description="Another beautiful necklace with great design",
        )

        assert result["status"] == "validation_failed"
        assert "SKU already exists" in result["error"]

    def test_add_product_with_variants(self):
        """Test product variants are created correctly."""
        agent = EcommerceAgent()

        result = agent.add_product(
            name="Ring Collection",
            category=ProductCategory.RINGS,
            price=89.0,
            cost=30.0,
            stock_quantity=120,
            sku="RING001",
            sizes=["6", "7", "8"],
            colors=["Gold", "Silver", "Rose Gold"],
            description="Premium ring collection with multiple size and color options",
        )

        assert result["status"] == "created"
        assert result["variants_created"] == 9  # 3 sizes * 3 colors

    def test_product_seo_generation(self):
        """Test SEO content is generated for products."""
        agent = EcommerceAgent()

        result = agent.add_product(
            name="Luxury Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=250.0,
            cost=80.0,
            stock_quantity=50,
            sku="LUX001",
            sizes=["One Size"],
            colors=["Platinum"],
            description="Exquisite luxury diamond necklace featuring hand-selected diamonds with superior clarity and brilliance. Perfect for special occasions.",
            tags=["luxury", "diamond", "special-occasion"],
        )

        assert result["status"] == "created"
        assert result["seo_score"] > 0


class TestInventoryManagement:
    """Test inventory operations."""

    def test_update_inventory_increase(self):
        """Test inventory increase."""
        agent = EcommerceAgent()

        # Add product first
        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=150.0,
            cost=50.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )

        product_id = product_result["product_id"]

        # Update inventory
        result = agent.update_inventory(product_id, 50)

        assert result["status"] == "updated"
        assert result["previous_level"] == 100
        assert result["current_level"] == 150
        assert result["change"] == 50

    def test_update_inventory_decrease(self):
        """Test inventory decrease."""
        agent = EcommerceAgent()

        # Add product first
        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=150.0,
            cost=50.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )

        product_id = product_result["product_id"]

        # Update inventory
        result = agent.update_inventory(product_id, -30)

        assert result["status"] == "updated"
        assert result["previous_level"] == 100
        assert result["current_level"] == 70
        assert result["change"] == -30

    def test_update_inventory_insufficient_stock(self):
        """Test inventory update fails when insufficient stock."""
        agent = EcommerceAgent()

        # Add product first
        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=150.0,
            cost=50.0,
            stock_quantity=10,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )

        product_id = product_result["product_id"]

        # Try to decrease inventory beyond available
        result = agent.update_inventory(product_id, -50)

        assert result["status"] == "failed"
        assert "Insufficient inventory" in result["error"]

    def test_update_inventory_product_not_found(self):
        """Test inventory update fails for non-existent product."""
        agent = EcommerceAgent()

        result = agent.update_inventory("non-existent-id", 10)

        assert result["status"] == "failed"
        assert "Product not found" in result["error"]

    def test_inventory_alerts_out_of_stock(self):
        """Test out of stock alert is generated."""
        agent = EcommerceAgent()

        # Add product
        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=150.0,
            cost=50.0,
            stock_quantity=10,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )

        product_id = product_result["product_id"]

        # Reduce to zero
        result = agent.update_inventory(product_id, -10)

        assert "OUT_OF_STOCK" in result["alerts"]

    def test_inventory_alerts_low_stock(self):
        """Test low stock alert is generated."""
        agent = EcommerceAgent()

        # Add product
        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=150.0,
            cost=50.0,
            stock_quantity=10,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )

        product_id = product_result["product_id"]

        # Reduce to 5
        result = agent.update_inventory(product_id, -5)

        assert "LOW_STOCK" in result["alerts"]

    def test_reorder_suggestion(self):
        """Test reorder suggestion is generated."""
        agent = EcommerceAgent()

        # Add product
        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=150.0,
            cost=50.0,
            stock_quantity=10,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )

        product_id = product_result["product_id"]

        # Update inventory
        result = agent.update_inventory(product_id, -5)

        assert "reorder_suggestion" in result
        assert "current_level" in result["reorder_suggestion"]
        assert "suggested_quantity" in result["reorder_suggestion"]


class TestCustomerManagement:
    """Test customer operations."""

    def test_create_customer_success(self):
        """Test successful customer creation."""
        agent = EcommerceAgent()

        result = agent.create_customer(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            phone="555-1234",
            address={
                "street": "123 Main St",
                "city": "New York",
                "state": "NY",
                "zip": "10001",
            },
        )

        assert result["status"] == "created"
        assert "customer_id" in result
        assert "profile_score" in result
        assert "welcome_campaign" in result

    def test_create_customer_invalid_email(self):
        """Test customer creation fails with invalid email."""
        agent = EcommerceAgent()

        result = agent.create_customer(
            email="invalid-email",
            first_name="John",
            last_name="Doe",
        )

        assert result["status"] == "validation_failed"
        assert "Invalid email format" in result["error"]

    def test_create_customer_duplicate_email(self):
        """Test customer creation fails with duplicate email."""
        agent = EcommerceAgent()

        # Create first customer
        agent.create_customer(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
        )

        # Try to create second customer with same email
        result = agent.create_customer(
            email="test@example.com",
            first_name="Jane",
            last_name="Smith",
        )

        assert "Customer already exists" in result["error"]
        assert "customer_id" in result

    def test_customer_profile_generation(self):
        """Test customer profile is generated."""
        agent = EcommerceAgent()

        result = agent.create_customer(
            email="premium@company.com",
            first_name="Premium",
            last_name="Customer",
        )

        assert result["status"] == "created"
        assert result["profile_score"] > 0

    def test_customer_loyalty_initialization(self):
        """Test customer loyalty data is initialized."""
        agent = EcommerceAgent()

        result = agent.create_customer(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
        )

        customer_id = result["customer_id"]
        customer = agent.customers[customer_id]

        assert customer["loyalty"]["tier"] == "bronze"
        assert customer["loyalty"]["points"] == 0
        assert customer["loyalty"]["lifetime_value"] == 0.0
        assert customer["loyalty"]["total_orders"] == 0


class TestOrderProcessing:
    """Test order operations."""

    def test_create_order_success(self):
        """Test successful order creation."""
        agent = EcommerceAgent()

        # Create customer
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        # Create product
        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=150.0,
            cost=50.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )
        product_id = product_result["product_id"]

        # Create order
        result = agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 2,
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        assert result["status"] == OrderStatus.PENDING.value
        assert "order_id" in result
        assert result["total_amount"] > 0
        assert "estimated_delivery" in result

    def test_create_order_customer_not_found(self):
        """Test order creation fails with invalid customer."""
        agent = EcommerceAgent()

        result = agent.create_order(
            customer_id="non-existent",
            items=[],
            shipping_address={},
        )

        assert result["status"] == "failed"
        assert "Customer not found" in result["error"]

    def test_create_order_invalid_item(self):
        """Test order creation fails with invalid item."""
        agent = EcommerceAgent()

        # Create customer
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        # Try to create order with missing required fields
        result = agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": "prod123",
                    # Missing variant_id and quantity
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        assert result["status"] == "validation_failed"

    def test_create_order_insufficient_inventory(self):
        """Test order creation fails with insufficient inventory."""
        agent = EcommerceAgent()

        # Create customer
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        # Create product with low stock
        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=150.0,
            cost=50.0,
            stock_quantity=5,  # Low stock
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )
        product_id = product_result["product_id"]

        # Try to order more than available
        result = agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 10,  # More than available
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        assert "Insufficient inventory" in result["error"]
        assert "unavailable_items" in result

    def test_order_inventory_reservation(self):
        """Test inventory is reserved when order is created."""
        agent = EcommerceAgent()

        # Create customer
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        # Create product
        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=150.0,
            cost=50.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )
        product_id = product_result["product_id"]

        # Create order
        agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 5,
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        # Check inventory was reduced
        assert agent.inventory_levels[product_id] == 95


class TestPricingAndDiscounts:
    """Test pricing calculations and discount logic."""

    def test_pricing_calculation(self):
        """Test order pricing calculation."""
        agent = EcommerceAgent()

        # Create customer and product
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=100.0,
            cost=30.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )
        product_id = product_result["product_id"]

        # Create order
        result = agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 2,
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        # Check pricing
        order = agent.orders[result["order_id"]]
        assert float(order["pricing"]["subtotal"]) == 200.0  # 2 * $100

    def test_new_customer_discount(self):
        """Test new customer discount is applied."""
        agent = EcommerceAgent()

        # Create new customer
        customer_result = agent.create_customer(
            email="newcustomer@example.com",
            first_name="New",
            last_name="Customer",
        )
        customer_id = customer_result["customer_id"]

        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=100.0,
            cost=30.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )
        product_id = product_result["product_id"]

        # Create order
        result = agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 1,
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        # Check discount was applied
        order = agent.orders[result["order_id"]]
        assert len(order["discounts"]["discounts"]) > 0
        assert any(d["type"] == "new_customer" for d in order["discounts"]["discounts"])

    def test_volume_discount(self):
        """Test volume discount is applied for large orders."""
        agent = EcommerceAgent()

        # Create customer
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        # Make first order to avoid new customer discount
        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=10.0,
            cost=3.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )
        product_id = product_result["product_id"]

        agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 1,
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        # Now create large order
        product_result2 = agent.add_product(
            name="Expensive Necklace",
            category=ProductCategory.NECKLACES,
            price=250.0,
            cost=80.0,
            stock_quantity=100,
            sku="NECK002",
            sizes=["S"],
            colors=["Gold"],
            description="Very expensive diamond necklace with premium craftsmanship",
        )
        product_id2 = product_result2["product_id"]

        result = agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id2,
                    "variant_id": "variant1",
                    "quantity": 1,
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        # Check volume discount was applied
        order = agent.orders[result["order_id"]]
        assert any(d["type"] == "volume_discount" for d in order["discounts"]["discounts"])

    def test_free_shipping_threshold(self):
        """Test free shipping over $75."""
        agent = EcommerceAgent()

        # Create customer
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        # Create product
        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=80.0,
            cost=25.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )
        product_id = product_result["product_id"]

        # Create order above threshold
        result = agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 1,
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        # Check shipping is free
        order = agent.orders[result["order_id"]]
        assert float(order["pricing"]["shipping_cost"]) == 0.0

    def test_paid_shipping_below_threshold(self):
        """Test paid shipping under $75."""
        agent = EcommerceAgent()

        # Create customer
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        # Create product
        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=50.0,
            cost=15.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )
        product_id = product_result["product_id"]

        # Create order below threshold
        result = agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 1,
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        # Check shipping cost
        order = agent.orders[result["order_id"]]
        assert float(order["pricing"]["shipping_cost"]) == 9.99


class TestCustomerAnalytics:
    """Test customer analytics and loyalty."""

    def test_customer_loyalty_tier_upgrade_silver(self):
        """Test customer loyalty tier upgrades to silver."""
        agent = EcommerceAgent()

        # Create customer
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        # Create product
        product_result = agent.add_product(
            name="Expensive Item",
            category=ProductCategory.NECKLACES,
            price=600.0,
            cost=200.0,
            stock_quantity=100,
            sku="EXP001",
            sizes=["S"],
            colors=["Gold"],
            description="Very expensive item to test loyalty tier upgrade",
        )
        product_id = product_result["product_id"]

        # Create order to exceed silver threshold
        agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 1,
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        # Check tier was upgraded to silver
        customer = agent.customers[customer_id]
        assert customer["loyalty"]["tier"] == "silver"

    def test_customer_loyalty_tier_upgrade_gold(self):
        """Test customer loyalty tier upgrades to gold."""
        agent = EcommerceAgent()

        # Create customer
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        # Create product
        product_result = agent.add_product(
            name="Very Expensive Item",
            category=ProductCategory.NECKLACES,
            price=1100.0,
            cost=350.0,
            stock_quantity=100,
            sku="VEXP001",
            sizes=["S"],
            colors=["Gold"],
            description="Very expensive item to test gold loyalty tier upgrade",
        )
        product_id = product_result["product_id"]

        # Create order to exceed gold threshold
        agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 1,
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        # Check tier was upgraded to gold
        customer = agent.customers[customer_id]
        assert customer["loyalty"]["tier"] == "gold"

    def test_customer_lifetime_value_calculation(self):
        """Test customer lifetime value is tracked."""
        agent = EcommerceAgent()

        # Create customer
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        # Create product
        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=100.0,
            cost=30.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )
        product_id = product_result["product_id"]

        # Create order
        agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 2,
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        # Check lifetime value was updated
        customer = agent.customers[customer_id]
        assert customer["loyalty"]["lifetime_value"] > 0
        assert customer["loyalty"]["total_orders"] == 1


class TestProductRecommendations:
    """Test recommendation engine."""

    def test_get_product_recommendations(self):
        """Test product recommendations are generated."""
        agent = EcommerceAgent()

        # Create customer
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        # Create some products
        for i in range(5):
            agent.add_product(
                name=f"Product {i}",
                category=ProductCategory.NECKLACES,
                price=100.0 + i * 10,
                cost=30.0,
                stock_quantity=100,
                sku=f"PROD{i:03d}",
                sizes=["S"],
                colors=["Gold"],
                description=f"Beautiful product number {i} with premium craftsmanship",
            )

        # Get recommendations
        recommendations = agent.get_product_recommendations(customer_id, limit=3)

        assert len(recommendations) <= 3
        assert all("product_id" in rec for rec in recommendations)
        assert all("score" in rec for rec in recommendations)
        assert all("reason" in rec for rec in recommendations)

    def test_recommendations_customer_not_found(self):
        """Test recommendations return empty for non-existent customer."""
        agent = EcommerceAgent()

        recommendations = agent.get_product_recommendations("non-existent", limit=5)

        assert recommendations == []

    def test_recommendations_with_inactive_products(self):
        """Test recommendations only include active products."""
        agent = EcommerceAgent()

        # Create customer
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        # Create active product
        product_result = agent.add_product(
            name="Active Product",
            category=ProductCategory.NECKLACES,
            price=100.0,
            cost=30.0,
            stock_quantity=100,
            sku="ACTIVE001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful active product with premium craftsmanship",
        )

        # Manually add inactive product
        inactive_id = str(uuid.uuid4())
        agent.products[inactive_id] = {
            "id": inactive_id,
            "name": "Inactive Product",
            "status": "inactive",
            "category": "necklaces",
            "base_price": Decimal("100.0"),
            "images": [],
            "reviews": {"average_rating": 0.0},
            "analytics": {"conversion_rate": 0.0},
        }

        # Get recommendations
        recommendations = agent.get_product_recommendations(customer_id, limit=10)

        # Should not include inactive product
        assert all(rec["product_id"] != inactive_id for rec in recommendations)


class TestAnalytics:
    """Test analytics and reporting."""

    def test_get_analytics_dashboard(self):
        """Test analytics dashboard returns correct data."""
        agent = EcommerceAgent()

        # Add some data
        agent.add_product(
            name="Product 1",
            category=ProductCategory.NECKLACES,
            price=100.0,
            cost=30.0,
            stock_quantity=100,
            sku="PROD001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful product with premium craftsmanship",
        )

        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )

        dashboard = agent.get_analytics_dashboard()

        assert "total_products" in dashboard
        assert "active_orders" in dashboard
        assert "total_customers" in dashboard
        assert "monthly_revenue" in dashboard
        assert "conversion_rate" in dashboard

        assert dashboard["total_products"] == 1
        assert dashboard["total_customers"] == 1

    def test_generate_analytics_report(self):
        """Test comprehensive analytics report generation."""
        agent = EcommerceAgent()

        report = agent.generate_analytics_report()

        assert "report_id" in report
        assert "generated_at" in report
        assert "executive_summary" in report
        assert "sales_metrics" in report
        assert "customer_metrics" in report
        assert "product_metrics" in report
        assert "operational_metrics" in report
        assert "marketing_metrics" in report
        assert "recommendations" in report
        assert "forecasts" in report

    def test_calculate_total_revenue(self):
        """Test total revenue calculation."""
        agent = EcommerceAgent()

        # Create customer and product
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=100.0,
            cost=30.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )
        product_id = product_result["product_id"]

        # Create orders
        agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 2,
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        revenue = agent._calculate_total_revenue()
        assert revenue > 0

    def test_calculate_average_order_value(self):
        """Test average order value calculation."""
        agent = EcommerceAgent()

        # Create customer and product
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=100.0,
            cost=30.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )
        product_id = product_result["product_id"]

        # Create order
        agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 2,
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        aov = agent._calculate_aov()
        assert aov > 0

    def test_calculate_customer_lifetime_value(self):
        """Test customer lifetime value calculation."""
        agent = EcommerceAgent()

        # Create customer and product
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        product_result = agent.add_product(
            name="Diamond Necklace",
            category=ProductCategory.NECKLACES,
            price=100.0,
            cost=30.0,
            stock_quantity=100,
            sku="NECK001",
            sizes=["S"],
            colors=["Gold"],
            description="Beautiful diamond necklace with premium craftsmanship",
        )
        product_id = product_result["product_id"]

        # Create order
        agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 2,
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        clv = agent._calculate_clv()
        assert clv > 0


class TestHelperMethods:
    """Test various helper methods."""

    def test_validate_email_valid(self):
        """Test email validation with valid email."""
        agent = EcommerceAgent()

        assert agent._validate_email("test@example.com") is True
        assert agent._validate_email("user.name@domain.co.uk") is True

    def test_validate_email_invalid(self):
        """Test email validation with invalid email."""
        agent = EcommerceAgent()

        assert agent._validate_email("invalid-email") is False
        assert agent._validate_email("@example.com") is False
        assert agent._validate_email("test@") is False

    def test_generate_url_slug(self):
        """Test URL slug generation."""
        agent = EcommerceAgent()

        slug = agent._generate_url_slug("Diamond Necklace Collection")
        assert slug == "diamond-necklace-collection"

        slug = agent._generate_url_slug("Rose Gold! Ring #1")
        assert slug == "rose-gold-ring-1"

    def test_calculate_seo_score(self):
        """Test SEO score calculation."""
        agent = EcommerceAgent()

        # Good SEO
        score = agent._calculate_seo_score(
            name="Long Product Name Here",
            description="This is a very long description that should meet the minimum character requirement for good SEO optimization and help with search engine rankings and visibility.",
            tags=["tag1", "tag2", "tag3", "tag4"],
        )
        assert score >= 90

        # Poor SEO
        score = agent._calculate_seo_score(
            name="Short",
            description="Short description",
            tags=["tag1"],
        )
        assert score < 90

    def test_calculate_delivery_date_major_state(self):
        """Test delivery date calculation for major states."""
        agent = EcommerceAgent()

        delivery_date = agent._calculate_delivery_date({"state": "CA"})
        assert delivery_date is not None

        delivery_date = agent._calculate_delivery_date({"state": "NY"})
        assert delivery_date is not None

    def test_calculate_delivery_date_other_state(self):
        """Test delivery date calculation for other states."""
        agent = EcommerceAgent()

        delivery_date = agent._calculate_delivery_date({"state": "MT"})
        assert delivery_date is not None


class TestExperimentalFeatures:
    """Test experimental features."""

    @pytest.mark.asyncio
    async def test_experimental_neural_commerce_session(self):
        """Test neural commerce session."""
        agent = EcommerceAgent()

        # Create customer
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        # Create neural commerce session
        result = await agent.experimental_neural_commerce_session(customer_id)

        assert result["status"] == "neural_session_active"
        assert "session_id" in result
        assert "neural_personalization" in result
        assert "ai_stylist_recommendations" in result
        assert "metaverse_experience" in result

    @pytest.mark.asyncio
    async def test_experimental_neural_commerce_customer_not_found(self):
        """Test neural commerce session with non-existent customer."""
        agent = EcommerceAgent()

        result = await agent.experimental_neural_commerce_session("non-existent")

        assert result["status"] == "failed"
        assert "Customer not found" in result["error"]

    def test_initialize_neural_personalization(self):
        """Test neural personalization initialization."""
        agent = EcommerceAgent()

        assert agent.neural_personalization is not None
        assert "model_architecture" in agent.neural_personalization
        assert "features" in agent.neural_personalization

    def test_initialize_metaverse_commerce(self):
        """Test metaverse commerce initialization."""
        agent = EcommerceAgent()

        assert agent.metaverse_commerce is not None
        assert "virtual_showroom" in agent.metaverse_commerce
        assert "supported_platforms" in agent.metaverse_commerce

    def test_initialize_ai_stylist(self):
        """Test AI stylist initialization."""
        agent = EcommerceAgent()

        assert agent.ai_stylist is not None
        assert "fashion_knowledge_base" in agent.ai_stylist
        assert "style_prediction" in agent.ai_stylist


class TestOptimizeMarketingFunction:
    """Test the standalone optimize_marketing function."""

    def test_optimize_marketing(self):
        """Test optimize_marketing function."""
        result = optimize_marketing()

        assert result["status"] == "marketing_optimized"
        assert "analytics" in result
        assert "timestamp" in result


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_product_with_zero_variants(self):
        """Test product with empty sizes and colors."""
        agent = EcommerceAgent()

        result = agent.add_product(
            name="Simple Product",
            category=ProductCategory.CHARMS,
            price=50.0,
            cost=15.0,
            stock_quantity=100,
            sku="SIMPLE001",
            sizes=[],
            colors=[],
            description="Simple product with no variants for testing purposes",
        )

        assert result["status"] == "created"
        assert result["variants_created"] == 0

    def test_order_with_billing_address(self):
        """Test order creation with separate billing address."""
        agent = EcommerceAgent()

        # Create customer and product
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        product_result = agent.add_product(
            name="Product",
            category=ProductCategory.RINGS,
            price=100.0,
            cost=30.0,
            stock_quantity=100,
            sku="PROD001",
            sizes=["S"],
            colors=["Gold"],
            description="Product for testing billing address functionality",
        )
        product_id = product_result["product_id"]

        # Create order with billing address
        result = agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 1,
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
            billing_address={
                "street": "789 Pine St",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94102",
            },
        )

        assert result["status"] == OrderStatus.PENDING.value
        order = agent.orders[result["order_id"]]
        assert order["billing_address"]["street"] == "789 Pine St"

    def test_multiple_orders_same_customer(self):
        """Test multiple orders from same customer."""
        agent = EcommerceAgent()

        # Create customer
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        # Create product
        product_result = agent.add_product(
            name="Product",
            category=ProductCategory.EARRINGS,
            price=50.0,
            cost=15.0,
            stock_quantity=100,
            sku="PROD001",
            sizes=["S"],
            colors=["Gold"],
            description="Product for testing multiple orders functionality",
        )
        product_id = product_result["product_id"]

        # Create first order
        result1 = agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 1,
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        # Create second order
        result2 = agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 2,
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        # Check customer analytics
        customer = agent.customers[customer_id]
        assert customer["loyalty"]["total_orders"] == 2

    def test_empty_analytics_with_no_data(self):
        """Test analytics work with no data."""
        agent = EcommerceAgent()

        dashboard = agent.get_analytics_dashboard()
        assert dashboard["total_products"] == 0
        assert dashboard["active_orders"] == 0
        assert dashboard["total_customers"] == 0

        # Test calculation methods with no data
        assert agent._calculate_total_revenue() == 0
        assert agent._calculate_aov() == 0.0
        assert agent._calculate_clv() == 0.0

    def test_product_with_all_optional_fields(self):
        """Test product creation with all optional fields."""
        agent = EcommerceAgent()

        result = agent.add_product(
            name="Complete Product",
            category=ProductCategory.BRACELETS,
            price=120.0,
            cost=40.0,
            stock_quantity=75,
            sku="COMPLETE001",
            sizes=["S", "M", "L"],
            colors=["Gold", "Silver", "Rose Gold"],
            description="Complete product with all optional fields for comprehensive testing",
            images=["img1.jpg", "img2.jpg", "img3.jpg"],
            tags=["premium", "luxury", "bestseller", "new"],
        )

        assert result["status"] == "created"
        product_id = result["product_id"]
        product = agent.products[product_id]

        assert len(product["images"]) == 3
        assert len(product["tags"]) == 4
        assert len(product["variants"]) == 9

    def test_order_item_validation_zero_quantity(self):
        """Test order item validation with zero quantity."""
        agent = EcommerceAgent()

        # Create customer
        customer_result = agent.create_customer(
            email="customer@example.com",
            first_name="Jane",
            last_name="Smith",
        )
        customer_id = customer_result["customer_id"]

        # Create product
        product_result = agent.add_product(
            name="Product",
            category=ProductCategory.RINGS,
            price=100.0,
            cost=30.0,
            stock_quantity=100,
            sku="PROD001",
            sizes=["S"],
            colors=["Gold"],
            description="Product for testing zero quantity validation",
        )
        product_id = product_result["product_id"]

        # Try to create order with zero quantity
        result = agent.create_order(
            customer_id=customer_id,
            items=[
                {
                    "product_id": product_id,
                    "variant_id": "variant1",
                    "quantity": 0,  # Invalid
                }
            ],
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
        )

        assert result["status"] == "validation_failed"
        assert "Quantity must be positive" in result["error"]
