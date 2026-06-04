from unittest import result
from analytics.logger import log_action, save_logs
import urllib.parse

# from bs4 import BeautifulSoup
# from tavily import TavilyClient
import time
from turtle import title
import requests
import shutil
from examples.logger import log_event
from sandbox.runner import run_python_code
import subprocess
import webbrowser
import os
import requests
import sys
import json
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
decision_history = []


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "agent_workspace")
)
SYSTEM_SANDBOX = os.path.join(BASE_DIR, "system_sandbox")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

os.makedirs(SYSTEM_SANDBOX, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


# =============================
# CONFIG (USE ENV VARIABLES)
# =============================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # set via terminal
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
LOW_RISK_THRESHOLD = 4.5
HIGH_RISK_THRESHOLD = 7

client = Groq(api_key=GROQ_API_KEY)

# =============================
# HITL CONTROL SWITCH
# =============================

HITL_ENABLED = True
MODE = "no hitl"
# options: "adaptive", "no_hitl", "always_hitl"
# =============================
# HUMAN APPROVAL
# =============================


def get_valid_approval():
    while True:
        decision = input("Approve this action? (y/n): ").strip().lower()

        if decision in ["y", "yes"]:
            return True
        elif decision in ["n", "no"]:
            return False
        else:
            print("❌ Invalid input. Please enter 'y' or 'n'.")


def human_approval(action_type: str, details: str, risk: int = None) -> bool:

    if MODE == "no_hitl":
        return True

    elif MODE == "always_hitl":
        print("\n⚠️ HUMAN APPROVAL REQUIRED (FORCED MODE)")
        print("Action:", action_type)
        print("Details:", details)
        return get_valid_approval()
    if not HITL_ENABLED:
        print("⚠️ HITL disabled → MODE inactive")
        return True

    # Case 1: No risk provided
    if risk is None:
        print("\n⚠️ HUMAN APPROVAL REQUIRED")
        print("Action:", action_type)
        print("Details:", details)
        return get_valid_approval()

    # Case 2: Low risk → auto approve
    if risk <= LOW_RISK_THRESHOLD:
        print(f"🟢 Low risk auto-approved (Risk: {risk})")
        return True

    # Case 3: Medium / High risk → require approval
    print("\n⚠️ HUMAN APPROVAL REQUIRED")
    print("Action:", action_type)
    print("Details:", details)
    print("Risk Score:", risk)

    if risk >= HIGH_RISK_THRESHOLD:
        print("🚨 HIGH RISK ACTION")

    return get_valid_approval()


def self_critic(action_type, details, risk):
    if risk >= 9:
        return (
            "🚨 Extremely dangerous action. Potential system damage or security risk."
        )

    elif risk >= 7:
        return "⚠️ High-risk action. Requires careful human approval."

    elif risk >= 4:
        return "ℹ️ Low-to-moderate risk action."

    else:
        return "✅ Low-risk action. Safe to execute automatically."


def explain_decision(action_type, details, risk, decision):
    reasons = []
    confidence = "LOW"

    # Risk-based reasoning
    if risk >= 9:
        reasons.append("Extremely high-risk action detected")
        confidence = "HIGH"
    elif risk >= 7:
        reasons.append("High-risk keywords or intent detected")
        confidence = "HIGH"
    elif risk >= 4:
        reasons.append("Moderate system-level operation")
        confidence = "MEDIUM"
    else:
        reasons.append("Low-risk operation")
        confidence = "HIGH"

    # Threshold reasoning (important for justification)
    if risk >= HIGH_RISK_THRESHOLD:
        reasons.append("Risk exceeds high-risk threshold")

    # Action-specific hints
    details_str = str(details).lower()
    if "delete" in details_str:
        reasons.append("Destructive operation identified")
    if "http" in details_str:
        reasons.append("External web interaction")

    return {
        "action_type": action_type,
        "risk_score": risk,
        "decision": decision,
        "reasons": reasons,
        "confidence": confidence,
    }


def execute_action(action_type, details, risk, function, task, planned_actions):

    print("\n🧠 SELF-CRITIC ANALYSIS:")
    print(self_critic(action_type, details, risk))

    approved = human_approval(action_type, details, risk)

    if approved:
        output = function()
        print("✅ Action completed.")

        if output:
            print("\n📄 Result:\n")
            print(output)

        result = {"status": "success", "output": str(output)}
        decision = "approved"

    else:
        output = None
        print("⛔ Action blocked.")

        result = {"status": "blocked", "output": "Action blocked by human approval."}
        decision = "blocked"

    # =============================
    # 🧠 ERADE — ADD FROM HERE
    # =============================

    decision_data = explain_decision(action_type, details, risk, decision)

    # 🔹 Compact display (per action)
    print(
        f"\n[Decision] Risk: {decision_data['risk_score']} | "
        f"Decision: {decision_data['decision']} | "
        f"Reason: {decision_data['reasons'][0]}"
    )

    # 🔹 Store for final summary
    global decision_history
    if "decision_history" not in globals():
        decision_history = []

    decision_history.append(decision_data)

    # =============================
    # LOGGING (UPDATED)
    # =============================
    unsafe_flag = risk >= 8

    log_event(
        task=task,
        planned_actions=planned_actions,
        risk_score=risk,
        hitl_enabled=HITL_ENABLED,
        mode=MODE,
        decision=decision,
        result=str(result),
        explanation=decision_data["reasons"],
        confidence=decision_data["confidence"],
        action_type=decision_data["action_type"],
        unsafe_flag=unsafe_flag,
    )

    return result


# =============================
# TOOL FUNCTIONS
# =============================


def open_website(site: str):
    if not site.startswith("http"):
        site = "https://" + site
    webbrowser.open(site)


def open_search_in_browser(query: str):
    import urllib.parse

    encoded_query = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded_query}"
    webbrowser.open(url)


