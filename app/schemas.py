from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    price: float
    category: str
    image_url: str

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    class Config:
        from_attributes = True

class OrderItemSchema(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    payment_method: str
    items: List[OrderItemSchema]

class TransactionItemSchema(BaseModel):
    product_name: str
    quantity: int
    price: float
    category: str

    class Config:
        from_attributes = True

class TransactionSchema(BaseModel):
    id: int
    created_at: datetime
    total_amount: float
    payment_method: str
    items: List[TransactionItemSchema] = []

    class Config:
        from_attributes = True
