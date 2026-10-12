#!/bin/sh
set -eu

CODE_PATH="${CODE_PATH:-/sandbox/code.py}"
CALLBACK_URL="${CALLBACK_URL:-}"
EXECUTION_TIMEOUT="${EXECUTION_TIMEOUT:-30}"

if [ -z "$CALLBACK_URL" ]; then
  echo "CALLBACK_URL is required" >&2
  exit 2
fi

python - <<'PY'
import json
import os
import subprocess
import urllib.request

code_path = os.environ.get("CODE_PATH", "/sandbox/code.py")
callback_url = os.environ["CALLBACK_URL"]
timeout = int(os.environ.get("EXECUTION_TIMEOUT", "30"))

result = {
    "stdout": "",
    "stderr": "",
    "exit_code": 1,
    "timed_out": False,
}

try:
    proc = subprocess.run(["python", code_path], capture_output=True, text=True, timeout=timeout, check=False)
    result["stdout"] = proc.stdout
    result["stderr"] = proc.stderr
    result["exit_code"] = proc.returncode
except subprocess.TimeoutExpired as exc:
    result["stdout"] = exc.stdout or ""
    result["stderr"] = (exc.stderr or "") + "\nExecution timed out"
    result["exit_code"] = 124
    result["timed_out"] = True
except Exception as exc:
    result["stderr"] = str(exc)

payload = json.dumps(result).encode("utf-8")
req = urllib.request.Request(callback_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=5):
    pass
PY
