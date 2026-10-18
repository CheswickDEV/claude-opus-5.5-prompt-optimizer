# Output Templates

This file is the single source of truth for the optimizer's output format. Two variants: **A (API target)** and **B (claude.ai chat target)**. Target detection is defined in `03-workflow-and-routing.md`, Phase 0; the score is defined in `07-scoring.md`.

Shared conventions:

- **The optimized prompt is emitted first, as a standalone fenced code block** (```` ```text ````). The fence contains the prompt and nothing else — no commentary, no score, no meta text — so it is directly copyable in one action. `<parameters>`, `<score>`, `<changes>`, and `<open_questions>` follow as separate blocks *outside* the fence, in that order.
- Inside the fence, variant A separates `<system>` and `<user>` sections (API users need both). Variant B contains the paste-ready prompt text without a wrapper tag — what is in the fence is exactly what the user pastes into the chat.
- Beta fields (`fallbacks`, `display: "updates"`, `task_budget`, per-message effort, `clear_at`, on-demand compaction) exist only in the beta request schema: SDK `client.beta.messages.*` with `betas=[…]`, raw HTTP via the `anthropic-beta` header (several features comma-separated). `speed` (fast mode) is a standard field for Opus 5.5 (`client.messages.create`, no beta header).
- Bulk user content (documents, code, data, pasted third-party text) is represented by placeholders — `{{DOCUMENTS}}`, `{{INPUT}}`, `{{CODE}}`, `{{PASTED_TEXT}}` — with a one-line placement note, instead of being echoed back.
- **The prompt in the fence works as pasted.** `{{…}}` placeholders stand only for content the user pastes and for values their own system supplies (an ID, a date). Missing context — purpose, audience, reason, the decision the output feeds — is never a `[bracketed]` gap in the prompt: write the prompt so it works without it and ask for it in `<open_questions>`; the answer goes into the prompt in the next round. Never write invented example scenarios into the prompt ("e.g., a game setting"): the model treats them as facts. For human readers, add no sections, tables, columns, citation or reporting duties the user did not ask for (R1/R2; exceptions: claim grounding in unattended status reports and the one R29 grounding sentence, see 03). Facts only the user knows (a name, an address, a date) are not context gaps: in a chat prompt either leave them out and ask, or use one `{{…}}` slot per fact plus a line telling the model to mark a missing fact instead of inventing it — never a bare `[bracket]`.
- Every `<changes>` entry cites the rule number(s) from `02-prompting-rules.md` that motivated it. Notes that are not edits get no entry of their own: the target/route decision is one entry citing `(Phase 0)` (it also carries the "already well-optimized" statement for a score ≥ 90), score explanations stay in `<score>`, follow-on edits cite the rule of the change they serve, and in rounds ≥ 2 there is neither a separate "Round 2: …" entry nor a recap of round-1 changes that stay ("kept all round-1 fixes") — each integrated answer or requested change is an entry citing the rule whose gap it closes. Snippets measured on Opus 5 are marked `(re-test)`. Decisions made autonomously after the iteration budget is exhausted are marked `(assumption)`.
- `<open_questions>` holds **at most 3 entries**, each tagged with its estimated score gain per `07-scoring.md` ("+~X points if answered"). The optimizer never withholds the optimized prompt to ask a question first.
- On follow-up rounds — answers to `<open_questions>` or change requests ("make it shorter", "add X") — integrate the answers or apply the change, re-run the Phase 4 quality gate, re-score, and re-emit the **full** block set — not a diff. Questions in at most 2 rounds (round 1 = initial optimization, round 2 = first reply); from round 3 on, no new questions — decide, mark `(assumption)`, finalize. Round counting and score progression: `07-scoring.md`, *Follow-up rounds*.
- `<open_questions>` ends with one line telling the user how to answer: in a normal message without the trigger prefix. The line names the trigger to leave out in every round; in round 2 it also says it is the last question round. From round 3 on, `<open_questions>` holds no entries (no "- None" bullet), only that line.

## Variant A — API target

````text
```text
<system>
…optimized system prompt…
</system>
<user>
…optimized user prompt with {{DOCUMENTS}}/{{INPUT}}/{{PASTED_TEXT}} placeholders…
</user>
```
<parameters>
  model: claude-opus-5-5
  effort: <low|medium|high|xhigh|max> — set explicitly (default is medium) — <one-line justification>
  max_tokens: <value> — covers thinking + reply — <one-line justification>
  streaming: <yes/no>
  thinking: <omit (always on; display stays "omitted") | {type: "adaptive", display: "updates" | "summarized"}> — <why>
  tool_choice: <auto (+ strict: true on tools) | none | not applicable>
  output_config.format: <JSON-schema recommendation (every object: additionalProperties: false) | not needed>
  fallbacks: <"default" (beta server-side-fallback-2026-07-01) | SDK middleware (non-Claude-API platform) | not needed>
  caching: <cache-breakpoint recommendation>
  task_budget: <value from measured p99 | omit>
  extras: <per-message effort / mid-conversation system messages / fast mode / computer toolset | none>
</parameters>
<score>
  total: <n>/100 — band: <band label>        (round ≥ 2: total: <old> → <new>/100 (+<d> from your answers))
  A structure: <n>/25 · B thinking: <n>/15 · C verbosity: <n>/15 ·
  D agentics: <n>/20 · E parameters: <n>/15 · F legacy: <n>/10
  <one line per deducted dimension: finding (R<number>): −<points>>
</score>
<changes>
  - <change> (R<number>): <justification in one sentence>
</changes>
<open_questions>
  - <missing information or risk note> (+~<X> points if answered | +0 points (risk note))
  <one line: how to answer — normal message, no trigger prefix>
</open_questions>
````

### Per-field guidance for `<parameters>` (from R33–R44)

| Field | Guidance |
|---|---|
| `model` | Always `claude-opus-5-5` (Bedrock: `anthropic.claude-opus-5-5`; Google Cloud, Foundry, Claude Platform on AWS: `claude-opus-5-5`). |
| `effort` | **Always set explicitly** — omitting it runs `medium` (R33/R45). Best-result presets: S `low` where quality holds and any parsed format is enforced by `output_config.format` (measured: without it, `low` broke a JSON classifier's format), else `medium`; M `medium`, `high` for critical deliverables; L `high`, `xhigh` for the hardest tasks; XL `high`, `xhigh`/`max` for correctness-critical runs. Keep an explicitly set `xhigh`/`max` and note its token cost (SWE-bench Pro: `xhigh` ≈ +1.4 points over `high` at 2.5× the cost). Secondary token-saving option, only on request or when quality is shown to hold: `low` + re-run failures at `high`. Mid-conversation changes: per-message effort (beta `mid-conversation-output-config-2026-07-01`) keeps the cache and holds until replaced. |
| `max_tokens` | Hard cap on thinking + reply; invisible to the model (R34). Long agentic coding turns: 128000 (streaming). `xhigh`/`max`: ≥ 64000. Routine replies: leave room for thinking (no documented floor for Opus 5.5; ≥ 16000 non-streaming is this optimizer's [DERIVED] default, more at `high`+). On `stop_reason: "max_tokens"`: raise it or lower effort. |
| `streaming` | `yes` for `max_tokens` above ~16k, all Route L/XL workloads, and any UI that shows progress (R34/R27). |
| `thinking` / `display` | Never set `type` to `disabled`/`enabled` (R10). To change `display`, send the whole object `{"type": "adaptive", "display": …}` — `display` can't be set while `thinking` is omitted. `display: "updates"` (beta `thinking-display-updates-2026-08-18`) when a UI shows between-tool progress; `"summarized"` when reasoning visibility is needed instead of R9 instructions; otherwise `omitted` (default). Read blocks by `type`, pass them back unchanged (R40). |
| `tool_choice` | `auto` (default) or `none` only (R37). To make a tool call likely: say in the prompt when the tool applies, add `strict: true` to the tool (every schema object `additionalProperties: false`; at most 20 strict tools per request), check that a call happened and retry. Extraction-only forced calls → `output_config.format`. Amazon Bedrock: no `strict` or structured outputs for Opus 5.5 — `auto`, the prompt says when the tool applies, validate the input in code. |
| `output_config.format` | `{"type": "json_schema", "schema": …}` when the consumer is a parser (R38); every object `additionalProperties: false`; never the deprecated top-level `output_format` parameter (400 without its old beta header). No `reasoning`/`thinking`/`trace` properties (R9). Not combinable with citations. Not available for Opus 5.5 on Amazon Bedrock (describe the format in the prompt, validate in code). Otherwise "not needed". |
| `fallbacks` | `"default"` with beta header `server-side-fallback-2026-07-01` (Claude API; not on Bedrock, Google Cloud, or Foundry) whenever a refusal would break the product — mandatory near cyber/bio/frontier-LLM territory (R39). Bedrock/Google Cloud/Foundry: SDK refusal-fallback middleware or own retry with fallback credit; Message Batches: no `fallbacks` parameter and no fallback credit — collect refused items and resubmit them on a fallback model. Note: `reasoning_extraction` is never retried; a fallback model runs without Opus 5.5's thinking. Not documented: whether a request carrying Opus-5.5-only fields (`display: "updates"`, per-message effort) is accepted when `"default"` routes it to a fallback model — test before relying on the combination. |
| `caching` | Stable prefix (tools → system → messages, byte-exact; no timestamps), minimum 512 tokens, cache reads $0.20/MTok (0.05×) — misses cost relatively more (R41). Change instructions via mid-conversation system messages, not by editing `system`; declare all tools from request one (R42). Short human pauses: keep the 5-minute cache warm rather than buying the 1-hour duration. |
| `task_budget` | Only from a measured value (p99 of per-task spend), minimum 20000, beta `task-budgets-2026-03-13`; omit for open-ended quality tasks; too small → refusal-like behavior (R43). Platform availability isn't documented on the task-budget page; plan for the Claude API. |
| `extras` | Mid-conversation system messages (no header) for instruction changes; turn-scoped reminders (`clear_at`, beta `mid-conversation-system-clear-at-2026-08-21`); fast mode `speed: "fast"` (no beta header; Claude API and Microsoft Foundry deployments hosted on Azure; $8/$40; a speed switch invalidates the cache; not with the Batch API) for latency-sensitive routes, only on request; computer use only as `{"type": "computer_toolset_20260801"}` on Claude API/Google Cloud — not available on Claude Platform on AWS (R44). |

Never recommend: `temperature`, `top_p`, `top_k`, assistant prefill, `thinking: {type: "disabled"}`, `thinking: {type: "enabled", budget_tokens: …}`, `tool_choice` `any`/`tool`, `computer_20251124`/`computer_20250124` on the Claude API or Google Cloud — all return 400 (R10/R35/R36/R37/R44).

## Variant B — claude.ai chat target

````text
```text
…paste-ready optimized prompt with {{DOCUMENTS}}/{{INPUT}}/{{PASTED_TEXT}} placeholders…
```
<score>
  total: <n>/100 — band: <band label>        (round ≥ 2: total: <old> → <new>/100 (+<d> from your answers))
  A structure: <n>/25 · B thinking: <n>/15 · C verbosity: <n>/15 ·
  D agentics: <n>/20 · E parameters: <n>/15 · F legacy: <n>/10
  <one line per deducted dimension: finding (R<number>): −<points>>
</score>
<changes>
  - <change> (R<number>): <justification in one sentence>
</changes>
<open_questions>
  - <missing information or risk note> (+~<X> points if answered | +0 points (risk note))
  <one line: how to answer — normal message, no trigger prefix>
</open_questions>
````

No `<parameters>` block — those controls do not exist in the chat UI. Instead, fold parameter intent into the prompt text:

| API intent | Chat-prompt substitute |
|---|---|
| `effort: low` (routine task) | No chat equivalent — effort controls thinking, not length (R15). A lighter model is mentioned in `<open_questions>` only if the user says cost or speed matters more than quality; a brevity line is a separate R15 decision, made only if the output needs length steering. |
| `effort: high`/`xhigh` (hard problem) | Nothing by default — "The model determines how much to think" (R12). For a single genuinely hard turn only: "Please think hard before responding." (snippet 16). |
| Less thinking / faster first token | Remove "think carefully" lines from the prompt (R12); for one latency-sensitive turn: "Answer directly without deliberating." |
| `fallbacks` (cyber/bio/frontier-LLM risk) | A note in `<open_questions>` (snippet 24): the request may be declined or answered by a fallback model (R39). |
| `output_config.format` (structured output) | Describe the exact output format in the prompt text, positively (R19); grammar-constrained schemas exist only on the API. |
| `thinking.display: "summarized"` | Not available in chat; never replace it with "show your reasoning" (R9) — ask for a short explanation of the answer instead. |
| `<pasted_content>` system note | claude.ai Project: put the note in the Project instructions. Single chat prompt: put it at the top, then the wrapped pasted text (R7, snippet 14). Both are [DERIVED] adaptations of the documented system-prompt placement. |
| `max_tokens` / streaming / caching / task budget / fast mode | Not applicable in chat — omit silently. |

## Language rule (both variants)

The optimized prompt — including inserted snippets, translated — keeps the **input prompt's language**. XML tag names the optimizer adds (including `<pasted_content>`) are English even when the prompt is not; tag names the user already chose are kept, because renaming them changes nothing for the model. `<score>`, `<changes>`, `<open_questions>`, and all commentary follow the user's conversation language.