def web_search(query: str, open_in_browser=False):
    print(f"\n🌐 Searching the web for: {query}")

    try:
        url = "https://api.tavily.com/search"

        payload = {
            "api_key": os.getenv("TAVILY_API_KEY"),
            "query": query,
            "max_results": 5,
        }

        response = requests.post(url, json=payload)
        data = response.json()

        results = []
        links = []

        for r in data.get("results", []):
            title = r.get("title")
            snippet = r.get("content")
            link = r.get("url")

            # ✅ filtering
            if not title or not snippet:
                continue

            if len(snippet) < 50:
                continue

            results.append({"title": title, "snippet": snippet, "link": link})

            if link:
                links.append(link)

        # ✅ Display nicely
        print("\nTop Results:\n")
        for i, r in enumerate(results[:3]):
            print(f"{i+1}. {r['title']}")
            print(f"   {r['snippet'][:100]}...")
            print(f"   🔗 {r['link']}\n")

        # ✅ HITL control
        if open_in_browser and links:
            choice = input("Open top links in browser? (yes/no/select): ").lower()

            if choice == "yes":
                for link in links[:3]:
                    webbrowser.open(link)

            elif choice == "select":
                selection = input("Enter numbers (e.g., 1 3): ")
                try:
                    selected_links = [links[int(i) - 1] for i in selection.split()]
                    for link in selected_links:
                        webbrowser.open(link)
                except:
                    print("Invalid selection.")

        return results

    except Exception as e:
        print("❌ Web search failed:", str(e))
        return []


