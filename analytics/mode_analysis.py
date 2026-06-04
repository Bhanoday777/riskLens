import pandas as pd
import matplotlib.pyplot as plt
import json

# ✅ Directly load correct file
with open("analytics/logs.json", "r") as f:
    logs = json.load(f)

if not logs:
    print("No logs found.")
    exit()

df = pd.DataFrame(logs)
approval_rate = (df["approved_or_blocked"] == "approved").mean()
block_rate = (df["approved_or_blocked"] == "blocked").mean()

print("Approval Rate:", approval_rate)
print("Block Rate:", block_rate)

# Debug (optional)
print(df.columns)

# Make sure correct column name
decision_col = "decision" if "decision" in df.columns else "approved_or_blocked"

# =========================
# GRAPH 1: Mode vs Approval Rate
# =========================
approval_rate = df.groupby("mode")[decision_col].apply(
    lambda x: (x == "approved").mean()
)

plt.figure()
approval_rate.plot(kind="bar")
plt.title("Approval Rate by Mode")
plt.ylabel("Approval Rate")
plt.xlabel("Mode")
plt.show()

# =========================
# GRAPH 2: Mode vs Blocked Actions
# =========================
blocked_count = df.groupby("mode")[decision_col].apply(
    lambda x: (x == "blocked").sum()
)

plt.figure()
blocked_count.plot(kind="bar")
plt.title("Blocked Actions by Mode")
plt.ylabel("Count")
plt.xlabel("Mode")
plt.show()

plt.figure()

colors = df["approved_or_blocked"].map({
    "approved": "green",
    "blocked": "red"
})

plt.scatter(df["risk_score"], df["approved_or_blocked"].astype("category").cat.codes, c=colors)

plt.xlabel("Risk Score")
plt.ylabel("Decision (0=approved, 1=blocked)")
plt.title("Risk Score vs Decision")

plt.show()

plt.figure()
df.boxplot(column="risk_score", by="mode")

plt.title("Risk Distribution by Mode")
plt.suptitle("")
plt.xlabel("Mode")
plt.ylabel("Risk Score")

plt.show()

df["risk_bucket"] = pd.cut(df["risk_score"], bins=[0,3,6,10], labels=["Low","Medium","High"])

bucket_analysis = df.groupby(["risk_bucket", "approved_or_blocked"]).size().unstack()

bucket_analysis.plot(kind="bar", stacked=True)

plt.title("Decision Distribution Across Risk Levels")
plt.xlabel("Risk Level")
plt.ylabel("Count")

plt.show()