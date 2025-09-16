from fastapi import FastAPI
from pydantic import BaseModel

from .safety import check_safety
from .retriever import Retriever
from .personalizer import make_chat_messages
from .llm import call_llm
from .realtime import RealtimeFetcher

app = FastAPI(title="Personalized Finance Chatbot")

# -----------------------------
# Load modules
# -----------------------------
retriever = Retriever(index_dir="C:/Users/Admin/Desktop/Finance_bot/index")
fetcher = RealtimeFetcher()  # for real-time data


# -----------------------------
# Request / Response Models
# -----------------------------
class ChatRequest(BaseModel):
    query: str
    profile: dict  # e.g., {"age":28, "income":"6-10 LPA", "risk":"medium", "goal":"retirement"}


class ChatResponse(BaseModel):
    answer: str
    sources: list
    profile_used: dict
    blocked: bool = False


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

    # 5. Call LLM
    answer = call_llm(messages)

    # 6. Sources
    sources = [doc["source"] for doc in docs]

    return ChatResponse(answer=answer, sources=sources, profile_used=profile)
