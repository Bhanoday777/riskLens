# sandbox/policies.py

import re

# Safe standard library whitelist
ALLOWED_IMPORTS = {
    "math",
    "heapq",
    "collections",
    "random",
    "itertools",
    "functools",
    "statistics",
    "string",
    "bisect",
    "sys",   # Allow sys now
}

# Dangerous patterns (always blocked)
BLOCKED_PATTERNS = [
    "import os",
    "import subprocess",
    "subprocess",
    "socket",
    "shutil",
    "pathlib",
    "requests",
    "eval(",
    "exec(",
    "__import__",
    "open(",
]


def imports_are_safe(code: str) -> bool:
    import_statements = re.findall(r"^\s*import (\w+)", code, re.MULTILINE)

    for module in import_statements:
        if module not in ALLOWED_IMPORTS:
            return False

    return True


def is_code_safe(code: str) -> bool:
    for pattern in BLOCKED_PATTERNS:
        if pattern in code:
            return False

    if not imports_are_safe(code):
        return False

    return True