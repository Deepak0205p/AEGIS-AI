import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from backend.sandbox import execute_python_sandbox

code_sample = """
import sys
import math

print("=== SANDBOX EXECUTION START ===")
print("Python version:", sys.version.split()[0])
print("Factorial of 6:", math.factorial(6))
print("Array computation:", [x**2 for x in range(5)])
print("=== SANDBOX EXECUTION SUCCESS ===")
"""

print("[1] Running code in sandbox engine...")
result = execute_python_sandbox(code_sample)
print("\n[2] Execution Result:")
print(json.dumps(result, indent=2))

assert result["success"] is True, "Sandbox execution failed!"
assert "Factorial of 6: 720" in result["stdout"], "Expected output not found in stdout!"
print("\n[OK] Sandbox executed code successfully and verified stdout!")
