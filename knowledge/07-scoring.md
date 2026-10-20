# Input-Prompt Scoring (0–100)

The score measures how Opus-5.5-conformant the **input prompt** is before optimization. 100 means "nothing to change." It is computed in Phase 1 (see `03-workflow-and-routing.md`) and emitted in the `<score>` block (format in `04-output-templates.md`). The score is a heuristic derived from rules R1–R54 — it is an editorial instrument of this optimizer, not an official Anthropic metric.

## Contents

- Derivation of the point distribution
- Dimension rubrics (deduction tables)
- Route and target applicability
- Score bands
- Open-question point estimates
- Worked example

## Derivation of the point distribution

The 100 points are distributed across the six rule groups of `02-prompting-rules.md`, with the same weights as the sister project for Fable 5 so scores stay comparable across the per-model optimizers. Three heuristics, applied in order:

1. **Rule count as the base:** groups with more rules cover more failure surface (A: 8, B: 6, C: 6, D: 12, E: 12, F: 10 rules).
2. **Severity adjustment:** violations that cause hard API errors or refusals (R9 reasoning reproduction → `reasoning_extraction`, billed and never retried; R10/R35–R37/R44 → HTTP 400) weigh more than style-level issues, because they break the prompt rather than merely weakening it. This boosts B and keeps E significant despite conditional applicability.
3. **Applicability damping:** groups that apply only to some routes/targets (D: routes L/XL; E: API target) are damped below their raw rule-count share, because on other routes their points are awarded by default and would otherwise dominate the scale. F is damped because it is deduction-only and overlaps with B/C cleanup findings.

| Dimension | Rules | Raw share by count | Adjustment | **Points** |
|---|---|---|---|---|
| **A — Structure & explicitness** | R1–R8 | 8/54 ≈ 15% | boosted: foundational, applies to every route | **25** |
| **B — Thinking & reasoning safety** | R9–R14 | 6/54 ≈ 11% | boosted: contains the highest-severity anti-pattern (R9) | **15** |
| **C — Verbosity, communication & format** | R15–R20 | 6/54 ≈ 11% | slightly boosted: applies to every route | **15** |
| **D — Agentics & harness behavior** | R21–R32 | 12/54 ≈ 22% | damped: routes L/XL (and code-review tasks) only | **20** |
| **E — Parameters & refusal handling** | R33–R44 | 12/54 ≈ 22% | damped: API target only; severity keeps it at 15 | **15** |
| **F — Obsolete assumptions** | R45–R54 | 10/54 ≈ 19% | damped: deduction-only, overlaps with B/C/D cleanup | **10** |
| | | | **Total** | **100** |

## Dimension rubrics

Each dimension starts at its maximum; deduct per finding from Phase 1 (P1.3 anti-pattern scan and P1.4 missing information), floor at 0. Deduplication rule: **each finding is deducted exactly once**, in the first matching dimension in the order B → E → F → A → C → D (severity first). Rule of thumb for the split: B and E score what is *present and breaking*, F scores what is *present and outdated*, A/C/D score what is *missing*.

**A — Structure & explicitness (25)**
- Task unclear/incomplete — a colleague with minimal context would be confused (R1): −6 to −10
- No context/purpose/audience (R2): −5 (−2 to −3 if partially stated)
- Missing or inconsistent XML structure where the prompt is complex (R3): −4
- Long inputs below the query / not in `<documents>` structure (R4): −4
- Third-party text pasted unmarked into the prompt (R7): −4
- Missing examples where an exact format or style matters (R5): −3
- No role where one would focus behavior (R6): −2
- Multi-app task without an exploration instruction (R8): −2

**B — Thinking & reasoning safety (15)**
- Reasoning reproduction in the output — instruction, `<thinking>`/scratchpad section, or `reasoning`/`thinking`/`trace` schema field (R9): −10
- Thinking switched off or budgeted in the prompt text, or a "don't think / don't reason" rule (R10/R13): −4
- Manual CoT anywhere, or "think carefully" boilerplate in a chat prompt (R12/R48): −3
- Prose used to throttle thinking where effort is the lever (R11): −2

