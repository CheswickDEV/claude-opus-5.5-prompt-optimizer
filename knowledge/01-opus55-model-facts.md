# Claude Opus 5.5 — Model Facts

> Snapshot: October 3, 2026 (eleven days after the Claude Opus 5.5 launch on September 22, 2026). Every statement below is based exclusively on official Anthropic sources (anthropic.com, platform.claude.com, www-cdn.anthropic.com), fetched on the snapshot date. Source codes refer to the legend below. This file is the factual backbone of the optimizer: when a question is not answered here or in the other knowledge files, the correct answer is "not documented."

## Source legend

This legend is canonical for all knowledge files in this project.

| Code | Source |
|---|---|
| [News] | https://www.anthropic.com/claude-opus-5-5 (release announcement) |
| [Product] | https://www.anthropic.com/claude/opus (product page) |
| [SystemCard] | System Card (PDF): https://www-cdn.anthropic.com/fc1b44717c85dc068bc6ba5024219938094694bd/Claude%20Opus%205.5%20System%20Card.pdf |
| [ModelPage] | https://platform.claude.com/docs/en/models/opus-5-5/overview |
| [WhatsNew] | https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5 |
| [Migration] | https://platform.claude.com/docs/en/models/opus-5-5/migration-guide |
| [PromptO55] | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5 |
| [PromptO5] | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5 (per [PromptO55] "a reasonable starting point" for Opus 5.5) |
| [BestPract] | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices |
| [Models] | https://platform.claude.com/docs/en/models/overview |
| [Pricing] | https://platform.claude.com/docs/en/about-claude/pricing |
| [Effort] | https://platform.claude.com/docs/en/build-with-claude/effort |
| [Thinking] | https://platform.claude.com/docs/en/build-with-claude/thinking |
| [ThinkSteer] | https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost |
| [ContextWin] | https://platform.claude.com/docs/en/build-with-claude/context-windows |
| [TaskBudget] | https://platform.claude.com/docs/en/build-with-claude/task-budgets |
| [Compaction] | https://platform.claude.com/docs/en/build-with-claude/compaction |
| [CompactOnDemand] | https://platform.claude.com/docs/en/build-with-claude/compaction-on-demand |
| [ContextEdit] | https://platform.claude.com/docs/en/build-with-claude/context-editing |
| [PreservedThinking] | https://platform.claude.com/docs/en/build-with-claude/preserved-thinking |
| [MidConvSys] | https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages |
| [Refusals] | https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback |
| [StructOut] | https://platform.claude.com/docs/en/build-with-claude/structured-outputs |
| [CostIntel] | https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence |
| [SysPrompt] | https://platform.claude.com/docs/en/release-notes/system-prompts/claude-opus-5-5 (the system prompt Opus 5.5 uses on claude.ai) |
| [FallbackCredit] | https://platform.claude.com/docs/en/build-with-claude/fallback-credit |
| [FastMode] | https://platform.claude.com/docs/en/build-with-claude/fast-mode |

Docs note: model pages moved to `/docs/en/models/<model>/…` in 2026; the old `/docs/en/about-claude/models/migration-guide` URL is now only an index page. An `introducing-claude-opus-5-5` page does not exist (404); [WhatsNew] is its equivalent.

## What Opus 5.5 is

Claude Opus 5.5 (`claude-opus-5-5`, generally available since September 22, 2026) is the current Opus model and the first model of the Claude 5.5 family: built for long-running agentic coding and knowledge work, at $4/$20 per MTok — below Opus 5's $5/$25. Anthropic positions it at Fable-5.1 level "on most work" at 40% lower running cost than Opus 5, and recommends it as the starting model for most workloads. Specs: 1M-token context (default = maximum), 128k max output. The API surface tightens Opus 5 in four places: thinking is always on (`disabled`/`budget_tokens` → 400), forced `tool_choice` → 400, thinking blocks are tied to the model and the conversation ("preserved thinking"), and on the Claude API/Google Cloud computer use only works via the computer toolset. The primary control is `output_config.effort`, whose default is **`medium`** — one level below every other model that supports effort (where it is `high`). Existing Opus 5 prompts "should perform well without changes"; the Opus 5 prompting patterns remain the starting point, to be re-tested rather than carried over blindly.

## Model knowledge table

