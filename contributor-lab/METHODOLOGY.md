# Local lab: methodology and limitations

This is an exploratory diagnostic, not a competitive agent benchmark.

## Runs

- `run_diagnostics.py`: 16 authored next-operation cases × compact/distractor condition × LFM3/d1. One sample per cell, interleaved by case.
- `run_constrained.py`: same 16 cases × two conditions; LFM3 with a four-option JSON schema. Designed after observing format problems in the first run.
- `run_evidence_selection.py`: d1 relevance scoring for 12 authored snippets, then bounded prompt packing with the actual LFM3 chat template/tokenizer.
- `run_thinking.py`: compact reasoning-enabled control with explicit reasoning/output budgets.
- `run_native_tools.py`: compact native-function interface control with zero-argument operations (a diagnostic representation, not production tool schemas).
- `run-04-thinking`: aborted initial unbounded-thinking configuration; only three completed responses are reported.

Models are real existing local servers. Responses and usage are retained verbatim in JSONL. Expected answers are hand-authored and never sent to the models. Constructed distractors are clearly identified as test data, not records extracted from external systems.

## What these tasks measure

Narrow workflow-policy adherence: read-back after writes, permission checking, ambiguous record/target, latest user corrections, uncertainty reconciliation, stale observations, and simple injected instructions.

A model is asked to classify an operation, not to execute it. No actual business record is read or changed. The policy sometimes prefers escalation where another read could also be harmless; an incorrect label is not automatically an unsafe action. Likewise, a correct label is not proof of correct arguments or execution.

## Confounds to retain in every publication

- Only 16 scenarios and one sample per condition. No held-out distribution or statistically powered comparison.
- d1 and the generative model consume different interfaces/serialization; the same rule text is supplied but rendered contexts differ.
- The JSON-schema follow-up changes output instruction and decoding together. Do not claim a clean causal effect from grammar alone.
- LFM3 thinking is disabled in these main diagnostics. They are not tests of its maximum reasoning capability.
- Existing servers use different execution/offload paths and may contend with other requests. Do not claim d1 is faster/slower in general from these timings.
- A noisy prompt adds about one thousand tokens, not tens of thousands. Do not describe failures as a proven hard context-window limit or universal context rot.
- Compact prompts supply relevant state directly. This is an oracle-like representation advantage, not learned retrieval success.
- d1 probabilities are not proven calibrated on these tasks. A single Brier score/threshold evaluation is not a calibration study.
- The evidence snippets are classified independently. The candidate pool includes potentially conflicting statements (a status observation versus a missing-read-back notice); the prototype does not reconcile provenance/freshness or establish a consistent downstream view. This is another reason prompt packing is not evidence of task success.
- No frontier-model baseline, teacher training, distillation, long-horizon search, or full Hermes plugin integration has been exercised.
- Actual tokenizer count agreement on these text requests does not certify multimodal/tool paths across every backend.

## Native output handling

The initial LFM3 condition asks for a bare operation name but may return an XML-style tool call. Report two metrics separately:

1. Exact interface compliance: matches the requested bare label.
2. Diagnostic operation identity: if exactly one `<function=...>` exists, extract its literal name for an additional semantic-choice analysis.

The second metric is a retrospective analysis, not a tested execution parser or proof of valid arguments. Do not discard or relabel initial failures to improve the headline.

## What the software tests establish

Unit tests exercise mandatory-context retention, full schema charging, atomic tool groups, exact Unicode artifact recovery, stable selections, unknown-action rejection, no classifier permission override, and no completion without a matching read-back in a simplified state model.

The deterministic token counter used in unit tests is byte-based. It is explicitly a test double, never a reported model tokenizer. Real prompt-packing diagnostics use `/apply-template` plus `/tokenize` from the LFM server and compare counts to actual usage.

These tests are engineering invariants, not security certification. The simplified gate is not an entity-aware, production-grade transaction system. A production controller needs exact record/actor identity, authorization provenance, idempotency, and durable reconciliation.
