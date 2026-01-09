from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from .llm import shorten_answer, call_llm
from .safety import check_safety
from .retriever import Retriever
from .personalizer import make_chat_messages
from .realtime import RealtimeFetcher
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson import ObjectId
import datetime

app = FastAPI(title="Personalized Finance Chatbot")

# -----------------------------
# Load modules
# -----------------------------
retriever = Retriever(index_dir="C:/Users/Admin/Desktop/Finance_bot/index")
fetcher = RealtimeFetcher()

# -----------------------------
# MongoDB Setup
# -----------------------------
client = MongoClient("mongodb://localhost:27017")
db = client["finance_chatbot"]
goals_collection = db["goals"]

# -----------------------------
# Request / Response Models
# -----------------------------
class ChatRequest(BaseModel):
    query: str
    profile: dict

class ChatResponse(BaseModel):
    answer: str
    sources: list
    profile_used: dict
    blocked: bool = False

class GoalRequest(BaseModel):
    user: str
    goal_name: str
    target_amount: float
    duration_months: int
    salary: float

class SaveRequest(BaseModel):
    user: str
    goal_id: str
    amount_saved: float


# -----------------------------
# Simple rule-based routing to realtime fetcher
# -----------------------------
def try_realtime(query: str):
    """Detect if query requires realtime info and fetch it."""
    q_lower = query.lower()

    # -----------------------------
    # Stocks
    # -----------------------------
    if "stock" in q_lower or "share" in q_lower or any(sym in q_lower for sym in ["nse", "bse", ".ns", ".bo"]):
        ticker_map = {
            "sbi": "SBIN",
            "reliance": "RELIANCE",
            "tcs": "TCS",
            "infosys": "INFY",
            "hdfc": "HDFCBANK",
            "icici": "ICICIBANK",
            "axis": "AXISBANK",
            "kotak": "KOTAKBANK",
            "idfc": "IDFCFIRSTB",
            "indigo": "INDIGO",
            "tata motors": "TATAMOTORS",
            "tata steel": "TATASTEEL",
            "wipro": "WIPRO",
            "zomato":"ETERNAL",
            "bharat electronics ltd": "BEL",
            "itc ltd": "ITC",
            "reliance industries": "RELIANCE",
            "reliance industries ltd": "RELIANCE",
            "reliance industries limited": "RELIANCE",
        }

        ticker = None
        for name in sorted(ticker_map.keys(), key=lambda x: -len(x)):
            if name in q_lower:
                ticker = ticker_map[name]
                break

        for token in q_lower.replace(",", " ").split():
            tok = token.strip().upper()
            if len(tok) >= 2 and tok.isalnum() and tok in set(ticker_map.values()):
                ticker = tok
                break

        if ticker:
            return [fetcher.fetch_stock_price(ticker)]

    # -----------------------------
    # Fixed Deposits
    # -----------------------------
    if "fd" in q_lower or "fixed deposit" in q_lower:
        banks = []
        for bank in ["sbi", "hdfc", "axis", "icici", "kotak", "idfc"]:
            if bank in q_lower:
                banks.append(bank)
        if banks:
            return fetcher.fetch_fd_rates(tuple(banks))

    # -----------------------------
    # Mutual Funds
    # -----------------------------
        # -----------------------------
    # Mutual Funds
    # -----------------------------
        # -----------------------------
    # Mutual Funds
    # -----------------------------
    if "mutual fund" in q_lower or "nav" in q_lower:
        # Try to detect scheme code (numeric)
        tokens = q_lower.replace("?", "").replace(",", "").split()
        scheme_identifier = None

        for tok in tokens:
            if tok.isdigit():  # e.g., "120503"
                scheme_identifier = tok
                break

        # If no scheme code, use the whole query as scheme name
        if not scheme_identifier:
            # strip extra words like "what", "is", etc.
            # just pass query as-is for partial name matching
            scheme_identifier = query  

        return [fetcher.fetch_mf_nav(scheme_identifier)]



# -----------------------------
# Chat Endpoint
# -----------------------------
@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    query = request.query
    profile = request.profile

    # 1. Safety check
    safe, msg = check_safety(query)
    if not safe:
        return ChatResponse(
            answer=msg, sources=[], profile_used=profile, blocked=True
        )

    # 2. Realtime fetch
    realtime_data = try_realtime(query)
    if realtime_data:
        return ChatResponse(
            answer=f"Here’s the latest data I found: {realtime_data}",
            sources=["realtime_api"],
            profile_used=profile,
        )

    # 3. Knowledge base retrieval
    docs = retriever.retrieve(query, top_k=3)

    # 4. Personalized prompt
    messages = make_chat_messages(query, docs, profile)

    # 5. Call LLM with KB context
    answer = call_llm(messages)
    answer = shorten_answer(answer, max_sentences=3)
    # 6. Detect fallback/irrelevant answers → retry directly with Gemini
    FALLBACK_PATTERNS = [
        "does not directly cover your query",
        "please consult a financial advisor",
        "information not available",
    ]

    if any(pat.lower() in answer.lower() for pat in FALLBACK_PATTERNS):
        # Retry with direct Gemini call, no KB context
        direct_messages = [
            {"role": "system", "content": "You are a helpful financial assistant."},
            {"role": "user", "content": query},
        ]
        answer = call_llm(direct_messages)
        sources = ["gemini_fallback"]
    else:
        sources = [doc["source"] for doc in docs]

    return ChatResponse(answer=answer, sources=sources, profile_used=profile)

## -----------------------------
# Create Goal
# -----------------------------
@app.post("/goal")
def create_goal(goal: GoalRequest):
    monthly_required = goal.target_amount / goal.duration_months

    goal_doc = {
        "user": goal.user,
        "goal_name": goal.goal_name,
        "target_amount": goal.target_amount,
        "duration_months": goal.duration_months,
        "salary": goal.salary,
        "monthly_required": monthly_required,
        "saved_amount": 0.0,
        "savings_history": [],
        "created_at": datetime.datetime.utcnow(),
    }

    res = goals_collection.insert_one(goal_doc)
    goal_doc["_id"] = str(res.inserted_id)

    return {"message": "Goal created successfully", "goal": goal_doc}

# -----------------------------
# Save Progress
# -----------------------------
@app.post("/goal/save")
def save_progress(data: SaveRequest):
    goal = goals_collection.find_one(
        {"_id": ObjectId(data.goal_id), "user": data.user}
    )

    if not goal:
        return {"error": "Goal not found"}

    new_saved = goal["saved_amount"] + data.amount_saved

    goals_collection.update_one(
        {"_id": ObjectId(data.goal_id)},
        {
            "$set": {"saved_amount": new_saved},
            "$push": {
                "savings_history": {
                    "amount": data.amount_saved,
                    "date": datetime.datetime.utcnow(),
                }
            },
        },
    )

    progress = (new_saved / goal["target_amount"]) * 100

    return {
        "message": f"Progress updated: {progress:.2f}%",
        "saved_amount": new_saved,
        "progress": progress,
    }

# -----------------------------
# Get All Goals for User
# -----------------------------
@app.get("/goal/{user}")
def get_goals(user: str):
    goals = list(goals_collection.find({"user": user}))
    for g in goals:
        g["_id"] = str(g["_id"])
    return goals

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)