| Property | Value | Source |
|---|---|---|
| **Positioning** | Current Opus; "For long-running agentic coding and knowledge work"; "performs at the level of Claude Fable 5.1 on most work and costs 40% less to run than Opus 5"; recommended default: "start with Claude Opus 5.5 for most workloads. Use Claude Fable 5.1 for demanding reasoning and long-horizon agentic work, or when your evals on Claude Opus 5.5 at higher effort still fall short." | [ModelPage], [News], [Models], [CostIntel] |
| **Model IDs** | Claude API, Google Cloud, Microsoft Foundry, Claude Platform on AWS: `claude-opus-5-5` · Amazon Bedrock: `anthropic.claude-opus-5-5`; fixed ID without date suffix | [ModelPage], [WhatsNew] |
| **Lifecycle** | Released September 22, 2026; retirement "Not sooner than September 22, 2027"; status Active (latest) | [ModelPage] |
| **Pricing** | $4 / MTok input, $20 / MTok output; 5-min cache write $5, 1-h cache write $8, cache read $0.20 (0.05× input — deeper discount than the 0.1× of most models); Batch API −50% ($2/$10); fast mode (research preview, Claude API only) $8/$40; full 1M window at standard pricing | [ModelPage], [WhatsNew], [Pricing] |
| **Context window** | 1M tokens, default and maximum, no beta header; ≈ 555k words / 2.5M Unicode characters on the current tokenizer | [ModelPage], [Migration] |
| **Max output** | 128k tokens (synchronous Messages API); up to 300k on the Message Batches API with beta `output-300k-2026-03-24`; `max_tokens` is a hard limit on thinking **plus** response text | [ModelPage], [Migration] |
| **Tokenizer** | The tokenizer introduced with Opus 4.7 (unchanged from Opus 4.7/4.8/5); ~30% more tokens for the same text than Sonnet 4.6 and earlier | [ModelPage], [Pricing] |
| **Knowledge cutoff** | Reliable knowledge cutoff Jun 2026; training data cutoff Jun 2026 | [ModelPage] |
| **Thinking mode** | "Adaptive (always on)" — can't be turned off; `thinking: {"type":"disabled"}` and `{"type":"enabled","budget_tokens":N}` both return 400 `invalid_request_error` at every effort level; omit `thinking` or send `{"type":"adaptive"}` (equivalent) | [ModelPage], [WhatsNew], [Effort] |
| **Thinking output** | Raw chain of thought is never returned; `thinking.display` defaults to `"omitted"` (empty `thinking` field), opt-in `"summarized"`, and `"updates"` (beta `thinking-display-updates-2026-08-18`) returns only between-tool progress notes; responses may begin with zero or more `thinking` blocks → select blocks by `type`, pass them back unchanged | [WhatsNew], [Thinking], [PromptO55] |
| **Progress updates** | Text the model writes between tool calls comes back as progress-update `thinking` blocks (not `text`), empty under the default display → a text-only client looks silent during long agentic turns | [WhatsNew], [PromptO55] |
| **Effort** | `output_config.effort`: `low` \| **`medium` (default)** \| `high` \| `xhigh` \| `max`; at a given level Opus 5.5 thinks more per turn than Opus 5 (most at `xhigh`/`max`); `medium` matches or exceeds Opus 5 at `high` on coding and knowledge work; `low` comes close on several coding evals at much lower cost; per-message effort change (beta `mid-conversation-output-config-2026-07-01`) on the Claude API and Google Cloud keeps the prompt cache, a top-level change invalidates it | [Effort], [PromptO55], [WhatsNew] |
| **Effort cost data (SWE-bench Pro, vs. `high`)** | `medium` ≈ −2.5 points at ~70% of the cost; `low` ≈ −8 points at ~⅓ of the cost; `xhigh` ≈ +1.4 points at 2.5× the cost; `low` with failures re-run at `high`: ~97% vs. 95.3% all-`high`, at ~$0.17 vs. $0.29 per task | [CostIntel] |
| **Sampling parameters** | Non-default `temperature`, `top_p`, `top_k` → 400 on every request; "Use prompting to guide the model's behavior." | [Migration], [Thinking] |
| **Assistant prefill** | A prefilled last assistant turn → 400; use structured outputs or system-prompt instructions | [Migration], [BestPract] |
| **Forced tool use** | `tool_choice` `{"type":"any"}` / `{"type":"tool",…}` → 400 (also on token counting); `auto` (default) and `none` work; for schema-valid JSON use `strict: true` or structured outputs; "To make the model call a tool rather than reply in text, say in the prompt when the tool applies." | [WhatsNew], [Migration] |
| **Computer use** | Claude API and Google Cloud: only `computer_toolset_20260801` (no beta header); `computer_20251124` → 400. Amazon Bedrock still accepts `computer_20251124`. Browser use tool supported | [WhatsNew], [Migration] |
| **Structured outputs / strict tool use** | Supported; incompatible with citations (400 with `output_config.format`); "A property that asks for the model's thinking or step-by-step reasoning may lead to a `reasoning_extraction` refusal." | [StructOut], [WhatsNew] |
| **Preserved thinking** | Thinking blocks record the producing model: Opus 5.5 reads blocks from Opus 5 and earlier Opus/Sonnet/Haiku models (and, on Claude API/Google Cloud, Sonnet 5.5), **not** from Fable/Mythos; on the Claude API only Fable 5.1/Mythos 5.1 read Opus 5.5 blocks. Conversation binding: changing `system`, `tools`, or any earlier message invalidates later blocks; enforced by default (400) for accounts created on/after 2026-08-31 00:00 UTC; `drop_block` via beta `thinking-binding-controls-2026-08-01` | [WhatsNew], [PreservedThinking], [News] |
| **Mid-conversation system messages** | Supported on the Claude API, Amazon Bedrock, and Google Cloud (no beta header; placement rules apply); the append-only way to change instructions; turn-scoped `clear_at: "next_user_message"` via beta `mid-conversation-system-clear-at-2026-08-21`. Mid-conversation tool changes are beta: `inline-tools-2026-09-15` on the Claude API (references and full definitions), `mid-conversation-tool-changes-2026-07-01` for by-reference changes | [WhatsNew], [MidConvSys], [Migration] |
| **Context awareness** | Opus 5.5 does **not** receive injected `<budget:token_budget>` / remaining-context tags ("Claude Opus 4.7 and later Opus models … don't receive these injected tags"); the only model-visible budget is a task budget | [ContextWin] |
| **Task budgets** | Beta `task-budgets-2026-03-13`; `output_config.task_budget {type:"tokens", total, remaining?}`, minimum 20,000; model sees a running countdown; soft hint, not a hard cap; "A budget that is too small for the task can cause refusal-like behavior"; not supported in Claude Code or Cowork | [TaskBudget], [Migration] |
| **Compaction & context editing** | Server-side compaction (beta) and on-demand compaction (beta `compact-2026-09-04`, custom `instructions` up to 16,384 chars, keeps thinking in retained turns under conditions; not on Bedrock); context editing (beta `context-management-2025-06-27`) — server-side context management never invalidates thinking blocks, client-side edits can; a compaction request can't carry `context_management` and rejects `stop_sequences`, a forced `tool_choice`, a structured-output `output_config.format`, and `task_budget.remaining` (also on every later request that carries the compaction block) | [WhatsNew], [Compaction], [CompactOnDemand], [ContextEdit] |
| **Prompt-caching minimum** | 512 tokens (Opus 4.8: 1,024) | [ModelPage], [Migration] |
| **Other features** | Task budgets, per-message effort, mid-conversation system messages and tool changes, batch, Files API, PDF, vision (text and images in → text out), server- and client-side tools; fast mode (`speed: "fast"`, beta `fast-mode-2026-02-01`, Claude API only, research preview with access on request; switching speed invalidates the prompt cache); **no Priority Tier** | [WhatsNew], [ModelPage], [Migration], [FastMode] |
| **Safety classifiers** | Cybersecurity, **biology** (new vs. Opus 5; same as Fable 5.1) and reasoning extraction; announcement also names distillation — "all of which fall back to another model transparently". Finding vulnerabilities in source code is allowed; "most cybersecurity tasks will be re-routed to Opus 4.8"; in Anthropic's benchmark runs, intervening safeguards had "biology and frontier LLM development tasks … completed by Claude Opus 5"; for life sciences work blocked by the classifier → Life Sciences Verification Program | [PromptO55], [News], [WhatsNew] |
| **Refusal mechanics (API)** | HTTP 200 with `stop_reason: "refusal"` and `stop_details {type, category, explanation, recommended_model}`; categories `cyber`, `bio`, `frontier_llm`, `reasoning_extraction`, `general_harms`, or `null`; refusals before any output are **billed** for `bio`, `frontier_llm`, `reasoning_extraction`; `reasoning_extraction` has no recommended fallback and is not retried by server-side fallback | [Refusals], [PromptO55] |
| **Fallback** | Server-side `fallbacks` (beta on the Claude API; not available on Amazon Bedrock, Google Cloud, or Microsoft Foundry; for Claude Platform on AWS the fallback-credit page publishes `allowed_fallback_models` under this header, the refusals page does not list it): header `server-side-fallback-2026-07-01` supports both `"default"` (routes by refusal category) and an explicit model list; the older `-2026-06-01` header accepts only the list form. Bedrock/Google Cloud/Foundry: SDK middleware or own retry with fallback credit (beta `fallback-credit-2026-07-01` on the refused request and on the retry, which redeems the token; the token expires five minutes after the refusal). Message Batches: the `fallbacks` parameter is not supported (a batch item that includes it comes back as an errored result) and batch refusals don't mint fallback credits — collect refused items and resubmit them on a fallback model. A fallback model runs without Opus 5.5's thinking (except Fable 5.1/Mythos 5.1 on the Claude API) | [Refusals], [WhatsNew], [FallbackCredit] |
| **Capabilities (prompting-relevant)** | Strongest on multistep work in a real repository; sustains multi-hour autonomous runs with parallel subagents; stronger code review (more bugs, fewer false alarms); "much less likely to state an incorrect figure or cite the wrong source"; catches easy-to-miss details in large inputs; reads dense charts/diagrams/screenshots more accurately than Opus 5 even at `low`; more reliable computer use | [PromptO55], [News] |
| **Communication profile** | "puts the most important information up front", "less likely to use jargon or idiosyncratic phrases, and follows the writing rules you give it"; tester: answers "40% less verbose without losing accuracy"; generates output >30% faster than Opus 5 | [News], [PromptO55] |
| **Behavioral profile (System Card)** | "took overeager or destructive actions less than any other model we tested"; more likely to ask permission before a potentially destructive action; strongest model yet on instruction-following failures and recklessness. Regressions: "more likely to follow malicious instructions planted in text a user pastes into their own prompt, more often accepting unverifiable claims of authorization, and being more evasive on sensitive questions than Claude Mythos-class models"; top flagged internal-use behavior: "asserting unverified inferences as established fact"; rare "overclaiming user intent" (<0.01%) under an act-don't-ask instruction; "modest countervailing increase in susceptibility to user pressure"; reward-hacking subtype: told to use a particular tool, answered directly instead; prompt injection via tool results 0/105, via pasted text ~2% (default effort) / 7.4% (max) in the final model | [SystemCard] |
| **Data retention** | "Like previous Opus models, Opus 5.5 is available with zero data retention." (unlike the Fable/Mythos Covered Models) | [News] |

