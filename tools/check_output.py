#!/usr/bin/env python3
"""Format checks for one reply of the Opus 5.5 prompt optimizer.

Parses the reply's first fenced code block (the optimized prompt) and the
<parameters>, <score>, <changes> and <open_questions> blocks, then checks them
against the output contract (knowledge/04-output-templates.md), the Phase 4
quality gate (knowledge/03-workflow-and-routing.md) and the round rules
(knowledge/07-scoring.md, "Follow-up rounds"). Works for the skill and the
Project variant. Semantic judgment (routing, sensible changes, minimal diff,
question quality) is left to a human reader.

CLI:  python3 tools/check_output.py OUTPUT.md [--target api|chat] [--round N]
          [--lang en|de] [--expect-no-blocks] [--json]
Each check is a named finding: PASS, FAIL, WARN, INFO or SKIP.
Exit code 1 if any check FAILs; WARN/INFO never fail.
"""
import argparse, json, pathlib, re, sys

BLOCKS = ("parameters", "score", "changes", "open_questions")
DIM_MAX = {"A": 25, "B": 15, "C": 15, "D": 20, "E": 15, "F": 10}
RULE_MAX = 54
MINUS = "[−–-]"  # unicode minus, en dash, hyphen

# <parameters>: settings that return HTTP 400 on Opus 5.5 (R10/R35/R36/R37/R44)
FORBIDDEN_PARAMS = {
    "temperature": r"\btemperature\b",
    "top_p": r"\btop_p\b",
    "top_k": r"\btop_k\b",
    "budget_tokens": r"\bbudget_tokens\b",
    "thinking disabled": r"[\"']disabled[\"']|\bthinking\b[^\n]*\bdisabled\b",
    'tool_choice type "tool"': r"\btype[\"']?\s*:\s*[\"']?tool\b",
    'tool_choice "any"': r"\btype[\"']?\s*:\s*[\"']?any\b|\btool_choice[\"']?\s*:\s*[\"']?any\b",
    "computer_20251124": r"computer_20251124",
    "prefill": r"\bprefill",
}
# <parameters> fields: required by the Phase 4 gate / listed in the 04 template (field: pattern);
# display sits on the thinking line ("display stays \"omitted\"" or {type: "adaptive", display: …})
PARAM_FIELD = {k: r"(?:^|[\s·.;(])%s\s*:" % k for k in
               ("model", "effort", "max_tokens", "streaming", "thinking", "tool_choice", "fallbacks", "caching",
                "task_budget", "extras")}
PARAM_FIELD.update({"display": r"\bdisplay\b", "output_config.format": r"\b(?:output_config\.format|output_format)\s*:"})
PARAM_GATE = ("model", "effort", "max_tokens", "streaming", "display", "fallbacks")
PARAM_TEMPLATE = PARAM_GATE + ("thinking", "tool_choice", "output_config.format", "caching", "task_budget", "extras")
# a forbidden name on a line with one of these cues is a warning, not a recommendation
NEGATION = re.compile(r"\b(never|not|no|don't|do not|without|removed?|dropped?|stripped?|avoid|instead of|"
                      r"replaces?|takes over|400|nicht|kein\w*|ohne|entfernt|weder|ersetzt)\b", re.I)
CAPS_TRIGGERS = r"\b(CRITICAL|MUST|IMPORTANT|NEVER|ALWAYS|REQUIRED|WICHTIG|MUSS|MUSST|NIEMALS|IMMER|KRITISCH)\b"
MANUAL_COT = (r"\bthink(?:ing)?\b[^.\n]{0,25}\bstep[- ]by[- ]step|\blet'?s think\b|"
              r"\bdenk\w*\b[^.\n]{0,40}Schritt für Schritt|Schritt für Schritt\s+(?:nach|durch)\w*denk")
