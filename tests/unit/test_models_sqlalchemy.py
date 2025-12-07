"""
Comprehensive Unit Tests for SQLAlchemy Models (models_sqlalchemy.py)
Testing database models, constraints, defaults, and Pydantic validation
Coverage target: ≥90% (129/143 lines)
"""

from datetime import datetime
from pathlib import Path
import sys

from pydantic import ValidationError
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Create Base for testing (synchronous for unit tests)
Base = declarative_base()

# Add the root directory to Python path to import models_sqlalchemy
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Now import models - they will use our test Base
# We need to mock the database import first
sys.modules["database"] = type(sys)("database")
sys.modules["database"].Base = Base

# Import models to test
from models_sqlalchemy import (
    AgentLog,
    BrandAsset,
    Campaign,
    Customer,
    InMemoryStorage,
    Order,
    PaymentRequest,
    Product,
    ProductRequest,
    User,
    memory_storage,
)


@pytest.fixture
def in_memory_db():
    """
    Create an in-memory SQLite database for testing.

    Yields:
        Session: SQLAlchemy session for database operations

    Notes:
        - Creates all tables from Base metadata
        - Automatically cleans up after test completion
        - Fast execution (< 100ms per test)
    """
    # Create in-memory SQLite engine (synchronous for unit tests)
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session factory
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)