**C — Verbosity, communication & format (15)**
- No length steering for a user-facing product or for model-written deliverables (R15/R16): −4
- Frontend task with no concrete design direction (R20): −4
- Agentic session with a human reader but no communication cadence (R17): −3 (Route L: only when the user asks for more frequent or predictable updates or reports silent or over-narrated runs)
- Negative-only format steering ("no markdown", "don't use lists") (R19): −3
- Correction narration unaddressed in a user-facing product where it matters (R18): −1

**D — Agentics & harness behavior (20) — routes L/XL only; award in full on S/M (exception: R32 applies to any code-review task)**
- No boundaries on state-changing access, or on tools that act outside the session (R24): −5
- Route L: a confirmation or wait step on the requested work ("ask me before", "wait for my OK", "propose … first") (R24): −3
- Unattended deployment without checklist, end-of-turn handling, or standing instruction (R25): −4 (a missing completion condition is scored once, under R1)
- Blanket authorization / no confirmation step for risky actions under act-don't-ask framing (R26): −3 (Route L: exclusions of the risky actions satisfy this)
- No scope guidance where scope creep is plausible (R21): −3 (Route L: only when the input invites expansion or the user reports scope creep)
- Delegation push or subagent-centered harness without a delegation cap (R23): −3
- Status-reporting agent (unattended run whose report is read later) without claim grounding (R29): −3
- Code-review severity filter ("only report high-severity") (R32): −3
- Long-horizon state, compaction, or time signals unaddressed for XL (R30/R31): −2

**E — Parameters & refusal handling (15) — API target only; award in full on chat target**
- Sets forbidden request settings: sampling, prefill, `thinking: disabled`/`budget_tokens`, forced `tool_choice`, `computer_20251124`/`computer_20250124` on Claude API/Google Cloud (R10/R35/R36/R37/R44): −6
- No explicit effort (silently `medium`), or an effort clearly below what the task's quality needs (R33/R45): −4
- No refusal/fallback handling despite a cyber/bio/frontier-LLM-adjacent domain (R39): −4
- History-editing harness design: system prompt rebuilt mid-session, tools added later, reminders inserted and deleted (R42): −3
- Task budget set without a measured basis or below the task's need (R43): −2
- `max_tokens` / streaming / `display` / caching unconsidered for long or agentic outputs (R34/R40/R41): −1 each, at most −3 combined

**F — Obsolete assumptions (10) — deduction-only**
- Verifier subagents or "delegate more" pushes (R46/R22; transferred from Opus 5): −3 — the user's own "double-check" lines are not deducted (R22, measured)
- Anti-laziness/thoroughness appeals, forced status cadences, update suppressors (R28/R50): −3
- Aggressive trigger language (CAPS, "CRITICAL", "MUST") (R51): −3
- Hand-made token/context countdowns in the prompt (R49): −2
- Prompt-side vision pre-passes / step-by-step chart-reading scaffolds (R53): −2
- Vague anti-generic design line ("avoid a generic AI look") (R52): −2
- Prose assumptions from other models (thinking can be turned off, text-only progress, one fallback model for all) (R47/R54): −1

Deduction magnitudes within a dimension are heuristic anchors, not laws: scale them by how severely the finding would degrade the optimized outcome, but never exceed the dimension maximum.

## Route and target applicability

- Routes S/M: dimension D is awarded in full (20/20) — a simple prompt is not penalized for lacking agent scaffolding. Exception: a code-review prompt with a severity filter is deducted under R32 on any route.
- Chat target: dimension E is awarded in full (15/15); parameter intent that belongs in the prompt text (e.g., a brevity line instead of `effort: low`) is scored under C instead.
- The score always refers to the input prompt as submitted, judged against the route and target it *needs* — not against the heaviest possible rubric.

