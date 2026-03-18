"""
Context Manager for Conversational Flow

Handles:
- Reply binding (numeric/short answers to last question)
- Intent persistence across turns
- Conversation state tracking
"""

import re
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class ConversationState:
    """Tracks conversation context for a user session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.last_question: Optional[str] = None
        self.last_intent: Optional[str] = None
        self.waiting_for: Optional[str] = None  # "age", "time_horizon", "amount", etc.
        self.context: Dict[str, Any] = {}
        self.last_updated = datetime.now()
    
    def update(self, question: str = None, intent: str = None, waiting_for: str = None):
        """Update conversation state."""
        if question:
            self.last_question = question
        if intent:
            self.last_intent = intent
        if waiting_for:
            self.waiting_for = waiting_for
        self.last_updated = datetime.now()
    
    def add_context(self, key: str, value: Any):
        """Add information to context."""
        self.context[key] = value
        self.last_updated = datetime.now()
    
    def is_expired(self, timeout_minutes: int = 10) -> bool:
        """Check if conversation state has expired."""
        return datetime.now() - self.last_updated > timedelta(minutes=timeout_minutes)
    
    def clear(self):
        """Clear conversation state."""
        self.last_question = None
        self.last_intent = None
        self.waiting_for = None
        self.context = {}


# In-memory state storage (use Redis/DB for production)
_conversation_states: Dict[str, ConversationState] = {}


def get_or_create_state(session_id: str) -> ConversationState:
    """Get existing state or create new one."""
    if session_id not in _conversation_states:
        _conversation_states[session_id] = ConversationState(session_id)
    
    state = _conversation_states[session_id]
    
    # Clear expired states
    if state.is_expired():
        state.clear()
    
    return state


def is_followup_response(query: str, state: ConversationState) -> bool:
    """
    Detect if query is a follow-up response to last question.
    
    Indicators:
    - Numeric answer (age, amount, years)
    - Short answer (< 10 words)
    - Yes/No answer
    - Has waiting_for context
    """
    if not state.waiting_for:
        return False
    
    query_lower = query.lower().strip()
    word_count = len(query_lower.split())
    
    # Numeric answer
    if re.match(r'^\d+[\s\w]*$', query_lower):  # "30", "5 years", "50000"
        return True
    
    # Very short answer
    if word_count <= 3:
        return True
    
    # Yes/No
    if query_lower in ["yes", "no", "yeah", "nope", "sure"]:
        return True
    
    # Short answer with context
    if word_count <= 10 and state.last_question:
        return True
    
    return False


def bind_response(query: str, state: ConversationState) -> str:
    """
    Bind short/numeric response to last question context.
    
    Examples:
    - "30" + waiting_for="age" → "My age is 30"
    - "5 years" + waiting_for="time_horizon" → "I have 5 years to retirement"
    - "50000" + waiting_for="amount" → "The amount is 50000"
    """
    if not state.waiting_for:
        return query
    
    query_clean = query.strip()
    
    # Extract number if present
    number_match = re.search(r'(\d[\d,]*(?:\.\d+)?)', query_clean)
    number = number_match.group(1) if number_match else query_clean
    
    # Bind based on what we're waiting for
    bindings = {
        "age": f"My age is {number}",
        "time_horizon": f"I have {query_clean} to retirement" if "year" in query_clean.lower() else f"I have {number} years to retirement",
        "amount": f"The amount is {number}",
        "income": f"My monthly income is {number}",
        "savings": f"I can save {number} per month",
        "car_price": f"The car costs {number}",
        "target_amount": f"My target amount is {number}",
    }
    
    bound_query = bindings.get(state.waiting_for, query)
    
    # Store in context
    state.add_context(state.waiting_for, number)
    
    return bound_query


def should_persist_intent(query: str, state: ConversationState) -> bool:
    """
    Determine if we should persist the last intent or classify fresh.
    
    Persist if:
    - Follow-up response detected
    - Query is continuation of same topic
    - No new topic indicators
    """
    if is_followup_response(query, state):
        return True
    
    # Check for topic change indicators
    topic_change_keywords = [
        "instead", "actually", "wait", "no", "different",
        "what about", "how about", "tell me about"
    ]
    
    query_lower = query.lower()
    if any(keyword in query_lower for keyword in topic_change_keywords):
        return False
    
    # If we have active context and query is short, likely continuation
    if state.context and len(query.split()) <= 15:
        return True
    
    return False


def is_new_topic(query: str) -> bool:
    """Check if query indicates a new topic."""
    new_topic_indicators = [
        "what is", "explain", "tell me about", "how does",
        "instead", "actually", "different question"
    ]
    
    query_lower = query.lower()
    return any(indicator in query_lower for indicator in new_topic_indicators)


# Test cases
if __name__ == "__main__":
    print("Context Manager Tests\n")
    
    # Test 1: Follow-up detection
    state = ConversationState("test_session")
    state.update(question="What is your age?", waiting_for="age")
    
    test_queries = ["30", "I am 30", "30 years old", "What is SIP?"]
    for q in test_queries:
        is_followup = is_followup_response(q, state)
        print(f"Query: '{q}' -> Follow-up: {is_followup}")
    
    # Test 2: Reply binding
    print("\nReply Binding Tests:")
    state.waiting_for = "age"
    bound = bind_response("30", state)
    print(f"'30' + waiting_for='age' -> '{bound}'")
    
    state.waiting_for = "time_horizon"
    bound = bind_response("5 years", state)
    print(f"'5 years' + waiting_for='time_horizon' -> '{bound}'")
    
    print(f"\nContext: {state.context}")
