"""
SQLAlchemy Models for DevSkyy
Database models using SQLAlchemy ORM
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text

from database import Base


class User(Base):
    """User model"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(200))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Product(Base):
    """Product model"""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(String(100), index=True)
    price = Column(Float, nullable=False)
    cost = Column(Float)
    stock_quantity = Column(Integer, default=0)
    sizes = Column(JSON)  # Store as JSON array
    colors = Column(JSON)  # Store as JSON array
    images = Column(JSON)  # Store as JSON array
    tags = Column(JSON)  # Store as JSON array
    seo_data = Column(JSON)  # SEO metadata
    variants = Column(JSON)  # Product variants
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Customer(Base):
    """Customer model"""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(50))
    address = Column(JSON)  # Store full address as JSON
    preferences = Column(JSON)  # Customer preferences
    lifetime_value = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Order(Base):
    """Order model"""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(100), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, index=True)
    customer_email = Column(String(255))
    items = Column(JSON, nullable=False)  # Order items as JSON
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, default=0.0)
    shipping = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    status = Column(String(50), default="pending", index=True)
    shipping_address = Column(JSON)
    billing_address = Column(JSON)
    payment_method = Column(String(50))
    payment_status = Column(String(50), default="pending")
    tracking_number = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentLog(Base):
    """Agent activity log"""

    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100), index=True, nullable=False)
    action = Column(String(100), nullable=False)
    status = Column(String(50), default="success")
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    execution_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class BrandAsset(Base):
    """Brand assets and intelligence data"""

    __tablename__ = "brand_assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_type = Column(String(50), nullable=False)  # logo, color_palette, voice, etc.
    name = Column(String(200), nullable=False)
    data = Column(JSON, nullable=False)  # Flexible JSON storage
    asset_metadata = Column(JSON)  # Renamed from 'metadata' (reserved by SQLAlchemy)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Campaign(Base):
    """Marketing campaign"""

    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    campaign_type = Column(String(50))  # email, social, ads, etc.
    status = Column(String(50), default="draft")
    platform = Column(String(50))  # facebook, instagram, google, etc.
    budget = Column(Float)
    spent = Column(Float, default=0.0)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    content = Column(JSON)  # Campaign content and assets
    targeting = Column(JSON)  # Audience targeting data
    metrics = Column(JSON)  # Performance metrics
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# In-memory cache for backward compatibility with existing code
# Agents can still use dictionaries; we'll persist to DB when needed
class InMemoryStorage:
    """
    In-memory storage that mimics MongoDB behavior.
    Used by agents that expect dictionary-based storage.
    """

    def __init__(self):
        self.products = {}
        self.customers = {}
        self.orders = {}
        self.analytics = {}
        self.campaigns = {}
        self.brand_assets = {}

    def clear_all(self):
        """Clear all in-memory data"""
        self.products.clear()
        self.customers.clear()
        self.orders.clear()
        self.analytics.clear()
        self.campaigns.clear()
        self.brand_assets.clear()


# Global in-memory storage instance
memory_storage = InMemoryStorage()


# ============================================================================
# PYDANTIC REQUEST/RESPONSE MODELS (for FastAPI validation)
# ============================================================================


class ProductRequest(BaseModel):
    """Request model for creating/updating products"""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    base_price: float = Field(..., gt=0)
    cost: float | None = None
    category: str | None = None
    sku: str | None = None
    stock_quantity: int | None = 0
    tags: list[str] | None = []
    images: list[str] | None = []


class PaymentRequest(BaseModel):
    """Request model for processing payments"""

    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    payment_method: str = Field(..., max_length=50)
    customer_id: str | None = None
    order_id: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = {}
