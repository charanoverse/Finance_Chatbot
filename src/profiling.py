from datetime import date

def calculate_age(dob: str) -> int:
    """Calculate age from date of birth (YYYY-MM-DD)."""
    try:
        birth_date = date.fromisoformat(dob)
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except ValueError:
        return 0

def calculate_risk_profile(
    age: int,
    income: float = 0,
    savings: float = 0,
    risk_willingness: str = "medium"
) -> dict:
    """
    Compute risk profile based on financial parameters.
    Returns a dict with: risk_level, capacity, horizon.
    """
    
    # 1. Determine Risk Capacity (Ability to take risk)
    # Rule of thumb: Higher savings & income + Younger age = Higher capacity
    capacity_score = 0
    
    if age < 30:
        capacity_score += 3
    elif age < 50:
        capacity_score += 2
    else:
        capacity_score += 1
        
    if savings > (income * 0.5): # Has 6 months savings (approx)
        capacity_score += 2
    elif savings > 0:
        capacity_score += 1
        
    if income > 1000000: # High income (>10LPA)
        capacity_score += 2
    elif income > 500000:
        capacity_score += 1

    # 2. Map Willingness
    willingness_score = {"low": 1, "medium": 2, "high": 3}.get(risk_willingness.lower(), 2)
    
    # 3. Blended Risk Level
    total_score = capacity_score + willingness_score
    
    if total_score >= 6:
        risk_level = "High"
    elif total_score >= 4:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # 4. Investment Horizon
    # Default assumptions based on age
    if age < 40:
        horizon = "Long-term (>10 years)"
    elif age < 60:
        horizon = "Medium-term (5-10 years)"
    else:
        horizon = "Short-term (<5 years)"

    return {
        "risk_level": risk_level,
        "capacity_score": capacity_score,
        "willingness_score": willingness_score,
        "horizon": horizon,
        "income_stability": "High" if savings > income else "Moderate" # Simple proxy
    }
