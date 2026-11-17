# Contributor RFC: bounded-context agents with pluggable decision assistance

Status: local research proposal, not submitted upstream. No live Hermes profiles or services modified.

## Problem statement

Hermes is designed for reliable general-purpose tool use and normally rejects custom-provider models served below 64,000 tokens. Its existing context engine can select request-local messages; its existing tool-search infrastructure can reduce schema exposure. Neither mechanism alone establishes safe, reliable small-model operation.

We should investigate an **opt-in small-model profile** whose reliability contract is an explicitly measured request budget, mandatory task/policy retention, atomic tool-history preservation, and independently verified execution—not an assumption that every agent needs the same minimum advertised window.

This proposal does **not** claim that small models match frontier reasoning, that decision models solve general planning, or that a classifier can authorize external changes.

## Respect existing work

- [#36765](https://github.com/NousResearch/hermes-agent/issues/36765): first-class context selection; implemented through the existing context-engine seam. Do not duplicate it.
- [#104064](https://github.com/NousResearch/hermes-agent/issues/104064): declarative context scope, with discussion of optional scope hooks and validation boundaries.
- [#132846](https://github.com/NousResearch/hermes-agent/issues/132846): benchmark-aware decision/classifier routing. Treat routing as related prior work, not an original discovery here.

Current contribution guidance recommends standalone plugins for third-party product integrations and memory providers. A Liquid-specific adapter should live outside core. Any upstream request should concern a generic missing capability, not vendor-specific behavior.

## Scope

Three separable components:

1. **Budgeted context compilation**: selects evidence and complete recent interaction groups while keeping mandatory task state and policy.
2. **Pluggable decision assistance**: classification/ranking/escalation suggestions with typed probabilities.
3. **Deterministic execution authority**: permission/precondition checks, outcome reconciliation, and completion tests.

The decision provider is optional. A heuristic, existing small language model, local decision model, or remote decision service can implement the same ranking contract.

## Candidate interfaces (proposals, not existing Hermes APIs)

```python
@dataclass
class DecisionRequest:
    observable_state: dict
    choices: dict[str, str]
    decision_kind: str

@dataclass
class DecisionResponse:
    probabilities: dict[str, float]
    selected: str | None
    provider_metadata: dict

class DecisionProvider(Protocol):
    def decide(self, request: DecisionRequest) -> DecisionResponse: ...
```

Candidate decision kinds:

- Optional-evidence relevance.
- Applicable skill selection.
- Tool-bundle selection.
- Need for clarification or a stronger model.
- Ranking already valid, authorized candidate actions.
- Loop/failure classification.

Do not give this interface permission to write session history, replace hard policy, or mark a task complete.

## Request-budget contract

`rendered_input_tokens + reserved_output_tokens + safety_margin <= actual_served_window`

Count system instructions, messages, image/media contributions where supported, chat-template tokens, and tools. Character estimates may inform provisional packing, but a strict deployment requires a model-specific final check or conservative bounds.

Existing `select_context()` receives the model context length, not a complete `RequestBudget` accounting for generation reservation and separate tools. A possible generic extension would expose that accounting at the request-assembly seam; maintainers should determine the correct ownership.

Essential failure behavior:

- Mandatory material too large: split, escalate, or explicitly fail. No silent truncation.
- Invalid selector response or selector exception: normal fail-open behavior is acceptable only if the unmodified request still passes final admission.
- Oversized tool-call arguments: do not paraphrase execution records. Use an artifact-aware tool interface or stop.
- Tool-result spillover: retain an exact pointer and bounded expansion capability.

## State and persistence

Keep two independent representations:

- Immutable execution evidence: full requests/results, observed effects, exact identifiers.
- Bounded current-task state: goals, constraints, authorized scope, pending actions, verified observations, unresolved errors.

`on_turn_complete()` may index completed work but is not the sole persistence seam: abnormal returns can skip it. Store pending external actions before dispatch and reconcile interrupted writes with read-back/idempotency.

Do not manufacture user/system roles to increase the authority of retrieved evidence. Distinguish observations, summaries, procedural examples, and policies.

## Cache-aware selection

Keep the stable policy prefix intact. Append within a local episode when useful; recompile when topic/task relevance changes. Measure cache hit rate and context-selection latency in addition to prompt size. A smaller prompt that repeatedly defeats caching may be slower than a moderately larger stable prompt.

## Tool-selection ownership

`select_context()` affects message selection. Tools are a separate request field. Reuse progressive tool disclosure where suitable; investigate task-preselected bundles as a baseline. Do not assume that a tiny number of generic tools makes action selection easy: a free-form shell can move complexity back into the policy.

## Teacher–student modes

1. Offline teacher procedures, frozen student: retrieve the active workflow/subtask/function memory.
2. Strong planner and small executor: typed task dependencies and verification contracts.
3. Bounded-view policy distillation: teach the student only from causally available context.
4. Student-state correction: collect failure states and validate teacher correction targets.

A teacher target using evidence absent from the student view is unsuitable policy supervision. For context-selector supervision, richer teacher visibility is allowed only when it selects causally available evidence; label this difference explicitly.

No teacher/student training has been run in the local diagnostic attached to this proposal.

## Decision models and search

A decision model may act as a learned evaluator in candidate search, but is not inherently a process reward model or long-term value estimator. Those roles require relevant supervision and held-out testing.

Use read-only/sandboxed transitions for search. Require an abstain/escalate path. Maintain deterministic safety checks regardless of confidence. Multiple models sharing the same mistake are not independent verification.

## Evaluation and acceptance criteria

Before reducing normal admission constraints:

- Same-model comparisons: stock supported context; early compression; bounded selection; selection+decision assistance.
- Include native tools and constrained generative decisions as baselines, not only unconstrained classification.
- Keep served context and active context distinct.
- Evaluate task success, permission violations, unsupported completion, recovery, exact evidence recall, total tokens, full latency, memory, and teacher cost.
- Hold out tasks/tools/workflows and repeat runs with uncertainty estimates.
- Test missing results, wrong entities, current-vs-stale evidence, user corrections, prompt injection, interrupted writes, giant schemas, and multilingual tokenization.
- Do not infer calibrated reliability from returned confidence alone.
- Lower-window support must cover startup, runtime server probes, switching, fallback, resumed sessions, and child agents.

The attached standalone prototype tests several protocol/budget/persistence invariants and exercises real local models on deliberately narrow authored diagnostic cases. It is not a full Hermes integration or a validation of any new minimum context window.

## Open questions for maintainers

1. Can an opt-in context-engine capability declare support for bounded working contexts below the default floor, or should this remain a dedicated experimental profile?
2. Where should a final rendered-request budget guard live so it covers normal dispatch, retries, and fallbacks?
3. What public interface should expose active-tool schema cost to a context selector?
4. How should learned decisions attach provenance and abstention metadata without contaminating transcript authority?
5. Which end-to-end evaluation results would justify relaxing the default admission policy?

## Recommended contribution sequence

1. Publish a standalone prototype and full negative/positive diagnostic results.
2. Discuss alignment with existing context-scope and decision-routing work.
3. Add a vendor-neutral plugin adapter only after testing real endpoint behavior.
4. Propose a narrowly scoped generic budget/admission extension if needed.
5. Do not submit a patch that merely lowers `MINIMUM_CONTEXT_LENGTH`.

Source snapshot: Hermes `26cd2e6d83494c22a8b5e961f20e293285c48d0a`; see the accompanying report and experiment metadata for model/backend revisions.
