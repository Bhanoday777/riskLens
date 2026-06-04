# analytics/logger.py

import time
import json
import os

LOG_FILE = os.path.join(os.path.dirname(__file__), "logs.json")

logs = []


def log_action(task, action, approved, success, start_time):
    entry = {
        "task": task,
        "action": action,
        "approved": approved,
        "success": success,
        "time_taken": round(time.time() - start_time, 3)
    }

    logs.append(entry)


def save_logs():
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)


def load_logs():
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, "r") as f:
        return json.load(f)