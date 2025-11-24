from sqlalchemy.orm import Session
from . import models, schemas
from typing import List

def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()

def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def create_transaction(db: Session, order: schemas.OrderCreate):
    # Calculate total and prepare items
    total = 0.0
    db_items = []

    # 1. Create Transaction Record
    # We commit later after adding items, or we can flush.
    # Actually, we need to look up prices.

    for item in order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if product:
            item_total = product.price * item.quantity
            total += item_total
            db_item = models.TransactionItem(
                product_name=product.name,
                quantity=item.quantity,
                price=product.price,
                category=product.category
            )
            db_items.append(db_item)

    # Add Tax (10%)
    tax = total * 0.10
    final_total = total + tax

    db_transaction = models.Transaction(
        total_amount=final_total,
        payment_method=order.payment_method
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    for db_item in db_items:
        db_item.transaction_id = db_transaction.id
        db.add(db_item)

    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_transactions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Transaction).order_by(models.Transaction.created_at.desc()).offset(skip).limit(limit).all()
