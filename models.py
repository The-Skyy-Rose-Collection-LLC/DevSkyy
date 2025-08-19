
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class ProductCategoryEnum(str, Enum):
    jewelry = "jewelry"
    accessories = "accessories"
    clothing = "clothing"
    beauty = "beauty"
    home = "home"

class OrderStatusEnum(str, Enum):
    pending = "pending"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"

class PaymentMethodEnum(str, Enum):
    credit_card = "credit_card"
    debit_card = "debit_card"
    paypal = "paypal"
    apple_pay = "apple_pay"
    google_pay = "google_pay"

class PaymentRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Payment amount must be greater than 0")
    currency: str = Field(..., min_length=3, max_length=3, description="3-letter currency code")
    customer_id: str = Field(..., min_length=1, description="Customer ID is required")
    product_id: str = Field(..., min_length=1, description="Product ID is required")
    payment_method: PaymentMethodEnum
    gateway: str = Field(default="stripe", description="Payment gateway")

class ProductRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    category: ProductCategoryEnum
    price: float = Field(..., gt=0, description="Price must be greater than 0")
    cost: float = Field(..., gt=0, description="Cost must be greater than 0")
    stock_quantity: int = Field(..., ge=0, description="Stock quantity cannot be negative")
    sku: str = Field(..., min_length=1, max_length=50, description="SKU is required")
    sizes: List[str] = Field(default=[], description="Available sizes")
    colors: List[str] = Field(default=[], description="Available colors")
    description: str = Field(..., min_length=10, description="Description must be at least 10 characters")
    images: Optional[List[str]] = Field(default=None, description="Product image URLs")
    tags: Optional[List[str]] = Field(default=None, description="Product tags")

    @validator('price')
    def price_must_be_greater_than_cost(cls, v, values):
        if 'cost' in values and v <= values['cost']:
            raise ValueError('Price must be greater than cost')
        return v

class CustomerRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid email address")
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    phone: Optional[str] = Field(default="", max_length=20, description="Phone number")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="Customer preferences")

class AddressModel(BaseModel):
    street: str = Field(..., min_length=5, description="Street address")
    city: str = Field(..., min_length=2, description="City name")
    state: str = Field(..., min_length=2, description="State/Province")
    postal_code: str = Field(..., min_length=3, description="Postal/ZIP code")
    country: str = Field(..., min_length=2, description="Country code")

class OrderItem(BaseModel):
    product_id: str = Field(..., min_length=1, description="Product ID")
    quantity: int = Field(..., gt=0, description="Quantity must be greater than 0")
    size: Optional[str] = Field(default=None, description="Selected size")
    color: Optional[str] = Field(default=None, description="Selected color")

class OrderRequest(BaseModel):
    customer_id: str = Field(..., min_length=1, description="Customer ID")
    items: List[OrderItem] = Field(..., min_items=1, description="Order must contain at least one item")
    shipping_address: AddressModel
    billing_address: Optional[AddressModel] = Field(default=None, description="Billing address")

class ChargebackRequest(BaseModel):
    transaction_id: str = Field(..., min_length=1, description="Transaction ID")
    reason: str = Field(..., min_length=3, description="Chargeback reason")
    amount: Optional[float] = Field(default=None, gt=0, description="Chargeback amount")

class CodeAnalysisRequest(BaseModel):
    code: str = Field(..., min_length=1, description="Code to analyze")
    language: str = Field(..., min_length=1, description="Programming language")

class WebsiteAnalysisRequest(BaseModel):
    website_url: str = Field(..., regex=r'^https?://', description="Valid website URL")
    api_key: Optional[str] = Field(default=None, description="API key if required")
