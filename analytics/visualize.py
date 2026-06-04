import pandas as pd
import matplotlib.pyplot as plt
from logger import load_logs

logs = load_logs()

if not logs:
    print("No logs found. Run your agent first.")
    exit()

df = pd.DataFrame(logs)

plt.figure()
df["planned_actions"].value_counts().plot(kind="bar")
plt.title("Planned Actions Distribution")
plt.xticks(rotation=45)
plt.show()

plt.figure()
df["approved_or_blocked"].value_counts().plot(kind="pie", autopct="%1.1f%%")
plt.title("HITL Decisions (Approved vs Blocked)")
plt.ylabel("")
plt.show()

plt.figure()
df["risk_score"].plot(kind="hist", bins=10)
plt.title("Risk Score Distribution")
plt.xlabel("Risk Score")
plt.ylabel("Frequency")
plt.show()

import pandas as pd

grouped = df.groupby("approved_or_blocked")["risk_score"].mean()

plt.figure()
grouped.plot(kind="bar")
plt.title("Average Risk Score by Decision")
plt.ylabel("Average Risk")
plt.show()

plt.figure()
df["execution_result"].value_counts().plot(kind="bar")
plt.title("Execution Results")
plt.ylabel("Count")
plt.show()

