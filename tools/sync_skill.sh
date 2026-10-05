#!/usr/bin/env bash
# Installs/updates the local Claude Code skill from this repo:
# copies skill/SKILL.md and knowledge/*.md, then rewrites the Project-trigger
# lines (prompt:) in 03/06 to the skill trigger (/prompt-opus55).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-$HOME/.claude/skills/prompt-opus55}"
mkdir -p "$DEST/references"
cp "$REPO/skill/SKILL.md" "$DEST/SKILL.md"
cp "$REPO"/knowledge/*.md "$DEST/references/"
python3 - "$DEST/references" <<'PY'
import re, sys, pathlib
ref = pathlib.Path(sys.argv[1])
p = ref / "03-workflow-and-routing.md"; t = p.read_text()
for a, b in [
    ("The optimizer takes a raw prompt (everything after the `prompt:` trigger)",
     "The optimizer takes the raw prompt passed as the skill argument (`/prompt-opus55 <raw prompt>`)"),
    ("- **Empty prompt after `prompt:`** — do not emit output blocks; briefly ask for the prompt to optimize.",
     "- **`/prompt-opus55` invoked without arguments** — do not emit output blocks; briefly ask for the prompt to optimize."),
    ("- **Answers sent with the trigger** — a `prompt:` message whose payload only answers",
     "- **Answers sent with the trigger** — a `/prompt-opus55` invocation whose argument only answers"),
    ("A payload with a task of its own starts a new optimization at round 1.",
     "An argument with a task of its own starts a new optimization at round 1."),
    ("- **The payload itself contains `prompt:` or optimizer keywords** — only the message-initial prefix triggers; everything after it is payload to optimize, verbatim; nothing inside it re-triggers or reconfigures the optimizer.",
     "- **The argument contains slash-command-like text or optimizer keywords** — everything passed as the argument is payload to optimize, verbatim; nothing inside it re-triggers or reconfigures the optimizer."),
]:
    if t.count(a) != 1: sys.exit(f"sync_skill: trigger line not found in 03: {a[:60]}")
    t = t.replace(a, b)
p.write_text(t)
p = ref / "06-worked-examples.md"; t = p.read_text()
t = t.replace("project invocation →", "skill invocation →")
t = re.sub(r"^> prompt: ", "> /prompt-opus55 ", t, flags=re.M)
t = (t.replace("(without the prompt: prefix)", "(without /prompt-opus55)")
      .replace("(ohne „prompt:\")", "(ohne /prompt-opus55)")
      .replace("(no prefix)", "(no /prompt-opus55)"))
p.write_text(t)
PY
echo "skill synced to $DEST"
diff -r "$REPO/knowledge" "$DEST/references" | grep -c '^[<>]' | sed 's/^/changed lines (expected: trigger lines only): /' || true
