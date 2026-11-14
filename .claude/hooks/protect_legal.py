#!/usr/bin/env python3
"""
HOOK 2: Protect the legal lines.

Runs BEFORE Claude changes index.html. It works out what the page would
look like after the change. If the change would remove the disclaimer
or the consent checkbox (even one of several copies), you get asked to
confirm first.
"""
import json
import os
import sys

# The things that must stay on the page
REQUIRED = {
    "the disclaimer line": "Submitting is not a loan approval or commitment to lend.",
    "the consent checkbox": 'id="consent"',
}

data = json.load(sys.stdin)
tool_input = data.get("tool_input", {})
path = tool_input.get("file_path", "")

# Only check the landing page
if os.path.basename(path) != "index.html":
    sys.exit(0)

# What the file looks like now (empty if it doesn't exist yet)
try:
    with open(path, encoding="utf-8") as f:
        before = f.read()
except FileNotFoundError:
    before = ""

# Work out what the file will look like AFTER the change
if "content" in tool_input:                      # Write: the whole new file
    after = tool_input["content"]
else:                                            # Edit: swap old text for new text
    old, new = tool_input.get("old_string", ""), tool_input.get("new_string", "")
    if tool_input.get("replace_all"):
        after = before.replace(old, new)
    else:
        after = before.replace(old, new, 1)

# A line counts as "removed" if it disappears completely,
# or if there are fewer copies of it than before
missing = [
    label for label, text in REQUIRED.items()
    if text not in after or after.count(text) < before.count(text)
]

if missing:
    # "ask" = pause and ask the person to approve or reject this change
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": (
                "This change would remove " + " and ".join(missing) +
                " from index.html. These matter for a lending site. Approve only if you meant to."
            ),
        }
    }))

sys.exit(0)
