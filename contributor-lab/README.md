# A typed worker contract with explicit evidence and failure states

Status: standalone research prototype (`contributor-lab`) in [`iamdgarcia/the-learning-curve`](https://github.com/iamdgarcia/the-learning-curve). It is not an installed Hermes plugin, not a production safety controller, and not a benchmark against frontier models.

## Why this package exists

Small models often fail in agent loops for two separate reasons: interface/format errors and workflow-policy errors. Fixing JSON syntax does not make a model verify a write or respect a permission boundary.

This standalone package separates three responsibilities so deterministic software owns safety and completion while models propose bounded choices:

1. **Budgeted context compilation (`ContextCompiler`)**: reserves output tokens and a safety margin, charges active tool schemas, preserves atomic assistant/tool-result groups, pins mandatory policy/state, and fails closed (`BudgetExceeded`) instead of truncating mandatory context.
2. **Content-addressed evidence (`ArtifactStore`)**: stores exact tool outputs by SHA-256 digest with bounded slice reads and path-traversal checks, avoiding lossy paraphrases of execution records.
3. **Deterministic execution gate (`VerifiedState`, `choose_or_escalate`)**: blocks `update_record` when `write_authorized` is false or `uncertain_write` is true, blocks `finish` until `readback_done` matches `expected_value`, and abstains to `escalate` on invalid or sub-threshold probability distributions.

`CONTRIBUTOR_RFC.md` also outlines a candidate `DecisionProvider` protocol (`DecisionRequest` / `DecisionResponse`) for pluggable relevance scoring, action ranking, and escalation. Those RFC interfaces are design proposals, not existing Hermes APIs.

## What is verified locally

All core invariants and diagnostic numbers come from local artifacts in `contributor-lab`:

- **Unit tests (`unit-test-output.txt`)**: 17/17 tests pass in `0.002s` using Python standard library only. The unit suite uses a deterministic byte-based counter (`DeterministicTestCounter`) as a test double, never as a model tokenizer metric.
- **Diagnostic runs (`RESULTS.md`, `results/aggregate.json`)**: 140 completed inference requests across five main runs on 16 hand-authored record-update scenarios (one sample per case and condition, no business records mutated), plus 3 completed requests in an aborted unbounded-thinking run (`run-04-thinking`) that exhausted its 1,024-token output cap in reasoning (`3,072` output tokens, no final JSON):
  - LFM3 bare-label: `0/16` exact interface compliance in both compact and distractor conditions (`4/16` compact and `2/16` distractors retrospective operation identity).
  - d1 typed choice: `11/16` compact and `9/16` distractors expected action (`16/16` valid interface).
  - LFM3 constrained JSON: `7/16` compact and `3/16` distractors expected action (`16/16` schema valid).
  - LFM3 constrained JSON + 128-token reasoning budget (compact): `10/16` expected action (`16/16` schema valid).
  - LFM3 native-function compact control: `3/16` expected action, `5/16` parsed single-tool interface (11 responses hit the 256-token output limit).
- **Evidence filter (`run-03-selection`)**: on 12 authored snippets at threshold `0.5`, d1 matched `9/12` labels (`3/6` relevant selected, `0` irrelevant selected; precision `1.0`, recall `0.5` on this single task). The read-only constraint scored about `0.136` and would have been dropped by the learned filter; software pinned it as `mandatory=True`. Compiled prompt size was `214` input tokens + `128` output reserve + `96` margin inside a proposed `1,024`-token budget (no downstream model-success run was executed on that compiled view).
- **Template token accounting**: zero delta between `/apply-template` + `/tokenize` counts and reported provider prompt tokens across completed non-thinking text requests in `run-01` and `run-02`.

## Limitations and confounds

- Narrow 16-case diagnostic with 1 sample per cell; no held-out distribution, calibration study, or statistical comparison.
- d1 and LFM3 consume different interfaces and serialization; constrained JSON changes prompt instructions and decoding together.
- LFM3 thinking is disabled in the main diagnostics; noisy prompts add roughly 1,000 tokens of constructed distractors rather than tens of thousands.
- `VerifiedState` is a simplified invariant model, not an entity-aware production transaction controller.

## How to reproduce locally

Core library and unit tests require Python 3.10+ (standard library only):

```bash
python -m unittest -v test_bounded_context
```

Inference diagnostics expect local `llama.cpp`-compatible servers at `http://127.0.0.1:8080` (LFM3) and `http://127.0.0.1:8081` (d1), recorded in `environment.json`:

```bash
python run_diagnostics.py --output results/my-run
python run_constrained.py --output results/my-constrained-run
python run_evidence_selection.py
python run_thinking.py --output results/my-thinking-run
python run_native_tools.py
python aggregate_results.py
```

Package contents: `bounded_context.py`, `test_bounded_context.py`, `fixtures.py`, `run_*.py`, `aggregate_results.py`, `document_aborted_run.py`, `RESULTS.md`, `METHODOLOGY.md`, `CONTRIBUTOR_RFC.md`, `environment.json`, `MANIFEST.json`, `LICENSE`, and raw JSONL/summaries under `results/`.

Feedback or reproduction bugs: open an issue on `iamdgarcia/the-learning-curve` with a minimal case (Discussions are not enabled on the hub repository).

Join The Learning Curve for upcoming experiments and reproducible agent architecture notes:
https://iamdgarcia.substack.com
