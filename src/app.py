from fastapi import FastAPI
from pydantic import BaseModel
from .safety import check_safety
from .retriever import Retriever
from .personalizer import make_chat_messages
from .llm import call_llm

app = FastAPI(title="Personalized Finance Chatbot")

# Load your FAISS retriever once
retriever = Retriever(index_dir="C:/Users/Admin/Desktop/Finance_bot/index")

# Request body schema
class ChatRequest(BaseModel):
    query: str
    profile: dict  # e.g., {"age":28, "income":"6-10 LPA", "risk":"medium", "goal":"retirement"}

# Response schema
class ChatResponse(BaseModel):
    answer: str
    sources: list
    profile_used: dict
    blocked: bool = False

# Chat endpoint
@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    query = request.query
    profile = request.profile

    # 1. Safety check
    safe, msg = check_safety(query)
    if not safe:
        return ChatResponse(answer=msg, sources=[], profile_used=profile, blocked=True)

    # 2. Retrieve docs
    docs = retriever.retrieve(query, top_k=3)

    # 3. Build personalized prompt/messages
    messages = make_chat_messages(query, docs, profile)

    # 4. Call LLM
    answer = call_llm(messages)

    # 5. Collect sources from docs
    sources = [doc["source"] for doc in docs]

    return ChatResponse(answer=answer, sources=sources, profile_used=profile)
