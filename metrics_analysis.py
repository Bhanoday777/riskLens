import json
from collections import Counter

LOG_FILE = "logs.json"

with open(LOG_FILE, "r") as f:
    logs = json.load(f)

total_runs = len(logs)

success_runs = sum(1 for log in logs if log["execution_result"] == "success")
blocked_runs = sum(1 for log in logs if log["approved_or_blocked"] == "blocked")

hitl_runs = sum(1 for log in logs if log["hitl_enabled"] == True)

avg_risk = sum(log["risk_score"] for log in logs) / total_runs if total_runs else 0

# Risk distribution
risk_categories = []

for log in logs:
    risk = log["risk_score"]

    if risk <= 3:
        risk_categories.append("low")
    elif risk <= 6:
        risk_categories.append("medium")
    else:
        risk_categories.append("high")

risk_dist = Counter(risk_categories)

print("\n===== AGENT METRICS =====")
print("Total Runs:", total_runs)
print("Success Runs:", success_runs)
print("Blocked Runs:", blocked_runs)
print("Average Risk Score:", round(avg_risk, 2))
print("HITL Enabled Runs:", hitl_runs)

print("\nRisk Distribution:")
for k, v in risk_dist.items():
    print(f"{k}: {v}")

print("=========================\n")