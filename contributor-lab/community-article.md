# Why a small agent needs more than a smaller prompt

*An open-source exploration of Hermes, LFM3, bounded context, and decision-model assistance. This is a working note with reproducible diagnostic code—not a claim of frontier-model parity.*

## The question

Can an agent harness designed around capable, large-context models become useful on a small local model without simply increasing the context window?

That question has two different parts:

1. Can we reduce the memory and interface burden imposed by the harness?
2. Can the remaining model make the decisions the task actually requires?

It is easy to solve part of the first and accidentally claim to have solved the second.

I inspected a pinned Hermes source snapshot and built a standalone diagnostic prototype. I also exercised real local LFM3-1.7B and d1-2B endpoints. The early results point to a bounded-context architecture, but they also expose failure modes that a credible contributor proposal must retain.

## A large context is useful, but it is not the source of intelligence

Successful agent systems combine a capable model, an interaction loop, usable tools, sufficient working memory, and external feedback. A coding agent can run tests instead of guessing whether a patch works. A research agent can fetch a source instead of inventing facts. A good interface makes those actions easier.

The [SWE-agent interface research](https://proceedings.neurips.cc/paper_files/paper/2024/hash/5a7c947568c1b1328ccc5230172e1e7c-Abstract.html) provides evidence that agent–computer interface design affects performance. It does not establish that interface engineering substitutes for all model reasoning.

Context preserves files, constraints, failed attempts, and dependencies. It does not guarantee that the model can discover a strategy, interpret an ambiguous instruction, or resolve a contradiction.

A single tool call can still be a difficult reasoning problem.

## What Hermes actually puts in context

The inspected Hermes implementation assembles three system-prompt tiers:

- **Stable:** identity, execution guidance, pinned skills, and operating instructions.
- **Project/context:** project files and workspace-specific guidance.
- **Volatile:** skill index, memory, user profile, date, and environment information.

These are arranged to preserve reusable prefixes. Conversation then records user requests, assistant actions, actual tool results, and corrections. Tool definitions are a separate request field, rendered into the model input by the backend’s template.

Hermes already has compression, progressive tool disclosure, result spillover, searchable history, and a `ContextEngine.select_context()` hook. It is not oblivious to context.

But the default harness is also not a perfect symbolic task controller. A significant portion of its working state remains in conversational text and summaries.

The normal custom-provider startup path enforces at least 64,000 context tokens. That is a reliability policy in the harness, not a universal lower bound on agent intelligence. Removing it without auditing request accounting, output reserves, compaction, retries, and child agents would be the wrong contribution.

Source snapshot: [Hermes commit 26cd2e6](https://github.com/NousResearch/hermes-agent/tree/26cd2e6d83494c22a8b5e961f20e293285c48d0a).

## LFM3 is small; its advertised window is not

LFM3-1.7B supports a 262,144-token model context. A local server may serve much less. The local endpoint used here serves 32,768 tokens, with Q4_K_M weights.

[Liquid’s model card](https://huggingface.co/LiquidAI/LFM3-1.7B) reports agent and tool-use scores, but its capability evaluations use BF16 at full context. Those numbers are not evidence of equivalent success at Q4 and a tiny active window.

The distinction matters:

- Model parameter count.
- Model-supported context.
- Actual served context.
- Tokens used in a particular request.
- Effective task reliability.

All five need separate measurements.

## The prototype: context as a view, not a growing bin

The standalone context compiler preserves mandatory state and constraints, then admits optional evidence in ranked order. Recent tool interactions stay as complete call/result groups. Artifacts are stored exactly by content-addressed ID.

The admission rule is:

```text
rendered input + output reserve + safety margin
≤ actual served window
```

The compiler counts the actual local model’s rendered prompt through llama.cpp’s `/apply-template` and `/tokenize` endpoints. Tool schemas are included in the packing check. It fails closed when mandatory content cannot fit.

A real-template check packed a task, read-only constraint, current observation, and four small tool schemas into 294 input tokens. It excluded a large optional archive. With 128 output tokens and a 96-token margin, the request fit an illustrative 1,024-token total budget.

This is a prompt-packing test, not proof of agent success at a physically served 1K window. The actual server still serves 32K.

The software tests cover mandatory retention, schema costs, atomic tool groups, exact Unicode artifact recovery, stable selection, unknown-action rejection, and a simplified completion gate. They do not certify production security or transaction correctness.

## Why decision models are interesting

A decision model can answer a bounded question without generating a free-form explanation. [Liquid’s d1 documentation](https://docs.liquid.ai/lfm/models/decision-models) describes typed choices, scores, and yes/no probabilities.

Possible harness roles include:

- Reranking optional evidence.
- Selecting a relevant skill.
- Routing a task to a small or stronger model.
- Detecting missing context or repeated failures.
- Ranking candidate actions that already passed deterministic checks.

This is an assistance layer—not the authority that grants permission or declares external success.

Zero output tokens does not mean zero computation. The model still processes its input. A confident probability distribution is also not proof of correctness on a new task distribution.

The local d1 endpoint used here serves 4,096 tokens with Q4_K_M weights and returns real typed decisions via `/v1/systemone`. Backend and weight hashes are included with the code.

## The diagnostic tasks

I authored 16 small workflow-state scenarios. Each asks for one of four next operations:

```text
update_record / read_back / finish / escalate
```

The scenarios include explicit permission, missing permission, ambiguous identity, missing target status, a successful write without verification, a mismatching read-back, an uncertain timed-out write, stale logs, a user correction, and an injected instruction in tool text.

No business record was actually changed. Expected labels were not sent to the models. These are diagnostic fixtures, not a standard agent benchmark or teacher-generated demonstrations.

There are two context conditions:

- **Compact:** directly supplied relevant state.
- **Distractors:** the same state surrounded by 50 explicitly constructed, unrelated historical records.

The distracting material adds about 957 input tokens. The noisy prompts are roughly 1.2K tokens—not anywhere near the models’ context ceilings. Therefore this is not evidence of a universal hard context limit or a context-rot threshold.

### First lesson: output shape and decision quality are separate

The initial LFM3 condition requested a bare operation name. It sometimes produced XML-style tool calls instead. Exact-label scoring therefore counts an interface failure even where the literal function name is appropriate.

The release preserves both metrics: requested interface compliance and a retrospective extraction of one literal function name. That extraction is not a production parser and does not establish correct arguments.

I then added schema-constrained JSON and native tool-call controls. These follow-ups were exploratory, not preregistered.

### Second lesson: perfect schema does not imply correct action

In the schema-constrained LFM3 condition, all 32 responses matched the four-option JSON schema.

Yet only 7 of 16 compact cases and 3 of 16 distractor cases matched the expected next operation.

Examples of semantic mistakes include finishing after a mismatching observation and selecting another update when verification was needed. Those failures are exactly why typed output is not sufficient authorization or completion evidence.

### Third lesson: a decision model is useful, not infallible

d1 matched the expected action in 11 of 16 compact cases and 9 of 16 distractor cases.

That is better than the constrained non-thinking LFM3 setup on these authored cases, but not grounds for a universal model ranking. Interfaces, prompts, decoding, execution paths, and model training differ. Some expected-escalate failures chose another read, which can be harmless rather than a dangerous action.

These controls also show why it would be misleading to compare d1 only with the initial bare-label setup. With a bounded thinking phase, the compact LFM3 result rose to 10 of 16 versus d1’s 11 of 16; the sample is far too small and interfaces too different to establish a winner. The useful contribution is the behavior trace and failure taxonomy, not a leaderboard claim.

### Fourth lesson: learned relevance can miss hard constraints

A separate d1 diagnostic classified 12 authored evidence snippets. At the declared 0.5 threshold, it selected three of six relevant snippets and no irrelevant snippets: precision 1.0, recall 0.5 on this tiny set.

It assigned the read-only authorization statement a relevance probability of about 0.136—below the selection threshold. It also missed source-authority information and a correction-related snippet.

If permissions had depended on learned relevance, a crucial constraint could have disappeared.

The compiler instead pins permissions in software. The classifier ranks only optional material. Its final selected context occupied 214 input tokens and excluded the large archive, but downstream answer success was not tested for that selected context. The candidate pool also contained potentially conflicting state statements; this prototype does not reconcile their provenance or freshness. A production context compiler must do that before calling its view authoritative.

That is the central engineering lesson:

> Learned context selection should not own policy retention.

## Thinking needs its own budget

A reasoning-enabled control initially allowed 1,024 total output tokens. The first three completed responses used the entire budget in reasoning and returned no final JSON. I stopped that configuration and retained the raw results rather than reporting imaginary remaining cases.

This is a finite-budget/configuration failure—not a reasoning-model accuracy estimate. The subsequent compact control set an explicit 128-token reasoning budget and a 512-token output limit. It returned valid JSON in all 16 cases and the expected action in 10, compared with 7 in the non-thinking compact condition. It still failed ambiguity, missing-target, injected-instruction, stale-evidence, revoked-permission, and latest-observation cases.

The native function-calling control matched the expected action in 3 of 16 cases, with a parsed tool call in 5. Eleven responses exhausted the 256-token output cap. These zero-argument functions and output limits are diagnostic choices, not production task schemas or a maximum-capability configuration. This control exposes a configuration/interface problem rather than proving that native tool calling is intrinsically weak.

Thinking, output schema, and tool adapters can interact. A fair small-model investigation needs to test those interactions rather than infer that one flag is sufficient.

## The architecture worth exploring

```text
User goal
   ↓
Teacher plan or retrieved workflow
   ↓
Deterministic task controller
   ↓
Bounded context compiler ← decision-assisted evidence/skill ranking
   ↓
Small generator or typed decision
   ↓
Deterministic permission and precondition checks
   ↓
Tool execution
   ↓
Read-back / tests / verified state
   ↓
Next local action, repair, or escalation
```

The model can suggest. The controller retains authoritative state. Tools provide observations. Verification remains independent of fluent prose and classifier confidence.

Teacher–student transfer can happen through procedural memory before weight training. [Agent Memory Distillation](https://arxiv.org/html/2608.07169) organizes teacher experience into workflows, subtask examples, and function guidance. Its published students are 4B–8B, not this local LFM3 setup.

Policy distillation should then use the same bounded state representation the student sees at deployment. Student-visited failures need correction data; copying only successful teacher trajectories misses the states a weaker agent actually encounters.

No teacher training or distillation was performed in this diagnostic.

## What this does not solve

A small model can still fail to invent a strategy, recognize dependencies, or reason correctly over the selected evidence. External memory solves access; it does not automatically solve inference.

Decision-assisted search is another possibility, but an ordinary classifier is not automatically a long-term value model or a process reward model. A selector cannot choose an action absent from its candidate set. Search also needs reversible tools or a sandbox, appropriate training, and a reliable evaluator.

[Research on test-time scaling](https://arxiv.org/abs/2408.03314) shows gains under important conditions, including nontrivial base-model success. It is not a promise that enough retries turn every small model into a frontier planner.

## An open-source contribution should start from existing work

This area already has relevant Hermes proposals:

- [First-class context selection](https://github.com/NousResearch/hermes-agent/issues/36765).
- [Declarative context scope](https://github.com/NousResearch/hermes-agent/issues/104064).
- [Decision/classifier model routing](https://github.com/NousResearch/hermes-agent/issues/132846).

The contributor RFC therefore focuses on a bounded request-budget contract, separate decision assistance, and deterministic authority. A vendor adapter belongs in a standalone plugin rather than a Liquid-specific core patch.

The wrong first PR would simply lower the context minimum.

## Next experiments

Before proposing a relaxed default floor:

1. Repeat and expand these cases with held-out task/tool families.
2. Test native tool parsing, thinking budgets, and structured outputs systematically.
3. Measure task success after context selection—not merely token savings.
4. Compare heuristic retrieval against decision-model reranking.
5. Add a strong-model baseline under the same observable state.
6. Test actual multi-step execution in a reversible sandbox.
7. Add teacher subtask memory, then student-state correction training.
8. Measure full latency, memory, cache reuse, and cost per successful task.

## Conclusion

The interesting claim is not “tiny models can do everything if we trim the prompt.”

It is:

> Some agent work can become bounded, observable decisions if the harness supplies reliable state and the right interface—but model reasoning limits and learned-selector failures remain real.

That is a testable contribution. Publishing the failed actions, missed constraints, raw responses, and exact configurations is more valuable than presenting a clean architecture diagram as proof.

---

**Publication status:** draft, not posted. A final results appendix accompanies this article. Code, diagnostics, methodology, and the contributor RFC are packaged for publication together. There is no public code-repository URL yet; one must be created or selected before announcing a public repository.