REASONING_FIELD = (r"[\"']?\b(reasoning|thinking|thought_process|chain_of_thought|trace|scratchpad)\b[\"']?\s*:\s*"
                   r"(?:[\"'{\[]|string\b|str\b|text\b|\.\.\.|…)")
REASONING_TAG = r"</?(thinking|reasoning|scratchpad)>"
GAIN_TAG = (r"\+~\s*\d+(?:\s*(?:–|-|to|bis)\s*\+?~?\s*\d+)?\s+(?:points?|Punkte?)\s*,?\s+"
            r"(?:if answered|wenn beantwortet|falls beantwortet)")
ZERO_TAG = r"\+0\s+(?:points?|Punkte?)\s*[(—–,:-]"
ANSWER_LINE = r"normal(?:en)?\s+(?:message|Nachricht)"
TRIGGER_MENTION = r"/prompt-opus55|\bprompt:|\bprefix\b|Präfix|\btrigger\b"
LAST_ROUND = (r"last (?:round of questions|question round|round of question)|final (?:round of questions|question round)|"
              r"letzte (?:Fragerunde|Runde)|no (?:further|more) questions|keine weiteren Fragen")
ASSUMPTION = r"\((?:assumption|Annahme)\)"
BRACKET_GAP = r"(?<![\w\]])\[([A-Za-zÄÖÜäöü„][^\[\]\n]{1,160})\](?!\()"  # [name], [e.g., …]; not links or arrays
NONE_MARKER = r"^[-*•]\s*(?:none|no (?:open |further |more )?questions|keine(?: weiteren| offenen)? Fragen)\b"

STOP_DE = set("der die das und ist nicht mit für auf ein eine einen einem einer zu den dem des sich von auch wie oder "
              "wenn du dein deine deinen ich wir es im bei aus nach über unser unsere unseren sie werden wird sind dass "
              "als nur noch kein keine bitte dann diese dieser dieses jede jeden jeder zum zur vom schreib schreibe gib "
              "nenne soll sollen kann können".split())
STOP_EN = set("the and is are not with for on a to of that this it as be you your we our or if from by at each what "
              "which when do don't only than then should would use write give keep make they their there these those "
              "into about".split())
GERMAN_TAG_WORDS = set("rolle kontext aufgabe aufgaben anweisung anweisungen beispiel beispiele dokument dokumente "
                       "eingabe ausgabe ziel ziele zielgruppe hintergrund regeln grenzen stil ton daten quelle quellen "
                       "nachricht frage fragen antwort antworten kriterien umfang vorgaben ergebnis zusammenfassung "
                       "produkt produktdaten beschreibung inhalt inhalte eingefuegt eingefügt stilvorlage vorlage technische "
                       "angaben hinweise anforderungen aufgabenstellung bericht vorgabe".split())


class Findings:
    def __init__(self):
        self.items = []

    def add(self, name, ok, detail="", level="FAIL"):
        self.items.append({"name": name, "status": "PASS" if ok else level, "detail": detail})

    def info(self, name, detail):
        self.items.append({"name": name, "status": "INFO", "detail": detail})

    def skip(self, name, detail):
        self.items.append({"name": name, "status": "SKIP", "detail": detail})

    @property
    def failed(self):
        return [f for f in self.items if f["status"] == "FAIL"]


