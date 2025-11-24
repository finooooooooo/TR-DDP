from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    category = Column(String) # Coffee, Non-Coffee, Snack, Foods
    image_url = Column(String)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Float)
    payment_method = Column(String) # Cash, Debit, QRIS

    items = relationship("TransactionItem", back_populates="transaction")

class TransactionItem(Base):
    __tablename__ = "transaction_items"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    product_name = Column(String)
    quantity = Column(Integer)
    price = Column(Float) # Price at time of transaction
    category = Column(String) # Stored to help routing (Kitchen vs Bar)

    transaction = relationship("Transaction", back_populates="items")
