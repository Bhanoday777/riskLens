import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import numpy as np

# Load data
with open("analytics/logs.json", "r") as f:
    logs = json.load(f)

df = pd.DataFrame(logs)

# Preprocessing
df["decision_binary"] = (df["approved_or_blocked"] == "blocked").astype(int)
df["risk_bucket"] = pd.cut(
    df["risk_score"], bins=[0, 3, 6, 10], labels=["Low", "Medium", "High"]
)

alpha = 0.02

# Style
plt.rcParams.update({"font.size": 11, "axes.titlesize": 13, "axes.labelsize": 11})

# =========================
# 1. Scatter Plot (WITH LEGEND)
# =========================
plt.figure()

y = df["decision_binary"]
y_jitter = y + np.random.uniform(-0.05, 0.05, size=len(y))

colors = df["approved_or_blocked"].map({"approved": "green", "blocked": "red"})

plt.scatter(df["risk_score"], y_jitter, c=colors, s=60, alpha=0.7)

# Legend manually added
from matplotlib.lines import Line2D

legend_elements = [
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        label="Approved",
        markerfacecolor="green",
        markersize=8,
    ),
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        label="Blocked",
        markerfacecolor="red",
        markersize=8,
    ),
]
plt.legend(handles=legend_elements)

plt.axhline(0.5, linestyle="--", alpha=0.3)

plt.xlabel("Risk Score")
plt.ylabel("Decision (0 = approved, 1 = blocked)")
plt.title("Risk Score vs Decision")

plt.tight_layout()
plt.savefig("scatter.png", dpi=300)
plt.show()

# =========================
# 2. Logistic Curve
# =========================
plt.figure()
sns.regplot(x="risk_score", y="decision_binary", data=df, logistic=True, color="blue")

plt.title("Probability of Blocking vs Risk Score")
plt.xlabel("Risk Score")
plt.ylabel("Probability of Blocking")

plt.tight_layout()
plt.savefig("scatter.png", dpi=300)
plt.show()

# =========================
# 3. Heatmap (AUTO LEGEND via colorbar)
# =========================
pivot = df.pivot_table(
    values="decision_binary", index="mode", columns="risk_bucket", aggfunc="mean"
)
pivot = pivot + alpha

plt.figure()
sns.heatmap(
    pivot,
    annot=True,
    cmap="coolwarm",
    fmt=".2f",
    cbar_kws={"label": "Blocking Probability"},
)

plt.title("Blocking Probability across Modes and Risk Levels")

plt.tight_layout()
plt.savefig("scatter.png", dpi=300)
plt.show()


# =========================
# 4. Decision Reliability
# =========================
df["correct_decision"] = (
    ((df["risk_score"] >= 8) & (df["approved_or_blocked"] == "blocked"))
    | ((df["risk_score"] < 8) & (df["approved_or_blocked"] == "approved"))
).astype(int)

reliability = df.groupby("risk_bucket")["correct_decision"].mean()

plt.figure()
reliability.plot(kind="bar", color="blue")

plt.title("Decision Reliability across Risk Levels")
plt.ylabel("Accuracy")
plt.xlabel("Risk Level")

plt.tight_layout()
plt.savefig("scatter.png", dpi=300)
plt.show()

# =========================
# 5. HITL vs NON-HITL COMPARISON
# =========================

with_human = df[df["mode"] == "always_hitl"]
without_human = df[df["mode"] == "no_hitl"]

# Success = correct decision
with_success_rate = with_human["correct_decision"].mean()
without_success_rate = without_human["correct_decision"].mean()

print("\n===== HITL vs NON-HITL =====")

print("\nWITH HUMAN (always_hitl):")
print("Success Rate:", with_success_rate)

print("\nWITHOUT HUMAN (no_hitl):")
print("Success Rate:", without_success_rate)

# Improvement
improvement = with_success_rate - without_success_rate
print("\nImprovement in Success Rate:", improvement)


# =========================
# 8. COMPARISON VISUALIZATION
# =========================

labels = ["With Human", "Without Human"]
success_rates = [with_success_rate, without_success_rate]

plt.figure()
plt.bar(labels, success_rates)

plt.title("HITL vs Non-HITL: Success Rate Comparison")
plt.ylabel("Success Rate")

plt.tight_layout()
plt.savefig("scatter.png", dpi=300)
plt.show()


# =========================
# 9. 3D SURFACE PLOT (Advanced Visualization)
# =========================

from mpl_toolkits.mplot3d import Axes3D

# Encode mode numerically
mode_mapping = {"no_hitl": 0, "adaptive": 1, "always_hitl": 2}

df["mode_numeric"] = df["mode"].map(mode_mapping)

# Create pivot grid
pivot_3d = df.pivot_table(
    values="decision_binary", index="risk_score", columns="mode_numeric", aggfunc="mean"
)
# pivot = pivot.applymap(lambda x: 0.02 if x == 0 else x)

pivot_3d = pivot_3d.fillna(alpha)

X, Y = np.meshgrid(pivot_3d.columns, pivot_3d.index)
Z = pivot_3d.values

# Plot
fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")

ax.plot_surface(X, Y, Z)

ax.set_xlabel("Mode (0=no_hitl, 1=adaptive, 2=always_hitl)")
ax.set_ylabel("Risk Score")
ax.set_zlabel("Blocking Probability")

plt.title("3D View: Risk vs Mode vs Blocking Probability")

plt.tight_layout()
plt.show()
