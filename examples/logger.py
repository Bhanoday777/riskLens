import json
import os
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "logs.json")


def log_event(task, planned_actions, risk_score, hitl_enabled, decision, result, status=None, **kwargs):

    entry = {
        "timestamp": datetime.now().isoformat(),
        "task": task,
        "planned_actions": planned_actions,
        "risk_score": risk_score,
        "hitl_enabled": hitl_enabled,
        "mode": kwargs.get("mode", "unknown"),
        "approved_or_blocked": decision,
        "execution_result": result
    }

    # ✅ Add extra fields dynamically (THIS FIXES YOUR ERROR)
    entry.update(kwargs)

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)

    with open(LOG_FILE, "r+") as f:
        data = json.load(f)
        data.append(entry)
        f.seek(0)
        json.dump(data, f, indent=4)