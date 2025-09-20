import os
import google.generativeai as genai

# -----------------------------
# CONFIG
# -----------------------------
DEFAULT_MODEL = "gemini-2.5-flash"  # or "gemini-pro" depending on your access
FALLBACK_RESPONSE = "I'm sorry, but I couldn't process your request at this time."

# Load your API key from environment variable or replace with your actual key
genai.configure(api_key="Replace_with_api_key")

# -----------------------------
# LLM WRAPPER
# -----------------------------
def call_llm(messages: list, model: str = DEFAULT_MODEL) -> str:
    try:
        model_instance = genai.GenerativeModel(model)

        # ✅ Crispness instruction
        crisp_instruction = (
            "You are a helpful financial assistant. "
            "Always answer in a short, crisp, and simple way (max 3 sentences). "
            "Avoid long explanations, keep it clear and to the point."
        )

        # If system message exists, append instruction
        if messages and messages[0]["role"] == "system":
            messages[0]["content"] += " " + crisp_instruction
        else:
            messages.insert(0, {"role": "system", "content": crisp_instruction})

        # Convert structured messages into prompt
        prompt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
        response = model_instance.generate_content(prompt)

        return response.text.strip()
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
    {"role": "system", "content": "You are a financial assistant. Always answer in a short, simple, and crisp way (2–4 sentences max)."},
    {"role": "user", "content": "What is a Systematic Investment Plan (SIP)?"}
]


    reply = call_llm(test_messages)
    print("Assistant's reply:\n", reply)
