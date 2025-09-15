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
            "idfc": "IDFCFIRSTB"
        }
        ticker = None
        for name, symbol in ticker_map.items():
            if name in q_lower:
                ticker = symbol
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
    if "mutual fund" in q_lower or "nav" in q_lower:
        return [fetcher.fetch_mf_nav("sample_scheme")]  # TODO: detect scheme dynamically

    return None


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
