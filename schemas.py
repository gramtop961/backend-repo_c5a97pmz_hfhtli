"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

# Core business schemas

class Service(BaseModel):
    name: str = Field(..., description="Service or zone name")
    category: str = Field(..., description="e.g., Oksels, Bikinilijn, Benen, Gezicht, Armen, Full Body")
    code: str = Field(..., description="Unique code for the zone")
    price_single: float = Field(..., ge=0, description="Single session price in EUR")
    price_package_6x: Optional[float] = Field(None, ge=0, description="Price for 6 sessions (optional)")
    duration_min: int = Field(..., ge=5, description="Estimated duration in minutes")

class Package(BaseModel):
    title: str
    description: Optional[str] = None
    code: str
    included_codes: List[str] = Field(..., description="List of service codes included")
    price_single: float = Field(..., ge=0)
    promo_6_plus_2: bool = Field(True, description="Whether 6+2 promo applies")

class Booking(BaseModel):
    type: str = Field(..., description="intake | behandeling")
    name: str
    email: EmailStr
    phone: str
    date: str = Field(..., description="ISO date (YYYY-MM-DD)")
    time: str = Field(..., description="HH:MM")
    selected_codes: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

class Inquiry(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: str
    message: str
    created_at: Optional[datetime] = None

class Special(BaseModel):
    title: str
    description: Optional[str] = None
    code: str
    price: Optional[float] = None
    old_price: Optional[float] = None
    ends_at: Optional[str] = None  # ISO date

class FAQ(BaseModel):
    question: str
    answer: str

# Example schemas kept for reference
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
