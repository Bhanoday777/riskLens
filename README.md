# RiskLens: Risk-Aware Human-in-the-Loop Agent

RiskLens is an LLM agent that scores the risk of every action before it runs and decides whether to auto-approve it, ask a human, or block it. Every decision is logged, and an analytics module compares how often each oversight mode makes the right call.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB)
![Groq](https://img.shields.io/badge/LLM-Llama_3.1_8B_(Groq)-F55036)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Why

Tool-using AI agents can take actions with real consequences, such as running code, changing system settings or sending data elsewhere. Asking a human to approve every action is slow, and approving nothing is unsafe. RiskLens tests a middle ground: **adaptive oversight**, where the level of human involvement scales with how risky an action is.

## How it works

```text
User task
   │
   ▼
LLM planner (Llama 3.1 8B via Groq)  →  JSON list of actions
   │
   ▼
Risk scoring for each action
   final_risk = 0.6 × LLM-assessed risk (1–10)  +  0.4 × rule-based command risk
   │
   ▼
Oversight policy (depends on mode)
   ├─ risk ≤ 4.5     → auto-approve
   ├─ 4.5 < risk < 7 → ask a human
   └─ risk ≥ 7       → flagged high-risk, requires explicit human approval
   │
   ▼
Execute (code runs in a sandbox)  →  log decision + explanation + confidence
```

**Oversight modes**

| Mode | Behaviour |
|---|---|
| `no_hitl` | The agent acts on its own, with no human approval |
| `always_hitl` | Every action needs human approval |
| `adaptive` | Low-risk actions run automatically; medium- and high-risk actions go to a human |

**Safety layers**

- **Sandboxed code execution.** Generated Python runs in a subprocess with a 5-second timeout, a whitelist of allowed imports, and blocked patterns (`os`, `subprocess`, `socket`, `eval`, `open`, …).
- **Simulated dangerous actions.** Actions like disabling the firewall, exfiltrating data or deleting a directory are simulated, not run for real. This lets the policy be tested against unsafe requests safely.
- **Explainable decisions.** Every decision records the risk score, the reasons behind it and a confidence label.

## Results

Across 80 logged runs (35 adaptive, 31 always-HITL, 14 no-HITL), a decision counted as **correct** when high-risk actions (risk ≥ 8) were blocked and everything else was approved.

| Mode | Correct decisions |
|---|---|
| With human approval (`always_hitl`) | **71%** |
| Without human approval (`no_hitl`) | 43% |

Human oversight improved decision correctness by about **28 percentage points**. This is a small sample from a prototype, so treat the numbers as directional rather than conclusive.

<p>
  <img src="screenshots/hitl_vs_no_hitl.png" width="49%" alt="HITL vs non-HITL success rate" />
  <img src="screenshots/blocking_probability.png" width="49%" alt="Blocking probability vs risk score" />
</p>
<p>
  <img src="screenshots/blocking_by_mode.png" width="49%" alt="Blocking probability by mode and risk level" />
  <img src="screenshots/decision_reliability.png" width="49%" alt="Decision reliability across risk levels" />
</p>

## Running it

```bash
git clone https://github.com/Bhanoday777/riskLens.git
cd riskLens
pip install groq python-dotenv requests pandas matplotlib seaborn statsmodels
```

Create a `.env` file:

```env
GROQ_API_KEY=your_key_here
```

Run the agent. Set `MODE` at the top of the file to `no_hitl`, `always_hitl` or `adaptive`:

```bash
python examples/hitl_agent_demo.py
```

Regenerate the analysis plots from the decision log:

```bash
python analytics/final_plots.py
python analytics/mode_analysis.py
```

## Where the code is

This repository started from a copy of the [LangGraph](https://github.com/langchain-ai/langgraph) repository, which is why `libs/` and most of `examples/` contain LangGraph's own code. RiskLens itself is in:

```text
examples/hitl_agent_demo.py   # Agent: planner, risk scoring, oversight policy, tool actions
sandbox/
├── runner.py                 # Subprocess sandbox with timeout
└── policies.py               # Import whitelist and blocked patterns
analytics/
├── logger.py                 # Structured decision logging
├── logs.json                 # Logged decisions (80 runs)
├── analysis.py, mode_analysis.py, final_plots.py, visualize.py  # Analysis and plots
screenshots/                  # Generated result plots
```

## Roadmap

- Re-implement the agent loop as a LangGraph graph with interrupt-based human approval
- Larger evaluation set with labelled ground-truth risk
- Live dashboard for monitoring decisions

## License

MIT. The bundled LangGraph code keeps its original MIT license (© LangChain, Inc.).
