from fastapi import FastAPI, APIRouter, HTTPException, Cookie, Response, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import json
import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    picture: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str  # "income" or "expense"
    amount: float
    category: str
    description: str
    date: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TransactionCreate(BaseModel):
    type: str
    amount: float
    category: str
    description: str
    date: datetime

class TransactionUpdate(BaseModel):
    type: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None

class DashboardStats(BaseModel):
    total_income: float
    total_expenses: float
    balance: float
    transactions_count: int
    category_breakdown: Dict[str, float]

# Authentication helpers
async def get_current_user(request: Request) -> Optional[User]:
    """Get current user from session token (cookie or header)"""
    session_token = request.cookies.get("session_token") or request.headers.get("authorization", "").replace("Bearer ", "")
    
    if not session_token:
        return None
    
    # Check if session exists and is valid
    session = await db.user_sessions.find_one({
        "session_token": session_token,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not session:
        return None
    
    # Get user
    user = await db.users.find_one({"id": session["user_id"]})
    return User(**user) if user else None

# Authentication routes
@api_router.get("/auth/session-data")
async def get_session_data(request: Request):
    """Process session_id from auth service and return user data"""
    session_id = request.headers.get("X-Session-ID")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session")
            
            user_data = response.json()
            
            # Check if user exists
            existing_user = await db.users.find_one({"email": user_data["email"]})
            
            if not existing_user:
                # Create new user
                new_user = User(
                    email=user_data["email"],
                    name=user_data["name"],
                    picture=user_data["picture"]
                )
                await db.users.insert_one(new_user.dict())
                user = new_user
            else:
                user = User(**existing_user)
            
            # Create session
            session_token = user_data["session_token"]
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            
            user_session = UserSession(
                user_id=user.id,
                session_token=session_token,
                expires_at=expires_at
            )
            
            await db.user_sessions.insert_one(user_session.dict())
            
            return {
                "user": user.dict(),
                "session_token": session_token
            }
            
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Authentication service error")

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user and clear session"""
    session_token = request.cookies.get("session_token") or request.headers.get("authorization", "").replace("Bearer ", "")
    
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie("session_token", path="/", secure=True, samesite="none")
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(request: Request):
    """Get current user information"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# Transaction routes
@api_router.post("/transactions", response_model=Transaction)
async def create_transaction(transaction_data: TransactionCreate, request: Request):
    """Create a new transaction"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    transaction = Transaction(
        user_id=user.id,
        **transaction_data.dict()
    )
    
    await db.transactions.insert_one(transaction.dict())
    return transaction

@api_router.get("/transactions", response_model=List[Transaction])
async def get_transactions(request: Request, category: Optional[str] = None, 
                         start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get user's transactions with filtering"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    query = {"user_id": user.id}
    
    if category:
        query["category"] = category
    
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            date_query["$lte"] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        query["date"] = date_query
    
    transactions = await db.transactions.find(query).sort("date", -1).to_list(1000)
    return [Transaction(**transaction) for transaction in transactions]

@api_router.get("/transactions/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: str, request: Request):
    """Get specific transaction"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    transaction = await db.transactions.find_one({"id": transaction_id, "user_id": user.id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return Transaction(**transaction)

@api_router.put("/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction(transaction_id: str, transaction_data: TransactionUpdate, request: Request):
    """Update a transaction"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if transaction exists and belongs to user
    existing = await db.transactions.find_one({"id": transaction_id, "user_id": user.id})
    if not existing:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update only provided fields
    update_data = {k: v for k, v in transaction_data.dict().items() if v is not None}
    
    if update_data:
        await db.transactions.update_one(
            {"id": transaction_id, "user_id": user.id},
            {"$set": update_data}
        )
    
    # Return updated transaction
    updated_transaction = await db.transactions.find_one({"id": transaction_id, "user_id": user.id})
    return Transaction(**updated_transaction)

@api_router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str, request: Request):
    """Delete a transaction"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = await db.transactions.delete_one({"id": transaction_id, "user_id": user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {"message": "Transaction deleted successfully"}

# Analytics routes
@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(request: Request):
    """Get dashboard statistics"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get all transactions
    transactions = await db.transactions.find({"user_id": user.id}).to_list(1000)
    
    total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
    balance = total_income - total_expenses
    
    # Category breakdown
    category_breakdown = {}
    for transaction in transactions:
        category = transaction["category"]
        if category not in category_breakdown:
            category_breakdown[category] = 0
        category_breakdown[category] += transaction["amount"]
    
    return DashboardStats(
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance,
        transactions_count=len(transactions),
        category_breakdown=category_breakdown
    )

@api_router.get("/analytics/monthly")
async def get_monthly_analytics(request: Request):
    """Get monthly spending analytics"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get last 12 months of data
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=365)
    
    transactions = await db.transactions.find({
        "user_id": user.id,
        "date": {"$gte": start_date, "$lte": end_date}
    }).to_list(1000)
    
    # Group by month
    monthly_data = {}
    for transaction in transactions:
        month_key = transaction["date"].strftime("%Y-%m")
        if month_key not in monthly_data:
            monthly_data[month_key] = {"income": 0, "expenses": 0}
        
        if transaction["type"] == "income":
            monthly_data[month_key]["income"] += transaction["amount"]
        else:
            monthly_data[month_key]["expenses"] += transaction["amount"]
    
    return monthly_data

# Export routes
@api_router.get("/export/csv")
async def export_csv(request: Request):
    """Export transactions as CSV"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    transactions = await db.transactions.find({"user_id": user.id}).sort("date", -1).to_list(1000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Date", "Type", "Category", "Description", "Amount"])
    
    # Write transactions
    for transaction in transactions:
        writer.writerow([
            transaction["date"].strftime("%Y-%m-%d"),
            transaction["type"],
            transaction["category"],
            transaction["description"],
            transaction["amount"]
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"}
    )

@api_router.get("/export/pdf")
async def export_pdf(request: Request):
    """Export transactions as PDF"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    transactions = await db.transactions.find({"user_id": user.id}).sort("date", -1).to_list(1000)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title = Paragraph("Expense Tracker Report", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.25*inch))
    
    # Summary stats
    total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
    balance = total_income - total_expenses
    
    summary_text = f"Total Income: ${total_income:.2f}<br/>Total Expenses: ${total_expenses:.2f}<br/>Balance: ${balance:.2f}"
    summary = Paragraph(summary_text, styles['Normal'])
    elements.append(summary)
    elements.append(Spacer(1, 0.25*inch))
    
    # Transactions table
    table_data = [["Date", "Type", "Category", "Description", "Amount"]]
    
    for transaction in transactions:
        table_data.append([
            transaction["date"].strftime("%Y-%m-%d"),
            transaction["type"].capitalize(),
            transaction["category"],
            transaction["description"],
            f"${transaction['amount']:.2f}"
        ])
    
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=transactions.pdf"}
    )

# Categories endpoint
@api_router.get("/categories")
async def get_categories():
    """Get available categories"""
    return {
        "expense_categories": [
            "Food & Dining",
            "Transportation",
            "Shopping",
            "Entertainment",
            "Bills & Utilities",
            "Healthcare",
            "Education",
            "Travel",
            "Home & Garden",
            "Personal Care",
            "Gifts & Donations",
            "Business",
            "Others"
        ],
        "income_categories": [
            "Salary",
            "Freelance",
            "Investment",
            "Business",
            "Rental",
            "Gifts",
            "Others"
        ]
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()