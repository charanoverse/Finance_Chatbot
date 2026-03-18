"""
Question Detector for Context Manager

Detects when the LLM asks a question and determines what it's waiting for.
"""

import re


def detect_question_type(answer: str) -> str:
    """
    Detect what the bot is asking for based on the answer.
    
    Returns:
        waiting_for type: "age", "car_price", "amount", etc.
    """
    answer_lower = answer.lower()
    
    # Age questions
    if any(phrase in answer_lower for phrase in [
        "your age", "how old", "tell me your age", "current age"
    ]):
        return "age"
    
    # Car price / Cost
    if any(phrase in answer_lower for phrase in [
        "price of the car", "car cost", "how much is the car",
        "estimated price", "cost of the car", "price", "cost"
    ]):
        # This is slightly risky if context is unknown, but valid for most goal flows
        return "car_price"
    
    # Time horizon / when
    if any(phrase in answer_lower for phrase in [
        "when you plan", "when do you plan", "time to retirement",
        "how long until", "when will you", "time horizon", "how many years",
        "duration"
    ]):
        return "time_horizon"
    
    # Amount / target
    if any(phrase in answer_lower for phrase in [
        "target amount", "how much do you need", "amount you need", 
        "goal amount", "corpus", "estimated cost"
    ]):
        return "target_amount"
    
    # Monthly savings
    if any(phrase in answer_lower for phrase in [
        "save per month", "save monthly", "how much can you save",
        "monthly savings", "invest per month"
    ]):
        return "savings"
    
    # Income
    if any(phrase in answer_lower for phrase in [
        "your income", "your salary", "monthly income", "take home"
    ]):
        return "income"
    
    return None


def is_asking_question(answer: str) -> bool:
    """Check if the answer contains a question."""
    # Check for question marks
    if "?" in answer:
        return True
    
    # Check for question patterns
    question_patterns = [
        r"could you (?:please )?tell me",
        r"can you (?:please )?tell me",
        r"what is your",
        r"how much",
        r"when (?:do you|will you)",
    ]
    
    answer_lower = answer.lower()
    return any(re.search(pattern, answer_lower) for pattern in question_patterns)


# Test
if __name__ == "__main__":
    test_answers = [
        "To help you buy a car, could you please tell me the estimated price of the car?",
        "What is your age?",
        "How much can you save per month?",
        "Here's some information about SIPs.",
    ]
    
    for answer in test_answers:
        is_question = is_asking_question(answer)
        waiting_for = detect_question_type(answer)
        print(f"Answer: '{answer[:60]}...'")
        print(f"  Is question: {is_question}")
        print(f"  Waiting for: {waiting_for}\n")
