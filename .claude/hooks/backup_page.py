#!/usr/bin/env python3
"""
HOOK 3: Back up the page before every change.

Runs BEFORE Claude changes index.html. It saves a copy in
.claude/backups/ with the date and time in the name, so you can always
go back. Only the newest 20 copies are kept.
"""
import json
import os
import shutil
import sys
from datetime import datetime

KEEP = 20  # how many backups to keep

data = json.load(sys.stdin)
path = data.get("tool_input", {}).get("file_path", "")

# Only back up the landing page, and only if it already exists
if os.path.basename(path) != "index.html" or not os.path.exists(path):
    sys.exit(0)

project = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(os.path.abspath(path))
backup_dir = os.path.join(project, ".claude", "backups")
os.makedirs(backup_dir, exist_ok=True)

stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
shutil.copy2(path, os.path.join(backup_dir, f"index_{stamp}.html"))

# Delete the oldest backups so the folder doesn't grow forever
backups = sorted(f for f in os.listdir(backup_dir) if f.startswith("index_"))
for old in backups[:-KEEP]:
    os.remove(os.path.join(backup_dir, old))

sys.exit(0)
