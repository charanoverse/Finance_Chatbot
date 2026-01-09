import json, os
from datetime import datetime

FILE = "progress.json"

def load_data():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

def set_goal(user_id, goal, target_amount, duration_months):
    data = load_data()
    monthly_required = target_amount // duration_months
    data[user_id] = {
        "goal": goal,
        "target_amount": target_amount,
        "duration_months": duration_months,
        "monthly_required": monthly_required,
        "savings_done": [],
        "created_at": str(datetime.now().date())
    }
    save_data(data)
    return data[user_id]

def add_saving(user_id, amount):
    data = load_data()
    if user_id not in data:
        return {"error": "No goal set"}
    data[user_id]["savings_done"].append(amount)
    save_data(data)
    return data[user_id]

def get_status(user_id):
    data = load_data()
    if user_id not in data:
        return {"error": "No goal set"}
    g = data[user_id]
    total_saved = sum(g["savings_done"])
    percent = (total_saved / g["target_amount"]) * 100
    remaining = g["target_amount"] - total_saved
    return {
        "goal": g["goal"],
        "target": g["target_amount"],
        "saved": total_saved,
        "remaining": remaining,
        "progress_percent": round(percent, 2),
        "monthly_required": g["monthly_required"],
        "months_left": g["duration_months"] - len(g["savings_done"])
    }
