import pandas as pd
import json

# Load logs
with open("analytics/logs.json", "r") as f:
    logs = json.load(f)

df = pd.DataFrame(logs)

# Now this will work
print(df["mode"].unique())