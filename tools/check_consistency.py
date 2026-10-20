#!/usr/bin/env python3
"""Consistency checks for the Opus 5.5 optimizer knowledge base.

Checks rule numbering and references, source codes, snippet structure,
verbatim snippets against archived raw sources (docs/research/sources, local
only; skipped if absent), score arithmetic, quality-gate count, and the
round/answer conventions in the worked examples. Exit code 1 on problems.
"""
import re, pathlib, sys
R = pathlib.Path(__file__).resolve().parent.parent
K = R/"knowledge"
files = {p.name: p.read_text() for p in sorted(K.glob("*.md"))}
extra = {p: (R/p).read_text() for p in ["README.md","project-instructions.md","skill/SKILL.md"]}
src = (R/"docs/research/sources")
problems = []

# 1. rules defined in 02
rules = files["02-prompting-rules.md"]
defined = sorted({int(m) for m in re.findall(r"^\*\*R(\d+) —", rules, re.M)})
print("defined rules:", len(defined), defined[0], "..", defined[-1])
if defined != list(range(1, 55)): problems.append(f"rule numbering gap: {set(range(1,55))-set(defined)}")

# 2. every cited rule exists
alltext = {**files, **extra}
for name, t in alltext.items():
    for m in re.findall(r"\bR(\d+)\b", t):
        if int(m) not in defined: problems.append(f"{name}: cites undefined R{m}")

# 3. every source code in the legend
legend = files["01-opus55-model-facts.md"].split("## What Opus 5.5 is")[0]
codes = set(re.findall(r"^\| \[(\w+)\]", legend, re.M))
print("legend codes:", len(codes))
for name, t in alltext.items():
    for c in set(re.findall(r"\[([A-Z][A-Za-z0-9]+)\]", t)):
        if c in {"DOCUMENTED","DERIVED","MEASURED","BELEGT","ABGELEITET"}: continue
        if c not in codes: problems.append(f"{name}: unknown source code [{c}]")
for name, t in alltext.items():
    for c in re.findall(r"DOCUMENTED: ([A-Za-z0-9, ]+)\]", t):
        for part in [x.strip() for x in c.split(",")]:
            part = part.split(" ")[0]
            if part and part not in codes and part != "source": problems.append(f"{name}: DOCUMENTED cites unknown '{part}'")

# 4. snippet sections name rule + source; numbering 1..24 consistent with table
sn = files["05-snippet-library.md"]
heads = re.findall(r"^## (\d+)\. (.+)$", sn, re.M)
print("snippets:", len(heads))
for n, h in heads:
    if not re.search(r"R\d+", h): problems.append(f"snippet {n} heading lacks rule")
    if not re.search(r"\[(PromptO5|PromptO55|BestPract|ThinkSteer|DERIVED)\]", h): problems.append(f"snippet {n} heading lacks source")
table_rows = re.findall(r"^\| (\d+) \| .+? \| (R[\d/R]+) \|", sn, re.M)
if [int(a) for a,_ in table_rows] != list(range(1, len(heads)+1)): problems.append("snippet table numbering mismatch")
for (a, r), (n, h) in zip(table_rows, heads):
    if r.split("/")[0] not in h: problems.append(f"snippet {n}: table rule {r} not in heading")
# snippet references "snippet N" elsewhere must exist
for name, t in alltext.items():
    for m in re.findall(r"snippet (\d+)", t):
        if int(m) > len(heads): problems.append(f"{name}: references missing snippet {m}")

# 5. verbatim snippets present in raw sources
srcmap = {"PromptO5":"PromptO5.md","PromptO55":"PromptO55.md","BestPract":"BestPract.md","ThinkSteer":"ThinkSteer.md"}
blocks = re.split(r"^## \d+\. ", sn, flags=re.M)[1:]
for b in blocks:
    head = b.splitlines()[0]
    m = re.search(r"\[(PromptO55|PromptO5|BestPract|ThinkSteer)\] verbatim", head)
    if not m: continue
    if not (src/srcmap[m.group(1)]).exists(): continue
    s = (src/srcmap[m.group(1)]).read_text()
    norm = lambda x: re.sub(r"\s+", " ", x).strip()
    ns = norm(s)
    for code in re.findall(r"```text\n(.*?)```", b, re.S):
        lines = [l for l in code.splitlines() if l.strip()]
        # snippet 16 mixes labels; check each phrase after a colon label
        chunks = [norm(code)]
        if "Encourage" in code:
            chunks = ["Please think hard before responding.", "Answer directly without deliberating.",
                      norm("Extended thinking adds latency and should only be used when it will meaningfully improve answer quality, typically for problems that require multistep reasoning. When in doubt, respond directly.")]
        for c in chunks:
            if c not in ns: problems.append(f"snippet '{head[:40]}' not verbatim in {srcmap[m.group(1)]}: {c[:70]}")

