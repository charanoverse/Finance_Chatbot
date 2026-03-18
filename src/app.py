from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from .llm import shorten_answer, call_llm
from .safety import check_safety
from .retriever import Retriever
from .personalizer import make_chat_messages
from .realtime import RealtimeFetcher
from .profiling import calculate_risk_profile
from .intent_classifier import classify_intent, get_allowed_docs
from .calculator import calculate
from .context_manager import get_or_create_state, is_followup_response, bind_response, should_persist_intent
from .question_detector import detect_question_type, is_asking_question
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
    profile: Optional[dict] = {}  # Make profile optional
    session_id: Optional[str] = "default"  # Session ID for context tracking

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
    session_id = request.session_id
    
    # Get conversation state
    state = get_or_create_state(session_id)

    # 1. Safety check
    safe, msg = check_safety(query)
    if not safe:
        return ChatResponse(
            answer=msg, sources=[], profile_used=profile, blocked=True
        )
    
    # 1.5 Reply binding - bind short/numeric responses to context
    original_query = query
    if is_followup_response(query, state):
        query = bind_response(query, state)
        # Clear waiting_for after binding
        state.waiting_for = None

    # 2. Calculation check (before RAG)
    calc_result = calculate(query)
    if calc_result and "error" not in calc_result:
        # Return calculated result with explanation from LLM
        calc_explanation = calc_result.get("explanation", "")
        calc_math = calc_result.get("calculation", "")
        
        # Ask LLM to explain the result in context
        messages = [
            {"role": "system", "content": "You are a financial assistant. Explain the calculation result to the user."},
            {"role": "user", "content": f"User asked: {query}\n\nCalculation: {calc_math}\n\nExplain this result briefly and provide any relevant financial advice."}
        ]
        answer = call_llm(messages)
        
        return ChatResponse(
            answer=f"{calc_math}\n\n{answer}",
            sources=["code_calculation"],
            profile_used=profile
        )
    
    # 3. Realtime fetch
    realtime_data = try_realtime(query)
    if realtime_data:
        return ChatResponse(
            answer=f"Here’s the latest data I found: {realtime_data}",
            sources=["realtime_api"],
            profile_used=profile,
        )

    # 2.5 Compute Risk Profile (ONLY if profile data exists and is needed)
    # Profile is now optional and silent - only used internally if provided
    if profile:
        age = int(profile.get("age", 0))
        income = float(profile.get("income", 0))
        savings = float(profile.get("savings", 0))
        risk_willingness = profile.get("risk", "medium")
        
        # Only compute if we have meaningful data
        if age > 0 or income > 0:
            computed_profile = calculate_risk_profile(age, income, savings, risk_willingness)
            profile.update(computed_profile)
    else:
        profile = {}  # Empty profile for generic queries
    
    
    # 4. Intent classification with persistence
    # Persist intent if this is a follow-up in same conversation
    if should_persist_intent(original_query, state) and state.last_intent:
        intent = state.last_intent
    else:
        intent = classify_intent(query)
        state.update(intent=intent)
    
    # RAG LOGIC CHECK (Issue 2)
    from .intent_classifier import requires_rag
    
    if not requires_rag(query, intent):
        docs = [] # Skip RAG for simple definitions/small talk
        sources = ["internal_knowledge"]
    else:
        allowed_docs = get_allowed_docs(intent)
        
        # Issue 1: Conditionally add emergency fund
        if "emergency" in query.lower() or "risk" in query.lower() or "safe" in query.lower():
            if "emergency_fund.txt" not in allowed_docs:
                allowed_docs.append("emergency_fund.txt")

        docs = retriever.retrieve(query, top_k=3, allowed_docs=allowed_docs)
        sources = [doc["source"] for doc in docs]

    # 4. Personalized prompt
    messages = make_chat_messages(query, docs, profile, context=state.context)

    # 5. Call LLM with KB context
    answer = call_llm(messages)
    answer = shorten_answer(answer, max_sentences=3)
    
    # 6. Detect fallback/irrelevant answers → retry directly with Gemini
    # Issue 4: Disable generic fallback during active planning flows
    FALLBACK_PATTERNS = [
        "does not directly cover your query",
        "please consult a financial advisor",
        "information not available",
    ]

    # Only allow fallback if intent is education (generic queries)
    if intent == "education" and any(pat.lower() in answer.lower() for pat in FALLBACK_PATTERNS):
        # Retry with direct Gemini call, no KB context
        direct_messages = [
            {"role": "system", "content": "You are a helpful financial assistant."},
            {"role": "user", "content": query},
        ]
        answer = call_llm(direct_messages)
        sources = ["gemini_fallback"]
    
    # If sources wasn't set by fallback logic (and not set by skipping RAG)
    if "sources" not in locals():
         sources = [doc["source"] for doc in docs]
    
    # 6. Update conversation state if bot asked a question
    if is_asking_question(answer):
        waiting_for = detect_question_type(answer)
        # Fix Issue 3: If question detected but type unknown, still verify it's valid
        if not waiting_for:
            # Fallback for intent persistence even if type extraction failed
            waiting_for = "details"
            
        state.update(question=answer, waiting_for=waiting_for)

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