## Not documented / open points (as of October 3, 2026)

When users ask about these, answer "not documented" and cite this list:

1. **Opus-5.5-measured versions of the Opus 5 snippets** (conciseness, deliverable length, over-verification, scope, subagent caps, correction narration): Anthropic published only the Opus 5 measurements (this project re-tested R15, R22, R23 and R33 on Opus 5.5, see 02 [MEASURED: T5]); [PromptO55] calls them "a reasonable starting point" and [Migration] says Opus-5-tuned instructions "may no longer be needed" → every such rule is marked [DERIVED: transfer] and is a re-test candidate.
2. **Long-context degradation or placement guidance specific to Opus 5.5:** only the generic 20k+ rules in [BestPract] and the System Card's ProgramBench result across context lengths up to 1M.
3. **Opus-5.5-specific guidance on XML structure, roles, intent blocks, few-shot counts:** none beyond the generic [BestPract] techniques (which cover Opus 5.5 explicitly).
4. **Adapting Fable 5/5.1 prompts to Opus 5.5:** no official statement; only the generic "Where a technique names a specific model, treat it as measured on that model and re-check it" ([BestPract]) and the fact that Opus 5.5 can't read Fable thinking blocks.
5. **Prompt-side countermeasures for user-pressure susceptibility / sycophancy:** findings exist only in the System Card; no documented prompt fix.
6. **Prompt-side countermeasures against safeguard false positives on Opus 5.5:** none documented (the Fable 5.1 tips are documented for Fable 5.1 only).
7. **A per-workload effort table for Opus 5.5:** only general guidance plus the [CostIntel] measurements; the detailed table exists for Opus 4.7.
8. **Memory-tool behavior specific to Opus 5.5:** only the product-page claim that it "uses memory to learn across sessions."
9. **Default compaction summarization prompt text:** not published.
10. **Rate limits / tier assignment:** not covered by the evaluated sources.
11. **Per-message effort on Amazon Bedrock, Claude Platform on AWS, and Microsoft Foundry:** [MidConvSys] documents the beta for the Claude API and Google Cloud only; the other platforms are not mentioned.
12. **Server-side fallback combined with Opus-5.5-only fields:** whether a request with `thinking.display: "updates"` or per-message effort is accepted when `fallbacks: "default"` routes it to Opus 4.8 or Opus 5 is not documented.

---

*Methodological note: core facts (model ID, context window, output limit, pricing, effort default, thinking restriction, forced-tool-use restriction) are confirmed across at least three independent official pages ([ModelPage], [WhatsNew], [Migration], [Effort], [Pricing]). Snippet wording in `05-snippet-library.md` is copied from the raw page source of [PromptO55], [PromptO5], [ThinkSteer], and [BestPract] fetched on October 3, 2026.*