class TestUserModel:
    """Test suite for User model"""

    def test_user_creation_with_required_fields(self, in_memory_db):
        """Test User model creation with all required fields"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password_123"
        )
        in_memory_db.add(user)
        in_memory_db.commit()

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.hashed_password == "hashed_password_123"

    def test_user_default_values(self, in_memory_db):
        """Test User model default values for is_active, is_superuser"""
        user = User(
            email="default@example.com",
            username="defaultuser",
            hashed_password="hashed123"
        )
        in_memory_db.add(user)
        in_memory_db.commit()

        assert user.is_active is True
        assert user.is_superuser is False
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_unique_email_constraint(self, in_memory_db):
        """Test User email uniqueness constraint"""
        user1 = User(
            email="duplicate@example.com",
            username="user1",
            hashed_password="hash1"
        )
        in_memory_db.add(user1)
        in_memory_db.commit()

        user2 = User(
            email="duplicate@example.com",
            username="user2",
            hashed_password="hash2"
        )
        in_memory_db.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            in_memory_db.commit()

    def test_user_unique_username_constraint(self, in_memory_db):
        """Test User username uniqueness constraint"""
        user1 = User(
            email="user1@example.com",
            username="duplicate_username",
            hashed_password="hash1"
        )
        in_memory_db.add(user1)
        in_memory_db.commit()

        user2 = User(
            email="user2@example.com",
            username="duplicate_username",
            hashed_password="hash2"
        )
        in_memory_db.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            in_memory_db.commit()

    def test_user_optional_full_name(self, in_memory_db):
        """Test User with optional full_name field"""
        user = User(
            email="optional@example.com",
            username="optionaluser",
            full_name="John Doe",
            hashed_password="hash123"
        )
        in_memory_db.add(user)
        in_memory_db.commit()

        assert user.full_name == "John Doe"

    def test_user_tablename(self):
        """Test User model __tablename__"""
        assert User.__tablename__ == "users"


class TestProductModel:
    """Test suite for Product model"""

    def test_product_creation_with_required_fields(self, in_memory_db):
        """Test Product model creation with required fields"""
        product = Product(
            name="Test Product",
            sku="TEST-SKU-001",
            price=99.99
        )
        in_memory_db.add(product)
        in_memory_db.commit()

        assert product.id is not None
        assert product.name == "Test Product"
        assert product.sku == "TEST-SKU-001"
        assert product.price == 99.99

    def test_product_default_values(self, in_memory_db):
        """Test Product model default values"""
        product = Product(
            name="Default Product",
            sku="DEFAULT-001",
            price=50.0
        )
        in_memory_db.add(product)
        in_memory_db.commit()

        assert product.stock_quantity == 0
        assert product.is_active is True
        assert product.created_at is not None
        assert product.updated_at is not None

    def test_product_json_fields(self, in_memory_db):
        """Test Product model with JSON fields (sizes, colors, images, tags, etc.)"""
        product = Product(
            name="JSON Product",
            sku="JSON-001",
            price=100.0,
            sizes=["S", "M", "L", "XL"],
            colors=["red", "blue", "green"],
            images=["image1.jpg", "image2.jpg"],
            tags=["new", "sale", "featured"],
            seo_data={"title": "Product Title", "description": "SEO description"},
            variants=[{"size": "M", "color": "red", "sku": "JSON-001-M-R"}]
        )
        in_memory_db.add(product)
        in_memory_db.commit()

        assert product.sizes == ["S", "M", "L", "XL"]
        assert product.colors == ["red", "blue", "green"]
        assert product.images == ["image1.jpg", "image2.jpg"]
        assert product.tags == ["new", "sale", "featured"]
        assert product.seo_data["title"] == "Product Title"
        assert len(product.variants) == 1

    def test_product_unique_sku_constraint(self, in_memory_db):
        """Test Product SKU uniqueness constraint"""
        product1 = Product(name="Product 1", sku="DUP-SKU", price=10.0)
        in_memory_db.add(product1)
        in_memory_db.commit()

        product2 = Product(name="Product 2", sku="DUP-SKU", price=20.0)
        in_memory_db.add(product2)

        with pytest.raises(Exception):  # IntegrityError
            in_memory_db.commit()

    def test_product_optional_fields(self, in_memory_db):
        """Test Product with optional fields (description, category, cost)"""
        product = Product(
            name="Complete Product",
            sku="COMPLETE-001",
            price=150.0,
            description="Full product description",
            category="Electronics",
            cost=75.0
        )
        in_memory_db.add(product)
        in_memory_db.commit()

        assert product.description == "Full product description"
        assert product.category == "Electronics"
        assert product.cost == 75.0

    def test_product_tablename(self):
        """Test Product model __tablename__"""
        assert Product.__tablename__ == "products"


class TestCustomerModel:
    """Test suite for Customer model"""

    def test_customer_creation_with_required_fields(self, in_memory_db):
        """Test Customer model creation with required email"""
        customer = Customer(email="customer@example.com")
        in_memory_db.add(customer)
        in_memory_db.commit()

        assert customer.id is not None
        assert customer.email == "customer@example.com"

    def test_customer_default_values(self, in_memory_db):
        """Test Customer model default values"""
        customer = Customer(email="defaults@example.com")
        in_memory_db.add(customer)
        in_memory_db.commit()

        assert customer.lifetime_value == 0.0
        assert customer.total_orders == 0
        assert customer.created_at is not None
        assert customer.updated_at is not None

    def test_customer_with_all_fields(self, in_memory_db):
        """Test Customer with all optional fields"""
        customer = Customer(
            email="full@example.com",
            first_name="John",
            last_name="Doe",
            phone="+1-555-1234",
            address={"street": "123 Main St", "city": "Seattle", "zip": "98101"},
            preferences={"newsletter": True, "sms": False}
        )
        in_memory_db.add(customer)
        in_memory_db.commit()

        assert customer.first_name == "John"
        assert customer.last_name == "Doe"
        assert customer.phone == "+1-555-1234"
        assert customer.address["city"] == "Seattle"
        assert customer.preferences["newsletter"] is True

    def test_customer_unique_email_constraint(self, in_memory_db):
        """Test Customer email uniqueness constraint"""
        customer1 = Customer(email="duplicate@example.com")
        in_memory_db.add(customer1)
        in_memory_db.commit()

        customer2 = Customer(email="duplicate@example.com")
        in_memory_db.add(customer2)

        with pytest.raises(Exception):  # IntegrityError
            in_memory_db.commit()

    def test_customer_tablename(self):
        """Test Customer model __tablename__"""
        assert Customer.__tablename__ == "customers"


class TestOrderModel:
    """Test suite for Order model"""

    def test_order_creation_with_required_fields(self, in_memory_db):
        """Test Order model creation with required fields"""
        order = Order(
            order_number="ORD-001",
            items=[{"product_id": 1, "quantity": 2, "price": 50.0}],
            subtotal=100.0,
            total=110.0
        )
        in_memory_db.add(order)
        in_memory_db.commit()

        assert order.id is not None
        assert order.order_number == "ORD-001"
        assert len(order.items) == 1
        assert order.subtotal == 100.0
        assert order.total == 110.0

    def test_order_default_values(self, in_memory_db):
        """Test Order model default values"""
        order = Order(
            order_number="ORD-002",
            items=[{"product_id": 1, "quantity": 1}],
            subtotal=50.0,
            total=50.0
        )
        in_memory_db.add(order)
        in_memory_db.commit()

        assert order.tax == 0.0
        assert order.shipping == 0.0
        assert order.status == "pending"
        assert order.payment_status == "pending"
        assert order.created_at is not None
        assert order.updated_at is not None

    def test_order_with_all_fields(self, in_memory_db):
        """Test Order with all optional fields"""
        order = Order(
            order_number="ORD-003",
            customer_id=1,
            customer_email="buyer@example.com",
            items=[{"product_id": 1, "quantity": 3, "price": 25.0}],
            subtotal=75.0,
            tax=7.5,
            shipping=5.0,
            total=87.5,
            status="shipped",
            shipping_address={"street": "123 Buyer St", "city": "Portland"},
            billing_address={"street": "456 Bill St", "city": "Portland"},
            payment_method="credit_card",
            payment_status="paid",
            tracking_number="TRACK-123",
            notes="Gift wrap requested"
        )
        in_memory_db.add(order)
        in_memory_db.commit()

        assert order.customer_id == 1
        assert order.customer_email == "buyer@example.com"
        assert order.tax == 7.5
        assert order.shipping == 5.0
        assert order.status == "shipped"
        assert order.payment_status == "paid"
        assert order.tracking_number == "TRACK-123"
        assert order.notes == "Gift wrap requested"

    def test_order_unique_order_number_constraint(self, in_memory_db):
        """Test Order order_number uniqueness constraint"""
        order1 = Order(
            order_number="DUP-ORDER",
            items=[{"item": 1}],
            subtotal=10.0,
            total=10.0
        )
        in_memory_db.add(order1)
        in_memory_db.commit()

        order2 = Order(
            order_number="DUP-ORDER",
            items=[{"item": 2}],
            subtotal=20.0,
            total=20.0
        )
        in_memory_db.add(order2)

        with pytest.raises(Exception):  # IntegrityError
            in_memory_db.commit()

    def test_order_tablename(self):
        """Test Order model __tablename__"""
        assert Order.__tablename__ == "orders"


class TestAgentLogModel:
    """Test suite for AgentLog model"""

    def test_agent_log_creation_with_required_fields(self, in_memory_db):
        """Test AgentLog model creation with required fields"""
        log = AgentLog(
            agent_name="TestAgent",
            action="process_request"
        )
        in_memory_db.add(log)
        in_memory_db.commit()

        assert log.id is not None
        assert log.agent_name == "TestAgent"
        assert log.action == "process_request"

    def test_agent_log_default_status(self, in_memory_db):
        """Test AgentLog model default status value"""
        log = AgentLog(
            agent_name="DefaultAgent",
            action="test_action"
        )
        in_memory_db.add(log)
        in_memory_db.commit()

        assert log.status == "success"
        assert log.created_at is not None

    def test_agent_log_with_all_fields(self, in_memory_db):
        """Test AgentLog with all optional fields"""
        log = AgentLog(
            agent_name="CompleteAgent",
            action="complex_action",
            status="error",
            input_data={"param1": "value1", "param2": 42},
            output_data={"result": "failed", "code": 500},
            error_message="Connection timeout",
            execution_time_ms=1234.56
        )
        in_memory_db.add(log)
        in_memory_db.commit()

        assert log.status == "error"
        assert log.input_data["param1"] == "value1"
        assert log.output_data["code"] == 500
        assert log.error_message == "Connection timeout"
        assert log.execution_time_ms == 1234.56

    def test_agent_log_tablename(self):
        """Test AgentLog model __tablename__"""
        assert AgentLog.__tablename__ == "agent_logs"


class TestBrandAssetModel:
    """Test suite for BrandAsset model"""

    def test_brand_asset_creation_with_required_fields(self, in_memory_db):
        """Test BrandAsset model creation with required fields"""
        asset = BrandAsset(
            asset_type="logo",
            name="Primary Logo",
            data={"url": "logo.png", "format": "PNG"}
        )
        in_memory_db.add(asset)
        in_memory_db.commit()

        assert asset.id is not None
        assert asset.asset_type == "logo"
        assert asset.name == "Primary Logo"
        assert asset.data["url"] == "logo.png"

    def test_brand_asset_default_values(self, in_memory_db):
        """Test BrandAsset model default values"""
        asset = BrandAsset(
            asset_type="color_palette",
            name="Brand Colors",
            data={"primary": "#FF0000", "secondary": "#0000FF"}
        )
        in_memory_db.add(asset)
        in_memory_db.commit()

        assert asset.version == 1
        assert asset.is_active is True
        assert asset.created_at is not None
        assert asset.updated_at is not None

    def test_brand_asset_with_metadata(self, in_memory_db):
        """Test BrandAsset with asset_metadata field"""
        asset = BrandAsset(
            asset_type="voice",
            name="Brand Voice Guidelines",
            data={"tone": "professional", "style": "friendly"},
            asset_metadata={"author": "Marketing Team", "approved": True},
            version=2
        )
        in_memory_db.add(asset)
        in_memory_db.commit()

        assert asset.asset_metadata["author"] == "Marketing Team"
        assert asset.version == 2

    def test_brand_asset_tablename(self):
        """Test BrandAsset model __tablename__"""
        assert BrandAsset.__tablename__ == "brand_assets"


class TestCampaignModel:
    """Test suite for Campaign model"""

    def test_campaign_creation_with_required_fields(self, in_memory_db):
        """Test Campaign model creation with required name"""
        campaign = Campaign(name="Summer Sale 2025")
        in_memory_db.add(campaign)
        in_memory_db.commit()

        assert campaign.id is not None
        assert campaign.name == "Summer Sale 2025"

    def test_campaign_default_values(self, in_memory_db):
        """Test Campaign model default values"""
        campaign = Campaign(name="Default Campaign")
        in_memory_db.add(campaign)
        in_memory_db.commit()

        assert campaign.status == "draft"
        assert campaign.spent == 0.0
        assert campaign.impressions == 0
        assert campaign.clicks == 0
        assert campaign.conversions == 0
        assert campaign.created_at is not None
        assert campaign.updated_at is not None

    def test_campaign_with_all_fields(self, in_memory_db):
        """Test Campaign with all optional fields"""
        start_date = datetime(2025, 6, 1)
        end_date = datetime(2025, 6, 30)

        campaign = Campaign(
            name="Complete Campaign",
            campaign_type="email",
            status="active",
            platform="mailchimp",
            budget=5000.0,
            spent=1234.56,
            impressions=10000,
            clicks=500,
            conversions=25,
            content={"subject": "Sale!", "body": "Check out our deals"},
            targeting={"age_range": "25-45", "interests": ["fashion"]},
            metrics={"ctr": 5.0, "conversion_rate": 5.0},
            start_date=start_date,
            end_date=end_date
        )
        in_memory_db.add(campaign)
        in_memory_db.commit()

        assert campaign.campaign_type == "email"
        assert campaign.platform == "mailchimp"
        assert campaign.budget == 5000.0
        assert campaign.spent == 1234.56
        assert campaign.impressions == 10000
        assert campaign.clicks == 500
        assert campaign.conversions == 25
        assert campaign.content["subject"] == "Sale!"
        assert campaign.targeting["interests"] == ["fashion"]
        assert campaign.metrics["ctr"] == 5.0
        assert campaign.start_date == start_date
        assert campaign.end_date == end_date

    def test_campaign_tablename(self):
        """Test Campaign model __tablename__"""
        assert Campaign.__tablename__ == "campaigns"


class TestInMemoryStorage:
    """Test suite for InMemoryStorage class"""

    def test_in_memory_storage_initialization(self):
        """Test InMemoryStorage initializes with empty dictionaries"""
        storage = InMemoryStorage()

        assert isinstance(storage.products, dict)
        assert isinstance(storage.customers, dict)
        assert isinstance(storage.orders, dict)
        assert isinstance(storage.analytics, dict)
        assert isinstance(storage.campaigns, dict)
        assert isinstance(storage.brand_assets, dict)
        assert len(storage.products) == 0

    def test_in_memory_storage_clear_all(self):
        """Test InMemoryStorage clear_all method"""
        storage = InMemoryStorage()

        # Add some data
        storage.products["prod1"] = {"name": "Product 1"}
        storage.customers["cust1"] = {"email": "customer@example.com"}
        storage.orders["order1"] = {"total": 100.0}
        storage.analytics["metric1"] = {"views": 1000}
        storage.campaigns["camp1"] = {"name": "Campaign 1"}
        storage.brand_assets["asset1"] = {"type": "logo"}

        # Verify data exists
        assert len(storage.products) == 1
        assert len(storage.customers) == 1
        assert len(storage.orders) == 1

        # Clear all
        storage.clear_all()

        # Verify all dictionaries are empty
        assert len(storage.products) == 0
        assert len(storage.customers) == 0
        assert len(storage.orders) == 0
        assert len(storage.analytics) == 0
        assert len(storage.campaigns) == 0
        assert len(storage.brand_assets) == 0

    def test_global_memory_storage_instance(self):
        """Test global memory_storage instance exists"""
        assert memory_storage is not None
        assert isinstance(memory_storage, InMemoryStorage)

    def test_in_memory_storage_data_persistence(self):
        """Test InMemoryStorage data can be added and retrieved"""
        storage = InMemoryStorage()

        # Add product
        storage.products["test_product"] = {
            "name": "Test Product",
            "price": 99.99,
            "sku": "TEST-001"
        }

        # Retrieve and verify
        product = storage.products["test_product"]
        assert product["name"] == "Test Product"
        assert product["price"] == 99.99
        assert product["sku"] == "TEST-001"


class TestPydanticProductRequest:
    """Test suite for ProductRequest Pydantic model"""

    def test_product_request_with_required_fields(self):
        """Test ProductRequest with required fields (name, base_price)"""
        request = ProductRequest(
            name="Valid Product",
            base_price=49.99
        )

        assert request.name == "Valid Product"
        assert request.base_price == 49.99

    def test_product_request_with_all_fields(self):
        """Test ProductRequest with all optional fields"""
        request = ProductRequest(
            name="Complete Product",
            description="Full description",
            base_price=99.99,
            cost=50.0,
            category="Electronics",
            sku="COMP-001",
            stock_quantity=100,
            tags=["new", "featured"],
            images=["image1.jpg", "image2.jpg"]
        )

        assert request.description == "Full description"
        assert request.cost == 50.0
        assert request.category == "Electronics"
        assert request.sku == "COMP-001"
        assert request.stock_quantity == 100
        assert len(request.tags) == 2
        assert len(request.images) == 2

    def test_product_request_default_values(self):
        """Test ProductRequest default values for optional fields"""
        request = ProductRequest(
            name="Minimal Product",
            base_price=25.0
        )

        assert request.description is None
        assert request.cost is None
        assert request.category is None
        assert request.sku is None
        assert request.stock_quantity == 0
        assert request.tags == []
        assert request.images == []

    def test_product_request_name_min_length_validation(self):
        """Test ProductRequest name minimum length validation"""
        with pytest.raises(ValidationError) as exc_info:
            ProductRequest(name="", base_price=10.0)

        errors = exc_info.value.errors()
        assert any("name" in str(error) for error in errors)

    def test_product_request_price_positive_validation(self):
        """Test ProductRequest base_price must be positive"""
        with pytest.raises(ValidationError) as exc_info:
            ProductRequest(name="Invalid Price", base_price=0)

        errors = exc_info.value.errors()
        assert any("base_price" in str(error) for error in errors)

    def test_product_request_negative_price_validation(self):
        """Test ProductRequest base_price cannot be negative"""
        with pytest.raises(ValidationError) as exc_info:
            ProductRequest(name="Negative Price", base_price=-10.0)

        errors = exc_info.value.errors()
        assert any("base_price" in str(error) for error in errors)


class TestPydanticPaymentRequest:
    """Test suite for PaymentRequest Pydantic model"""

    def test_payment_request_with_required_fields(self):
        """Test PaymentRequest with required fields (amount, payment_method)"""
        request = PaymentRequest(
            amount=100.0,
            payment_method="credit_card"
        )

        assert request.amount == 100.0
        assert request.payment_method == "credit_card"
        assert request.currency == "USD"  # Default value

    def test_payment_request_with_all_fields(self):
        """Test PaymentRequest with all optional fields"""
        request = PaymentRequest(
            amount=250.50,
            currency="EUR",
            payment_method="paypal",
            customer_id="cust_123",
            order_id="order_456",
            description="Payment for order 456",
            metadata={"invoice_id": "INV-789", "department": "sales"}
        )

        assert request.amount == 250.50
        assert request.currency == "EUR"
        assert request.customer_id == "cust_123"
        assert request.order_id == "order_456"
        assert request.description == "Payment for order 456"
        assert request.metadata["invoice_id"] == "INV-789"

    def test_payment_request_default_values(self):
        """Test PaymentRequest default values"""
        request = PaymentRequest(
            amount=50.0,
            payment_method="bank_transfer"
        )

        assert request.currency == "USD"
        assert request.customer_id is None
        assert request.order_id is None
        assert request.description is None
        assert request.metadata == {}

    def test_payment_request_amount_positive_validation(self):
        """Test PaymentRequest amount must be positive"""
        with pytest.raises(ValidationError) as exc_info:
            PaymentRequest(amount=0, payment_method="cash")

        errors = exc_info.value.errors()
        assert any("amount" in str(error) for error in errors)

    def test_payment_request_negative_amount_validation(self):
        """Test PaymentRequest amount cannot be negative"""
        with pytest.raises(ValidationError) as exc_info:
            PaymentRequest(amount=-50.0, payment_method="credit_card")

        errors = exc_info.value.errors()
        assert any("amount" in str(error) for error in errors)


class TestModelTableNames:
    """Test suite for verifying all model __tablename__ attributes"""

    def test_all_tablenames_defined(self):
        """Test all SQLAlchemy models have __tablename__ defined"""
        models = [User, Product, Customer, Order, AgentLog, BrandAsset, Campaign]

        for model in models:
            assert hasattr(model, "__tablename__")
            assert isinstance(model.__tablename__, str)
            assert len(model.__tablename__) > 0


class TestModelInspection:
    """Test suite for inspecting model columns and constraints"""

    def test_user_columns_exist(self, in_memory_db):
        """Test User model has expected columns"""
        inspector = inspect(in_memory_db.bind)
        columns = [col["name"] for col in inspector.get_columns("users")]

        expected_columns = [
            "id", "email", "username", "full_name", "hashed_password",
            "is_active", "is_superuser", "created_at", "updated_at"
        ]

        for col in expected_columns:
            assert col in columns

    def test_product_columns_exist(self, in_memory_db):
        """Test Product model has expected columns"""
        inspector = inspect(in_memory_db.bind)
        columns = [col["name"] for col in inspector.get_columns("products")]

        expected_columns = [
            "id", "name", "description", "sku", "category", "price", "cost",
            "stock_quantity", "sizes", "colors", "images", "tags", "seo_data",
            "variants", "is_active", "created_at", "updated_at"
        ]

        for col in expected_columns:
            assert col in columns

    def test_customer_columns_exist(self, in_memory_db):
        """Test Customer model has expected columns"""
        inspector = inspect(in_memory_db.bind)
        columns = [col["name"] for col in inspector.get_columns("customers")]

        expected_columns = [
            "id", "email", "first_name", "last_name", "phone", "address",
            "preferences", "lifetime_value", "total_orders", "created_at", "updated_at"
        ]

        for col in expected_columns:
            assert col in columns
