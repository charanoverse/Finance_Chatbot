import textwrap

RISK_TONE_MAP = {
    "low": "conservative",
    "medium": "balanced",
    "high": "growth-oriented"
}

def make_prompt(query, docs, profile, max_docs=3, max_chars=1500):
    """
    Build a personalized prompt for the LLM.
    - query: str
    - docs: list of {content, source, score}
    - profile: dict with fields: age, income_range, risk, goal
    """
    # Truncate docs to avoid token blowup
    selected_docs = docs[:max_docs]
    excerpts = []
    char_count = 0
    for d in selected_docs:
        snippet = d["content"][:400]  # limit each excerpt
        if char_count + len(snippet) > max_chars:
            break
        excerpts.append(f"- {snippet.strip()} [source: {d['source']}]")
        char_count += len(snippet)

    # Profile tone
    tone = RISK_TONE_MAP.get(profile.get("risk", "medium"), "balanced")

    prompt = f"""
You are a financial assistant. Answer the query based on the retrieved documents.

User profile:
- Age: {profile.get("age", "N/A")}
- Income: {profile.get("income_range", "N/A")}
- Risk preference: {profile.get("risk", "N/A")} → tone: {tone}
- Goal: {profile.get("goal", "N/A")}

User query: "{query}"

Relevant information from documents:
{textwrap.indent(chr(10).join(excerpts), "  ")}

Instructions:
1. Provide a short answer (50–150 words) in a {tone} tone.
2. Include at least one inline citation using [source: filename].
3. Add one actionable suggestion as a bullet point.
4. If the documents don’t cover the topic, respond: 
   "The available information does not directly cover your query. Please consult a financial advisor."
5. End with this disclaimer line:
   "Disclaimer: This is general information, not financial advice."
    """
    return textwrap.dedent(prompt).strip()


def make_chat_messages(query, docs, profile):
    """
    Convert into chat messages format (for OpenAI/Anthropic API).
    """
    prompt = make_prompt(query, docs, profile)
    return [
        {"role": "system", "content": "You are a helpful financial assistant."},
        {"role": "user", "content": prompt}
    ]


# --- Quick test ---
if __name__ == "__main__":
    dummy_docs = [
        {"content": "Systematic Investment Plan (SIP) is a method of investing...", "source": "sip_basics.txt", "score": 0.9},
        {"content": "Equity represents ownership in a company...", "source": "equity_basics.txt", "score": 0.8},
    ]
    profile = {"age": 28, "income_range": "6–10 LPA", "risk": "medium", "goal": "retirement"}
    query = "Should I invest in SIPs?"

    print(make_prompt(query, dummy_docs, profile))
