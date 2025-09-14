import os
import google.generativeai as genai

# -----------------------------
# CONFIG
# -----------------------------
DEFAULT_MODEL = "gemini-2.5-flash"  # or "gemini-pro" depending on your access
FALLBACK_RESPONSE = "I'm sorry, but I couldn't process your request at this time."

# Load your API key from environment variable or replace with your actual key
genai.configure(api_key="AIzaSyCkdSw_rqIA90LlOf_nu48je_dM1Tw04jw")

# -----------------------------
# LLM WRAPPER
# -----------------------------
def call_llm(messages: list, model: str = DEFAULT_MODEL) -> str:
    """
    Call Google Gemini API to generate a response.

    Args:
        messages (list): list of dicts: {"role": "system"/"user", "content": str}
        model (str): Gemini model, default "gemini-2.5-flash"

    Returns:
        str: assistant response
    """
    try:
        # Create the model
        chat_model = genai.GenerativeModel(model)

        # Start the chat
        chat = chat_model.start_chat(history=[])

        # Feed messages one by one
        for msg in messages:
            if msg["role"] == "user":
                response = chat.send_message(msg["content"])
        
        # Return only the last response
        return response.text.strip()

    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return FALLBACK_RESPONSE

# -----------------------------
# TEST RUN
# -----------------------------
if __name__ == "__main__":
    test_messages = [
        {"role": "system", "content": "You are a helpful financial assistant."},  # Optional — Gemini may ignore this
        {"role": "user", "content": "What is a Systematic Investment Plan (SIP)?"}
    ]

    reply = call_llm(test_messages)
    print("Assistant's reply:\n", reply)