def analyze_system():
    print("\n🧠 Running system diagnostics...")

    try:
        ip_output = subprocess.check_output(
            "ipconfig", shell=True, text=True, stderr=subprocess.DEVNULL
        )
    except:
        ip_output = "Failed to retrieve network info"

    try:
        task_output = subprocess.check_output(
            "tasklist", shell=True, text=True, stderr=subprocess.DEVNULL
        )
    except:
        task_output = "Failed to retrieve process list"

    # Trim to avoid token overload
    ip_output = ip_output[:2000]
    task_output = task_output[:2000]

    prompt = f"""
You are a STRICT system diagnostics AI.

You MUST ONLY use the provided system data.
DO NOT assume anything not explicitly present.

--- NETWORK INFO ---
{ip_output}

--- PROCESS LIST ---
{task_output}

RULES:

1. Base your analysis ONLY on visible evidence in the data.
2. If something is not clearly visible, say:
   "Not enough evidence"
3.You may identify potential risks if patterns are commonly associated with issues,
but clearly label them as LOW confidence unless strongly supported by evidence.
4. If a behavior is normal (e.g., multiple svchost.exe), state that clearly.
5. If data appears incomplete or truncated, mention it as a limitation.

For EACH point, include:
- Observation (what you see)
- Evidence (exact reference from data)
- Confidence level:
    HIGH = clearly visible in data
    MEDIUM = likely but not fully certain
    LOW = uncertain / incomplete data

OUTPUT FORMAT:

System Health:
- Summary
- Confidence:

Network Status:
- Observation:
- Evidence:
- Confidence:

Process Analysis:
- Observation:
- Evidence:
- Confidence:

Risks:
Risks:
- Include confirmed risks (HIGH confidence)
- Include potential risks (LOW or MEDIUM confidence) if patterns are suspicious
- Clearly label confidence for each risk
- If no risks found, say: "No significant risks detected"

Recommendations:
- Only based on confirmed observations
"""
    print("\n🧾 RAW DATA (USED FOR ANALYSIS):")

    print("\n--- IPCONFIG (partial) ---")
    print(ip_output[:500])

    print("\n--- TASKLIST (partial) ---")
    print(task_output[:500])
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    result = response.choices[0].message.content.strip()

    print("\n📊 SYSTEM DIAGNOSIS:\n")
    print(result)


def summarize_web_results(query: str, results: list):

    combined = "\n".join([f"{r['title']}: {r['snippet']}" for r in results])

    prompt = f"""
You are a STRICT research summarizer.

User query:
{query}

Web results:
{combined}

Instructions:
- ONLY use the provided web results
- DO NOT add external knowledge
- DO NOT make predictions
- DO NOT assume missing information
- If information is unclear, say "Not enough information"
- Keep it factual and grounded in the results

Format:
- Key points
- Keep it concise
- Avoid future predictions unless explicitly stated in sources
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    summary = response.choices[0].message.content.strip()

    print("\n📊 Web Search Summary:\n")
    print(summary)

    print("\n🔗 Sources:")
    for r in results:
        print(f"- {r.get('title')}")
        print(f"  {r.get('link')}\n")

    return summary


def rewrite_sensitive_query(query: str):

    prompt = f"""
Transform the following user request into a SAFE educational explanation request.

Requirements:
- Keep the same topic.
- Explain how the concept works at a high level.
- Explain risks, impacts, and real-world consequences.
- Include defensive or preventive measures when relevant.
- DO NOT include step-by-step instructions, tools, or attack methods.

User request:
{query}

Return ONLY the rewritten educational explanation request.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    return response.choices[0].message.content.strip()


def information_lookup(query: str):

    print(f"\n🔎 Researching: {query}")

    try:

        prompt = f"""
You are an intelligent research assistant.

User query:
{query}

Instructions:
- Provide a clear and helpful answer.
- If the query asks for recommendations (example: laptops under 1 lakh),
  provide a list with key specifications.
- If it asks for comparisons, present them clearly.
- Keep the response concise and structured.
- End with a short recommendation if applicable.
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful research assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        answer = response.choices[0].message.content.strip()

        print("\n📊 Research Result:\n")
        print(answer)

    except Exception as e:
        print("❌ Research lookup failed:", e)


def answer_general_question(question: str, risk: int):

    if risk >= HIGH_RISK_THRESHOLD:
        safe_query = rewrite_sensitive_query(question)

        final_prompt = f"""
You are an educational AI assistant.

The user originally asked:
"{question}"

For safety reasons the request has been converted into this educational topic:
"{safe_query}"

Provide a **high-level explanation** of the concept.

Rules:
- Explain how the concept works.
- Discuss risks or impacts.
- Mention defensive or prevention techniques when relevant.
- Do NOT give instructions, tools, or procedural steps.

Respond in a clear educational style.
"""

    else:
        final_prompt = question

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Provide safe educational explanations."},
            {"role": "user", "content": final_prompt},
        ],
        temperature=0,
    )

    answer = response.choices[0].message.content.strip()

    print("\n📚 Answer:")
    print(answer)


def search_job_and_summarize(query: str):

    print(f"\n🔎 Searching jobs for: {query}")

    try:

        prompt = f"""
You are a job research assistant.

User request:
{query}

Provide:
1. Example companies hiring
2. Typical job description
3. Key skills required
4. Short summary of the role

