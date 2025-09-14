personas = [
    {"age": 22, "income": "low", "risk": "low", "goal": "savings"},         # Student
    {"age": 30, "income": "medium", "risk": "medium", "goal": "investment"}, # Young professional
    {"age": 60, "income": "high", "risk": "low", "goal": "retirement"}      # Retiree
]
queries = [
    "Should I start an SIP?",
    "How should I allocate my first 1L?",
    "Is equity suitable for me?",
    "What is a Fixed Deposit?",
    "How do I save tax legally?",
    "What is an emergency fund?",
    "Are mutual funds safe?",
    "What is the risk in debt instruments?",
    "How much should I save monthly?",
    "Best way to plan retirement?"
]
import pytest
from src.app import chat_endpoint
from pydantic import BaseModel

# Helper functions
def contains_disclaimer(text):
    return "Disclaimer: This is general information" in text

def contains_citation(text):
    return "[source:" in text

# End-to-end test
@pytest.mark.parametrize("persona", personas)
@pytest.mark.parametrize("query", queries)
def test_chat_pipeline(query, persona):
    # Build request object
    request = BaseModel.parse_obj({"query": query, "profile": persona})
    
    # Call the chatbot endpoint directly
    response = chat_endpoint(request)

    # 1️⃣ Basic response exists
    assert "answer" in response.__dict__
    assert "sources" in response.__dict__
    assert "profile_used" in response.__dict__
    assert response.blocked in [True, False]

    # 2️⃣ Check disclaimer is present
    assert contains_disclaimer(response.answer)

    # 3️⃣ Check citations exist if not blocked
    if not response.blocked:
        assert contains_citation(response.answer)
