"""
Intent Classifier for Finance Chatbot

Classifies user queries into intents to enable intent-scoped RAG retrieval.
This prevents wrong citations and document leakage (e.g., SIP docs in short-term answers).

Intents:
- education: General finance questions
- short_term_goal: Goals < 3 years
- long_term_investing: Goals >= 3 years
- affordability_planning: Budget/EMI/affordability questions
"""

import re

# Intent keywords and patterns
INTENT_PATTERNS = {
    "short_term_goal": {
        "keywords": [
            "1 year", "2 year", "6 months", "next year", "soon",
            "emergency fund", "car", "vacation", "wedding",
            "short term", "short-term", "liquid", "fd", "fixed deposit", "rd", "recurring deposit"
        ],
        "time_horizon": ["< 3 years", "1-2 years", "6 months", "12 months"]
    },
    
    "long_term_investing": {
        "keywords": [
            "retirement", "wealth", "5 years", "10 years", "long term", "long-term",
            "sip", "systematic investment", "equity", "mutual fund", "stock",
            "portfolio", "asset allocation", "compound", "growth",
            "invest", "investing", "investment"  # Added generic investment keywords
        ],
        "time_horizon": [">= 3 years", "5+ years", "10+ years"]
    },
    
    "affordability_planning": {
        "keywords": [
            "afford", "budget", "emi", "loan", "monthly payment",
            "income", "salary", "expense", "can i buy", "how much can i spend",
            "50-30-20", "budgeting"
        ]
    },
    
    "education": {
        "keywords": [
            "what is", "explain", "define", "meaning", "difference between",
            "how does", "why", "risky", "safe", "better", "vs"
        ]
    }
}


def classify_intent(query: str) -> str:
    """
    Classify user query into one of four intents.
    
    Args:
        query: User's question
        
    Returns:
        Intent string: 'education', 'short_term_goal', 'long_term_investing', 'affordability_planning'
    """
    query_lower = query.lower()
    
    # Extract time horizon if present
    time_match = re.search(r'(\d+)\s*(year|month|yr|mo)', query_lower)
    if time_match:
        value = int(time_match.group(1))
        unit = time_match.group(2)
        
        # Convert to months
        months = value if 'month' in unit or 'mo' in unit else value * 12
        
        if months < 36:  # Less than 3 years
            return "short_term_goal"
        else:
            return "long_term_investing"
    
    # Score each intent based on keyword matches
    scores = {intent: 0 for intent in INTENT_PATTERNS.keys()}
    
    for intent, patterns in INTENT_PATTERNS.items():
        for keyword in patterns["keywords"]:
            if keyword in query_lower:
                scores[intent] += 1
    
    # Return intent with highest score
    max_intent = max(scores, key=scores.get)
    
    # If no clear winner, default to education
    if scores[max_intent] == 0:
        return "education"
    
    return max_intent


def get_allowed_docs(intent: str) -> list:
    """
    Get list of allowed document filenames for a given intent.
    
    Args:
        intent: Intent classification
        
    Returns:
        List of allowed document filenames
    """
    DOC_MAPPING = {
        "short_term_goal": [
            "fds_rds.txt",
            # "emergency_fund.txt",  <-- REMOVED: Only include if explicitly asked
            "debt_instruments.txt",
            "budgeting.txt"
        ],
        
        "long_term_investing": [
            "sip_basics.txt",
            "equity_basics.txt",
            "mutual_funds.txt",
            "retirement_planning.txt",
            "risk_explained.txt"
        ],
        
        "affordability_planning": [
            "budgeting.txt",
            "financial_goals.txt",
            # "emergency_fund.txt" <-- REMOVED
        ],
        
        "education": [
            # All documents allowed for educational queries
            "fds_rds.txt",
            "emergency_fund.txt",
            "debt_instruments.txt",
            "budgeting.txt",
            "sip_basics.txt",
            "equity_basics.txt",
            "mutual_funds.txt",
            "retirement_planning.txt",
            "risk_explained.txt",
            "financial_goals.txt",
            "insurance.txt",
            "tax_basics.txt"
        ]
    }
    
    docs = DOC_MAPPING.get(intent, DOC_MAPPING["education"])
    
    # CONDITIONALLY Add emergency fund if explicitly relevant
    # (This is a hacky way to access the query, but we don't have it here. 
    #  We will move this logic to the caller in app.py or change signature)
    #  Actually, let's keep it simple: the caller (app.py) should append it.
    
    return docs


def requires_rag(query: str, intent: str) -> bool:
    """
    Determine if RAG is actually needed for this query.
    
    Skip RAG if:
    - Simple definition question ("What is X?")
    - Small talk / Greeting
    - Simple confirmation
    """
    query_lower = query.lower().strip()
    
    # 1. Check for simple definitions regardless of intent
    # "What is X", "Define X", "Meaning of X"
    definition_patterns = [
        r"^what is (a |an |the )?[\w\s]+\??$", 
        r"^define [\w\s]+\??$",
        r"^meaning of [\w\s]+\??$"
    ]
    
    if any(re.match(pat, query_lower) for pat in definition_patterns):
        # Even if intent classifier thinks it's short_term_goal (e.g. "what is fd"),
        # it's just a definition. Skip RAG to avoid over-citation (Issue 2).
        return False
            
    # 2. Check for greetings / small talk
    greetings = ["hi", "hello", "hey", "good morning", "good evening", "thanks", "thank you"]
    if query_lower in greetings:
        return False
        
    return True


# Test cases
if __name__ == "__main__":
    test_queries = [
        ("What is a mutual fund?", "education"),
        ("I want to buy a car in 1 year", "short_term_goal"),
        ("How should I plan for retirement?", "long_term_investing"),
        ("Can I afford a 30k EMI on 80k salary?", "affordability_planning"),
        ("Are small caps risky?", "education"),
        ("I need to save for a vacation in 6 months", "short_term_goal"),
        ("Should I start a SIP for 10 years?", "long_term_investing"),
    ]
    
    print("Intent Classification Tests:\n")
    for query, expected in test_queries:
        result = classify_intent(query)
        status = "[PASS]" if result == expected else "[FAIL]"
        print(f"{status} Query: '{query}'")
        print(f"  Expected: {expected}, Got: {result}")
        print(f"  Allowed docs: {get_allowed_docs(result)[:3]}...\n")