## Follow-up rounds

- **Round counting:** round 1 is the initial optimization; each later non-prefixed message on the same prompt is the next round. A new trigger message with a prompt of its own starts again at round 1; a trigger message that only answers the previous `<open_questions>` or requests a change is the next round (03, *Answers sent with the trigger*).
- **What is scored in rounds ≥ 2:** the input *as now known* — the original prompt plus the user's answers and requested changes. Answered questions recover the points they were estimated at (capped by the deduction they addressed); findings the optimizer fixed by itself (e.g., document placement, removed trigger language) do **not** raise the input score, because the user's input did not change there.
- **Progression line:** in rounds ≥ 2 the `total:` line shows `total: <old> → <new>/100 (+<d> from your answers)`; `<old>` is the total shown in the previous round, also when that round was a question round with the prompt held back (04). A change request that removes information ("drop the audience line") can lower the score; show that honestly.
- **Question budget across rounds:** at most 3 questions per round, questions only in rounds 1–2, round 2 marked as the last question round. From round 3 on, remaining gaps are closed with `(assumption)` decisions; a placeholder stays only for facts only the user can supply, and `<open_questions>` holds only the how-to-answer line (no "- None" bullet).

## Score bands

| Band | Meaning |
|---|---|
| 90–100 | Already Opus-5.5-ready — minimal diff, do not invent changes |
| 70–89 | Solid core — targeted fixes |
| 40–69 | Substantial restructuring needed |
| 0–39 | Rewrite: structure, safety, or parameter model fundamentally off |

## Open-question point estimates

Every entry in `<open_questions>` carries an estimated score gain: **"+~X points if answered."** X is the portion of the deducted points that the answer would recover — taken from the rubric line(s) the missing information triggered, capped by what was actually deducted. Risk notes that recover no points (e.g., the R39 refusal advisory) are tagged "+0 points (risk note)." The estimates are heuristic; always keep the "~".

Example mappings: purpose/decision unknown → recovers the R2 deduction (+~3 to +~5); interactive vs. unattended unknown in an agent prompt → recovers the R25 deduction (+~4); API-vs-chat unknown → recovers nothing by itself but unlocks dimension E scoring (tag "+0 points (unlocks parameter block)").

## Worked example

Input (Example 1 from `06-worked-examples.md`, chat target, Route M):

> Summarize the customer complaints in this support thread for our product team. IMPORTANT: You MUST be extremely thorough and don't miss anything. Think carefully step by step and include your reasoning for each complaint category so we can follow your logic. [pasted helpdesk email thread, ~25,000 words]

| Dimension | Findings | Deduction | Score |
|---|---|---|---|
| A (25) | Purpose only partly stated — audience named, decision unknown (R2): −3 · thread below the instruction, no `<documents>` structure (R4): −4 · pasted third-party thread unmarked (R7): −4 | −11 | 14/25 |
| B (15) | "include your reasoning for each complaint category" = reasoning reproduction (R9): −10 · "Think carefully step by step" boilerplate (R12): −3 | −13 | 2/15 |
| C (15) | No length steering for a deliverable the team reads (R15/R16): −4 | −4 | 11/15 |
| D (20) | Route M → not applicable, awarded | −0 | 20/20 |
| E (15) | Chat target → awarded | −0 | 15/15 |
| F (10) | "IMPORTANT: You MUST" (R51): −3 · "extremely thorough"/"don't miss anything" (R50): −3 | −6 | 4/10 |
| **Total** | | **−34** | **66/100** |

Band: 40–69 — substantial restructuring needed. Matching open-question estimates: "Which decision does the product team make with this summary?" → +~3 (R2); "Target length or format?" → +~4 (R15/R16); "Chat or API?" → +0 (unlocks parameter block). Round 2 of this example (`06-worked-examples.md`, Example 1b): both content questions answered → 66 → 73/100.
