from sandbox.runner import run_python_code

test_code = """
while True:
    pass
"""

result = run_python_code(test_code)
print(result)