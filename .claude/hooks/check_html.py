#!/usr/bin/env python3
"""
HOOK 4: Check the HTML after every change.

Runs AFTER Claude changes an .html file. It looks for broken tags,
like a <div> that was never closed or a </section> with no matching
opening tag. If it finds a problem, it tells Claude so it gets fixed
right away.
"""
import json
import os
import sys
from html.parser import HTMLParser

# Tags that never need a closing tag
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "source", "track", "wbr", "path", "circle", "rect", "line",
        "polyline", "polygon", "ellipse", "stop", "use"}
# Tags the browser lets you skip closing (we don't complain about these)
OPTIONAL_CLOSE = {"p", "li", "option", "tr", "td", "th", "dt", "dd"}


class TagChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []      # open tags waiting to be closed
        self.problems = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        pass  # self-closing like <br/> is fine

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        # Close any optional-close tags sitting on top
        while self.stack and self.stack[-1][0] != tag and self.stack[-1][0] in OPTIONAL_CLOSE:
            self.stack.pop()
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
        else:
            line = self.getpos()[0]
            expected = self.stack[-1] if self.stack else None
            if expected:
                self.problems.append(
                    f"line {line}: found </{tag}> but <{expected[0]}> from line {expected[1]} is still open")
            else:
                self.problems.append(f"line {line}: found </{tag}> with no matching opening tag")


data = json.load(sys.stdin)
path = data.get("tool_input", {}).get("file_path", "")

if not path.endswith(".html") or not os.path.exists(path):
    sys.exit(0)

with open(path, encoding="utf-8") as f:
    checker = TagChecker()
    checker.feed(f.read())

for tag, line in checker.stack:
    if tag not in OPTIONAL_CLOSE:
        checker.problems.append(f"<{tag}> opened on line {line} is never closed")

if checker.problems:
    # Exit code 2 after a change = tell Claude about the problem so it fixes it
    print(f"HTML check found problems in {os.path.basename(path)}:\n- " +
          "\n- ".join(checker.problems[:10]), file=sys.stderr)
    sys.exit(2)

sys.exit(0)
