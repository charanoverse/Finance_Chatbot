"""
Calculator Module for Finance Chatbot

Provides deterministic mathematical calculations to eliminate LLM hallucinations.
The LLM should only explain results, not compute them.

Supported calculations:
- time_to_save: How long to save a target amount
- monthly_required: How much to save monthly
- emi_affordability: Whether EMI is affordable based on income
"""

import re
from typing import Optional, Dict, Any


def extract_numbers(query: str) -> list:
    """Extract all numbers from a query string."""
    # Match numbers with optional commas and decimals
    pattern = r'[\d,]+(?:\.\d+)?'
    matches = re.findall(pattern, query)
    # Remove commas and convert to float
    return [float(m.replace(',', '')) for m in matches]


def time_to_save(target_amount: float, monthly_saving: float) -> Dict[str, Any]:
    """
    Calculate time required to save a target amount.
    
    Args:
        target_amount: Target savings goal
        monthly_saving: Monthly savings amount
        
    Returns:
        Dict with months, years, and formatted calculation
    """
    if monthly_saving <= 0:
        return {
            "error": "Monthly saving must be greater than 0",
            "months": None,
            "years": None
        }
    
    months = target_amount / monthly_saving
    years = months / 12
    
    return {
        "months": round(months, 1),
        "years": round(years, 1),
        "calculation": f"₹{target_amount:,.0f} ÷ ₹{monthly_saving:,.0f} = {months:.1f} months",
        "explanation": f"At ₹{monthly_saving:,.0f} per month, you'll reach ₹{target_amount:,.0f} in {months:.1f} months ({years:.1f} years)."
    }


def monthly_required(target_amount: float, months: int) -> Dict[str, Any]:
    """
    Calculate monthly savings required to reach a target.
    
    Args:
        target_amount: Target savings goal
        months: Number of months to save
        
    Returns:
        Dict with monthly amount and formatted calculation
    """
    if months <= 0:
        return {
            "error": "Months must be greater than 0",
            "monthly": None
        }
    
    monthly = target_amount / months
    
    return {
        "monthly": round(monthly, 2),
        "calculation": f"₹{target_amount:,.0f} ÷ {months} months = ₹{monthly:,.2f} per month",
        "explanation": f"To save ₹{target_amount:,.0f} in {months} months, you need to save ₹{monthly:,.2f} per month."
    }


def emi_affordability(monthly_income: float, emi_amount: float) -> Dict[str, Any]:
    """
    Check if EMI is affordable (should be <= 40% of income).
    
    Args:
        monthly_income: Monthly income
        emi_amount: EMI amount
        
    Returns:
        Dict with affordability status and percentage
    """
    if monthly_income <= 0:
        return {
            "error": "Monthly income must be greater than 0",
            "affordable": None
        }
    
    percentage = (emi_amount / monthly_income) * 100
    affordable = percentage <= 40
    
    status = "affordable" if affordable else "risky"
    
    return {
        "affordable": affordable,
        "percentage": round(percentage, 1),
        "calculation": f"₹{emi_amount:,.0f} ÷ ₹{monthly_income:,.0f} = {percentage:.1f}%",
        "explanation": f"EMI of ₹{emi_amount:,.0f} is {percentage:.1f}% of your ₹{monthly_income:,.0f} income. This is {status} (recommended: ≤40%)."
    }


def detect_calculation_intent(query: str) -> Optional[str]:
    """
    Detect if query requires calculation and which type.
    
    Returns:
        'time_to_save', 'monthly_required', 'emi_affordability', or None
    """
    query_lower = query.lower()
    
    # Time to save patterns
    if any(phrase in query_lower for phrase in [
        "how long", "how many months", "how many years",
        "time to save", "when will i reach"
    ]):
        return "time_to_save"
    
    # Monthly required patterns
    if any(phrase in query_lower for phrase in [
        "how much per month", "monthly savings", "save per month",
        "how much should i save"
    ]):
        return "monthly_required"
    
    # EMI affordability patterns
    if any(phrase in query_lower for phrase in [
        "can i afford", "afford emi", "emi affordable",
        "should i take loan"
    ]) and ("emi" in query_lower or "loan" in query_lower):
        return "emi_affordability"
    
    return None


def calculate(query: str) -> Optional[Dict[str, Any]]:
    """
    Main calculation function - detects intent and performs calculation.
    
    Args:
        query: User query
        
    Returns:
        Calculation result dict or None if no calculation needed
    """
    calc_type = detect_calculation_intent(query)
    if not calc_type:
        return None
    
    numbers = extract_numbers(query)
    
    if calc_type == "time_to_save":
        if len(numbers) >= 2:
            # Assume larger number is target, smaller is monthly
            target = max(numbers)
            monthly = min(numbers)
            return time_to_save(target, monthly)
    
    elif calc_type == "monthly_required":
        if len(numbers) >= 2:
            # Look for time indicator
            query_lower = query.lower()
            target = max(numbers)
            time_value = min(numbers)
            
            # Convert years to months if needed
            if "year" in query_lower:
                months = int(time_value * 12)
            else:
                months = int(time_value)
            
            return monthly_required(target, months)
    
    elif calc_type == "emi_affordability":
        if len(numbers) >= 2:
            # Assume larger number is income, smaller is EMI
            income = max(numbers)
            emi = min(numbers)
            return emi_affordability(income, emi)
    
    return None


# Test cases
if __name__ == "__main__":
    test_queries = [
        "How long to save 10 lakh at 50k per month?",
        "I want to save 5,00,000. I can save 25,000 monthly. How long?",
        "How much should I save per month to reach 10 lakh in 2 years?",
        "Can I afford 30k EMI on 80k salary?",
    ]
    
    print("Calculator Tests:\n")
    for query in test_queries:
        print(f"Query: {query}")
        result = calculate(query)
        if result:
            if "error" in result:
                print(f"  Error: {result['error']}")
            else:
                print(f"  Calculation: {result.get('calculation', 'N/A')}")
                print(f"  Explanation: {result.get('explanation', 'N/A')}")
        else:
            print("  No calculation detected")
        print()