Keep it structured and concise.
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You help summarize job descriptions."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        result = response.choices[0].message.content.strip()

        print("\n📄 Job Summary:\n")
        print(result)

    except Exception as e:
        print("❌ Job search failed:", e)


import re


def check_sensitive_content(text: str):

    prompt = f"""
You are a safety classifier for an AI agent.

Evaluate the following user request and assign a risk score from 1 to 10.

1 = completely safe
5 = moderate system risk
10 = extremely dangerous / illegal activity

Respond ONLY with the number.

User request:
{text}
"""

    try:

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        risk_text = response.choices[0].message.content.strip()

        # Extract number safely
        risk_score = int(re.findall(r"\d+", risk_text)[0])

        return risk_score

    except Exception as e:
        print("Risk detection failed:", e)
        return 5


def analyze_logs():
    if not os.path.exists("logs.jsonl"):
        print("No logs found.")
        return

    total, approved, blocked = 0, 0, 0

    with open("logs.jsonl", "r") as f:
        for line in f:
            log = json.loads(line)
            total += 1

            if log.get("decision") == "approved":
                approved += 1
            elif log.get("decision") == "blocked":
                blocked += 1

    print("\n=== LOG ANALYSIS ===")
    print("Total actions:", total)
    print("Approved:", approved)
    print("Blocked:", blocked)


def open_browser_default():
    webbrowser.open("https://www.google.com")


def open_notepad():
    subprocess.Popen("notepad", shell=True)


def simulate_disable_security(component: str):

    import json

    state_file = "security_state.json"

    state = {"firewall": "enabled", "antivirus": "enabled"}

    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            state = json.load(f)

    state[component] = "disabled"

    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

    print("\n⚠️ SIMULATED SECURITY CHANGE")
    print(f"[SIMULATION] {component} disabled")
    print(f"[SIMULATION] Updated {state_file}\n")


def simulate_data_exfiltration(target: str):

    log_file = "exfiltration_log.txt"

    with open(log_file, "a") as f:
        f.write(f"Simulated data exfiltration to {target}\n")

    print("\n⚠️ SIMULATED DATA EXFILTRATION")
    print(f"[SIMULATION] Data would be sent to: {target}")
    print(f"[SIMULATION] Logged in {log_file}\n")


def simulate_delete_directory(path: str):
    print("\n⚠️ DANGEROUS ACTION EXECUTING")

    # ✅ Convert relative → absolute inside workspace
    full_path = os.path.abspath(os.path.join(BASE_DIR, path))

    # ✅ Restrict to agent workspace only
    if not full_path.startswith(BASE_DIR):
        print("❌ Deletion blocked. Outside allowed workspace.")
        return

    # ❌ Prevent breaking your code execution sandbox
    if "code_sandbox" in full_path:
        print("❌ Deletion blocked. Cannot delete code sandbox.")
        return

    # ✅ Perform deletion
    if os.path.exists(full_path):
        shutil.rmtree(full_path)
        print(f"🗑️ Folder '{full_path}' deleted successfully.")
    else:
        print(f"⚠️ Folder '{full_path}' does not exist.")


def clean_system():
    print("\n🧹 Scanning system sandbox...")

    # print("DEBUG BASE_DIR:", BASE_DIR)
    print("DEBUG SYSTEM_SANDBOX:", SYSTEM_SANDBOX)
    print("DEBUG TEMP_DIR:", TEMP_DIR)

    targets = []

    for root, dirs, files in os.walk(SYSTEM_SANDBOX):
        print("DEBUG scanning SYSTEM_SANDBOX root:", root)
        for f in files:
            print("DEBUG found file:", f)
            targets.append(os.path.join(root, f))

    for root, dirs, files in os.walk(TEMP_DIR):
        print("DEBUG scanning TEMP_DIR root:", root)
        for f in files:
            print("DEBUG found file:", f)
            targets.append(os.path.join(root, f))

    # print("DEBUG targets list:", targets)

    if not targets:
        print("✅ Nothing to clean.")
        return

    print("\n⚠️ Proposed deletions:")
    for t in targets:
        print("-", t)

    if HITL_ENABLED:
        decision = input("\nApprove deletion? (y/n): ").lower()
        if decision != "y":
            print("⛔ Cleanup cancelled.")
            return

    for t in targets:
        try:
            os.remove(t)
        except Exception as e:
            print(f"❌ Failed to delete {t}: {e}")

    print("🧹 Cleanup completed.")


