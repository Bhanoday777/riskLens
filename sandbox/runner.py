# sandbox/runner.py

import subprocess
import sys
from pathlib import Path
from sandbox.policies import is_code_safe

SANDBOX_DIR = Path("sandbox/temp_exec")

def run_python_code(code: str, timeout: int = 5):

    # 1️⃣ Safety check
    if not is_code_safe(code):
        return {
            "status": "rejected",
            "reason": "Blocked pattern detected."
        }

    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

    file_path = SANDBOX_DIR / "script.py"
    file_path.write_text(code)

    try:
        result = subprocess.run(
            [sys.executable, "script.py"],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=SANDBOX_DIR
        )

        return {
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "reason": "Execution exceeded time limit."
        }