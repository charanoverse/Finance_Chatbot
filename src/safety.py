import re

# Define keyword lists
BANNED_PATTERNS = [
    r"get[- ]?rich[- ]?quick",
    r"guaranteed returns?",
    r"double (your|the) money",
    r"illegal",
    r"tax evasion",
    r"scam",
]

SENSITIVE_PATTERNS = [
    r"\btax\b",
    r"\blegal\b",
    r"\binsurance claim\b",
]

DISCLAIMER = "This is educational advice, not financial advice. Please consult a certified advisor."
def check_safety(query: str):
    """
    Check query for compliance & safety.
    Returns: (safe: bool, message: str|None)
    - safe=False if query is blocked or needs redirect
    - safe=True if query can continue normally
    """
    q_lower = query.lower()

    # Rule 1: Hard block
    for pat in BANNED_PATTERNS:
        if re.search(pat, q_lower):
            return False, (
                "Your request cannot be processed because it promotes unsafe or misleading "
                f"financial practices. {DISCLAIMER}"
            )

    # Rule 2: Sensitive (flag but allow fallback response)
    for pat in SENSITIVE_PATTERNS:
        if re.search(pat, q_lower):
            return False, (
                f"Your query involves sensitive {pat.strip('\\\\b')} topics. "
                f"Please seek certified advice. {DISCLAIMER}"
            )

    # Rule 3: Default safe
    return True, None


# --- Quick test ---
if __name__ == "__main__":
    test_queries = [
        "Tell me a get rich quick scheme",
        "How to do tax saving legally?",
        "What is SIP?",
    ]

    for q in test_queries:
        safe, msg = check_safety(q)
        print(f"Query: {q}\nSafe? {safe}\nMessage: {msg}\n{'-'*50}")
