#!/usr/bin/env python3
"""
HOOK 1: Block secret keys.

Runs BEFORE Claude writes or edits any file. If the new text contains
something that looks like a secret key (like a 21st.dev key), the save
is blocked, so a key can never end up in your project or on GitHub.
"""
import json
import re
import sys

# Patterns that look like secret keys. Add more here if you use other services.
SECRET_PATTERNS = {
    "21st.dev API key": r"21st_sk_[A-Za-z0-9]{16,}",
    "Anthropic API key": r"sk-ant-[A-Za-z0-9_\-]{20,}",
    "OpenAI-style API key": r"\bsk-[A-Za-z0-9]{32,}",
    "GitHub token": r"\b(ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}",
    "AWS access key": r"\bAKIA[0-9A-Z]{16}\b",
    "Stripe secret key": r"\b(sk|rk)_live_[A-Za-z0-9]{16,}",
    "Private key file": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
}

data = json.load(sys.stdin)
tool_input = data.get("tool_input", {})

# "Write" sends the whole file as "content"; "Edit" sends the new part as "new_string"
new_text = (tool_input.get("content") or "") + "\n" + (tool_input.get("new_string") or "")

for name, pattern in SECRET_PATTERNS.items():
    if re.search(pattern, new_text):
        # Exit code 2 = block the save. The message goes back to Claude.
        print(
            f"Blocked: this change contains what looks like a {name}. "
            "Secret keys must never be saved into project files. "
            "Remove the key and keep it in the secure credential settings instead.",
            file=sys.stderr,
        )
        sys.exit(2)

sys.exit(0)