def get_real_weather(city: str):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)

    if response.status_code != 200:
        print("❌ Weather API error.")
        return

    data = response.json()
    print(
        f"🌦 Weather in {city}: {data['main']['temp']}°C, {data['weather'][0]['description']}"
    )


def handle_code_execution(description: str, max_retries: int = 2):
    code_prompt = f"""
Write ONLY valid Python code.
No explanations.
No markdown.
Assume all required values must be hardcoded.
Task: {description}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": code_prompt}],
        temperature=0,
    )

    code = response.choices[0].message.content.strip()
    # Clean markdown fences
    code = code.replace("```python", "").replace("```", "").strip()

    attempt = 0

    while attempt <= max_retries:
        print(f"\n=== Attempt {attempt + 1} ===")
        print("\nGenerated Code:\n")
        print(code)

        # approval = input("\nApprove execution? (y/n): ")
        # if approval.lower() != "y":
        # print("Execution cancelled.")
        # return

        result = run_python_code(code)

        print("\n=== Execution Summary ===")

        status = result.get("status")
        stdout = result.get("stdout")
        stderr = result.get("stderr")
        returncode = result.get("returncode")

        print(f"Status       : {status}")
        print(f"Return Code  : {returncode}")

        if stdout:
            print("\n--- Output ---")
            print(stdout.strip())

        if stderr:
            print("\n--- Error ---")
            print(stderr.strip())

        print("=========================")

        # Success case
        if result.get("status") == "success" and result.get("returncode") == 0:
            print("✅ Code executed successfully.")
            return

        # If failed and retries remain
        attempt += 1
        if attempt > max_retries:
            print("❌ Max retries reached. Stopping.")
            return

        print("\n🔁 Attempting automatic debug...")

        debug_prompt = f"""
The following Python code failed.

Task:
{description}

Code:
{code}

Error:
{result.get("stderr")}

Fix the code.
Return ONLY corrected Python code.
No explanations.
"""

        debug_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": debug_prompt}],
            temperature=0,
        )

        code = debug_response.choices[0].message.content.strip()
        code = code.replace("```python", "").replace("```", "").strip()


# =============================
# SAFE COMMAND MAPPING
# =============================

COMMAND_CACHE = {}

COMMAND_MAP = {
    "get_ip": "ipconfig",
    "list_processes": "tasklist",
    "system_info": "systeminfo",
    "list_files": "dir",
}

COMMAND_RISK = {"ipconfig": 4, "tasklist": 6, "systeminfo": 5, "dir": 3}


def adjust_risk(command):
    base = COMMAND_RISK.get(command, 5)

    # ✅ Reduce risk if command already executed (cached)
    if command in COMMAND_CACHE:
        base -= 1

    # ✅ Reduce risk for read-only commands
    if command in ["ipconfig", "tasklist", "dir"]:
        base -= 1

    return max(1, base)


# =============================
# ROBUST LLM PLANNER
# =============================


def plan_with_llm(task: str):
    prompt = f"""
You are a strict JSON planning engine.

Return ONLY valid JSON in this format:

{{
  "actions": [
    {{
      "action": "action_name",
      "parameters": {{}}
    }}
  ]
}}

Rules:

1. If the user asks to write, generate, implement, or run Python code,
   you MUST return ONLY ONE action:
   - generate_and_run_code

2. Do NOT include any additional actions when generate_and_run_code is used.

3. Only include system-related actions (get_ip, list_files, etc.)
   if the user explicitly asks for system information.

4. If deleting a folder, use the exact folder name provided by the user.
    Example:
    User: delete test_folder
    Action: dangerous_delete_directory
    Parameters: {{"path": "test_folder"}}
5. If the user asks a general knowledge or informational question,
return the action:
general_question

6. If the user asks for recommendations, comparisons, product suggestions,
or informational lists (example: top laptops under 1 lakh),
use the action:
information_lookup

7. If the user asks for jobs, internships, or job descriptions,
use the action:
search_job_and_summarize
If the query involves:
- latest news
- recent updates
- current events
- real-time information

You MUST use:
web_search

Do NOT use information_lookup for these queries.

8 . If the user explicitly wants to browse, search in browser, or open results in browser,
use the action:
browser_search