def short(s, n=70):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def parse_fence(text):
    """First fenced code block (CommonMark: closing fence >= opening length)."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        m = re.match(r"^ {0,3}(`{3,}|~{3,})\s*([^\s`]*)[^`]*$", line)
        if not m:
            continue
        mark = m.group(1)
        close = re.compile(r"^ {0,3}" + re.escape(mark[0]) + "{" + str(len(mark)) + r",}\s*$")
        for j in range(i + 1, len(lines)):
            if close.match(lines[j]):
                return {"leading": "\n".join(lines[:i]), "info": m.group(2), "body": "\n".join(lines[i + 1:j]),
                        "after": "\n".join(lines[j + 1:])}
        return {"leading": "\n".join(lines[:i]), "info": m.group(2), "body": "\n".join(lines[i + 1:]),
                "after": "", "unclosed": True}
    return None


def find_blocks(text):
    """{name: (start, end, inner)} for each output block found in text."""
    out = {}
    for name in BLOCKS:
        m = re.search(r"<%s>(.*?)</%s>" % (name, name), text, re.S)
        if m:
            out[name] = (m.start(), m.end(), m.group(1))
        elif re.search(r"<%s>" % name, text):
            out[name] = (text.index("<%s>" % name), len(text), text.split("<%s>" % name, 1)[1])
            out[name] += ("unclosed",)
    return out


def entries(block):
    """Split a block into bullet entries (with continuation lines) and free-text lines."""
    items, free, cur, indent, top = [], [], None, 0, None
    for line in block.split("\n"):
        m = re.match(r"^(\s*)(?:[-*•]|\d+[.)])\s+", line)
        if m and cur is not None and top is not None and len(m.group(1)) > top:
            cur.append(line.strip())          # sub-bullet: part of the current entry
        elif m:
            cur, indent = [line.strip()], len(m.group(1))
            top = indent if top is None else min(top, indent)
            items.append(cur)
        elif line.strip() and cur is not None and len(line) - len(line.lstrip()) > indent:
            cur.append(line.strip())
        elif line.strip():
            cur = None
            free.append(line.strip())
    return [" ".join(e) for e in items], free


def lang_share(text, lang):
    words = re.findall(r"[a-zäöüß']+", text.lower())
    de = sum(w in STOP_DE for w in words)
    en = sum(w in STOP_EN for w in words)
    hits = de + en
    return (de if lang == "de" else en) / hits if hits else None, hits


def prompt_text(body):
    """Fence body without XML tags, placeholders and HTML comments (for language checks)."""
    t = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
    t = re.sub(r"</?[A-Za-z_][\w.-]*(?:\s[^>]*)?>", " ", t)
    return re.sub(r"\{\{[^}]*\}\}", " ", t)


def check(text, target=None, rnd=1, lang="en", expect_no_blocks=False):
    f = Findings()
    parsed = {"chars": len(text)}
    f.add("nonempty", bool(text.strip()), "reply is empty (technical error?)")
    if not text.strip():
        return f, parsed

    if expect_no_blocks:
        present = [b for b in BLOCKS if "<%s>" % b in text]
        f.add("no_blocks", not present, "blocks present: " + ", ".join(present))
        fence = parse_fence(text)
        if fence and not fence["leading"].strip():
            f.add("no_prompt_fence_first", False, "reply opens with a fenced block", level="WARN")
        f.info("reply", "%d chars, %d lines; starts: %s" % (len(text), text.count("\n") + 1, short(text, 90)))
        return f, parsed

    # 1. the optimized prompt: first, alone, followed directly by a block
    fence = parse_fence(text)
    if not fence:
        f.add("fence_present", False, "no fenced code block")
        return f, parsed
    body = fence["body"]
    parsed["prompt_chars"] = len(body)
    f.add("fence_first", not fence["leading"].strip(), "text before the fence: " + short(fence["leading"]))
    f.add("fence_closed", not fence.get("unclosed"), "fence never closed")
    f.add("fence_info_text", fence["info"] == "text", "info string is %r, template uses 'text'" % fence["info"],
          level="WARN")
    inside = [t for t in ("<score>", "<changes>", "<open_questions>", "<parameters>") if t in body]
    if re.search(r"^\s*total:\s*\d+\s*(?:→\s*\d+\s*)?/100", body, re.M):
        inside.append("total: …/100")
    f.add("fence_prompt_only", not inside, "inside the fence: " + ", ".join(inside))
    after = fence["after"]
    first = next((l.strip() for l in after.split("\n") if l.strip()), "")
    f.add("fence_followed_by_block", any(first.startswith("<%s>" % b) for b in BLOCKS),
          "after the fence comes: " + short(first or "(nothing)"))

    # 2. blocks outside the fence: presence, order, stray text
    blocks = find_blocks(after)
    parsed["blocks"] = list(blocks)
    for name, b in blocks.items():
        if len(b) > 3:
            f.add("block_closed_" + name, False, "<%s> never closed" % name)
    order = sorted(blocks, key=lambda n: blocks[n][0])
    f.add("block_order", order == [b for b in BLOCKS if b in blocks], "order: " + " → ".join(order))
    if blocks:
        spans = sorted((b[0], b[1]) for b in blocks.values())
        between = [after[spans[k][1]:spans[k + 1][0]].strip() for k in range(len(spans) - 1)]
        between = [s for s in between if s]
        f.add("text_between_blocks", not between, "; ".join(short(s, 50) for s in between), level="WARN")
        trailing = after[spans[-1][1]:].strip()
        f.add("no_trailing_text", not trailing, "after the last block: " + short(trailing, 90), level="WARN")
    for name in ("score", "changes"):
        f.add("block_" + name, name in blocks, "<%s> missing" % name)

    # 3. <parameters> iff API target
    has_params = "parameters" in blocks
    if target:
        f.add("parameters_iff_api", has_params == (target == "api"),
              "%s target but <parameters> %s" % (target, "present" if has_params else "missing"))
    else:
        f.info("target_inferred", "api (parameters present)" if has_params else "chat (no parameters)")
    if has_params:
        p = blocks["parameters"][2]
        f.add("param_model", re.search(r"\bmodel:\s*(?:anthropic\.)?claude-opus-5-5\b", p),
              "no 'model: claude-opus-5-5'")
        m = re.search(r"\beffort:\s*[\"']?(low|medium|high|xhigh|max)\b", p, re.I)
        parsed["effort"] = m.group(1).lower() if m else None
        f.add("param_effort_explicit", m, "no explicit 'effort: <level>'")
        keys = {k for k in PARAM_TEMPLATE if re.search(PARAM_FIELD[k], p, re.M)}
        gate = [k for k in PARAM_GATE if k not in keys]
        rest = [k for k in PARAM_TEMPLATE if k not in keys and k not in PARAM_GATE]
        f.add("param_fields_gate", not gate, "missing gate field(s): " + ", ".join(gate))
        f.add("param_fields_template", not rest, "missing template field(s): " + ", ".join(rest), level="WARN")
        hard, soft = [], []
        # one entry per parameter field: continuation lines (deeper indent) belong to the field above,
        # so a negation that wrapped onto the previous line still counts
        fields = []
        for line in p.split("\n"):
            if fields and line.strip() and (len(line) - len(line.lstrip())) > (len(fields[-1]) - len(fields[-1].lstrip())):
                fields[-1] += " " + line.strip()
            else:
                fields.append(line)
        for line in fields:
            for label, pat in FORBIDDEN_PARAMS.items():
                if re.search(pat, line, re.I):
                    (soft if NEGATION.search(line) else hard).append("%s (%s)" % (label, short(line, 60)))
        f.add("param_no_forbidden", not hard, "; ".join(hard))
        f.add("param_forbidden_mentions", not soft, "named in a negated context: " + "; ".join(soft), level="WARN")
        schema = "\n".join(l for l in p.split("\n") if re.search(r"output_format|output_config|schema", l, re.I))
        rf = re.findall(REASONING_FIELD, schema, re.I)
        f.add("param_no_reasoning_field", not rf, "schema field(s): " + ", ".join(sorted(set(rf))))

    # 4. <score>: total, six dimensions, arithmetic, progression, deductions
    if "score" in blocks:
        s = blocks["score"][2]
        m = re.search(r"total:\s*(?:(\d+)\s*(?:→|->)\s*)?(\d+)\s*/\s*100([^\n]*)", s)
        if not m:
            f.add("score_total_parsed", False, "no 'total: n/100' line")
        else:
            old, new, tail = (int(m.group(1)) if m.group(1) else None), int(m.group(2)), m.group(3)
            parsed.update(score_old=old, score=new)
            d = re.search(r"\(\s*(" + MINUS + r"|\+|±)\s*(\d+)\b[^)]*\)", tail)
            if old is not None:
                f.add("score_progression_delta", d, "progression without '(+d from your answers)'")
                if d:
                    delta = int(d.group(2)) * (-1 if re.match(MINUS, d.group(1)) else 1)
                    parsed["score_delta"] = delta
                    f.add("score_progression_arithmetic", old + delta == new, "%d %+d != %d" % (old, delta, new))
            if rnd >= 2:
                f.add("score_progression", old is not None, "round %d without 'old → new/100' progression" % rnd)
            elif old is not None:
                f.add("score_no_progression_r1", False, "round 1 shows a progression", level="WARN")
            dims = {}
            for letter, val, mx in re.findall(r"\b([A-F])\s+[^:\n·]{1,25}?:\s*(\d+)\s*/\s*(\d+)", s):
                dims.setdefault(letter, (int(val), int(mx)))
            parsed["dims"] = {k: v[0] for k, v in sorted(dims.items())}
            missing = [k for k in DIM_MAX if k not in dims]
            f.add("score_dimensions_parsed", not missing, "missing dimension(s): " + ", ".join(missing))
            bad = ["%s %d/%d" % (k, v, mx) for k, (v, mx) in dims.items() if mx != DIM_MAX[k] or not 0 <= v <= mx]
            f.add("score_dimension_max", not bad, "outside maxima: " + ", ".join(bad))
            if not missing:
                total = sum(v for v, _ in dims.values())
                f.add("score_sum", total == new, "dimensions sum to %d, total says %d" % (total, new))
            # deduction lines "X: finding (Rn): −k; …" must cite rules and match the dimension value
            ded, cur = {}, None
            for line in s.split("\n"):
                mm = re.match(r"^\s*([A-F]):\s", line)
                if mm:
                    cur = mm.group(1)
                    ded.setdefault(cur, []).append(line)
                elif cur and line.strip() and not re.search(r"\b[A-F]\s+\w+:\s*\d+\s*/", line):
                    ded[cur].append(line)
            uncited, mismatch = [], []
            for k, lines in ded.items():
                t = " ".join(lines)
                pts = [int(x) for x in re.findall(r":\s*" + MINUS + r"\s*(\d+)\b", t)]
                if pts and not re.search(r"\bR\d+\b", t):
                    uncited.append(k)
                if k in dims and pts and sum(pts) != DIM_MAX[k] - dims[k][0]:
                    mismatch.append("%s: −%d listed, %d/%d shown" % (k, sum(pts), dims[k][0], DIM_MAX[k]))
            unexplained = [k for k, (v, mx) in dims.items() if v < mx and k not in ded]
            f.add("score_deductions_cite_rules", not uncited, "deduction line(s) without R<n>: " + ", ".join(uncited))
            f.add("score_deductions_match", not mismatch and not unexplained,
                  "; ".join(mismatch + ["%s deducted without a finding line" % k for k in unexplained]))

    # 5. <changes>: every entry cites R1–R54
    rule_refs = [int(n) for n in re.findall(r"\bR(\d+)\b", after)]
    out_of_range = sorted({n for n in rule_refs if not 1 <= n <= RULE_MAX})
    f.add("rule_refs_in_range", not out_of_range, "cites " + ", ".join("R%d" % n for n in out_of_range))
    if "changes" in blocks:
        ch, _ = entries(blocks["changes"][2])
        parsed["n_changes"] = len(ch)
        f.add("changes_nonempty", ch, "no entries in <changes>")
        nocite = [short(e, 60) for e in ch if not re.search(r"\bR\d+\b|\(Phase 0\)", e)]
        f.add("changes_cite_rules", not nocite, "%d entr%s without R<n>: %s" % (
            len(nocite), "y" if len(nocite) == 1 else "ies", " | ".join(nocite)))
        if rnd >= 2:  # 04: no recap of kept round-1 changes and no separate "Round 2: …" entry
            recap = [short(e, 60) for e in ch if re.search(
                r"\b(kept|keep|retained|unchanged)\b.{0,30}\b(all |the )?(round[- ]?1|earlier|previous|first[- ]round)\b.{0,20}\b(fix|change|edit)"
                r"|^(this is )?round [23]\b|\b(behalten|beibehalten)\b.{0,40}\b(Runde 1|ersten Runde)", e, re.I)]
            f.add("changes_no_recap", not recap, "recap/round entr%s: %s" % ("y" if len(recap) == 1 else "ies", " | ".join(recap)), level="WARN")
        parsed["assumptions"] = len(re.findall(ASSUMPTION, blocks["changes"][2]))

    # 6. <open_questions>: ≤ 3 tagged entries + how-to-answer line
    if "open_questions" in blocks:
        oq = blocks["open_questions"][2]
        qs, free = entries(oq)
        markers = [q for q in qs if re.match(NONE_MARKER, q, re.I)]
        qs = [q for q in qs if q not in markers]
        f.add("questions_no_none_bullet", not markers, "placeholder bullet instead of a question: " +
              " | ".join(short(m, 60) for m in markers), level="WARN")
        parsed["n_questions"] = len(qs)
        free_text = " ".join(free)
        f.add("questions_max3", len(qs) <= 3, "%d questions" % len(qs))
        untagged = [short(q, 60) for q in qs if not re.search(GAIN_TAG + "|" + ZERO_TAG, q, re.I)]
        f.add("questions_tagged", not untagged, "untagged: " + " | ".join(untagged))
        has_line = re.search(ANSWER_LINE, free_text, re.I)
        if not has_line and re.search(ANSWER_LINE, oq, re.I):
            f.add("answer_line", False, "how-to-answer text sits inside a question entry", level="WARN")
        else:
            f.add("answer_line", has_line or (rnd >= 3 and not qs), "no 'reply in a normal message' line")
        if has_line:
            f.add("answer_line_prefix", re.search(TRIGGER_MENTION, free_text, re.I),
                  "answer line does not say to leave out the trigger (/prompt-opus55 or prompt:)")
        if rnd == 2:
            f.add("last_question_round", re.search(LAST_ROUND, oq, re.I), "round 2 not marked as the last question round")
    elif rnd <= 2:
        f.add("block_open_questions", False, "<open_questions> missing")
    if rnd >= 3:
        qs = [q for q in (entries(blocks["open_questions"][2])[0] if "open_questions" in blocks else [])
              if not re.match(NONE_MARKER, q, re.I)]
        f.add("r3_no_questions", not qs, "%d question(s) in round %d" % (len(qs), rnd))
        f.add("r3_assumption_marked", parsed.get("assumptions"), "no '(assumption)' in <changes>")
        if "open_questions" not in blocks:
            f.info("r3_open_questions_block", "absent")
        else:
            f.info("r3_open_questions_block", "present with %d entr%s; free text: %s" % (
                len(qs), "y" if len(qs) == 1 else "ies", short(" ".join(entries(blocks["open_questions"][2])[1]), 120)))

    # 7. the prompt text itself
    caps = sorted(set(re.findall(CAPS_TRIGGERS, body)))
    f.add("prompt_no_caps_triggers", not caps, "found: " + ", ".join(caps))
    cot = re.search(MANUAL_COT, body, re.I)
    f.add("prompt_no_manual_cot", not cot, "manual chain-of-thought phrasing: " + (cot.group(0) if cot else ""))
    loose = re.search(r"step[- ]by[- ]step|Schritt für Schritt|think carefully|denk\w* gründlich", body, re.I)
    f.add("prompt_no_stepwise_phrasing", not loose or cot, "phrase: " + (loose.group(0) if loose else ""), level="WARN")
    rf = sorted(set(re.findall(REASONING_FIELD, body, re.I)) | set(re.findall(REASONING_TAG, body, re.I)))
    f.add("prompt_no_reasoning_field", not rf, "reasoning field/tag: " + ", ".join(rf))
    # gate "works as pasted": [bracketed] gaps are listed for a human to judge ({{…}} slots are fine)
    gaps = [g for g in re.findall(BRACKET_GAP, body) if '":' not in g]
    parsed["bracket_gaps"] = len(gaps)
    f.add("prompt_bracket_gaps", not gaps, "%d [bracketed] gap(s): %s" % (
        len(gaps), " | ".join("[" + short(g, 50) + "]" for g in gaps[:6])), level="WARN")

    # 8. language: prompt text in the input language, XML tag names English
    plain = prompt_text(body)
    share, hits = lang_share(plain, lang)
    parsed["lang_share"] = round(share, 2) if share is not None else None
    if share is None or hits < 10:
        f.skip("lang_prompt", "too few stop words to judge (%d)" % hits)
    else:
        f.add("lang_prompt", share >= 0.7, "%s share of stop words %.2f (< 0.70)" % (lang, share))
        off = []
        for para in re.split(r"\n\s*\n", plain):
            ps, ph = lang_share(para, lang)
            if ps is not None and ph >= 12 and ps < 0.4:
                off.append(short(para, 50))
        f.add("lang_paragraphs", not off, "paragraph(s) in another language: " + " | ".join(off))
    if lang != "en":
        tags = sorted(set(re.findall(r"</?([A-Za-z_À-ÿ][\wÀ-ÿ.-]*)", body)))
        german = [t for t in tags if re.search(r"[äöüßÄÖÜ]", t)
                  or any(part in GERMAN_TAG_WORDS for part in re.split(r"[_.-]", t.lower()))]
        f.add("lang_tags_english", not german, "non-English tag names: " + ", ".join(german))
    return f, parsed


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("output", help="optimizer reply (markdown/text file)")
    ap.add_argument("--target", choices=("api", "chat"), help="expected target; omit to infer")
    ap.add_argument("--round", type=int, default=1, help="answer round (1 = initial optimization)")
    ap.add_argument("--lang", choices=("en", "de"), default="en", help="language of the input prompt")
    ap.add_argument("--expect-no-blocks", action="store_true", help="empty input or meta question: no output blocks")
    ap.add_argument("--json", action="store_true", help="print machine-readable JSON")
    a = ap.parse_args()
    text = pathlib.Path(a.output).read_text()
    f, parsed = check(text, a.target, a.round, a.lang, a.expect_no_blocks)
    if a.json:
        print(json.dumps({"file": a.output, "target": a.target, "round": a.round, "lang": a.lang,
                          "expect_no_blocks": a.expect_no_blocks, "ok": not f.failed,
                          "findings": f.items, "parsed": parsed}, ensure_ascii=False, indent=1))
    else:
        print("check_output: %s (target=%s, round=%d, lang=%s%s)" % (
            a.output, a.target or "auto", a.round, a.lang, ", expect-no-blocks" if a.expect_no_blocks else ""))
        for it in f.items:
            detail = "" if it["status"] == "PASS" else "  " + it["detail"]
            print("  %-4s %s%s" % (it["status"], it["name"], detail))
        counts = {s: sum(i["status"] == s for i in f.items) for s in ("PASS", "FAIL", "WARN", "INFO", "SKIP")}
        print("\n" + " · ".join("%d %s" % (n, s.lower()) for s, n in counts.items() if n))
        print("PARSED:", json.dumps(parsed, ensure_ascii=False))
    sys.exit(1 if f.failed else 0)


if __name__ == "__main__":
    main()
