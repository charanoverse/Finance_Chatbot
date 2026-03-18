import os
import google.generativeai as genai
from dotenv import load_dotenv
from src.prompts import SYSTEM_PROMPT

load_dotenv()

# -----------------------------
# CONFIG
# -----------------------------
DEFAULT_MODEL = "gemini-2.5-flash"
FALLBACK_RESPONSE = "I'm sorry, but I couldn't process your request at this time."

# Load your API key from environment variable or replace with your actual key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# -----------------------------
# LLM WRAPPER
# -----------------------------
def call_llm(messages: list, model: str = DEFAULT_MODEL) -> str:
    try:
        model_instance = genai.GenerativeModel(model)

        # If system message exists, append instruction, else insert it
        # We use the detailed SYSTEM_PROMPT now
        if messages and messages[0]["role"] == "system":
            messages[0]["content"] = SYSTEM_PROMPT + "\n\n" + messages[0]["content"]
        else:
            messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

        # Convert structured messages into prompt
        prompt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
        
        response = model_instance.generate_content(prompt)
        response_text = response.text.strip()
        
        # LOGGING (Internal)
        # In a real app, use a proper logger. Printing for now as requested.
        print(f"\n[LLM Response Log] Length: {len(response_text)} chars")
        if "I can calculate" in response_text or "once I know" in response_text:
             print("[LLM Log] Partial/Conditional Answer detected.")
        if "?" in response_text and len(response_text.split()) < 50:
             print("[LLM Log] Asking clarifying question.")

        return response_text
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return FALLBACK_RESPONSE



def shorten_answer(answer: str, max_sentences: int = 3) -> str:
    sentences = answer.split(". ")
    return ". ".join(sentences[:max_sentences]).strip() + "."

# -----------------------------
# TEST RUN
# -----------------------------
if __name__ == "__main__":
    test_messages = [
    {"role": "user", "content": "Can I buy a car next year? Cost is 15L."}
]


    reply = call_llm(test_messages)
    print("Assistant's reply:\n", reply)