9. If the user asks to clean system, remove temp files, delete junk files,
or free up space, you MUST use:

action: clean_system

Do NOT return "clean system" as action.

10. If the user asks to:
- analyze system
- check system health
- diagnose system
- check performance

Use action:
analyze_system

Parameters:
{{ "query": "..." }}

Allowed actions:
- open_website (url)
- web_search (query)
- browser_search (query)
- open_notepad
- weather (city)
- get_ip
- list_processes
- system_info
- analyze_logs
- analyze_system
- list_files
- general_question (question)
- dangerous_delete_directory (path)
- clean system
- information_lookup (query)
- simulate_data_exfiltration (target)
- simulate_disable_security (component)
- search_job_and_summarize (query)
- generate_and_run_code (description)
Do NOT generate raw shell commands.
No explanations.
No markdown.

User request: "{task}"
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    raw_output = response.choices[0].message.content.strip()

    try:
        start = raw_output.find("{")
        end = raw_output.rfind("}") + 1
        json_string = raw_output[start:end]
        return json.loads(json_string)
    except Exception:
        print("⚠️ Planning failed. Falling back to safe response.")
        return {"actions": []}


# =============================
# HELPER FOR REACT LOOP
# =============================


def handle_action(action_type, params, task, planned_actions):

    if action_type == "open_website":
        url = params.get("url")
        if url:
            # risk = check_sensitive_content(url)
            llm_risk = check_sensitive_content(url)
            command_risk = 5
            risk = final_risk_score(llm_risk, command_risk)
            return execute_action(
                "Open Website",
                url,
                risk,
                lambda: open_website(url),
                task,
                planned_actions,
            )

    elif action_type == "open_browser":
        return execute_action(
            "Open Browser",
            "Launch browser",
            2,
            open_browser_default,
            task,
            planned_actions,
        )

    elif action_type == "open_notepad":
        return execute_action(
            "Open Notepad", "Launch Notepad", 2, open_notepad, task, planned_actions
        )

    elif action_type == "general_question":
        question = params.get("question")
        if question:
            # risk = check_sensitive_content(question)
            llm_risk = check_sensitive_content(question)
            command_risk = 5  # safe default
            risk = final_risk_score(llm_risk, command_risk)
            return execute_action(
                "General Question",
                question,
                risk,
                lambda: answer_general_question(question, risk),
                task,
                planned_actions,
            )

    elif action_type == "weather":
        city = params.get("city")
        if city:
            return execute_action(
                "Weather Check",
                city,
                4,
                lambda: get_real_weather(city),
                task,
                planned_actions,
            )

    elif action_type == "dangerous_delete_directory":
        path = params.get("path")
        if path:
            return execute_action(
                "Dangerous Delete Directory",
                path,
                10,
                lambda: simulate_delete_directory(path),
                task,
                planned_actions,
            )

    elif action_type in COMMAND_MAP:
        command = COMMAND_MAP[action_type]

        # 🔁 Cache check
        if command in COMMAND_CACHE:
            print("⚠️ Using cached result")
            cached_output = COMMAND_CACHE[command]

        def run():
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            COMMAND_CACHE[command] = result.stdout
            return result.stdout

        # 🎯 Risk calculation
        risk = adjust_risk(command)
        return execute_action(
            "Execute Command", command, risk, run, task, planned_actions
        )

    elif action_type == "simulate_data_exfiltration":
        target = params.get("target")
        if target:
            return execute_action(
                "Data Exfiltration",
                target,
                8,
                lambda: simulate_data_exfiltration(target),
                task,
                planned_actions,
            )

    elif action_type == "simulate_disable_security":
        component = params.get("component")
        if component:
            return execute_action(
                "Disable Security",
                component,
                9,
                lambda: simulate_disable_security(component),
                task,
                planned_actions,
            )

    elif action_type == "information_lookup":
        query = params.get("query")

        if not query:
            print("⚠️ Missing query parameter.")
            return "invalid input"

        # risk = check_sensitive_content(query)
        llm_risk = check_sensitive_content(query)
        command_risk = 5
        risk = final_risk_score(llm_risk, command_risk)

        return execute_action(
            "Information Lookup",
            query,
            risk,
            lambda: information_lookup(query),
            task,
            planned_actions,
        )

    elif action_type == "search_job_and_summarize":
        query = params.get("query")
        if query:
            llm_risk = check_sensitive_content(query)
            command_risk = 5
            risk = final_risk_score(llm_risk, command_risk)
            return execute_action(
                "Job Search & Summary",
                query,
                risk,
                lambda: search_job_and_summarize(query),
                task,
                planned_actions,
            )

    elif action_type == "web_search":
        query = params.get("query")
        if query:
            # risk = check_sensitive_content(query)
            llm_risk = check_sensitive_content(query)
            command_risk = 5
            risk = final_risk_score(llm_risk, command_risk)

            def run_search():
                results = web_search(query)
                if results:
                    summarize_web_results(query, results)

            return execute_action(
                "Web Search", query, risk, run_search, task, planned_actions
            )

    elif action_type == "browser_search":
        query = params.get("query")
        if query:
            return execute_action(
                "Browser Search",
                query,
                2,
                lambda: open_search_in_browser(query),
                task,
                planned_actions,
            )

    elif action_type == "clean system":
        return execute_action(
            "Clean System",
            "Cleaning sandbox temp files",
            6,
            clean_system,
            task,
            planned_actions,
        )

    elif action_type == "analyze_logs":
        return execute_action(
            "Analyze Logs", "logs.json", 2, analyze_logs, task, planned_actions
        )

    elif action_type == "analyze_system":
        return execute_action(
            "System Diagnosis",
            "Analyzing system health",
            5,
            analyze_system,
            task,
            planned_actions,
        )

    elif action_type == "generate_and_run_code":
        description = params.get("description")
        if description:
            return execute_action(
                "Generate & Run Code",
                description,
                6,
                lambda: handle_code_execution(description),
                task,
                planned_actions,
            )

    else:
        print("⚠️ Unknown action:", action_type)
        return "unknown"


