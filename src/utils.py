# src/utils.py
import re

LIVE_PATTERNS = [
    r"\b(current|today|now)\b",
    r"\b(price|quote|rate|rates|interest|nav|FD|fd|SIP|stock|share|index)\b",
    r"\b(SBI|HDFC|ICICI|SBIN|NIFTY|SENSEX|AAPL|TSLA)\b",  # add common tokens
]

def detect_live_need(query: str) -> bool:
    q = query.lower()
    for p in LIVE_PATTERNS:
        if re.search(p, q):
            return True
    return False