# 6. scoring maxima and worked-example sums
sc = files["07-scoring.md"]
pts = [int(x) for x in re.findall(r"\| \*\*(\d+)\*\* \|", sc)]
print("dimension points:", pts, sum(pts[:-1]) if len(pts)>6 else sum(pts))
def check_score(block, label):
    mp = re.search(r"total: (\d+) → (\d+)/100 \(\+(\d+) from your answers\)", block)
    if mp and int(mp.group(1))+int(mp.group(3)) != int(mp.group(2)): problems.append(f"{label}: progression arithmetic")
    m = re.search(r"total: (?:\d+ → )?(\d+)/100.*?A structure: (\d+)/25 · B thinking: (\d+)/15 · C verbosity: (\d+)/15 ·\s*D agentics: (\d+)/20 · E parameters: (\d+)/15 · F legacy: (\d+)/10", block, re.S)
    if not m: problems.append(f"{label}: score block unparsable"); return
    tot, *dims = map(int, m.groups())
    if sum(dims) != tot: problems.append(f"{label}: dims {dims} sum {sum(dims)} != {tot}")
    else: print(f"{label}: {tot} ok")
ex = files["06-worked-examples.md"]
for i, part in enumerate(re.split(r"^## Example \d", ex, flags=re.M)[1:], 1):
    outs = re.findall(r"\*\*Optimizer output([^\n]*)\n(.*?)(?=\n\*\*(?:User reply|Commentary|Detection)|\Z)", part, re.S)
    if not outs: problems.append(f"example {i}: no optimizer output")
    for k, (head, body) in enumerate(outs, 1):
        label = f"example {i}.{k}"
        check_score(body, label)
        oq = re.search(r"<open_questions>(.*?)</open_questions>", body, re.S)
        n = len(re.findall(r"^\s*- ", oq.group(1), re.M)) if oq else 0
        if n > 3: problems.append(f"{label}: {n} open questions")
        if not oq or not re.search(r"(normal message|normalen Nachricht)", oq.group(1)): problems.append(f"{label}: no how-to-answer line")
        if "question round" in head:
            # question round: score and questions only, the draft held back (04)
            if not re.match(r"\s*```text\n<score>", body): problems.append(f"{label}: question round does not start with <score>")
            for blk in ["<changes>", "<parameters>", "<system>"]:
                if blk in body: problems.append(f"{label}: question round shows {blk}")
            if not re.search(r"\+~\d+ (points?|Punkte?)", oq.group(1) if oq else ""): problems.append(f"{label}: question round without a point-recovering question")
            if oq and not re.search(r"(follows|frei)", oq.group(1)): problems.append(f"{label}: question round does not say the prompt follows")
            continue
        # release: forbidden settings inside recommended parameters
        pm = re.search(r"<parameters>(.*?)</parameters>", body, re.S)
        if pm:
            p = pm.group(1)
            for bad in ["temperature", "budget_tokens", '"disabled"', 'type: "tool"', "computer_20251124", "computer_20250124"]:
                if bad in p: problems.append(f"{label}: parameters mention {bad}")
            if "claude-opus-5-5" not in p or "effort:" not in p: problems.append(f"{label}: model/effort missing")
        # fence contains only prompt (no <score> inside first fence)
        fm = re.match(r"\s*```text\n(.*?)\n```\n<", body, re.S)
        if not fm: problems.append(f"{label}: prompt fence not followed directly by a block")
        elif "<score>" in fm.group(1): problems.append(f"{label}: score inside fence")
# 07 worked example table total
m = re.search(r"\*\*Total\*\* \| \| \*\*−(\d+)\*\* \| \*\*(\d+)/100\*\*", sc)
print("07 worked example:", m.groups() if m else None)
if m and 100-int(m.group(1)) != int(m.group(2)): problems.append("07 worked example arithmetic")

# 7. quality gate item count vs README
qg = files["03-workflow-and-routing.md"].split("## Phase 4")[1].split("## Phase 5")[0]
n_qg = len(re.findall(r"^- \[ \]", qg, re.M)); print("quality gate items:", n_qg)
if f"{n_qg}-point checklist" not in extra["README.md"]: problems.append(f"README checklist count != {n_qg}")

# 8. transfer-marked rules count
transfer = re.findall(r"^\*\*R(\d+) —.*?DERIVED: transfer", rules, re.M)
print("transfer-marked rules:", transfer)
print("\nPROBLEMS:" if problems else "\nNO PROBLEMS", *problems, sep="\n")
sys.exit(1 if problems else 0)