# =============================
# DYNAMIC AGENT
# =============================

# =============================
# RISK COMBINATION (NEW)
# =============================


def final_risk_score(llm_risk, command_risk):
    return round(0.6 * llm_risk + 0.4 * command_risk, 2)


def agent(task: str):

    current_state = task
    max_steps = 4

    for step in range(max_steps):

        print(f"\n🔁 Step {step+1}")

        try:
            plan = plan_with_llm(current_state)
        except Exception as e:
            print("❌ Planning failed:", e)
            return

        actions = plan.get("actions", [])
        planned_actions = [a.get("action") for a in actions]

        if not actions:
            print("✅ No more actions. Stopping.")
            break

        action = actions[0]
        action_type = action.get("action")
        params = action.get("parameters", {})

        result = handle_action(action_type, params, task, planned_actions)

        current_state = f"""
Original task: {task}

Last action: {action_type}
Result: {result}

What should be done next?
If task is complete, return no actions.
"""

        if result and result != "blocked":
            print("✅ Task completed.")
            break

    # =============================
    # 🧾 FINAL DECISION SUMMARY
    # =============================

    # decision_history.clear()


# =============================
# MAIN LOOP
# =============================


def choose_hitl_mode():
    while True:
        choice = input("Enable Human-in-the-Loop mode? (y/n): ").strip().lower()
        if choice == "y":
            return True
        elif choice == "n":
            return False


def decide_execution(risk):
    if risk < 3:
        return "auto_execute"
    elif risk < 7:
        return "require_hitl"
    else:
        return "block"


if __name__ == "__main__":
    print("=== Dynamic LLM HITL Agent ===")
    HITL_ENABLED = choose_hitl_mode()
    print("HITL Enabled:", HITL_ENABLED)
    print("MODE:", MODE)

    while True:
        user_task = input("\nEnter a task (or 'exit'): ")

        if user_task.lower() == "exit":

            # =============================
            # 🧾 FINAL SESSION DECISION REPORT
            # =============================
            if decision_history:
                print("\n=== FINAL SESSION DECISION REPORT ===\n")

                for i, d in enumerate(decision_history, 1):
                    print(f"{i}. {d['action_type']}")
                    print(f"   Risk: {d['risk_score']} → {d['decision']}")
                    print(f"   Confidence: {d['confidence']}")
                    print(f"   Reason: {', '.join(d['reasons'])}")
                    print()

            break

        agent(user_task)
