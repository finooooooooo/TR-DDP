from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
import json
import os

from . import models, database, schemas, crud

# Create Tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Mount Static & Templates
if not os.path.exists("app/static"):
    os.makedirs("app/static")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Seeding Data on Startup
@app.on_event("startup")
def startup_event():
    db = database.SessionLocal()
    if db.query(models.Product).count() == 0:
        # Seed Data
        items = [
            # Coffee
            {"name": "Blueberry Coffee", "price": 25000, "category": "Coffee", "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=200"},
            {"name": "V60", "price": 30000, "category": "Coffee", "image_url": "https://images.unsplash.com/photo-1497935586351-b67a49e012bf?w=200"},
            {"name": "Espresso", "price": 18000, "category": "Coffee", "image_url": "https://images.unsplash.com/photo-1510591509098-f4fdc6d0ff04?w=200"},
            {"name": "Cappuccino", "price": 28000, "category": "Coffee", "image_url": "https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=200"},
            # Non-Coffee
            {"name": "Matcha Latte", "price": 28000, "category": "Non-Coffee", "image_url": "https://images.unsplash.com/photo-1515825838458-f2a94b20105a?w=200"},
            {"name": "Iced Tea", "price": 15000, "category": "Non-Coffee", "image_url": "https://images.unsplash.com/photo-1497534446932-c925b458314e?w=200"},
            # Snack
            {"name": "Potato Stick", "price": 20000, "category": "Snack", "image_url": "https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?w=200"},
            {"name": "Samosa", "price": 15000, "category": "Snack", "image_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=200"},
            # Foods
            {"name": "Fried Rice", "price": 35000, "category": "Foods", "image_url": "https://images.unsplash.com/photo-1603133872878-684f10842f63?w=200"},
            {"name": "Pasta Carbonara", "price": 45000, "category": "Foods", "image_url": "https://images.unsplash.com/photo-1612874742237-6526221588e3?w=200"},
        ]
        for item in items:
            crud.create_product(db, schemas.ProductCreate(**item))
    db.close()

# API Endpoints

@app.get("/products", response_model=List[schemas.Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = crud.get_products(db, skip=skip, limit=limit)
    return products

@app.post("/orders", response_model=schemas.TransactionSchema)
async def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    transaction = crud.create_transaction(db, order)

    # Broadcast to Kitchen/Bar
    # We send the full transaction details
    # Pydantic to dict
    data = schemas.TransactionSchema.from_orm(transaction).dict()
    # Serialize datetime
    data['created_at'] = data['created_at'].isoformat()

    await manager.broadcast({"type": "NEW_ORDER", "data": data})

    return transaction

@app.get("/transactions", response_model=List[schemas.TransactionSchema])
def read_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_transactions(db, skip=skip, limit=limit)

# Page Routes

@app.get("/")
def get_cashier_ui(request: Request):
    return templates.TemplateResponse("cashier.html", {"request": request})

@app.get("/monitor")
def get_monitor_ui(request: Request):
    return templates.TemplateResponse("monitor.html", {"request": request})

@app.get("/reports")
def get_reports_ui(request: Request):
    return templates.TemplateResponse("reports.html", {"request": request})

# WebSocket Endpoint
@app.websocket("/ws/{client_type}")
async def websocket_endpoint(websocket: WebSocket, client_type: str):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
